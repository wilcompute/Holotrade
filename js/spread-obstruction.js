// ======================================================================
// HOLOTRADE W33 SPREAD OBSTRUCTION / EXACT CONFLICT COLORING
//
// Exact finite layer on the 36 W(3,3) spreads.  Two spread venues are
// adjacent when they share four W33 lines.  The resulting graph has the
// SRG parameter set (36,15,6,6), but it is not a Latin-square graph of
// order six: omega=4 and alpha=5.  A certified 8-coloring therefore closes
// chi=8.  Interpreting adjacency as a market/scheduler conflict is a MODEL;
// the graph invariants themselves are exact finite combinatorics.
// ======================================================================
(function(root){
  "use strict";
  const W=root.HolotradeW33Scheduler||(typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const V=root.HolotradeSpreadVenueMarket||(typeof require!=="undefined"?require("./spread-venue-market.js"):null);
  if(!W||!V)throw new Error("spread-obstruction requires w33-scheduler and spread-venue-market");
  // Proper 8-colouring, from analysis/spread_colouring_sat.py.
  //
  // The previous array had the right chromatic number and the right class
  // sizes but was NOT a proper colouring: 29 of its edges were
  // monochromatic, and certificate().valid reported false because of it.
  // SAT confirms chi = 8 (alpha = 5 forces chi >= ceil(36/5) = 8, and 8 is
  // achievable) and that the asserted profile [5,5,5,5,5,5,4,2] is itself
  // achievable, so only the assignment needed replacing -- the theorem and
  // the published class sizes stand unchanged.
  const COLORS=Object.freeze([4,1,5,0,3,7,5,6,2,0,4,1,7,5,1,3,2,0,2,3,5,6,0,2,4,6,1,1,3,0,5,3,4,2,6,4]);
  const CLIQUE4=Object.freeze([26,33,34,35]);
  const COClique5=Object.freeze([0,10,24,32,35]);
  const n=()=>W.spreads().length;
  function adjacency(){const N=n(),a=Array.from({length:N},()=>Array(N).fill(false));for(let i=0;i<N;i++)for(let j=i+1;j<N;j++)if(V.overlap(i,j)===4)a[i][j]=a[j][i]=true;return a;}
  function masks(a,complement=false){const N=a.length,full=(1n<<BigInt(N))-1n;return a.map((row,i)=>{let m=0n;for(let j=0;j<N;j++)if(j!==i&&(complement?!row[j]:row[j]))m|=1n<<BigInt(j);return m&full;});}
  function popcount(x){let c=0;while(x){x&=x-1n;c++;}return c;}
  function bitIndex(bit){let i=0;while(bit>1n){bit>>=1n;i++;}return i;}
  function hasCliqueAtLeast(ms,target){const full=(1n<<BigInt(ms.length))-1n;let witness=null;function go(P,chosen){if(witness)return;if(chosen.length>=target){witness=chosen.slice();return;}if(chosen.length+popcount(P)<target)return;while(P&&!witness){if(chosen.length+popcount(P)<target)return;const bit=P&-P;P^=bit;const v=bitIndex(bit);go(P&ms[v],chosen.concat(v));}}go(full,[]);return witness;}
  function validClique(a,vs,edge=true){return vs.every((u,i)=>vs.slice(i+1).every(v=>edge?a[u][v]:!a[u][v]));}
  function colorClasses(){const out=Array.from({length:8},()=>[]);COLORS.forEach((c,v)=>out[c].push(v));return out.map(Object.freeze);}
  function certificate(){
    const a=adjacency(),N=a.length,deg=a.map(r=>r.filter(Boolean).length),cls=colorClasses();
    const noK5=!hasCliqueAtLeast(masks(a),5),noIndependent6=!hasCliqueAtLeast(masks(a,true),6);
    const colorValid=COLORS.length===N&&cls.every(c=>validClique(a,c,false));
    const theorem={spreads36:N===36,degree15:deg.every(d=>d===15),clique4Witness:validClique(a,CLIQUE4,true),noClique5:noK5,coclique5Witness:validClique(a,COClique5,false),noIndependent6,colorValid,eightColors:cls.length===8,lowerBound8:noIndependent6&&Math.ceil(N/5)===8};
    return Object.freeze({schema:"holotrade.w33-spread-obstruction.v1",theorem,valid:Object.values(theorem).every(Boolean),omega:4,alpha:5,chromaticNumber:8,coloring:[...COLORS],colorClassSizes:cls.map(c=>c.length),batches:cls,latinSquareGraphOrder6:false,reason:"A Latin-square graph of order 6 contains K6 row/column/symbol cliques; this graph has exact clique number 4.",evidenceBoundary:"Graph invariants and coloring certificate are exact. Treating four-line overlap as a scheduling conflict is a HoloTrade model, not a physical-network measurement."});
  }
  const API={COLORS,CLIQUE4,COClique5,adjacency,colorClasses,certificate,conflictFreeBatches:colorClasses};
  root.HolotradeSpreadObstruction=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
