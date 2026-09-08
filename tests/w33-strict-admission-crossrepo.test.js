"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const H = require("../js/w33-strict-admission-binding.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(label) { return S.sha256(label); }

const path = process.env.W33_STRICT_POLICY_EXECUTION_BUNDLE;
if (!path) {
  test("strict W33 cross-repo bundle is supplied by CI", { skip: true }, () => {});
} else {
  test("strict W33 delta and joint-plan identity survive pricing attestation migration and signed delivery", () => {
    const bundle = JSON.parse(fs.readFileSync(path, "utf8"));
    assert.equal(bundle.schema, "w33.holotrade-strict-policy-execution-bundle.v1");
    assert.equal(bundle.status, "PASS");
    const strict = H.verifyStrictBinding(bundle.strictBinding, bundle.executionPolicy);
    const policy = strict.executionPolicy;
    const execution = bundle.execution;
    assert.equal(strict.retainedUnionDeltaBytes < strict.postAdmissionRetainedUnionBytes, true);
    assert.equal(strict.postAdmissionRetainedUnionBytes, policy.snapshotPayloadBytes);

    const verifierKeys = crypto.generateKeyPairSync("ed25519");
    const deliveryKeys = crypto.generateKeyPairSync("ed25519");
    const deploymentDigest = d("strict-crossrepo-deployment");
    const passport = Object.freeze({
      schema: D.SCHEMA,
      passportId: d("strict-crossrepo-passport"),
      deploymentDigest,
      machineType: "w33.circuit216.steinberg81",
      logicalDimension: 81,
      capabilityEpoch: 31,
      revocationRoot: d("strict-crossrepo-revocations"),
    });
    const contract = Object.freeze({ deploymentDigest });
    const request = Object.freeze({
      continuationRoot: policy.continuationRoot,
      processId: policy.processId,
      generation: policy.generation,
      executionPolicy: bundle.executionPolicy,
      strictAdmissionBinding: bundle.strictBinding,
      passport,
      contract,
      evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
      requiredPoints: [0, 1],
      durationSeconds: 1,
    });
    function worker(id, delta) {
      return Object.freeze({
        id,
        evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
        runtimePublicKeyDigest: d(`strict-runtime-${id}`),
        topology: Object.freeze({ attested: true, attestationDigest: d(`strict-topology-${id}`), points: [0,1,2,3,4,5], failurePoints: [] }),
        retainedUnionDeltaBytesByPolicy: { [policy.executionPolicyDigest]: delta },
        computePerSecondUSD: 0.01,
      });
    }
    const good = worker("good", strict.retainedUnionDeltaBytes);
    const bad = worker("bad", strict.retainedUnionDeltaBytes + 1);
    const rejected = S.rankContinuations([bad], request);
    assert.equal(rejected.eligible.length, 0);
    assert.equal(rejected.rejected[0].code, "EXACT_STRICT_RETAINED_DELTA_REQUIRED");

    const dispatch = S.chooseContinuationWorker([good], request).dispatch;
    assert.equal(dispatch.strictAdmissionBindingDigest, strict.strictBindingDigest);
    assert.equal(dispatch.jointPlanDigest, strict.jointPlanDigest);
    assert.equal(dispatch.strategyDigest, strict.strategyDigest);
    assert.equal(dispatch.strictPlacementDigest, strict.placementDigest);
    assert.equal(dispatch.retainedUnionDeltaBytes, strict.retainedUnionDeltaBytes);
    assert.equal(dispatch.challenge.strictAdmissionBindingDigest, strict.strictBindingDigest);

    const migrated = S.migrateWorker(dispatch, worker("migrated", strict.retainedUnionDeltaBytes), request);
    assert.equal(migrated.strictAdmissionBindingDigest, strict.strictBindingDigest);
    assert.equal(migrated.jointPlanDigest, strict.jointPlanDigest);
    assert.equal(migrated.strategyDigest, strict.strategyDigest);
    assert.equal(migrated.strictPlacementDigest, strict.placementDigest);
    assert.equal(migrated.dispatch.strictAdmissionBindingDigest, strict.strictBindingDigest);

    const tx = T.executeContinuationTransaction({
      candidates: [good],
      request,
      obtainSignedVerifierVerdict: ({ challenge }) => A.signVerifierVerdict({
        provider: A.PROVIDER.SEV_SNP,
        challengeDigest: challenge.challengeDigest,
        launchMeasurement: d("strict-launch"),
        reportedTcbDigest: d("strict-tcb"),
        signerChainDigest: d("strict-chain"),
        hardwareBacked: true,
        vendorSignatureVerified: true,
        measurementPolicyVerified: true,
        tcbPolicyVerified: true,
        runtimeKeyBound: true,
        verifierKeyId: "strict-verifier",
      }, verifierKeys.privateKey),
      trustedVerifierPublicKey: verifierKeys.publicKey,
      executeWorker: () => execution,
      deliveryPrivateKey: deliveryKeys.privateKey,
      deliveryKeyId: "strict-delivery",
    });

    assert.equal(tx.attestation.strictAdmissionBindingDigest, strict.strictBindingDigest);
    const body = tx.delivery.body;
    assert.equal(body.strictAdmissionBindingDigest, strict.strictBindingDigest);
    assert.equal(body.handoffDigest, strict.handoffDigest);
    assert.equal(body.jointPlanDigest, strict.jointPlanDigest);
    assert.equal(body.strategyDigest, strict.strategyDigest);
    assert.equal(body.strictPlacementDigest, strict.placementDigest);
    assert.equal(body.retainedUnionDeltaBytes, strict.retainedUnionDeltaBytes);
    assert.equal(body.baselineRetainedUnionBytes, strict.baselineRetainedUnionBytes);
    assert.equal(body.postAdmissionRetainedUnionBytes, strict.postAdmissionRetainedUnionBytes);
    assert.equal(T.verifyDelivery(tx.delivery, deliveryKeys.publicKey).ok, true);
  });
}
