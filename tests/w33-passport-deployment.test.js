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

function d(label) {
  return D.sha256({ label });
}

function fixture(machineType = P.MACHINE_TYPE.CIRCUIT_ST81, magicBudget = 2) {
  const plan = new ExecutionPlan({
    name: "passport-deploy",
    workloadId: "llm-train",
    requestedSeconds: 2,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
    magicBudget,
  });
  // ExecutionPlan derives magicBudget from the supplied spec when constructed
  // directly. Keep the fixture explicit so the passport cannot exceed it.
  plan.magicBudget = magicBudget;
  plan.digest = plan.computeDigest();
  plan.signature = plan.sign();

  const node = { id: machineType === P.MACHINE_TYPE.CIRCUIT_ST81 ? "n81" : "n64" };
  const base = {
    place: () => [{ node, score: 1 }],
    launch: (_plan, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }),
  };
  const registry = new X.W33HostRegistry();
  registry.register(node.id, machineType);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile = P.bind(plan, machineType);
  const launched = engine.launch(plan, profile, node);
  assert.ok(launched.ok);
  const contract = engine.compileGoMicroVM(plan, profile);

  const context = {
    plan,
    profile,
    vm: launched.vm,
    contract,
    guestImage: d("guest"),
    memoryRoot: d("memory"),
    memoryCapabilityDigest: d("cap"),
    componentLinkDigest: d("link"),
    packetRefinementDigest: d("packet"),
    historyRoot: d("history"),
    erasurePolicy: "EXPLICIT_DISCARD_ONLY",
    magicBudget,
  };
  const passport = D.bindPassport(context);
  return { plan, node, engine, profile, vm: launched.vm, contract, context, passport };
}

test("passport commits the complete profiled deployment context", () => {
  const f = fixture();
  assert.equal(f.passport.planDigest, f.plan.digest);
  assert.equal(f.passport.profileDigest, f.profile.digest);
  assert.equal(f.passport.machineType, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(f.passport.logicalDimension, 81);
  assert.equal(f.passport.runtimeRetype, "FORBIDDEN");
  assert.equal(f.passport.magicBudget, 2);
  assert.ok(D.verifyPassport(f.passport, f.context));
});

test("passport cannot inflate magic authority beyond the signed plan", () => {
  const f = fixture(P.MACHINE_TYPE.CIRCUIT_ST81, 1);
  assert.throws(() => D.bindPassport({ ...f.context, magicBudget: 2 }), /exceeds signed execution plan budget/);
});

test("full restore is same-carrier only; neutral continuation may cross the fork", () => {
  const f = fixture();
  const profile64 = P.bind(f.plan, P.MACHINE_TYPE.PAIR_ST64);

  assert.equal(
    D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: f.profile, kind: D.CHECKPOINT.FULL_RESTORE }).code,
    "FULL_RESTORE_SAME_CARRIER"
  );
  assert.equal(
    D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: profile64, kind: D.CHECKPOINT.FULL_RESTORE }).code,
    "CROSS_CARRIER_FULL_RESTORE_FORBIDDEN"
  );

  const neutral = D.checkpointAdmission({
    sourcePassport: f.passport,
    targetProfile: profile64,
    kind: D.CHECKPOINT.NEUTRAL_CONTINUATION,
    safePoint: "SYSCALL_BOUNDARY",
    neutralStateDigest: d("neutral-state"),
  });
  assert.ok(neutral.ok);
  assert.equal(neutral.code, "NEUTRAL_CONTINUATION_CROSS_CARRIER");
  assert.equal(neutral.startsNewMachineIdentity, true);
  assert.equal(neutral.runtimeRetype, "FORBIDDEN");
});

test("cross-carrier neutral continuation requires explicit safe point and content identity", () => {
  const f = fixture();
  const profile64 = P.bind(f.plan, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(D.checkpointAdmission({
    sourcePassport: f.passport,
    targetProfile: profile64,
    kind: D.CHECKPOINT.NEUTRAL_CONTINUATION,
    safePoint: "MID_INSTRUCTION",
    neutralStateDigest: d("neutral-state"),
  }).code, "NEUTRAL_SAFEPOINT_REQUIRED");
  assert.equal(D.checkpointAdmission({
    sourcePassport: f.passport,
    targetProfile: profile64,
    kind: D.CHECKPOINT.NEUTRAL_CONTINUATION,
    safePoint: "SYSCALL_BOUNDARY",
    neutralStateDigest: "not-a-digest",
  }).code, "NEUTRAL_STATE_DIGEST_REQUIRED");
});

test("stale or tampered passport fails exact verification", () => {
  const f = fixture();
  assert.equal(D.verifyPassport({ ...f.passport, magicBudget: 999 }, f.context), false);
  assert.equal(D.verifyPassport({ ...f.passport, machineType: P.MACHINE_TYPE.PAIR_ST64 }, f.context), false);
  assert.equal(D.verifyPassport({ ...f.passport, memoryRoot: d("different-memory") }, f.context), false);
});

test("generic signed receipt payload commits exact execution passport binding", () => {
  const f = fixture();
  const metadata = D.attachPassportReceiptMetadata(
    { market: "demo" }, f.plan, f.profile, f.vm, f.contract, f.passport,
    { bindingDigest: d("history-binding") }
  );
  const payload = Receipt.deliveryPayload({
    executionId: "exec-passport-1",
    nodeId: f.node.id,
    outcome: "settled",
    artifacts: [{ role: "output", bytes: 1, digest: `sha256:${"a".repeat(64)}` }],
    capabilities: { findings: [] },
    startedAtMs: 1000,
    finishedAtMs: 2000,
    nonce: "nonce-passport-1",
    metadata,
  });
  assert.deepEqual(payload.metadata.w33ExecutionPassport, metadata.w33ExecutionPassport);
  assert.equal(payload.metadata.w33ExecutionPassport.passportId, f.passport.passportId);
  assert.equal(payload.metadata.w33ExecutionPassport.magicBudget, f.passport.magicBudget);

  const tampered = {
    ...payload,
    metadata: {
      ...payload.metadata,
      w33ExecutionPassport: {
        ...payload.metadata.w33ExecutionPassport,
        magicBudget: 999,
      },
    },
  };
  assert.notDeepEqual(tampered.metadata, payload.metadata);
});
