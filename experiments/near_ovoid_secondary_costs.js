#!/usr/bin/env node
"use strict";

// Secondary-objective sensitivity experiment.
//
// Primary migration order is NEVER changed: minimise rays, then hops, then the
// topology-aware headroom scores.  At level 1 all selected moves sit at 3 rays
// / 1 hop, so the locality objective is already tied.  Energy is not intrinsic
// to a W33 point, so this experiment declares a synthetic-but-reproducible
// catalog mapping: assign every point to its nearest one-digit datacenter prefix
// in W33 distance, with catalog order breaking distance ties, and score that
// destination by baseEnergy * PUE.  This is sensitivity evidence, not telemetry.

const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const S=require(path.join(root,"js/substrate.js"));
const P=require(path.join(root,"scheduler/w33-migration-policy.js"));
const {DATACENTERS}=require(path.join(root,"data/catalog.js"));
const corpus=JSON.parse(fs.readFileSync(path.join(root,"data/w33_near_ovoid_adversarial_corpus.json"),"utf8"));

const anchors=DATACENTERS.map((dc,i)=>({
  i,id:dc.id,point:dc.prefix[0],score:dc.baseEnergy*dc.pue,
}));

function pointDistance(a,b){
  if(a===b) return 0;
  return S.isAdjacent(a,b)?1:2;
}

const pointSite=Array.from({length:40},(_,p)=>{
  let best=null;
  for(const a of anchors){
    const d=pointDistance(p,a.point);
    if(!best || d<best.distance || (d===best.distance && a.i<best.i)) best={...a,distance:d};
  }
  return best;
});

function runArm(start,{energySecondary=false,steps=6}={}){
  let busy=[...start].sort((a,b)=>a-b);
  const trace=[];
  for(let step=1;step<=steps;step++){
    const move=P.chooseMigration(busy,{
      policy:P.POLICY.TOPOLOGY_AWARE,
      destinationScore:energySecondary?(to)=>pointSite[to].score:null,
    });
    busy=move.nextBusy;
    trace.push({
      step,from:move.from,to:move.to,rays:move.rays,hops:move.hops,
      freeLines:move.freeLinesAfterMove,
      site:pointSite[move.to].id,
      energyIndex:pointSite[move.to].score,
    });
  }
  return trace;
}

function runExperiment({steps=6}={}){
  const arms={lexicographic:{energySecondary:false},energySecondary:{energySecondary:true}};
  const out={};
  for(const [name,opts] of Object.entries(arms)){
    const energyByStep=Array(steps).fill(0),headByStep=Array(steps).fill(0),siteHistogram={};
    let states=0,totalEnergyIndex=0,totalHeadroom=0;
    for(const rec of corpus.records) for(const a of rec.removals){
      const start=rec.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
      const trace=runArm(start,{...opts,steps});
      for(let i=0;i<trace.length;i++){
        const z=trace[i];
        if(z.rays!==3 || z.hops!==1) throw new Error("secondary objective changed the primary movement floor");
        energyByStep[i]+=z.energyIndex;
        headByStep[i]+=z.freeLines;
        siteHistogram[z.site]=(siteHistogram[z.site]||0)+1;
        totalEnergyIndex+=z.energyIndex;
        totalHeadroom+=z.freeLines;
      }
      states++;
    }
    out[name]={
      states,
      meanEnergyIndexByStep:energyByStep.map((x)=>x/states),
      meanFreeLinesByStep:headByStep.map((x)=>x/states),
      totalEnergyIndex,totalHeadroom,siteHistogram,
    };
  }
  return {
    schema:"holotrade.near-ovoid-secondary-costs.v1",
    evidence:"CATALOG-ANCHORED SENSITIVITY EXPERIMENT",
    mapping:{
      rule:"nearest W33 distance to the six catalog one-digit datacenter prefixes; catalog order breaks distance ties",
      score:"baseEnergy * PUE",
      anchors,
      pointCounts:Object.fromEntries(anchors.map((a)=>[a.id,pointSite.filter((x)=>x.id===a.id).length])),
    },
    locality:{result:"degenerate at level 1",why:"all selected moves in both arms remain 3 rays and 1 hop"},
    arms:out,
    boundary:"The energy field is a declared sensitivity mapping built from seed catalog figures, not live energy telemetry or an intrinsic W33 coordinate. The experiment may inform tie-break design but does not prove an energy saving in a physical deployment.",
  };
}

if(require.main===module) process.stdout.write(JSON.stringify(runExperiment(),null,2)+"\n");
module.exports={pointSite,runArm,runExperiment};
