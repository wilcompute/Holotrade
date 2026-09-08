"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const A = require("../scheduler/w33-minimal-blocker-atlas.js");
const Q = require("../scheduler/w33-failure-distance.js");
const Search = require("../scheduler/w33-failure-distance-search.js");
const R = require("../scheduler/w33-topology-resilience.js");

test("complete minimal blocker atlas is exactly 360 size11 plus 40 neighborhoods", () => {
  const v = A.verifyAtlas();
  assert.equal(v.status, "PASS");
  assert.equal(v.blockerCount, 400);
  assert.deepEqual(v.sizeHistogram, { 11: 360, 12: 40 });
  assert.equal(A.CLASSIFIED.filter((x) => x.type === "minimum-11").length, 360);
  assert.equal(A.CLASSIFIED.filter((x) => x.type === "neighborhood-12").length, 40);
});

test("atlas distance is exact on every minimal blocker and every one-point deletion", () => {
  for (const row of A.CLASSIFIED) {
    assert.equal(A.distanceViaAtlas(row.points).distance, 0);
    const deleted = row.points.slice(1);
    assert.equal(R.assessFailures(deleted).allLinesHit, false);
    assert.equal(A.distanceViaAtlas(deleted).distance, 1);
  }
});

test("closed-form atlas agrees with independent set-cover oracle on diverse representatives", () => {
  const cases = [[]];
  for (let p = 0; p < 10; p++) cases.push([p]);
  const neighbors = [...R.GEOMETRY.adjacency[0]].sort((a, b) => a - b);
  const nonneighbors = Array.from({ length: 40 }, (_, i) => i).filter((i) => i !== 0 && !R.GEOMETRY.adjacency[0].has(i));
  for (const q of neighbors.slice(0, 5)) cases.push([0, q]);
  for (const q of nonneighbors.slice(0, 5)) cases.push([0, q]);
  cases.push([0, 1, 2], [3, 7, 11, 19], [...neighbors.slice(0, 6)]);
  for (const F of cases) {
    const atlas = Q.exactFailureDistance(F);
    const search = Search.exactFailureDistanceSearch(F);
    assert.equal(atlas.distance, search.distance, `distance mismatch on ${F}`);
    assert.equal(R.assessFailures([...F, ...atlas.witnessAdditionalFailures]).allLinesHit, true);
  }
});

test("production distance certificate names its nearest minimal blocker template", () => {
  const row = Q.exactFailureDistance([]);
  assert.equal(row.distance, 11);
  assert.equal(row.atlasBlockerCount, 400);
  assert.equal(row.method, "complete-minimal-blocker-atlas");
  assert.equal(Number.isInteger(row.nearestMinimalBlockerIndex), true);
  assert.equal(row.nearestMinimalBlockerSize, 11);
});
