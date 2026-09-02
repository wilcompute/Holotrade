const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));
const D = require(path.join(root, "js/w33-passport-deployment.js"));
const Receipt = require(path.join(root, "runtime/receipt.js"));

function d(label) { return D.sha256({ label }); }

function fixture(machineType = P.MACHINE_TYPE.CIRCUIT_ST81, magicBudget = 2) {
  const plan = new ExecutionPlan({
    name: "passport-deploy",
    workloadId: "llm-train",
    requestedSeconds: 2,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
    magicBudget,
  });
  plan.magicBudget = magicBudget;
  plan.digest = plan.computeDigest();
  plan.signature = plan.sign();

  const node = { id: machineType === P.MACHINE_TYPE.CIRCUIT_ST81 ? "n81" : "n64" };
  const base = { place: () => [{ node, score: 1 }], launch: (_plan, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry();
  registry.register(node.id, machineType);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile = P.bind(plan, machineType);
  const launched = engine.launch(plan, profile, node);
  assert.ok(launched.ok);
  const contract = engine.compileGoMicroVM(plan, profile);

  const context = {
    plan, profile, vm: launched.vm, contract,
    guestImage: d("guest"),
    memoryRoot: d("memory"),
    memoryCapabilityDigest: d("cap"),
    componentLinkDigest: d("link"),
    packetRefinementDigest: d("packet"),
    historyRoot: d("history"),
    capabilityEpoch: 0,
    revocationRoot: d("revocation-root-0"),
    waitForRoot: d("wait-for"),
    cancellationRoot: d("cancellation"),
    asyncScheduleRoot: d("schedule"),
    gcRegistryRoot: d("gc"),
    erasurePolicy: "EXPLICIT_DISCARD_ONLY",
    magicBudget,
  };
  const passport = D.bindPassport(context);
  return { plan, node, engine, profile, vm: launched.vm, contract, context, passport };
}

test("passport commits complete profiled deployment and runtime control plane", () => {
  const f = fixture();
  assert.equal(f.passport.planDigest, f.plan.digest);
  assert.equal(f.passport.profileDigest, f.profile.digest);
  assert.equal(f.passport.logicalDimension, 81);
  assert.equal(f.passport.runtimeRetype, "FORBIDDEN");
  assert.equal(f.passport.capabilityEpoch, 0);
  assert.equal(f.passport.revocationRoot, f.context.revocationRoot);
  assert.equal(f.passport.waitForRoot, f.context.waitForRoot);
  assert.equal(f.passport.cancellationRoot, f.context.cancellationRoot);
  assert.equal(f.passport.asyncScheduleRoot, f.context.asyncScheduleRoot);
  assert.equal(f.passport.gcRegistryRoot, f.context.gcRegistryRoot);
  assert.ok(D.verifyPassport(f.passport, f.context));
  assert.ok(D.validatePassportIdentity(f.passport, f.plan, f.profile, f.vm, f.contract));
});

test("passport cannot inflate magic authority beyond signed plan", () => {
  const f = fixture(P.MACHINE_TYPE.CIRCUIT_ST81, 1);
  assert.throws(() => D.bindPassport({ ...f.context, magicBudget: 2 }), /exceeds signed execution plan budget/);
});

test("full restore is same construction profile only; neutral continuation may cross fork", () => {
  const f = fixture();
  const profile64 = P.bind(f.plan, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: f.profile, kind: D.CHECKPOINT.FULL_RESTORE }).code, "FULL_RESTORE_SAME_PROFILE");
  assert.equal(D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: profile64, kind: D.CHECKPOINT.FULL_RESTORE }).code, "CROSS_CARRIER_FULL_RESTORE_FORBIDDEN");
  const neutral = D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: profile64, kind: D.CHECKPOINT.NEUTRAL_CONTINUATION, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral-state") });
  assert.ok(neutral.ok);
  assert.equal(neutral.code, "NEUTRAL_CONTINUATION_CROSS_CARRIER");
  assert.equal(neutral.startsNewMachineIdentity, true);
});

test("neutral continuation requires explicit safe point and content identity", () => {
  const f = fixture();
  const profile64 = P.bind(f.plan, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: profile64, kind: D.CHECKPOINT.NEUTRAL_CONTINUATION, safePoint: "MID_INSTRUCTION", neutralStateDigest: d("neutral") }).code, "NEUTRAL_SAFEPOINT_REQUIRED");
  assert.equal(D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: profile64, kind: D.CHECKPOINT.NEUTRAL_CONTINUATION, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: "bad" }).code, "NEUTRAL_STATE_DIGEST_REQUIRED");
});

test("runtime control-plane mutation invalidates passport identity", () => {
  const f = fixture();
  for (const mutation of [
    { magicBudget: 999 },
    { memoryRoot: d("different-memory") },
    { capabilityEpoch: 1 },
    { revocationRoot: d("revoked") },
    { waitForRoot: d("different-wait") },
    { cancellationRoot: d("different-cancel") },
    { asyncScheduleRoot: d("different-schedule") },
    { gcRegistryRoot: d("different-gc") },
  ]) assert.equal(D.verifyPassport({ ...f.passport, ...mutation }, f.context), false);
});

test("signed receipt binder refuses stale internal passport digest", () => {
  const f = fixture();
  const stale = { ...f.passport, cancellationRoot: d("attacker-cancel") };
  assert.equal(D.validatePassportIdentity(stale, f.plan, f.profile, f.vm, f.contract), false);
  assert.throws(() => D.attachPassportReceiptMetadata({}, f.plan, f.profile, f.vm, f.contract, stale), /passport identity does not verify/);
});

test("delivery payload commits exact execution passport control-plane binding", () => {
  const f = fixture();
  const metadata = D.attachPassportReceiptMetadata({ market: "demo" }, f.plan, f.profile, f.vm, f.contract, f.passport, { bindingDigest: d("history-binding") });
  const payload = Receipt.deliveryPayload({
    executionId: "exec-passport-1", nodeId: f.node.id, outcome: "settled",
    artifacts: [{ role: "output", bytes: 1, digest: `sha256:${"a".repeat(64)}` }],
    capabilities: { findings: [] }, startedAtMs: 1000, finishedAtMs: 2000,
    nonce: "nonce-passport-1", metadata,
  });
  assert.equal(payload.metadata.w33ExecutionPassport.passportId, f.passport.passportId);
  assert.equal(payload.metadata.w33ExecutionPassport.capabilityEpoch, 0);
  assert.equal(payload.metadata.w33ExecutionPassport.cancellationRoot, f.passport.cancellationRoot);
  assert.equal(payload.metadata.w33ExecutionPassport.asyncScheduleRoot, f.passport.asyncScheduleRoot);
});
