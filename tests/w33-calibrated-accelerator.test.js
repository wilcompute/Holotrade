"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");

const A = require("../js/w33-measured-boot-attestation.js");
const X = require("../js/w33-accelerator-certificate.js");
const Cal = require("../js/w33-accelerator-calibration.js");
const D = require("../js/w33-passport-deployment.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");
const CT = require("../scheduler/w33-calibrated-accelerator-transaction.js");

function d(x) { return S.sha256(x); }
function loadCert() {
  const path = process.env.W33_ACCELERATOR_CERTIFICATE;
  if (!path) throw new Error("W33_ACCELERATOR_CERTIFICATE is required");
  return X.verifyAcceleratorCertificate(JSON.parse(fs.readFileSync(path, "utf8")));
}
function runtimeVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("calibrated-launch"),
    reportedTcbDigest: d("calibrated-tcb"),
    signerChainDigest: d("calibrated-vcek"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "calibrated-runtime-verifier",
  }, privateKey);
}
function fixture(cert) {
  const runtimeKeys = crypto.generateKeyPairSync("ed25519");
  const calibrationKeys = crypto.generateKeyPairSync("ed25519");
  const deliveryKeys = crypto.generateKeyPairSync("ed25519");
  const deviceIdentityDigest = d("fixture-optical-device");
  const deploymentDigest = d("calibrated-deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("calibrated-passport"),
    deploymentDigest,
    machineType: cert.machineType,
    logicalDimension: 81,
    capabilityEpoch: 31,
    revocationRoot: d("calibrated-revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const request = Object.freeze({
    continuationRoot: cert.parentContinuationRoot,
    processId: cert.processId,
    generation: cert.generationBefore,
    passport, contract,
    acceleratorCertificate: cert,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    durationSeconds: 1,
  });
  const worker = Object.freeze({
    id: "calibrated-worker",
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d("calibrated-runtime-key"),
    acceleratorDeviceIdentityDigest: deviceIdentityDigest,
    topology: Object.freeze({ attested: true, attestationDigest: d("calibrated-topology"), points: Array.from({ length: 40 }, (_, i) => i), failurePoints: [] }),
    retainedUnionDeltaBytes: { [cert.parentContinuationRoot]: 0 },
    computePerSecondUSD: 0.01,
  });
  const evidenceBody = {
    acceleratorCertificateDigest: cert.acceleratorCertificateDigest,
    calibrationEpoch: cert.calibrationEpoch,
    deviceIdentityDigest,
    measuredTransferMatrixDigest: d("synthetic-transfer-matrix"),
    rawMeasurementSetDigest: d("synthetic-measurement-set"),
    sampleCount: 4096,
    observedMaxInfidelityPpm: 120,
    observedMaxLeakagePpm: 40,
    measuredAt: "2026-09-08T00:00:00.000Z",
    sourceClass: "ci-synthetic",
    syntheticFixture: true,
    calibrationAuthorityKeyId: "ci-calibration-authority",
  };
  const signedCalibrationEvidence = Cal.signCalibrationEvidence(evidenceBody, calibrationKeys.privateKey);
  return { runtimeKeys, calibrationKeys, deliveryKeys, deviceIdentityDigest, passport, contract, request, worker, signedCalibrationEvidence, evidenceBody };
}
function certifiedExecution(cert, overrides = {}) {
  return Object.freeze({
    schema: T.EXECUTION_SCHEMA,
    parentContinuationRoot: cert.parentContinuationRoot,
    childContinuationRoot: cert.childContinuationRoot,
    processId: cert.processId,
    generationBefore: cert.generationBefore,
    generationAfter: cert.generationAfter,
    emissionId: d("calibrated-emission"),
    guestReceiptIds: [...cert.subreceiptIds],
    intermediateContinuationRoots: [...cert.intermediateContinuationRoots],
    stopReason: "calibrated-interface-window-complete",
    ...overrides,
  });
}

test("synthetic CI calibration can exercise ABI but cannot satisfy physical admission", () => {
  const cert = loadCert(); const f = fixture(cert);
  const ok = Cal.verifyCalibrationEvidence(f.signedCalibrationEvidence, cert, f.calibrationKeys.publicKey, {
    allowSyntheticFixtureForTest: true,
    minimumSamples: 1000,
    maxInfidelityPpm: 500,
    maxLeakagePpm: 100,
    requiredDeviceIdentityDigest: f.deviceIdentityDigest,
  });
  assert.equal(ok.syntheticTestFixtureAccepted, true);
  assert.equal(ok.physicalMeasurementAdmitted, false);
  assert.throws(() => Cal.verifyCalibrationEvidence(f.signedCalibrationEvidence, cert, f.calibrationKeys.publicKey, {
    requirePhysicalMeasurement: true,
    minimumSamples: 1000,
    maxInfidelityPpm: 500,
    maxLeakagePpm: 100,
  }), /requires non-synthetic hardware-measured/);
});

test("calibration evidence is nested into measured boot and verdict cannot replay across changed evidence", () => {
  const cert = loadCert(); const f = fixture(cert);
  const selected = S.chooseContinuationWorker([f.worker], f.request);
  assert.equal(selected.ok, true);
  const v1 = Cal.verifyCalibrationEvidence(f.signedCalibrationEvidence, cert, f.calibrationKeys.publicKey, { allowSyntheticFixtureForTest: true });
  const c1 = Cal.buildCalibratedChallenge(selected.dispatch.challenge, v1);
  const signed1 = runtimeVerdict(c1, f.runtimeKeys.privateKey);
  const b1 = Cal.verifyCalibratedRuntimeBinding(c1, signed1, f.runtimeKeys.publicKey);
  assert.equal(b1.calibrationEvidenceDigest, v1.calibrationEvidenceDigest);

  const changedSigned = Cal.signCalibrationEvidence({ ...f.evidenceBody, measuredTransferMatrixDigest: d("different-transfer-matrix") }, f.calibrationKeys.privateKey);
  const v2 = Cal.verifyCalibrationEvidence(changedSigned, cert, f.calibrationKeys.publicKey, { allowSyntheticFixtureForTest: true });
  const c2 = Cal.buildCalibratedChallenge(selected.dispatch.challenge, v2);
  assert.notEqual(c1.challengeDigest, c2.challengeDigest);
  assert.throws(() => Cal.verifyCalibratedRuntimeBinding(c2, signed1, f.runtimeKeys.publicKey), /ATTESTATION_CHALLENGE_MISMATCH/);
});

test("calibration-interface transaction preserves exact accelerator receipt interval in signed delivery", () => {
  const cert = loadCert(); const f = fixture(cert);
  const tx = CT.executeCalibratedAcceleratorTransaction({
    candidates: [f.worker],
    request: f.request,
    signedCalibrationEvidence: f.signedCalibrationEvidence,
    trustedCalibrationPublicKey: f.calibrationKeys.publicKey,
    calibrationPolicy: { allowSyntheticFixtureForTest: true, minimumSamples: 1000, maxInfidelityPpm: 500, maxLeakagePpm: 100 },
    obtainSignedVerifierVerdict: ({ challenge }) => runtimeVerdict(challenge, f.runtimeKeys.privateKey),
    trustedRuntimeVerifierPublicKey: f.runtimeKeys.publicKey,
    executeWorker: () => certifiedExecution(cert),
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  });
  assert.equal(tx.ok, true);
  assert.equal(tx.code, "CALIBRATION_INTERFACE_TRANSACTION_COMMITTED");
  assert.equal(tx.delivery.body.physicalMeasurementAdmitted, false);
  assert.equal(tx.delivery.body.acceleratorCertificateDigest, cert.acceleratorCertificateDigest);
  assert.equal(tx.delivery.body.acceleratorCalibrationEvidenceDigest, tx.calibration.calibrationEvidenceDigest);
  assert.deepEqual(tx.execution.guestReceiptIds, cert.subreceiptIds);
  assert.deepEqual(tx.execution.intermediateContinuationRoots, cert.intermediateContinuationRoots);
  assert.equal(T.verifyDelivery(tx.delivery, f.deliveryKeys.publicKey).ok, true);

  const bad = [...cert.subreceiptIds]; bad[0] = d("calibrated-wrong-receipt");
  assert.throws(() => CT.executeCalibratedAcceleratorTransaction({
    candidates: [f.worker], request: f.request,
    signedCalibrationEvidence: f.signedCalibrationEvidence,
    trustedCalibrationPublicKey: f.calibrationKeys.publicKey,
    calibrationPolicy: { allowSyntheticFixtureForTest: true },
    obtainSignedVerifierVerdict: ({ challenge }) => runtimeVerdict(challenge, f.runtimeKeys.privateKey),
    trustedRuntimeVerifierPublicKey: f.runtimeKeys.publicKey,
    executeWorker: () => certifiedExecution(cert, { guestReceiptIds: bad }),
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  }), /receipt interval disagrees/);
});
