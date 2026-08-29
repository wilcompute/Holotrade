"use strict";

// Two-state source controller induced by the canonical 3+3 microstate blocks.
//
// For a near-ovoid with defect centre a and blocker centre c, the hinge line ac
// contains two residual points.  Exactly one residual point lies in the exact
// four-point high-release set.  The unique nontrivial 3+3 block system is
// therefore encoded by one bit: which residual hinge point is active.
//
// Action: release/migrate that active residual point.  This chooses a certified
// high-release source without rescoring all ten busy points.  Destination
// selection still respects the same movement floor and maximises final line
// headroom among adjacent healthy destinations.

const S=require("../js/substrate.js");
const M=require("./w33-near-ovoid-migration.js");

function hingeLine(a,c){
  const ids=[];
  for(let li=0;li<S.LINES.length;li++) if(S.LINES[li].includes(a)&&S.LINES[li].includes(c)) ids.push(li);
  if(ids.length!==1) throw new Error("expected a unique W33 hinge line");
  return ids[0];
}

function classify(busy){
  const info=M.analyzeNearOvoid(busy);
  if(!info) return null;
  const li=hingeLine(info.defectCenter,info.blockerCenter);
  const residual=S.LINES[li]
    .filter((p)=>p!==info.defectCenter&&p!==info.blockerCenter)
    .sort((a,b)=>a-b);
  if(residual.length!==2) throw new Error("hinge residual pair malformed");
  const active=residual.filter((p)=>info.highRelease.includes(p));
  if(active.length!==1) throw new Error("microstate did not select exactly one hinge residual");
  const block=active[0]===residual[0]?0:1;
  return {
    block,
    source:active[0],
    residual,
    defectCenter:info.defectCenter,
    blockerCenter:info.blockerCenter,
    hingeLine:li,
    highRelease:info.highRelease,
  };
}

function chooseMove(busy){
  const state=classify(busy);
  if(!state) return null;
  const B=new Set(busy);
  const from=state.source;
  const candidates=[];
  for(let to=0;to<S.CONST.points;to++){
    if(B.has(to)) continue;
    const rays=S.migrationRays(from,to);
    const hops=S.route(from,to).distance;
    const next=[...B].filter((p)=>p!==from).concat([to]).sort((a,b)=>a-b);
    candidates.push({
      from,to,rays,hops,nextBusy:next,
      freeLinesAfterRelease:M.freeLineIds([...B].filter((p)=>p!==from)).length,
      freeLinesAfterMove:M.freeLineIds(next).length,
    });
  }
  candidates.sort((a,b)=>
    (a.rays-b.rays)||
    (a.hops-b.hops)||
    (b.freeLinesAfterMove-a.freeLinesAfterMove)||
    (a.to-b.to)
  );
  return {...candidates[0],...state};
}

module.exports={hingeLine,classify,chooseMove};
