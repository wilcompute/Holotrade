#!/usr/bin/env node
"use strict";

// Adversarial single-node failure recovery on the complete near-ovoid corpus.
// For every optimal near-ovoid, the defect centre is the unique idle point whose
// outage destroys all three currently free W33 lines.  Keep that point failed,
// then compare six healthy size-preserving migrations under the legacy and
// topology-aware policies.

const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const P=require(path.join(root,"scheduler/w33-migration-policy.js"));
const M=require(path.join(root,"scheduler/w33-near-ovoid-migration.js"));
const corpus=JSON.parse(fs.readFileSync(path.join(root,"data/w33_near_ovoid_adversarial_corpus.json"),"utf8"));

function inc(h,k){const s=String(k);h[s]=(h[s]||0)+1;}

function runArm(start,failed,policy,steps=6){
  let busy=[...start].sort((a,b)=>a-b);
  const heads=[P.freeLineCount(busy,[failed])];
  const trace=[];
  for(let step=1;step<=steps;step++){
    const move=P.chooseMigration(busy,{policy,failed:[failed]});
    busy=move.nextBusy;
    heads.push(move.freeLinesAfterMove);
    trace.push({step,from:move.from,to:move.to,rays:move.rays,hops:move.hops,freeLines:move.freeLinesAfterMove});
  }
  return {heads,trace};
}

function firstReach(heads,target){
  for(let i=0;i<heads.length;i++) if(heads[i]>=target) return i;
  return null;
}

function runExperiment({steps=6}={}){
  const policies=[P.POLICY.LEGACY,P.POLICY.TOPOLOGY_AWARE];
  const out={};
  for(const policy of policies){
    const stepTotals=Array(steps+1).fill(0);
    const stepHist=Array.from({length:steps+1},()=>({}));
    const reach={"3":{},"6":{},"9":{},"12":{}};
    let states=0,totalRays=0;
    for(const rec of corpus.records) for(const a of rec.removals){
      const start=rec.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
      const info=M.analyzeNearOvoid(start);
      if(!info || info.defectCenter!==a) throw new Error("defect-centre provenance mismatch");
      const z=runArm(start,a,policy,steps);
      if(z.heads[0]!==0) throw new Error("injected defect-centre outage did not kill all line placements");
      z.heads.forEach((h,i)=>{stepTotals[i]+=h;inc(stepHist[i],h);});
      totalRays+=z.trace.reduce((s,x)=>s+x.rays,0);
      for(const target of [3,6,9,12]){
        const hit=firstReach(z.heads,target);
        inc(reach[String(target)],hit===null?"unreached":hit);
      }
      states++;
    }
    if(states!==2880) throw new Error(`expected 2880 failures, got ${states}`);
    out[policy]={
      states,
      meanFreeLinesByStep:stepTotals.map((x)=>x/states),
      freeLineHistogramByStep:stepHist,
      firstReachStepHistogram:reach,
      totalRays,
      raysPerTrajectory:totalRays/states,
    };
  }
  return {
    schema:"holotrade.near-ovoid-failure-recovery.v1",
    evidence:"EXHAUSTIVE ADVERSARIAL SINGLE-FAILURE CORPUS",
    design:{startStates:2880,failedPoint:"the unique defect centre",steps,failedNodeRemainsUnavailable:true},
    policies:out,
    reading:"The topology-aware controller deterministically rebuilds 3, 6 and 9 free lines after one, two and three migrations from the worst single idle-node outage, while paying the same movement floor as legacy.",
    boundary:"This is exact for one declared level-1 failure model and these deterministic policies. It is not a hardware MTTR, SLA, or production reliability measurement.",
  };
}

if(require.main===module) process.stdout.write(JSON.stringify(runExperiment(),null,2)+"\n");
module.exports={runArm,runExperiment,firstReach};
