// ======================================================================
// HOLOTRADE W33 SECTOR-DIVERSE REPLAY QUORUM
//
// Independent deterministic re-executions are placed on distinct fleet nodes
// and distinct anchor-line sectors of the exact 36-spread W33 carrier.  The
// four sectors are optionally labeled by the four dimensions of the Q4
// controller.  This is logical/simulated path diversity, not hardware fault-
// domain independence or proof that physical packets traversed those spreads.
// ======================================================================
(function(root){
  "use strict";
  const S=root.Substrate||(typeof require!=="undefined"?require("./substrate.js"):null);
  const W=root.HolotradeW33Scheduler||(typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const Q=root.HolotradeHypercube||(typeof require!=="undefined"?require("./hypercube.js"):null);
  const R=root.HolotradeResultContract||(typeof require!=="undefined"?require("./result-contract.js"):null);
  const C=root.HolotradeW33TransitionCertificate||(typeof require!=="undefined"?require("./w33-transition-certificate.js"):null);
  const Challenge=root.HolotradeChallengeMarket||(typeof require!=="undefined"?require("./challenge-market.js"):null);
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  if(!S||!W||!Q||!R||!C||!Challenge||!E)throw new Error("replay-quorum dependencies missing");
  const SCHEMA="holotrade.w33-sector-replay-quorum.v1";

  function sectorCatalog(anchorPoint){
    const cert=W.spreadCertificate(anchorPoint);if(!cert.valid)throw new Error("W33 spread certificate invalid");
    const overlay=Q.sectorOverlay(cert.anchorLines);
    return cert.anchorLines.map((lineId)=>Object.freeze({lineId,q4Dimension:overlay.dimensions[lineId],spreadIndices:W.spreads().map((s,i)=>s.includes(lineId)?i:null).filter((x)=>x!==null)}));
  }
  function restrictedSchedule(demands,spreadIndices){
    const remaining=[...demands],frames=[],catalog=W.spreads();
    while(remaining.length){let best=null;
      for(const spreadIndex of spreadIndices){const lineSet=new Set(catalog[spreadIndex]),seen=new Set(),covered=[];for(const row of remaining){if(lineSet.has(row.lineId)&&!seen.has(row.lineId)){seen.add(row.lineId);covered.push(row);}}
        if(!best||covered.length>best.demands.length||(covered.length===best.demands.length&&spreadIndex<best.spreadIndex))best={spreadIndex,demands:covered};}
      if(!best||best.demands.length===0)return null;
      const ids=new Set(best.demands.map((r)=>r.demandId));frames.push(Object.freeze({spreadIndex:best.spreadIndex,demandIds:Object.freeze([...ids].sort()),lineIds:Object.freeze(best.demands.map((r)=>r.lineId).sort((a,b)=>a-b))}));
      for(let i=remaining.length-1;i>=0;i--)if(ids.has(remaining[i].demandId))remaining.splice(i,1);
    }
    return Object.freeze({frames:Object.freeze(frames),frameCount:frames.length,conflictFree:true});
  }
  function chooseRows(bySector,quorum){
    let best=null;const sectors=[...bySector.keys()];
    function chooseSectorSets(start,chosen){if(chosen.length===quorum){assign(0,chosen,new Set(),[],0);return;}for(let i=start;i<=sectors.length-(quorum-chosen.length);i++)chooseSectorSets(i+1,[...chosen,sectors[i]]);}
    function assign(pos,chosen,used,rows,score){if(best&&score>=best.score)return;if(pos===chosen.length){const ids=rows.map((r)=>r.node.id);const key=ids.slice().sort().join("|")+"|"+chosen.join(",");if(!best||score<best.score||(score===best.score&&key<best.key))best={rows:[...rows],score,key};return;}const sec=chosen[pos];for(const row of bySector.get(sec)||[]){if(used.has(row.node.id))continue;used.add(row.node.id);assign(pos+1,chosen,used,[...rows,row],score+row.objective);used.delete(row.node.id);}}
    chooseSectorSets(0,[]);return best;
  }
  function planSectorQuorum(projectionEngine,executionEngine,projection,{quorum=3,requestedSeconds=1,anchorPoint=null,maxCandidates=120,perSectorLimit=12,framePenalty=0}={}){
    if(!Number.isInteger(quorum)||quorum<2||quorum>4)throw new RangeError("sector-diverse quorum must be 2..4 (four anchor-line sectors)");
    const created=projectionEngine.createPlan(projection,{requestedSeconds});
    const base=executionEngine.place(created.plan,{limit:maxCandidates});if(base.length<quorum)throw new Error("insufficient admissible fleet nodes for replay quorum");
    const anchors=anchorPoint==null?[...Array(S.POINTS.length).keys()]:[anchorPoint];let globalBest=null;
    for(const ap of anchors){const sectors=sectorCatalog(ap),bySector=new Map();for(const sec of sectors){const rows=[];for(const candidate of base){const demands=W.inputLineDemands(projection,candidate.node.cellPoint),schedule=restrictedSchedule(demands,sec.spreadIndices);if(!schedule)continue;rows.push(Object.freeze({sectorLine:sec.lineId,q4Dimension:sec.q4Dimension,node:candidate.node,candidate,demands,schedule,estimatedCost:candidate.total,objective:candidate.total+framePenalty*schedule.frameCount}));}rows.sort((a,b)=>a.objective-b.objective||a.node.id.localeCompare(b.node.id));bySector.set(sec.lineId,rows.slice(0,perSectorLimit));}
      const pick=chooseRows(bySector,quorum);if(pick&&(!globalBest||pick.score<globalBest.score))globalBest={anchorPoint:ap,pick,sectors};}
    if(!globalBest)throw new Error("no node-distinct W33 sector-diverse quorum is schedulable");
    const selected=globalBest.pick.rows.sort((a,b)=>a.q4Dimension-b.q4Dimension);
    const body={schema:SCHEMA,projectionDigest:projection.digest,anchorPoint:globalBest.anchorPoint,quorum,requestedSeconds,selected:Object.freeze(selected.map((r)=>Object.freeze({nodeId:r.node.id,nodePoint:r.node.cellPoint,sectorLine:r.sectorLine,q4Dimension:r.q4Dimension,estimatedCost:r.estimatedCost,objective:r.objective,frameCount:r.schedule.frameCount,spreadIndices:Object.freeze(r.schedule.frames.map((f)=>f.spreadIndex))}))),estimatedQuorumCost:selected.reduce((s,r)=>s+r.estimatedCost,0),distinctNodes:new Set(selected.map((r)=>r.node.id)).size===quorum,distinctSectors:new Set(selected.map((r)=>r.sectorLine)).size===quorum,boundary:"Independence means distinct simulated fleet nodes plus distinct exact W33 anchor-line scheduling sectors. Q4 dimensions are a chosen controller overlay. Physical rack/provider/common-mode independence is not established."};
    return Object.freeze({...body,_selectedRows:Object.freeze(selected),templatePlan:created.plan,digest:E.demoDigest(body)});
  }
  function executeSectorQuorum(projectionEngine,executionEngine,projection,planned,{contract,resultValue,requestedSeconds=planned.requestedSeconds}={}){
    const launches=[];
    for(const row of planned._selectedRows){const created=projectionEngine.createPlan(projection,{requestedSeconds});const launch=executionEngine.launch(created.plan,row.node);if(!launch.ok)throw new Error(`replay launch failed on ${row.node.id}: ${launch.reason}`);launches.push({row,plan:created.plan});}
    const settled=executionEngine.meter(requestedSeconds);const receiptByPlan=new Map(settled.map((r)=>[r.planId,r]));const bundles=[];
    for(const x of launches){const receipt=receiptByPlan.get(x.plan.id);if(!receipt||receipt.outcome!=="settled")throw new Error(`missing settled replay receipt for ${x.plan.id}`);const emission=R.emit(projectionEngine,projection,x.plan,receipt,{contract,value:resultValue});const certificate=C.buildCertificate({projection,plan:x.plan,receipt,emission,executionEngine,projectionEngine});if(certificate.status!=="PASS")throw new Error("replay transition certificate failed");bundles.push(Object.freeze({nodeId:x.row.node.id,sectorLine:x.row.sectorLine,q4Dimension:x.row.q4Dimension,plan:x.plan,receipt,emission,certificate}));}
    return Object.freeze({schema:`${SCHEMA}.execution`,plannedDigest:planned.digest,bundles:Object.freeze(bundles),actualCost:bundles.reduce((s,b)=>s+b.receipt.cost,0),actualNodeSeconds:bundles.reduce((s,b)=>s+b.receipt.nodeSeconds,0)});
  }
  function verifyExecutedQuorum(executed,{bounty=0,sponsor="replay-quorum"}={}){
    if(!executed||!Array.isArray(executed.bundles)||executed.bundles.length<3)throw new Error("at least three independently executed bundles required");
    const [source,...replays]=executed.bundles,pool=new Challenge.ChallengePool();const challenge=pool.open(source.certificate,{emission:source.emission,bounty,deterministic:true,sponsor});const result=pool.resolveQuorum(challenge,replays,{minimum:replays.length});return Object.freeze({challenge,result,verified:result.resolved===true&&result.match===true,distinctNodes:new Set(executed.bundles.map((b)=>b.nodeId)).size,distinctSectors:new Set(executed.bundles.map((b)=>b.sectorLine)).size,totalActualCost:executed.actualCost});
  }
  const API={SCHEMA,sectorCatalog,restrictedSchedule,planSectorQuorum,executeSectorQuorum,verifyExecutedQuorum};root.HolotradeReplayQuorum=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
