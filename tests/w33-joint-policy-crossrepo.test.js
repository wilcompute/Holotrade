"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const J = require("../js/w33-joint-admission-policy.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(label) { return S.sha256(label); }

const path = process.env.W33_POLICY_EXECUTION_BUNDLE;
if (!path) {
  test("cross-repo W33 policy execution bundle is supplied by CI", { skip: true }, () => {});
} else {
  test("real W33 parent is jointly priced, attested, executed and signed without identity substitution", () => {
    const bundle = JSON.parse(fs.readFileSync(path, "utf8"));
    assert.equal(bundle.schema, "w33.holotrade-policy-execution-bundle.v1");
    assert.equal(bundle.status, "PASS");
    const executionPolicy = J.verifyPolicy(bundle.executionPolicy);
    const execution = bundle.execution;
    assert.equal(executionPolicy.continuationRoot, execution.parentContinuationRoot);
    assert.equal(executionPolicy.processId, execution.processId);
    assert.equal(executionPolicy.generation, execution.generationBefore);

    const verifierKeys = crypto.generateKeyPairSync("ed25519");
    const deliveryKeys = crypto.generateKeyPairSync("ed25519");
    const deploymentDigest = d("crossrepo-policy-deployment");
    const passport = Object.freeze({
      schema: D.SCHEMA,
      passportId: d("crossrepo-policy-passport"),
      deploymentDigest,
      machineType: "w33.circuit216.steinberg81",
      logicalDimension: 81,
      capabilityEpoch: 21,
      revocationRoot: d("crossrepo-policy-revocations"),
    });
    const contract = Object.freeze({ deploymentDigest });
    const request = Object.freeze({
      continuationRoot: executionPolicy.continuationRoot,
      processId: executionPolicy.processId,
      generation: executionPolicy.generation,
      executionPolicy: bundle.executionPolicy,
      passport,
      contract,
      evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
      requiredPoints: [0, 1],
      requireLineResilience: true,
      durationSeconds: 1,
    });
    const worker = Object.freeze({
      id: "crossrepo-policy-worker",
      evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
      runtimePublicKeyDigest: d("crossrepo-policy-runtime"),
      topology: Object.freeze({
        attested: true,
        attestationDigest: d("crossrepo-policy-topology"),
        points: [0, 1, 2, 3, 4, 5],
        failurePoints: [],
      }),
      retainedUnionDeltaBytesByPolicy: {
        [executionPolicy.executionPolicyDigest]: executionPolicy.combinedBytes,
      },
      computePerSecondUSD: 0.01,
    });

    const tx = T.executeContinuationTransaction({
      candidates: [worker],
      request,
      obtainSignedVerifierVerdict: ({ challenge }) => A.signVerifierVerdict({
        provider: A.PROVIDER.SEV_SNP,
        challengeDigest: challenge.challengeDigest,
        launchMeasurement: d("crossrepo-policy-launch"),
        reportedTcbDigest: d("crossrepo-policy-tcb"),
        signerChainDigest: d("crossrepo-policy-chain"),
        hardwareBacked: true,
        vendorSignatureVerified: true,
        measurementPolicyVerified: true,
        tcbPolicyVerified: true,
        runtimeKeyBound: true,
        verifierKeyId: "crossrepo-policy-verifier",
      }, verifierKeys.privateKey),
      trustedVerifierPublicKey: verifierKeys.publicKey,
      executeWorker: () => execution,
      deliveryPrivateKey: deliveryKeys.privateKey,
      deliveryKeyId: "crossrepo-policy-delivery",
    });

    assert.equal(tx.dispatch.executionPolicyDigest, executionPolicy.executionPolicyDigest);
    assert.equal(tx.attestation.executionPolicyDigest, executionPolicy.executionPolicyDigest);
    assert.equal(tx.execution.executionDigest.startsWith("sha256:"), true);
    assert.equal(tx.delivery.body.executionPolicyDigest, executionPolicy.executionPolicyDigest);
    assert.equal(tx.delivery.body.parentContinuationRoot, execution.parentContinuationRoot);
    assert.equal(tx.delivery.body.childContinuationRoot, execution.childContinuationRoot);
    assert.equal(T.verifyDelivery(tx.delivery, deliveryKeys.publicKey).ok, true);
  });
}
