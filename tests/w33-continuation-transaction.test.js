"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");

const A = require("../js/w33-measured-boot-attestation.js");
const C = require("../js/w33-continuation-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(label) { return S.sha256(label); }

function fixture() {
  const verifierKeys = crypto.generateKeyPairSync("ed25519");
  const deliveryKeys = crypto.generateKeyPairSync("ed25519");
  const deploymentDigest = d("deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("passport"),
    deploymentDigest,
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 11,
    revocationRoot: d("revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const continuationRoot = d("w33-parent-continuation");
  const processId = d("w33-process");
  const request = Object.freeze({
    continuationRoot,
    processId,
    generation: 7,
    passport,
    contract,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints: [0, 2, 31],
    durationSeconds: 1,
  });
  const worker = Object.freeze({
    id: "worker-A",
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d("runtime-worker-A"),
    topology: Object.freeze({
      attested: true,
      attestationDigest: d("topology-worker-A"),
      points: [0, 1, 2, 3, 31],
    }),
    retainedUnionDeltaBytes: { [continuationRoot]: 4096 },
    computePerSecondUSD: 0.01,
    startupUSD: 0,
  });
  return { verifierKeys, deliveryKeys, passport, contract, request, worker };
}

function signVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("launch"),
    reportedTcbDigest: d("tcb"),
    signerChainDigest: d("vcek-chain"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "transaction-fixture-verifier",
  }, privateKey);
}

function executionFor(request, overrides = {}) {
  return Object.freeze({
    schema: T.EXECUTION_SCHEMA,
    parentContinuationRoot: request.continuationRoot,
    childContinuationRoot: d("w33-child-continuation"),
    processId: request.processId,
    generationBefore: request.generation,
    generationAfter: request.generation + 1,
    emissionId: d("w33-emission"),
    guestReceiptIds: [d("guest-receipt-1")],
    stopReason: "fuel-exhausted",
    ...overrides,
  });
}

const policy = Object.freeze({ retainedByteSecondUSD: 1e-9, transferByteUSD: 1e-8 });

test("selection -> challenge -> verifier -> W33 execution -> signed delivery is one ordered transaction", () => {
  const f = fixture();
  const sequence = [];
  const tx = T.executeContinuationTransaction({
    candidates: [f.worker],
    request: f.request,
    policy,
    obtainSignedVerifierVerdict: ({ challenge, dispatch, request }) => {
      sequence.push("verifier");
      assert.equal(challenge.challengeDigest, dispatch.challenge.challengeDigest);
      assert.equal(challenge.continuationRoot, request.continuationRoot);
      return signVerdict(challenge, f.verifierKeys.privateKey);
    },
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    executeWorker: ({ dispatch, binding }) => {
      sequence.push("worker");
      assert.equal(binding.continuationRoot, f.request.continuationRoot);
      assert.equal(dispatch.workerId, f.worker.id);
      return executionFor(f.request);
    },
    deliveryPrivateKey: f.deliveryKeys.privateKey,
    deliveryKeyId: "fixture-delivery-key",
  });
  assert.deepEqual(sequence, ["verifier", "worker"]);
  assert.equal(tx.ok, true);
  assert.equal(tx.code, "CONTINUATION_TRANSACTION_COMMITTED");
  assert.equal(tx.execution.parentContinuationRoot, f.request.continuationRoot);
  assert.equal(tx.execution.processId, f.request.processId);
  assert.equal(tx.execution.generationAfter, 8);
  assert.equal(tx.delivery.body.childContinuationRoot, d("w33-child-continuation"));
  assert.equal(tx.delivery.body.attestationBindingDigest, tx.attestation.bindingDigest);
  const verified = T.verifyDelivery(tx.delivery, f.deliveryKeys.publicKey);
  assert.equal(verified.ok, true);
  assert.match(tx.transactionDigest, /^sha256:[0-9a-f]{64}$/);
});

test("a W33 receipt cannot drift parent, process, or generation", () => {
  const f = fixture();
  const preview = S.chooseContinuationWorker([f.worker], f.request, policy);
  const verdict = signVerdict(preview.dispatch.challenge, f.verifierKeys.privateKey);
  for (const overrides of [
    { parentContinuationRoot: d("wrong-parent") },
    { processId: d("wrong-process") },
    { generationBefore: 6 },
    { generationAfter: 7 },
  ]) {
    assert.throws(() => T.executeContinuationTransaction({
      candidates: [f.worker], request: f.request, policy,
      signedVerifierVerdict: verdict,
      trustedVerifierPublicKey: f.verifierKeys.publicKey,
      executeWorker: () => executionFor(f.request, overrides),
      deliveryPrivateKey: f.deliveryKeys.privateKey,
    }), /(drift|advance generation)/);
  }
});

test("signed delivery fails verification after child-continuation tampering", () => {
  const f = fixture();
  const tx = T.executeContinuationTransaction({
    candidates: [f.worker], request: f.request, policy,
    obtainSignedVerifierVerdict: ({ challenge }) => signVerdict(challenge, f.verifierKeys.privateKey),
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    executeWorker: () => executionFor(f.request),
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  });
  const tampered = {
    ...tx.delivery,
    body: { ...tx.delivery.body, childContinuationRoot: d("tampered-child") },
  };
  assert.equal(T.verifyDelivery(tampered, f.deliveryKeys.publicKey).ok, false);
});

test("verifier verdict for a different continuation cannot reach worker execution", () => {
  const f = fixture();
  let executed = false;
  assert.throws(() => T.executeContinuationTransaction({
    candidates: [f.worker], request: f.request, policy,
    obtainSignedVerifierVerdict: ({ challenge }) => {
      const otherChallenge = C.buildContinuationChallenge({
        passport: f.passport,
        contract: f.contract,
        runtimePublicKeyDigest: challenge.runtimePublicKeyDigest,
        continuationRoot: d("other-continuation"),
        processId: f.request.processId,
        generation: f.request.generation,
      });
      assert.notEqual(otherChallenge.challengeDigest, challenge.challengeDigest);
      return signVerdict(otherChallenge, f.verifierKeys.privateKey);
    },
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    executeWorker: () => { executed = true; return executionFor(f.request); },
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  }), /ATTESTATION_CHALLENGE_MISMATCH/);
  assert.equal(executed, false);
});
