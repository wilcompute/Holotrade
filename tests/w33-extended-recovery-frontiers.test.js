"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const orbit=require(path.join(root,"data/near_ovoid_attractor_psp_orbit.json"));
const local=require(path.join(root,"data/w33_local_recovery_equivalence.json"));
const multi=require(path.join(root,"data/w33_multi_failure_recovery.json"));
const cross=require(path.join(root,"data/w33_crossdc_energy_tiebreak.json"));
const rtl=require(path.join(root,"data/w33_recovery_two_stage_core.json"));
const crossRun=require(path.join(root,"experiments/w33_crossdc_energy_tiebreak.js"));

test("19/19 policy cycles lie in one ambient PSp orbit",()=>{
  assert.equal(orbit.status,"PASS");
  assert.equal(orbit.policyHighCycles,933);
  assert.equal(orbit.ambientOrbitSize,12960);
  assert.equal(orbit.cycleStabilizerOrder,2);
});

test("local healthy controller is exact through the 32-step corpus",()=>{
  assert.equal(local.status,"PASS");
  assert.equal(local.decisions,92160);
  assert.equal(local.distinctVisitedStates,25184);
  assert.equal(local.exactDecisionMatches,local.decisions);
});

test("multi-failure census remains exhaustive at the declared boundary",()=>{
  assert.equal(multi.status,"PASS");
  assert.equal(multi.twoFailures.cases,1252800);
  assert.equal(multi.threeFailures.allInitialPatterns,11692800);
  assert.equal(multi.threeFailures.worstZeroInitialClass.cases,1247040);
  assert.equal(multi.threeFailures.worstZeroInitialClass.topologyAware.reach3["1"],1247040);
  assert.equal(multi.threeFailures.worstZeroInitialClass.topologyAware.reach9.unreached,306);
});

test("cross-DC energy tie-break preserves the movement frontier",()=>{
  const z=crossRun.run();
  assert.equal(z.status,"PASS");
  assert.deepEqual(z.primaryCost,cross.primaryCost);
  assert.equal(z.changedDestinations,148);
  assert.equal(z.energyIndex.lexicographic,15505.55);
  assert.equal(z.energyIndex.energyAware,13547.88);
  assert.equal(z.carbonIndex.lexicographic,96016);
  assert.equal(z.carbonIndex.energyAware,72256);
});

test("two-stage RTL certificate keeps synthesis evidence boundary explicit",()=>{
  assert.equal(rtl.status,"PASS");
  assert.equal(rtl.entryStage.objectiveEquivalentStates,2880);
  assert.equal(rtl.postEntryStage.secondMoveExactMatches,2880);
  assert.equal(rtl.postEntryStage.longHorizonValidation.exactGenericDecisionMatches,92160);
  assert.equal(rtl.rtl.registeredBitsAtSourceLevel,3);
  assert.equal(rtl.rtl.measuredLutCount,null);
});
