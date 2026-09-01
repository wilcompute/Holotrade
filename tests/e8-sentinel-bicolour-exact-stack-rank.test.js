"use strict";

const assert=require("node:assert/strict");
const test=require("node:test");
const Freezer=require("../analysis/e8_sentinel_bicolour_exact_stack_rank.js");
const frozen=require("../data/e8_sentinel_bicolour_exact_stack_rank.json");

test("GAP closes the colour-stack rank over Q rather than one finite field",{timeout:300000},()=>{
  assert.deepEqual(Freezer.build(),frozen);
  assert.deepEqual(frozen.rationalRowSpaces,{
    rankMplus:216,rankMminus:216,stackedRank:372,commonDimension:60,characteristic:"Q",
  });
  assert.equal(frozen.proofBoundary.modularRankUsedAsProof,false);
  assert.equal(frozen.proofBoundary.characteristicZeroRankComputed,true);
});

test("the common colour space is 1+15+20+24, not the symmetric 60-sector",()=>{
  assert.deepEqual(frozen.jointSectorResolution.directCommonIntersections,[0,0,0,20,0,24,1]);
  assert.equal(frozen.jointSectorResolution.doubledFifteenIsotypicCommonDimension,15);
  assert.equal(frozen.jointSectorResolution.exactCommonDecomposition,"1+15+20+24");
  assert.equal(frozen.jointSectorResolution.equalsSymmetricSixtySector,false);
  assert.match(frozen.jointSectorResolution.reading,/zero intersection with the symmetric 60-sector/);
});

test("both colours have the same canonical 1+20+24 circuit image",()=>{
  assert.deepEqual(frozen.circuitCarrierBridge.gramScalarsByJointSector,[0,0,0,12,0,30,120]);
  assert.deepEqual(frozen.circuitCarrierBridge.directSectorIntersections,[0,0,0,20,0,24,1]);
  assert.equal(frozen.circuitCarrierBridge.circuitCarrierDimension,45);
  assert.equal(frozen.circuitCarrierBridge.plusTransportedIntoCommon,45);
  assert.equal(frozen.circuitCarrierBridge.minusTransportedIntoCommon,45);
  assert.equal(frozen.circuitCarrierBridge.plusMinusImagesEqual,true);
  assert.equal(frozen.circuitCarrierBridge.commonComplementDimension,15);
  assert.equal(frozen.circuitCarrierBridge.exactSplit,"common60 = common circuit image(1+20+24) direct-sum diagonal15");
});

test("the certificate keeps finite incidence separate from deployment claims",()=>{
  assert.equal(frozen.incidence.fiveCircuits,216);
  assert.equal(frozen.incidence.sixCircuits,540);
  assert.deepEqual(frozen.incidence.colourOrbitSizes,[2160,2160]);
  assert.match(frozen.evidenceBoundary,/exact finite circuit-incidence/);
  assert.match(frozen.evidenceBoundary,/dispatch bindings/);
});
