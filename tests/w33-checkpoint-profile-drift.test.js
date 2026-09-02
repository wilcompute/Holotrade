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
function signedPlan(name) {
  const plan = new ExecutionPlan({ name, workloadId: "llm-train", requestedSeconds: 2, artifacts: [{ name: "img", digest: "sha256:demo" }], magicBudget: 1 });
  plan.magicBudget = 1; plan.digest = plan.computeDigest(); plan.signature = plan.sign(); return plan;
}
function fixture() {
  const sourcePlan = signedPlan("profile-drift-source"), driftPlan = signedPlan("profile-drift-target");
  const node = { id: "source81" };
  const base = { place: () => [{ node, score: 1 }], launch: (_p, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry(); registry.register(node.id, P.MACHINE_TYPE.CIRCUIT_ST81);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const sourceProfile = P.bind(sourcePlan, P.MACHINE_TYPE.CIRCUIT_ST81), driftProfile = P.bind(driftPlan, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(sourceProfile.machineType, driftProfile.machineType); assert.notEqual(sourceProfile.digest, driftProfile.digest);
  const vm = engine.launch(sourcePlan, sourceProfile, node).vm, contract = engine.compileGoMicroVM(sourcePlan, sourceProfile);
  const passport = D.bindPassport({
    plan: sourcePlan, profile: sourceProfile, vm, contract,
    guestImage: d("guest"), memoryRoot: d("memory"), memoryCapabilityDigest: d("cap"), componentLinkDigest: d("link"), packetRefinementDigest: d("packet"), historyRoot: d("history"),
    capabilityEpoch: 2, revocationRoot: d("rev2"), waitForRoot: d("wait"), cancellationRoot: d("cancel"), asyncScheduleRoot: d("schedule"), gcRegistryRoot: d("gc"), magicBudget: 1,
  });
  return { passport, sourceProfile, driftProfile };
}

test("full checkpoint restore rejects same-shaped construction-profile drift", () => {
  const f = fixture();
  const gate = D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: f.driftProfile, kind: D.CHECKPOINT.FULL_RESTORE });
  assert.equal(gate.ok, false); assert.equal(gate.code, "PROFILE_DRIFT_FULL_RESTORE_FORBIDDEN");
});

test("neutral continuation across profile drift starts new identity", () => {
  const f = fixture();
  const gate = D.checkpointAdmission({ sourcePassport: f.passport, targetProfile: f.driftProfile, kind: D.CHECKPOINT.NEUTRAL_CONTINUATION, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral") });
  assert.equal(gate.ok, true); assert.equal(gate.code, "NEUTRAL_CONTINUATION_PROFILE_DRIFT"); assert.equal(gate.startsNewMachineIdentity, true);
});

test("failover cannot disguise same-shaped profile drift as full restore", () => {
  const f = fixture();
  const r = F.planRecovery({ sourcePassport: f.passport, safePoint: "SYSCALL_BOUNDARY", neutralStateDigest: d("neutral"), candidates: [
    { nodeId: "drift81", profile: f.driftProfile, capabilityEpoch: 2, revocationRoot: d("rev2"), estimatedRecoveryMs: 1 },
  ] });
  assert.equal(r.ok, true); assert.equal(r.mode, D.CHECKPOINT.NEUTRAL_CONTINUATION); assert.equal(r.startsNewMachineIdentity, true);
});
