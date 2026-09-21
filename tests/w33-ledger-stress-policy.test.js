"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const P=require("../js/w33-ledger-stress-policy.js");

function load(name){
  const root=process.env.W33_LEDGER_ROOT;
  assert.ok(root,"W33_LEDGER_ROOT is required for cross-repo Ledger verification");
  return JSON.parse(fs.readFileSync(path.join(root,"data",name),"utf8"));
}
function bundle(){return {
  suite:load("PART_LEDGER_STRESS_SUITE.json"),
  modular:load("PART_LEDGER_MODULAR_CHARACTER_STRESS_TEST.json"),
  mirror:load("PART_LEDGER_MIRROR_GROUP_STRESS_TEST.json"),
  audit:load("PART_LEDGER_QUTRIT_AUDIT_COMPLETENESS.json"),
  monopole:load("PART_LEDGER_MONOPOLE_COHOMOLOGY.json"),
  dark:load("PART_LEDGER_DARK_BOND_NO_GO.json")
};}

test("W33 Ledger suite is admitted only as a finite structural program",()=>{
  const v=P.verifyLedgerStressBundle(bundle());
  assert.equal(v.validFiniteProgram,true);
  assert.equal(v.claimAdmission,false);
  assert.equal(v.admitted.length,3);
  assert.equal(v.blocked.length,4);
});

test("claim firewall rejects the two corrected claims and unproved identifications",()=>{
  for(const k of ["ledgerUniversalLaw","tomitaEqualsGeometricMirror","universalNoMonopoles","qutritDepth2Completeness","darkBondH4AsWritten"]){
    assert.throws(()=>P.enforceClaimPolicy({[k]:true}),/Ledger claim firewall rejected/);
  }
  assert.equal(P.enforceClaimPolicy({finiteStructuralBridge:true,qutritDepth3Repair:true}),true);
});

test("tampering with exact qutrit depth-two rank is detected",()=>{
  const b=bundle();
  b.audit=structuredClone(b.audit);
  b.audit.qutrit_trials[0].rank_depth2=729;
  assert.throws(()=>P.verifyLedgerStressBundle(b),/qutrit correction witness mismatch/);
});
