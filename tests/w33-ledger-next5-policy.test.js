"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const P=require("../js/w33-ledger-next5-policy.js");
function load(name){
  const root=process.env.W33_LEDGER_ROOT;assert.ok(root,"W33_LEDGER_ROOT required");
  return JSON.parse(fs.readFileSync(path.join(root,"data",name),"utf8"));
}
function bundle(){return {
  aggregate:load("PART_LEDGER_NEXT5_2026_09_21.json"),
  audit:load("PART_LEDGER_AUDIT_DEPTH3_ALLQ.json"),
  tomita:load("PART_LEDGER_TOMITA_MIRROR_FOLD.json"),
  h2:load("PART_LEDGER_ALLQ_H2.json"),
  dark:load("PART_LEDGER_DARK_BOND_ROUTE_CENSUS.json"),
  def80:load("PART_LEDGER_DEFICIENCY80_INVARIANCE.json")
};}

test("next-five W33 packet verifies and keeps candidate/theorem grades separate",()=>{
  const v=P.verifyNext5Bundle(bundle());
  assert.equal(v.valid,true);assert.equal(v.admitted.length,3);assert.equal(v.candidates.length,1);assert.equal(v.blocked.length,5);
});

test("next-five claim firewall blocks superseded readings",()=>{
  for(const k of ["depthEqualsQ","tomitaStateDependent540","deficiency80BuildingModule","interactionFreeDarkBond","auxiliaryHiggsProtectionProven"])
    assert.throws(()=>P.enforceClaimPolicy({[k]:true}),/claim firewall rejected/);
  assert.equal(P.enforceClaimPolicy({foldedTomitaMirror:true,allqH2:true,depth3OpenFamily:true}),true);
});

test("tampering q5 depth-three closure is detected",()=>{
  const b=bundle();b.audit=structuredClone(b.audit);
  b.audit.certificates.find(x=>x.q===5).depth3_labels=15624;
  assert.throws(()=>P.verifyNext5Bundle(b),/q=5 depth3 not full/);
});

test("tampering the 80-deficiency Clifford hull is detected",()=>{
  const b=bundle();b.def80=structuredClone(b.def80);b.def80.symmetry_test.rank_A2_plus_conjugate_A2=728;
  assert.throws(()=>P.verifyNext5Bundle(b),/Clifford hull/);
});
