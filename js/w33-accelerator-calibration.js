"use strict";

// Signed calibration-evidence ABI for W33 finite-control accelerators.
//
// This module does not manufacture calibration.  A future calibration authority
// signs measured transfer/error evidence for one exact W33 accelerator
// certificate and software calibration epoch.  Deployment policy supplies the
// acceptance thresholds.  CI fixtures are marked synthetic and cannot satisfy a
// physical-admission policy unless an explicit test-only override is supplied.

const crypto = require("node:crypto");
const A = require("./w33-measured-boot-attestation.js");
const X = require("./w33-accelerator-certificate.js");

const EVIDENCE_SCHEMA = "holotrade.w33-accelerator-calibration-evidence.v1";
const SIGNED_SCHEMA = "holotrade.w33-signed-accelerator-calibration.v1";
const CHALLENGE_SCHEMA = "holotrade.w33-calibrated-continuation-challenge.v1";
const BINDING_SCHEMA = "holotrade.w33-calibrated-continuation-binding.v1";

function isDigest(v) { return typeof v === "string" && /^sha256:[0-9a-f]{64}$/.test(v); }
function natural(v, name) { if (!Number.isSafeInteger(v) || v < 0) throw new RangeError(`${name} must be a natural number`); return v; }
function finiteNonnegative(v, name) { const n = Number(v); if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`); return n; }

function evidenceBody(raw) {
  if (!raw || typeof raw !== "object") throw new TypeError("calibration evidence body required");
  for (const name of ["acceleratorCertificateDigest", "deviceIdentityDigest", "measuredTransferMatrixDigest", "rawMeasurementSetDigest"]) {
    if (!isDigest(raw[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  }
  if (typeof raw.calibrationEpoch !== "string" || !raw.calibrationEpoch) throw new TypeError("calibrationEpoch required");
  if (typeof raw.sourceClass !== "string" || !raw.sourceClass) throw new TypeError("sourceClass required");
  if (typeof raw.calibrationAuthorityKeyId !== "string" || !raw.calibrationAuthorityKeyId) throw new TypeError("calibrationAuthorityKeyId required");
  const measuredAt = new Date(raw.measuredAt);
  if (!Number.isFinite(measuredAt.getTime())) throw new TypeError("measuredAt must be an ISO-compatible timestamp");
  const body = {
    schema: EVIDENCE_SCHEMA,
    acceleratorCertificateDigest: raw.acceleratorCertificateDigest,
    calibrationEpoch: raw.calibrationEpoch,
    deviceIdentityDigest: raw.deviceIdentityDigest,
    measuredTransferMatrixDigest: raw.measuredTransferMatrixDigest,
    rawMeasurementSetDigest: raw.rawMeasurementSetDigest,
    sampleCount: natural(raw.sampleCount, "sampleCount"),
    observedMaxInfidelityPpm: finiteNonnegative(raw.observedMaxInfidelityPpm, "observedMaxInfidelityPpm"),
    observedMaxLeakagePpm: finiteNonnegative(raw.observedMaxLeakagePpm, "observedMaxLeakagePpm"),
    measuredAt: measuredAt.toISOString(),
    sourceClass: raw.sourceClass,
    calibrationAuthorityKeyId: raw.calibrationAuthorityKeyId,
    syntheticFixture: raw.syntheticFixture === true,
  };
  return Object.freeze(body);
}

function signCalibrationEvidence(rawBody, privateKey) {
  const body = evidenceBody(rawBody);
  const calibrationEvidenceDigest = A.sha256(body);
  const signature = crypto.sign(null, Buffer.from(A.sha256({ body, calibrationEvidenceDigest })), privateKey).toString("base64");
  return Object.freeze({ schema: SIGNED_SCHEMA, body, calibrationEvidenceDigest, signature });
}

function verifyCalibrationEvidence(signed, acceleratorCertificate, trustedCalibrationPublicKey, policy = {}) {
  const cert = X.verifyAcceleratorCertificate(acceleratorCertificate);
  if (!signed || signed.schema !== SIGNED_SCHEMA || typeof signed.signature !== "string") throw new TypeError("signed accelerator calibration evidence required");
  const body = evidenceBody(signed.body);
  const digest = A.sha256(body);
  if (signed.calibrationEvidenceDigest !== digest) throw new Error("calibration evidence digest mismatch");
  const sigOk = crypto.verify(
    null,
    Buffer.from(A.sha256({ body, calibrationEvidenceDigest: digest })),
    trustedCalibrationPublicKey,
    Buffer.from(signed.signature, "base64")
  );
  if (!sigOk) throw new Error("calibration authority signature invalid");
  if (body.acceleratorCertificateDigest !== cert.acceleratorCertificateDigest) throw new Error("calibration evidence targets different accelerator certificate");
  if (body.calibrationEpoch !== cert.calibrationEpoch) throw new Error("calibration evidence epoch mismatch");

  const minSamples = natural(policy.minimumSamples == null ? 1 : policy.minimumSamples, "minimumSamples");
  const maxInfidelity = finiteNonnegative(policy.maxInfidelityPpm == null ? Number.MAX_SAFE_INTEGER : policy.maxInfidelityPpm, "maxInfidelityPpm");
  const maxLeakage = finiteNonnegative(policy.maxLeakagePpm == null ? Number.MAX_SAFE_INTEGER : policy.maxLeakagePpm, "maxLeakagePpm");
  if (body.sampleCount < minSamples) throw new Error("calibration sample floor unmet");
  if (body.observedMaxInfidelityPpm > maxInfidelity) throw new Error("calibration infidelity threshold exceeded");
  if (body.observedMaxLeakagePpm > maxLeakage) throw new Error("calibration leakage threshold exceeded");
  if (policy.requiredDeviceIdentityDigest != null && body.deviceIdentityDigest !== policy.requiredDeviceIdentityDigest) throw new Error("calibration device identity mismatch");

  const physicalSource = body.sourceClass === "hardware-measured" && body.syntheticFixture !== true;
  if (policy.requirePhysicalMeasurement === true && !physicalSource) throw new Error("physical accelerator admission requires non-synthetic hardware-measured calibration evidence");
  const testOnlySyntheticAccepted = body.syntheticFixture === true && policy.allowSyntheticFixtureForTest === true;
  if (body.syntheticFixture === true && !testOnlySyntheticAccepted && policy.requirePhysicalMeasurement !== true) throw new Error("synthetic calibration fixture requires explicit test-only override");

  const bindingBody = {
    schema: "holotrade.w33-accelerator-calibration-verification.v1",
    calibrationEvidenceDigest: digest,
    acceleratorCertificateDigest: cert.acceleratorCertificateDigest,
    calibrationEpoch: body.calibrationEpoch,
    deviceIdentityDigest: body.deviceIdentityDigest,
    measuredTransferMatrixDigest: body.measuredTransferMatrixDigest,
    rawMeasurementSetDigest: body.rawMeasurementSetDigest,
    sampleCount: body.sampleCount,
    observedMaxInfidelityPpm: body.observedMaxInfidelityPpm,
    observedMaxLeakagePpm: body.observedMaxLeakagePpm,
    calibrationAuthorityKeyId: body.calibrationAuthorityKeyId,
    physicalMeasurementAdmitted: physicalSource,
    syntheticTestFixtureAccepted: testOnlySyntheticAccepted,
  };
  return Object.freeze({ ...bindingBody, calibrationVerificationDigest: A.sha256(bindingBody), signedEvidence: signed });
}

function buildCalibratedChallenge(baseContinuationChallenge, calibrationVerification) {
  if (!baseContinuationChallenge || !isDigest(baseContinuationChallenge.challengeDigest)) throw new TypeError("base continuation challenge required");
  if (!calibrationVerification || !isDigest(calibrationVerification.calibrationVerificationDigest)) throw new TypeError("verified calibration context required");
  if ((baseContinuationChallenge.acceleratorCertificateDigest || null) !== calibrationVerification.acceleratorCertificateDigest) throw new Error("base continuation challenge and calibration target different accelerator certificates");
  const body = {
    schema: CHALLENGE_SCHEMA,
    baseContinuationChallengeDigest: baseContinuationChallenge.challengeDigest,
    acceleratorCertificateDigest: calibrationVerification.acceleratorCertificateDigest,
    calibrationEvidenceDigest: calibrationVerification.calibrationEvidenceDigest,
    calibrationVerificationDigest: calibrationVerification.calibrationVerificationDigest,
    calibrationEpoch: calibrationVerification.calibrationEpoch,
    deviceIdentityDigest: calibrationVerification.deviceIdentityDigest,
    measuredTransferMatrixDigest: calibrationVerification.measuredTransferMatrixDigest,
    rawMeasurementSetDigest: calibrationVerification.rawMeasurementSetDigest,
    physicalMeasurementAdmitted: calibrationVerification.physicalMeasurementAdmitted,
  };
  return Object.freeze({ ...body, challengeDigest: A.sha256(body) });
}

function verifyCalibratedRuntimeBinding(calibratedChallenge, signedVerifierVerdict, trustedRuntimeVerifierPublicKey) {
  const verification = A.verifyVerifierVerdict(signedVerifierVerdict, calibratedChallenge, trustedRuntimeVerifierPublicKey, { requireHardware: true });
  if (!verification.ok) throw new Error(`refusing unbound calibrated accelerator runtime: ${verification.code}`);
  const body = {
    schema: BINDING_SCHEMA,
    challengeDigest: calibratedChallenge.challengeDigest,
    baseContinuationChallengeDigest: calibratedChallenge.baseContinuationChallengeDigest,
    acceleratorCertificateDigest: calibratedChallenge.acceleratorCertificateDigest,
    calibrationEvidenceDigest: calibratedChallenge.calibrationEvidenceDigest,
    calibrationVerificationDigest: calibratedChallenge.calibrationVerificationDigest,
    calibrationEpoch: calibratedChallenge.calibrationEpoch,
    deviceIdentityDigest: calibratedChallenge.deviceIdentityDigest,
    measuredTransferMatrixDigest: calibratedChallenge.measuredTransferMatrixDigest,
    rawMeasurementSetDigest: calibratedChallenge.rawMeasurementSetDigest,
    physicalMeasurementAdmitted: calibratedChallenge.physicalMeasurementAdmitted,
    provider: signedVerifierVerdict.body.provider,
    verifierKeyId: signedVerifierVerdict.body.verifierKeyId,
    verifierVerdictDigest: verification.verdictDigest,
    hardwareBacked: true,
  };
  return Object.freeze({ ...body, calibratedBindingDigest: A.sha256(body) });
}

module.exports = {
  EVIDENCE_SCHEMA, SIGNED_SCHEMA, CHALLENGE_SCHEMA, BINDING_SCHEMA,
  evidenceBody, signCalibrationEvidence, verifyCalibrationEvidence,
  buildCalibratedChallenge, verifyCalibratedRuntimeBinding,
};
