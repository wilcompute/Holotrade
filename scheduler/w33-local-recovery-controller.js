"use strict";

// Exact healthy level-1 recovery controller for ten busy W33 points.
//
// Let F be the number of free lines, s1(p) the number of singleton lines
// incident with busy source p, z(q) the number of currently free lines incident
// with adjacent idle destination q, and ell=pq the unique W33 line through an
// adjacent pair.  Releasing p opens exactly s1(p) lines.  Occupying q destroys
// z(q) old free lines plus the newly opened shared line iff ell was singleton.
// Therefore
//
//   F_after = F + s1(p) - z(q) - 1[occ(ell)=1].
//
// With ten busy points every source has at least 12-9=3 adjacent idle points,
// so the exact 3-ray / 1-hop movement floor is always available in the healthy
// model.  Maximising F_after, then release headroom, then labels is algebraically
// identical to the existing topology-aware scorer, without constructing every
// candidate next state.

const S=require("../js/substrate.js");

const PAIR_LINE=new Map();
S.LINES.forEach((L,li)=>{
  for(let i=0;i<L.length;i++)for(let j=i+1;j<L.length;j++){
    const a=Math.min(L[i],L[j]),b=Math.max(L[i],L[j]);PAIR_LINE.set(`${a}:${b}`,li);
  }
});

function occupancy(busy){
  const B=new Set(busy);return S.LINES.map((L)=>L.reduce((n,p)=>n+(B.has(p)?1:0),0));
}
function chooseMigration(busy){
  const B=[...new Set(busy)].sort((a,b)=>a-b);if(B.length!==10)throw new RangeError("local controller requires exactly ten busy points");
  const set=new Set(B),occ=occupancy(B),free=occ.filter((x)=>x===0).length;
  const singleton=new Set(occ.map((x,i)=>x===1?i:-1).filter((i)=>i>=0));
  const zero=new Set(occ.map((x,i)=>x===0?i:-1).filter((i)=>i>=0));
  let best=null;
  for(const from of B){
    const s1=S.LINES.reduce((n,L,li)=>n+(singleton.has(li)&&L.includes(from)?1:0),0);
    const idleAdj=S.ADJ[from].filter((to)=>!set.has(to)).sort((a,b)=>a-b);
    if(idleAdj.length<3)throw new Error("degree-count invariant failed: source has fewer than three adjacent idle points");
    for(const to of idleAdj){
      const z=S.LINES.reduce((n,L,li)=>n+(zero.has(li)&&L.includes(to)?1:0),0);
      const li=PAIR_LINE.get(`${Math.min(from,to)}:${Math.max(from,to)}`);
      if(li==null)throw new Error("adjacent pair has no W33 line");
      const refill=occ[li]===1?1:0;
      const after=free+s1-z-refill,release=free+s1;
      const row={from,to,freeLinesAfterMove:after,freeLinesAfterRelease:release,singletonsAtSource:s1,oldFreeAtDestination:z,refillsReleasedSharedLine:Boolean(refill)};
      if(!best||after>best.freeLinesAfterMove||
        (after===best.freeLinesAfterMove&&(release>best.freeLinesAfterRelease||
        (release===best.freeLinesAfterRelease&&(from<best.from||(from===best.from&&to<best.to))))))best=row;
    }
  }
  const nextBusy=B.filter((p)=>p!==best.from).concat([best.to]).sort((a,b)=>a-b);
  return {...best,nextBusy,rays:3,hops:1};
}

module.exports={occupancy,chooseMigration};
