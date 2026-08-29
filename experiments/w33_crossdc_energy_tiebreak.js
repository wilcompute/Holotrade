#!/usr/bin/env node
"use strict";

// Seeded-fleet cross-datacenter migration sensitivity using the ACTUAL address
// model.  Unlike the older level-1 point->site sensitivity field, this experiment
// compares full addresses and only lets energy/carbon break ties AFTER exact
// rays/hops equality.

global.window=global;
const S=require("../js/substrate.js");
const {Fleet}=require("../js/fleet.js");
const {DATACENTERS,HARDWARE,WORKLOADS,OPERATORS}=require("../data/catalog.js");

function run(){
  const fleet=new Fleet({datacenters:DATACENTERS,hardware:HARDWARE,workloads:WORKLOADS,operators:OPERATORS,size:320,seed:"holotrade-fleet"});
  const dc=new Map(DATACENTERS.map((d)=>[d.id,d]));
  let lexEnergy=0,awareEnergy=0,lexCarbon=0,awareCarbon=0,changed=0;
  let minTie=Infinity,maxTie=0;const sourceDcCounts={},transitionCounts={};
  for(const source of fleet.nodes){
    let best=null,candidates=[];
    for(const target of fleet.nodes){
      if(target.id===source.id||target.dcId===source.dcId)continue;
      const c=S.migrationCost(source.addr,target.addr),key=[c.rays,c.hops];
      if(best===null||key[0]<best[0]||(key[0]===best[0]&&key[1]<best[1])){best=key;candidates=[target];}
      else if(key[0]===best[0]&&key[1]===best[1])candidates.push(target);
    }
    candidates.sort((a,b)=>a.seq-b.seq);const lex=candidates[0];
    const aware=[...candidates].sort((a,b)=>{
      const da=dc.get(a.dcId),db=dc.get(b.dcId),ea=da.baseEnergy*da.pue,eb=db.baseEnergy*db.pue;
      return (ea-eb)||(da.carbon-db.carbon)||(a.seq-b.seq);
    })[0];
    if(best[0]!==7||best[1]!==33)throw new Error("seeded fleet cross-DC cost frontier changed");
    minTie=Math.min(minTie,candidates.length);maxTie=Math.max(maxTie,candidates.length);
    const dl=dc.get(lex.dcId),da=dc.get(aware.dcId);
    lexEnergy+=dl.baseEnergy*dl.pue;awareEnergy+=da.baseEnergy*da.pue;lexCarbon+=dl.carbon;awareCarbon+=da.carbon;
    if(lex.id!==aware.id)changed++;
    sourceDcCounts[source.dcId]=(sourceDcCounts[source.dcId]||0)+1;
    const tk=`${source.dcId}->${lex.dcId}|${aware.dcId}`;transitionCounts[tk]=(transitionCounts[tk]||0)+1;
  }
  const round=(x)=>Math.round(x*1e6)/1e6;
  const out={schema:"holotrade.w33-crossdc-energy-tiebreak.v1",status:"PASS",seed:"holotrade-fleet",sources:fleet.nodes.length,
    primaryCost:{rays:7,hops:33,preservedForAllSources:true},equalCostCandidateRange:[minTie,maxTie],changedDestinations:changed,
    sourceDcCounts,
    energyIndex:{lexicographic:round(lexEnergy),energyAware:round(awareEnergy),relativeReduction:(lexEnergy-awareEnergy)/lexEnergy},
    carbonIndex:{lexicographic:lexCarbon,energyAware:awareCarbon,relativeReduction:(lexCarbon-awareCarbon)/lexCarbon},transitionCounts,
    reading:"Site energy and carbon become legitimate secondary objectives only after moving above the level-1 cell and comparing full-address cross-DC candidates at equal rays/hops cost.",
    boundary:"Catalog baseEnergy, PUE and carbon are seeded prototype inputs, not live telemetry. The experiment preserves the exact topology price ordering and does not claim measured energy savings."};
  if(out.sources!==320||changed!==148||round(lexEnergy)!==15505.55||round(awareEnergy)!==13547.88||lexCarbon!==96016||awareCarbon!==72256)throw new Error("frozen seeded-fleet result changed");
  return out;
}
if(require.main===module)process.stdout.write(JSON.stringify(run(),null,2)+"\n");
module.exports={run};
