"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const F = require("../analysis/e8_unitary_hole_sectors.js");
const frozen = require("../data/e8_unitary_hole_sectors.json");

test("the unitary hole certificate is canonical and GAP-reproducible", { timeout: 180_000 }, () => {
  const { sha256, ...body } = frozen;
  assert.equal(F.digest(body), sha256);
  assert.deepEqual(F.run(), frozen);
});

test("q=2 closes at the known 15-vertex strongly regular residual", () => {
  const q2 = frozen.profiles.find((row) => row.q === 2);
  assert.equal(q2.maximumPartialSpreads, 72);
  assert.deepEqual(q2.maximumOrbitSizes, [72]);
  assert.equal(q2.holes, 15);
  assert.equal(q2.holeGraph.certifiedParameters, "SRG(15,6,1,3)");
  assert.deepEqual(q2.holeGraph.spectrum, [[6, 1], [1, 9], [-3, 5]]);
});

test("q=3 closes as the exact folded-Q6 coset graph, not the natural duad graph", () => {
  const q3 = frozen.profiles.find((row) => row.q === 3);
  assert.equal(q3.maximumPartialSpreads, 2268);
  assert.deepEqual(q3.maximumOrbitSizes, [2268]);
  assert.equal(q3.holes, 120);
  assert.equal(q3.holeGraph.degree, 20);
  assert.equal(q3.holeGraph.stronglyRegular, false);
  assert.deepEqual(q3.holeGraph.spectrum,
    [[20, 1], [8, 5], [4, 45], [0, 9], [-4, 60]]);
  assert.equal(frozen.q3Symmetry.isomorphicToFoldedQ6AutomorphismGroup, true);
  assert.equal(frozen.q3Symmetry.isomorphicToWeylD6, false);
  assert.deepEqual(frozen.q3CosetModel.stabilizerSmallGroupId, [192, 1485]);
  assert.deepEqual(frozen.q3CosetModel.adjacencyOrbitalDegrees, [16, 4]);
  assert.equal(frozen.q3CosetModel.graphIsomorphismToH39HoleGraph, true);
  assert.deepEqual(frozen.naturalKummerDuadNoGo.stabilizerSmallGroupId, [192, 1472]);
  assert.equal(frozen.naturalKummerDuadNoGo.graphIsomorphismToH39HoleGraph, false);
});

test("the demo labels the graph as ceiling-only and loads its independent certificate", () => {
  const root = path.resolve(__dirname, "..");
  const html = fs.readFileSync(path.join(root, "holotrade.html"), "utf8");
  const app = fs.readFileSync(path.join(root, "js/app.js"), "utf8");
  assert.match(html, /id="unitaryHoleShape"/);
  assert.match(html, /Maximum-rung boundary geometry/);
  assert.match(app, /data\/e8_unitary_hole_sectors\.json/);
  assert.match(app, /rung !== maximumRung/);
  assert.match(app, /current residual is intentionally not assigned the ceiling graph/);
  assert.match(app, /natural 120-duad action is a certified no-go/);
});
