"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const Freezer = require("../analysis/e8_normalizer_stable_adapter.js");
const Adapter = require("../scheduler/e8-normalizer-stable-adapter.js");
const frozen = require("../data/e8_normalizer_stable_adapter.json");

test("GAP exactly regenerates the strengthened D26 certificate", { timeout: 60_000 }, () => {
  assert.equal(Adapter.verifyFrozen(), true);
  assert.deepEqual(Freezer.run(), frozen);
  assert.equal(frozen.d26Branch.c13FixedSector.dimension, 316);
  assert.equal(frozen.d26Branch.nontrivialC13Sector.moduleEachSide, "W12^315");
  assert.equal(frozen.d26Branch.nontrivialC13Sector.c2InvariantDimensionEachSide, 1890);
});

test("the odd and D26 branches balance exact auxiliary dimensions", () => {
  const odd = Adapter.planStableAdapter("c13c3");
  assert.equal(odd.stableDimensionEachSide, 4200);
  assert.equal(odd.sourceDimensionEachSide + odd.correctionDimensionEachSide, 4200);
  assert.equal(odd.exact, true);
  assert.equal(odd.dispatchable, false);
  assert.equal(Adapter.verifyPlan(odd), true);

  const d26 = Adapter.planStableAdapter("d26");
  assert.equal(d26.stableDimensionEachSide, 4160);
  assert.equal(d26.sourceDimensionEachSide + d26.correctionDimensionEachSide, 4160);
  assert.equal(d26.leftCorrection.antipodalPairs, 32);
  assert.equal(d26.leftCorrection.module, "J2^32");
  assert.equal(d26.rightCorrection.module, "J1^64");
  assert.equal(d26.naturalFixedConeIsCorrectionCarrier, false);
  assert.equal(d26.c13EquivariantTranslationExists, false);
  assert.equal(Adapter.verifyPlan(d26), true);
});

test("the full C13:C6 request is a signed-off refusal, not an inferred bridge", () => {
  const blocked = Adapter.planStableAdapter("c13c6");
  assert.equal(blocked.accepted, false);
  assert.equal(blocked.dispatchable, false);
  assert.match(blocked.reason, /no single compatible C13:C6 module intertwiner/i);
  assert.equal(Adapter.verifyPlan(blocked), true);
  assert.throws(() => Adapter.planStableAdapter("c13"), /branch must be/);
});

test("stable plans are immutable and mutation is detected", () => {
  const plan = Adapter.planStableAdapter("d26");
  assert.equal(Object.isFrozen(plan), true);
  assert.equal(Object.isFrozen(plan.c13FixedSector), true);
  assert.equal(Adapter.verifyPlan({ ...plan, stableDimensionEachSide: 4096 }), false);
});
