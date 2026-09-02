const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
global.window = global;
require(path.join(root, "js/substrate.js"));
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const A = require(path.join(root, "js/w33-machine-admission.js"));

function plan() {
  return new ExecutionPlan({
    name: "carrier-fork-admission",
    workloadId: "llm-train",
    requestedSeconds: 10,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
}

function nodes() {
  return [
    { id: "N81-A" },
    { id: "N64-A" },
    { id: "N81-B" },
    { id: "UNTYPED" },
  ];
}

function inventory() {
  return A.compileInventory([
    { nodeId: "N81-A", machineType: P.MACHINE_TYPE.CIRCUIT_ST81 },
    { nodeId: "N64-A", machineType: P.MACHINE_TYPE.PAIR_ST64 },
    { nodeId: "N81-B", machineType: P.MACHINE_TYPE.CIRCUIT_ST81 },
  ]);
}

test("immutable W33 inventory binds node ids to one carrier fork", () => {
  const inv = inventory();
  assert.ok(A.verifyInventory(inv));
  assert.equal(inv.runtimeRetype, "FORBIDDEN");
  assert.equal(Object.isFrozen(inv), true);
  assert.equal(Object.isFrozen(inv.assignments), true);
  assert.equal(A.machineTypeFor(inv, { id: "N81-A" }), P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(A.machineTypeFor(inv, { id: "N64-A" }), P.MACHINE_TYPE.PAIR_ST64);
  assert.equal(A.machineTypeFor(inv, { id: "UNTYPED" }), null);
});

test("the carrier fork first becomes operational at scheduler placement", () => {
  const pl = plan();
  const p81 = P.bind(pl, P.MACHINE_TYPE.CIRCUIT_ST81);
  const p64 = P.bind(pl, P.MACHINE_TYPE.PAIR_ST64);
  const ns = nodes();
  const engine = {
    place: (_plan, _opts) => ns.map((node, i) => ({ node, score: i })),
  };
  const inv = inventory();
  const a = A.place(engine, p81, pl, inv, { limit: 10 });
  const b = A.place(engine, p64, pl, inv, { limit: 10 });
  assert.ok(a.ok && b.ok);
  assert.deepEqual(a.candidates.map((x) => x.node.id), ["N81-A", "N81-B"]);
  assert.deepEqual(b.candidates.map((x) => x.node.id), ["N64-A"]);
  assert.equal(a.logicalDimension, 81);
  assert.equal(b.logicalDimension, 64);
  assert.deepEqual(new Set(a.candidates.map((x) => x.node.id)), new Set(["N81-A", "N81-B"]));
  assert.equal(a.candidates.some((x) => b.candidates.some((y) => y.node.id === x.node.id)), false,
    "the two machine profiles must not alias to one typed node pool");
});

test("wrong-type launch fails before generic ExecutionEngine.launch is called", () => {
  const pl = plan();
  const p81 = P.bind(pl, P.MACHINE_TYPE.CIRCUIT_ST81);
  const inv = inventory();
  let calls = 0;
  const engine = { launch: () => { calls += 1; return { ok: true, vm: { id: "VM" } }; } };
  const wrong = A.launch(engine, p81, pl, { id: "N64-A" }, inv);
  assert.equal(wrong.ok, false);
  assert.equal(wrong.code, "W33_MACHINE_MISMATCH");
  assert.equal(calls, 0);

  const untyped = A.launch(engine, p81, pl, { id: "UNTYPED" }, inv);
  assert.equal(untyped.ok, false);
  assert.equal(untyped.code, "W33_UNTYPED_NODE");
  assert.equal(calls, 0);
});

test("correct-type launch carries both immutable commitments into the result", () => {
  const pl = plan();
  const p81 = P.bind(pl, P.MACHINE_TYPE.CIRCUIT_ST81);
  const inv = inventory();
  let calls = 0;
  const engine = { launch: (_plan, node) => { calls += 1; return { ok: true, vm: { id: `VM-${node.id}` } }; } };
  const r = A.launch(engine, p81, pl, { id: "N81-A" }, inv);
  assert.ok(r.ok);
  assert.equal(calls, 1);
  assert.equal(r.w33MachineType, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(r.w33LogicalDimension, 81);
  assert.equal(r.w33ProfileDigest, p81.digest);
  assert.equal(r.w33InventoryDigest, inv.digest);
});

test("tampered profile or inventory is rejected fail-closed", () => {
  const pl = plan();
  const p81 = P.bind(pl, P.MACHINE_TYPE.CIRCUIT_ST81);
  const inv = inventory();
  const fakeProfile = { ...p81, logicalDimension: 64 };
  const fakeInventory = { ...inv, assignments: { ...inv.assignments, "N81-A": P.MACHINE_TYPE.PAIR_ST64 } };
  assert.equal(A.typeGate(fakeProfile, pl, { id: "N81-A" }, inv).code, "BAD_W33_PROFILE");
  assert.equal(A.typeGate(p81, pl, { id: "N81-A" }, fakeInventory).code, "BAD_W33_INVENTORY");
});
