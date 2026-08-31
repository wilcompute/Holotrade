#!/usr/bin/env node
"use strict";

// Full Koopman/Jordan census of the deterministic topology-aware recovery map
// on the forward closure of all 2,880 certified near-ovoid starts.
//
// For Kf=f∘T, rank(K^j)=|Im(T^j)|.  After removing the eventual cycle image,
// r_j=rank(K^j)-N_cycle obeys r_j=sum_s n_s max(s-j,0), where n_s is the
// number of zero-eigenvalue Jordan blocks of size s.  Thus the complete zero
// Jordan partition follows from finite differences of exact image sizes.

const {buildCorpus}=require("./w33_near_ovoid_corpus.js");
const P=require("../scheduler/w33-migration-policy.js");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function parse(k){return k.split(",").map(Number);}
function freeLines(busy){
  const B=new Set(busy);return require("../js/substrate.js").LINES.reduce((n,L)=>n+(L.every((p)=>!B.has(p))?1:0),0);
}

function run(){
  const corpus=buildCorpus();
  const starts=[];
  for(const rec of corpus.records) for(const a of rec.removals) starts.push(key(rec.blocker.filter((x)=>x!==a)));
  if(new Set(starts).size!==2880)throw new Error("start cardinality mismatch");

  const next=new Map(),queue=[...new Set(starts)];let qi=0;
  while(qi<queue.length){
    const k=queue[qi++];const move=P.chooseMigration(parse(k),{policy:P.POLICY.TOPOLOGY_AWARE});const n=key(move.nextBusy);
    next.set(k,n);if(!next.has(n)&&!queue.includes(n))queue.push(n);
  }
  const states=[...next.keys()];const stateSet=new Set(states);for(const n of next.values())if(!stateSet.has(n))throw new Error("closure incomplete");
  const N=states.length;

  // Exact functional-graph cycles and distance-to-cycle.
  const color=new Map(),cycles=[];
  for(const s of states){
    if(color.get(s)===2)continue;
    const path=[],pos=new Map();let x=s;
    while(color.get(x)!==2 && !pos.has(x)){
      pos.set(x,path.length);path.push(x);color.set(x,1);x=next.get(x);
    }
    if(pos.has(x))cycles.push(path.slice(pos.get(x)));
    for(const y of path)color.set(y,2);
  }
  if(!cycles.every((c)=>c.length===2))throw new Error("non-period-two cycle found");
  const cycleNodes=new Set(cycles.flat()),C=cycles.length,Nc=cycleNodes.size;

  const depth=new Map([...cycleNodes].map((x)=>[x,0]));
  function dep(x){
    if(depth.has(x))return depth.get(x);const d=1+dep(next.get(x));depth.set(x,d);return d;
  }
  for(const s of states)dep(s);
  const depthHist={};for(const d of depth.values())depthHist[d]=(depthHist[d]||0)+1;
  const maxDepth=Math.max(...depth.values());

  // Image ranks of K^j.  rank K^j equals number of distinct T^j images.
  const imageSizes=[];let img=new Set(states);imageSizes.push(img.size);
  for(let j=1;j<=maxDepth+2;j++){
    img=new Set([...img].map((x)=>next.get(x)));imageSizes.push(img.size);
  }
  if(imageSizes[imageSizes.length-1]!==Nc)throw new Error("image chain did not stabilize on cycles");

  const r=imageSizes.map((x)=>x-Nc);
  const jordan={};
  // exact blocks of size s = r_{s-1}-2r_s+r_{s+1}
  for(let s=1;s<=maxDepth;s++){
    const n=(r[s-1]||0)-2*(r[s]||0)+(r[s+1]||0);
    if(n)jordan[s]=n;
  }
  const zeroAlg=N-Nc;
  const checkAlg=Object.entries(jordan).reduce((z,[s,n])=>z+Number(s)*n,0);
  if(checkAlg!==zeroAlg)throw new Error(`Jordan partition mismatch ${checkAlg} != ${zeroAlg}`);

  const indeg=new Map(states.map((x)=>[x,0]));for(const y of next.values())indeg.set(y,indeg.get(y)+1);
  const indegHist={};for(const d of indeg.values())indegHist[d]=(indegHist[d]||0)+1;
  const cycleHeadroom={};for(const c of cycles){const h=c.map((x)=>freeLines(parse(x))).sort((a,b)=>a-b).join("/");cycleHeadroom[h]=(cycleHeadroom[h]||0)+1;}

  const out={schema:"holotrade.w33-recovery-koopman-full.v1",status:"PASS",
    stateSpace:{starts:2880,forwardClosure:N,cycleNodes:Nc,transientNodes:zeroAlg,maxTransientDepth:maxDepth},
    functionalGraph:{periodTwoCycles:C,cycleHeadroomDistinctCounts:cycleHeadroom,depthHistogram:depthHist,indegreeHistogram:indegHist},
    koopman:{
      convention:"K f = f o T on functions over the finite forward-closed state set",
      imageSizes,
      eigenvalues:{"+1":C,"-1":C,"0":zeroAlg},
      zeroJordanBlocks:jordan,
      characteristicPolynomial:`x^${zeroAlg} (x-1)^${C} (x+1)^${C}`,
      minimalPolynomial:`x^${maxDepth} (x^2-1)`
    },
    theorem:"The complete finite Koopman spectrum and zero-eigenvalue Jordan partition follow exactly from the functional graph. All nonzero modes are the +/-1 modes of period-two cycles; every transient degree of freedom belongs to the nilpotent zero sector.",
    boundary:"Exact deterministic finite-state dynamics for the declared topology-aware tie-break. This is not a unitary quantum evolution, thermodynamic Floquet spectrum, or production trace."};
  console.log(JSON.stringify(out,null,2));return out;
}
if(require.main===module)run();
module.exports={run};
