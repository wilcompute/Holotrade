"use strict";

// Price-independent market identity for a verified W33 signed representation.
// The identity commits *which representation class was authorized*, while price
// digests and telemetry epochs remain separate mutable market coordinates.

const crypto=require("node:crypto");
const P=require("./w33-signed-resource-policy.js");

const IDENTITY_SCHEMA="holotrade.w33-representation-market-identity.v1";
const BID_SCHEMA="holotrade.w33-representation-bid.v1";
const AWARD_SCHEMA="holotrade.w33-representation-award.v1";
const ATTESTED_SCHEMA="holotrade.w33-representation-attestation-market-binding.v1";
const MIGRATION_SCHEMA="holotrade.w33-representation-migration-market-binding.v1";
const SETTLEMENT_SCHEMA="holotrade.w33-representation-settlement.v1";
const REPLAY_SCHEMA="holotrade.w33-representation-replay-key.v1";

function stable(value){
  if(Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if(value&&typeof value==="object") return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value){return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;}
function isDigest(v){return typeof v==="string"&&/^sha256:[0-9a-f]{64}$/.test(v);}
function finiteNonnegative(v,name){const n=Number(v);if(!Number.isFinite(n)||n<0)throw new RangeError(`${name} must be finite nonnegative`);return n;}

function identityFromSelection(selection){
  if(!selection||selection.schema!==P.RESOURCE_SCHEMA) throw new TypeError("verified W33 signed-resource selection required");
  if(!isDigest(selection.selectionDigest)||!isDigest(selection.certificateDigest)) throw new TypeError("selection/certificate digest required");
  const body={schema:IDENTITY_SCHEMA,certificateDigest:selection.certificateDigest,selectionDigest:selection.selectionDigest,
    representationClass:String(selection.representationClass),depth:selection.depth,
    representationAmplification:String(selection.representationAmplification),signedSamplingSecondMomentFactor:String(selection.signedSamplingSecondMomentFactor)};
  return Object.freeze({...body,representationMarketIdentityDigest:sha256(body)});
}

function assertSelectionIdentity(selection,identity){
  const expected=identityFromSelection(selection);
  if(!identity||identity.schema!==IDENTITY_SCHEMA||identity.representationMarketIdentityDigest!==expected.representationMarketIdentityDigest) throw new Error("representation market identity disagrees with verified selection");
  return expected;
}

function buildBid({workerId,identity,priceDigest,totalUSD,pricingEpoch=0}){
  if(!identity||identity.schema!==IDENTITY_SCHEMA||!isDigest(identity.representationMarketIdentityDigest)) throw new TypeError("representation market identity required");
  if(!isDigest(priceDigest)) throw new TypeError("priceDigest required");
  if(!Number.isSafeInteger(pricingEpoch)||pricingEpoch<0) throw new RangeError("pricingEpoch must be a natural number");
  const body={schema:BID_SCHEMA,workerId:String(workerId),representationMarketIdentityDigest:identity.representationMarketIdentityDigest,
    signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass,priceDigest,totalUSD:finiteNonnegative(totalUSD,"totalUSD"),pricingEpoch};
  return Object.freeze({...body,bidDigest:sha256(body)});
}

function verifyBid(bid,identity){
  if(!bid||bid.schema!==BID_SCHEMA) throw new TypeError("representation bid required");
  const bare={...bid};delete bare.bidDigest;
  if(sha256(bare)!==bid.bidDigest) throw new Error("representation bid digest mismatch");
  if(bid.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||bid.signedResourceSelectionDigest!==identity.selectionDigest||bid.representationClass!==identity.representationClass) throw new Error("representation bid attempts class substitution");
  finiteNonnegative(bid.totalUSD,"totalUSD");
  return bid;
}

function selectBid(bids,identity){
  const eligible=[]; const rejected=[];
  for(const b of bids||[]){
    try{eligible.push(verifyBid(b,identity));}catch(e){rejected.push(Object.freeze({workerId:b&&b.workerId||null,code:"REPRESENTATION_IDENTITY_MISMATCH",reason:String(e.message)}));}
  }
  eligible.sort((a,b)=>a.totalUSD-b.totalUSD||a.workerId.localeCompare(b.workerId));
  if(!eligible.length) return Object.freeze({ok:false,code:"NO_BID_FOR_EXACT_REPRESENTATION_IDENTITY",rejected:Object.freeze(rejected)});
  const winner=eligible[0];
  const body={schema:AWARD_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,bidDigest:winner.bidDigest,
    workerId:winner.workerId,signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass,priceDigest:winner.priceDigest,totalUSD:winner.totalUSD};
  return Object.freeze({ok:true,code:"EXACT_REPRESENTATION_BID_SELECTED",award:Object.freeze({...body,awardDigest:sha256(body)}),rejected:Object.freeze(rejected)});
}

function bindDispatchAttestation(dispatch,identity){
  if(!dispatch||!dispatch.challenge) throw new TypeError("continuation dispatch with challenge required");
  if(dispatch.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest) throw new Error("dispatch representation market identity drift");
  if(dispatch.signedResourceSelectionDigest!==identity.selectionDigest||dispatch.representationClass!==identity.representationClass) throw new Error("dispatch signed-resource identity drift");
  if(dispatch.challenge.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||dispatch.challenge.signedResourceSelectionDigest!==identity.selectionDigest) throw new Error("hardware challenge did not bind exact representation market identity");
  const body={schema:ATTESTED_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,dispatchDigest:dispatch.dispatchDigest,
    attestationChallengeDigest:dispatch.attestationChallengeDigest,workerId:dispatch.workerId,signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass};
  return Object.freeze({...body,representationAttestationMarketDigest:sha256(body)});
}

function bindMigration(migration,identity){
  if(!migration||!migration.dispatch) throw new TypeError("worker migration with next dispatch required");
  if(migration.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||migration.dispatch.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest) throw new Error("migration representation market identity drift");
  if(migration.signedResourceSelectionDigest!==identity.selectionDigest||migration.representationClass!==identity.representationClass) throw new Error("migration representation selection drift");
  const body={schema:MIGRATION_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,migrationDigest:migration.migrationDigest,
    fromWorkerId:migration.fromWorkerId,toWorkerId:migration.toWorkerId,oldChallengeDigest:migration.oldChallengeDigest,newChallengeDigest:migration.newChallengeDigest,
    signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass};
  return Object.freeze({...body,representationMigrationMarketDigest:sha256(body)});
}

function settleVerifiedDynamicResult(result,identity){
  if(!result||!result.dispatch||!result.delivery||!result.dynamicResource||!result.dynamicResource.delivery) throw new TypeError("verified dynamic-resource transaction result required");
  const db=result.delivery.body, dyn=result.dynamicResource.delivery.body;
  if(result.dispatch.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||db.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||dyn.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest) throw new Error("settlement representation market identity drift");
  if(result.dispatch.signedResourceSelectionDigest!==identity.selectionDigest||db.signedResourceSelectionDigest!==identity.selectionDigest) throw new Error("settlement signed-resource selection drift");
  const body={schema:SETTLEMENT_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,signedResourceSelectionDigest:identity.selectionDigest,
    representationClass:identity.representationClass,workerId:result.dispatch.workerId,continuationRoot:result.dispatch.continuationRoot,processId:result.dispatch.processId,generation:result.dispatch.generation,
    signedResourcePriceDigest:result.dispatch.signedResourcePriceDigest,dynamicDeliveryDigest:dyn.dynamicDeliveryDigest,baseDeliveryDigest:db.deliveryDigest,
    quotedSettlementUSD:finiteNonnegative(result.dispatch.price.totalUSD,"quotedSettlementUSD")};
  return Object.freeze({...body,representationSettlementDigest:sha256(body)});
}

function replayKey(settlement,identity){
  if(!settlement||settlement.schema!==SETTLEMENT_SCHEMA||!isDigest(settlement.representationSettlementDigest)) throw new TypeError("representation settlement required");
  if(settlement.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest||settlement.signedResourceSelectionDigest!==identity.selectionDigest||settlement.representationClass!==identity.representationClass) throw new Error("replay under a substituted representation is forbidden");
  const bare={...settlement};delete bare.representationSettlementDigest;if(sha256(bare)!==settlement.representationSettlementDigest) throw new Error("settlement digest mismatch");
  const body={schema:REPLAY_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,representationSettlementDigest:settlement.representationSettlementDigest,
    continuationRoot:settlement.continuationRoot,processId:settlement.processId,generation:settlement.generation,representationClass:identity.representationClass};
  return Object.freeze({...body,representationReplayKeyDigest:sha256(body)});
}

module.exports={IDENTITY_SCHEMA,BID_SCHEMA,AWARD_SCHEMA,ATTESTED_SCHEMA,MIGRATION_SCHEMA,SETTLEMENT_SCHEMA,REPLAY_SCHEMA,sha256,identityFromSelection,assertSelectionIdentity,buildBid,verifyBid,selectBid,bindDispatchAttestation,bindMigration,settleVerifiedDynamicResult,replayKey};
