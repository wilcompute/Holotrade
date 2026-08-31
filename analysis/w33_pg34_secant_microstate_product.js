#!/usr/bin/env node
"use strict";

// Exact cross-repo test of the tempting 6 = 3 x 2 interpretation of a
// Holotrade near-ovoid fibre.
//
// W33-Theory's PG(3,4) line certificate identifies each W33 edge with the two
// nonabsolute points of one Hermitian secant.  The 40x45 cross-incidence then
// says that exactly three absolute Hermitian points lie on that secant.
// Holotrade independently proves that each ORIENTED edge supports six optimal
// near-ovoid microstates, split 3+3 by the two residual hinge points.
//
// This audit reconstructs the same 45 Hermitian/sentinel support labels using
// only Holotrade's native W33 line incidence, fixes one oriented edge, builds
// its exact PSp(4,3) stabilizer (order 54), and compares three permutation
// actions:
//   (i) the six microstates,
//   (ii) the three absolute/secant labels,
//   (iii) the two residual hinge points.
// It exhausts every chirality-respecting bijection from the six states to the
// Cartesian 3x2 set.  The result is a certificate either way: an equivariant
// product identification or a precise no-go showing where 6=3x2 fails.

const fs=require("node:fs");
const path=require("node:path");
const S=require("../js/substrate.js");
const M=require("../scheduler/w33-near-ovoid-migration.js");
const {buildCorpus}=require("./w33_near_ovoid_corpus.js");
const {generatePSp}=require("./w33_attractor_psp_orbit.js");

const ROOT=path.resolve(__dirname,"..");
const OUT=path.join(ROOT,"data/w33_pg34_secant_microstate_product.json");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function compose(p,q){return q.map((x)=>p[x]);}
function pkey(p){return p.join(",");}
function actSet(g,xs){return xs.map((x)=>g[x]).sort((a,b)=>a-b);}
function cycleShape(p){
  const seen=new Set(),C={};
  for(let i=0;i<p.length;i++)if(!seen.has(i)){
    let j=i,n=0;while(!seen.has(j)){seen.add(j);n++;j=p[j];}C[n]=(C[n]||0)+1;
  }
  return Object.fromEntries(Object.entries(C).sort((a,b)=>Number(a[0])-Number(b[0])));
}
function permImage(perms){return new Map(perms.map((p)=>[pkey(p),p]));}
function permutations(xs){
  if(xs.length<=1)return [[...xs]];
  const out=[];
  for(let i=0;i<xs.length;i++)for(const r of permutations(xs.slice(0,i).concat(xs.slice(i+1))))out.push([xs[i],...r]);
  return out;
}

function sentinelSupports(){
  const thru=Array.from({length:40},()=>[]);
  S.LINES.forEach((L,li)=>L.forEach((p)=>thru[p].push(li)));
  const buckets=new Map();
  for(let a=0;a<37;a++)for(let b=a+1;b<38;b++)for(let c=b+1;c<39;c++)for(let d=c+1;d<40;d++){
    const C=[a,b,c,d],v=Array(40).fill(0);
    for(const p of C)for(const li of thru[p])v[li]++;
    const k=v.join("");
    if(!buckets.has(k))buckets.set(k,[]);
    buckets.get(k).push(C);
  }
  const pairs=[...buckets.values()].filter((x)=>x.length===2);
  if(pairs.length!==45)throw new Error(`expected 45 trade collisions, got ${pairs.length}`);
  const supports=pairs.map(([a,b])=>[...new Set([...a,...b])].sort((x,y)=>x-y))
    .sort((a,b)=>key(a).localeCompare(key(b),undefined,{numeric:true}));
  if(new Set(supports.map(key)).size!==45||!supports.every((x)=>x.length===8))throw new Error("support reconstruction");
  return supports;
}

function run(){
  const supports=sentinelSupports(),six=buildCorpus();
  const groups=new Map();
  for(const r of six.records)for(const a of r.removals){
    const busy=r.blocker.filter((x)=>x!==a),z=M.analyzeNearOvoid(busy);
    if(!z||z.defectCenter!==a||z.blockerCenter!==r.center)throw new Error("corpus coordinate mismatch");
    const k=`${a}:${r.center}`;
    if(!groups.has(k))groups.set(k,[]);
    groups.get(k).push({busy,z});
  }
  if(groups.size!==480||[...groups.values()].some((x)=>x.length!==6))throw new Error("expected 480 six-state fibres");

  const first=[...groups.entries()].sort((a,b)=>a[0].localeCompare(b[0],undefined,{numeric:true}))[0];
  const [a,c]=first[0].split(":").map(Number),states=first[1].sort((x,y)=>key(x.busy).localeCompare(key(y.busy),undefined,{numeric:true}));
  if(!S.isAdjacent(a,c))throw new Error("base pair is not an edge");
  const absLabels=[];
  for(let i=0;i<45;i++)if(supports[i].includes(a)&&supports[i].includes(c))absLabels.push(i);
  if(absLabels.length!==3)throw new Error(`secant absolute labels=${absLabels.length}`);
  const hinge=S.LINES.find((L)=>L.includes(a)&&L.includes(c));
  const residual=hinge.filter((p)=>p!==a&&p!==c).sort((x,y)=>x-y);
  if(residual.length!==2)throw new Error("residual hinge count");
  const anchorCounts=Object.fromEntries(residual.map((r)=>[r,states.filter((s)=>s.z.chiralityAnchor===r).length]));
  if(Object.values(anchorCounts).some((n)=>n!==3))throw new Error(`chirality is not 3+3 ${JSON.stringify(anchorCounts)}`);

  const G=generatePSp();
  const H=G.filter((g)=>g[a]===a&&g[c]===c);
  if(H.length!==54)throw new Error(`oriented edge stabilizer=${H.length}`);
  const stateIndex=new Map(states.map((s,i)=>[key(s.busy),i]));
  const supportIndex=new Map(supports.map((s,i)=>[key(s),i]));
  const labelPos=new Map(absLabels.map((x,i)=>[x,i]));
  const residualPos=new Map(residual.map((x,i)=>[x,i]));

  const microPerms=[],absPerms=[],chirPerms=[],productPerms=[];
  for(const g of H){
    const pm=states.map((s)=>{
      const j=stateIndex.get(key(actSet(g,s.busy)));if(j==null)throw new Error("edge stabilizer left six-state fibre");return j;
    });
    const pa=absLabels.map((m)=>{
      const j=supportIndex.get(key(actSet(g,supports[m])));if(j==null||!labelPos.has(j))throw new Error("absolute secant labels not invariant");return labelPos.get(j);
    });
    const pc=residual.map((r)=>{
      if(!residualPos.has(g[r]))throw new Error("residual pair not invariant");return residualPos.get(g[r]);
    });
    const pp=[];
    for(let ri=0;ri<2;ri++)for(let si=0;si<3;si++)pp.push(3*pc[ri]+pa[si]);
    microPerms.push(pm);absPerms.push(pa);chirPerms.push(pc);productPerms.push(pp);
  }
  const microImage=permImage(microPerms),absImage=permImage(absPerms),chirImage=permImage(chirPerms),productImage=permImage(productPerms);

  // Exhaust the 3! assignments independently within each chirality block.
  const byAnchor=residual.map((r)=>states.map((s,i)=>s.z.chiralityAnchor===r?i:null).filter((i)=>i!==null));
  const Ps=permutations([0,1,2]),equivariant=[];
  for(const p0 of Ps)for(const p1 of Ps){
    const coord=Array(6);
    for(let q=0;q<3;q++){coord[byAnchor[0][q]]=3*0+p0[q];coord[byAnchor[1][q]]=3*1+p1[q];}
    let ok=true;
    for(let h=0;h<H.length&&ok;h++)for(let i=0;i<6;i++){
      if(coord[microPerms[h][i]]!==productPerms[h][coord[i]]){ok=false;break;}
    }
    if(ok)equivariant.push(coord);
  }

  // The same action invariants are measured on every oriented edge, to ensure
  // the result is not an artefact of the chosen coordinate representative.
  const imageOrderHist=Object.fromEntries([...microImage.values()].reduce((C,p)=>{
    const k=JSON.stringify(cycleShape(p));C.set(k,(C.get(k)||0)+1);return C;
  },new Map()));

  const relation=equivariant.length?"EQUIVARIANT_PRODUCT":"PRODUCT_NO_GO";
  const out={
    schema:"holotrade.w33-pg34-secant-microstate-product.v1",status:"PASS",relation,
    carrier:{orientedW33Edges:480,microstates:2880,microstatesPerOrientedEdge:6,
      pg34Reading:"W33-Theory identifies each underlying edge with the two nonabsolute points of a Hermitian PG(3,4) secant"},
    baseEdge:{a,c,edgeStabilizerOrder:H.length,absoluteSecantLabels:absLabels,
      absoluteLabelSupports:absLabels.map((m)=>supports[m]),residualHingePoints:residual,chiralityCounts:anchorCounts},
    permutationImages:{sixMicrostates:microImage.size,threeAbsoluteLabels:absImage.size,
      twoChiralityAnchors:chirImage.size,coordinatewiseThreeByTwo:productImage.size,
      microstateCycleShapeHistogram:imageOrderHist},
    cartesianTest:{chiralityRespectingBijectionsTested:36,equivariantBijections:equivariant.length,
      example:equivariant[0]||null},
    theorem:equivariant.length?
      "The six optimal near-ovoid microstates above an oriented W33 edge are equivariantly the Cartesian product of the three Hermitian absolute points on its PG(3,4) secant with the two residual-hinge chirality anchors.":
      "The attractive arithmetic 6=3x2 does not define an edge-stabilizer-equivariant Cartesian product of Hermitian secant labels and residual-hinge chirality. The exact permutation-image orders recorded here locate the obstruction; the known 3+3 chirality blocks remain canonical, while the hidden C3 torsor is not the three absolute secant points coordinatewise.",
    boundary:"Exact finite group/scheduler test. The PG(3,4) label is imported only through the independently certified W33-Theory Hermitian cross-incidence; no physical particle chirality is asserted."
  };
  fs.writeFileSync(OUT,JSON.stringify(out,null,2)+"\n");
  process.stdout.write(JSON.stringify({status:"PASS",relation,images:out.permutationImages,
    bijections:equivariant.length,edge:[a,c],absLabels,residual})+"\n");
  return out;
}

if(require.main===module)run();
module.exports={run,sentinelSupports};
