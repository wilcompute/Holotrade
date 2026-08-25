// ======================================================================
// HOLOTRADE 36-SPREAD VENUE MARKET / LINE-PRESERVING HEDGES
//
// Exact finite layer over W(3,3)'s 36 symplectic spreads.  Four-line overlap
// is the NO_6^-(2) venue relation.  New operational theorem: for any anchor
// spread A and each line l in A, exactly two remote spreads preserve l; the
// three spreads intersect pairwise in exactly l.  Across the nine spreads
// containing a fixed line, one-line overlap is 3 K3 and four-line overlap is
// K_{3,3,3}.  The two remote legs are the Johnson J(6,3) antipodes.
// ======================================================================
(function (root) {
  "use strict";
  const W = root.HolotradeW33Scheduler || (typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const E = root.HolotradeEvidence || (typeof require!=="undefined"?require("./evidence.js"):null);
  if (!W||!E) throw new Error("spread-venue-market requires w33-scheduler and evidence");
  const SCHEMA="holotrade.spread-venue-market.v1";
  const catalog=()=>W.spreads();
  const intersection=(a,b)=>a.filter((x)=>new Set(b).has(x));
  function overlap(i,j){ return intersection(catalog()[i],catalog()[j]).length; }
  function neighbors(i,relation=4){ return catalog().map((_,j)=>j).filter((j)=>j!==i&&overlap(i,j)===relation); }

  function bfsDistance(vertices, adjacency, start) {
    const V=new Set(vertices), d=new Map([[start,0]]), q=[start];
    while(q.length){const u=q.shift();for(const v of adjacency(u))if(V.has(v)&&!d.has(v)){d.set(v,d.get(u)+1);q.push(v);}}
    return d;
  }

  function lineFiber(lineId) { return catalog().map((s,i)=>s.includes(lineId)?i:null).filter((x)=>x!==null); }
  function lineFiberCertificate(lineId) {
    const fiber=lineFiber(lineId);
    if(fiber.length!==9) throw new Error(`line ${lineId} lies in ${fiber.length} spreads, expected 9`);
    const oneAdj=(i)=>fiber.filter((j)=>j!==i&&overlap(i,j)===1);
    const fourAdj=(i)=>fiber.filter((j)=>j!==i&&overlap(i,j)===4);
    const seen=new Set(), components=[];
    for(const v of fiber){if(seen.has(v))continue;const st=[v], comp=[];seen.add(v);while(st.length){const u=st.pop();comp.push(u);for(const z of oneAdj(u))if(!seen.has(z)){seen.add(z);st.push(z);}}components.push(comp.sort((a,b)=>a-b));}
    const theorem={
      nineSpreads:fiber.length===9,
      oneLineDegree2:fiber.every((i)=>oneAdj(i).length===2),
      oneLineThreeTriangles:components.length===3&&components.every((c)=>c.length===3&&c.every((u)=>oneAdj(u).filter((v)=>c.includes(v)).length===2)),
      fourLineDegree6:fiber.every((i)=>fourAdj(i).length===6),
      fourLineK333:components.every((c)=>c.every((u)=>fourAdj(u).every((v)=>!c.includes(v))))
    };
    const body={schema:"holotrade.w33-line-spread-fiber.v1",lineId,fiber:Object.freeze(fiber),oneLineTriangles:Object.freeze(components.map(Object.freeze)),theorem,valid:Object.values(theorem).every(Boolean)};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }

  function anchorCertificate(anchor=0) {
    const A=catalog()[anchor]; if(!A)throw new RangeError("invalid anchor spread");
    const near=neighbors(anchor,4), remote=neighbors(anchor,1);
    const remoteAdj=(i)=>remote.filter((j)=>j!==i&&overlap(i,j)===4);
    const distanceProfiles=[];
    for(const r of remote){const d=bfsDistance(remote,remoteAdj,r);const hist={};for(const x of d.values())hist[x]=(hist[x]||0)+1;distanceProfiles.push({r,hist,max:Math.max(...d.values())});}
    const hedges=A.map((lineId)=>{
      const legs=remote.filter((r)=>catalog()[r].includes(lineId));
      const distance=legs.length===2?bfsDistance(remote,remoteAdj,legs[0]).get(legs[1]):null;
      return Object.freeze({lineId,legs:Object.freeze(legs),remoteDistance:distance,legOverlap:legs.length===2?overlap(legs[0],legs[1]):null,
        tripleCommon:legs.length===2?intersection(A,intersection(catalog()[legs[0]],catalog()[legs[1]])):[]});
    });
    const theorem={
      degree15:near.length===15,
      remote20:remote.length===20,
      localKneserDegree6:near.every((i)=>near.filter((j)=>j!==i&&overlap(i,j)===4).length===6),
      remoteJohnsonDegree9:remote.every((i)=>remoteAdj(i).length===9),
      remoteJohnsonDistanceDistribution:distanceProfiles.every((x)=>x.max===3&&x.hist[0]===1&&x.hist[1]===9&&x.hist[2]===9&&x.hist[3]===1),
      tenLineHedges:hedges.length===10,
      exactlyTwoRemoteLegsPerLine:hedges.every((h)=>h.legs.length===2),
      legsAreJohnsonAntipodes:hedges.every((h)=>h.remoteDistance===3),
      pairwiseOnlyAnchorLine:hedges.every((h)=>h.legOverlap===1&&h.tripleCommon.length===1&&h.tripleCommon[0]===h.lineId),
    };
    const body={schema:"holotrade.w33-spread-anchor-hedges.v1",anchorSpread:anchor,anchorLines:Object.freeze([...A]),near:Object.freeze(near),remote:Object.freeze(remote),hedges:Object.freeze(hedges),theorem,valid:Object.values(theorem).every(Boolean),
      interpretation:"Each anchor carrier line owns a two-leg remote redundancy hedge: both legs preserve exactly that line while lying at Johnson distance 3 in the remote shell."};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }

  function globalCertificate(){
    const spreads=catalog();let pairs1=0,pairs4=0;
    for(let i=0;i<spreads.length;i++)for(let j=i+1;j<spreads.length;j++){const n=overlap(i,j);if(n===1)pairs1++;else if(n===4)pairs4++;else throw new Error(`unexpected spread intersection ${n}`);}
    const theorem={spreads36:spreads.length===36,pairsOne360:pairs1===360,pairsFour270:pairs4===270,degree15:spreads.every((_,i)=>neighbors(i,4).length===15),allAnchorHedgesClose:spreads.every((_,i)=>anchorCertificate(i).valid)};
    const body={schema:SCHEMA,pairHistogram:{oneLine:pairs1,fourLines:pairs4},theorem,valid:Object.values(theorem).every(Boolean),graph:"NO_6^-(2)",boundary:"Graph name is inherited from W33-Theory's independent literal identification; this certificate reconstructs the overlap and hedge invariants."};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }

  class SpreadVenueBook {
    constructor(marks={}){this.marks=new Map(Object.entries(marks).map(([k,v])=>[Number(k),Number(v)]));}
    mark(spreadId,price){if(!Number.isInteger(spreadId)||spreadId<0||spreadId>=36)throw new RangeError("invalid spreadId");if(!Number.isFinite(price)||price<0)throw new RangeError("price must be non-negative");this.marks.set(spreadId,price);return this;}
    quoteHedges(anchor){const cert=anchorCertificate(anchor);const anchorPrice=this.marks.get(anchor)??null;return cert.hedges.map((h)=>{const p=h.legs.map((x)=>this.marks.get(x)??null);const complete=p.every(Number.isFinite);return Object.freeze({...h,legPrices:Object.freeze(p),twoLegCost:complete?p[0]+p[1]:null,meanLegPrice:complete?(p[0]+p[1])/2:null,basis:complete&&Number.isFinite(anchorPrice)?(p[0]+p[1])/2-anchorPrice:null});}).sort((a,b)=>(a.twoLegCost??Infinity)-(b.twoLegCost??Infinity)||a.lineId-b.lineId);}
  }
  const API={SCHEMA,overlap,neighbors,lineFiber,lineFiberCertificate,anchorCertificate,globalCertificate,SpreadVenueBook};
  root.HolotradeSpreadVenueMarket=API;
  if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
