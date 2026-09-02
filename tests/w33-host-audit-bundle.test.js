"use strict";
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const test=require("node:test");
const Host=require("../js/w33-host-audit-bundle.js");
const Native=require("../js/w33-native-attestation.js");
const Passport=require("../js/w33-passport-deployment.js");

function d(s){return `sha256:${crypto.createHash("sha256").update(s).digest("hex")}`;}
function fixture(){
  const challenge={challengeDigest:d("host-challenge"),runtimePublicKeyDigest:d("host-runtime-key")};
  const p384=crypto.generateKeyPairSync("ec",{namedCurve:"secp384r1"});
  const report=Buffer.alloc(Native.SNP.REPORT_BYTES);
  report.writeUInt32LE(5,0); report.writeUInt32LE(1,0x34); report.writeBigUInt64LE(9n,0x180);
  Buffer.concat([Native.digestBytes(challenge.challengeDigest),Native.digestBytes(challenge.runtimePublicKeyDigest)]).copy(report,0x50);
  const measurement=crypto.createHash("sha384").update("host-launch").digest(); measurement.copy(report,0x90);
  crypto.createHash("sha512").update("host-chip").digest().copy(report,0x1a0);
  const sig=crypto.sign("sha384",report.subarray(0,Native.SNP.SIGNED_BYTES),p384.privateKey);
  Native.derSignatureToSnpRaw(sig).copy(report,Native.SNP.SIGNATURE_OFFSET);
  const native=Native.verifySnpReportNative({report,challenge,expectedMeasurement:measurement,minimumReportedTcb:8n,pinnedVcekPublicKey:p384.publicKey});
  assert.equal(native.ok,true);
  const core={
    schema:"holotrade.w33-execution-passport.v2",deploymentDigest:d("deployment"),machineType:"w33.circuit216.steinberg81",logicalDimension:81,
    capabilityEpoch:0,revocationRoot:d("revocation0"),waitForRoot:d("wait"),cancellationRoot:d("cancel"),asyncScheduleRoot:d("schedule"),gcRegistryRoot:d("gc"),magicBudget:2,
  };
  const passport=Object.freeze({...core,passportId:Passport.sha256(core)});
  const telemetry=Host.normalizeTelemetry({nodeId:"node-81",rapl:{beforeUj:1000000,afterUj:2500000,maxRangeUj:10000000}});
  const artifacts=[{role:"output",bytes:4,digest:d("artifact")}];
  const receiptKeys=crypto.generateKeyPairSync("ed25519");
  const signed=Host.createMeasuredAttestedReplayReceipt({
    receiptSpec:{executionId:"exec-host-1",nodeId:"node-81",outcome:"settled",artifacts,capabilities:{findings:[]},startedAtMs:1,finishedAtMs:2,nonce:"host-nonce",microvmExecuted:true},
    passport,deploymentDigest:passport.deploymentDigest,nativeVerification:native,epochCertificates:[],gcEvolution:[passport.gcRegistryRoot],magicEvents:[],
  },receiptKeys.privateKey,{publicKey:receiptKeys.publicKey,keyId:"host-receipt"},telemetry);
  const hardware={provider:"SEV_SNP",reportBase64:report.toString("base64"),challenge,expectedMeasurement:`sha384:${measurement.toString("hex")}`,minimumReportedTcb:"8",pinnedVcekPublicKeyPem:p384.publicKey.export({type:"spki",format:"pem"})};
  const bundle=Host.buildHostBundle({signedReceipt:signed,passport,epochCertificates:[],authorityPublicKeys:{},gcEvolution:[passport.gcRegistryRoot],magicEvents:[],hardware,telemetry},receiptKeys.publicKey);
  return {bundle,receiptKeys,telemetry};
}

test("host bundle binds physical telemetry into signed receipt and re-verifies raw hardware",()=>{
  const f=fixture(); const v=Host.verifyHostBundle(f.bundle,f.receiptKeys.publicKey);
  assert.equal(v.ok,true); assert.equal(v.code,"PORTABLE_W33_HOST_AUDIT_PASS");
  assert.equal(v.telemetryDigest,f.telemetry.telemetryDigest);
});

test("host bundle rejects telemetry mutation after receipt signing",()=>{
  const f=fixture();
  const bad={...f.bundle,telemetry:{...f.bundle.telemetry,nodeId:"other-node"}};
  const v=Host.verifyHostBundle(bad,f.receiptKeys.publicKey);
  assert.equal(v.ok,false); assert.equal(v.code,"TELEMETRY_CONTENT_DIGEST_INVALID");
});
