"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const frozen = require(path.join(root, "data/near_ovoid_migration_trajectory_ab.json"));
const T = require(path.join(root, "experiments/near_ovoid_migration_trajectory_ab.js"));
const corpus = require(path.join(root, "analysis/w33_near_ovoid_corpus.js")).buildCorpus();

test("six-step near-ovoid recovery trajectories reproduce the frozen paired result", () => {
  const z = T.runExperiment({ steps: 6, includeRows: false });
  assert.equal(z.evidence, "EXHAUSTIVE FINITE CORPUS / POLICY TRAJECTORY");
  assert.equal(z.design.startStates, 2880);
  assert.equal(z.design.migrationIsSizePreserving, true);
  assert.deepEqual(z.summary.movement, frozen.summary.movement);
  assert.deepEqual(z.summary.strictlyBetterStatesByStep,
    frozen.summary.strictlyBetterStatesByStep);
  assert.deepEqual(z.summary.legacy.freeLineHistogramByStep,
    frozen.summary.legacy.freeLineHistogramByStep);
  assert.deepEqual(z.summary.aware.freeLineHistogramByStep,
    frozen.summary.aware.freeLineHistogramByStep);
  assert.deepEqual(z.summary.legacy.minimumHeadroomHistogram,
    frozen.summary.legacy.minimumHeadroomHistogram);
  assert.deepEqual(z.summary.aware.minimumHeadroomHistogram,
    frozen.summary.aware.minimumHeadroomHistogram);
  assert.deepEqual(z.summary.legacy.uniqueStatesVisitedHistogram,
    frozen.summary.legacy.uniqueStatesVisitedHistogram);
  assert.deepEqual(z.summary.aware.uniqueStatesVisitedHistogram,
    frozen.summary.aware.uniqueStatesVisitedHistogram);
  assert.equal(z.summary.legacy.cumulativeHeadroomTotal, 98186);
  assert.equal(z.summary.aware.cumulativeHeadroomTotal, 212045);
  assert.equal(z.summary.cumulativeHeadroomGainTotal, 113859);
  assert.equal(z.summary.movement.pairedExtraRayCost, 0);
  assert.deepEqual(z.summary.aware.minimumHeadroomHistogram, { "6": 2880 });
  assert.deepEqual(z.summary.aware.uniqueStatesVisitedHistogram, { "7": 2880 });
});

test("aware full migrations keep the same movement cost floor as legacy", () => {
  const rec = corpus.records[0];
  const start = rec.blocker.filter((x) => x !== rec.removals[0]);
  const A = T.runArm(start, "legacy", 6);
  const B = T.runArm(start, "aware", 6);
  assert.equal(A.totalRays, 18);
  assert.equal(B.totalRays, 18);
  assert.equal(A.totalHops, 6);
  assert.equal(B.totalHops, 6);
  assert.ok(B.cumulativeHeadroom >= A.cumulativeHeadroom);
  assert.ok(B.minimumHeadroom >= 6);
});
