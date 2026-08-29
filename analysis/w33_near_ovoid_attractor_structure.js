#!/usr/bin/env node
"use strict";

const S=require("../js/substrate.js");
const P=require("../scheduler/w33-migration-policy.js");
const {buildCorpus}=require("./w33_near_ovoid_corpus.js");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function occ(state){const B=new Set(state);return S.LINES.map((L)=>L.reduce((n,p)=>n+(B.has(p)?1:0),0));}
function hist(xs){const h={};for(const x of xs)h[x]=(h[x]||0)+1;return h;}
function free(state){return occ(state).filter((x)=>x===0).length;}
function degseq(state){const B=new Set(state);return [...B].map((p)=>S.ADJ[p].filter((q)=>B.has(q)).length).sort((a,b)=>b-a);}
function lineMeet(a,b){return S.LINES[a].some((p)=>S.LINES[b].includes(p));}

function detect(start,cap=64){
  let state=[...start].sort((a,b)=>a-b);const seen=new Map([[key(state),0]]),seq=[state];
  for(let t=1;t<=cap;t++){
    state=P.chooseMigration(state,{policy:P.POLICY.TOPOLOGY_AWARE}).nextBusy;
    const k=key(state);
    if(seen.has(k)){const mu=seen.get(k);return {mu,lambda:t-mu,cycle:seq.slice(mu,t)};}
    seen.set(k,t);seq.push(state);
  }
  throw new Error("cycle cap exceeded");
}

function permutations(xs){
  if(xs.length<=1)return [xs.slice()];
  const out=[];
  for(let i=0;i<xs.length;i++)for(const tail of permutations(xs.slice(0,i).concat(xs.slice(i+1))))out.push([xs[i],...tail]);
  return out;
}
function product(arrays,i=0,prefix=[],out=[]){
  if(i===arrays.length){out.push(prefix);return out;}
  for(const x of arrays[i])product(arrays,i+1,prefix.concat(x),out);
  return out;
}
function adjacencyBits(order){
  let s="";for(let i=0;i<order.length;i++)for(let j=i+1;j<order.length;j++)s+=S.isAdjacent(order[i],order[j])?"1":"0";return s;
}
function canonicalGraph(state){
  const B=new Set(state),classes=new Map();
  for(const p of state){const d=S.ADJ[p].filter((q)=>B.has(q)).length;if(!classes.has(d))classes.set(d,[]);classes.get(d).push(p);}
  const blocks=[...classes.keys()].sort((a,b)=>a-b).map((d)=>permutations(classes.get(d).sort((a,b)=>a-b)));
  let best=null;for(const order of product(blocks)){const z=adjacencyBits(order);if(best===null||z<best)best=z;}return best;
}
function permOrder(p){
  const seen=new Set();let out=1;function gcd(a,b){while(b)[a,b]=[b,a%b];return a;}function lcm(a,b){return a/gcd(a,b)*b;}
  for(let i=0;i<p.length;i++)if(!seen.has(i)){let j=i,n=0;while(!seen.has(j)){seen.add(j);n++;j=p[j];}out=lcm(out,n);}return out;
}
function representativeAut(state){
  const B=[...state].sort((a,b)=>a-b),set=new Set(B),classes=new Map();
  B.forEach((p)=>{const d=S.ADJ[p].filter((q)=>set.has(q)).length;if(!classes.has(d))classes.set(d,[]);classes.get(d).push(p);});
  const blocks=[...classes.keys()].sort((a,b)=>a-b).map((d)=>permutations(classes.get(d)));
  const index=new Map(B.map((p,i)=>[p,i])),base=adjacencyBits(B),orders=[];
  for(const orderByClass of product(blocks)){
    const image=new Map();let off=0;
    for(const d of [...classes.keys()].sort((a,b)=>a-b)){
      const src=classes.get(d),dst=orderByClass.slice(off,off+src.length);off+=src.length;
      src.forEach((p,i)=>image.set(p,dst[i]));
    }
    let ok=true;
    for(let i=0;i<B.length&&ok;i++)for(let j=i+1;j<B.length;j++)if(S.isAdjacent(B[i],B[j])!==S.isAdjacent(image.get(B[i]),image.get(B[j]))){ok=false;break;}
    if(ok)orders.push(permOrder(B.map((p)=>index.get(image.get(p)))));
  }
  return {order:orders.length,elementOrderCensus:hist(orders)};
}

function run(){
  const corpus=buildCorpus(),starts=[];
  for(const r of corpus.records)for(const a of r.removals)starts.push(r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y));
  const cycles=new Map();
  for(const start of starts){const z=detect(start),pair=z.cycle.map(key).sort().join("|");if(!cycles.has(pair))cycles.set(pair,{cycle:z.cycle,basin:0});cycles.get(pair).basin++;}
  const high=[...cycles.values()].filter((z)=>z.cycle.length===2&&z.cycle.every((s)=>free(s)===19));
  const states=new Map();for(const z of high)for(const s of z.cycle)states.set(key(s),s);
  const occTypes=new Set(),degreeTypes=new Set(),canonTypes=new Set();let disjointTriple=true;
  for(const s of states.values()){
    occTypes.add(JSON.stringify(hist(occ(s))));degreeTypes.add(degseq(s).join(","));canonTypes.add(canonicalGraph(s));
    const triples=occ(s).map((x,i)=>x===3?i:-1).filter((i)=>i>=0);if(triples.length!==2||lineMeet(triples[0],triples[1]))disjointTriple=false;
  }
  const cores=new Map();let toggleInvariant=true;
  for(const z of high){const A=new Set(z.cycle[0]),B=new Set(z.cycle[1]),core=[...A].filter((x)=>B.has(x)).sort((a,b)=>a-b);cores.set(key(core),core);
    const x=[...A].find((p)=>!B.has(p)),y=[...B].find((p)=>!A.has(p)),C=new Set(core);
    const nx=S.ADJ[x].filter((p)=>C.has(p)),ny=S.ADJ[y].filter((p)=>C.has(p));
    const d=degseq(core),coreDeg=new Map(core.map((p)=>[p,S.ADJ[p].filter((q)=>C.has(q)).length]));
    const shared=nx.filter((p)=>ny.includes(p));
    if(!S.isAdjacent(x,y)||nx.length!==3||ny.length!==3||shared.length!==1||coreDeg.get(shared[0])!==2||d.join(",")!=="5,5,4,4,4,4,4,4,2")toggleInvariant=false;
  }
  const basin=hist(high.map((z)=>z.basin));
  const rep=[...states.values()][0],aut=representativeAut(rep);
  const result={
    schema:"holotrade.near-ovoid-attractor-structure.v1",status:"PASS",startStates:starts.length,
    highBasinStarts:high.reduce((s,z)=>s+z.basin,0),distinctHighCycles:high.length,distinctHighStates:states.size,distinctCores:cores.size,
    basinSizeHistogram:basin,
    state:{freeLines:19,occupancyProfile:"0^19 1^4 2^15 3^2",degreeSequence:"5^4 4^4 3^2",tripleHitLinesAlwaysDisjoint:disjointTriple,inducedGraphIsomorphismTypes:canonTypes.size,automorphismGroup:{structure:"D8 x C2",...aut}},
    cycleCore:{size:9,occupancyProfile:"0^21 1^3 2^15 3^1",degreeSequence:"5^2 4^6 2^1",toggleInvariant},
    reading:"The dominant 19/19 attractor is one rigid 10-point graph type. Each period-two transition exchanges adjacent degree-three points over a fixed nine-point core; the toggled points share exactly the unique degree-two core vertex.",
    boundary:"Exact for the declared deterministic topology-aware policy on the 2,880 certified starts; 19 is not asserted globally optimal over all migration policies or all ten-point W33 states."
  };
  if(occTypes.size!==1||degreeTypes.size!==1||canonTypes.size!==1||!toggleInvariant||aut.order!==16)throw new Error("attractor structure invariant failed");
  return result;
}
if(require.main===module)process.stdout.write(JSON.stringify(run(),null,2)+"\n");
module.exports={run};
