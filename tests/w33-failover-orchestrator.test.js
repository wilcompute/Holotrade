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
  const plan = new ExecutionPlan({ name: "failover-source", workloadId: "llm-train", requestedSeconds: 2, artifacts: [{ name: "img", digest: "sha256:demo" }], magicBudget: 1 });
  plan.magicBudget = 1; plan.digest = plan.computeDigest(); plan.signature = plan.sign();
  const node = { id: "source81" };
  const base = { place: () => [{ node, score: 1 }], launch: (_p, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry(); registry.register(node.id, P.MACHINE_TYPE.CIRCUIT_ST81);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile81 = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const profile64 = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  const vm = engine.launch(plan, profile81, node).vm;
  const contract = engine.compileGoMicroVM(plan, profile81);
  const controls = {
    capabilityEpoch: 4, revocationRoot: d("rev-4"), waitForRoot: d("wait"), cancellationRoot: d("cancel"),
    asyncScheduleRoot: d("schedule"), gcRegistryRoot: d("gc"),
  };
  const passport = D.bindPassport({
    plan, profile: profile81, vm, contract,
    guestImage: d("guest"), memoryRoot: d("memory"), memoryCapabilityDigest: d("cap"),
    componentLinkDigest: d("link"), packetRefinementDigest: d("packet"), historyRoot: d("history"),
    ...controls, magicBudget: 1,
  });
  return { plan, engine, passport, profile81, profile64, controls };
}

function candidate(nodeId, profile, f, extra = {}) {
  return { nodeId, profile, capabilityEpoch: f.controls.capabilityEpoch, revocationRoot: f.controls.revocationRoot, ...extra };
}

test("same-profile same-authority full restore wins even when cross-carrier target is cheaper", () => {
  const f = source();
  const r = F.planRecovery({ sourcePassport: f.passport, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral"), candidates: [
    candidate("cheap64", f.profile64, f, { estimatedRecoveryMs: 1 }),
    candidate("slower81", f.profile81, f, { estimatedRecoveryMs: 50, estimatedCostUSD: 1 }),
  ] });
  assert.ok(r.ok); assert.equal(r.mode, D.CHECKPOINT.FULL_RESTORE); assert.equal(r.nodeId, "slower81");
  assert.equal(r.requiresPassportRemint, false);
});

test("rotated authority forbids old full restore and forces neutral continuation with remint", () => {
  const f = source();
  const r = F.planRecovery({ sourcePassport: f.passport, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral"), candidates: [
    { nodeId: "rotated81", profile: f.profile81, capabilityEpoch: 5, revocationRoot: d("rev-5") },
  ] });
  assert.ok(r.ok); assert.equal(r.mode, D.CHECKPOINT.NEUTRAL_CONTINUATION);
  assert.equal(r.requiresPassportRemint, true); assert.equal(r.targetCapabilityEpoch, 5);
});

test("cross-carrier failover uses neutral continuation only when full restore is unavailable", () => {
  const f = source();
  const r = F.planRecovery({ sourcePassport: f.passport, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral"), candidates: [candidate("target64", f.profile64, f)] });
  assert.ok(r.ok); assert.equal(r.mode, D.CHECKPOINT.NEUTRAL_CONTINUATION); assert.equal(r.startsNewMachineIdentity, true);
});

test("neutral continuation remints exact target-authority passport", () => {
  const f = source();
  const recovery = F.planRecovery({ sourcePassport: f.passport, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral"), candidates: [
    { nodeId: "target64", profile: f.profile64, capabilityEpoch: 5, revocationRoot: d("rev-5") },
  ] });
  const targetNode = { id: "target64" };
  const base = { place: () => [{ node: targetNode, score: 1 }], launch: (_p, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry(); registry.register(targetNode.id, P.MACHINE_TYPE.PAIR_ST64);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const vm = engine.launch(f.plan, f.profile64, targetNode).vm;
  const contract = engine.compileGoMicroVM(f.plan, f.profile64);
  const fresh = F.materializeRecoveryPassport({
    recovery, sourcePassport: f.passport, neutralStateDigest: d("neutral"), plan: f.plan, profile: f.profile64, vm, contract,
    targetState: { capabilityEpoch: 5, revocationRoot: d("rev-5"), memoryCapabilityDigest: d("new-cap"), historyRoot: d("new-history"), waitForRoot: d("new-wait"), cancellationRoot: d("new-cancel"), asyncScheduleRoot: d("new-schedule"), gcRegistryRoot: d("new-gc") },
  });
  assert.equal(fresh.machineType, P.MACHINE_TYPE.PAIR_ST64); assert.equal(fresh.capabilityEpoch, 5);
  assert.notEqual(fresh.passportId, f.passport.passportId); assert.equal(fresh.memoryRoot, d("neutral"));
});

test("cross-carrier fallback fails closed without neutral safe point", () => {
  const f = source();
  const r = F.planRecovery({ sourcePassport: f.passport, safePoint: "MID_INSTRUCTION", neutralStateDigest: d("neutral"), candidates: [candidate("target64", f.profile64, f)] });
  assert.equal(r.ok, false); assert.equal(r.code, "NO_ADMISSIBLE_RECOVERY_MODE");
});
