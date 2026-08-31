#!/usr/bin/env node
"use strict";

// Exact bridge between Holotrade's compact W33 recovery chooser and the
// 480-state directed-edge/Hashimoto carrier used in W33-Theory.
//
// For a busy point set B let F(B) be the number of empty W33 lines.  The RTL
// score delta=s1-z-refill is proved here to be exactly
//
//   F(B - {p} + {q}) - F(B)
//
// for every legal adjacent move p->q.  Thus the chooser is steepest ascent of
// a discrete empty-line potential over the active directed edges, with the
// existing release score equal to the intermediate potential after removing p.
//
// We also identify the non-backtracking 11=2+9 continuation split geometrically:
// 2 same-line continuations (triangle turns) and 9 line-switch continuations
// (three alternate lines through q, three alternate points on each).

const fs=require("node:fs");
const path=require("node:path");
const S=require("../js/substrate.js");
const ROOT=path.resolve(__dirname,"..");
const OUT=path.join(ROOT,"data/w33_recovery_edge_gradient_carrier.json");

const LINES=S.LINES;
const ADJ=S.ADJ;
if(LINES.length!==40||ADJ.length!==40) throw new Error("expected W(3,3)");
const thru=Array.from({length:40},()=>[]);
LINES.forEach((L,li)=>L.forEach(p=>thru[p].push(li)));
if(!thru.every(x=>x.length===4)) throw new Error("point line degree");

function bit(mask,p){return ((mask>>BigInt(p))&1n)!==0n;}
function setbit(mask,p,v){return v ? (mask|(1n<<BigInt(p))) : (mask&~(1n<<BigInt(p)));}
function occ(mask,li){let n=0;for(const p of LINES[li])if(bit(mask,p))n++;return n;}
function F(mask){let n=0;for(let li=0;li<40;li++)if(occ(mask,li)===0)n++;return n;}
function edgeScore(mask,p,q){
  if(!bit(mask,p)||bit(mask,q)||!ADJ[p].includes(q)) throw new Error("illegal move");
  const shared=thru[p].filter(li=>thru[q].includes(li));
  if(shared.length!==1) throw new Error("shared line");
  const s1=thru[p].filter(li=>occ(mask,li)===1).length;
  const z=thru[q].filter(li=>occ(mask,li)===0).length;
  const refill=occ(mask,shared[0])===1?1:0;
  const delta=s1-z-refill;
  const release=F(mask)+s1;
  const moved=setbit(setbit(mask,p,false),q,true);
  return {delta,release,before:F(mask),after:F(moved),shared:shared[0],s1,z,refill};
}

const directed=[];
for(let p=0;p<40;p++)for(const q of ADJ[p])directed.push([p,q]);
if(directed.length!==480)throw new Error(`directed=${directed.length}`);

// Structural local signatures for all 480 directed edges.
const localSigs=new Set();
for(const [p,q] of directed){
  const shared=thru[p].filter(li=>thru[q].includes(li));
  const union=new Set([...thru[p],...thru[q]]);
  localSigs.add(JSON.stringify([thru[p].length,thru[q].length,shared.length,union.size]));
}
if(localSigs.size!==1||![...localSigs][0]===JSON.stringify([4,4,1,7])){}
if(!localSigs.has(JSON.stringify([4,4,1,7]))) throw new Error(`local signatures ${[...localSigs]}`);

// Exhaust the 2^7 empty/single status patterns around one directed edge.
// The seven affected lines have disjoint arms away from p,q, so these patterns
// are independently realizable; multiplicity >1 does not affect emptiness and
// therefore cannot change the identity being proved.
const [p0,q0]=directed[0];
const shared0=thru[p0].find(li=>thru[q0].includes(li));
const pOnly=thru[p0].filter(li=>li!==shared0);
const qOnly=thru[q0].filter(li=>li!==shared0);
const pickOther=(li,ban)=>LINES[li].find(x=>!ban.has(x));
const pRep=pOnly.map(li=>pickOther(li,new Set([p0,q0])));
const qRep=qOnly.map(li=>pickOther(li,new Set([p0,q0])));
const sRep=pickOther(shared0,new Set([p0,q0]));
let exhaustivePatterns=0;
for(let bits=0;bits<128;bits++){
  let mask=1n<<BigInt(p0); // p busy, q free
  // bits 0..2: p-only line is single iff 1; else add one extra busy point.
  for(let i=0;i<3;i++)if(((bits>>i)&1)===0)mask|=1n<<BigInt(pRep[i]);
  // bits 3..5: q-only line is zero iff 1; else add one busy point.
  for(let i=0;i<3;i++)if(((bits>>(3+i))&1)===0)mask|=1n<<BigInt(qRep[i]);
  // bit 6: shared line is single iff 1; else add one other busy point.
  if(((bits>>6)&1)===0)mask|=1n<<BigInt(sRep);
  const r=edgeScore(mask,p0,q0);
  if(r.after-r.before!==r.delta)throw new Error(`gradient mismatch bits=${bits}`);
  // release is exactly the potential after removing p but before inserting q.
  const removed=setbit(mask,p0,false);
  if(F(removed)!==r.release)throw new Error(`release mismatch bits=${bits}`);
  exhaustivePatterns++;
}

// Hashimoto continuation split: p->q followed by q->r, r!=p.
let triangleTurns=0,openTurns=0;
const perEdge=[];
for(const [p,q] of directed){
  const l1=thru[p].find(li=>thru[q].includes(li));
  let tri=0,open=0,sameLine=0,switchLine=0;
  for(const r of ADJ[q]) if(r!==p){
    const l2=thru[q].find(li=>thru[r].includes(li));
    const triangle=ADJ[p].includes(r);
    if(triangle)tri++;else open++;
    if(l2===l1)sameLine++;else switchLine++;
    if(triangle!==(l2===l1))throw new Error(`turn classification ${p},${q},${r}`);
  }
  if(tri!==2||open!==9||sameLine!==2||switchLine!==9)throw new Error(`turn split ${p},${q}`);
  triangleTurns+=tri;openTurns+=open;
  perEdge.push([tri,open,sameLine,switchLine]);
}
if(new Set(perEdge.map(JSON.stringify)).size!==1)throw new Error("nonuniform turn split");

// At q there are 4 lines.  Continuing on the incoming line leaves 2 points;
// switching uses 3 other lines x 3 points each.
const out={
  schema:"holotrade.w33-recovery-edge-gradient-carrier.v1",status:"PASS",
  carrier:{directedEdges:480,degree:12,nonBacktrackingOutdegree:11,
    localIncidentLineSignature:[4,4,1,7]},
  gradient:{potential:"F(B)=number of empty W33 lines",
    exactIdentity:"delta(p->q)=F(B-{p}+{q})-F(B)",
    releaseIdentity:"release=F(B-{p})",
    localStatusPatternsExhausted:exhaustivePatterns,
    chooserMeaning:"lexicographically tie-broken steepest ascent of F over active directed W33 edges"},
  hashimotoRouter:{triangleTurnsPerEdge:2,openTurnsPerEdge:9,
    sameLineContinuationsPerEdge:2,lineSwitchContinuationsPerEdge:9,
    decomposition:"11 = 2 + 9 = (same GQ line) + (3 alternate lines x 3 points)",
    totalTriangleTurns:triangleTurns,totalOpenTurns:openTurns},
  theorem:"Holotrade's compact recovery candidate universe is exactly the 480-state directed-edge carrier of W(3,3). Its RTL delta score is the exact discrete derivative of the empty-line potential. The W33-Theory Hashimoto split T+O becomes a literal local router split: T stays on the incoming GQ line (2 choices), O switches line at the intermediate point (3x3=9 choices).",
  boundary:"This is an exact finite-geometry/control identity. It does not imply that the deployed two-stage policy itself follows a non-backtracking trajectory; after the entry-constrained stage the RTL may optimize over all currently active directed edges."
};
fs.writeFileSync(OUT,JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({status:"PASS",directed:480,patterns:exhaustivePatterns,turns:[2,9],gradient:true}));
