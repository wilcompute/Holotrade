"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(label) { return S.sha256(label); }

function signedVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("crossrepo-launch"),
    reportedTcbDigest: d("crossrepo-tcb"),
    signerChainDigest: d("crossrepo-vcek-chain"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "crossrepo-verifier",
  }, privateKey);
}

test("Holotrade commits a signed transaction around a receipt emitted by the W33 process kernel", () => {
  const path = process.env.W33_EXECUTION_FIXTURE;
  assert.ok(path, "W33_EXECUTION_FIXTURE must point to generated W33 JSON");
  const execution = JSON.parse(fs.readFileSync(path, "utf8"));
  assert.equal(execution.schema, T.EXECUTION_SCHEMA);
  const verifierKeys = crypto.generateKeyPairSync("ed25519");
  const deliveryKeys = crypto.generateKeyPairSync("ed25519");
  const deploymentDigest = d("crossrepo-deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("crossrepo-passport"),
    deploymentDigest,
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 1,
    revocationRoot: d("crossrepo-revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const request = Object.freeze({
    continuationRoot: execution.parentContinuationRoot,
    processId: execution.processId,
    generation: execution.generationBefore,
    passport,
    contract,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints: [0],
    durationSeconds: 1,
  });
  const worker = Object.freeze({
    id: "crossrepo-worker",
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d("crossrepo-runtime"),
    topology: Object.freeze({ attested: true, attestationDigest: d("crossrepo-topology"), points: [0, 1, 2, 3] }),
    retainedUnionDeltaBytes: { [request.continuationRoot]: 0 },
    computePerSecondUSD: 0,
    startupUSD: 0,
  });
  const preview = S.chooseContinuationWorker([worker], request, {});
  assert.equal(preview.ok, true);
  const verdict = signedVerdict(preview.dispatch.challenge, verifierKeys.privateKey);
  const tx = T.executeContinuationTransaction({
    candidates: [worker], request,
    signedVerifierVerdict: verdict,
    trustedVerifierPublicKey: verifierKeys.publicKey,
    executeWorker: () => execution,
    deliveryPrivateKey: deliveryKeys.privateKey,
    deliveryKeyId: "crossrepo-delivery",
  });
  assert.equal(tx.execution.executionDigest.startsWith("sha256:"), true);
  assert.equal(tx.delivery.body.emissionId, execution.emissionId);
  assert.deepEqual(tx.delivery.body.guestReceiptIds, execution.guestReceiptIds);
  assert.equal(tx.delivery.body.childContinuationRoot, execution.childContinuationRoot);
  assert.equal(T.verifyDelivery(tx.delivery, deliveryKeys.publicKey).ok, true);
});
