"use strict";

const assert=require("node:assert/strict");
const test=require("node:test");
const Freezer=require("../analysis/e8_unitary_homology_sentinel_bridge.js");
const frozen=require("../data/e8_unitary_homology_sentinel_bridge.json");

test("GAP and MeatAxe freeze the complete homology-to-sentinel factorization",{timeout:180000},()=>{
  assert.deepEqual(Freezer.build(),frozen);
  assert.deepEqual([
    frozen.carriers.logicalHomology.dimension,
    frozen.normalSubgroupReduction.coinvariantDimension,
    frozen.normalSubgroupReduction.fixedDimension,
    frozen.normalSubgroupReduction.sentinelDimension,
  ],[40,15,15,15]);
  assert.deepEqual(frozen.normalSubgroupReduction.compositionFactors.coinvariants,[1,1,1,4,4,4]);
  assert.ok(Object.values(frozen.normalSubgroupReduction.pairwiseIsomorphisms).every((value)=>value===false));
});

test("all W33-compatible forward shadows land in the sentinel",()=>{
  const shadow=frozen.universalW33Shadow;
  assert.equal(shadow.everyForwardMapKillsTwoCoreRelations,true);
  assert.equal(shadow.everyBackwardImageInsideFixedHomology,true);
  assert.equal(shadow.innerIdentification.everyForwardImageInsideSentinel,true);
  assert.equal(shadow.outerIdentification.everyForwardImageInsideSentinel,true);
  assert.equal(shadow.innerIdentification.spanOfAllForwardImages,11);
  assert.equal(shadow.outerIdentification.spanOfAllForwardImages,6);
  assert.equal(shadow.innerIdentification.spanOfAllBackwardImages,11);
  assert.equal(shadow.outerIdentification.spanOfAllBackwardImages,6);
});

test("extension data and low-rank maps prevent a relabeling overread",()=>{
  assert.deepEqual(frozen.exhaustiveHomRanks.coinvariantsToSentinelInner.nonzeroRanks,[1,11]);
  assert.deepEqual(frozen.exhaustiveHomRanks.coinvariantsToSentinelOuter.nonzeroRanks,[1,6]);
  assert.deepEqual(frozen.exhaustiveHomRanks.sentinelInnerToCoinvariants.nonzeroRanks,[4,5]);
  assert.deepEqual(frozen.exhaustiveHomRanks.sentinelOuterToCoinvariants.nonzeroRanks,[10]);
  assert.match(frozen.evidenceBoundary,/not an isomorphic relabeling/);
  assert.match(frozen.evidenceBoundary,/no preferred nonzero map/);
  assert.match(frozen.evidenceBoundary,/dispatch binding/);
});
