// ======================================================================
// HOLOTRADE W33 TENSOR SHARDING / ROBUSTNESS BOUNDS
//
// A tensor tile at depth 2 is L x M for two W33 lines: 16 leaves in the
// 40 x 40 Cartesian fabric.  The exact level-1 line transversal number
// tau_1=11 is imported from the repository's independently frozen SAT
// certificate.  Shadow double-counting gives 110 <= tau_tensor,2.  The
// product construction B x B gives 121; a CYCLIC-ORDER-12-INVARIANT blocker
// found by CP-SAT gives 115, so the product construction is NOT optimal.
// Current interval 110 <= tau_tensor,2 <= 115.  The exact value is OPEN.
// ======================================================================
(function(root){
  "use strict";
  const S=root.Substrate||(typeof require!=="undefined"?require("./substrate.js"):null);
  const W=root.HolotradeW33Scheduler||(typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const SAT=(typeof require!=="undefined"?require("../data/w33_blocking_sat.json"):null);
  if(!S||!W||!SAT)throw new Error("tensor-sharding requires substrate, w33-scheduler and blocking SAT certificate");
  const lineRow=SAT.shapes.find(x=>x.kind==="densest"&&x.m===4);
  if(!lineRow)throw new Error("missing exact m=4 blocking certificate");
  const TAU1=lineRow.tau;
  const BLOCKER=Object.freeze([...lineRow.witness]);
  function hitsAllLines(points){const B=new Set(points);return S.LINES.every(L=>L.some(p=>B.has(p)));}
  function lineBlockerCertificate(){const theorem={tau1Eleven:TAU1===11,witnessSize11:BLOCKER.length===11,witnessHitsAll40:hitsAllLines(BLOCKER),satUnsatBelow11:lineRow.guaranteeProvedUnsat===true&&lineRow.unsatProofs===10};return Object.freeze({schema:"holotrade.w33-line-blocker-import.v1",valid:Object.values(theorem).every(Boolean),theorem,tau1:TAU1,witness:[...BLOCKER],source:"data/w33_blocking_sat.json",boundary:"Minimality is imported from the frozen SAT/UNSAT certificate; this module independently checks the explicit upper witness."});}
  const leaf=(p,q)=>p*40+q;
  function productTile(lineA,lineB){if(!S.LINES[lineA]||!S.LINES[lineB])throw new RangeError("invalid W33 line");const leaves=[];for(const p of S.LINES[lineA])for(const q of S.LINES[lineB])leaves.push(leaf(p,q));return Object.freeze({lineA,lineB,leaves:Object.freeze(leaves.sort((a,b)=>a-b))});}
  // A 115-leaf blocker invariant under an order-6 element of Aut(W33),
  // found by orbit-collapsed CP-SAT (analysis/tensor_symmetric_blocker.py)
  // and re-verified below against all 1600 product tiles.  It beats B x B,
  // and its row support is 37 -- not an 11-point line blocker -- which
  // refutes the hypothesis of the earlier conditional tau=121 theorem.
  const SYMMETRIC_WITNESS=Object.freeze([24,29,30,62,103,105,106,107,143,145,147,149,150,164,178,191,219,221,225,235,254,295,296,317,325,335,336,407,419,421,425,451,453,478,497,524,533,558,593,608,625,634,635,659,665,674,675,719,731,738,751,770,792,797,855,872,877,881,908,922,923,943,945,946,960,987,990,1000,1001,1002,1009,1020,1024,1026,1027,1028,1029,1036,1042,1063,1065,1069,1082,1083,1104,1142,1160,1163,1186,1200,1203,1224,1230,1251,1253,1271,1287,1288,1301,1305,1326,1365,1370,1376,1405,1410,1432,1487,1488,1505,1514,1524,1538,1558,1572]);
  function blockerProduct(){const leaves=[];for(const p of BLOCKER)for(const q of BLOCKER)leaves.push(leaf(p,q));return leaves;}
  function hitsAllProductTiles(points){const B=new Set(points);for(let a=0;a<40;a++)for(let b=0;b<40;b++)if(!productTile(a,b).leaves.some(x=>B.has(x)))return false;return true;}
  function tensorBlockingBounds(depth=2){if(!Number.isInteger(depth)||depth<1)throw new RangeError("depth must be positive integer");const lower=TAU1*Math.pow(10,depth-1),product=Math.pow(TAU1,depth);const upper=depth===2?SYMMETRIC_WITNESS.length:product;return Object.freeze({depth,lower,upper,productUpper:product,upperBeatsProduct:upper<product,exact:depth===1,proof:depth===1?"repository SAT certificate":"Recursive shadow double-count: each fixed first-axis line needs a depth-(n-1) blocker, 40 line shadows are counted, and each leaf belongs to 4 first-axis lines, multiplying the lower bound by 10. Upper bound at depth 2 is the explicit 115-leaf order-6-invariant blocker; at other depths it is the product construction B^n.",boundary:"Finite-combinatorial placement guarantee only; not a physical availability SLA."});}
  function depth2Certificate(){const base=lineBlockerCertificate(),product=blockerProduct(),best=[...SYMMETRIC_WITNESS];const bounds=tensorBlockingBounds(2);const rowSupport=new Set(best.map(v=>Math.floor(v/40))).size,colSupport=new Set(best.map(v=>v%40)).size;const minimal=best.every(v=>{const T=new Set(best);T.delete(v);return !hitsAllProductTiles(T);});const theorem={baseValid:base.valid,lower110:bounds.lower===110,productWitnessSize121:product.length===121,productWitnessHitsAll1600ProductPlacements:hitsAllProductTiles(product),upper115:bounds.upper===115,bestWitnessSize115:best.length===115,bestWitnessHitsAll1600ProductPlacements:hitsAllProductTiles(best),bestWitnessMinimal:minimal,bestWitnessBeatsProduct:best.length<product.length,rowSupportExceedsLineBlocker:rowSupport>TAU1};return Object.freeze({schema:"holotrade.w33-tensor-blocking.v2",valid:Object.values(theorem).every(Boolean),theorem,bounds,openGap:bounds.upper-bounds.lower,exactTau:null,upperWitness:best,productWitness:product,rowSupport,colSupport,productConstructionOptimal:false,evidenceBoundary:"110 is a proved lower bound conditional only on the repository's exact tau1=11 SAT certificate; 115 is constructive and re-verified here leaf-by-leaf. B x B = 121 is superseded, so the product construction is proved non-optimal. No claim is made that either endpoint is the exact depth-2 value."});}
  function pairedSpreadShard(spreadA=0,spreadB=1,permutation=null){const spreads=W.spreads();const A=spreads[spreadA],B=spreads[spreadB];if(!A||!B)throw new RangeError("invalid spread");const perm=permutation||Array.from({length:10},(_,i)=>i);if(perm.length!==10||new Set(perm).size!==10||perm.some(i=>i<0||i>9))throw new Error("permutation must rearrange 0..9");const tiles=A.map((la,i)=>productTile(la,B[perm[i]]));const all=tiles.flatMap(t=>t.leaves),unique=[...new Set(all)].sort((a,b)=>a-b),first=new Set(unique.map(x=>Math.floor(x/40))),second=new Set(unique.map(x=>x%40));const theorem={tenTiles:tiles.length===10,eachTile16:tiles.every(t=>t.leaves.length===16),disjoint160:all.length===160&&unique.length===160,firstShadow40:first.size===40,secondShadow40:second.size===40};return Object.freeze({schema:"holotrade.w33-paired-spread-shard.v1",valid:Object.values(theorem).every(Boolean),theorem,spreadA,spreadB,permutation:[...perm],tiles,leaves:unique,totalLeaves:160,comparison:{standardLineLiftLeaves:160,tensorTileLeaves:16,tilesPerEqualCapacity:10},evidenceBoundary:"Equal-capacity combinatorial sharding construction; congestion, failure correlation and performance are not measured here."});}
  function recursiveCapacity(depth){if(!Number.isInteger(depth)||depth<1)throw new RangeError("depth must be positive integer");const tensor=Math.pow(4,depth),lift=4*Math.pow(40,depth-1),ratio=lift/tensor,b=tensorBlockingBounds(depth);return Object.freeze({depth,tensorTileLeaves:tensor,standardLiftLeaves:lift,capacityRatio:ratio,blockingLower:b.lower,blockingUpper:b.upper,lowerAmplificationVsLift:b.lower/TAU1,identityHolds:ratio===Math.pow(10,depth-1)&&b.lower/TAU1===ratio});}
  const API={TAU1,BLOCKER,SYMMETRIC_WITNESS,lineBlockerCertificate,productTile,tensorBlockingBounds,depth2Certificate,pairedSpreadShard,recursiveCapacity,hitsAllProductTiles};root.HolotradeTensorSharding=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
