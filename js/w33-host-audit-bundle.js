"use strict";

const crypto=require("node:crypto");
const Receipt=require("../runtime/receipt.js");
const Flight=require("./w33-attested-replay-receipt.js");
const Portable=require("./w33-portable-audit-verifier.js");
const Measured=require("./w33-measured-placement-loop.js");

function stable(v){
  if(Array.isArray(v)) return `[${v.map(stable).join(",")}]`;
  if(v&&typeof v==="object") return `{${Object.keys(v).sort().map(k=>`${JSON.stringify(k)}:${stable(v[k])}`).join(",")}}`;
  return JSON.stringify(v);
}
function sha256(v){return `sha256:${crypto.createHash("sha256").update(typeof v==="string"?v:stable(v)).digest("hex")}`;}

function normalizeTelemetry({rapl=null,kepler=null,strongRoot=null,nodeId=null,window=null}={}){
  const energy=[];
  if(rapl){
    const row=Measured.raplDeltaJoules(rapl.beforeUj,rapl.afterUj,rapl.maxRangeUj??null);
    energy.push(row);
  }
  if(kepler){
    const row=Measured.keplerDeltaJoules(kepler.beforeText,kepler.afterText,kepler.metric);
    energy.push(row);
  }
  if(!energy.length) throw new Error("at least one physical RAPL or Kepler measurement is required");
  const storage=strongRoot?Measured.strongRootRealization(strongRoot):null;
  const body=Object.freeze({
    schema:"holotrade.w33-host-measured-telemetry.v1",
    nodeId:nodeId==null?null:String(nodeId),
    window:window||null,
    energy:Object.freeze(energy.map(x=>Object.freeze({...x}))),
    storage,
    physicallyMeasured:energy.every(x=>x.physicallyMeasured===true),
  });
  return Object.freeze({...body,telemetryDigest:sha256(body)});
}

function bindTelemetryReceiptSpec(receiptSpec,telemetry){
  if(!receiptSpec||typeof receiptSpec!=="object") throw new TypeError("receiptSpec required");
  if(!telemetry||telemetry.physicallyMeasured!==true||!/^sha256:[0-9a-f]{64}$/.test(telemetry.telemetryDigest||"")) throw new TypeError("physically measured telemetry required");
  return Object.freeze({
    ...receiptSpec,
    metadata:Object.freeze({...(receiptSpec.metadata||{}),w33MeasuredTelemetryDigest:telemetry.telemetryDigest,w33MeasuredTelemetrySchema:telemetry.schema}),
  });
}

function createMeasuredAttestedReplayReceipt(args,privateKey,options={},telemetry){
  const receiptSpec=bindTelemetryReceiptSpec(args.receiptSpec,telemetry);
  return Flight.createAttestedReplayReceipt({...args,receiptSpec},privateKey,options);
}

function signedPayload(envelope,trustedKey){
  const v=Receipt.verifyDeliveryReceipt(envelope,trustedKey);
  if(!v.valid) throw new Error(`delivery receipt invalid: ${v.error||"signature"}`);
  return v.payload;
}

function buildHostBundle({signedReceipt,passport,epochCertificates,authorityPublicKeys,gcEvolution,magicEvents,concurrency=null,context=null,hardware,telemetry},trustedReceiptPublicKey){
  const envelope=signedReceipt&&signedReceipt.envelope?signedReceipt.envelope:signedReceipt;
  if(!envelope) throw new TypeError("signed receipt envelope required");
  const payload=signedPayload(envelope,trustedReceiptPublicKey);
  if(!telemetry||telemetry.physicallyMeasured!==true) throw new Error("physical host telemetry required");
  if(payload.metadata?.w33MeasuredTelemetryDigest!==telemetry.telemetryDigest) throw new Error("signed receipt does not bind this measured telemetry digest");
  return Object.freeze({
    schema:"holotrade.w33-linux-host-portable-bundle.v1",
    envelope,passport,epochCertificates,authorityPublicKeys,gcEvolution,magicEvents,concurrency,context,hardware,telemetry,
  });
}

function verifyHostBundle(bundle,trustedReceiptPublicKey){
  const base=Portable.verifyPortableBundle(bundle,trustedReceiptPublicKey);
  if(!base.ok) return base;
  try{
    const payload=signedPayload(bundle.envelope,trustedReceiptPublicKey);
    const t=bundle.telemetry;
    if(!t||t.schema!=="holotrade.w33-host-measured-telemetry.v1"||t.physicallyMeasured!==true) return Object.freeze({ok:false,code:"PHYSICAL_TELEMETRY_REQUIRED"});
    const {telemetryDigest,...body}=t;
    if(sha256(body)!==telemetryDigest) return Object.freeze({ok:false,code:"TELEMETRY_CONTENT_DIGEST_INVALID"});
    if(payload.metadata?.w33MeasuredTelemetryDigest!==telemetryDigest) return Object.freeze({ok:false,code:"SIGNED_TELEMETRY_BINDING_MISMATCH"});
    return Object.freeze({...base,code:"PORTABLE_W33_HOST_AUDIT_PASS",telemetryDigest,telemetrySources:t.energy.map(x=>x.source)});
  }catch(error){return Object.freeze({ok:false,code:"HOST_BUNDLE_VERIFICATION_ERROR",error:error.message});}
}

module.exports={stable,sha256,normalizeTelemetry,bindTelemetryReceiptSpec,createMeasuredAttestedReplayReceipt,buildHostBundle,verifyHostBundle};
