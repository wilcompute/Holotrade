const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));
const D = require(path.join(root, "js/w33-passport-deployment.js"));
const F = require(path.join(root, "js/w33-failover-orchestrator.js"));

function d(label) { return D.sha256({ label }); }

function source() {
  const plan = new ExecutionPlan({
    name: "failover-source",
    workloadId: "llm-train",
    requestedSeconds: 2,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
    magicBudget: 1,
  });
  plan.magicBudget = 1;
  plan.digest = plan.computeDigest();
  plan.signature = plan.sign();
  const node = { id: "source81" };
  const base = { place: () => [{ node, score: 1 }], launch: (_p, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry();
  registry.register(node.id, P.MACHINE_TYPE.CIRCUIT_ST81);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile81 = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const profile64 = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  const vm = engine.launch(plan, profile81, node).vm;
  const contract = engine.compileGoMicroVM(plan, profile81);
  const passport = D.bindPassport({
    plan, profile: profile81, vm, contract,
    guestImage: d("guest"), memoryRoot: d("memory"), memoryCapabilityDigest: d("cap"),
    componentLinkDigest: d("link"), packetRefinementDigest: d("packet"), historyRoot: d("history"),
    magicBudget: 1,
  });
  return { plan, passport, profile81, profile64 };
}

test("same-carrier full restore wins even when cross-carrier target is cheaper", () => {
  const f = source();
  const r = F.planRecovery({
    sourcePassport: f.passport,
    safePoint: "SYSCALL_BOUNDARY",
    neutralStateDigest: d("neutral"),
    candidates: [
      { nodeId: "cheap64", profile: f.profile64, estimatedRecoveryMs: 1, estimatedCostUSD: 0 },
      { nodeId: "slower81", profile: f.profile81, estimatedRecoveryMs: 50, estimatedCostUSD: 1 },
    ],
  });
  assert.ok(r.ok);
  assert.equal(r.mode, D.CHECKPOINT.FULL_RESTORE);
  assert.equal(r.nodeId, "slower81");
  assert.equal(r.startsNewMachineIdentity, false);
});

test("cross-carrier failover uses neutral continuation only when same-carrier is unavailable", () => {
  const f = source();
  const r = F.planRecovery({
    sourcePassport: f.passport,
    safePoint: "SYSCALL_BOUNDARY",
    neutralStateDigest: d("neutral"),
    candidates: [{ nodeId: "target64", profile: f.profile64, estimatedRecoveryMs: 4, estimatedCostUSD: 0.01 }],
  });
  assert.ok(r.ok);
  assert.equal(r.mode, D.CHECKPOINT.NEUTRAL_CONTINUATION);
  assert.equal(r.targetMachineType, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(r.startsNewMachineIdentity, true);
});

test("cross-carrier fallback fails closed without neutral safe point", () => {
  const f = source();
  const r = F.planRecovery({
    sourcePassport: f.passport,
    safePoint: "MID_INSTRUCTION",
    neutralStateDigest: d("neutral"),
    candidates: [{ nodeId: "target64", profile: f.profile64 }],
  });
  assert.equal(r.ok, false);
  assert.equal(r.code, "NO_ADMISSIBLE_RECOVERY_MODE");
});

test("unhealthy same-carrier nodes are ignored before policy selection", () => {
  const f = source();
  const r = F.planRecovery({
    sourcePassport: f.passport,
    safePoint: "SYSCALL_BOUNDARY",
    neutralStateDigest: d("neutral"),
    candidates: [
      { nodeId: "dead81", profile: f.profile81, healthy: false, estimatedRecoveryMs: 1 },
      { nodeId: "live64", profile: f.profile64, estimatedRecoveryMs: 5 },
    ],
  });
  assert.ok(r.ok);
  assert.equal(r.nodeId, "live64");
  assert.equal(r.mode, D.CHECKPOINT.NEUTRAL_CONTINUATION);
});
