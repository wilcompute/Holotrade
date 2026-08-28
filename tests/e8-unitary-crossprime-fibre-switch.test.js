"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const Freezer = require("../analysis/e8_unitary_crossprime_fibre_differential.js");
const Switch = require("../scheduler/e8-unitary-fibre-switch.js");
const frozen = require("../data/e8_unitary_crossprime_fibre_differential.json");
const graph = require("../data/e8_unitary_hole_coset_rtl.json");
const ROOT = path.resolve(__dirname, "..");

test("GAP exactly regenerates the cross-prime fibre differential", { timeout: 120_000 }, () => {
  assert.equal(Switch.verifyFrozen(), true);
  assert.deepEqual(Freezer.run(), frozen);
  const { sha256, ...body } = frozen;
  assert.equal(Freezer.digest(body), sha256);
});

test("the 120 logical states have one bijective 15 by 8 address chart", () => {
  const seen = new Set();
  for (let vertex = 0; vertex < 120; vertex += 1) {
    const address = Switch.addressOf(vertex);
    seen.add(`${address.blockId}:${address.fibreSlot}`);
    assert.equal(address.duad.length, 2);
    assert.equal(address.abstractFibreGroup, "F2^3");
  }
  assert.equal(seen.size, 120);
});

test("actual adjacency realizes the exact 4I plus 2T6 weighted quotient", () => {
  for (const sourceBlock of frozen.blocks) {
    for (const source of sourceBlock.vertices) {
      for (let targetBlock = 0; targetBlock < 15; targetBlock += 1) {
        const actual = graph.neighbours[source]
          .filter((vertex) => Switch.addressOf(vertex).blockId === targetBlock).length;
        const relation = Switch.blockRelation(sourceBlock.blockId, targetBlock);
        assert.equal(actual, relation.neighbourCountPerSourceVertex);
      }
    }
  }
  assert.equal(Switch.blockRelation(0, 0).relation, "same-fibre-K4,4");
  const disjoint = frozen.blocks.find((row) =>
    row.duad.every((value) => !frozen.blocks[0].duad.includes(value)));
  assert.equal(Switch.blockRelation(0, disjoint.blockId).relation, "disjoint-duads-KG6,2-zero");
});

test("the parity operator squares to zero on every basis vector", () => {
  const images = [];
  for (let basis = 0; basis < 120; basis += 1) {
    const input = Array(120).fill(0);
    input[basis] = 1;
    const first = Switch.applyDifferential(input);
    const second = Switch.applyDifferential(first);
    assert.equal(first.reduce((sum, bit) => sum + bit, 0), 20);
    assert.equal(second.every((bit) => bit === 0), true);
    images.push(first.join(""));
  }
  assert.equal(new Set(images).size, 120);
});

test("a switch certificate is immutable, tamper-evident, and non-dispatchable", () => {
  const input = Array.from({ length: 120 }, (_, index) => index % 3 === 0 ? 1 : 0);
  const certificate = Switch.buildSwitchCertificate(input);
  assert.equal(certificate.squareZeroObserved, true);
  assert.deepEqual(certificate.certifiedAssociatedGradedDimensions, [40, 40, 40]);
  assert.equal(certificate.dispatchable, false);
  assert.equal(Object.isFrozen(certificate), true);
  assert.equal(Switch.verifySwitchCertificate(certificate), true);
  assert.equal(Switch.verifySwitchCertificate({ ...certificate, outputWeight: 41 }), false);
});

test("the demo exposes the theorem and its no-identification boundary", () => {
  const html = fs.readFileSync(path.join(ROOT, "holotrade.html"), "utf8");
  const app = fs.readFileSync(path.join(ROOT, "js/app.js"), "utf8");
  assert.match(html, /id="unitaryCrossprimeShape"/);
  assert.match(app, /120 = 15 × 8/);
  assert.match(app, /40 \| 40 \| 40/);
  assert.match(app, /No graded piece is claimed to be W\(3,3\)/);
});
