const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));
const R = require(path.join(root, "js/w33-profiled-receipt.js"));
const Receipt = require(path.join(root, "runtime/receipt.js"));

function fixture(machineType = P.MACHINE_TYPE.CIRCUIT_ST81) {
  const plan = new ExecutionPlan({
    name: "receipt-bind",
    workloadId: "llm-train",
    requestedSeconds: 2,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
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
  return { plan, node, engine, profile, vm: launched.vm, contract };
}

test("receipt binding commits plan, profile, VM and deployment identities", () => {
  const f = fixture();
  const b = R.bindReceiptMetadata(f.plan, f.profile, f.vm, f.contract);
  assert.equal(b.planDigest, f.plan.digest);
  assert.equal(b.profileDigest, f.profile.digest);
  assert.equal(b.machineType, P.MACHINE_TYPE.CIRCUIT_ST81);
  assert.equal(b.logicalDimension, 81);
  assert.equal(b.deploymentDigest, f.contract.deploymentDigest);
  assert.equal(b.runtimeRetype, "FORBIDDEN");
  assert.ok(R.verifyReceiptMetadata(b, f.plan, f.profile, f.vm, f.contract));
});

test("generic signed-receipt payload carries the W33 binding inside signed metadata", () => {
  const f = fixture();
  const metadata = R.attachToReceiptMetadata({ market: "demo" }, f.plan, f.profile, f.vm, f.contract);
  const payload = Receipt.deliveryPayload({
    executionId: "exec-1",
    nodeId: f.node.id,
    outcome: "settled",
    artifacts: [{ role: "output", bytes: 1, digest: `sha256:${"a".repeat(64)}` }],
    capabilities: { findings: [] },
    startedAtMs: 1000,
    finishedAtMs: 2000,
    nonce: "nonce-1",
    metadata,
  });
  assert.deepEqual(payload.metadata.w33, metadata.w33);
  assert.ok(R.verifyReceiptMetadata(payload.metadata.w33, f.plan, f.profile, f.vm, f.contract));
});

test("cross-carrier receipt replay fails closed", () => {
  const f81 = fixture(P.MACHINE_TYPE.CIRCUIT_ST81);
  const b81 = R.bindReceiptMetadata(f81.plan, f81.profile, f81.vm, f81.contract);
  const profile64 = P.bind(f81.plan, P.MACHINE_TYPE.PAIR_ST64);
  const fake64vm = { ...f81.vm, w33ProfileDigest: profile64.digest,
    w33MachineType: profile64.machineType, w33LogicalDimension: 64 };
  assert.equal(R.verifyReceiptMetadata(b81, f81.plan, profile64, fake64vm, null), false);
});

test("tampering with machine type, dimension or deployment digest invalidates receipt binding", () => {
  const f = fixture();
  const b = R.bindReceiptMetadata(f.plan, f.profile, f.vm, f.contract);
  assert.equal(R.verifyReceiptMetadata({ ...b, logicalDimension: 64 }, f.plan, f.profile, f.vm, f.contract), false);
  assert.equal(R.verifyReceiptMetadata({ ...b, machineType: P.MACHINE_TYPE.PAIR_ST64 }, f.plan, f.profile, f.vm, f.contract), false);
  assert.equal(R.verifyReceiptMetadata({ ...b, deploymentDigest: "sha256:wrong" }, f.plan, f.profile, f.vm, f.contract), false);
});
