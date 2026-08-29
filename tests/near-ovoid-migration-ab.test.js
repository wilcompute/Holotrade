"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const {runExperiment}=require("../experiments/near_ovoid_migration_ab.js");

test("microstate-aware near-ovoid migration weakly dominates ray-only source choice",()=>{
  const r=runExperiment();
  assert.equal(r.design.states,2880);
  assert.equal(r.summary.improvedStates,1682);
  assert.equal(r.summary.equalStates,1198);
  assert.equal(r.summary.rayOnlyHistogram["6"],1682);
  assert.equal(r.summary.rayOnlyHistogram["7"],1198);
  assert.equal(r.summary.awareHistogram["7"],2880);
  assert.equal(r.summary.bothArmsMigrationRays,3);
  assert.equal(r.summary.extraRayCostForAwarePolicy,0);
  assert.ok(Math.abs(r.summary.rayOnlyMeanFreeLines-6.415972222222222)<1e-12);
  assert.equal(r.summary.microstateAwareMeanFreeLines,7);
});
