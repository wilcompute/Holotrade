"use strict";

const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const test=require("node:test");
const Freezer=require("../analysis/w33_circuit_hemisystem_gset_bridge.js");
const frozen=require("../data/w33_circuit_hemisystem_gset_bridge.json");

test("GAP separates the two 216-state carriers by their native actions",{timeout:300000},()=>{
  assert.deepEqual(Freezer.build(),frozen);
  assert.deepEqual(frozen.carriers,{sentinelFiveCircuits:216,hemisystemsModuloComplement:216,eachTransitive:true});
  assert.equal(frozen.innerPSpAction.circuitStabilizerOrder,120);
  assert.equal(frozen.innerPSpAction.hemisystemStabilizerOrder,120);
  assert.deepEqual(frozen.innerPSpAction.circuitStabilizerOrderHistogram,frozen.innerPSpAction.hemisystemStabilizerOrderHistogram);
  assert.equal(frozen.innerPSpAction.stabilizersConjugate,false);
});

test("the outer graph automorphism does not repair the mismatch",()=>{
  assert.equal(frozen.fullAutomorphismAction.order,51840);
  assert.equal(frozen.fullAutomorphismAction.circuitStabilizerOrder,240);
  assert.equal(frozen.fullAutomorphismAction.hemisystemStabilizerOrder,240);
  assert.deepEqual(frozen.fullAutomorphismAction.circuitStabilizerOrderHistogram,frozen.fullAutomorphismAction.hemisystemStabilizerOrderHistogram);
  assert.equal(frozen.fullAutomorphismAction.stabilizersConjugate,false);
  assert.ok(frozen.fullAutomorphismAction.discrepancyCount>0);
  assert.deepEqual(frozen.fullAutomorphismAction.sharpWitnesses,[
    {order:2,classSize:36,circuitFixed:6,hemisystemFixed:66},
    {order:2,classSize:45,circuitFixed:48,hemisystemFixed:0},
  ]);
  assert.equal(frozen.conclusion.equivariantBijectionExists,false);
  assert.equal(frozen.conclusion.outerTwistRepairs,false);
});

test("Steinberg-81 is the sharp module-level separator",()=>{
  const psp=frozen.representationDiagnosis.pspDecomposition;
  const circuitDimension=psp.reduce((sum,row)=>sum+row.degree*row.circuitMultiplicity,0);
  const hemisystemDimension=psp.reduce((sum,row)=>sum+row.degree*row.hemisystemMultiplicity,0);
  assert.equal(frozen.representationDiagnosis.pspCircuitDimension,216);
  assert.equal(frozen.representationDiagnosis.pspHemisystemDimension,216);
  assert.equal(circuitDimension,216);
  assert.equal(hemisystemDimension,216);
  assert.equal(frozen.representationDiagnosis.circuitSteinberg81Multiplicity,1);
  assert.equal(frozen.representationDiagnosis.hemisystemSteinberg81Multiplicity,0);
  assert.match(frozen.representationDiagnosis.reading,/sharp module-level separator/);

  const note=fs.readFileSync(path.join(__dirname,"..","analysis","2026-09-01_THE_TWO_216S_ARE_NOT_THE_SAME_GSET.md"),"utf8");
  assert.match(note,/circuits:\s+1 \+ 2\*15 \+ 20 \+ 24 \+ 30 \+ 30 \+ 81/);
  assert.doesNotMatch(note,/circuits:\s+1 \+ 2\*15 \+ 20 \+ 24 \+ 30 \+ 30 \+ 30 \+ 81/);
});

test("the no-go stays at the finite G-set boundary",()=>{
  assert.match(frozen.dependencies.priorBoundary,/explicitly left a fibre-level correspondence unclaimed/);
  assert.match(frozen.evidenceBoundary,/non-equivariant lookup table/);
  assert.match(frozen.evidenceBoundary,/changes no blocking bound/);
});
