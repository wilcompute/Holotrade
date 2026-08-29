"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const P=require(path.join(root,"scheduler/w33-migration-policy.js"));
const M=require(path.join(root,"scheduler/w33-near-ovoid-migration.js"));
const C=require(path.join(root,"scheduler/w33-near-ovoid-block-controller.js"));
const corpus=require(path.join(root,"data/w33_near_ovoid_adversarial_corpus.json"));

function read(name){return JSON.parse(fs.readFileSync(path.join(root,"data",name),"utf8"));}

test("migration policy defaults to legacy and topology-aware is opt-in",()=>{
  const r=corpus.records[0];
  const busy=r.blocker.filter((x)=>x!==r.removals[0]);
  const implicit=P.chooseMigration(busy);
  const explicit=P.chooseMigration(busy,{policy:P.POLICY.LEGACY});
  assert.equal(implicit.policy,P.POLICY.LEGACY);
  assert.deepEqual([implicit.from,implicit.to],[explicit.from,explicit.to]);
  const aware=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
  assert.equal(aware.policy,P.POLICY.TOPOLOGY_AWARE);
  assert.equal(aware.rays,3);
  assert.equal(aware.hops,1);
});

test("the two-state block controller is exact on all 2880 near-ovoids",()=>{
  let states=0;
  const blocks=[0,0];
  for(const r of corpus.records) for(const a of r.removals){
    const busy=r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
    const info=M.analyzeNearOvoid(busy);
    const state=C.classify(busy);
    const move=C.chooseMove(busy);
    const full=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
    assert.ok(info&&state&&move);
    assert.equal(state.defectCenter,a);
    assert.ok(info.highRelease.includes(state.source));
    blocks[state.block]++;
    assert.equal(move.rays,3);
    assert.equal(move.hops,1);
    assert.equal(move.freeLinesAfterRelease,7);
    assert.equal(move.freeLinesAfterMove,6);
    assert.equal(move.freeLinesAfterMove,full.freeLinesAfterMove);
    states++;
  }
  assert.equal(states,2880);
  assert.deepEqual(blocks,[1440,1440]);
});

test("long-horizon certificate records universal period-two dynamics",()=>{
  const z=read("near_ovoid_migration_long_horizon.json");
  assert.equal(z.legacy.cycleLengthHistogram["2"],2880);
  assert.equal(z.topologyAware.cycleLengthHistogram["2"],2880);
  assert.equal(z.topologyAware.cycleHeadroomHistogram["19/19"],2255);
  assert.ok(z.relativeCumulativeHeadroomGain32>1.99);
});

test("worst single-node failure recovery certificate keeps theorem boundary explicit",()=>{
  const z=read("near_ovoid_failure_recovery.json");
  assert.equal(z.topologyAware.firstReach["3"]["1"],2880);
  assert.equal(z.topologyAware.firstReach["6"]["2"],2880);
  assert.equal(z.topologyAware.firstReach["9"]["3"],2880);
  assert.equal(z.topologyAware.raysPerTrajectory,z.legacy.raysPerTrajectory);
  assert.match(z.boundary,/not a hardware failure-rate/i);
});

test("secondary-cost certificate preserves movement floor and labels energy as sensitivity",()=>{
  const z=read("near_ovoid_secondary_costs.json");
  assert.equal(z.locality.result,"NO SECONDARY TRADEOFF AT LEVEL 1");
  assert.ok(z.relativeEnergyIndexReduction>0.36);
  assert.ok(z.energySecondary.totalEnergyIndex<z.lexicographicTopologyAware.totalEnergyIndex);
  assert.match(z.boundary,/not live telemetry/i);
});
