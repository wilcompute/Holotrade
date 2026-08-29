"use strict";

// Exact second-step controller for the image of the 2,880 near-ovoid states
// after one topology-aware migration.
//
// On that certified 2,818-state image, the full generic policy collapses to:
//   1. choose the lexicographically first busy point incident with the maximum
//      number of singly occupied W33 lines;
//   2. release it;
//   3. among adjacent idle destinations, choose the lexicographically first
//      point hitting the fewest currently free lines.
// This is exactly equivalent to the generic topology-aware move on all 2,880
// provenance-labelled starts and produces nine free lines after move two.

const S=require("../js/substrate.js");
const M=require("./w33-near-ovoid-migration.js");

function occupancies(busy){const B=new Set(busy);return S.LINES.map((L)=>L.reduce((n,p)=>n+(B.has(p)?1:0),0));}
function chooseSecondMove(busy){
  const B=[...new Set(busy)].sort((a,b)=>a-b);
  if(B.length!==10)throw new RangeError("stage-2 controller requires ten busy points");
  const occ=occupancies(B),busySet=new Set(B);
  const singleCount=(p)=>S.LINES.reduce((n,L,li)=>n+(L.includes(p)&&occ[li]===1?1:0),0);
  const maxSingles=Math.max(...B.map(singleCount));
  const from=B.find((p)=>singleCount(p)===maxSingles);
  const afterRelease=B.filter((p)=>p!==from);
  const freeAfterRelease=M.freeLineIds(afterRelease),freeSet=new Set(freeAfterRelease);
  const candidates=[];
  for(let to=0;to<S.CONST.points;to++){
    if(busySet.has(to)||!S.isAdjacent(from,to))continue;
    const hitFree=S.LINES.reduce((n,L,li)=>n+(L.includes(to)&&freeSet.has(li)?1:0),0);
    const nextBusy=afterRelease.concat(to).sort((a,b)=>a-b);
    candidates.push({from,to,rays:S.migrationRays(from,to),hops:S.route(from,to).distance,maxSingles,hitFree,freeLinesAfterRelease:freeAfterRelease.length,freeLinesAfterMove:M.freeLineIds(nextBusy).length,nextBusy});
  }
  if(!candidates.length)throw new Error("post-first state has no adjacent idle destination");
  candidates.sort((a,b)=>(a.hitFree-b.hitFree)||(a.to-b.to));
  return candidates[0];
}
module.exports={occupancies,chooseSecondMove};
