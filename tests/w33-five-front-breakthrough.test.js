"use strict";

const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const test=require("node:test");
const freezer=require("../analysis/w33_five_front_breakthrough.js");
const formal=require("../analysis/w33_dual_carrier_router_formal.js");

const ROOT=path.resolve(__dirname,"..");
const packet=require("../data/w33_five_front_breakthrough.json");
const proof=require("../data/w33_dual_carrier_router_formal.json");
const shaFile=rel=>crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT,rel))).digest("hex");

test("corrected line-product obstruction retains the explicit Steinberg basis",()=>{
  assert.equal(packet.schema,"holotrade.w33-five-front-breakthrough.v2");
  assert.equal(packet.steinbergIntertwiner.sourceFactorization,"27chartsx40lines");
  assert.equal(packet.steinbergIntertwiner.rank,3);
  assert.deepEqual(packet.steinbergIntertwiner.basisOrbitSizes,[3,3,12]);
  assert.deepEqual(packet.steinbergIntertwiner.basisGram,[
    ["14","-6","-4"],["-6","14","-4"],["-4","-4","24"],
  ]);
  const body={...packet}; delete body.sha256;
  assert.equal(packet.sha256,crypto.createHash("sha256").update(freezer.canonical(body)).digest("hex"));
});

test("the two S5 forks share exactly the 36-state spread quotient",()=>{
  const d=packet.twoS5Correspondence;
  assert.deepEqual(d.valencies,[6,30,60,60,60]);
  assert.deepEqual(d.ranks,[36,36,36,36,36]);
  assert.deepEqual(d.steinbergRanks,[0,0,0,0,0]);
  assert.equal(d.minimumRelation.components,36);
  assert.equal(d.minimumRelation.component,"K6,6");
  assert.equal(d.minimumRelation.quotientStabilizerType,"S6");
  assert.deepEqual(packet.colourSwap.residual15Parity,[8,7]);
});

test("the F20 fibre product matches the full 435-dimensional obstruction building block",()=>{
  const f=packet.fibreProduct;
  assert.deepEqual([
    f.states,f.stabilizerOrder,f.stabilizerType,
    f.building81Multiplicity,f.building64Multiplicity,
    f.obstruction81Multiplicity,f.obstruction64Multiplicity,
    f.commonBuildingDimension,f.buildingCrossHomDimension,
  ],[1296,20,"C5 : C4",3,3,3,3,435,18]);
  assert.equal(f.abstractIsotypicIsomorphism,true);
  assert.equal(f.explicitIntertwinerBuilt,false);
  assert.equal(f.seesBoth,true);
});

test("the defect correction narrows structure without overstating tau2",()=>{
  assert.equal(packet.tau111Defect.maximumTripleFibres,10);
  assert.equal(packet.tau111Defect.elevenTripleWitnessPatternExcluded,true);
  assert.equal(packet.tau111Defect.raisesLowerBound,false);
  assert.deepEqual(packet.tau111Defect.interval,[111,115]);
});

test("the dual-carrier formal certificate is source-bound and has a failing control",()=>{
  assert.equal(proof.schema,"holotrade.w33-dual-carrier-router-formal.v1");
  assert.equal(proof.valid,true);
  assert.equal(proof.source.packetSha256,shaFile(proof.source.packet));
  assert.equal(proof.source.rtlSha256,shaFile(proof.source.rtl));
  assert.deepEqual(proof.source.carriers,[
    "sentinel-circuit","complementary-hemisystem-pair",
  ]);
  assert.equal(proof.positive.proved,true);
  assert.equal(proof.positive.exitCode,0);
  assert.equal(proof.negativeControl.counterexample,true);
  assert.notEqual(proof.negativeControl.exitCode,0);
  const body={...proof}; delete body.sha256;
  assert.equal(proof.sha256,crypto.createHash("sha256").update(formal.canonical(body)).digest("hex"));
});
