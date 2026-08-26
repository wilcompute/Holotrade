// ======================================================================
// HOLOTRADE Q3 CHART / SPREAD CALENDAR FUSION
// Exact structural fusion: 540 skew-line Q3 charts -> 540 spread triangles,
// a proper 8-colouring of the 36 spread graph, and the 1+15+20 harmonics.
// ======================================================================
(function(root){
  "use strict";
  const B=root.HolotradeChartSpreadBridge||(typeof require!=="undefined"?require("./chart-spread-bridge.js"):null);
  const V=root.HolotradeSpreadVenueMarket||(typeof require!=="undefined"?require("./spread-venue-market.js"):null);
  const H=root.HolotradeSpreadHarmonics||(typeof require!=="undefined"?require("./spread-harmonics.js"):null);
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  if(!B||!V||!H||!E)throw new Error("chart-calendar-fusion requires chart-spread-bridge, spread-venue-market, spread-harmonics, evidence");
  // Frozen SAT witness from data/spread_colouring_sat.json. Keeping the vector
  // here makes the browser-side certificate independent of JSON require().
  const COLOURING=Object.freeze([0,1,2,6,7,5,4,3,6,3,5,1,3,2,6,0,7,4,3,4,7,4,6,5,7,1,5,6,5,2,2,1,0,4,1,0]);
  function classes(){const out=Array.from({length:8},()=>[]);COLOURING.forEach((c,i)=>out[c].push(i));return out.map(x=>Object.freeze(x));}
  function chartRows(){return B.charts().map((chart,i)=>{const spreads=B.containingSpreads(chart),colours=spreads.map(s=>COLOURING[s]);return Object.freeze({chartId:i,lines:Object.freeze([...chart]),spreads:Object.freeze(spreads),colours:Object.freeze(colours),distinctColours:new Set(colours).size});});}
  function spreadCoordinate(spreadId){if(!Number.isInteger(spreadId)||spreadId<0||spreadId>=36)throw new RangeError("spreadId out of range");const hc=H.certificate();return Object.freeze({spreadId,calendarColour:COLOURING[spreadId],harmonicProjectorColumnNumerators:{constant:hc.projectorNumerators.constant.map(r=>r[spreadId]),harmonic15:hc.projectorNumerators.harmonic15.map(r=>r[spreadId]),harmonic20:hc.projectorNumerators.harmonic20.map(r=>r[spreadId])},projectorDenominator:hc.projectorDenominator});}
  function certificate(){
    const bridge=B.incidenceCertificate(),harm=H.certificate(),C=classes(),rows=chartRows();
    const proper=Array.from({length:36},(_,i)=>Array.from({length:36},(_,j)=>i>=j||V.overlap(i,j)!==4||COLOURING[i]!==COLOURING[j])).flat().every(Boolean);
    const theorem={bridge540:bridge.valid&&bridge.counts.charts===540&&bridge.counts.flags===1620,colours8:C.length===8,covers36:new Set(C.flat()).size===36,classSizes:JSON.stringify(C.map(x=>x.length).sort((a,b)=>a-b))===JSON.stringify([4,4,4,4,5,5,5,5]),properIndependentBatches:proper,everyChartTriangleUsesThreeDistinctColours:rows.every(r=>r.spreads.length===3&&r.distinctColours===3),harmonics1plus15plus20:harm.valid&&harm.ranks.constant===1&&harm.ranks.harmonic15===15&&harm.ranks.harmonic20===20};
    const body={schema:"holotrade.w33-chart-calendar-fusion.v1",valid:Object.values(theorem).every(Boolean),theorem,colouring:[...COLOURING],classes:C,counts:{charts:rows.length,chartSpreadFlags:1620,batches:8},harmonicRanks:harm.ranks,boundary:"Exact scheduling/combinatorial coordinates only. Calendar colours and harmonic coordinates are not physical time slots, throughput measurements, or failure probabilities."};return Object.freeze({...body,digest:E.demoDigest(body)});
  }
  const API={COLOURING,classes,chartRows,spreadCoordinate,certificate};root.HolotradeChartCalendarFusion=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
