// ======================================================================
// HOLOTRADE FINITE POLICY GLUING
// A conservative finite compatibility analogue: values agree on overlaps,
// authority narrows by intersection, obligations accumulate by union, and
// the strongest evidence floor wins. This is not a general sheaf theorem.
// ======================================================================
(function(root){
  "use strict";
  const G=root.HolotradeGluing||(typeof require!=="undefined"?require("./gluing.js"):null);
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  if(!G||!E)throw new Error("policy-gluing requires gluing and evidence");
  const ORDER=Object.freeze([E.POLICY.DEMO,E.POLICY.RESEARCH,E.POLICY.VERIFIED,E.POLICY.RUNTIME_ATTESTED]);
  const unique=(xs)=>[...new Set(xs.map(String))].sort();
  function normalize(spec,i){
    if(!spec||typeof spec!=="object")throw new TypeError("policy section required");
    const authorities=unique(spec.authorities||[]);if(!authorities.length)throw new Error("each policy section must name at least one authority");
    const obligations=unique(spec.obligations||[]),evidencePolicy=spec.evidencePolicy||E.POLICY.DEMO;if(!ORDER.includes(evidencePolicy))throw new RangeError("unsupported evidence policy");
    return Object.freeze({id:String(spec.id||`policy-${i}`),values:spec.values||{},authorities,obligations,evidencePolicy,evidenceRefs:unique(spec.evidenceRefs||[])});
  }
  function gluePolicy(specs,{requiredPaths=[]}={}){
    if(!Array.isArray(specs)||!specs.length)throw new TypeError("at least one policy section required");
    const sections=specs.map(normalize),structural=G.glue(sections.map(s=>({id:s.id,kind:"policy",values:s.values,evidenceRefs:s.evidenceRefs})),{requiredPaths});
    let authorities=[...sections[0].authorities];for(const s of sections.slice(1)){const allowed=new Set(s.authorities);authorities=authorities.filter(x=>allowed.has(x));}
    authorities=unique(authorities);const obligations=unique(sections.flatMap(s=>s.obligations));const evidencePolicy=sections.reduce((best,s)=>ORDER.indexOf(s.evidencePolicy)>ORDER.indexOf(best)?s.evidencePolicy:best,E.POLICY.DEMO);
    const authorityConflict=authorities.length===0;const conflicts=[...structural.conflicts];if(authorityConflict)conflicts.push({code:"EMPTY_AUTHORITY_INTERSECTION",sections:sections.map(s=>s.id),authoritySets:sections.map(s=>s.authorities)});
    const ok=structural.ok&&!authorityConflict;
    const body={schema:"holotrade.finite-policy-gluing.v1",ok,unique:ok,structuralDigest:structural.digest,globalValues:ok?structural.globalSection:null,authorities,obligations,evidencePolicy,evidenceRefs:unique(sections.flatMap(s=>s.evidenceRefs)),missing:structural.missing,conflicts,boundary:"Finite compatibility/gluing policy kernel only; authority intersection and evidence ordering are explicit HoloTrade policy choices, not a mathematical sheaf theorem."};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }
  function admitPolicy(specs,ledger,options={}){const glued=gluePolicy(specs,options);if(!ledger||typeof ledger.evaluate!=="function")throw new TypeError("EvidenceLedger required");const decision=ledger.evaluate(glued.evidenceRefs,{policy:glued.evidencePolicy});const body={schema:"holotrade.finite-policy-gluing-admission.v1",gluingDigest:glued.digest,structuralOk:glued.ok,evidenceDecisionDigest:decision.digest,evidenceOk:decision.ok,ok:glued.ok&&decision.ok,blockers:[...glued.conflicts,...glued.missing.map(path=>({code:"MISSING_REQUIRED_PATH",path})),...decision.blockers]};return Object.freeze({...body,glued,evidenceDecision:decision,digest:E.demoDigest(body)});}
  const API={ORDER,gluePolicy,admitPolicy};root.HolotradePolicyGluing=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
