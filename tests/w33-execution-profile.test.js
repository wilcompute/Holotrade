const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
global.window = global;
const S = require(path.join(root, "js/substrate.js"));
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));

function freshPlan() {
  return new ExecutionPlan({
    name: "typed-w33",
    workloadId: "llm-train",
    requestedSeconds: 10,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
}

test("W33 machine carrier fixes the logical module dimension", () => {
  const plan = freshPlan();
  const a = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const b = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(a.logicalDimension, 81);
  assert.equal(b.logicalDimension, 64);
  assert.notEqual(a.machineType, b.machineType);
  assert.notEqual(a.digest, b.digest, "different machines must have different deployment identities");
  assert.ok(P.verify(a, plan));
  assert.ok(P.verify(b, plan));
});

test("the two order-51840 symmetry domains never alias in the execution profile", () => {
  const p = P.bind(freshPlan(), P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(p.symmetryNamespaces.order, 51840);
  assert.notEqual(p.symmetryNamespaces.cliffordLift, p.symmetryNamespaces.projectiveWeyl);
  assert.equal(p.symmetryNamespaces.sameOrderNotSameNamespace, true);
});

test("tampering with the underlying plan invalidates the W33 execution profile", () => {
  const plan = freshPlan();
  const profile = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.ok(P.verify(profile, plan));
  plan.requestedSeconds = 9999;
  assert.equal(plan.verify(), false, "core plan integrity seal detects the edit");
  assert.equal(P.verify(profile, plan), false, "profile fails closed when its plan is no longer valid");
});

test("unknown carriers are rejected rather than coerced", () => {
  assert.throws(() => P.bind(freshPlan(), "w33.gauge-maybe"), /unknown W33 machine type/);
});

test("binding is construction-time: a different carrier is a new profile, not a mutation", () => {
  const plan = freshPlan();
  const first = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(Object.isFrozen(first), true);
  const second = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(first.machineType, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(second.machineType, P.MACHINE_TYPE.PAIR_ST64);
  assert.notEqual(first.digest, second.digest);
});
