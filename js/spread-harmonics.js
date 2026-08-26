// ======================================================================
// HOLOTRADE W33 SPREAD HARMONICS
//
// Exact integer linear algebra for the 36-spread four-line-overlap graph.
// For A=srg(36,15,6,6), A^2=9I+6J.  Its Seidel matrix
// S=J-I-2A satisfies S^2+2S-35I=0.  This yields complementary rank
// 15/21 projectors and, after splitting the constants, an exact
// 1+15+20 harmonic decomposition.  H15/5 is the Gram matrix of a
// 36-vector equiangular tight frame in R^15 with coherence 1/5.
// ======================================================================
(function(root){
  "use strict";
  const W=root.HolotradeW33Scheduler||(typeof require!=="undefined"?require("./w33-scheduler.js"):null);
  const V=root.HolotradeSpreadVenueMarket||(typeof require!=="undefined"?require("./spread-venue-market.js"):null);
  if(!W||!V)throw new Error("spread-harmonics requires w33-scheduler and spread-venue-market");
  const N=36;
  const mat=(f)=>Array.from({length:N},(_,i)=>Array.from({length:N},(_,j)=>f(i,j)));
  const I=()=>mat((i,j)=>i===j?1:0),J=()=>mat(()=>1);
  const add=(A,B)=>A.map((r,i)=>r.map((x,j)=>x+B[i][j]));
  const sub=(A,B)=>A.map((r,i)=>r.map((x,j)=>x-B[i][j]));
  const scale=(A,c)=>A.map(r=>r.map(x=>x*c));
  function mul(A,B){const C=mat(()=>0);for(let i=0;i<N;i++)for(let k=0;k<N;k++){const x=A[i][k];if(!x)continue;for(let j=0;j<N;j++)C[i][j]+=x*B[k][j];}return C;}
  const equal=(A,B)=>A.every((r,i)=>r.every((x,j)=>x===B[i][j]));
  const zero=(A)=>A.every(r=>r.every(x=>x===0));
  const trace=(A)=>A.reduce((s,r,i)=>s+r[i],0);
  function adjacency(){return mat((i,j)=>i!==j&&V.overlap(i,j)===4?1:0);}
  function matrices(){const a=adjacency(),i=I(),j=J(),s=sub(sub(j,i),scale(a,2)),h15=sub(scale(i,5),s),h21=add(scale(i,7),s);return{A:a,I:i,J:j,S:s,H15:h15,H21:h21};}
  function certificate(){
    const m=matrices(),{A,I:Id,J:Ones,S,H15,H21}=m;
    const A2=mul(A,A),srg=add(scale(Id,9),scale(Ones,6));
    const seidelPoly=add(add(mul(S,S),scale(S,2)),scale(Id,-35));
    const N1=Ones,N15=scale(H15,3),N20=sub(scale(H21,3),Ones); // projectors /36
    const theorem={
      srgIdentity:equal(A2,srg),seidelQuadratic:zero(seidelPoly),
      h15ScaledProjector:equal(mul(H15,H15),scale(H15,12)),
      h21ScaledProjector:equal(mul(H21,H21),scale(H21,12)),
      complementary:zero(mul(H15,H21))&&equal(add(H15,H21),scale(Id,12)),
      p1Projector:equal(mul(N1,N1),scale(N1,36)),
      p15Projector:equal(mul(N15,N15),scale(N15,36)),
      p20Projector:equal(mul(N20,N20),scale(N20,36)),
      pairwiseOrthogonal:zero(mul(N1,N15))&&zero(mul(N1,N20))&&zero(mul(N15,N20)),
      resolutionOfIdentity:equal(add(add(N1,N15),N20),scale(Id,36)),
      ranks:trace(N1)/36===1&&trace(N15)/36===15&&trace(N20)/36===20,
      etfDiagonal:H15.every((r,i)=>r[i]===5),
      etfEquiangular:H15.every((r,i)=>r.every((x,j)=>i===j||Math.abs(x)===1)),
      etfTight:equal(mul(H15,H15),scale(H15,12))
    };
    return Object.freeze({schema:"holotrade.w33-spread-harmonics.v1",valid:Object.values(theorem).every(Boolean),theorem,ranks:{constant:1,harmonic15:15,harmonic20:20},projectorDenominator:36,projectorNumerators:{constant:N1,harmonic15:N15,harmonic20:N20},etf:{vectors:36,dimension:15,gramNumerator:H15,gramDenominator:5,coherence:{numerator:1,denominator:5},frameBound:{numerator:12,denominator:5}},evidenceBoundary:"All identities are exact integer matrix equalities on the reconstructed W33 spread graph; no physical mode, energy, or quantum-state interpretation is asserted."});
  }
  const API={adjacency,matrices,certificate};root.HolotradeSpreadHarmonics=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
