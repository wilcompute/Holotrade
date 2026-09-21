"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const P=require("../js/w33-ledger-continuation-policy.js");
function load(name){
  const root=process.env.W33_LEDGER_ROOT;assert.ok(root,"W33_LEDGER_ROOT required");
  return JSON.parse(fs.readFileSync(path.join(root,"data",name),"utf8"));
}
function bundle(){return {
  aggregate:load("PART_LEDGER_CONTINUATION_2026_09_21.json"),
  depth3:load("PART_LEDGER_DEPTH3_NPARTY.json"),
  flow:load("PART_LEDGER_MODULAR_FLOW_FIREWALL.json"),
  homotopy:load("PART_W3Q_SIMPLE_HOMOTOPY_COLLAPSE.json"),
  winding:load("PART_LEDGER_WINDING_SECTOR_FIREWALL.json"),
  aux:load("PART_LEDGER_AUXILIARY_RADIATIVE_FIREWALL.json")
};}

test("continuation packet verifies with theorem/candidate boundaries intact",()=>{
  const v=P.verifyContinuationBundle(bundle());
  assert.equal(v.valid,true);assert.equal(v.admitted.length,4);assert.equal(v.candidates.length,1);assert.equal(v.blocked.length,4);
});

test("claim firewall blocks overpromotion",()=>{
  for(const k of ["allStatesDepth3","modularTimeInsideW33","windingUniquelySelectsMatter","auxiliaryUVSolved","bouquetClaimNew"])
    assert.throws(()=>P.enforceClaimPolicy({[k]:true}),/claim firewall rejected/);
});

test("tampering the n-party span is detected",()=>{
  const b=bundle();b.depth3=structuredClone(b.depth3);
  b.depth3.phase_rank_certificates.find(x=>x.n===10).rank=19;
  assert.throws(()=>P.verifyContinuationBundle(b),/n=10 phase span not full/);
});

test("tampering W33 winding count is detected",()=>{
  const b=bundle();b.winding=structuredClone(b.winding);
  b.winding.examples.find(x=>x.q===3).Zq_flat_sector_count="0";
  assert.throws(()=>P.verifyContinuationBundle(b),/3\^81 sector count mismatch/);
});
