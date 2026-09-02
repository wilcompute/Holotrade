"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const P=require(path.join(root,"scheduler/w33-migration-policy.js"));
const M=require(path.join(root,"scheduler/w33-near-ovoid-migration.js"));
const B=require(path.join(root,"scheduler/w33-near-ovoid-block-controller.js"));
const S2=require(path.join(root,"scheduler/w33-near-ovoid-stage2-controller.js"));
const CrossDc=require(path.join(root,"experiments/w33_crossdc_energy_tiebreak.js"));
const corpus=require(path.join(root,"analysis/w33_near_ovoid_corpus.js")).buildCorpus();
function read(name){return JSON.parse(fs.readFileSync(path.join(root,"data",name),"utf8"));}

test("post-first controller exactly reproduces generic topology-aware move two",()=>{
  let states=0,distinct=new Set();
  for(const r of corpus.records)for(const a of r.removals){
    const start=r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
    const first=P.chooseMigration(start,{policy:P.POLICY.TOPOLOGY_AWARE});
    distinct.add(first.nextBusy.join(","));
    const compact=S2.chooseSecondMove(first.nextBusy);
    const generic=P.chooseMigration(first.nextBusy,{policy:P.POLICY.TOPOLOGY_AWARE});
    assert.deepEqual([compact.from,compact.to],[generic.from,generic.to]);
    assert.equal(compact.rays,3);assert.equal(compact.hops,1);assert.equal(compact.freeLinesAfterMove,9);
    states++;
  }
  assert.equal(states,2880);assert.equal(distinct.size,2818);
});

test("one-bit RTL-equivalent source selector is objective-equivalent on all entry states",()=>{
  let states=0,exact=0;const blocks=[0,0];
  for(const r of corpus.records)for(const a of r.removals){
    const busy=r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y),state=B.classify(busy),move=B.chooseMove(busy),generic=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
    const rtlSource=state.block?state.residual[1]:state.residual[0];
    assert.equal(rtlSource,state.source);assert.ok(state.highRelease.includes(rtlSource));
    assert.equal(move.rays,generic.rays);assert.equal(move.hops,generic.hops);assert.equal(move.freeLinesAfterMove,generic.freeLinesAfterMove);
    blocks[state.block]++;if(move.from===generic.from&&move.to===generic.to)exact++;states++;
  }
  assert.equal(states,2880);assert.deepEqual(blocks,[1440,1440]);assert.equal(exact,664);
});

test("high-headroom attractor certificate is the rigid 19/19 graph type",()=>{
  const z=read("near_ovoid_attractor_structure.json");
  assert.equal(z.highBasinStarts,2255);assert.equal(z.distinctHighCycles,933);assert.equal(z.distinctHighStates,1866);
  assert.equal(z.state.inducedGraphIsomorphismTypes,1);assert.equal(z.state.automorphismGroup.order,16);assert.equal(z.state.automorphismGroup.structure,"D8 x C2");
  assert.equal(z.state.tripleHitLinesAlwaysDisjoint,true);
});

test("two-failure certificate has universal 1/2/3 recovery through nine lines",()=>{
  const z=read("near_ovoid_double_failure_recovery.json");
  assert.equal(z.design.cases,83520);assert.deepEqual(z.topologyAware.universalThresholds,{free3:1,free6:2,free9:3});
  assert.equal(Object.values(z.relationCases).reduce((a,b)=>a+b,0),83520);
});

test("actual fleet energy boundary forbids a level-1 point energy tie-break",()=>{
  const z=read("near_ovoid_actual_fleet_energy.json");
  assert.equal(z.withinLevel1CellSingleDatacenter,true);assert.equal(z.withinLevel1CellEnergyIndexConstant,true);assert.equal(z.energyCanBreakLevel1PointTie,false);
});

test("cross-DC energy sensitivity certificate exactly replays its executable",()=>{
  const frozen=read("w33_crossdc_energy_tiebreak.json"),actual=CrossDc.run();
  assert.deepEqual(actual,frozen);
  assert.equal(actual.primaryCost.preservedForAllSources,true);
  assert.equal(actual.energyIndex.relativeReduction,0.12625608249948786);
  assert.equal(actual.carbonIndex.relativeReduction,0.24745875687385435);
  assert.match(actual.boundary,/not live telemetry/);
  assert.match(actual.boundary,/does not claim measured energy savings/);
});

test("FSM certificate states objective equivalence, not exact generic action identity",()=>{
  const z=read("near_ovoid_recovery_fsm.json");
  assert.equal(z.stateBits,1);assert.equal(z.selectedSourceIsHighRelease,2880);assert.equal(z.postMoveHeadroomEquivalence.states,2880);
  assert.equal(z.exactGenericMoveIdentityMatches,664);assert.equal(z.exactGenericMoveIdentityMismatches,2216);
});
