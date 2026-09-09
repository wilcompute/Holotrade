"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");

const A=require("../js/w33-measured-boot-attestation.js");
const D=require("../js/w33-passport-deployment.js");
const P=require("../js/w33-signed-resource-policy.js");
const M=require("../js/w33-signed-resource-telemetry.js");
const S=require("../scheduler/w33-continuation-scheduler.js");
const Q=require("../scheduler/w33-continuation-transaction.js");
const R=require("../scheduler/w33-dynamic-resource-transaction.js");

function d(label){return S.sha256(label);}
function prices(overrides={}){return Object.freeze({semanticGuestStepUSD:0,w33RouteHopUSD:0,authenticatedRetainedByteTickUSD:0,
  authenticatedSweptPayloadByteUSD:0,deterministicReplayStepUSD:0,representationExcessUSD:3,samplingExcessUSD:5,...overrides});}
function verdict(challenge,key){return A.signVerifierVerdict({provider:A.PROVIDER.SEV_SNP,challengeDigest:challenge.challengeDigest,
  launchMeasurement:d("d3-launch"),reportedTcbDigest:d("d3-tcb"),signerChainDigest:d("d3-chain"),hardwareBacked:true,
  vendorSignatureVerified:true,measurementPolicyVerified:true,tcbPolicyVerified:true,runtimeKeyBound:true,verifierKeyId:"d3-verifier"},key);}

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if(!certPath){test("depth3 W33 economics certificate supplied by cross-repo CI",{skip:true},()=>{});}else{
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));

  test("depth2 and depth3 share exact A/A2 but retain distinct signed-resource identities",()=>{
    const d2=P.verifySignedResourceCertificate(cert,"exception-depth2");
    const d3=P.verifySignedResourceCertificate(cert,"exception-depth3-mass24");
    assert.equal(d2.depth,2); assert.equal(d3.depth,3);
    assert.equal(d2.representationAmplification,"2"); assert.equal(d3.representationAmplification,"2");
    assert.equal(d2.signedSamplingSecondMomentFactor,"4"); assert.equal(d3.signedSamplingSecondMomentFactor,"4");
    assert.equal(d2.representationExcessAminus1,d3.representationExcessAminus1);
    assert.equal(d2.samplingExcessA2minus1,d3.samplingExcessA2minus1);
    assert.notEqual(d2.selectionDigest,d3.selectionDigest);
    const q=prices(); const p2=P.priceSignedResource(d2,q),p3=P.priceSignedResource(d3,q);
    assert.equal(p2.totalUSD,p3.totalUSD);
    assert.notEqual(p2.priceDigest,p3.priceDigest);
  });

  test("dynamic telemetry signs and delivers the depth3 selection without aliasing depth2",()=>{
    const deploymentDigest=d("d3-deployment");
    const passport=Object.freeze({schema:D.SCHEMA,passportId:d("d3-passport"),deploymentDigest,machineType:"w33.circuit216.steinberg81",
      logicalDimension:81,capabilityEpoch:1,revocationRoot:d("d3-revocations")});
    const contract=Object.freeze({deploymentDigest}); const root=d("d3-root"),processId=d("d3-process");
    const request=Object.freeze({continuationRoot:root,processId,generation:12,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,
      requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass:"exception-depth3-mass24"});
    const pricing=crypto.generateKeyPairSync("ed25519"), verifier=crypto.generateKeyPairSync("ed25519"), delivery=crypto.generateKeyPairSync("ed25519");
    const id="depth3-worker",runtimePublicKeyDigest=d("depth3-runtime");
    const telemetry=M.buildPricingTelemetry({workerId:id,runtimePublicKeyDigest,calibrationEpoch:21,pricingEpoch:7,validFromGeneration:12,validThroughGeneration:12,
      measurementDigest:d("depth3-pricing-measurement"),unitPrices:prices({semanticGuestStepUSD:1})});
    const signed=M.signPricingTelemetry(telemetry,pricing.privateKey,"depth3-pricing-key");
    const candidate=Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest,
      topology:Object.freeze({attested:true,attestationDigest:d("d3-topology"),points:[0,1,2,3]}),retainedUnionDeltaBytes:{[root]:0},
      computePerSecondUSD:0,startupUSD:0,signedResourcePricingTelemetry:signed});
    const tx=R.executeDynamicResourceTransaction({candidates:[candidate],request,trustedPricingPublicKeys:{"depth3-pricing-key":pricing.publicKey},
      minimumCalibrationEpoch:21,minimumPricingEpoch:7,
      obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
      executeWorker:()=>Object.freeze({schema:Q.EXECUTION_SCHEMA,parentContinuationRoot:root,childContinuationRoot:d("d3-child"),processId,
        generationBefore:12,generationAfter:13,emissionId:d("d3-emission"),guestReceiptIds:[d("d3-receipt")],stopReason:"fuel"}),
      deliveryPrivateKey:delivery.privateKey,deliveryKeyId:"depth3-delivery"});
    assert.equal(tx.ok,true);
    assert.equal(tx.dispatch.representationClass,"exception-depth3-mass24");
    assert.equal(tx.dispatch.representationAmplification,"2");
    assert.equal(tx.dispatch.signedSamplingSecondMomentFactor,"4");
    assert.equal(tx.dynamicResource.delivery.body.representationClass,"exception-depth3-mass24");
    assert.equal(tx.dynamicResource.delivery.body.signedResourceSelectionDigest,tx.dispatch.signedResourceSelectionDigest);
    assert.equal(R.verifyDynamicResourceDelivery(tx,delivery.publicKey).ok,true);
    const depth2=S.normalizeRequest({...request,representationClass:"exception-depth2"});
    assert.notEqual(depth2.signedResourceSelectionDigest,tx.dispatch.signedResourceSelectionDigest);
  });

  test("tampering depth3 class to depth2 fails even though A and A2 are identical",()=>{
    const sel=P.verifySignedResourceCertificate(cert,"exception-depth3-mass24");
    const fake={...sel,representationClass:"exception-depth2"};
    assert.notEqual(P.sha256({...fake,selectionDigest:undefined}),sel.selectionDigest);
    const certBad=structuredClone(cert);
    certBad.resource_vectors["exception-depth3-mass24"].representation_class="exception-depth2";
    assert.throws(()=>P.verifySignedResourceCertificate(certBad,"exception-depth3-mass24"),/representation class identity drift/);
  });
}
