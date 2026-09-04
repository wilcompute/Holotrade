// Fail-closed adapter from protected one-qutrit Pauli addresses to the
// committed W33-axis / Payne slow-cover catalogue.  The chosen 40-state map
// is reproducible but is explicitly a gauge choice among 800 F20-equivariant
// bijections; callers must retain that fact in any receipt or cache key.
"use strict";

const atlas=require("../data/w33_f20_payne_five_state_atlas.json");
const {PayneCoverCatalogue}=require("./w33-payne-cover-catalogue.js");

function sameInts(a,b){return Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((x,i)=>x===b[i]);}

function bootCheck(){
  const errors=[];
  let catalogue=null;
  try{catalogue=new PayneCoverCatalogue();}catch(_error){errors.push("PAYNE_CATALOGUE");}
  if(atlas.schema!=="holotrade.w33-f20-payne-five-state-atlas.v1"||atlas.status!=="PASS")errors.push("ATLAS_CERT");
  if(!/^[0-9a-f]{64}$/.test(atlas.sha256||""))errors.push("ATLAS_DIGEST");
  const bridge=atlas.addressToPayne||{};
  const rows=bridge.compiler||[];
  if(bridge.equivariantBijections!==800)errors.push("GAUGE_COUNT");
  if(rows.length!==40)errors.push("ADDRESS_COUNT");
  if(new Set(rows.map((row)=>row.w33Axis)).size!==40)errors.push("AXIS_BIJECTION");
  for(let address=0;address<rows.length;address+=1){
    const row=rows[address];
    if(row.address!==address||row.site!==Math.floor(address/8)||row.localPauliLabel!==address%8)errors.push(`ADDRESS_${address}`);
    if(!Array.isArray(row.payneSlowCover)||row.payneSlowCover.length!==9||new Set(row.payneSlowCover).size!==9)errors.push(`COVER_${address}`);
    if(catalogue&&!sameInts(row.payneSlowCover,catalogue.coverForAxis(row.w33Axis)))errors.push(`PRODUCTION_COVER_${address}`);
    if(row.matchedCircuitTarget!==atlas.fiveStateAtlas.circuit.qutritSiteToSlowTarget[row.site])errors.push(`CIRCUIT_${address}`);
    if(catalogue){
      const repair=catalogue.stage(row.matchedCircuitTarget,row.w33Axis);
      if(repair.routeDistance!==1||!catalogue.coverForAxis(repair.chosenAxis).includes(row.matchedCircuitTarget))errors.push(`ONE_HOP_${address}`);
    }
  }
  const noGo=atlas.incidenceCompatibilityNoGo||{};
  if(noGo.presentationCompatibleF20Isomorphisms!==20||noGo.equivariantMapCandidates!==16000||noGo.coherentMaps!==0)errors.push("INCIDENCE_BOUNDARY");
  if(noGo.overlapCensus?.maximumMatchedAddresses!==20||noGo.overlapCensus?.matchedAddressHistogram?.[0]!==9600||noGo.overlapCensus?.matchedAddressHistogram?.[20]!==6400)errors.push("OVERLAP_CENSUS");
  if(atlas.oneHopRepair?.selectedGaugeAllExactlyOneHop!==true||atlas.oneHopRepair?.selectedGaugeDistanceHistogram?.[1]!==40)errors.push("ONE_HOP_CERT");
  return Object.freeze({ok:errors.length===0,errors:Object.freeze(errors)});
}

class F20PayneCodec{
  constructor(){
    const boot=bootCheck();
    if(!boot.ok)throw new Error(`F20 Payne codec boot refused: ${boot.errors.join(",")}`);
    this.schema=atlas.schema;
    this.atlasDigest=`sha256:${atlas.sha256}`;
    this.gaugeId=this.atlasDigest;
    this.gaugeChoice=atlas.addressToPayne.selectedMap;
    this.equivariantChoices=atlas.addressToPayne.equivariantBijections;
    this.catalogue=new PayneCoverCatalogue();
  }
  compile(address){
    if(!Number.isInteger(address)||address<0||address>=40)throw new RangeError("address must be 0..39");
    const row=atlas.addressToPayne.compiler[address];
    const repair=this.catalogue.stage(row.matchedCircuitTarget,row.w33Axis);
    return Object.freeze({
      schema:"holotrade.w33-f20-payne-compiled-address.v1",
      dispatchable:false,
      atlasDigest:this.atlasDigest,
      gaugeId:this.gaugeId,
      gaugeChoice:this.gaugeChoice,
      address:row.address,
      site:row.site,
      localPauliLabel:row.localPauliLabel,
      w33Axis:row.w33Axis,
      payneSlowCover:this.catalogue.coverForAxis(row.w33Axis),
      matchedCircuitTarget:row.matchedCircuitTarget,
      coverContainsMatchedTarget:row.coverContainsMatchedTarget,
      oneHopRepair:Object.freeze({...repair,dispatchable:false}),
      boundary:"Finite F20-equivariant address translation plus a non-equivariant certified one-hop staging repair; neither is a fault-tolerant recode, physical route, or dispatch authorization.",
    });
  }
  circuitTargetForSite(site){
    if(!Number.isInteger(site)||site<0||site>=5)throw new RangeError("site must be 0..4");
    return atlas.fiveStateAtlas.circuit.qutritSiteToSlowTarget[site];
  }
}

module.exports={F20PayneCodec,bootCheck};
