#!/usr/bin/env node
"use strict";

// Full Koopman/Jordan census of the deterministic topology-aware recovery map
// on the forward closure of all 2,880 certified near-ovoid starts.  Besides the
// spectrum, this version resolves the apparent 6-vs-5 endpoint discrepancy at
// maximum depth by tracing the six depth-14 states through the actual W33
// geometry and recording the merge classes that support the five size-14
// Jordan blocks.

const {buildCorpus}=require("./w33_near_ovoid_corpus.js");
const P=require("../scheduler/w33-migration-policy.js");
const M=require("../scheduler/w33-near-ovoid-migration.js");
const S=require("../js/substrate.js");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function parse(k){return k.split(",").map(Number);}
function freeLines(busy){
  const B=new Set(busy);return S.LINES.reduce((n,L)=>n+(L.every((p)=>!B.has(p))?1:0),0);
}
function occProfile(busy){
  const B=new Set(busy),hist={};
  for(const L of S.LINES){const n=L.reduce((z,p)=>z+(B.has(p)?1:0),0);hist[n]=(hist[n]||0)+1;}
  return Object.fromEntries(Object.entries(hist).sort((a,b)=>Number(a[0])-Number(b[0])));
}
function inducedDegreeHistogram(busy){
  const B=[...busy],hist={};
  for(const p of B){let d=0;for(const q of B)if(q!==p&&S.isAdjacent(p,q))d++;hist[d]=(hist[d]||0)+1;}
  return Object.fromEntries(Object.entries(hist).sort((a,b)=>Number(a[0])-Number(b[0])));
}
function geom(k){
  const busy=parse(k),info=M.analyzeNearOvoid(busy);
  const out={busy,freeLines:freeLines(busy),lineOccupancyHistogram:occProfile(busy),inducedBusyDegreeHistogram:inducedDegreeHistogram(busy),nearOvoid:Boolean(info)};
  if(info)Object.assign(out,{defectCenter:info.defectCenter,blockerCenter:info.blockerCenter,hingeLine:info.hingeLine,chiralityAnchor:info.chiralityAnchor,chiralityBit:info.chiralityBit,highRelease:info.highRelease});
  return out;
}
function symdiff(a,b){const A=new Set(a),B=new Set(b);return [...new Set([...a,...b])].filter(x=>A.has(x)!==B.has(x)).sort((x,y)=>x-y);}

function run(){
  const corpus=buildCorpus();
  const starts=[];
  for(const rec of corpus.records) for(const a of rec.removals) starts.push(key(rec.blocker.filter((x)=>x!==a)));
  if(new Set(starts).size!==2880)throw new Error("start cardinality mismatch");

  const next=new Map(),moves=new Map(),queue=[...new Set(starts)];let qi=0;
  while(qi<queue.length){
    const k=queue[qi++];const move=P.chooseMigration(parse(k),{policy:P.POLICY.TOPOLOGY_AWARE});const n=key(move.nextBusy);
    next.set(k,n);moves.set(k,move);if(!next.has(n)&&!queue.includes(n))queue.push(n);
  }
  const states=[...next.keys()];const stateSet=new Set(states);for(const n of next.values())if(!stateSet.has(n))throw new Error("closure incomplete");
  const N=states.length;

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
  function dep(x){if(depth.has(x))return depth.get(x);const d=1+dep(next.get(x));depth.set(x,d);return d;}
  for(const s of states)dep(s);
  const depthHist={};for(const d of depth.values())depthHist[d]=(depthHist[d]||0)+1;
  const maxDepth=Math.max(...depth.values());

  const imageSizes=[];let img=new Set(states);imageSizes.push(img.size);
  for(let j=1;j<=maxDepth+2;j++){img=new Set([...img].map((x)=>next.get(x)));imageSizes.push(img.size);}
  if(imageSizes[imageSizes.length-1]!==Nc)throw new Error("image chain did not stabilize on cycles");
  const r=imageSizes.map((x)=>x-Nc),jordan={};
  for(let s=1;s<=maxDepth;s++){const n=(r[s-1]||0)-2*(r[s]||0)+(r[s+1]||0);if(n)jordan[s]=n;}
  const zeroAlg=N-Nc;
  const checkAlg=Object.entries(jordan).reduce((z,[s,n])=>z+Number(s)*n,0);
  if(checkAlg!==zeroAlg)throw new Error(`Jordan partition mismatch ${checkAlg} != ${zeroAlg}`);

  const indeg=new Map(states.map((x)=>[x,0]));for(const y of next.values())indeg.set(y,indeg.get(y)+1);
  const indegHist={};for(const d of indeg.values())indegHist[d]=(indegHist[d]||0)+1;
  const cycleHeadroom={};for(const c of cycles){const h=c.map((x)=>freeLines(parse(x))).sort((a,b)=>a-b).join("/");cycleHeadroom[h]=(cycleHeadroom[h]||0)+1;}

  // Geometry of the longest nilpotent sector.  Six states have depth 14, but
  // a size-14 Jordan block is counted by the five transient survivors in
  // Im(T^13)\cycle.  We trace all six heads and identify the deterministic
  // coalescence that turns six maximal-depth starts into five algebraic chains.
  const maxHeads=states.filter(x=>depth.get(x)===maxDepth).sort();
  if(maxDepth!==14||maxHeads.length!==6||Number(jordan[14])!==5)throw new Error("unexpected longest-chain census");
  function trajectory(h){const a=[h];while(depth.get(a[a.length-1])>0)a.push(next.get(a[a.length-1]));return a;}
  const paths=maxHeads.map(trajectory);
  if(!paths.every(p=>p.length===15))throw new Error("depth-14 path length mismatch");
  const survivorGroups=new Map();
  for(let i=0;i<maxHeads.length;i++){
    const tail=paths[i][13]; // depth-one survivor, i.e. T^13(head)
    if(!survivorGroups.has(tail))survivorGroups.set(tail,[]);
    survivorGroups.get(tail).push(i);
  }
  if(survivorGroups.size!==5)throw new Error("six heads do not resolve to five depth-one survivors");

  const mergePairs=[];
  for(let i=0;i<paths.length;i++)for(let j=i+1;j<paths.length;j++){
    let t=-1;for(let s=0;s<paths[i].length;s++)if(paths[i][s]===paths[j][s]){t=s;break;}
    if(t>=0){
      const rec={headIndices:[i,j],stepsFromHeads:t,mergeDepth:depth.get(paths[i][t]),mergeState:paths[i][t]};
      if(t>0){
        const pa=paths[i][t-1],pb=paths[j][t-1],ma=moves.get(pa),mb=moves.get(pb);
        rec.parents=[pa,pb];rec.parentSymmetricDifference=symdiff(parse(pa),parse(pb));
        rec.parentMoves=[{from:ma.from,to:ma.to,rays:ma.rays,hops:ma.hops},{from:mb.from,to:mb.to,rays:mb.rays,hops:mb.hops}];
      }
      mergePairs.push(rec);
    }
  }
  const longest=[];
  for(let i=0;i<maxHeads.length;i++){
    const p=paths[i],steps=[];
    for(let t=0;t<p.length;t++){
      const g=geom(p[t]);g.depth=depth.get(p[t]);
      if(t<p.length-1){const mv=moves.get(p[t]);g.move={from:mv.from,to:mv.to,rays:mv.rays,hops:mv.hops,freeLinesAfterRelease:mv.freeLinesAfterRelease,freeLinesAfterMove:mv.freeLinesAfterMove,usedNearOvoidMicrostate:mv.usedNearOvoidMicrostate};}
      steps.push(g);
    }
    longest.push({headIndex:i,head:maxHeads[i],depthOneSurvivor:p[13],cycleEntry:p[14],geometry:steps});
  }
  const longestClasses=[...survivorGroups.entries()].map(([tail,ids])=>({depthOneSurvivor:tail,headIndices:ids,headCount:ids.length,depthOneGeometry:geom(tail)})).sort((a,b)=>a.depthOneSurvivor.localeCompare(b.depthOneSurvivor));

  const out={schema:"holotrade.w33-recovery-koopman-full.v2",status:"PASS",
    stateSpace:{starts:2880,forwardClosure:N,cycleNodes:Nc,transientNodes:zeroAlg,maxTransientDepth:maxDepth},
    functionalGraph:{periodTwoCycles:C,cycleHeadroomDistinctCounts:cycleHeadroom,depthHistogram:depthHist,indegreeHistogram:indegHist},
    koopman:{convention:"K f = f o T on functions over the finite forward-closed state set",imageSizes,
      eigenvalues:{"+1":C,"-1":C,"0":zeroAlg},zeroJordanBlocks:jordan,
      characteristicPolynomial:`x^${zeroAlg} (x-1)^${C} (x+1)^${C}`,minimalPolynomial:`x^${maxDepth} (x^2-1)`},
    longestNilpotentGeometry:{depth:maxDepth,depth14States:maxHeads.length,size14JordanBlocks:Number(jordan[14]),
      depthOneSurvivorClasses:longestClasses,mergingHeadPairs:mergePairs,headTrajectories:longest,
      explanation:"The six depth-14 states are state-space leaves, whereas size-14 Jordan blocks are counted by independent image survivors. T^13 maps the six leaves to five distinct depth-one transient states; the deterministic merge therefore removes one algebraically independent longest chain."},
    theorem:"The complete finite Koopman spectrum and zero-eigenvalue Jordan partition follow exactly from the functional graph. The apparent six-depth-14 versus five-size-14 discrepancy is resolved by an explicit W33 trajectory merge: six maximal-depth states map onto only five depth-one survivors after 13 steps.",
    boundary:"Exact deterministic finite-state dynamics for the declared topology-aware tie-break. The geometric trajectory profiles are scheduler-state geometry, not a unitary quantum evolution, thermodynamic Floquet spectrum, or production trace."};
  console.log(JSON.stringify(out,null,2));return out;
}
if(require.main===module)run();
module.exports={run};
