#!/usr/bin/env node
// Deterministic quantum-routing benchmark for W(3,3).
//
// This is a network-model experiment, not a quantum-device measurement and not
// a QKD security proof. It compares the exact W33 topology against two
// degree/size-matched classical control graphs while attaching explicit
// entanglement-generation, swap, memory, and visibility parameters.

"use strict";

const fs = require("node:fs");
const path = require("node:path");

function canon(v) {
  for (const x of v) {
    const a = ((x % 3) + 3) % 3;
    if (a !== 0) {
      const inv = a === 1 ? 1 : 2;
      return v.map((y) => ((inv * y) % 3 + 3) % 3);
    }
  }
  throw new Error("zero vector");
}

function key(v) { return v.join(","); }

function buildW33() {
  const map = new Map();
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++)
    for (let c = 0; c < 3; c++) for (let d = 0; d < 3; d++) {
      if (!(a || b || c || d)) continue;
      const v = canon([a,b,c,d]);
      map.set(key(v), v);
    }
  const points = [...map.values()].sort((x,y) => key(x).localeCompare(key(y)));
  if (points.length !== 40) throw new Error("W33 must have 40 projective points");
  const adj = Array.from({length:40}, () => new Set());
  const form = (x,y) => ((x[0]*y[2]-x[2]*y[0]+x[1]*y[3]-x[3]*y[1]) % 3 + 3) % 3;
  for (let i=0;i<40;i++) for (let j=i+1;j<40;j++) {
    if (form(points[i], points[j]) === 0) { adj[i].add(j); adj[j].add(i); }
  }
  if (![...adj].every((s) => s.size === 12)) throw new Error("W33 degree mismatch");
  return adj;
}

function edgesOf(adj) {
  const out=[];
  for (let i=0;i<adj.length;i++) for (const j of adj[i]) if (i<j) out.push([i,j]);
  return out;
}

function makeAdj(n, edges) {
  const adj=Array.from({length:n},()=>new Set());
  for (const [a,b] of edges) { adj[a].add(b); adj[b].add(a); }
  return adj;
}

function circulant40() {
  const adj=Array.from({length:40},()=>new Set());
  for (let i=0;i<40;i++) for (let d=1;d<=6;d++) {
    const j=(i+d)%40, k=(i-d+40)%40;
    adj[i].add(j); adj[j].add(i); adj[i].add(k); adj[k].add(i);
  }
  return adj;
}

function hashSeed(text) {
  let h=2166136261>>>0;
  for (const ch of String(text)) { h ^= ch.charCodeAt(0); h = Math.imul(h,16777619)>>>0; }
  return h>>>0;
}
function rng(seed) {
  let x=hashSeed(seed);
  return () => {
    x += 0x6D2B79F5;
    let t=x;
    t=Math.imul(t^(t>>>15),t|1);
    t^=t+Math.imul(t^(t>>>7),t|61);
    return ((t^(t>>>14))>>>0)/4294967296;
  };
}

function rewiredRegular(baseAdj, swaps=20000, seed="w33-qroute-control") {
  const rand=rng(seed);
  let edges=edgesOf(baseAdj).map((e)=>e.slice());
  const edgeSet=new Set(edges.map(([a,b])=>`${Math.min(a,b)}:${Math.max(a,b)}`));
  const ek=(a,b)=>`${Math.min(a,b)}:${Math.max(a,b)}`;
  let accepted=0;
  for (let step=0;step<swaps;step++) {
    const i=Math.floor(rand()*edges.length), j=Math.floor(rand()*edges.length);
    if (i===j) continue;
    const [a,b]=edges[i], [c,d]=edges[j];
    if (new Set([a,b,c,d]).size<4) continue;
    const flip=rand()<0.5;
    const e1=flip?[a,c]:[a,d], e2=flip?[b,d]:[b,c];
    if (e1[0]===e1[1]||e2[0]===e2[1]) continue;
    const k1=ek(...e1), k2=ek(...e2);
    const old1=ek(a,b), old2=ek(c,d);
    if ((edgeSet.has(k1)&&k1!==old1&&k1!==old2)||(edgeSet.has(k2)&&k2!==old1&&k2!==old2)||k1===k2) continue;
    edgeSet.delete(old1); edgeSet.delete(old2); edgeSet.add(k1); edgeSet.add(k2);
    edges[i]=e1[0]<e1[1]?e1:[e1[1],e1[0]];
    edges[j]=e2[0]<e2[1]?e2:[e2[1],e2[0]];
    accepted++;
  }
  const adj=makeAdj(baseAdj.length,edges);
  if (![...adj].every((s)=>s.size===12)) throw new Error("rewire broke regularity");
  return {adj, acceptedSwitches:accepted};
}

function bfs(adj,s,t,forbiddenNodes=new Set(),forbiddenEdges=new Set()) {
  if (forbiddenNodes.has(s)||forbiddenNodes.has(t)) return null;
  const q=[s], prev=Array(adj.length).fill(-2); prev[s]=-1;
  const ek=(a,b)=>`${Math.min(a,b)}:${Math.max(a,b)}`;
  for (let qi=0;qi<q.length;qi++) {
    const u=q[qi];
    for (const v of [...adj[u]].sort((a,b)=>a-b)) {
      if (forbiddenNodes.has(v)||forbiddenEdges.has(ek(u,v))||prev[v]!==-2) continue;
      prev[v]=u;
      if (v===t) {
        const p=[t]; let x=t;
        while (prev[x]!==-1) { x=prev[x]; p.push(x); }
        return p.reverse();
      }
      q.push(v);
    }
  }
  return null;
}

function vertexDisjointPaths(adj,s,t,maxPaths=4) {
  const forbiddenNodes=new Set(), forbiddenEdges=new Set(), paths=[];
  const ek=(a,b)=>`${Math.min(a,b)}:${Math.max(a,b)}`;
  for (let i=0;i<maxPaths;i++) {
    const p=bfs(adj,s,t,forbiddenNodes,forbiddenEdges);
    if (!p) break;
    paths.push(p);
    for (let j=1;j<p.length-1;j++) forbiddenNodes.add(p[j]);
    for (let j=0;j<p.length-1;j++) forbiddenEdges.add(ek(p[j],p[j+1]));
  }
  return paths;
}

function commonNeighborHistogram(adj) {
  const hist={};
  for (let i=0;i<adj.length;i++) for (let j=i+1;j<adj.length;j++) {
    if (adj[i].has(j)) continue;
    let n=0; for (const x of adj[i]) if (adj[j].has(x)) n++;
    hist[n]=(hist[n]||0)+1;
  }
  return hist;
}

function allPairsDistances(adj) {
  const hist={}; let diameter=0, disconnected=0;
  for (let s=0;s<adj.length;s++) for (let t=s+1;t<adj.length;t++) {
    const p=bfs(adj,s,t);
    if (!p) { disconnected++; continue; }
    const d=p.length-1; hist[d]=(hist[d]||0)+1; diameter=Math.max(diameter,d);
  }
  return {histogram:hist,diameter,disconnectedPairs:disconnected};
}

const MODELS=Object.freeze([
  Object.freeze({name:"nominal",pGenerate:0.78,pSwap:0.90,pMemory:0.995,vLink:0.97,vSwap:0.985,vMemory:0.995,minVisibility:0.75}),
  Object.freeze({name:"lossy",pGenerate:0.55,pSwap:0.82,pMemory:0.985,vLink:0.94,vSwap:0.97,vMemory:0.99,minVisibility:0.70}),
  Object.freeze({name:"stressed",pGenerate:0.35,pSwap:0.72,pMemory:0.96,vLink:0.90,vSwap:0.94,vMemory:0.98,minVisibility:0.65}),
]);

function pathModel(path,m) {
  const links=path.length-1, swaps=Math.max(0,links-1);
  const success=(m.pGenerate**links)*(m.pSwap**swaps)*(m.pMemory**swaps);
  const visibility=(m.vLink**links)*(m.vSwap**swaps)*(m.vMemory**swaps);
  return {links,swaps,success,visibility,qualifies:visibility>=m.minVisibility};
}

function evaluate(adj,m) {
  let pairs=0, connected=0, sumShortest=0, sumPaths=0, fourPathPairs=0;
  let sumAtLeastOne=0, sumParallelYield=0, qualifiedPairs=0;
  for (let s=0;s<adj.length;s++) for (let t=s+1;t<adj.length;t++) {
    pairs++;
    const paths=vertexDisjointPaths(adj,s,t,4);
    if (!paths.length) continue;
    connected++; sumShortest+=paths[0].length-1; sumPaths+=paths.length;
    if (paths.length===4) fourPathPairs++;
    const rows=paths.map((p)=>pathModel(p,m));
    const qualifying=rows.filter((r)=>r.qualifies);
    let none=1;
    for (const r of qualifying) none*=1-r.success;
    const atLeastOne=1-none;
    sumAtLeastOne+=atLeastOne;
    sumParallelYield+=qualifying.reduce((a,r)=>a+r.success*r.visibility,0);
    if (qualifying.length) qualifiedPairs++;
  }
  return {
    pairs,connectedPairs:connected,
    meanShortestHops:sumShortest/connected,
    meanVertexDisjointPaths:sumPaths/connected,
    fourPathPairs,
    qualifiedVisibilityPairs:qualifiedPairs,
    meanProbabilityAtLeastOneQualifiedEntanglement:sumAtLeastOne/connected,
    meanParallelSuccessVisibilityYield:sumParallelYield/connected,
    meanAcceptedWittingFrameOpportunity:(sumAtLeastOne/connected)*(13/40),
  };
}

function round(v,n=9) {
  if (typeof v==="number"&&Number.isFinite(v)) return Number(v.toFixed(n));
  if (Array.isArray(v)) return v.map((x)=>round(x,n));
  if (v&&typeof v==="object") return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,round(x,n)]));
  return v;
}

function run() {
  const w33=buildW33();
  const control=rewiredRegular(w33);
  const topologies={
    w33,
    circulant_degree12:circulant40(),
    degree_preserving_rewire:control.adj,
  };
  const structural={};
  const models={};
  for (const [name,adj] of Object.entries(topologies)) {
    structural[name]={
      vertices:adj.length,
      edges:edgesOf(adj).length,
      degreeHistogram:[...adj].reduce((h,s)=>(h[s.size]=(h[s.size]||0)+1,h),{}),
      distances:allPairsDistances(adj),
      nonadjacentCommonNeighborHistogram:commonNeighborHistogram(adj),
    };
    models[name]={};
    for (const m of MODELS) models[name][m.name]=round(evaluate(adj,m));
  }
  const checks={
    w33_40_240_12: structural.w33.vertices===40&&structural.w33.edges===240&&structural.w33.degreeHistogram[12]===40,
    w33_diameter_two: structural.w33.distances.diameter===2,
    w33_nonadjacent_pairs_all_have_four_relays:
      structural.w33.nonadjacentCommonNeighborHistogram[4]===540 &&
      Object.keys(structural.w33.nonadjacentCommonNeighborHistogram).length===1,
    controls_match_size_degree:
      ["circulant_degree12","degree_preserving_rewire"].every((k)=>
        structural[k].vertices===40&&structural[k].edges===240&&structural[k].degreeHistogram[12]===40),
    rewiring_actually_changed_edges: control.acceptedSwitches>100,
  };
  return round({
    schema:"holotrade.w33-quantum-routing-benchmark.v1",
    evidence:"DETERMINISTIC_NETWORK_MODEL",
    status:Object.values(checks).every(Boolean)?"PASS":"PARTIAL",
    topologyControls:{
      note:"Both controls have exactly 40 vertices, 240 edges and degree 12. They are not claimed to be optimal alternative quantum-network designs.",
      degreePreservingAcceptedSwitches:control.acceptedSwitches,
    },
    linkModels:MODELS,
    structural,
    modelResults:models,
    exactW33Reading:"Every one of the 540 nonadjacent W33 pairs has exactly four length-2 relay choices (mu=4); adjacent pairs are one hop apart.",
    metricBoundary:{
      probability:"Independent-path success proxy from declared pGenerate/pSwap/pMemory parameters.",
      visibility:"Multiplicative scalar visibility proxy, not a complete density-matrix/noise simulation.",
      acceptedWittingFrameOpportunity:"Routing success proxy multiplied by the exact 13/40 Witting same-or-orthogonal admission fraction; NOT a secret-key rate.",
    },
    limitations:[
      "No quantum hardware, repeater, memory, detector or fibre was measured.",
      "Path independence is a modeling assumption and can overstate multipath benefit under correlated failures.",
      "The scalar visibility composition is a benchmark model, not a universal quantum-channel law.",
      "No purification scheduler, finite-key QKD analysis, side-channel model or composable secrecy proof is included.",
      "The 540-chart Q3 web is a different routing layer and is analyzed separately rather than compared as a same-size control."
    ],
    checks,
  });
}

if (require.main===module) {
  const packet=run();
  const arg=process.argv.find((x)=>x.startsWith("--write="));
  if (arg) {
    const target=path.resolve(process.cwd(),arg.slice(8));
    fs.mkdirSync(path.dirname(target),{recursive:true});
    fs.writeFileSync(target,JSON.stringify(packet,null,2)+"\n");
  }
  console.log(JSON.stringify(packet,null,2));
  if (packet.status!=="PASS") process.exitCode=1;
}
module.exports={buildW33,circulant40,rewiredRegular,bfs,vertexDisjointPaths,pathModel,evaluate,run};
