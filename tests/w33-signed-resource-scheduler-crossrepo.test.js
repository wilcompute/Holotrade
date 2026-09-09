"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const C = require("../js/w33-continuation-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const P = require("../js/w33-signed-resource-policy.js");
const S = require("../scheduler/w33-continuation-scheduler.js");

function d(label) { return S.sha256(label); }
function prices(overrides={}) {
  return Object.freeze({ semanticGuestStepUSD:0, w33RouteHopUSD:0, authenticatedRetainedByteTickUSD:0,
    authenticatedSweptPayloadByteUSD:0, deterministicReplayStepUSD:0, representationExcessUSD:0, samplingExcessUSD:0, ...overrides });
}
function signedVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({ provider:A.PROVIDER.SEV_SNP, challengeDigest:challenge.challengeDigest,
    launchMeasurement:d("signed-resource-launch"), reportedTcbDigest:d("signed-resource-tcb"), signerChainDigest:d("signed-resource-chain"),
    hardwareBacked:true, vendorSignatureVerified:true, measurementPolicyVerified:true, tcbPolicyVerified:true, runtimeKeyBound:true,
    verifierKeyId:"signed-resource-verifier" }, privateKey);
}

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if (!certPath) {
  test("W33 signed-resource certificate is supplied by dedicated cross-repo CI", {skip:true},()=>{});
} else {
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const deploymentDigest=d("signed-resource-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("signed-resource-passport"),deploymentDigest,
    machineType:"w33.circuit216.steinberg81",logicalDimension:81,capabilityEpoch:1,revocationRoot:d("signed-resource-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const root=d("signed-resource-root"), processId=d("signed-resource-process");
  function request(representationClass) { return Object.freeze({continuationRoot:root,processId,generation:7,passport,contract,
    evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass}); }
  function worker(id, unitPrices) { return Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d(`runtime-${id}`),
    topology:Object.freeze({attested:true,attestationDigest:d(`topology-${id}`),points:[0,1,2,3]}),retainedUnionDeltaBytes:{[root]:0},
    computePerSecondUSD:0,startupUSD:0,signedResourceUnitPrices:unitPrices}); }
  const workCheap=worker("work-cheap",prices({representationExcessUSD:100,samplingExcessUSD:100}));
  const representationCheap=worker("representation-cheap",prices({semanticGuestStepUSD:1}));

  test("independent resource prices flip worker choice between depth0 and depth2 without changing semantic work",()=>{
    const q0=S.chooseContinuationWorker([workCheap,representationCheap],request("positive-depth0"));
    assert.equal(q0.ok,true); assert.equal(q0.dispatch.workerId,"work-cheap");
    assert.equal(q0.dispatch.price.signedResourceUSD,0);
    const q2=S.chooseContinuationWorker([workCheap,representationCheap],request("exception-depth2"));
    assert.equal(q2.ok,true); assert.equal(q2.dispatch.workerId,"representation-cheap");
    assert.equal(q2.dispatch.representationAmplification,"2"); assert.equal(q2.dispatch.signedSamplingSecondMomentFactor,"4");
    assert.equal(q2.dispatch.price.signedResourcePrice.components.representationExcessUSD,0);
    assert.ok(q2.dispatch.price.signedResourceUSD>0);
    assert.notEqual(q0.dispatch.attestationChallengeDigest,q2.dispatch.attestationChallengeDigest);
    assert.equal(q2.dispatch.challenge.signedResourceCertificateDigest,q2.dispatch.signedResourceCertificateDigest);
    assert.equal(q2.dispatch.challenge.signedResourceSelectionDigest,q2.dispatch.signedResourceSelectionDigest);
    assert.notEqual(q0.dispatch.signedResourceSelectionDigest,q2.dispatch.signedResourceSelectionDigest);
  });

  test("hardware binding commits the exact resource selection, not only the umbrella certificate",()=>{
    const selected=S.chooseContinuationWorker([representationCheap],request("exception-depth1"));
    const keys=crypto.generateKeyPairSync("ed25519");
    const verdict=signedVerdict(selected.dispatch.challenge,keys.privateKey);
    const binding=C.verifiedContinuationBinding(passport,contract,selected.dispatch.challenge,verdict,keys.publicKey);
    assert.equal(binding.signedResourceCertificateDigest,selected.dispatch.signedResourceCertificateDigest);
    assert.equal(binding.signedResourceSelectionDigest,selected.dispatch.signedResourceSelectionDigest);
  });

  test("tampered exact factors and partial price vectors fail closed",()=>{
    const bad=structuredClone(cert); bad.resource_vectors["exception-depth2"].representation_amplification="3";
    assert.throws(()=>S.normalizeRequest({...request("exception-depth2"),signedResourceCertificate:bad}),/factor drift/);
    const missing=worker("missing-price",Object.freeze({semanticGuestStepUSD:0}));
    const ranked=S.rankContinuations([missing],request("exception-depth1"));
    assert.equal(ranked.eligible.length,0); assert.equal(ranked.rejected[0].code,"COMPLETE_SIGNED_RESOURCE_UNIT_PRICES_REQUIRED");
  });

  test("migration cannot silently change representation class under the same W33 certificate",()=>{
    const q0=S.chooseContinuationWorker([workCheap],request("positive-depth0"));
    assert.throws(()=>S.migrateWorker(q0.dispatch,representationCheap,request("exception-depth2")),/selection identity|representation class/);
  });

  test("certificate verifier preserves all seven typed coordinates",()=>{
    const sel=P.verifySignedResourceCertificate(cert,"exception-depth1");
    assert.equal(sel.representationAmplification,"3/2"); assert.equal(sel.signedSamplingSecondMomentFactor,"9/4");
    for (const k of ["semanticGuestSteps","w33RouteHops","authenticatedRetainedByteTicks","authenticatedSweptPayloadBytes","deterministicReplaySteps"]) assert.equal(Number.isSafeInteger(sel[k]),true);
  });
}
