"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const M = require("../js/w33-measured-placement-loop.js");

const plan = { requestedSeconds: 10 };
const engine = {
  place() {
    return [
      { node: { id: "node-a" }, score: 1.00, perSecond: 0.01 },
      { node: { id: "node-b" }, score: 1.02, perSecond: 0.01 },
    ];
  },
};
function forecast(candidate) {
  return {
    executionSeconds: 10,
    liveStrongBlobs: 10,
    liveStrongBytes: 1000,
    retainedHistoryBlobs: 0,
    retainedHistoryBytes: 0,
    checkpointCount: 0,
    checkpointBlobs: 0,
    checkpointBytes: 0,
    checkpointRetentionSeconds: 0,
    recoveryProbability: 0,
    recoverySeconds: 0,
    recoveryStrongBlobs: 0,
    recoveryStrongBytes: 0,
    energyJoules: candidate.node.id === "node-a" ? 2 : 3,
    irreversibleEraseBits: 0,
  };
}
const policy = { strongBlobSecondUSD: 0, strongByteSecondUSD: 0, energyJouleUSD: 0.02, irreversibleEraseBitUSD: 0 };

test("RAPL adapter handles ordinary and wrapped microjoule counters", () => {
  assert.equal(M.raplDeltaJoules(1_000_000, 2_500_000).energyJoules, 1.5);
  assert.equal(M.raplDeltaJoules(9_000_000, 1_000_000, 10_000_000).energyJoules, 2);
});

test("Kepler adapter extracts cumulative joules and computes delta", () => {
  const before = "# HELP x x\nkepler_node_platform_joules_total{node=\"n\"} 10\n";
  const after = "kepler_node_platform_joules_total{node=\"n\"} 14.5\n";
  assert.equal(M.keplerDeltaJoules(before, after).energyJoules, 4.5);
});

test("closed-loop observation feeds realized energy back into next placement", () => {
  const c = new M.PlacementCalibrator({ alpha: 1 });
  let rows = M.rankMeasuredClosedLoop(engine, plan, c, { forecast, policy, limit: 2 });
  assert.equal(rows[0].node.id, "node-a");
  const pred = rows.find((x) => x.node.id === "node-a").w33StoragePlacement.physical;
  c.observe({
    nodeId: "node-a",
    predictedPhysical: pred,
    realized: {
      strongBlobSeconds: pred.strongBlobSeconds,
      recoverySeconds: pred.expectedRecoverySeconds,
      energyJoules: 20,
      irreversibleEraseBits: pred.irreversibleEraseBits,
    },
    source: "RAPL",
  });
  rows = M.rankMeasuredClosedLoop(engine, plan, c, { forecast, policy, limit: 2 });
  assert.equal(rows[0].node.id, "node-b");
  assert.equal(c.state("node-a").lastObservationPhysicallyMeasured, true);
  assert.ok(c.state("node-a").energy > 1);
});

test("fixture observations remain explicitly non-physical", () => {
  const c = new M.PlacementCalibrator({ alpha: 1 });
  const rows = M.rankMeasuredClosedLoop(engine, plan, c, { forecast, policy, limit: 2 });
  const pred = rows[0].w33StoragePlacement.physical;
  c.observe({ nodeId: rows[0].node.id, predictedPhysical: pred, realized: { strongBlobSeconds: pred.strongBlobSeconds, recoverySeconds: 0, energyJoules: pred.energyJoules, irreversibleEraseBits: 0 } });
  assert.equal(c.state(rows[0].node.id).lastObservationPhysicallyMeasured, false);
});
