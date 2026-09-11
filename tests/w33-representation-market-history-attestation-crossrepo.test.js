"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");

const A=require("../js/w33-measured-boot-attestation.js");
const D=require("../js/w33-passport-deployment.js");
const P=require("../js/w33-signed-resource-policy.js");
const I=require("../js/w33-representation-market-identity.js");
const H=require("../js/w33-representation-market-provenance.js");
const MMR=require("../js/w33-representation-market-merkle-provenance.js");
const Telemetry=require("../js/w33-signed-resource-telemetry.js");
const S=require("../scheduler/w33-continuation-scheduler.js");
const Q=require("../scheduler/w33-continuation-transaction.js");
const R=require("../scheduler/w33-dynamic-resource-transaction.js");

function d(label){return S.sha256(label);}
function prices(overrides={}){return Object.freeze({semanticGuestStepUSD:0,w33RouteHopUSD:0,authenticatedRetainedByteTickUSD:0,
  authenticatedSweptPayloadByteUSD:0,deterministicReplayStepUSD:0,representationExcessUSD:3,samplingExcessUSD:5,...overrides});}
function verdict(challenge,key){return A.signVerifierVerdict({provider:A.PROVIDER.SEV_SNP,challengeDigest:challenge.challengeDigest,
  launchMeasurement:d("history-launch"),reportedTcbDigest:d("history-tcb"),signerChainDigest:d("history-chain"),hardwareBacked:true,
  vendorSignatureVerified:true,measurementPolicyVerified:true,tcbPolicyVerified:true,runtimeKeyBound:true,verifierKeyId:"history-verifier"},key);}

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if(!certPath){test("W33 economics certificate supplied by cross-repo CI",{skip:true},()=>{});}else{
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const selection=P.verifySignedResourceCertificate(cert,"exception-depth3-mass24");
  const identity=I.identityFromSelection(selection);
  const marketKeys=crypto.generateKeyPairSync("ed25519");
  const bid1=I.buildBid({workerId:"history-worker",identity,priceDigest:d("history-price-1"),totalUSD:4,pricingEpoch:1});
  const bid2=I.buildBid({workerId:"history-worker",identity,priceDigest:d("history-price-2"),totalUSD:3,pricingEpoch:2});
  let h1=H.append(null,{type:"BID",artifact:bid1,identity,privateKey:marketKeys.privateKey,keyId:"market"});
  let h2=H.append(h1,{type:"BID",artifact:bid2,identity,privateKey:marketKeys.privateKey,keyId:"market"});
  const c1=MMR.commitHistory(h1),c2=MMR.commitHistory(h2);

  const deploymentDigest=d("history-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("history-passport"),deploymentDigest,machineType:"w33.circuit216.steinberg81",
    logicalDimension:81,capabilityEpoch:1,revocationRoot:d("history-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const root=d("history-root"),processId=d("history-process");
  const baseRequest=Object.freeze({continuationRoot:root,processId,generation:12,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass:"exception-depth3-mass24"});
  const request1=Object.freeze({...baseRequest,representationMarketHistoryCommitment:c1});
  const request2=Object.freeze({...baseRequest,representationMarketHistoryCommitment:c2});
  const candidate=(id,tag,extra={})=>Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d(`${tag}-runtime`),
    topology:Object.freeze({attested:true,attestationDigest:d(`${tag}-topology`),points:[0,1,2]}),retainedUnionDeltaBytes:{[root]:0},
    computePerSecondUSD:0,startupUSD:0,signedResourceUnitPrices:prices(),...extra});

  test("verified MMR root becomes measured-boot execution context",()=>{
    assert.equal(MMR.verifyCommitment(c1).ok,true);
    const n1=S.normalizeRequest(request1),n2=S.normalizeRequest(request2);
    assert.equal(n1.representationMarketHistoryRootDigest,c1.rootDigest);
    assert.equal(n1.representationMarketHistoryEventCount,1);
    assert.equal(n2.representationMarketHistoryRootDigest,c2.rootDigest);
    assert.notEqual(c1.rootDigest,c2.rootDigest);
    const a=S.dispatchFor(candidate("w","a"),n1),b=S.dispatchFor(candidate("w","a"),n2);
    assert.equal(a.challenge.representationMarketHistoryRootDigest,c1.rootDigest);
    assert.equal(b.challenge.representationMarketHistoryRootDigest,c2.rootDigest);
    assert.notEqual(a.attestationChallengeDigest,b.attestationChallengeDigest);
  });

  test("tampered or representation-substituted MMR commitment fails closed",()=>{
    const tampered={...c1,peaks:c1.peaks.map((p,i)=>i? p:{...p,hash:d("tampered-peak")})};
    assert.equal(MMR.verifyCommitment(tampered).ok,false);
    assert.throws(()=>S.normalizeRequest({...baseRequest,representationMarketHistoryCommitment:tampered}),/invalid representation market history commitment/);
    const depth2=P.verifySignedResourceCertificate(cert,"exception-depth2"),id2=I.identityFromSelection(depth2);
    const wrongBid=I.buildBid({workerId:"wrong",identity:id2,priceDigest:d("wrong-price"),totalUSD:1,pricingEpoch:1});
    const wrongHistory=H.append(null,{type:"BID",artifact:wrongBid,identity:id2,privateKey:marketKeys.privateKey,keyId:"market"});
    const wrongCommit=MMR.commitHistory(wrongHistory);
    assert.throws(()=>S.normalizeRequest({...baseRequest,representationMarketHistoryCommitment:wrongCommit}),/commitment disagrees/);
  });

  test("old attestation verdict cannot replay after valid history extension and migration cannot mutate root",()=>{
    const verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519");
    const c=candidate("w","replay");
    const oldDispatch=S.dispatchFor(c,S.normalizeRequest(request1));
    const oldVerdict=verdict(oldDispatch.challenge,verifier.privateKey);
    assert.throws(()=>Q.executeContinuationTransaction({candidates:[c],request:request2,signedVerifierVerdict:oldVerdict,trustedVerifierPublicKey:verifier.publicKey,
      executeWorker:()=>{throw new Error("must not execute");},deliveryPrivateKey:delivery.privateKey}),/refusing unattested HoloVM continuation/);
    assert.throws(()=>S.migrateWorker(oldDispatch,candidate("w2","replay2"),request2),/history root/);
  });

  test("base signed delivery carries the exact attested market-history root",()=>{
    const verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519"),c=candidate("w","base");
    const tx=Q.executeContinuationTransaction({candidates:[c],request:request1,
      obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
      executeWorker:()=>Object.freeze({schema:Q.EXECUTION_SCHEMA,parentContinuationRoot:root,childContinuationRoot:d("history-child"),processId,generationBefore:12,generationAfter:13,
        emissionId:d("history-emission"),guestReceiptIds:[d("history-receipt")],stopReason:"fuel"}),deliveryPrivateKey:delivery.privateKey});
    assert.equal(tx.dispatch.representationMarketHistoryRootDigest,c1.rootDigest);
    assert.equal(tx.attestation.representationMarketHistoryRootDigest,c1.rootDigest);
    assert.equal(tx.delivery.body.representationMarketHistoryRootDigest,c1.rootDigest);
    assert.equal(tx.delivery.body.representationMarketHistoryEventCount,1);
    assert.equal(Q.verifyDelivery(tx.delivery,delivery.publicKey).ok,true);
  });

  test("dynamic telemetry delivery preserves history root while price remains independently mutable",()=>{
    const pricing=crypto.generateKeyPairSync("ed25519"),verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519");
    const id="dynamic-history-worker",runtimePublicKeyDigest=d("dynamic-history-runtime");
    const telemetry=Telemetry.buildPricingTelemetry({workerId:id,runtimePublicKeyDigest,calibrationEpoch:40,pricingEpoch:20,validFromGeneration:12,validThroughGeneration:12,
      measurementDigest:d("dynamic-history-measurement"),unitPrices:prices({semanticGuestStepUSD:2})});
    const signed=Telemetry.signPricingTelemetry(telemetry,pricing.privateKey,"history-pricing-key");
    const c=Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest,
      topology:Object.freeze({attested:true,attestationDigest:d("dynamic-history-topology"),points:[0,1,2]}),retainedUnionDeltaBytes:{[root]:0},
      computePerSecondUSD:0,startupUSD:0,signedResourcePricingTelemetry:signed});
    const tx=R.executeDynamicResourceTransaction({candidates:[c],request:request1,trustedPricingPublicKeys:{"history-pricing-key":pricing.publicKey},minimumCalibrationEpoch:40,minimumPricingEpoch:20,
      obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
      executeWorker:()=>Object.freeze({schema:Q.EXECUTION_SCHEMA,parentContinuationRoot:root,childContinuationRoot:d("dynamic-history-child"),processId,generationBefore:12,generationAfter:13,
        emissionId:d("dynamic-history-emission"),guestReceiptIds:[d("dynamic-history-receipt")],stopReason:"fuel"}),deliveryPrivateKey:delivery.privateKey});
    assert.equal(tx.dynamicResource.delivery.body.representationMarketHistoryRootDigest,c1.rootDigest);
    const verified=R.verifyDynamicResourceDelivery(tx,delivery.publicKey);
    assert.equal(verified.ok,true);assert.equal(verified.representationMarketHistoryRootDigest,c1.rootDigest);
  });
}
