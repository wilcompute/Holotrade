const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
global.window = global;
require(path.join(root, "js/substrate.js"));
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const H = require(path.join(root, "js/w33-fibre-hypervisor-profile.js"));

function freshPlan() {
  return new ExecutionPlan({
    name: "fibre-hypervisor",
    workloadId: "universal-vm",
    requestedSeconds: 10,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
}

test("1296-state fibre hypervisor binds one immutable profile from each carrier fork", () => {
  const plan = freshPlan();
  const circuit = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const pair = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  const hyper = H.bind(plan, circuit, pair);

  assert.equal(hyper.machineType, H.MACHINE_TYPE);
  assert.deepEqual(hyper.logicalModules, [81, 64]);
  assert.equal(hyper.stateModel.hypervisorStates, 1296);
  assert.equal(hyper.stateModel.baseStates, 36);
  assert.equal(hyper.stateModel.circuitFibre, 6);
  assert.equal(hyper.stateModel.pairFibre, 6);
  assert.equal(hyper.runtimeRetype, "FORBIDDEN");
  assert.equal(hyper.carrierConversion, "FORBIDDEN");
  assert.ok(H.verify(hyper, plan, circuit, pair));
});

test("fibre-product coordinate is a bijection with six-to-one projections", () => {
  const check = H.selfCheck();
  assert.equal(check.ok, true);
  assert.equal(check.counts.hypervisorStates, 1296);
  assert.equal(check.counts.statesPerBase, 36);
  assert.equal(check.counts.projectionDegree, 6);
  assert.equal(check.checks.circuitProjectionSixToOne, true);
  assert.equal(check.checks.pairProjectionSixToOne, true);
});

test("one 216-state projection never determines the other fork", () => {
  const check = H.selfCheck();
  assert.equal(check.checks.circuitDoesNotDeterminePair, true);
  assert.equal(check.checks.pairDoesNotDetermineCircuit, true);

  const lifts = new Set();
  for (let p = 0; p < 6; p += 1) lifts.add(H.coordinate(7, 2, p).pair216);
  assert.equal(lifts.size, 6);
});

test("hypervisor refuses two copies of the same fork", () => {
  const plan = freshPlan();
  const a = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const b = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.throws(() => H.bind(plan, a, b), /exactly one ST81 fork and one ST64 fork/);
});

test("hypervisor identity is tied to the exact guest profiles and plan", () => {
  const plan = freshPlan();
  const circuit = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const pair = P.bind(plan, P.MACHINE_TYPE.PAIR_ST64);
  const hyper = H.bind(plan, circuit, pair);

  assert.ok(H.verify(hyper, plan, circuit, pair));
  plan.requestedSeconds = 999;
  assert.equal(plan.verify(), false);
  assert.equal(H.verify(hyper, plan, circuit, pair), false);
});
