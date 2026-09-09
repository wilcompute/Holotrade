"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const M = require("../js/w33-signed-resource-telemetry.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const Q = require("../scheduler/w33-continuation-transaction.js");
const R = require("../scheduler/w33-dynamic-resource-transaction.js");

function d(label) { return S.sha256(label); }
function prices(overrides={}) {
  return Object.freeze({ semanticGuestStepUSD:0, w33RouteHopUSD:0, authenticatedRetainedByteTickUSD:0,
    authenticatedSweptPayloadByteUSD:0, deterministicReplayStepUSD:0, representationExcessUSD:0, samplingExcessUSD:0, ...overrides });
}
function signedVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({ provider:A.PROVIDER.SEV_SNP, challengeDigest:challenge.challengeDigest,
    launchMeasurement:d("dynamic-resource-launch"), reportedTcbDigest:d("dynamic-resource-tcb"), signerChainDigest:d("dynamic-resource-chain"),
    hardwareBacked:true, vendorSignatureVerified:true, measurementPolicyVerified:true, tcbPolicyVerified:true, runtimeKeyBound:true,
    verifierKeyId:"dynamic-resource-verifier" }, privateKey);
}

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if (!certPath) {
  test("W33 signed-resource certificate is supplied by dedicated cross-repo CI", {skip:true},()=>{});
} else {
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const deploymentDigest=d("dynamic-resource-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("dynamic-resource-passport"),deploymentDigest,
    machineType:"w33.circuit216.steinberg81",logicalDimension:81,capabilityEpoch:1,revocationRoot:d("dynamic-resource-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const root=d("dynamic-resource-root"), processId=d("dynamic-resource-process");
  const pricingKeys=crypto.generateKeyPairSync("ed25519");
  const pricingKeys2=crypto.generateKeyPairSync("ed25519");
  const verifierKeys=crypto.generateKeyPairSync("ed25519");
  const deliveryKeys=crypto.generateKeyPairSync("ed25519");
  const trusted=Object.freeze({"pricing-key":pricingKeys.publicKey,"pricing-key-2":pricingKeys2.publicKey});

  function request(representationClass="exception-depth2") {
    return Object.freeze({continuationRoot:root,processId,generation:7,passport,contract,
      evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass});
  }
  function signedTelemetry(id, runtimePublicKeyDigest, unitPrices, {calibrationEpoch=11,pricingEpoch=1,from=7,through=7,keyId="pricing-key",privateKey=pricingKeys.privateKey,measurement="measurement"}={}) {
    const body=M.buildPricingTelemetry({workerId:id,runtimePublicKeyDigest,calibrationEpoch,pricingEpoch,validFromGeneration:from,validThroughGeneration:through,
      measurementDigest:d(`${measurement}-${id}-${calibrationEpoch}-${pricingEpoch}`),unitPrices});
    return M.signPricingTelemetry(body,privateKey,keyId);
  }
  function worker(id, unitPrices, telemetryOpts={}) {
    const runtimePublicKeyDigest=d(`runtime-${id}`);
    return Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest,
      topology:Object.freeze({attested:true,attestationDigest:d(`topology-${id}`),points:[0,1,2,3]}),retainedUnionDeltaBytes:{[root]:0},
      computePerSecondUSD:0,startupUSD:0,
      signedResourcePricingTelemetry:signedTelemetry(id,runtimePublicKeyDigest,unitPrices,telemetryOpts)});
  }
  function execReceipt(label="dynamic") {
    return Object.freeze({schema:Q.EXECUTION_SCHEMA,parentContinuationRoot:root,childContinuationRoot:d(`${label}-child`),processId,
      generationBefore:7,generationAfter:8,emissionId:d(`${label}-emission`),guestReceiptIds:[d(`${label}-receipt`)],stopReason:"fuel"});
  }
  function execute(candidates, req=request(), opts={}) {
    return R.executeDynamicResourceTransaction({candidates,request:req,trustedPricingPublicKeys:opts.trustedPricingPublicKeys||trusted,
      minimumCalibrationEpoch:opts.minimumCalibrationEpoch??10,minimumPricingEpoch:opts.minimumPricingEpoch??1,
      obtainSignedVerifierVerdict:({challenge})=>signedVerdict(challenge,verifierKeys.privateKey),trustedVerifierPublicKey:verifierKeys.publicKey,
      executeWorker:()=>execReceipt(opts.label||"dynamic"),deliveryPrivateKey:deliveryKeys.privateKey,deliveryKeyId:"dynamic-delivery"});
  }

  test("scheduler consumes only verified signed telemetry and dynamic prices can flip worker choice",()=>{
    const repExpensive=worker("rep-expensive",prices({representationExcessUSD:100,samplingExcessUSD:100}));
    const workExpensive=worker("work-expensive",prices({semanticGuestStepUSD:1}));
    assert.equal(Object.hasOwn(repExpensive,"signedResourceUnitPrices"),false);
    assert.equal(Object.hasOwn(workExpensive,"signedResourceUnitPrices"),false);
    const tx=execute([repExpensive,workExpensive],request("exception-depth2"),{label:"flip"});
    assert.equal(tx.dispatch.workerId,"work-expensive");
    assert.equal(tx.dispatch.price.signedResourcePrice.unitPrices.semanticGuestStepUSD,1);
    assert.equal(tx.dynamicResource.telemetry.workerId,"work-expensive");
    assert.equal(R.verifyDynamicResourceDelivery(tx,deliveryKeys.publicKey).ok,true);
  });

  test("pricing epoch update preserves continuation and representation identity but changes price and signed delivery identity",()=>{
    const id="epoch-worker", runtime=d(`runtime-${id}`);
    const base={id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:runtime,
      topology:Object.freeze({attested:true,attestationDigest:d(`topology-${id}`),points:[0,1,2,3]}),retainedUnionDeltaBytes:{[root]:0},computePerSecondUSD:0,startupUSD:0};
    const a=Object.freeze({...base,signedResourcePricingTelemetry:signedTelemetry(id,runtime,prices({semanticGuestStepUSD:1}),{pricingEpoch:1})});
    const b=Object.freeze({...base,signedResourcePricingTelemetry:signedTelemetry(id,runtime,prices({semanticGuestStepUSD:2}),{pricingEpoch:2})});
    const t1=execute([a],request("exception-depth1"),{label:"epoch1",minimumPricingEpoch:1});
    const t2=execute([b],request("exception-depth1"),{label:"epoch2",minimumPricingEpoch:2});
    for (const tx of [t1,t2]) {
      assert.equal(tx.dispatch.continuationRoot,root); assert.equal(tx.dispatch.processId,processId); assert.equal(tx.dispatch.generation,7);
      assert.equal(tx.dispatch.representationClass,"exception-depth1"); assert.equal(R.verifyDynamicResourceDelivery(tx,deliveryKeys.publicKey).ok,true);
    }
    assert.equal(t1.dispatch.signedResourceSelectionDigest,t2.dispatch.signedResourceSelectionDigest);
    assert.notEqual(t1.dynamicResource.telemetry.signedTelemetryDigest,t2.dynamicResource.telemetry.signedTelemetryDigest);
    assert.notEqual(t1.dispatch.signedResourcePriceDigest,t2.dispatch.signedResourcePriceDigest);
    assert.notEqual(t1.delivery.body.deliveryDigest,t2.delivery.body.deliveryDigest);
    assert.notEqual(t1.dynamicResource.delivery.body.dynamicDeliveryDigest,t2.dynamicResource.delivery.body.dynamicDeliveryDigest);
  });

  test("pricing telemetry cannot be replayed across worker or runtime identity",()=>{
    const a=worker("worker-a",prices());
    const replay=Object.freeze({id:"worker-b",evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d("runtime-worker-b"),
      topology:Object.freeze({attested:true,attestationDigest:d("topology-worker-b"),points:[0,1,2,3]}),retainedUnionDeltaBytes:{[root]:0},computePerSecondUSD:0,startupUSD:0,
      signedResourcePricingTelemetry:a.signedResourcePricingTelemetry});
    assert.throws(()=>R.verifiedTelemetryCandidates([replay],request(),{trustedPricingPublicKeys:trusted}),/worker identity drift|runtime key drift/);
  });

  test("stale generation, low calibration epoch, and untrusted pricing key fail closed",()=>{
    const stale=worker("stale",prices(),{from:6,through:6});
    assert.throws(()=>R.verifiedTelemetryCandidates([stale],request(),{trustedPricingPublicKeys:trusted}),/not valid for continuation generation/);
    const old=worker("old-cal",prices(),{calibrationEpoch:2});
    assert.throws(()=>R.verifiedTelemetryCandidates([old],request(),{trustedPricingPublicKeys:trusted,minimumCalibrationEpoch:10}),/calibration epoch below floor/);
    const untrusted=worker("untrusted",prices(),{keyId:"alien-key",privateKey:pricingKeys2.privateKey});
    assert.throws(()=>R.verifiedTelemetryCandidates([untrusted],request(),{trustedPricingPublicKeys:trusted}),/untrusted resource pricing key/);
  });

  test("tampering telemetry-bound dynamic delivery fails verification",()=>{
    const tx=execute([worker("tamper",prices({semanticGuestStepUSD:1}))],request(),{label:"tamper"});
    const bad=structuredClone(tx);
    bad.dynamicResource.delivery.body.pricingEpoch += 1;
    assert.equal(R.verifyDynamicResourceDelivery(bad,deliveryKeys.publicKey).ok,false);
  });
}
