// ======================================================================
// HOLOTRADE IMMUTABLE CAPABILITY TRANSITIONS
// Historical transition receipts never mutate. Current admission is a fresh
// evidence decision, so later supersession can refuse future use without
// rewriting the installation event that actually occurred.
// ======================================================================
(function(root){
  "use strict";
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  const C=root.HolotradeCapabilityMarket||(typeof require!=="undefined"?require("./capability-market.js"):null);
  if(!E||!C)throw new Error("capability-transition requires evidence and capability-market");
  const uniq=(xs)=>[...new Set((xs||[]).map(String))].sort();
  function transition(oldProfile,offers,ledger,{evidencePolicy=E.POLICY.VERIFIED,createdAt=0}={}){
    if(!oldProfile?.metadata||oldProfile.metadata.schema!==C.PROFILE_SCHEMA)throw new TypeError("old node capability profile required");
    if(!ledger||typeof ledger.evaluate!=="function")throw new TypeError("EvidenceLedger required");
    const list=(Array.isArray(offers)?offers:[offers]).map(o=>o instanceof C.CapabilityOffer?o:new C.CapabilityOffer(o));
    if(!list.length)throw new TypeError("at least one capability offer required");
    if(list.some(o=>!o.compatible(oldProfile)))throw new Error("capability offer is incompatible with the node profile");
    const evidenceRefs=uniq([...(oldProfile.metadata.evidenceRefs||[]),...list.flatMap(o=>o.evidenceRefs)]),decision=ledger.evaluate(evidenceRefs,{policy:evidencePolicy});
    const oldCaps=oldProfile.metadata.capabilities||[],added=uniq(list.flatMap(o=>o.capabilities).filter(x=>!oldCaps.includes(x))),capabilities=uniq([...oldCaps,...added]);
    let newProfile=null;if(decision.ok)newProfile=C.profileResource({nodeId:oldProfile.metadata.nodeId,hardwareKind:oldProfile.metadata.hardwareKind,capabilities,evidenceRefs,generation:(oldProfile.metadata.generation||0)+1});
    const body={schema:"holotrade.capability-transition.v1",status:decision.ok?"COMMITTED":"REFUSED",nodeId:oldProfile.metadata.nodeId,oldProfileDigest:oldProfile.digest,newProfileDigest:newProfile?.digest||null,offerDigests:list.map(o=>o.digest).sort(),addedCapabilities:added,evidenceRefs,evidencePolicy,evidenceDecisionDigest:decision.digest,createdAt:Number(createdAt)||0,boundary:"Immutable prototype transition receipt. It certifies repository state semantics, not physical installation, licensing, or hardware attestation."};
    return Object.freeze({...body,newProfile,evidenceDecision:decision,digest:E.demoDigest(body)});
  }
  function currentAdmission(receipt,ledger){
    if(!receipt||receipt.schema!=="holotrade.capability-transition.v1")throw new TypeError("transition receipt required");
    if(!ledger||typeof ledger.evaluate!=="function")throw new TypeError("EvidenceLedger required");
    const decision=ledger.evaluate(receipt.evidenceRefs,{policy:receipt.evidencePolicy});const body={schema:"holotrade.capability-transition-admission.v1",transitionDigest:receipt.digest,historicalStatus:receipt.status,currentEvidenceDecisionDigest:decision.digest,admitted:receipt.status==="COMMITTED"&&decision.ok,blockers:decision.blockers};return Object.freeze({...body,evidenceDecision:decision,digest:E.demoDigest(body)});
  }
  const API={transition,currentAdmission};root.HolotradeCapabilityTransition=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
