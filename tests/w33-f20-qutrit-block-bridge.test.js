"use strict";

const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const test=require("node:test");
const formal=require("../analysis/w33_f20_qutrit_block_router_formal.js");
const fiveFront=require("../analysis/w33_five_front_breakthrough.js");

const ROOT=path.resolve(__dirname,"..");
const packet=require("../data/w33_f20_qutrit_block_bridge.json");
const proof=require("../data/w33_f20_qutrit_block_router_formal.json");
const shaFile=rel=>`sha256:${crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT,rel))).digest("hex")}`;

test("the five-qutrit block upgrades D10 to F20 only with local Clifford compensation",()=>{
  assert.equal(packet.schema,"holotrade.w33-f20-qutrit-block-bridge.v1");
  assert.equal(packet.status,"PASS");
  assert.deepEqual(packet.cyclicQutritBlock.plainPermutationImage,{order:10,structure:"D10"});
  assert.deepEqual(packet.cyclicQutritBlock.localCliffordCoordinateImage,{order:20,structure:"C5 : C4"});
  assert.equal(packet.checks.missingMultiplierRequiresClifford,true);
  assert.equal(packet.checks.allLocalMapsAreSymplectic,true);
  assert.equal(packet.checks.physicalLiftPreservesCode,true);
  assert.equal(packet.checks.physicalLiftPreservesPauliForm,true);
});

test("the fibre stabilizer and qutrit code automorphisms share an explicit F20 presentation",()=>{
  assert.equal(packet.fibreProductF20.stabilizerOrder,20);
  assert.deepEqual(packet.fibreProductF20.generatorOrders,[5,4]);
  assert.equal(packet.fibreProductF20.conjugationExponent,3);
  assert.deepEqual(packet.explicitIsomorphism.generatorMap,{a:"T",b:"M"});
  assert.equal(packet.checks.commonF20Presentation,true);
  assert.equal(packet.checks.transitionTablesSatisfyPresentation,true);
  const action=packet.cyclicQutritBlock.addressedPauliAction;
  assert.deepEqual([action.degree,action.groupOrder],[40,20]);
  assert.equal(new Set(action.translation).size,40);
  assert.equal(new Set(action.multiplier).size,40);
  const body={...packet}; delete body.sha256;
  assert.equal(packet.sha256,`sha256:${crypto.createHash("sha256").update(fiveFront.canonical(body)).digest("hex")}`);
});

test("the Yosys proof is source-bound and the missing-Clifford mutation fails",()=>{
  assert.equal(proof.schema,"holotrade.w33-f20-qutrit-block-router-formal.v1");
  assert.equal(proof.status,"PASS");
  assert.equal(proof.source.packetSha256,shaFile(proof.source.packet));
  assert.equal(proof.source.rtlSha256,shaFile(proof.source.rtl));
  assert.equal(proof.positive.proved,true);
  assert.equal(proof.positive.exitCode,0);
  assert.equal(proof.negativeControl.counterexample,true);
  assert.notEqual(proof.negativeControl.exitCode,0);
  const body={...proof}; delete body.sha256;
  assert.equal(proof.sha256,`sha256:${crypto.createHash("sha256").update(formal.canonical(body)).digest("hex")}`);
});

test("the certificate keeps the locality and fault-tolerance boundary explicit",()=>{
  assert.match(packet.boundary,/does not identify the 1,296 fibre-product states with qutrit codewords/);
  assert.match(packet.boundary,/does not make the nonlocal 20-to-240 embedding local/);
  assert.match(packet.boundary,/does not close the physical calibration, threshold, or fault-tolerant recode gates/);
  assert.match(proof.boundary,/not a timing closure/);
});
