"use strict";

const assert=require("node:assert/strict");
const test=require("node:test");
const Freezer=require("../analysis/e8_unitary_homology_code_w33_obstruction.js");
const frozen=require("../data/e8_unitary_homology_code_w33_obstruction.json");

test("GAP, MeatAxe, the exhaustive coset enumerator, and MacWilliams replay agree",{timeout:180000},()=>{
  assert.deepEqual(Freezer.build(),frozen);
  assert.equal(frozen.codes.image.parameters,"[120,40,16]_2");
  assert.equal(frozen.codes.kernel.parameters,"[120,80,8]_2");
  assert.equal(frozen.codes.kernel.minimumWords,"435");
  assert.equal(frozen.codes.css.parameters,"[[120,40,8]]_2");
  assert.equal(Object.values(frozen.codes.image.weightEnumerator).reduce((sum,value)=>sum+BigInt(value),0n),1n<<40n);
  assert.equal(Object.values(frozen.codes.kernel.weightEnumerator).reduce((sum,value)=>sum+BigInt(value),0n),1n<<80n);
});

test("the normal 2-core separates logical homology from an inflated W33 point module",()=>{
  assert.deepEqual(frozen.twoCore.homologyMoveRankDistribution,{"0":1,"12":6,"14":15,"16":10});
  assert.deepEqual(frozen.twoCore.imageMoveRankDistribution,{"0":1,"10":6,"16":15,"18":10});
  assert.equal(frozen.modules.imageIsomorphicToCoimage,true);
  assert.equal(frozen.modules.imageIsomorphicToHomology,false);
  assert.equal(frozen.w33Comparison.s6IdentificationClassesTested,2);
  assert.equal(frozen.w33Comparison.isomorphicInEitherClass,false);
  assert.deepEqual(frozen.w33Comparison.nonzeroRankProfiles,[[1,6],[1,11]]);
});

test("the frozen packet preserves the finite-logical evidence boundary",()=>{
  assert.match(frozen.evidenceBoundary,/No physical qubits/);
  assert.match(frozen.evidenceBoundary,/No .*integral E8 coordinates/);
  assert.match(frozen.evidenceBoundary,/dispatch authority/);
});
