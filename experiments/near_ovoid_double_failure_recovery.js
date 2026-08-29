#!/usr/bin/env node
"use strict";

// Exhaustive two-idle-node failure recovery.  The first failed node is always
// the near-ovoid defect centre (the unique idle point that kills all three
// current placements); the second ranges over the other 29 idle points.
// Relation classes are measured relative to the defect centre.

const S=require("../js/substrate.js");
const P=require("../scheduler/w33-migration-policy.js");
const M=require("../scheduler/w33-near-ovoid-migration.js");
const {buildCorpus}=require("../analysis/w33_near_ovoid_corpus.js");

function inc(h,k){k=String(k);h[k]=(h[k]||0)+1;}
function relation(info,q){if(q===info.blockerCenter)return "adjacent:blocker-center";return S.isAdjacent(info.defectCenter,q)?"adjacent:other":"nonadjacent";}
function firstReach(heads,t){for(let i=0;i<heads.length;i++)if(heads[i]>=t)return i;return null;}
function runArm(start,failed,policy,steps){let busy=[...start];const heads=[P.freeLineCount(busy,failed)];for(let i=0;i<steps;i++){const z=P.chooseMigration(busy,{policy,failed});busy=z.nextBusy;heads.push(z.freeLinesAfterMove);}return heads;}

function runExperiment({steps=6}={}){
  const corpus=buildCorpus(),classes=["adjacent:blocker-center","adjacent:other","nonadjacent"],out={};
  for(const policy of [P.POLICY.LEGACY,P.POLICY.TOPOLOGY_AWARE]){
    const by={};for(const c of classes)by[c]={cases:0,stepTotals:Array(steps+1).fill(0),reach:{"3":{},"6":{},"9":{},"12":{}}};
    for(const rec of corpus.records)for(const a of rec.removals){
      const start=rec.blocker.filter((x)=>x!==a).sort((x,y)=>x-y),info=M.analyzeNearOvoid(start);
      if(!info||info.defectCenter!==a)throw new Error("near-ovoid provenance mismatch");
      const busySet=new Set(start);
      for(let q=0;q<40;q++){
        if(q===a||busySet.has(q))continue;
        const c=relation(info,q),failed=[a,q],heads=runArm(start,failed,policy,steps),z=by[c];
        if(heads[0]!==0)throw new Error("defect-centre pair did not kill initial availability");
        z.cases++;heads.forEach((h,i)=>z.stepTotals[i]+=h);
        for(const t of [3,6,9,12]){const r=firstReach(heads,t);inc(z.reach[String(t)],r===null?"unreached":r);}
      }
    }
    for(const c of classes){by[c].meanFreeLinesByStep=by[c].stepTotals.map((x)=>x/by[c].cases);delete by[c].stepTotals;}
    out[policy]=by;
  }
  const total=classes.reduce((s,c)=>s+out[P.POLICY.TOPOLOGY_AWARE][c].cases,0);
  if(total!==83520)throw new Error(`expected 83520 failure pairs, got ${total}`);
  return {schema:"holotrade.near-ovoid-double-failure-recovery.v1",evidence:"EXHAUSTIVE FINITE TWO-IDLE-FAILURE CORPUS",design:{firstFailure:"defect centre",secondFailure:"each other idle point",cases:total,steps,failedNodesRemainUnavailable:true},policies:out,reading:"Topology-aware recovery reaches 3/6/9 free lines after exactly 1/2/3 migrations for every one of the 83,520 two-failure cases; the second failure relation first changes the 12-line recovery distribution.",boundary:"Exact for this declared two-idle-node failure model and deterministic policies; not a hardware MTTR/SLA measurement."};
}
if(require.main===module)process.stdout.write(JSON.stringify(runExperiment(),null,2)+"\n");
module.exports={runExperiment};
