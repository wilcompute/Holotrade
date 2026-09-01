"use strict";

const assert=require("node:assert/strict");
const test=require("node:test");
const Freezer=require("../analysis/e8_pg34_sentinel_control_plane.js");
const Runtime=require("../scheduler/e8-pg34-sentinel-control-plane.js");
const frozen=require("../data/e8_pg34_sentinel_control_plane.json");

test("GAP reconstructs and JS independently replays the 85-state polarity plane",{timeout:120000},()=>{
  assert.equal(Runtime.verifyFrozen(),true);
  assert.deepEqual(Freezer.build(),frozen);
  assert.equal(frozen.polarityDesign.matrixIdentity,"H^2 = 16I + 5J");
  assert.deepEqual(frozen.polarityDesign.spectrum,{"21":1,"4":45,"-4":39});
  assert.equal(frozen.gramIdentities.BBt,"8I_40 + 2A_W33 + J_40");
  assert.equal(frozen.gramIdentities.BtB,"8I_45 + 2A_complement(GQ42)");
});

test("the same 45 supports are exactly the minimum sentinel shell",()=>{
  assert.equal(frozen.sentinel.parameters,"[40,15,8]_2");
  assert.equal(frozen.sentinel.minimumWordsExactlyCrossIncidenceColumns,true);
  assert.deepEqual(frozen.sentinel.weightEnumerator,{"0":1,"8":45,"12":720,"16":6930,"20":17376,"24":6930,"28":720,"32":45,"40":1});
  assert.deepEqual(frozen.gramIdentities.chiralKernelSplit,[15,20]);
  assert.equal(frozen.chiralProtection.exactZeroModes,35);
  assert.equal(frozen.chiralProtection.rectangularIndexFloor,5);
  assert.equal(frozen.chiralProtection.perturbedZeroModes,5);
  assert.equal(frozen.chiralProtection.symmetryDependentExtraModes,30);
  assert.equal(frozen.shell.distance12Pairs,720);
  assert.equal(frozen.shell.distance16Pairs,270);
});

test("all 216 five-circuits compile to immutable zero-parity logical plans",()=>{
  for(let i=0;i<216;i++){
    const plan=Runtime.fiveCircuitParity(i);
    assert.equal(plan.xorIsZero,true);assert.equal(plan.minimumWordIds.length,5);
    assert.equal(Runtime.verifyPlan(plan),true);assert.equal(Object.isFrozen(plan),true);
  }
  const altered={...Runtime.fiveCircuitParity(0),xorIsZero:false};
  assert.equal(Runtime.verifyPlan(altered),false);
});

test("sentinel reservations and polarity fanout preserve the non-dispatchable boundary",()=>{
  for(let i=0;i<45;i++){
    const plan=Runtime.sentinelReservation(i);assert.equal(plan.nodeCount,8);assert.equal(new Set(plan.w33LogicalPoints).size,8);assert.equal(Runtime.verifyPlan(plan),true);
  }
  for(let i=0;i<85;i++){
    const plan=Runtime.polarityFanout(i);assert.equal(plan.fanout,21);assert.equal(plan.containsSource,i>=40);assert.equal(Runtime.verifyPlan(plan),true);
  }
  assert.equal(Runtime.sentinelReservation(0).dispatchable,false);
  assert.match(Runtime.fiveCircuitParity(0).evidenceBoundary,/not a cryptographic MAC/);
});
