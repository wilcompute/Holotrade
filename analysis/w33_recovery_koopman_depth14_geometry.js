#!/usr/bin/env node
"use strict";

// State-level geometry behind the five size-14 zero-Jordan blocks.
// Rebuild the exact forward closure, isolate the six depth-14 leaves, and
// recover each near-ovoid's missed/doubled punctured-pencil centers.  For a
// functional graph, the number of size>=14 Koopman zero blocks is the number
// of distinct depth-13 images fed by depth-14 leaves.  We certify the unique
// two-to-one top merge explicitly.

const {buildCorpus}=require("./w33_near_ovoid_corpus.js");
const P=require("../scheduler/w33-migration-policy.js");
const S=require("../js/substrate.js");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function parse(k){return k.split(",").map(Number);}
function lineOcc(busy){const B=new Set(busy);return S.LINES.map(L=>L.reduce((n,p)=>n+B.has(p),0));}
function hist(xs){const h={};for(const x of xs)h[x]=(h[x]||0)+1;return h;}
function commonPoint(lineIds){
  let I=new Set(S.LINES[lineIds[0]]);
  for(const li of lineIds.slice(1))I=new Set([...I].filter(x=>S.LINES[li].includes(x)));
  return [...I].sort((a,b)=>a-b);
}
function hingeLine(a,b){return S.LINES.findIndex(L=>L.includes(a)&&L.includes(b));}
function symdiff(a,b){const A=new Set(a),B=new Set(b);return [...new Set([...a,...b])].filter(x=>A.has(x)!==B.has(x)).sort((x,y)=>x-y);}

function run(){
  const starts=[];
  for(const rec of buildCorpus().records)for(const a of rec.removals)starts.push(key(rec.blocker.filter(x=>x!==a)));
  if(new Set(starts).size!==2880)throw new Error("start cardinality mismatch");
  const startSet=new Set(starts),next=new Map(),move=new Map(),queue=[...startSet];let qi=0;
  while(qi<queue.length){
    const k=queue[qi++];const m=P.chooseMigration(parse(k),{policy:P.POLICY.TOPOLOGY_AWARE});const n=key(m.nextBusy);
    next.set(k,n);move.set(k,m);if(!next.has(n)&&!queue.includes(n))queue.push(n);
  }
  const states=[...next.keys()];const stateSet=new Set(states);
  for(const n of next.values())if(!stateSet.has(n))throw new Error("closure incomplete");

  // Exact cycles and depths.
  const color=new Map(),cycleNodes=new Set();
  for(const s of states){
    if(color.get(s)===2)continue;const path=[],pos=new Map();let x=s;
    while(color.get(x)!==2&&!pos.has(x)){pos.set(x,path.length);path.push(x);color.set(x,1);x=next.get(x);}
    if(pos.has(x))for(const y of path.slice(pos.get(x)))cycleNodes.add(y);
    for(const y of path)color.set(y,2);
  }
  const depth=new Map([...cycleNodes].map(x=>[x,0]));
  function dep(x){if(depth.has(x))return depth.get(x);const d=1+dep(next.get(x));depth.set(x,d);return d;}
  for(const s of states)dep(s);
  const maxDepth=Math.max(...depth.values());if(maxDepth!==14)throw new Error(`max depth ${maxDepth}`);
  const deep=states.filter(s=>depth.get(s)===14).sort();if(deep.length!==6)throw new Error(`deep ${deep.length}`);
  if(!deep.every(s=>startSet.has(s)))throw new Error("depth-14 leaf outside certified near-ovoid starts");

  const parents=deep.map(s=>next.get(s));const parentGroups=new Map();
  deep.forEach((s,i)=>{const p=parents[i];if(!parentGroups.has(p))parentGroups.set(p,[]);parentGroups.get(p).push(s);});
  if(parentGroups.size!==5)throw new Error(`expected five depth-13 parents, got ${parentGroups.size}`);
  const groupSizes=[...parentGroups.values()].map(g=>g.length).sort((a,b)=>a-b);
  if(JSON.stringify(groupSizes)!==JSON.stringify([1,1,1,1,2]))throw new Error(`top merge shape ${groupSizes}`);

  function geometry(s){
    const busy=parse(s),occ=lineOcc(busy),miss=[],dbl=[];
    occ.forEach((n,i)=>{if(n===0)miss.push(i);if(n===2)dbl.push(i);});
    if(JSON.stringify(hist(occ))!==JSON.stringify({"0":3,"1":34,"2":3}))throw new Error(`not optimal near-ovoid ${s}`);
    const mc=commonPoint(miss),dc=commonPoint(dbl);if(mc.length!==1||dc.length!==1)throw new Error("punctured-pencil center failure");
    const h=hingeLine(mc[0],dc[0]);if(h<0)throw new Error("centers not collinear");
    const trace=[];let x=s;
    for(let t=0;t<=14;t++){
      const o=lineOcc(parse(x));trace.push({step:t,depth:depth.get(x),freeLines:o.filter(n=>n===0).length,busy:x});
      if(t<14)x=next.get(x);
    }
    const m=move.get(s);
    return {busy,missedLines:miss,doubledLines:dbl,missCenter:mc[0],doubleCenter:dc[0],hingeLine:h,
            firstMove:{from:m.from,to:m.to,freeLinesAfterMove:m.freeLinesAfterMove},trace};
  }
  const records=deep.map(s=>({state:s,parent:next.get(s),geometry:geometry(s)}));
  const pair=[...parentGroups.entries()].find(([,g])=>g.length===2);const pairStates=pair[1].map(parse);
  const merge={parent:pair[0],children:pair[1],childSymmetricDifference:symdiff(pairStates[0],pairStates[1]),
               childGeometries:pair[1].map(s=>{const g=records.find(r=>r.state===s).geometry;return {missCenter:g.missCenter,doubleCenter:g.doubleCenter,hingeLine:g.hingeLine,firstMove:g.firstMove};})};

  // Image-rank identity at the top: |Im T^13|-|Im T^14| = 2891-2886 = 5.
  let img=new Set(states),sizes=[img.size];for(let j=1;j<=14;j++){img=new Set([...img].map(x=>next.get(x)));sizes.push(img.size);}
  if(sizes[13]!==2891||sizes[14]!==2886||sizes[13]-sizes[14]!==5)throw new Error("top rank-drop mismatch");

  const out={schema:"holotrade.w33-recovery-koopman-depth14-geometry.v1",status:"PASS",
    maxDepth:14,depth14Leaves:6,distinctDepth13Parents:5,parentMultiplicity:groupSizes,
    topImageSizes:{T13:sizes[13],T14:sizes[14],rankDrop:sizes[13]-sizes[14]},
    maximalLeaves:records,uniqueTopMerge:merge,
    theorem:"The six depth-14 recovery leaves are certified optimal near-ovoids with the standard missed/doubled punctured-pencil defect geometry. They feed exactly five distinct depth-13 parents: four singly and one by a two-to-one merge. Hence the top Koopman rank drop is five, explaining exactly five zero-eigenvalue Jordan blocks of size 14.",
    boundary:"Exact deterministic finite-state geometry for the declared topology-aware tie-break and repository point numbering. The selected six leaves are not asserted to be a symmetry-invariant physical ensemble."};
  console.log(JSON.stringify(out,null,2));return out;
}
if(require.main===module)run();module.exports={run};
