"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const path = require("node:path");

global.window = global;
const root = path.resolve(__dirname, "..");
const shapes = require(path.join(root, "scheduler/w33-shapes.js"));
const cert = JSON.parse(fs.readFileSync(
  path.join(root, "data/w33_near_ovoid_adversarial_corpus_certificate.json"), "utf8"));
const q5 = JSON.parse(fs.readFileSync(
  path.join(root, "data/w33_ovoid_deficiency_q5_support_update.json"), "utf8"));

test("near-ovoid adversarial corpus is pinned to the exact level-1 line-placement cliff", () => {
  assert.equal(cert.valid, true);
  assert.equal(cert.counts.minimumBlockers, 360);
  assert.equal(cert.counts.removalsPerBlocker, 8);
  assert.equal(cert.counts.nearOvoids, 2880);
  assert.equal(cert.counts.minimumBlockers * cert.counts.removalsPerBlocker,
    cert.counts.nearOvoids);
  assert.equal(cert.counts.blockersPerCenter, 9);
  assert.equal(cert.counts.freeLinesPerNearOvoid, 3);
  assert.match(cert.recordsSha256, /^[0-9a-f]{64}$/);

  const g = shapes.guaranteeFor(4);
  assert.equal(g.blockingNumber, 11);
  assert.equal(g.busyTolerated, 10);
  assert.equal(cert.placementCliff.reservationSize, 4);
  assert.equal(cert.placementCliff.busyStateSize, g.busyTolerated);
  assert.equal(cert.placementCliff.blockingNumber, g.blockingNumber);
  assert.equal(cert.placementCliff.freeLinePlacementsAtState, 3);
  assert.equal(cert.placementCliff.oneAddedPointDefeatsAllPlacements, true);
});

test("q=5 deficiency integration keeps an honest open interval", () => {
  assert.equal(q5.valid, true);
  assert.equal(q5.q5.deficiencyFivePossible, false);
  assert.ok(q5.q5.provedLowerBound >= 6);
  assert.equal(q5.q5.existingFeasibleUpperBound, 12);
  assert.deepEqual(q5.q5.certifiedInterval,
    [q5.q5.provedLowerBound, q5.q5.existingFeasibleUpperBound]);
  assert.equal(q5.q5.exactValue, null);
});
