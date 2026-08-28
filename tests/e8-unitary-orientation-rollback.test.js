"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const Probe = require("../analysis/e8_unitary_orientation_rollback_probe.js");
const frozen = require("../data/e8_unitary_orientation_rollback_probe.json");

test("GAP exactly regenerates the orientation and rollback certificate", { timeout: 120_000 }, () => {
  assert.deepEqual(Probe.run(), frozen);
  const { sha256, ...body } = frozen;
  assert.equal(Probe.digest(body), sha256);
});

test("the orientation character is relative to the embedded spread stabilizer", () => {
  assert.equal(frozen.carrier.index, 2);
  assert.equal(frozen.orientationCharacter.quotient, "C2");
  assert.equal(frozen.orientationCharacter.relativeToEmbeddedSpreadStabilizer, true);
  assert.equal(frozen.orientationCharacter.intrinsicToUnmarkedHoleGraph, false);
  assert.match(frozen.orientationCharacter.reason, /three distinct index-two/);
  assert.deepEqual(frozen.holeOrbitals.subdegrees, [1, 48, 48, 16, 4, 3]);
  assert.equal(frozen.holeOrbitals.unchangedByOuterExtension, true);
});

test("the maximum-spread partner is canonical only as an unlabelled pair", () => {
  const fibre = frozen.maximumSpreadFibre;
  assert.equal(fibre.maximumSpreads, 2268);
  assert.equal(fibre.coveredPointSets, 1134);
  assert.equal(fibre.fibreSize, 2);
  assert.equal(fibre.pairedSpreadsShareLines, 0);
  assert.equal(fibre.partnerInvolutionCommutesWithAmbientAction, true);
  assert.equal(fibre.partnerInvolutionInsideAmbientAction, false);
  assert.equal(fibre.canonicalUnlabelledPairing, true);
  assert.equal(fibre.canonicalZeroOneLabelling, false);
});

test("rollback refuses to choose among five exact outer-involution classes", () => {
  const rollback = frozen.rollback;
  assert.equal(rollback.outerInvolutions, 376);
  assert.equal(rollback.conjugacyClassesUnderSpreadGroup.length, 5);
  assert.equal(rollback.conjugacyClassesUnderSpreadGroup
    .reduce((sum, row) => sum + row.classSize, 0), 376);
  assert.equal(rollback.holeActionCentralizerOrder, 1);
  assert.equal(rollback.canonicalOuterInvolution, false);
  assert.equal(rollback.canonicalRollbackOperation, false);
});
