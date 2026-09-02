"use strict";

// Storage-aware physical placement for W33 executions.
//
// The ordinary ExecutionEngine score already prices requested compute and cold
// start. This wrapper adds explicit forecasted costs that were previously only
// visible at settlement time:
//   - strong-root blob-seconds / byte-seconds,
//   - checkpoint retention and expected recovery storage,
//   - expected recovery compute time,
//   - measured/forecast energy policy cost,
//   - irreversible erasure policy cost.
//
// Every term is returned separately.  No term is called thermodynamic unless
// the caller explicitly supplied a measured physical-energy tariff.

const Storage = require("./w33-strong-root-storage.js");

function finiteNonnegative(value, name) {
  const n = Number(value ?? 0);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`);
  return n;
}

function forecastFor(candidate, plan, options) {
  const f = typeof options.forecast === "function"
    ? options.forecast(candidate, plan)
    : candidate.node && candidate.node.w33StorageForecast;
  if (!f || typeof f !== "object") throw new TypeError(`storage forecast required for candidate ${candidate.node && candidate.node.id}`);
  return Object.freeze({
    executionSeconds: finiteNonnegative(f.executionSeconds ?? plan.requestedSeconds, "executionSeconds"),
    liveStrongBlobs: finiteNonnegative(f.liveStrongBlobs, "liveStrongBlobs"),
    liveStrongBytes: finiteNonnegative(f.liveStrongBytes, "liveStrongBytes"),
    retainedHistoryBlobs: finiteNonnegative(f.retainedHistoryBlobs, "retainedHistoryBlobs"),
    retainedHistoryBytes: finiteNonnegative(f.retainedHistoryBytes, "retainedHistoryBytes"),
    checkpointCount: finiteNonnegative(f.checkpointCount, "checkpointCount"),
    checkpointBlobs: finiteNonnegative(f.checkpointBlobs, "checkpointBlobs"),
    checkpointBytes: finiteNonnegative(f.checkpointBytes, "checkpointBytes"),
    checkpointRetentionSeconds: finiteNonnegative(f.checkpointRetentionSeconds, "checkpointRetentionSeconds"),
    recoveryProbability: finiteNonnegative(f.recoveryProbability, "recoveryProbability"),
    recoverySeconds: finiteNonnegative(f.recoverySeconds, "recoverySeconds"),
    recoveryStrongBlobs: finiteNonnegative(f.recoveryStrongBlobs, "recoveryStrongBlobs"),
    recoveryStrongBytes: finiteNonnegative(f.recoveryStrongBytes, "recoveryStrongBytes"),
    energyJoules: finiteNonnegative(f.energyJoules, "energyJoules"),
    irreversibleEraseBits: finiteNonnegative(f.irreversibleEraseBits, "irreversibleEraseBits"),
  });
}

function costForecast(candidate, plan, forecast, policy = {}) {
  if (forecast.recoveryProbability > 1) throw new RangeError("recoveryProbability must be <= 1");
  const blobTariff = finiteNonnegative(policy.strongBlobSecondUSD, "strongBlobSecondUSD");
  const byteTariff = finiteNonnegative(policy.strongByteSecondUSD, "strongByteSecondUSD");
  const jouleTariff = finiteNonnegative(policy.energyJouleUSD, "energyJouleUSD");
  const eraseTariff = finiteNonnegative(policy.irreversibleEraseBitUSD, "irreversibleEraseBitUSD");

  const liveBlobSeconds = forecast.liveStrongBlobs * forecast.executionSeconds;
  const liveByteSeconds = forecast.liveStrongBytes * forecast.executionSeconds;
  const historyBlobSeconds = forecast.retainedHistoryBlobs * forecast.executionSeconds;
  const historyByteSeconds = forecast.retainedHistoryBytes * forecast.executionSeconds;
  const checkpointBlobSeconds = forecast.checkpointCount * forecast.checkpointBlobs * forecast.checkpointRetentionSeconds;
  const checkpointByteSeconds = forecast.checkpointCount * forecast.checkpointBytes * forecast.checkpointRetentionSeconds;
  const expectedRecoveryBlobSeconds = forecast.recoveryProbability * forecast.recoveryStrongBlobs * forecast.recoverySeconds;
  const expectedRecoveryByteSeconds = forecast.recoveryProbability * forecast.recoveryStrongBytes * forecast.recoverySeconds;
  const strongBlobSeconds = liveBlobSeconds + historyBlobSeconds + checkpointBlobSeconds + expectedRecoveryBlobSeconds;
  const strongByteSeconds = liveByteSeconds + historyByteSeconds + checkpointByteSeconds + expectedRecoveryByteSeconds;

  const storageUSD = strongBlobSeconds * blobTariff + strongByteSeconds * byteTariff;
  const expectedRecoveryComputeUSD = forecast.recoveryProbability * forecast.recoverySeconds * finiteNonnegative(candidate.perSecond, "candidate.perSecond");
  const energyUSD = forecast.energyJoules * jouleTariff;
  const erasureUSD = forecast.irreversibleEraseBits * eraseTariff;
  const supplementalUSD = storageUSD + expectedRecoveryComputeUSD + energyUSD + erasureUSD;

  return Object.freeze({
    schema: "holotrade.w33-storage-aware-placement-cost.v1",
    strongBlobSeconds,
    strongByteSeconds,
    expectedRecoverySeconds: forecast.recoveryProbability * forecast.recoverySeconds,
    energyJoules: forecast.energyJoules,
    irreversibleEraseBits: forecast.irreversibleEraseBits,
    storageUSD,
    expectedRecoveryComputeUSD,
    energyUSD,
    erasureUSD,
    supplementalUSD,
    policy: Object.freeze({ strongBlobSecondUSD: blobTariff, strongByteSecondUSD: byteTariff, energyJouleUSD: jouleTariff, irreversibleEraseBitUSD: eraseTariff }),
  });
}

function rankStorageAwarePlacement(executionEngine, plan, options = {}) {
  if (!executionEngine || typeof executionEngine.place !== "function") throw new TypeError("ExecutionEngine with place() required");
  const base = executionEngine.place(plan, { limit: options.baseLimit || 32 });
  const rows = base.map((candidate) => {
    const forecast = forecastFor(candidate, plan, options);
    const physical = costForecast(candidate, plan, forecast, options.policy || {});
    const scoreWithStorage = candidate.score + physical.supplementalUSD;
    return Object.freeze({
      ...candidate,
      w33StoragePlacement: Object.freeze({ forecast, physical }),
      scoreWithStorage,
    });
  });
  rows.sort((a, b) => a.scoreWithStorage - b.scoreWithStorage || String(a.node.id).localeCompare(String(b.node.id)));
  return Object.freeze(rows.slice(0, options.limit || 8));
}

function paretoView(rows) {
  return Storage.storageParetoFrontier(rows.map((row) => Object.freeze({
    nodeId: row.node.id,
    latencySeconds: row.w33StoragePlacement.forecast.executionSeconds + row.w33StoragePlacement.physical.expectedRecoverySeconds,
    strongBlobSeconds: row.w33StoragePlacement.physical.strongBlobSeconds,
    irreversibleEraseBits: row.w33StoragePlacement.physical.irreversibleEraseBits,
  })));
}

module.exports = {
  forecastFor,
  costForecast,
  rankStorageAwarePlacement,
  paretoView,
};
