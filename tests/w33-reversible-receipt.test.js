const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));
const Reversible = require(path.join(root, "js/reversible-compute-settlement.js"));
const Bound = require(path.join(root, "js/w33-reversible-receipt.js"));
const Receipt = require(path.join(root, "runtime/receipt.js"));

function fixture() {
  const plan = new ExecutionPlan({
    name: "w33-reversible-receipt",
    workloadId: "llm-train",
    requestedSeconds: 2,
    artifacts: [{ name: "img", digest: "sha256:demo" }],
  });
  const node = { id: "n81" };
  const base = {
    place: () => [{ node, score: 1 }],
    launch: (_plan, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }),
  };
  const registry = new X.W33HostRegistry();
  registry.register(node.id, P.MACHINE_TYPE.CIRCUIT_ST81);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const launched = engine.launch(plan, profile, node);
  assert.ok(launched.ok);
  const contract = engine.compileGoMicroVM(plan, profile);
  const ledger = new Reversible.HistoryLedger({
    planDigest: plan.digest,
    profileDigest: profile.digest,
  });
  ledger.recordCompute({ logicalOps: 24, historyBitsCreated: 128, label: "compute" });
  ledger.recordUncompute({ logicalOps: 12, historyBitsRetired: 64, label: "uncompute" });
  ledger.discardHistory({ bits: 64, temperatureK: 300, label: "explicit-discard" });
  return { plan, node, profile, vm: launched.vm, contract, ledger };
}

test("history accounting is committed alongside W33 carrier identity", () => {
  const f = fixture();
  const metadata = Bound.attachToReceiptMetadata({ market: "demo" }, f.plan, f.profile, f.vm, f.contract, f.ledger);
  assert.equal(metadata.w33.profileDigest, f.profile.digest);
  assert.equal(metadata.reversibleHistory.planDigest, f.plan.digest);
  assert.equal(metadata.reversibleHistory.profileDigest, f.profile.digest);
  assert.match(metadata.reversibleHistory.accountingDigest, /^sha256:[0-9a-f]{64}$/);
  assert.ok(Bound.verifyReceiptMetadata(metadata, f.plan, f.profile, f.vm, f.contract, f.ledger));
});

test("generic signed-receipt payload contains both W33 and history commitments inside metadata", () => {
  const f = fixture();
  const metadata = Bound.attachToReceiptMetadata({}, f.plan, f.profile, f.vm, f.contract, f.ledger);
  const payload = Receipt.deliveryPayload({
    executionId: "exec-reversible-1",
    nodeId: f.node.id,
    outcome: "settled",
    artifacts: [{ role: "output", bytes: 1, digest: `sha256:${"b".repeat(64)}` }],
    capabilities: { findings: [] },
    startedAtMs: 1000,
    finishedAtMs: 2000,
    nonce: "nonce-reversible-1",
    metadata,
  });
  assert.deepEqual(payload.metadata.w33, metadata.w33);
  assert.deepEqual(payload.metadata.reversibleHistory, metadata.reversibleHistory);
  assert.ok(Bound.verifyReceiptMetadata(payload.metadata, f.plan, f.profile, f.vm, f.contract, f.ledger));
});

test("history tampering and cross-profile ledger reuse fail closed", () => {
  const f = fixture();
  const metadata = Bound.attachToReceiptMetadata({}, f.plan, f.profile, f.vm, f.contract, f.ledger);
  const tampered = {
    ...metadata,
    reversibleHistory: {
      ...metadata.reversibleHistory,
      accountingDigest: `sha256:${"0".repeat(64)}`,
    },
  };
  assert.equal(Bound.verifyReceiptMetadata(tampered, f.plan, f.profile, f.vm, f.contract, f.ledger), false);

  const wrong = new Reversible.HistoryLedger({
    planDigest: f.plan.digest,
    profileDigest: `sha256:${"f".repeat(64)}`,
  });
  assert.throws(
    () => Bound.attachToReceiptMetadata({}, f.plan, f.profile, f.vm, f.contract, wrong),
    /profile digest does not match/,
  );
});
