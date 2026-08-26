// ======================================================================
// HOLOTRADE 540-Q3-CHART <-> 36-SPREAD TRIANGLE BRIDGE
//
// A W33 Q3 chart is an unordered pair of skew isotropic lines. There are
// exactly 540. Each such pair lies in exactly three symplectic spreads;
// those spreads form a triangle in the four-line-overlap graph, and every
// one of that graph's 540 triangles occurs exactly once. Thus the two
// 540-counts are literally bijective, with 1620 chart/spread incidence
// flags. The incidence matrix M obeys M^T M = 45 I + 6 A.
//
// A stronger conjecture was tested and rejected exactly: the 540-chart
// web adjacency does NOT preserve col(M) except for the constant sector.
// ======================================================================
(function(root){
  "use strict";
  const S=root.Substrate||(typeof require!=="undefined"?require("./substrate.js"):null);
  const W=root.HolotradeW33Scheduler||(typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const V=root.HolotradeSpreadVenueMarket||(typeof require!=="undefined"?require("./spread-venue-market.js"):null);
  if(!S||!W||!V)throw new Error("chart-spread-bridge requires substrate, w33-scheduler and spread-venue-market");
  const disjoint=(a,b)=>S.LINES[a].every(p=>!S.LINES[b].includes(p));
  const meet=(a,b)=>!disjoint(a,b);
  function charts(){const out=[];for(let a=0;a<S.LINES.length;a++)for(let b=a+1;b<S.LINES.length;b++)if(disjoint(a,b))out.push(Object.freeze([a,b]));return Object.freeze(out);}
  function containingSpreads(chart){return W.spreads().map((sp,i)=>sp.includes(chart[0])&&sp.includes(chart[1])?i:null).filter(i=>i!==null);}
  const key=t=>[...t].sort((a,b)=>a-b).join(",");
  function spreadTriangles(){const out=[];for(let a=0;a<36;a++)for(let b=a+1;b<36;b++)if(V.overlap(a,b)===4)for(let c=b+1;c<36;c++)if(V.overlap(a,c)===4&&V.overlap(b,c)===4)out.push(Object.freeze([a,b,c]));return Object.freeze(out);}
  function incidenceCertificate(){const C=charts(),triples=C.map(containingSpreads),tri=spreadTriangles(),chartKeys=new Set(triples.map(key)),triKeys=new Set(tri.map(key));const spreadDegree=Array(36).fill(0);for(const t of triples)for(const s of t)spreadDegree[s]++;
    let gram=true;for(let i=0;i<36&&gram;i++)for(let j=0;j<36;j++){let count=0;for(const t of triples)if(t.includes(i)&&t.includes(j))count++;const want=i===j?45:(V.overlap(i,j)===4?6:0);if(count!==want){gram=false;break;}}
    const theorem={charts540:C.length===540,threeSpreadsEach:triples.every(t=>t.length===3),triplesAreTriangles:triples.every(t=>V.overlap(t[0],t[1])===4&&V.overlap(t[0],t[2])===4&&V.overlap(t[1],t[2])===4),spreadTriangles540:tri.length===540,chartTriplesDistinct:chartKeys.size===540,triangleBijection:chartKeys.size===triKeys.size&&[...chartKeys].every(k=>triKeys.has(k)),eachSpread45Charts:spreadDegree.every(x=>x===45),flags1620:spreadDegree.reduce((a,b)=>a+b,0)===1620,gram45Iplus6A:gram};
    return Object.freeze({schema:"holotrade.w33-chart-spread-bridge.v1",valid:Object.values(theorem).every(Boolean),theorem,counts:{charts:C.length,spreadTriangles:tri.length,flags:spreadDegree.reduce((a,b)=>a+b,0)},gramSpectrum:{constant:135,multiplicityConstant:1,harmonic15:63,multiplicity15:15,harmonic20:27,multiplicity20:20,rank:36},evidenceBoundary:"Exact incidence combinatorics. No representation-theoretic, quantum, or physical equivalence is inferred from the bijection alone."});}
  function chartWebAdjacency(C=charts()){const nbr=Array.from({length:C.length},()=>[]);for(let i=0;i<C.length;i++){const [a,b]=C[i];for(let j=i+1;j<C.length;j++){const[c,d]=C[j];if(new Set([a,b,c,d]).size<4)continue;if(meet(a,c)&&meet(a,d)&&meet(b,c)&&meet(b,d)){nbr[i].push(j);nbr[j].push(i);}}}return nbr;}
  function intertwinerObstruction(){const C=charts(),triples=C.map(containingSpreads),nbr=chartWebAdjacency(C);const y=C.map((_,c)=>nbr[c].reduce((s,d)=>s+(triples[d].includes(0)?1:0),0));const t=Array(36).fill(0);for(let c=0;c<C.length;c++)for(const s of triples[c])t[s]+=y[c];const num=Array.from({length:36},(_,s)=>s===0?-52:(V.overlap(s,0)===4?26:2));const normal=[];for(let i=0;i<36;i++){let lhs=45*num[i];for(let j=0;j<36;j++)if(i!==j&&V.overlap(i,j)===4)lhs+=6*num[j];normal.push(lhs===63*t[i]);}
    let witness=null;for(let c=0;c<C.length&&!witness;c++){const fitted=triples[c].reduce((s,k)=>s+num[k],0),actual=63*y[c];if(fitted!==actual)witness={chartIndex:c,chart:[...C[c]],containingSpreads:[...triples[c]],actualTimes63:actual,fittedNumerator:fitted,residual:actual-fitted};}
    const theorem={chartWeb540:C.length===540,chartWebDegree6:nbr.every(x=>x.length===6),normalEquationsSatisfied:normal.every(Boolean),nonzeroResidual:!!witness&&witness.residual!==0};return Object.freeze({schema:"holotrade.w33-chart-spread-intertwiner-obstruction.v1",valid:Object.values(theorem).every(Boolean),theorem,witness,leastSquaresCoefficientDenominator:63,coefficientRule:"-52 at source spread, 26 at four-line neighbors, 2 at one-line non-neighbors",conclusion:"Chart-web adjacency does not preserve the 36-dimensional spread-incidence column space. Only the constant direction is forced invariant by regularity.",evidenceBoundary:"Exact failed-intertwiner certificate; it explicitly prevents promoting the chart/triangle bijection into an unsupported adjacency equivalence."});}
  const API={charts,containingSpreads,spreadTriangles,incidenceCertificate,chartWebAdjacency,intertwinerObstruction};root.HolotradeChartSpreadBridge=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
