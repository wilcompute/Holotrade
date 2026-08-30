"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");

const root = path.resolve(__dirname, "..");

test("q=5 ovoid deficiency frontier is rigorously [9,12]", () => {
  const s = require(path.join(root, "data/w35_ovoid_deficiency_state.json"));
  assert.equal(s.status, "OPEN");
  assert.deepEqual(s.interval, [9, 12]);
  assert.equal(s.lowerBound.value, 9);
  assert.equal(s.lowerBound.proofCommit, "c1025ae22e63309db3a28afbafdf1beb723cdf91");
  assert.match(s.lowerBound.argument, /deficiency 8/i);
  assert.equal(s.rivalReadings.thetaMinusAlpha.value, 8);
  assert.match(s.rivalReadings.thetaMinusAlpha.status, /REFUTED/);
});

test("depth-2 tensor frontier excludes the tight 110 case", () => {
  const s = require(path.join(root, "data/tensor_tight_self_duality_obstruction.json"));
  assert.equal(s.status, "PASS");
  assert.equal(s.tightCandidate, 110);
  assert.equal(s.centreMultiplicity.thereforeFEmpty, true);
  assert.equal(s.centreMultiplicity.centreMapsBijective, true);
  assert.equal(s.consequence.tau2Equals110, false);
  assert.deepEqual(s.consequence.certifiedInterval, [111, 115]);
});
