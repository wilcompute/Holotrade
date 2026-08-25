"use strict";

// A read-only policy evaluator. It consumes observed per-CPU utilisation and
// emits recommendations in memory; it never changes affinity, cgroups, quotas,
// process priority, or workload placement. The "on" arm is consequently a
// counterfactual one-step model output, not an observed intervention outcome.

const { PricingEngine, TARGET_BAND, CLAMP } = require("../js/pricing.js");
const { canonicalSha256 } = require("./procfs.js");

const PRICE_ELASTICITY = -1.9;
const RESPONSE_FRACTION = 0.10;

function mean(xs) {
  return xs.length ? xs.reduce((sum, x) => sum + x, 0) / xs.length : 0;
}

function gini(xs) {
  const values = xs.map(Number).filter(Number.isFinite).sort((a, b) => a - b);
  const n = values.length;
  if (!n) return 0;
  const sum = values.reduce((a, b) => a + b, 0);
  if (sum <= 0) return 0;
  let weighted = 0;
  for (let i = 0; i < n; i++) weighted += (i + 1) * values[i];
  return (2 * weighted) / (n * sum) - (n + 1) / n;
}

function demandMultiplier(utilisation) {
  const probe = Object.create(PricingEngine.prototype);
  probe.balancerEnabled = true;
  return probe.demandMultiplier({
    utilisation,
    // Swing is deliberately unavailable in /proc/stat; equal EMA excludes an
    // invented thermal-cycle surcharge from the shadow recommendation.
    utilisationEMA: utilisation,
    hardware: { thermalSensitivity: 1 },
  });
}

function cappedProportional(total, weights) {
  const out = Array(weights.length).fill(0);
  let remaining = weights.map((_, i) => i);
  let remainingTotal = Math.max(0, Math.min(weights.length, total));
  while (remaining.length) {
    const weightSum = remaining.reduce((sum, i) => sum + weights[i], 0);
    if (!(weightSum > 0)) {
      const each = remainingTotal / remaining.length;
      for (const i of remaining) out[i] = each;
      break;
    }
    const saturated = remaining.filter((i) => remainingTotal * weights[i] / weightSum >= 1);
    if (!saturated.length) {
      for (const i of remaining) out[i] = remainingTotal * weights[i] / weightSum;
      break;
    }
    for (const i of saturated) {
      out[i] = 1;
      remainingTotal -= 1;
    }
    const saturatedSet = new Set(saturated);
    remaining = remaining.filter((i) => !saturatedSet.has(i));
  }
  return out;
}

function oneStepRecommendation(observed, { responseFraction = RESPONSE_FRACTION, commonEnergyMultiplier = 1 } = {}) {
  if (!Array.isArray(observed) || observed.length < 2) throw new TypeError("at least two observed CPU lanes are required");
  if (observed.some((x) => !Number.isFinite(x))) throw new TypeError("observed CPU lanes must be finite");
  if (!Number.isFinite(responseFraction) || responseFraction < 0 || responseFraction > 1) {
    throw new RangeError("responseFraction must be in [0,1]");
  }
  if (!Number.isFinite(commonEnergyMultiplier) || commonEnergyMultiplier <= 0) {
    throw new RangeError("commonEnergyMultiplier must be positive");
  }
  const lanes = observed.map((x) => Math.max(0, Math.min(1, Number(x))));
  const multipliers = lanes.map(demandMultiplier);
  // E is shown explicitly even though it cancels: every lane here is in one
  // host/price zone, so multiplying every price by the same positive scalar
  // cannot alter relative-price allocation.
  const prices = multipliers.map((d) => commonEnergyMultiplier * d);
  const weights = prices.map((p) => Math.pow(Math.max(1e-12, p), PRICE_ELASTICITY));
  const target = cappedProportional(lanes.reduce((a, b) => a + b, 0), weights);
  const proposed = lanes.map((u, i) => u + (target[i] - u) * responseFraction);
  return {
    observed: lanes,
    proposed,
    demandMultipliers: multipliers,
    commonEnergyMultiplier,
    totalObserved: lanes.reduce((a, b) => a + b, 0),
    totalProposed: proposed.reduce((a, b) => a + b, 0),
    observedGini: gini(lanes),
    proposedGini: gini(proposed),
    observedMax: Math.max(...lanes),
    proposedMax: Math.max(...proposed),
    inBandObserved: lanes.filter((u) => u >= TARGET_BAND.low && u <= TARGET_BAND.high).length,
    inBandProposed: proposed.filter((u) => u >= TARGET_BAND.low && u <= TARGET_BAND.high).length,
  };
}

function median(xs) {
  const sorted = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function marketCalibration(rows) {
  const prices = rows.map((row) => row.priceGBPPerMWh);
  const baseline = median(prices);
  const records = rows.map((row) => {
    const ratio = Math.max(0.05, row.priceGBPPerMWh / baseline);
    const multiplier = Math.max(CLAMP.energy[0], Math.min(CLAMP.energy[1], Math.pow(ratio, 0.55)));
    return { ...row, priceRatioToTraceMedian: ratio, commonEnergyMultiplier: multiplier };
  });
  const totalVolume = rows.reduce((sum, row) => sum + row.volumeMWh, 0);
  const vwap = totalVolume > 0
    ? rows.reduce((sum, row) => sum + row.priceGBPPerMWh * row.volumeMWh, 0) / totalVolume
    : null;
  return {
    baseline: { statistic: "trace median", priceGBPPerMWh: baseline },
    count: records.length,
    minPriceGBPPerMWh: Math.min(...prices),
    maxPriceGBPPerMWh: Math.max(...prices),
    meanPriceGBPPerMWh: mean(prices),
    volumeWeightedPriceGBPPerMWh: vwap,
    meanCommonEnergyMultiplier: mean(records.map((r) => r.commonEnergyMultiplier)),
    minCommonEnergyMultiplier: Math.min(...records.map((r) => r.commonEnergyMultiplier)),
    maxCommonEnergyMultiplier: Math.max(...records.map((r) => r.commonEnergyMultiplier)),
    records,
  };
}

function runShadowReplay(hostFixture, marketFixture) {
  const market = marketCalibration(marketFixture.rows);
  const rows = hostFixture.observations.map((observation, i) => {
    const marketRow = market.records[i % market.records.length];
    const pair = oneStepRecommendation(observation.observed.perCpuBusyFraction, {
      commonEnergyMultiplier: marketRow.commonEnergyMultiplier,
    });
    return {
      sequence: observation.sequence,
      telemetryIntervalStart: observation.intervalStart,
      telemetryIntervalEnd: observation.intervalEnd,
      marketOrdinal: i % market.records.length,
      marketStartTime: marketRow.startTime,
      // These streams are deliberately not represented as co-temporal.
      streamsTimeAligned: false,
      priceGBPPerMWh: marketRow.priceGBPPerMWh,
      commonEnergyMultiplier: marketRow.commonEnergyMultiplier,
      observed: {
        source: "MEASURED_LOCAL_KERNEL_COUNTERS",
        laneCount: pair.observed.length,
        utilisationGini: pair.observedGini,
        maximumLaneUtilisation: pair.observedMax,
        aggregateLaneUtilisation: pair.totalObserved,
      },
      counterfactual: {
        source: "COUNTERFACTUAL_ONE_STEP_POLICY_MODEL",
        utilisationGini: pair.proposedGini,
        maximumLaneUtilisation: pair.proposedMax,
        aggregateLaneUtilisation: pair.totalProposed,
        giniDifference: pair.observedGini - pair.proposedGini,
        recommendedUtilisation: pair.proposed,
      },
    };
  });
  const differences = rows.map((row) => row.counterfactual.giniDifference);
  const body = {
    schema: "holotrade.telemetry-shadow.replay.v1",
    evidence: "MEASURED_INPUTS_COUNTERFACTUAL_OUTPUTS",
    actuation: "NONE",
    inputCommitments: {
      hostFixtureSha256: hostFixture.fixtureSha256,
      marketFixtureSha256: marketFixture.fixtureSha256,
    },
    design: {
      paired: true,
      offArm: "observed per-CPU persistence; no recommendation applied",
      onArm: "one normalized 0.10 response step using the repository demand multiplier and -1.9 price elasticity",
      conservedQuantity: "sum of per-CPU busy fractions within each interval",
      thermalSwingTreatment: "not measured; utilisationEMA equals current utilisation so no swing surcharge is invented",
      priceTreatment: "official price drives one common dimensionless E multiplier; it cancels from within-host relative allocation",
      timeAlignment: "host telemetry and the historical market trace are independent streams paired by ordinal only, not co-temporal observations",
      fieldOutcome: false,
    },
    marketSummary: {
      count: market.count,
      baseline: market.baseline,
      minPriceGBPPerMWh: market.minPriceGBPPerMWh,
      maxPriceGBPPerMWh: market.maxPriceGBPPerMWh,
      meanPriceGBPPerMWh: market.meanPriceGBPPerMWh,
      volumeWeightedPriceGBPPerMWh: market.volumeWeightedPriceGBPPerMWh,
      meanCommonEnergyMultiplier: market.meanCommonEnergyMultiplier,
      minCommonEnergyMultiplier: market.minCommonEnergyMultiplier,
      maxCommonEnergyMultiplier: market.maxCommonEnergyMultiplier,
    },
    telemetrySummary: {
      observationCount: rows.length,
      logicalCpuLanes: rows[0] ? rows[0].observed.laneCount : 0,
      meanObservedHostCpuBusyFraction: mean(hostFixture.observations.map((x) => x.observed.cpuBusyFraction)),
      meanObservedLaneGini: mean(rows.map((row) => row.observed.utilisationGini)),
    },
    counterfactualSummary: {
      meanRecommendedLaneGini: mean(rows.map((row) => row.counterfactual.utilisationGini)),
      meanPairedGiniDifference: mean(differences),
      improvedIntervals: differences.filter((x) => x > 1e-12).length,
      unchangedIntervals: differences.filter((x) => Math.abs(x) <= 1e-12).length,
      worsenedIntervals: differences.filter((x) => x < -1e-12).length,
      meanObservedMaximumLaneUtilisation: mean(rows.map((row) => row.observed.maximumLaneUtilisation)),
      meanRecommendedMaximumLaneUtilisation: mean(rows.map((row) => row.counterfactual.maximumLaneUtilisation)),
    },
    rowsSha256: canonicalSha256(rows),
    rows,
  };
  return { ...body, certificateSha256: canonicalSha256(body) };
}

function verifyReplayCertificate(certificate, hostFixture, marketFixture) {
  if (!certificate || certificate.schema !== "holotrade.telemetry-shadow.replay.v1") return false;
  const { certificateSha256, ...body } = certificate;
  if (certificateSha256 !== canonicalSha256(body)) return false;
  if (certificate.rowsSha256 !== canonicalSha256(certificate.rows)) return false;
  const replay = runShadowReplay(hostFixture, marketFixture);
  return replay.certificateSha256 === certificate.certificateSha256;
}

module.exports = {
  PRICE_ELASTICITY,
  RESPONSE_FRACTION,
  mean,
  median,
  gini,
  demandMultiplier,
  cappedProportional,
  oneStepRecommendation,
  marketCalibration,
  runShadowReplay,
  verifyReplayCertificate,
};
