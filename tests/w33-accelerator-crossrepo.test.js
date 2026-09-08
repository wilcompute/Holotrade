"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const C = require("../js/w33-continuation-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const X = require("../js/w33-accelerator-certificate.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(x) { return S.sha256(x); }
function loadCertificate() {
  const path = process.env.W33_ACCELERATOR_CERTIFICATE;
  if (!path) throw new Error("W33_ACCELERATOR_CERTIFICATE is required");
  return JSON.parse(fs.readFileSync(path, "utf8"));
}
function signVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("accelerator-launch"),
    reportedTcbDigest: d("accelerator-tcb"),
    signerChainDigest: d("accelerator-vcek"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "accelerator-fixture-verifier",
  }, privateKey);
}
function fixture(cert) {
  const verifierKeys = crypto.generateKeyPairSync("ed25519");
  const deliveryKeys = crypto.generateKeyPairSync("ed25519");
  const deploymentDigest = d("accelerator-deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("accelerator-passport"),
    deploymentDigest,
    machineType: cert.machineType,
    logicalDimension: 81,
    capabilityEpoch: 23,
    revocationRoot: d("accelerator-revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const request = Object.freeze({
    continuationRoot: cert.parentContinuationRoot,
    processId: cert.processId,
    generation: cert.generationBefore,
    passport,
    contract,
    acceleratorCertificate: cert,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    durationSeconds: 1,
  });
  const worker = Object.freeze({
    id: "accelerator-worker",
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d("accelerator-runtime-key"),
    topology: Object.freeze({ attested: true, attestationDigest: d("accelerator-topology"), points: Array.from({ length: 40 }, (_, i) => i), failurePoints: [] }),
    retainedUnionDeltaBytes: { [cert.parentContinuationRoot]: 0 },
    computePerSecondUSD: 0.01,
  });
  return { verifierKeys, deliveryKeys, passport, contract, request, worker };
}
function certifiedExecution(cert, overrides = {}) {
  return Object.freeze({
    schema: T.EXECUTION_SCHEMA,
    parentContinuationRoot: cert.parentContinuationRoot,
    childContinuationRoot: cert.childContinuationRoot,
    processId: cert.processId,
    generationBefore: cert.generationBefore,
    generationAfter: cert.generationAfter,
    emissionId: d("accelerator-emission"),
    guestReceiptIds: [...cert.subreceiptIds],
    intermediateContinuationRoots: [...cert.intermediateContinuationRoots],
    stopReason: "accelerator-window-complete",
    ...overrides,
  });
}

test("real W33 accelerator certificate is hardware-bound and carried through signed delivery", () => {
  const raw = loadCertificate();
  const cert = X.verifyAcceleratorCertificate(raw);
  const f = fixture(cert);
  const tx = T.executeContinuationTransaction({
    candidates: [f.worker],
    request: f.request,
    obtainSignedVerifierVerdict: ({ challenge }) => signVerdict(challenge, f.verifierKeys.privateKey),
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    executeWorker: () => certifiedExecution(cert),
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  });
  assert.equal(tx.ok, true);
  assert.equal(tx.dispatch.acceleratorCertificateDigest, cert.acceleratorCertificateDigest);
  assert.equal(tx.attestation.acceleratorCertificateDigest, cert.acceleratorCertificateDigest);
  assert.equal(tx.delivery.body.acceleratorCertificateDigest, cert.acceleratorCertificateDigest);
  assert.equal(tx.delivery.body.acceleratorReceiptChainDigest, cert.receiptChainDigest);
  assert.equal(tx.delivery.body.acceleratorContinuationChainDigest, cert.continuationChainDigest);
  assert.deepEqual(tx.execution.guestReceiptIds, cert.subreceiptIds);
  assert.deepEqual(tx.execution.intermediateContinuationRoots, cert.intermediateContinuationRoots);
  assert.equal(T.verifyDelivery(tx.delivery, f.deliveryKeys.publicKey).ok, true);
  assert.equal(cert.physicalCalibrationEvidenceDigest, null);
});

test("same process with a different accelerator certificate changes hardware challenge and blocks verdict replay", () => {
  const raw = loadCertificate();
  const cert = X.verifyAcceleratorCertificate(raw);
  const f = fixture(cert);
  const selectedA = S.chooseContinuationWorker([f.worker], f.request);
  assert.equal(selectedA.ok, true);
  const signedA = signVerdict(selectedA.dispatch.challenge, f.verifierKeys.privateKey);

  const changedBody = { ...raw, calibrationEpoch: raw.calibrationEpoch + "-changed" };
  delete changedBody.acceleratorCertificateDigest;
  const changed = X.verifyAcceleratorCertificate({ ...changedBody, acceleratorCertificateDigest: X.sha256(changedBody) });
  const requestB = { ...f.request, acceleratorCertificate: changed };
  const selectedB = S.chooseContinuationWorker([f.worker], requestB);
  assert.equal(selectedB.ok, true);
  assert.notEqual(selectedA.dispatch.acceleratorCertificateDigest, selectedB.dispatch.acceleratorCertificateDigest);
  assert.notEqual(selectedA.dispatch.attestationChallengeDigest, selectedB.dispatch.attestationChallengeDigest);
  assert.throws(() => C.verifiedContinuationBinding(f.passport, f.contract, selectedB.dispatch.challenge, signedA, f.verifierKeys.publicKey), /ATTESTATION_CHALLENGE_MISMATCH/);
});

test("attested accelerator cannot return a different receipt or continuation interval", () => {
  const cert = X.verifyAcceleratorCertificate(loadCertificate());
  const f = fixture(cert);
  const args = {
    candidates: [f.worker],
    request: f.request,
    obtainSignedVerifierVerdict: ({ challenge }) => signVerdict(challenge, f.verifierKeys.privateKey),
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  };
  const badReceipts = [...cert.subreceiptIds]; badReceipts[0] = d("substituted-receipt");
  assert.throws(() => T.executeContinuationTransaction({ ...args, executeWorker: () => certifiedExecution(cert, { guestReceiptIds: badReceipts }) }), /receipt interval disagrees/);
  const badRoots = [...cert.intermediateContinuationRoots]; badRoots[0] = d("substituted-continuation");
  assert.throws(() => T.executeContinuationTransaction({ ...args, executeWorker: () => certifiedExecution(cert, { intermediateContinuationRoots: badRoots }) }), /continuation interval disagrees/);
  assert.throws(() => T.executeContinuationTransaction({ ...args, executeWorker: () => certifiedExecution(cert, { childContinuationRoot: d("wrong-child") }) }), /child disagrees/);
});
