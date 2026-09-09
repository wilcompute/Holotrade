"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");

const A=require("../js/w33-measured-boot-attestation.js");
const D=require("../js/w33-passport-deployment.js");
const P=require("../js/w33-signed-resource-policy.js");
const T=require("../js/w33-signed-resource-telemetry.js");
const I=require("../js/w33-representation-market-identity.js");
const S=require("../scheduler/w33-continuation-scheduler.js");
const Q=require("../scheduler/w33-continuation-transaction.js");
const R=require("../scheduler/w33-dynamic-resource-transaction.js");

function d(label){return S.sha256(label);}
function prices(overrides={}){return Object.freeze({semanticGuestStepUSD:0,w33RouteHopUSD:0,authenticatedRetainedByteTickUSD:0,
  authenticatedSweptPayloadByteUSD:0,deterministicReplayStepUSD:0,representationExcessUSD:3,samplingExcessUSD:5,...overrides});}
function verdict(challenge,key){return A.signVerifierVerdict({provider:A.PROVIDER.SEV_SNP,challengeDigest:challenge.challengeDigest,
  launchMeasurement:d("market-id-launch"),reportedTcbDigest:d("market-id-tcb"),signerChainDigest:d("market-id-chain"),hardwareBacked:true,
  vendorSignatureVerified:true,measurementPolicyVerified:true,tcbPolicyVerified:true,runtimeKeyBound:true,verifierKeyId:"market-id-verifier"},key);}

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if(!certPath){test("W33 economics certificate supplied by cross-repo CI",{skip:true},()=>{});}else{
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const d2=P.verifySignedResourceCertificate(cert,"exception-depth2");
  const d3=P.verifySignedResourceCertificate(cert,"exception-depth3-mass24");
  const i2=I.identityFromSelection(d2),i3=I.identityFromSelection(d3);

  test("equal-priced depth2/depth3 remain distinct first-class market identities",()=>{
    assert.equal(d2.representationAmplification,d3.representationAmplification);
    assert.equal(d2.signedSamplingSecondMomentFactor,d3.signedSamplingSecondMomentFactor);
    const p2=P.priceSignedResource(d2,prices()),p3=P.priceSignedResource(d3,prices());
    assert.equal(p2.totalUSD,p3.totalUSD);
    assert.notEqual(p2.priceDigest,p3.priceDigest);
    assert.notEqual(i2.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(I.assertSelectionIdentity(d3,i3).representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.throws(()=>I.assertSelectionIdentity(d3,i2),/market identity disagrees/);
  });

  test("bid and award reject a cheaper substituted representation class",()=>{
    const p2=P.priceSignedResource(d2,prices()),p3=P.priceSignedResource(d3,prices());
    const b2=I.buildBid({workerId:"depth2-cheap",identity:i2,priceDigest:p2.priceDigest,totalUSD:1,pricingEpoch:11});
    const b3=I.buildBid({workerId:"depth3-exact",identity:i3,priceDigest:p3.priceDigest,totalUSD:9,pricingEpoch:11});
    const picked=I.selectBid([b2,b3],i3);
    assert.equal(picked.ok,true);assert.equal(picked.award.workerId,"depth3-exact");
    assert.equal(picked.award.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(picked.rejected.length,1);assert.equal(picked.rejected[0].workerId,"depth2-cheap");
  });

  test("hardware challenge and migration preserve price-independent representation identity",()=>{
    const deploymentDigest=d("market-id-deployment");
    const passport=Object.freeze({schema:D.SCHEMA,passportId:d("market-id-passport"),deploymentDigest,machineType:"w33.circuit216.steinberg81",
      logicalDimension:81,capabilityEpoch:1,revocationRoot:d("market-id-revocations")});
    const contract=Object.freeze({deploymentDigest}); const root=d("market-id-root"),processId=d("market-id-process");
    const request=Object.freeze({continuationRoot:root,processId,generation:4,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,
      requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass:"exception-depth3-mass24"});
    const candidate=(id,tag)=>Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d(`${tag}-runtime`),
      topology:Object.freeze({attested:true,attestationDigest:d(`${tag}-topology`),points:[0,1,2]}),retainedUnionDeltaBytes:{[root]:0},
      computePerSecondUSD:0,startupUSD:0,signedResourceUnitPrices:prices()});
    const norm=S.normalizeRequest(request);assert.equal(norm.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    const dispatch=S.dispatchFor(candidate("w1","w1"),norm);
    assert.equal(dispatch.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(dispatch.challenge.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(I.bindDispatchAttestation(dispatch,i3).representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    const migration=S.migrateWorker(dispatch,candidate("w2","w2"),request);
    assert.equal(migration.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(I.bindMigration(migration,i3).representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    const depth2={...request,representationClass:"exception-depth2"};
    assert.throws(()=>S.migrateWorker(dispatch,candidate("w3","w3"),depth2),/signed-resource selection identity|representation market identity|representation class/);
  });

  test("dynamic signed delivery, settlement, and replay bind the exact representation identity",()=>{
    const deploymentDigest=d("settle-deployment");
    const passport=Object.freeze({schema:D.SCHEMA,passportId:d("settle-passport"),deploymentDigest,machineType:"w33.circuit216.steinberg81",
      logicalDimension:81,capabilityEpoch:1,revocationRoot:d("settle-revocations")});
    const contract=Object.freeze({deploymentDigest});const root=d("settle-root"),processId=d("settle-process");
    const request=Object.freeze({continuationRoot:root,processId,generation:8,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,
      requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass:"exception-depth3-mass24"});
    const pricing=crypto.generateKeyPairSync("ed25519"),verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519");
    const id="settle-worker",runtimePublicKeyDigest=d("settle-runtime");
    const telemetry=T.buildPricingTelemetry({workerId:id,runtimePublicKeyDigest,calibrationEpoch:30,pricingEpoch:12,validFromGeneration:8,validThroughGeneration:8,
      measurementDigest:d("settle-price-measurement"),unitPrices:prices({semanticGuestStepUSD:2})});
    const signed=T.signPricingTelemetry(telemetry,pricing.privateKey,"settle-pricing-key");
    const candidate=Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest,
      topology:Object.freeze({attested:true,attestationDigest:d("settle-topology"),points:[0,1,2]}),retainedUnionDeltaBytes:{[root]:0},
      computePerSecondUSD:0,startupUSD:0,signedResourcePricingTelemetry:signed});
    const tx=R.executeDynamicResourceTransaction({candidates:[candidate],request,trustedPricingPublicKeys:{"settle-pricing-key":pricing.publicKey},minimumCalibrationEpoch:30,minimumPricingEpoch:12,
      obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
      executeWorker:()=>Object.freeze({schema:Q.EXECUTION_SCHEMA,parentContinuationRoot:root,childContinuationRoot:d("settle-child"),processId,generationBefore:8,generationAfter:9,
        emissionId:d("settle-emission"),guestReceiptIds:[d("settle-receipt")],stopReason:"fuel"}),deliveryPrivateKey:delivery.privateKey,deliveryKeyId:"settle-delivery"});
    assert.equal(R.verifyDynamicResourceDelivery(tx,delivery.publicKey).ok,true);
    assert.equal(tx.dispatch.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(tx.attestation.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(tx.delivery.body.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.equal(tx.dynamicResource.delivery.body.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    const settlement=I.settleVerifiedDynamicResult(tx,i3);
    const replay=I.replayKey(settlement,i3);
    assert.equal(replay.representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
    assert.throws(()=>I.replayKey(settlement,i2),/substituted representation/);
  });

  test("price epochs can change price identity without changing representation identity",()=>{
    const q1=prices({representationExcessUSD:1,samplingExcessUSD:2});
    const q2=prices({representationExcessUSD:10,samplingExcessUSD:20});
    const p1=P.priceSignedResource(d3,q1),p2=P.priceSignedResource(d3,q2);
    assert.notEqual(p1.totalUSD,p2.totalUSD);assert.notEqual(p1.priceDigest,p2.priceDigest);
    assert.equal(I.identityFromSelection(d3).representationMarketIdentityDigest,i3.representationMarketIdentityDigest);
  });
}
