#!/usr/bin/env node
"use strict";

// Geometric PSp(4,3) audit of the deterministic 19/19 recovery attractor.
// The policy uses lexicographic tie-breaking, so its 933 cycles need not be a
// PSp-invariant subset.  This script measures the ambient geometric orbit rather
// than silently treating a policy-labelled set as a G-set.

const S=require("../js/substrate.js");
const P=require("../scheduler/w33-migration-policy.js");
const {buildCorpus}=require("./w33_near_ovoid_corpus.js");

function keyState(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function keyCycle(c){return c.map(keyState).sort().join("|");}
function freeCount(state){const B=new Set(state);return S.LINES.filter((L)=>!L.some((p)=>B.has(p))).length;}
function detect(start,cap=64){
  let state=[...start].sort((a,b)=>a-b);const seen=new Map([[keyState(state),0]]),seq=[state];
  for(let t=1;t<=cap;t++){
    state=P.chooseMigration(state,{policy:P.POLICY.TOPOLOGY_AWARE}).nextBusy;
    const k=keyState(state);
    if(seen.has(k)){const mu=seen.get(k);return {mu,lambda:t-mu,cycle:seq.slice(mu,t)};}
    seen.set(k,t);seq.push(state);
  }
  throw new Error("cycle cap exceeded");
}
function norm(v){
  const z=v.map((x)=>((x%3)+3)%3);const lead=z.find((x)=>x!==0);if(lead==null)throw new Error("zero vector");
  const inv=lead===1?1:2;return z.map((x)=>(x*inv)%3);
}
function compose(p,q){return q.map((x)=>p[x]);}
function permKey(p){return p.join(",");}
function transvection(v,alpha){
  return S.POINTS.map((x)=>{
    const b=S.symplecticForm(x.vec,v);const y=norm(x.vec.map((z,i)=>(z+alpha*b*v[i])%3));
    const j=S.POINT_INDEX.get(y.join(""));if(j==null)throw new Error("projective point lookup failed");return j;
  });
}
function generatePSp(){
  const gens=[];for(const p of S.POINTS)for(const a of [1,2])gens.push(transvection(p.vec,a));
  const id=Array.from({length:40},(_,i)=>i),seen=new Map([[permKey(id),id]]),queue=[id];
  for(let qi=0;qi<queue.length;qi++){
    const g=queue[qi];for(const s of gens){const h=compose(s,g),k=permKey(h);if(!seen.has(k)){seen.set(k,h);queue.push(h);}}
  }
  if(seen.size!==25920)throw new Error(`expected PSp order 25920, got ${seen.size}`);
  return [...seen.values()];
}
function actState(g,s){return [...s].map((p)=>g[p]).sort((a,b)=>a-b);}
function actCycle(g,c){return [actState(g,c[0]),actState(g,c[1])].sort((a,b)=>keyState(a).localeCompare(keyState(b)));}

function run(){
  const corpus=buildCorpus(),starts=[];
  for(const r of corpus.records)for(const a of r.removals)starts.push(r.blocker.filter((x)=>x!==a));
  const high=new Map();
  for(const start of starts){const z=detect(start);if(z.lambda===2&&z.cycle.every((s)=>freeCount(s)===19))high.set(keyCycle(z.cycle),z.cycle);}
  if(high.size!==933)throw new Error(`expected 933 high cycles, got ${high.size}`);
  const rep=high.values().next().value,G=generatePSp();
  const cycleOrbit=new Set(),stateOrbit=new Set(),coreOrbit=new Set();
  const core=rep[0].filter((p)=>rep[1].includes(p));
  for(const g of G){cycleOrbit.add(keyCycle(actCycle(g,rep)));stateOrbit.add(keyState(actState(g,rep[0])));coreOrbit.add(keyState(actState(g,core)));}
  const intersection=[...cycleOrbit].filter((k)=>high.has(k)).length;
  if(cycleOrbit.size!==12960||stateOrbit.size!==6480||coreOrbit.size!==1440||intersection!==933)throw new Error("ambient orbit invariant failed");
  return {
    schema:"holotrade.w33-attractor-psp-orbit.v1",status:"PASS",
    group:{name:"PSp(4,3)",order:G.length},
    policyAttractor:{highCycles:933,pspInvariant:false,reason:"the declared deterministic policy uses label-lexicographic tie-breaking"},
    ambientGeometry:{
      unorderedCycleOrbitSize:cycleOrbit.size,unorderedCycleStabilizer:G.length/cycleOrbit.size,
      stateOrbitSize:stateOrbit.size,stateStabilizer:G.length/stateOrbit.size,
      coreOrbitSize:coreOrbit.size,coreStabilizer:G.length/coreOrbit.size,
      policyCyclesInAmbientOrbit:intersection
    },
    theorem:"All 933 policy-selected 19/19 cycles are embeddings of one PSp geometric cycle type, but the 933-element policy subset is not a PSp G-set. The full unordered geometric orbit has 12,960 cycles.",
    boundary:"Exact finite group/action statement. It separates intrinsic W33 geometry from symmetry breaking introduced by deterministic label tie-breaking."
  };
}
if(require.main===module)process.stdout.write(JSON.stringify(run(),null,2)+"\n");
module.exports={run,generatePSp};
