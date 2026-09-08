"use strict";

// Additive calibrated-accelerator transaction path.
//
// Existing software-equivalence accelerator transactions remain unchanged.
// This path first obtains the ordinary continuation/accelerator dispatch, then
// verifies calibration-authority evidence and builds a nested measured-boot
// challenge whose parent is the exact ordinary continuation challenge.  The
// runtime verifier therefore attests continuation + process + topology + policy
// + accelerator certificate + calibration evidence in one transitive digest.

const S = require("./w33-continuation-scheduler.js");
const T = require("./w33-continuation-transaction.js");
const Cal = require("../js/w33-accelerator-calibration.js");

function executeCalibratedAcceleratorTransaction({
  candidates,
  request,
  policy = {},
  signedCalibrationEvidence,
  trustedCalibrationPublicKey,
  calibrationPolicy = {},
  obtainSignedVerifierVerdict,
  trustedRuntimeVerifierPublicKey,
  executeWorker,
  deliveryPrivateKey,
  deliveryKeyId = "holotrade-calibrated-delivery",
}) {
  if (!request || !request.acceleratorCertificate) throw new TypeError("calibrated transaction requires full accelerator certificate");
  if (typeof obtainSignedVerifierVerdict !== "function") throw new TypeError("runtime verifier callback required");
  if (typeof executeWorker !== "function") throw new TypeError("executeWorker callback required");

  const selected = S.chooseContinuationWorker(candidates, request, policy);
  if (!selected.ok) throw new Error(selected.code);
  const dispatch = selected.dispatch;
  const normalizedRequest = selected.ranked.request;
  const selectedCandidate = (candidates || []).find((c) => String(c.id) === dispatch.workerId);
  if (!selectedCandidate) throw new Error("selected worker disappeared before calibrated transaction");
  if (!selectedCandidate.acceleratorDeviceIdentityDigest) throw new Error("calibrated accelerator worker must declare acceleratorDeviceIdentityDigest");

  const verification = Cal.verifyCalibrationEvidence(
    signedCalibrationEvidence,
    normalizedRequest.acceleratorCertificate,
    trustedCalibrationPublicKey,
    { ...calibrationPolicy, requiredDeviceIdentityDigest: selectedCandidate.acceleratorDeviceIdentityDigest },
  );
  const calibratedChallenge = Cal.buildCalibratedChallenge(dispatch.challenge, verification);
  const verdict = obtainSignedVerifierVerdict(Object.freeze({
    challenge: calibratedChallenge,
    baseContinuationChallenge: dispatch.challenge,
    dispatch,
    request: normalizedRequest,
    calibration: verification,
  }));
  if (!verdict) throw new TypeError("runtime verifier callback returned no signed verdict");
  const calibratedBinding = Cal.verifyCalibratedRuntimeBinding(calibratedChallenge, verdict, trustedRuntimeVerifierPublicKey);

  const rawExecution = executeWorker(Object.freeze({
    dispatch,
    calibratedBinding,
    calibration: verification,
    request: normalizedRequest,
  }));
  const execution = T.normalizeExecution(rawExecution, normalizedRequest);
  T.acceleratorExecutionAgreement(normalizedRequest, execution);

  const body = {
    schema: T.DELIVERY_SCHEMA,
    dispatchDigest: dispatch.dispatchDigest,
    workerId: dispatch.workerId,
    attestationBindingDigest: calibratedBinding.calibratedBindingDigest,
    verifierVerdictDigest: calibratedBinding.verifierVerdictDigest,
    runtimePublicKeyDigest: dispatch.runtimePublicKeyDigest,
    topologyAttestationDigest: dispatch.topologyAttestationDigest,
    ...(dispatch.failureAssessmentDigest == null ? {} : { failureAssessmentDigest: dispatch.failureAssessmentDigest }),
    ...(dispatch.executionPolicyDigest == null ? {} : { executionPolicyDigest: dispatch.executionPolicyDigest }),
    acceleratorCertificateDigest: normalizedRequest.acceleratorCertificateDigest,
    acceleratorCalibrationEvidenceDigest: verification.calibrationEvidenceDigest,
    acceleratorCalibrationVerificationDigest: verification.calibrationVerificationDigest,
    acceleratorCalibrationEpoch: verification.calibrationEpoch,
    acceleratorDeviceIdentityDigest: verification.deviceIdentityDigest,
    measuredTransferMatrixDigest: verification.measuredTransferMatrixDigest,
    rawMeasurementSetDigest: verification.rawMeasurementSetDigest,
    observedMaxInfidelityPpm: verification.observedMaxInfidelityPpm,
    observedMaxLeakagePpm: verification.observedMaxLeakagePpm,
    calibrationSampleCount: verification.sampleCount,
    physicalMeasurementAdmitted: verification.physicalMeasurementAdmitted,
    baseAttestationChallengeDigest: dispatch.challenge.challengeDigest,
    calibratedAttestationChallengeDigest: calibratedChallenge.challengeDigest,
    parentContinuationRoot: execution.parentContinuationRoot,
    childContinuationRoot: execution.childContinuationRoot,
    processId: execution.processId,
    generationBefore: execution.generationBefore,
    generationAfter: execution.generationAfter,
    emissionId: execution.emissionId,
    guestReceiptIds: execution.guestReceiptIds,
    ...(execution.intermediateContinuationRoots == null ? {} : { intermediateContinuationRoots: execution.intermediateContinuationRoots }),
    executionDigest: execution.executionDigest,
  };
  const delivery = Object.freeze({ ...body, deliveryDigest: T.sha256(body) });
  const signedDelivery = T.signDelivery(delivery, deliveryPrivateKey, deliveryKeyId);
  return Object.freeze({
    ok: true,
    code: verification.physicalMeasurementAdmitted ? "PHYSICALLY_CALIBRATED_ACCELERATOR_TRANSACTION_COMMITTED" : "CALIBRATION_INTERFACE_TRANSACTION_COMMITTED",
    dispatch,
    calibration: verification,
    calibratedChallenge,
    attestation: calibratedBinding,
    execution,
    delivery: signedDelivery,
    transactionDigest: T.sha256({
      dispatchDigest: dispatch.dispatchDigest,
      calibrationVerificationDigest: verification.calibrationVerificationDigest,
      calibratedBindingDigest: calibratedBinding.calibratedBindingDigest,
      executionDigest: execution.executionDigest,
      signedReceiptDigest: signedDelivery.signedReceiptDigest,
    }),
  });
}

module.exports = { executeCalibratedAcceleratorTransaction };
