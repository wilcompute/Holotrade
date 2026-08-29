#!/usr/bin/env node
"use strict";

// Long-horizon deterministic migration dynamics on all 2,880 optimal
// near-ovoids.  This experiment follows each declared policy until its first
// repeated state (or a generous safety cap) and also records a 32-step headroom
// integral.  It is exact for these finite policies, not production telemetry.

const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const P = require(path.join(root, "scheduler/w33-migration-policy.js"));
const corpus = JSON.parse(fs.readFileSync(
  path.join(root, "data/w33_near_ovoid_adversarial_corpus.json"), "utf8"
));

function key(busy) { return [...busy].sort((a,b)=>a-b).join(","); }
function inc(h, k) { const s=String(k); h[s]=(h[s]||0)+1; }

function runUntilCycle(start, policy, cap = 64) {
  let busy=[...start].sort((a,b)=>a-b);
  const seen=new Map([[key(busy),0]]);
  const heads=[];
  for (let step=1; step<=cap; step++) {
    const move=P.chooseMigration(busy,{policy});
    busy=move.nextBusy;
    heads.push(move.freeLinesAfterMove);
    const k=key(busy);
    if (seen.has(k)) {
      const transient=seen.get(k);
      const cycleLength=step-transient;
      return {
        transient, cycleLength, firstRepeatStep:step,
        cycleHeadroom:heads.slice(transient, transient+cycleLength),
        heads,
      };
    }
    seen.set(k,step);
  }
  throw new Error(`cycle not found within ${cap} steps`);
}

function runFixed(start, policy, steps=32) {
  let busy=[...start].sort((a,b)=>a-b), sum=0;
  const heads=[];
  for (let i=0;i<steps;i++) {
    const move=P.chooseMigration(busy,{policy});
    busy=move.nextBusy;
    heads.push(move.freeLinesAfterMove);
    sum+=move.freeLinesAfterMove;
  }
  return {heads,sum};
}

function runExperiment({horizon=32,cycleCap=64}={}) {
  const policies=[P.POLICY.LEGACY,P.POLICY.TOPOLOGY_AWARE];
  const out={};
  for (const policy of policies) {
    const transientHistogram={},cycleLengthHistogram={},cycleHeadroomHistogram={};
    const stepTotals=Array(horizon).fill(0);
    let cumulativeTotal=0, states=0;
    for (const rec of corpus.records) for (const a of rec.removals) {
      const start=rec.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
      const cyc=runUntilCycle(start,policy,cycleCap);
      const fixed=runFixed(start,policy,horizon);
      inc(transientHistogram,cyc.transient);
      inc(cycleLengthHistogram,cyc.cycleLength);
      inc(cycleHeadroomHistogram,[...cyc.cycleHeadroom].sort((x,y)=>x-y).join("/"));
      fixed.heads.forEach((h,i)=>{stepTotals[i]+=h;});
      cumulativeTotal+=fixed.sum;
      states++;
    }
    if (states!==2880) throw new Error(`expected 2880 starts, got ${states}`);
    out[policy]={
      states,horizon,
      transientHistogram,cycleLengthHistogram,cycleHeadroomHistogram,
      meanFreeLinesByStep:stepTotals.map((x)=>x/states),
      cumulativeHeadroomTotal:cumulativeTotal,
      cumulativeHeadroomMean:cumulativeTotal/states,
    };
  }
  return {
    schema:"holotrade.near-ovoid-migration-long-horizon.v1",
    evidence:"EXHAUSTIVE FINITE CORPUS / DETERMINISTIC POLICY DYNAMICS",
    design:{startStates:2880,horizon,cycleCap,busyCardinality:10},
    policies:out,
    reading:"Both declared deterministic policies eventually enter period-two state cycles. The topology-aware policy has a longer transient but settles into much higher-headroom two-cycles.",
    boundary:"Cycle statements apply to these exact deterministic tie-breaks on the certified finite corpus. They are not a theorem about every ray-minimising migration policy or a production workload trace.",
  };
}

if (require.main===module) process.stdout.write(JSON.stringify(runExperiment(),null,2)+"\n");
module.exports={runUntilCycle,runFixed,runExperiment};
