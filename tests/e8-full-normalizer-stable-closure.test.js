"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const Freezer = require("../analysis/e8_full_normalizer_stable_closure.js");
const Closure = require("../scheduler/e8-full-normalizer-stable-closure.js");
const frozen = require("../data/e8_full_normalizer_stable_closure.json");
const local = require("../data/e8_normalizer_stable_adapter.json");
const ROOT = path.resolve(__dirname, "..");

test("GAP exactly regenerates the full C13:C6 stable closure", { timeout: 60_000 }, () => {
  assert.equal(Closure.verifyFrozen(), true);
  assert.deepEqual(Freezer.run(), frozen);
  assert.deepEqual(frozen.complementAction.vectorOrbitProfile,
    { "1": 4, "2": 6, "3": 20, "6": 670 });
  assert.equal(frozen.complementAction.permutationModuleFixedDimension, 700);
});

test("one 64-dimensional correction repairs C2 and C3 simultaneously", () => {
  assert.equal(frozen.correction.left.dimension, 64);
  assert.equal(frozen.correction.right.dimension, 64);
  assert.equal(frozen.correction.c2Restriction.left, "J2^32");
  assert.equal(frozen.correction.c2Restriction.right, "J1^64");
  assert.equal(frozen.correction.c2Restriction.recoversD26Repair, true);
  assert.equal(frozen.correction.c2StableMeaning.missingNonsplitExtensions, 32);
  assert.equal(frozen.correction.c2StableMeaning.identity, "64 = 2*32");
  assert.equal(frozen.correction.c3Restriction.repairsDefect, true);
  assert.equal(local.d26Branch.leftCorrection.module, "J2^32");
  assert.equal(local.d26Branch.rightCorrection.module, "J1^64");
});

test("the latest W33 carrier audit is a no-go, not an inferred 32-state correction", () => {
  assert.equal(frozen.rejectedCardinalityBridge.correctionCarrierClaimed, false);
  assert.match(frozen.rejectedCardinalityBridge.reason, /1\^5 3\^9/);
  assert.match(frozen.rejectedCardinalityBridge.reason, /1\^2 3\^10/);
});

test("the abstract stable closure is exact but remains non-dispatchable", () => {
  const plan = Closure.planStableClosure();
  assert.equal(plan.stableDimensionEachSide, 4160);
  assert.equal(plan.abstractModuleIsomorphismProved, true);
  assert.equal(plan.chainLevelIntertwinerBuilt, false);
  assert.equal(plan.dispatchable, false);
  assert.equal(plan.requiredNextEvidence, "EXPLICIT_CHAIN_LEVEL_4160_INTERTWINER");
  assert.equal(Object.isFrozen(plan), true);
  assert.equal(Closure.verifyPlan(plan), true);
  assert.equal(Closure.verifyPlan({ ...plan, stableDimensionEachSide: 4096 }), false);
});

test("the demo loads and bounds the complete six-certificate backend closure", () => {
  const html = fs.readFileSync(path.join(ROOT, "holotrade.html"), "utf8");
  const app = fs.readFileSync(path.join(ROOT, "js/app.js"), "utf8");
  assert.match(html, /id="unitaryBackendClosure"/);
  for (const certificate of [
    "e8_full_normalizer_stable_closure.json",
    "e8_unitary_canonical_fibre_partition.json",
    "e8_unitary_voltage_lift.json",
    "e8_unitary_reversible_dilation.json",
    "e8_fractal_microvm_fabric.json",
    "e8_pg34_sentinel_control_plane.json",
  ]) assert.match(app, new RegExp(certificate.replaceAll(".", "\\.")));
  assert.match(app, /EXACT \/ NON-DISPATCHABLE/);
  assert.match(app, /171 iCE40 LUT4s/);
  assert.match(app, /4C₄, not C₁₆/);
  assert.match(app, /20,160/);
  assert.match(app, /2-\(85,21,5\)/);
  assert.match(app, /\[40,15,8\]₂/);
  assert.match(app, /216 five-word zero-parity circuits/);
  assert.match(app, /None of these facts binds a host or authorizes dispatch/);
});
