"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const Freezer = require("../analysis/e8_unitary_canonical_fibre_partition.js");
const frozen = require("../data/e8_unitary_canonical_fibre_partition.json");
const fibre = require("../data/e8_unitary_crossprime_fibre_differential.json");

test("GAP proves full-automorphism canonicality of the fibre partition", { timeout: 240_000 }, () => {
  assert.deepEqual(Freezer.run(), frozen);
  const { sha256, ...body } = frozen;
  assert.equal(Freezer.digest(body), sha256);
  assert.equal(frozen.graph.order, 23040);
  assert.equal(frozen.intrinsicTwoCore.order, 32);
  assert.equal(frozen.partition.canonicalAsUnlabelledPartition, true);
});

test("the intrinsic O2 orbits are exactly the existing fifteen frozen blocks", () => {
  assert.equal(frozen.sourceCertificateSha256, fibre.sha256);
  assert.equal(frozen.partition.orbitCount, fibre.blocks.length);
  assert.equal(frozen.partition.orbitSize, 8);
  assert.equal(frozen.partition.equalsFrozenFibrePartition, true);
  assert.equal(frozen.partition.blockKernel, "O2(Aut graph)");
});

test("partition canonicality does not overclaim canonical fibre coordinates", () => {
  assert.equal(frozen.fibreAction.inducedGroup, "C2^3");
  assert.equal(frozen.fibreAction.individualSlotLabellingCanonical, false);
  assert.match(frozen.evidenceBoundary, /not machines or physical sites/);
});
