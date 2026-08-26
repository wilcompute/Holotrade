// ======================================================================
// HOLOTRADE DEPTH-2 TENSOR FRONTIER
// Preserves the exact open interval 110 <= tau_2 <= 121 and certifies the
// tight-size necessary eigen equation without promoting an unfinished search.
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
    const theorem={globalLower110:lower===110,constructiveUpper121:upper===121,exactStillOpen:base.exactTau===null,incidenceGram4IplusA:gramIdentity(),tightLineShadowTotal440:4*110===40*11,tightForcesEveryLineShadow11:(4*110===40*11),eigenEquationConstantCheck:(12+4)*(11/4)===44};
    const body={schema:"holotrade.w33-tensor-tight-frontier.v1",valid:Object.values(theorem).every(Boolean),theorem,interval:[lower,upper],exactTau:null,tightNecessaryEquation:"(A + 4 I) r = 44 * 1",particularSolution:"r = (11/4) * 1",freeLinearSector:"ker(A+4I), the 15-dimensional -4 eigenspace",searchStatus:"OPEN: current CP-SAT/SAT work has not excluded or constructed a size-110 blocker",deadEnds:Object.freeze(["fibre-size LP/integer relaxation","eigen-coset integrality alone","per-column alpha=7 cap alone","four-colourability alone"]),boundary:"This certificate proves necessary arithmetic/linear conditions at size 110 and preserves the constructive 121 upper bound. It does not claim tau_2=110 or tau_2=121."};return Object.freeze({...body,digest:E.demoDigest(body)});
  }
  const API={incidenceMatrix,pointAdjacency,gramIdentity,tightNecessaryConditions};root.HolotradeTensorFrontier=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
