"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const P = require("../js/w33-storage-aware-placement.js");

function fixture() {
  const candidates = [
    { node: { id: "cheap-fragile" }, perSecond: 0.01, score: 1.00 },
    { node: { id: "stable-storage" }, perSecond: 0.012, score: 1.03 },
    { node: { id: "energy-heavy" }, perSecond: 0.009, score: 0.98 },
  ];
  return {
    engine: { place: () => candidates },
    plan: { requestedSeconds: 100 },
    forecast(candidate) {
      if (candidate.node.id === "cheap-fragile") return {
        liveStrongBlobs: 10, retainedHistoryBlobs: 10, checkpointCount: 4, checkpointBlobs: 20,
        checkpointRetentionSeconds: 100, recoveryProbability: 0.5, recoverySeconds: 30, recoveryStrongBlobs: 30,
        energyJoules: 200, irreversibleEraseBits: 1000,
      };
      if (candidate.node.id === "stable-storage") return {
        liveStrongBlobs: 8, retainedHistoryBlobs: 2, checkpointCount: 1, checkpointBlobs: 8,
        checkpointRetentionSeconds: 100, recoveryProbability: 0.02, recoverySeconds: 10, recoveryStrongBlobs: 8,
        energyJoules: 90, irreversibleEraseBits: 20,
      };
      return {
        liveStrongBlobs: 7, retainedHistoryBlobs: 1, checkpointCount: 1, checkpointBlobs: 7,
        checkpointRetentionSeconds: 100, recoveryProbability: 0.03, recoverySeconds: 10, recoveryStrongBlobs: 7,
        energyJoules: 10000, irreversibleEraseBits: 10,
      };
    },
  };
}

test("placement can prefer slightly dearer compute when persistence and recovery are cheaper", () => {
  const f = fixture();
  const ranked = P.rankStorageAwarePlacement(f.engine, f.plan, {
    forecast: f.forecast,
    // The energy-heavy candidate is deliberately cheaper in both base score and
    // strong-root storage, so this scenario must price its 10 kJ strongly enough
    // for the intended stable-storage winner. At 1e-6 USD/J it correctly wins;
    // 1e-5 USD/J makes persistence/recovery + energy jointly decisive.
    policy: { strongBlobSecondUSD: 0.00001, energyJouleUSD: 0.00001, irreversibleEraseBitUSD: 0.000001 },
  });
  assert.equal(ranked[0].node.id, "stable-storage");
  assert.ok(ranked[0].w33StoragePlacement.physical.strongBlobSeconds < ranked.find((x) => x.node.id === "cheap-fragile").w33StoragePlacement.physical.strongBlobSeconds);
  assert.ok(ranked[0].scoreWithStorage < ranked.find((x) => x.node.id === "energy-heavy").scoreWithStorage);
});

test("energy term is explicit and can reject an otherwise cheap energy-heavy candidate by ranking", () => {
  const f = fixture();
  const ranked = P.rankStorageAwarePlacement(f.engine, f.plan, {
    forecast: f.forecast,
    policy: { strongBlobSecondUSD: 0, energyJouleUSD: 0.001, irreversibleEraseBitUSD: 0 },
  });
  assert.notEqual(ranked[0].node.id, "energy-heavy");
  const heavy = ranked.find((x) => x.node.id === "energy-heavy");
  assert.equal(heavy.w33StoragePlacement.physical.energyUSD, 10);
});

test("recovery probability is bounded and all supplemental terms remain inspectable", () => {
  const f = fixture();
  assert.throws(() => P.costForecast({ perSecond: 1 }, f.plan, {
    executionSeconds: 1, liveStrongBlobs: 0, liveStrongBytes: 0, retainedHistoryBlobs: 0, retainedHistoryBytes: 0,
    checkpointCount: 0, checkpointBlobs: 0, checkpointBytes: 0, checkpointRetentionSeconds: 0,
    recoveryProbability: 1.1, recoverySeconds: 1, recoveryStrongBlobs: 0, recoveryStrongBytes: 0,
    energyJoules: 0, irreversibleEraseBits: 0,
  }, {}), /recoveryProbability/);

  const rows = P.rankStorageAwarePlacement(f.engine, f.plan, { forecast: f.forecast, policy: {} });
  assert.ok(Array.isArray(P.paretoView(rows)));
  assert.ok(rows.every((x) => Object.hasOwn(x.w33StoragePlacement.physical, "expectedRecoveryComputeUSD")));
});
