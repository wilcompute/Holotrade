// ======================================================================
// HOLOTRADE RISK-ADJUSTED CAPABILITY BUNDLE OPTIMIZER
//
// Extends the exact capability set-cover market with an explicit modeled
// objective: acquisition price + current evidence penalty + W33 locality hops
// + declared correction risk.  The coverage constraint remains exact; the
// scalar weights are policy inputs, not mathematical constants.
// ======================================================================
(function(root){
  "use strict";
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  const Cap=root.HolotradeCapabilityMarket||(typeof require!=="undefined"?require("./capability-market.js"):null);
  const S=root.Substrate||(typeof require!=="undefined"?require("./substrate.js"):null);
  if(!E||!Cap||!S)throw new Error("capability-risk requires evidence, capability-market, substrate");
  const SCHEMA="holotrade.capability-risk-bundle.v1";
  const CLASS_PENALTY=Object.freeze({
    [E.EVIDENCE_CLASS.RUNTIME_ATTESTATION]:0,
    [E.EVIDENCE_CLASS.FORMAL_WITNESS]:0.05,
    [E.EVIDENCE_CLASS.EXTERNAL_VERIFIED]:0.08,
    [E.EVIDENCE_CLASS.REPO_CERTIFICATE]:0.12,
    [E.EVIDENCE_CLASS.SOURCE_DOCUMENT]:0.20,
    [E.EVIDENCE_CLASS.MODEL_RESULT]:0.30,
    [E.EVIDENCE_CLASS.OPERATOR_ASSERTION]:0.60,
  });
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  function offerRisk(profile,offer,ledger,{requireEvidence=true}={}){
    const refs=[...(offer.evidenceRefs||[])];
    const decision=ledger?ledger.evaluate(refs,{policy:E.POLICY.VERIFIED}):null;
    const evidenceMissing=refs.length===0;
    const eligible=(!requireEvidence||!evidenceMissing)&&(!decision||decision.ok);
    const evidencePenalty=evidenceMissing?1:(decision?.resolved||[]).reduce((s,r)=>s+(CLASS_PENALTY[r.evidenceClass]??0.75),0)/Math.max(1,(decision?.resolved||[]).length);
    const correctionRisk=clamp(Number(offer.metadata?.correctionRisk??0),0,1);
    const resource=offer.asResource();
    const localityHops=S.route(profile.address.point,resource.address.point).distance;
    return Object.freeze({offer,eligible,evidenceMissing,evidenceDecision:decision,evidencePenalty,correctionRisk,localityHops,price:offer.price});
  }
  function better(a,b){if(!b)return true;if(a.score!==b.score)return a.score<b.score;if(a.price!==b.price)return a.price<b.price;if(a.ids.length!==b.ids.length)return a.ids.length<b.ids.length;return a.ids.join("|").localeCompare(b.ids.join("|"))<0;}
  function bestRiskAdjustedBundle(exchange,profile,requiredCapabilities,{ledger=null,weights={},requireEvidence=true}={}){
    if(!(exchange instanceof Cap.CapabilityExchange))throw new TypeError("CapabilityExchange required");
    const W={price:Number(weights.price??1),evidence:Number(weights.evidence??1),locality:Number(weights.locality??0.25),correction:Number(weights.correction??2)};
    if(Object.values(W).some((x)=>!Number.isFinite(x)||x<0))throw new RangeError("weights must be finite non-negative numbers");
    const required=[...new Set((requiredCapabilities||[]).map(String))].sort(), have=new Set(profile.metadata?.capabilities||[]), missing=required.filter((x)=>!have.has(x));
    if(missing.length===0)return Object.freeze({schema:SCHEMA,complete:true,offers:[],offerIds:[],required,missing:[],score:0,totalPrice:0,weights:W});
    if(missing.length>24)throw new RangeError("optimizer supports at most 24 missing capabilities");
    const idx=new Map(missing.map((c,i)=>[c,i])),full=(1<<missing.length)-1;
    const rows=exchange.offers.filter((o)=>o.compatible(profile)).map((offer)=>{
      let mask=0;for(const c of offer.capabilities)if(idx.has(c))mask|=1<<idx.get(c);
      const risk=offerRisk(profile,offer,ledger,{requireEvidence});
      const score=W.price*risk.price+W.evidence*risk.evidencePenalty+W.locality*risk.localityHops+W.correction*risk.correctionRisk;
      return {offer,mask,risk,score};
    }).filter((r)=>r.mask!==0&&r.risk.eligible);
    const best=new Map([[0,{score:0,price:0,ids:[],rows:[]}]]);
    for(const row of rows){for(const [mask,state] of [...best.entries()]){if(state.ids.includes(row.offer.id))continue;const nm=mask|row.mask;const cand={score:state.score+row.score,price:state.price+row.offer.price,ids:[...state.ids,row.offer.id].sort(),rows:[...state.rows,row]};if(better(cand,best.get(nm)))best.set(nm,cand);}}
    const win=best.get(full);if(!win)return Object.freeze({schema:SCHEMA,complete:false,offers:[],offerIds:[],required,missing,score:null,totalPrice:null,weights:W});
    const ordered=[...win.rows].sort((a,b)=>a.offer.id.localeCompare(b.offer.id));
    const breakdown={price:ordered.reduce((s,r)=>s+r.risk.price,0),evidencePenalty:ordered.reduce((s,r)=>s+r.risk.evidencePenalty,0),localityHops:ordered.reduce((s,r)=>s+r.risk.localityHops,0),correctionRisk:ordered.reduce((s,r)=>s+r.risk.correctionRisk,0)};
    const body={schema:SCHEMA,complete:true,offers:Object.freeze(ordered.map((r)=>r.offer)),offerIds:Object.freeze(ordered.map((r)=>r.offer.id)),required:Object.freeze(required),missing:Object.freeze(missing),score:win.score,totalPrice:win.price,weights:Object.freeze(W),breakdown:Object.freeze(breakdown),offerRisk:Object.freeze(ordered.map((r)=>Object.freeze({id:r.offer.id,evidencePenalty:r.risk.evidencePenalty,localityHops:r.risk.localityHops,correctionRisk:r.risk.correctionRisk,evidenceDecisionDigest:r.risk.evidenceDecision?.digest||null}))),boundary:"Coverage is exact. Risk weights, evidence-class penalties, correctionRisk metadata, and their scalarization are explicit market policy inputs, not empirical failure probabilities."};
    return Object.freeze({...body,digest:E.demoDigest(body)});
  }
  const API={SCHEMA,CLASS_PENALTY,offerRisk,bestRiskAdjustedBundle};root.HolotradeCapabilityRisk=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
