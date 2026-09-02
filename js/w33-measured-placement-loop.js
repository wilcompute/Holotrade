"use strict";

// Closed-loop calibration for W33 storage-aware placement.
//
// This layer consumes realized execution telemetry and feeds calibrated
// multipliers back into the existing storage/recovery/energy/erasure-aware
// scheduler. It includes adapters for Linux RAPL counter deltas and Kepler
// Prometheus counters, plus strong-root ledger summaries.
//
// Fixture data can exercise the control loop in CI. A fixture is never labeled
// as a physical measurement; production callers must set source to RAPL,
// KEPLER, or another explicit measured source.

const Placement = require("./w33-storage-aware-placement.js");

function nneg(value, name) {
  const n = Number(value ?? 0);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`);
  return n;
}

function ratio(actual, predicted) {
  const a = nneg(actual, "actual");
  const p = nneg(predicted, "predicted");
  if (p === 0) return a === 0 ? 1 : 1;
  return a / p;
}

function raplDeltaJoules(before, after, maxRangeUj = null) {
  const b = nneg(before, "RAPL before energy_uj");
  const a = nneg(after, "RAPL after energy_uj");
  let delta = a - b;
  if (delta < 0) {
    const max = nneg(maxRangeUj, "RAPL max_energy_range_uj");
    if (!(max > b)) throw new RangeError("RAPL counter wrapped but max range is unavailable/invalid");
    delta = (max - b) + a;
  }
  return Object.freeze({ source: "RAPL", energyJoules: delta / 1e6, counterDeltaUj: delta, physicallyMeasured: true });
}

function parseKeplerPrometheus(text, metric = "kepler_node_platform_joules_total") {
  if (typeof text !== "string") throw new TypeError("Kepler Prometheus text required");
  let total = 0; let count = 0;
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const m = line.match(/^([^\s{]+)(?:\{[^}]*\})?\s+([-+0-9.eE]+)$/);
    if (!m || m[1] !== metric) continue;
    const value = Number(m[2]);
    if (!Number.isFinite(value) || value < 0) throw new RangeError("invalid Kepler counter");
    total += value; count++;
  }
  if (!count) throw new Error(`Kepler metric ${metric} not found`);
  return Object.freeze({ source: "KEPLER", metric, cumulativeJoules: total, seriesCount: count, physicallyMeasured: true });
}

function keplerDeltaJoules(beforeText, afterText, metric) {
  const b = parseKeplerPrometheus(beforeText, metric);
  const a = parseKeplerPrometheus(afterText, metric);
  if (a.cumulativeJoules < b.cumulativeJoules) throw new RangeError("Kepler cumulative counter decreased");
  return Object.freeze({ source: "KEPLER", metric: a.metric, energyJoules: a.cumulativeJoules - b.cumulativeJoules, physicallyMeasured: true });
}

function strongRootRealization(summary) {
  if (!summary || summary.schema !== "holotrade.w33-strong-root-storage.v1") throw new TypeError("strong-root storage summary required");
  return Object.freeze({
    strongBlobSeconds: nneg(summary.strongBlobSeconds, "strongBlobSeconds"),
    strongByteSeconds: nneg(summary.strongByteSeconds, "strongByteSeconds"),
  });
}

class PlacementCalibrator {
  constructor({ alpha = 0.35 } = {}) {
    if (!(alpha > 0 && alpha <= 1)) throw new RangeError("alpha must lie in (0,1]");
    this.alpha = alpha;
    this.byNode = new Map();
  }

  state(nodeId) {
    return this.byNode.get(String(nodeId)) || Object.freeze({ storage: 1, recovery: 1, energy: 1, erasure: 1, observations: 0 });
  }

  updateFactor(oldValue, observedRatio) {
    const bounded = Math.max(0.05, Math.min(20, observedRatio));
    return (1 - this.alpha) * oldValue + this.alpha * bounded;
  }

  observe({ nodeId, predictedPhysical, realized, source = "FIXTURE" }) {
    if (!predictedPhysical || !realized) throw new TypeError("predictedPhysical and realized required");
    const old = this.state(nodeId);
    const next = Object.freeze({
      storage: this.updateFactor(old.storage, ratio(realized.strongBlobSeconds, predictedPhysical.strongBlobSeconds)),
      recovery: this.updateFactor(old.recovery, ratio(realized.recoverySeconds, predictedPhysical.expectedRecoverySeconds)),
      energy: this.updateFactor(old.energy, ratio(realized.energyJoules, predictedPhysical.energyJoules)),
      erasure: this.updateFactor(old.erasure, ratio(realized.irreversibleEraseBits, predictedPhysical.irreversibleEraseBits)),
      observations: old.observations + 1,
      lastSource: String(source),
      lastObservationPhysicallyMeasured: source !== "FIXTURE",
    });
    this.byNode.set(String(nodeId), next);
    return next;
  }

  apply(nodeId, forecast) {
    const c = this.state(nodeId);
    const scale = (x, m) => nneg(x, "forecast component") * m;
    return Object.freeze({
      ...forecast,
      liveStrongBlobs: scale(forecast.liveStrongBlobs, c.storage),
      liveStrongBytes: scale(forecast.liveStrongBytes, c.storage),
      retainedHistoryBlobs: scale(forecast.retainedHistoryBlobs, c.storage),
      retainedHistoryBytes: scale(forecast.retainedHistoryBytes, c.storage),
      checkpointBlobs: scale(forecast.checkpointBlobs, c.storage),
      checkpointBytes: scale(forecast.checkpointBytes, c.storage),
      recoverySeconds: scale(forecast.recoverySeconds, c.recovery),
      recoveryStrongBlobs: scale(forecast.recoveryStrongBlobs, c.storage),
      recoveryStrongBytes: scale(forecast.recoveryStrongBytes, c.storage),
      energyJoules: scale(forecast.energyJoules, c.energy),
      irreversibleEraseBits: scale(forecast.irreversibleEraseBits, c.erasure),
    });
  }

  snapshot() {
    return Object.freeze({
      schema: "holotrade.w33-placement-calibration.v1",
      alpha: this.alpha,
      nodes: Object.freeze(Object.fromEntries([...this.byNode.entries()].sort(([a],[b]) => a.localeCompare(b)))),
    });
  }
}

function rankMeasuredClosedLoop(executionEngine, plan, calibrator, options = {}) {
  if (!(calibrator instanceof PlacementCalibrator)) throw new TypeError("PlacementCalibrator required");
  const baseForecast = options.forecast;
  if (typeof baseForecast !== "function") throw new TypeError("base forecast callback required");
  return Placement.rankStorageAwarePlacement(executionEngine, plan, {
    ...options,
    forecast(candidate, p) {
      return calibrator.apply(candidate.node.id, baseForecast(candidate, p));
    },
  });
}

module.exports = {
  raplDeltaJoules,
  parseKeplerPrometheus,
  keplerDeltaJoules,
  strongRootRealization,
  PlacementCalibrator,
  rankMeasuredClosedLoop,
};
