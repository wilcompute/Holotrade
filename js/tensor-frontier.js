// ======================================================================
// HOLOTRADE DEPTH-2 TENSOR FRONTIER
// Preserves the exact open interval for tau_2 and certifies the tight-size
// necessary eigen equation without promoting an unfinished search.
//
// SUPERSEDED CONSTANT, reconciled across tracks.  This module was written
// against the interval [110, 121], where 121 came from the product
// construction B x B.  analysis/tensor_symmetric_blocker.py then found an
// explicit, verified, minimal 115-leaf blocker, so the interval is now
// [110, 115] and B x B is proved NOT optimal.  The interval is read from
// tensor-sharding rather than hardcoded, so it tracks that result; the
// eigen-equation content below is unaffected and stands as written.
// ======================================================================
(function(root){
  "use strict";
  const S=root.Substrate||(typeof require!=="undefined"?require("./substrate.js"):null);
  const T=root.HolotradeTensorSharding||(typeof require!=="undefined"?require("./tensor-sharding.js"):null);
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  if(!S||!T||!E)throw new Error("tensor-frontier requires substrate, tensor-sharding, evidence");
  function incidenceMatrix(){const N=Array.from({length:40},()=>Array(40).fill(0));for(let l=0;l<40;l++)for(const p of S.LINES[l])N[l][p]=1;return N;}
  function pointAdjacency(){return Array.from({length:40},(_,i)=>Array.from({length:40},(_,j)=>i!==j&&S.isAdjacent(i,j)?1:0));}
  function gramIdentity(){const N=incidenceMatrix(),A=pointAdjacency();let ok=true;for(let i=0;i<40&&ok;i++)for(let j=0;j<40;j++){let x=0;for(let l=0;l<40;l++)x+=N[l][i]*N[l][j];const want=(i===j?4:0)+A[i][j];if(x!==want){ok=false;break;}}return ok;}
  function tightNecessaryConditions(){
    const base=T.depth2Certificate(),lower=base.bounds.lower,upper=base.bounds.upper;
    const theorem={globalLower110:lower===110,constructiveUpper115:upper===115,productUpperWas121:base.bounds.productUpper===121,productConstructionNotOptimal:base.productConstructionOptimal===false,upperStrictlyBeatsProduct:upper<base.bounds.productUpper,exactStillOpen:base.exactTau===null,incidenceGram4IplusA:gramIdentity(),tightLineShadowTotal440:4*110===40*11,tightForcesEveryLineShadow11:(4*110===40*11),eigenEquationConstantCheck:(12+4)*(11/4)===44};
    const body={schema:"holotrade.w33-tensor-tight-frontier.v1",valid:Object.values(theorem).every(Boolean),theorem,interval:[lower,upper],exactTau:null,tightNecessaryEquation:"(A + 4 I) r = 44 * 1",particularSolution:"r = (11/4) * 1",freeLinearSector:"ker(A+4I), the 15-dimensional -4 eigenspace",searchStatus:"OPEN: the upper bound moved 121 -> 115 by symmetry-restricted CP-SAT, but no work has excluded or constructed a size-110 blocker, so the lower end is untouched",deadEnds:Object.freeze(["fibre-size LP/integer relaxation","eigen-coset integrality alone","per-column alpha=7 cap alone","four-colourability alone","full tight-case CP-SAT with both shadow families, independence of every fibre and co-fibre, and the degree identity: UNKNOWN at 1901s and again at 2300s with a sound 360-fold symmetry break"]),supersededBy:"analysis/tensor_symmetric_blocker.py and data/tensor_symmetric_blocker.json -- the 115-leaf witness that replaced 121",boundary:"This certificate proves necessary arithmetic/linear conditions at size 110 and preserves the best constructive upper bound, now 115. It does not claim tau_2=110 or tau_2=115."};return Object.freeze({...body,digest:E.demoDigest(body)});
  }
  const API={incidenceMatrix,pointAdjacency,gramIdentity,tightNecessaryConditions};root.HolotradeTensorFrontier=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
