const assert=require("node:assert/strict");
const test=require("node:test");
global.window=global;
const E=require("../js/evidence.js");
require("../js/uor.js");
require("../js/w33-scheduler.js");
require("../js/spread-venue-market.js");
require("../js/hypercube.js");
require("../js/chart-spread-bridge.js");
require("../js/spread-harmonics.js");
require("../js/gluing.js");
const Cap=require("../js/capability-market.js");
require("../js/tensor-sharding.js");
const F=require("../js/w33-frontier-certificates.js");
const Calendar=require("../js/chart-calendar-fusion.js");
const PG=require("../js/policy-gluing.js");
const CT=require("../js/capability-transition.js");
const TF=require("../js/tensor-frontier.js");

test("all 36 spread anchors retain 15 near, 20 remote, and ten Johnson-antipode hedge pairs",()=>{
  const c=F.allAnchorCertificate();assert.equal(c.valid,true);assert.equal(c.theorem.everyNear15,true);assert.equal(c.theorem.everyRemote20,true);assert.equal(c.theorem.everyTenAntipodes,true);
  for(let line=0;line<40;line++){const s=F.lineFiberSchedule(line);assert.equal(s.valid,true);assert.deepEqual(s.groups.map(g=>g.spreads.length),[3,3,3]);}
});

test("spread clique GF(2) homology is exact and the Reye incidence kernel is [16,8,4]",()=>{
  const h=F.spreadCliqueHomology();assert.equal(h.valid,true);assert.deepEqual(h.fVector,[36,270,540,135]);assert.deepEqual(h.boundaryRanks,[35,235,135]);assert.deepEqual(h.betti,[1,0,170,0]);
  const r=F.reyeCode();assert.equal(r.valid,true);assert.equal(r.rank,8);assert.equal(r.nullity,8);assert.equal(r.minimumKernelWeight,4);assert.deepEqual(r.kernelWeightEnumerator,{0:1,4:12,6:64,8:102,10:64,12:12,16:1});assert.equal(r.rowCodeKernelIntersectionDimension,6);assert.equal(r.theorem.notSelfDual,true);
});

test("proper eight-batch calendar fuses with all 540 chart triangles and 1+15+20 spread harmonics",()=>{
  const c=Calendar.certificate();assert.equal(c.valid,true);assert.equal(c.counts.charts,540);assert.equal(c.counts.chartSpreadFlags,1620);assert.equal(c.counts.batches,8);assert.deepEqual(c.classes.map(x=>x.length).sort((a,b)=>a-b),[4,4,4,4,5,5,5,5]);assert.equal(c.theorem.everyChartTriangleUsesThreeDistinctColours,true);assert.deepEqual(c.harmonicRanks,{constant:1,harmonic15:15,harmonic20:20});
});

test("finite policy gluing intersects authority, unions obligations, raises evidence floor, and fails with witnesses",()=>{
  const good=PG.gluePolicy([{id:"a",values:{net:{zone:"east"}},authorities:["ops","sec"],obligations:["log"],evidencePolicy:E.POLICY.RESEARCH},{id:"b",values:{net:{zone:"east"},cpu:{isa:"x86"}},authorities:["sec","audit"],obligations:["retain"],evidencePolicy:E.POLICY.VERIFIED}],{requiredPaths:["net.zone","cpu.isa"]});
  assert.equal(good.ok,true);assert.deepEqual(good.authorities,["sec"]);assert.deepEqual(good.obligations,["log","retain"]);assert.equal(good.evidencePolicy,E.POLICY.VERIFIED);
  const bad=PG.gluePolicy([{id:"a",values:{net:{zone:"east"}},authorities:["ops"]},{id:"b",values:{net:{zone:"west"}},authorities:["sec"]}],{requiredPaths:["net.zone","missing.path"]});
  assert.equal(bad.ok,false);assert.ok(bad.conflicts.some(x=>x.path==="net.zone"));assert.ok(bad.conflicts.some(x=>x.code==="EMPTY_AUTHORITY_INTERSECTION"));assert.deepEqual(bad.missing,["missing.path"]);
});

test("capability transition receipt remains immutable while superseded evidence blocks future admission",()=>{
  const ledger=new E.EvidenceLedger();ledger.add({id:"base",status:E.STATUS.VERIFIED,evidenceClass:E.EVIDENCE_CLASS.REPO_CERTIFICATE,scope:E.SCOPE.EXACT,claim:"base profile",createdAt:1});ledger.add({id:"offer-proof",status:E.STATUS.VERIFIED,evidenceClass:E.EVIDENCE_CLASS.FORMAL_WITNESS,scope:E.SCOPE.FORMAL,claim:"offer proof",createdAt:1});
  const profile=Cap.profileResource({nodeId:"N",hardwareKind:"gpu",capabilities:["fp16"],evidenceRefs:["base"]});const offer=new Cap.CapabilityOffer({id:"int8",vendor:"v",capabilities:["int8"],hardwareKinds:["gpu"],evidenceRefs:["offer-proof"],price:1});
  const receipt=CT.transition(profile,offer,ledger,{createdAt:2});assert.equal(receipt.status,"COMMITTED");assert.deepEqual(receipt.newProfile.metadata.capabilities,["fp16","int8"]);const digest=receipt.digest;assert.equal(CT.currentAdmission(receipt,ledger).admitted,true);
  ledger.add({id:"offer-proof-v2",status:E.STATUS.VERIFIED,evidenceClass:E.EVIDENCE_CLASS.FORMAL_WITNESS,scope:E.SCOPE.FORMAL,claim:"superseding proof",supersedes:["offer-proof"],createdAt:3});assert.equal(CT.currentAdmission(receipt,ledger).admitted,false);assert.equal(receipt.digest,digest);assert.equal(receipt.status,"COMMITTED");
});

test("tensor frontier preserves [110,121] and certifies the tight eigen-equation prerequisite without overclaiming closure",()=>{
  const c=TF.tightNecessaryConditions();assert.equal(c.valid,true);assert.deepEqual(c.interval,[110,121]);assert.equal(c.exactTau,null);assert.equal(c.searchStatus.startsWith("OPEN"),true);assert.equal(c.theorem.incidenceGram4IplusA,true);assert.equal(c.tightNecessaryEquation,"(A + 4 I) r = 44 * 1");
});
