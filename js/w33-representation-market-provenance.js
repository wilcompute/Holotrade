"use strict";

// Append-only signed provenance for an exact W33 representation identity.
// Price may change between market events; representation identity may not.

const crypto=require("node:crypto");
const M=require("./w33-representation-market-identity.js");

const EVENT_SCHEMA="holotrade.w33-representation-provenance-event.v1";
const SIGNED_SCHEMA="holotrade.w33-signed-representation-provenance-event.v1";
const HISTORY_SCHEMA="holotrade.w33-representation-provenance-history.v1";
const TYPES=Object.freeze(["BID","AWARD","MIGRATION","SETTLEMENT","REPLAY"]);
const DIGEST_FIELD=Object.freeze({
  BID:"bidDigest",AWARD:"awardDigest",MIGRATION:"representationMigrationMarketDigest",
  SETTLEMENT:"representationSettlementDigest",REPLAY:"representationReplayKeyDigest",
});

function stable(value){
  if(Array.isArray(value))return `[${value.map(stable).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(v){return `sha256:${crypto.createHash("sha256").update(stable(v)).digest("hex")}`;}
function isDigest(v){return typeof v==="string"&&/^sha256:[0-9a-f]{64}$/.test(v);}

function artifactIdentity(type,artifact,identity){
  if(!TYPES.includes(type))throw new RangeError("unknown representation provenance event type");
  if(!artifact||typeof artifact!=="object")throw new TypeError("market lifecycle artifact required");
  if(!identity||identity.schema!==M.IDENTITY_SCHEMA||!isDigest(identity.representationMarketIdentityDigest))throw new TypeError("representation market identity required");
  if(artifact.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest)throw new Error("provenance artifact attempts representation substitution");
  const f=DIGEST_FIELD[type], d=artifact[f];
  if(!isDigest(d))throw new TypeError(`${type} artifact lacks ${f}`);
  return d;
}

function eventBody({sequence,previousSignedEventDigest=null,type,artifact,identity}){
  if(!Number.isSafeInteger(sequence)||sequence<0)throw new RangeError("sequence must be natural");
  if(sequence===0&&previousSignedEventDigest!==null)throw new Error("genesis provenance event may not have a predecessor");
  if(sequence>0&&!isDigest(previousSignedEventDigest))throw new TypeError("non-genesis provenance event requires predecessor digest");
  const artifactDigest=artifactIdentity(type,artifact,identity);
  const body={schema:EVENT_SCHEMA,sequence,previousSignedEventDigest,type,artifactDigest,
    representationMarketIdentityDigest:identity.representationMarketIdentityDigest,
    signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass};
  return Object.freeze({...body,eventDigest:sha256(body)});
}

function signEvent(body,privateKey,keyId){
  if(!body||body.schema!==EVENT_SCHEMA||!isDigest(body.eventDigest))throw new TypeError("provenance event body required");
  const bare={...body};delete bare.eventDigest;if(sha256(bare)!==body.eventDigest)throw new Error("provenance event digest mismatch");
  const signature=crypto.sign(null,Buffer.from(stable(body)),privateKey).toString("base64");
  const signed={schema:SIGNED_SCHEMA,body,keyId:String(keyId),signature};
  return Object.freeze({...signed,signedEventDigest:sha256(signed)});
}

function verifySignedEvent(signed,publicKey){
  if(!signed||signed.schema!==SIGNED_SCHEMA||!signed.body||signed.body.schema!==EVENT_SCHEMA)return Object.freeze({ok:false,code:"PROVENANCE_SCHEMA_INVALID"});
  const bare={...signed.body};delete bare.eventDigest;if(sha256(bare)!==signed.body.eventDigest)return Object.freeze({ok:false,code:"PROVENANCE_EVENT_DIGEST_MISMATCH"});
  const sb={schema:SIGNED_SCHEMA,body:signed.body,keyId:signed.keyId,signature:signed.signature};
  if(sha256(sb)!==signed.signedEventDigest)return Object.freeze({ok:false,code:"PROVENANCE_SIGNED_DIGEST_MISMATCH"});
  if(!crypto.verify(null,Buffer.from(stable(signed.body)),publicKey,Buffer.from(signed.signature,"base64")))return Object.freeze({ok:false,code:"PROVENANCE_SIGNATURE_INVALID"});
  return Object.freeze({ok:true,code:"PROVENANCE_EVENT_VERIFIED",signedEventDigest:signed.signedEventDigest});
}

function append(history,{type,artifact,identity,privateKey,keyId}){
  const events=history==null?[]:[...history.events];
  if(history!=null){
    if(history.schema!==HISTORY_SCHEMA)throw new TypeError("representation provenance history required");
    if(history.representationMarketIdentityDigest!==identity.representationMarketIdentityDigest)throw new Error("history representation identity is immutable");
    if(history.signedResourceSelectionDigest!==identity.selectionDigest)throw new Error("history signed-resource selection is immutable");
  }
  const artifactDigest=artifactIdentity(type,artifact,identity);
  if(events.some(e=>e.body.artifactDigest===artifactDigest))throw new Error("duplicate lifecycle artifact in append-only provenance history");
  const previous=events.length?events.at(-1).signedEventDigest:null;
  const body=eventBody({sequence:events.length,previousSignedEventDigest:previous,type,artifact,identity});
  const signed=signEvent(body,privateKey,keyId); events.push(signed);
  const rootBody={schema:HISTORY_SCHEMA,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,
    signedResourceSelectionDigest:identity.selectionDigest,representationClass:identity.representationClass,eventCount:events.length,lastSignedEventDigest:signed.signedEventDigest};
  return Object.freeze({...rootBody,events:Object.freeze(events),historyDigest:sha256(rootBody)});
}

function verifyHistory(history,publicKeys){
  if(!history||history.schema!==HISTORY_SCHEMA||!Array.isArray(history.events)||!history.events.length)return Object.freeze({ok:false,code:"PROVENANCE_HISTORY_INVALID"});
  let prev=null; const seen=new Set(); let identity=null,selection=null,repClass=null;
  for(let i=0;i<history.events.length;i++){
    const e=history.events[i],key=publicKeys&&publicKeys[e.keyId];if(!key)return Object.freeze({ok:false,code:"PROVENANCE_KEY_UNTRUSTED",sequence:i});
    const v=verifySignedEvent(e,key);if(!v.ok)return Object.freeze({...v,sequence:i});
    const b=e.body;
    if(b.sequence!==i||b.previousSignedEventDigest!==prev)return Object.freeze({ok:false,code:"PROVENANCE_CHAIN_BREAK",sequence:i});
    if(i===0){identity=b.representationMarketIdentityDigest;selection=b.signedResourceSelectionDigest;repClass=b.representationClass;}
    if(b.representationMarketIdentityDigest!==identity||b.signedResourceSelectionDigest!==selection||b.representationClass!==repClass)return Object.freeze({ok:false,code:"PROVENANCE_REPRESENTATION_SUBSTITUTION",sequence:i});
    if(seen.has(b.artifactDigest))return Object.freeze({ok:false,code:"PROVENANCE_DUPLICATE_ARTIFACT",sequence:i});seen.add(b.artifactDigest);prev=e.signedEventDigest;
  }
  if(history.eventCount!==history.events.length||history.lastSignedEventDigest!==prev||history.representationMarketIdentityDigest!==identity||history.signedResourceSelectionDigest!==selection||history.representationClass!==repClass)return Object.freeze({ok:false,code:"PROVENANCE_HISTORY_ROOT_DRIFT"});
  const rb={schema:HISTORY_SCHEMA,representationMarketIdentityDigest:identity,signedResourceSelectionDigest:selection,representationClass:repClass,eventCount:history.eventCount,lastSignedEventDigest:prev};
  if(sha256(rb)!==history.historyDigest)return Object.freeze({ok:false,code:"PROVENANCE_HISTORY_DIGEST_MISMATCH"});
  return Object.freeze({ok:true,code:"REPRESENTATION_PROVENANCE_VERIFIED",eventCount:history.eventCount,historyDigest:history.historyDigest,representationMarketIdentityDigest:identity});
}

module.exports={EVENT_SCHEMA,SIGNED_SCHEMA,HISTORY_SCHEMA,TYPES,DIGEST_FIELD,sha256,artifactIdentity,eventBody,signEvent,verifySignedEvent,append,verifyHistory};
