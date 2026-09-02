const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const R = require(path.join(root, "js/reversible-compute-settlement.js"));

test("only DISCARD_HISTORY contributes a Landauer floor", () => {
  const ledger = new R.HistoryLedger({ planDigest: "plan:demo" });
  ledger.recordCompute({ logicalOps: 24, historyBitsCreated: 128 });
  ledger.retainHistory({ bits: 128, seconds: 2 });
  ledger.recordUncompute({ logicalOps: 12, historyBitsRetired: 64 });
  assert.equal(ledger.landauerFloorJoules, 0);

  ledger.discardHistory({ bits: 64, temperatureK: 300 });
  const expected = 64 * R.K_B * 300 * R.LN2;
  assert.ok(Math.abs(ledger.landauerFloorJoules - expected) <= expected * 1e-12);
  assert.equal(ledger.liveHistoryBits, 0);
  assert.equal(ledger.discardedBits, 64);
});

test("theoretical erasure floor never overwrites measured device joules", () => {
  const ledger = new R.HistoryLedger();
  ledger.recordCompute({ historyBitsCreated: 10 });
  ledger.discardHistory({ bits: 10, temperatureK: 300 });
  const base = { id: "RX-demo", cost: 1.25, joules: 1234 };
  const receipt = R.extendReceipt(base, ledger);
  assert.equal(receipt.joules, 1234);
  assert.equal(receipt.modeledDeviceJoules, 1234);
  assert.equal(receipt.reversibleHistory.thermodynamics.floorIsMeasuredEnergy, false);
  assert.ok(receipt.landauerFloorJoules > 0);
});

test("explicit tariffs price compute, retention and erasure without pretending they are physics constants", () => {
  const ledger = new R.HistoryLedger({
    tariffs: {
      reversibleOpUSD: 0.01,
      historyBitSecondUSD: 0.001,
      discardBitUSD: 0.1,
    },
  });
  ledger.recordCompute({ logicalOps: 2, historyBitsCreated: 4 });
  ledger.retainHistory({ bits: 4, seconds: 3 });
  ledger.recordUncompute({ logicalOps: 1, historyBitsRetired: 2 });
  ledger.discardHistory({ bits: 2, temperatureK: 300 });
  const charges = ledger.charges();
  assert.equal(charges.reversibleComputeUSD, 0.03);
  assert.equal(charges.historyRetentionUSD, 0.012);
  assert.equal(charges.discardHistoryUSD, 0.2);
  assert.ok(Math.abs(charges.supplementalUSD - 0.242) < 1e-12);
});

test("settleWithHistory composes with the existing Holotrade settlement boundary", () => {
  const ledger = new R.HistoryLedger({ profileDigest: "sha256:w33" });
  ledger.recordCompute({ logicalOps: 1, historyBitsCreated: 8 });
  ledger.discardHistory({ bits: 8, temperatureK: 290 });
  const plan = {};
  const engine = {
    settle(vm, receivedPlan, node) {
      assert.equal(receivedPlan, plan);
      return { id: "RX-1", cost: 3.5, joules: 77, vmId: vm.id, nodeId: node.id };
    },
  };
  const receipt = R.settleWithHistory(engine, { id: "vm1" }, plan, { id: "n1" }, ledger);
  assert.equal(plan.receipt, receipt);
  assert.equal(receipt.baseExecutionCost, 3.5);
  assert.equal(receipt.joules, 77);
  assert.equal(receipt.reversibleHistory.profileDigest, "sha256:w33");
});

test("irreversible erasure fails closed when history is absent", () => {
  const ledger = new R.HistoryLedger();
  ledger.recordCompute({ historyBitsCreated: 3 });
  assert.throws(() => ledger.discardHistory({ bits: 4, temperatureK: 300 }), /more history bits than are live/);
  assert.throws(() => ledger.discardHistory({ bits: 1, temperatureK: 0 }), /positive/);
});

test("measured erasure energy is optional and reported only as a comparison to the floor", () => {
  const ledger = new R.HistoryLedger();
  ledger.recordCompute({ historyBitsCreated: 1 });
  ledger.discardHistory({ bits: 1, temperatureK: 300, measuredJoules: 1e-18 });
  const thermo = ledger.summary().thermodynamics;
  assert.equal(thermo.measuredErasureJoules, 1e-18);
  assert.ok(thermo.measuredToLandauerRatio > 1);
  assert.equal(thermo.floorIsMeasuredEnergy, false);
});

test("three-objective Pareto frontier keeps genuine time/history/erasure tradeoffs", () => {
  const candidates = [
    { id: "fast-history", latencySeconds: 1, peakHistoryBits: 100, irreversibleEraseBits: 0 },
    { id: "balanced", latencySeconds: 2, peakHistoryBits: 40, irreversibleEraseBits: 4 },
    { id: "slow-clean", latencySeconds: 4, peakHistoryBits: 10, irreversibleEraseBits: 0 },
    { id: "dominated", latencySeconds: 5, peakHistoryBits: 120, irreversibleEraseBits: 8 },
    { id: "erase-heavy", latencySeconds: 1.5, peakHistoryBits: 20, irreversibleEraseBits: 20 },
  ];
  const ids = R.paretoFrontier(candidates).map((x) => x.id);
  assert.deepEqual(ids, ["fast-history", "erase-heavy", "balanced", "slow-clean"]);
  assert.ok(!ids.includes("dominated"));
});
