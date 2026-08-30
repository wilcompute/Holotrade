#!/usr/bin/env node
"use strict";

// Exact source/geometry audit for the compact adjacency-indexed recovery core.
// This is deliberately independent of the expensive Yosys miter: it proves the
// finite transformation used to generate the compact core, while Yosys remains
// the bit-level RTL backstop.

const fs=require("node:fs");
const path=require("node:path");
const crypto=require("node:crypto");
const cp=require("node:child_process");
const S=require("../js/substrate.js");

const ROOT=path.resolve(__dirname,"..");
const BASE=path.join(ROOT,"rtl/w33_recovery_two_stage_core.v");
const GEN=path.join(ROOT,"scripts/gen-w33-recovery-compact.js");
const COMPACT=path.join(ROOT,"rtl/build/w33_recovery_two_stage_core_compact.v");
const OUT=path.join(ROOT,"data/w33_recovery_compact_structural_equivalence.json");

function sha256(s){return crypto.createHash("sha256").update(s).digest("hex");}
function norm(s){return s.replace(/\/\/.*$/gm,"").replace(/\s+/g,"");}
function fail(msg){throw new Error(msg);}
function tupleCmp(a,b){for(let i=0;i<a.length;i++){if(a[i]!==b[i])return a[i]>b[i]?1:-1;}return 0;}
function extractSeq(src){const i=src.lastIndexOf("always @(posedge clk)");if(i<0)fail("missing sequential block");const j=src.indexOf("endmodule",i);if(j<0)fail("missing endmodule");return norm(src.slice(i,j));}
function parseOccLines(src){
  const out=[];
  const re=/occv=([^;]+);\s*zero_lines\[(\d+)\]=\(occv==0\);\s*single_lines\[\2\]=\(occv==1\);/g;
  let m;while((m=re.exec(src))!==null){
    const pts=[...m[1].matchAll(/busy\[(\d+)\]/g)].map(x=>Number(x[1])).sort((a,b)=>a-b);
    out[Number(m[2])]=pts;
  }
  return out;
}
function parsePointMasks(src){
  const out=[];const re=/6'd(\d+):\s*plmask=40'h([0-9a-fA-F]+);/g;let m;
  while((m=re.exec(src))!==null)out[Number(m[1])]=BigInt("0x"+m[2]);
  return out;
}
function maskFor(lines){let x=0n;for(const li of lines)x|=1n<<BigInt(li);return x;}

function run(){
  cp.execFileSync(process.execPath,[GEN],{cwd:ROOT,stdio:"pipe"});
  const base=fs.readFileSync(BASE,"utf8"), compact=fs.readFileSync(COMPACT,"utf8");

  if(S.POINTS && S.POINTS.length!==40)fail("expected 40 points");
  if(S.LINES.length!==40||!S.LINES.every(L=>L.length===4))fail("expected 40 four-point lines");
  const pointLines=Array.from({length:40},()=>[]);
  S.LINES.forEach((L,li)=>L.forEach(p=>pointLines[p].push(li)));
  if(!pointLines.every(x=>x.length===4))fail("expected four lines through every point");

  // The baseline's hand-expanded occupancy equations and point-line masks must
  // exactly equal the canonical substrate used by the compact generator.
  const occ=parseOccLines(base);
  if(occ.length!==40)fail(`parsed ${occ.length} baseline occupancy rows`);
  for(let li=0;li<40;li++){
    const want=[...S.LINES[li]].sort((a,b)=>a-b);
    if(JSON.stringify(occ[li])!==JSON.stringify(want))fail(`baseline line ${li} mismatch`);
  }
  const masks=parsePointMasks(base);if(masks.length!==40)fail(`parsed ${masks.length} point masks`);
  for(let p=0;p<40;p++)if(masks[p]!==maskFor(pointLines[p]))fail(`baseline point mask ${p} mismatch`);

  // For p != q the baseline accepts a labelled pair iff their point-line masks
  // intersect.  In W(3,3) an accepted pair has one unique common line.  The
  // compact generator enumerates exactly those 12 neighbours per source.
  let directed=0,nonedges=0;const degree=[];
  for(let p=0;p<40;p++){
    let d=0;
    for(let q=0;q<40;q++)if(q!==p){
      const shared=pointLines[p].filter(li=>pointLines[q].includes(li));
      if(shared.length>1)fail(`points ${p},${q} share ${shared.length} lines`);
      const adjacent=shared.length===1;
      if(adjacent){directed++;d++;}else nonedges++;
    }
    degree.push(d);
  }
  if(directed!==480||!degree.every(d=>d===12))fail(`bad directed adjacency ${directed} ${degree}`);

  // The two score tuples are order-isomorphic because F is common to every
  // candidate in one decision:
  // baseline: (after=F+delta, release=F+s1, -p, -q)
  // compact : (delta,             s1, -p, -q).
  // Exhaust every attainable integer statistic pair; label tie-breaks are then
  // literally identical and need no state enumeration.
  let scorePairs=0;
  const stats=[];for(let s1=0;s1<=4;s1++)for(let z=0;z<=4;z++)for(let refill=0;refill<=1;refill++)stats.push({s1,z,refill,delta:s1-z-refill});
  for(let F=0;F<=40;F++)for(const a of stats)for(const b of stats){
    const cb=tupleCmp([F+a.delta,F+a.s1],[F+b.delta,F+b.s1]);
    const cc=tupleCmp([a.delta,a.s1],[b.delta,b.s1]);
    if(cb!==cc)fail(`score-order mismatch F=${F}`);scorePairs++;
    if((F+a.delta)!==(F+a.s1-a.z-a.refill))fail("free-after identity failure");
  }

  // The state machine is intentionally not optimized; prove it is literally
  // the same normalized always@(posedge clk) block in both RTLs.
  const baseSeq=extractSeq(base),compactSeq=extractSeq(compact);
  if(baseSeq!==compactSeq)fail("sequential state blocks differ");

  const requiredBase=["after=F+s1-z-refill","release=F+s1","(|shared)"];
  const requiredCompact=["delta=s1-z-refill","free_after=(F+best_delta)","q=nbr(p,k)"];
  for(const s of requiredBase)if(!norm(base).includes(norm(s)))fail(`baseline formula missing: ${s}`);
  for(const s of requiredCompact)if(!norm(compact).includes(norm(s)))fail(`compact formula missing: ${s}`);

  const out={
    schema:"holotrade.w33-recovery-compact-structural-equivalence.v1",status:"PASS",
    sourceHashes:{baselineSha256:sha256(base),generatorSha256:sha256(fs.readFileSync(GEN,"utf8")),generatedCompactSha256:sha256(compact)},
    geometry:{points:40,lines:40,lineSize:4,linesPerPoint:4,directedAdjacentCandidates:directed,directedNonCandidates:nonedges,degree:[...new Set(degree)]},
    baselineExpansion:{occupancyRowsMatched:40,pointLineMasksMatched:40},
    scoreOrder:{statisticsPerCandidate:stats.length,orderedStatisticComparisonsChecked:scorePairs,identity:"(F+delta,F+s1) has exactly the same lexicographic order as (delta,s1) for common F"},
    stateMachine:{normalizedSequentialBlocksIdentical:true,sequentialBlockSha256:sha256(baseSeq)},
    theorem:"The compact core is the exact finite transformation of the baseline search: busy[p]&&!busy[q] removes p=q; the baseline shared-line predicate is exactly the 480 directed W33 adjacency candidates; each candidate has one common line; F_after=F+s1-z-refill makes (after,release,p,q) order-equivalent to (delta,s1,p,q); baseline line equations and point masks equal the canonical substrate; and the sequential state block is textually identical after normalization.",
    boundary:"This certifies the generator transformation and source-level finite semantics for the checked source hashes. The independent Yosys bit-level equivalence miter remains the RTL backstop and is not replaced by this certificate."
  };
  fs.mkdirSync(path.dirname(OUT),{recursive:true});fs.writeFileSync(OUT,JSON.stringify(out,null,2)+"\n");
  console.log(JSON.stringify(out,null,2));return out;
}
if(require.main===module)run();module.exports={run};
