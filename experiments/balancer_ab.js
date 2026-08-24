#!/usr/bin/env node
"use strict";

// Reproducible, paired A/B experiment for the utilisation balancer.
// This is simulated evidence, never a production benchmark. Each seed
// builds the same initial fleet twice; the only changed switch is the
// two-sided demand multiplier.

const path = require("node:path");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
global.window = global;

const S = require(path.join(root, "js/substrate.js"));
const catalog = require(path.join(root, "data/catalog.js"));
const EnergyEngine = require(path.join(root, "js/energy.js"));
const { Fleet } = require(path.join(root, "js/fleet.js"));
const { PricingEngine } = require(path.join(root, "js/pricing.js"));

function build(size, seed) {
  const energy = new EnergyEngine(catalog.DATACENTERS, `${seed}-energy`);
  const fleet = new Fleet({
    datacenters: catalog.DATACENTERS,
    hardware: catalog.HARDWARE,
    workloads: catalog.WORKLOADS,
    operators: catalog.OPERATORS,
    size,
    seed,
  });
  const pricing = new PricingEngine(fleet, energy, catalog.WORKLOADS);
  return { energy, fleet, pricing };
}

function runArm({ seed, enabled, size = 220, steps = 500, stepSeconds = 60 }) {
  const { energy, fleet, pricing } = build(size, seed);
  pricing.balancerEnabled = enabled;
  const dtHours = stepSeconds / 3600;
  for (let i = 0; i < steps; i++) {
    energy.tick(stepSeconds);
    pricing.applyDemandResponse(dtHours, { workloadId: "llm-train" });
    fleet.tick(dtHours);
  }
  pricing.refreshFleetStats();
  return {
    gini: pricing.fleetStats.gini,
    meanUtilisation: pricing.fleetStats.meanUtilisation,
    inBandFraction: pricing.fleetStats.inBandFraction,
  };
}

function mean(xs) {
  return xs.reduce((sum, x) => sum + x, 0) / xs.length;
}

function sampleSd(xs) {
  if (xs.length < 2) return 0;
  const m = mean(xs);
  return Math.sqrt(xs.reduce((sum, x) => sum + (x - m) ** 2, 0) / (xs.length - 1));
}

function ci95(xs) {
  const m = mean(xs);
  // t_0.975,63 for the default 64-seed packet; normal approximation
  // is used for other n and identified in the output.
  const critical = xs.length === 64 ? 1.9983405425 : 1.9599639845;
  const half = critical * sampleSd(xs) / Math.sqrt(xs.length);
  return [m - half, m + half];
}

function runExperiment({ seeds = 64, size = 220, steps = 500, stepSeconds = 60 } = {}) {
  const rows = [];
  for (let i = 0; i < seeds; i++) {
    const seed = `balancer-paired-${String(i + 1).padStart(3, "0")}`;
    const on = runArm({ seed, enabled: true, size, steps, stepSeconds });
    const off = runArm({ seed, enabled: false, size, steps, stepSeconds });
    rows.push({
      seed,
      on: on.gini,
      off: off.gini,
      difference: off.gini - on.gini,
      relativeReduction: off.gini > 0 ? (off.gini - on.gini) / off.gini : 0,
    });
  }
  const on = rows.map((r) => r.on);
  const off = rows.map((r) => r.off);
  const differences = rows.map((r) => r.difference);
  const reductions = rows.map((r) => r.relativeReduction);
  const rowsSha256 = crypto.createHash("sha256").update(JSON.stringify(rows)).digest("hex");
  return {
    schema: "holotrade.balancer-ab.v1",
    evidence: "SIMULATION",
    generatedAt: new Date().toISOString(),
    design: {
      paired: true,
      seeds,
      fleetSize: size,
      steps,
      stepSeconds,
      simulatedHoursPerArm: steps * stepSeconds / 3600,
      changedVariable: "PricingEngine.balancerEnabled",
      workloadId: "llm-train",
    },
    summary: {
      on: { mean: mean(on), sampleSd: sampleSd(on), ci95: ci95(on) },
      off: { mean: mean(off), sampleSd: sampleSd(off), ci95: ci95(off) },
      pairedDifference: { mean: mean(differences), sampleSd: sampleSd(differences), ci95: ci95(differences) },
      relativeReduction: {
        mean: mean(reductions), sampleSd: sampleSd(reductions), ci95: ci95(reductions),
        min: Math.min(...reductions), max: Math.max(...reductions),
      },
      improvedSeeds: rows.filter((r) => r.difference > 0).length,
      allSeedsImproved: rows.every((r) => r.difference > 0),
    },
    rowsSha256,
    rows,
  };
}

function intArg(name, fallback) {
  const prefix = `--${name}=`;
  const raw = process.argv.find((arg) => arg.startsWith(prefix));
  if (!raw) return fallback;
  const value = Number(raw.slice(prefix.length));
  if (!Number.isSafeInteger(value) || value <= 0) throw new RangeError(`${name} must be a positive integer`);
  return value;
}

if (require.main === module) {
  const result = runExperiment({
    seeds: intArg("seeds", 64),
    size: intArg("size", 220),
    steps: intArg("steps", 500),
    stepSeconds: intArg("step-seconds", 60),
  });
  if (process.argv.includes("--summary")) delete result.rows;
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

module.exports = { runArm, runExperiment, mean, sampleSd, ci95 };
