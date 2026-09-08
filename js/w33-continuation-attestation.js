"use strict";

// Continuation-bound measured-boot challenge for HoloVM process execution.
//
// The challenge commits the exact immutable continuation tuple and can also
// commit the exact W33 checkpoint/snapshot policy, the stricter baseline-aware
// joint-admission binding, topology attestation, and correlated-failure
// assessment selected for this dispatch. A hardware verdict therefore cannot
// be replayed across a different retention/admission decision or topology
// evidence snapshot on the same continuation.

const A = require("./w33-measured-boot-attestation.js");

const CHALLENGE_SCHEMA = "holotrade.w33-continuation-attestation-challenge.v1";
const BINDING_SCHEMA = "holotrade.w33-continuation-attestation-binding.v1";
const HARDWARE_EVIDENCE_SCHEMA = "holotrade.hardware-evidence.v1";

function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }
function optionalDigest(value, name) { if (value != null && !isDigest(value)) throw new TypeError(`${name} must be a sha256 content identity`); return value; }

function buildContinuationChallenge({
  passport,
  contract,
  runtimePublicKeyDigest,
  continuationRoot,
  processId,
  generation,
  executionPolicyDigest = null,
  strictAdmissionBindingDigest = null,
  topologyAttestationDigest = null,
  failureAssessmentDigest = null,
}) {
  if (!isDigest(continuationRoot)) throw new TypeError("continuationRoot must be a sha256 content identity");
  if (!isDigest(processId)) throw new TypeError("processId must be a sha256 content identity");
  natural(generation, "generation");
  optionalDigest(executionPolicyDigest, "executionPolicyDigest");
  optionalDigest(strictAdmissionBindingDigest, "strictAdmissionBindingDigest");
  optionalDigest(topologyAttestationDigest, "topologyAttestationDigest");
  optionalDigest(failureAssessmentDigest, "failureAssessmentDigest");
  if (strictAdmissionBindingDigest != null && executionPolicyDigest == null) throw new TypeError("strictAdmissionBindingDigest requires executionPolicyDigest");
  if (failureAssessmentDigest != null && topologyAttestationDigest == null) throw new TypeError("failureAssessmentDigest requires topologyAttestationDigest");

  const base = A.buildChallenge({ passport, contract, runtimePublicKeyDigest });
  const body = {
    schema: CHALLENGE_SCHEMA,
    baseChallengeDigest: base.challengeDigest,
    passportId: base.passportId,
    deploymentDigest: base.deploymentDigest,
    runtimePublicKeyDigest: base.runtimePublicKeyDigest,
    machineType: base.machineType,
    logicalDimension: base.logicalDimension,
    capabilityEpoch: base.capabilityEpoch,
    revocationRoot: base.revocationRoot,
    continuationRoot,
    processId,
    generation,
    ...(executionPolicyDigest == null ? {} : { executionPolicyDigest }),
    ...(strictAdmissionBindingDigest == null ? {} : { strictAdmissionBindingDigest }),
    ...(topologyAttestationDigest == null ? {} : { topologyAttestationDigest }),
    ...(failureAssessmentDigest == null ? {} : { failureAssessmentDigest }),
  };
  return Object.freeze({ ...body, challengeDigest: A.sha256(body) });
}

function verifiedContinuationBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  if (!challenge || challenge.schema !== CHALLENGE_SCHEMA) throw new TypeError("continuation-bound attestation challenge required");
  const verification = A.verifyVerifierVerdict(signedVerdict, challenge, trustedVerifierPublicKey, { requireHardware: true });
  if (!verification.ok) throw new Error(`refusing unattested HoloVM continuation: ${verification.code}`);
  if (challenge.passportId !== passport.passportId || challenge.deploymentDigest !== contract.deploymentDigest) throw new Error("continuation challenge does not bind this passport/deployment");
  if (!isDigest(challenge.continuationRoot) || !isDigest(challenge.processId)) throw new Error("continuation challenge lost process identity");
  natural(challenge.generation, "generation");
  optionalDigest(challenge.executionPolicyDigest, "executionPolicyDigest");
  optionalDigest(challenge.strictAdmissionBindingDigest, "strictAdmissionBindingDigest");
  optionalDigest(challenge.topologyAttestationDigest, "topologyAttestationDigest");
  optionalDigest(challenge.failureAssessmentDigest, "failureAssessmentDigest");
  if (challenge.strictAdmissionBindingDigest != null && challenge.executionPolicyDigest == null) throw new Error("continuation challenge lost policy parent for strict admission binding");
  if (challenge.failureAssessmentDigest != null && challenge.topologyAttestationDigest == null) throw new Error("continuation challenge lost topology parent for failure assessment");

  const body = {
    schema: BINDING_SCHEMA,
    passportId: challenge.passportId,
    deploymentDigest: challenge.deploymentDigest,
    runtimePublicKeyDigest: challenge.runtimePublicKeyDigest,
    baseChallengeDigest: challenge.baseChallengeDigest,
    challengeDigest: challenge.challengeDigest,
    continuationRoot: challenge.continuationRoot,
    processId: challenge.processId,
    generation: challenge.generation,
    ...(challenge.executionPolicyDigest == null ? {} : { executionPolicyDigest: challenge.executionPolicyDigest }),
    ...(challenge.strictAdmissionBindingDigest == null ? {} : { strictAdmissionBindingDigest: challenge.strictAdmissionBindingDigest }),
    ...(challenge.topologyAttestationDigest == null ? {} : { topologyAttestationDigest: challenge.topologyAttestationDigest }),
    ...(challenge.failureAssessmentDigest == null ? {} : { failureAssessmentDigest: challenge.failureAssessmentDigest }),
    provider: signedVerdict.body.provider,
    launchMeasurement: signedVerdict.body.launchMeasurement,
    reportedTcbDigest: signedVerdict.body.reportedTcbDigest,
    signerChainDigest: signedVerdict.body.signerChainDigest,
    verifierKeyId: signedVerdict.body.verifierKeyId,
    verifierVerdictDigest: verification.verdictDigest,
    hardwareBacked: true,
  };
  return Object.freeze({ ...body, bindingDigest: A.sha256(body) });
}

function attachContinuationReceiptMetadata(metadata, passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  const binding = verifiedContinuationBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey);
  return Object.freeze({ ...(metadata || {}), w33ContinuationAttestation: binding });
}

function toReceiptHardwareEvidence(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  const binding = verifiedContinuationBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey);
  const kind = binding.provider === A.PROVIDER.TPM2 ? "TPM_QUOTE" : "SEV_SNP_REPORT";
  const fullyScoped = binding.executionPolicyDigest || binding.strictAdmissionBindingDigest || binding.topologyAttestationDigest || binding.failureAssessmentDigest;
  return Object.freeze({
    schema: HARDWARE_EVIDENCE_SCHEMA,
    hardwareAttested: true,
    evidence: Object.freeze([Object.freeze({
      kind,
      status: "VERIFIED",
      reasonCode: fullyScoped ? "CONTINUATION_EXECUTION_CONTEXT_BOUND_SIGNED_VERIFIER_VERDICT" : "CONTINUATION_BOUND_SIGNED_VERIFIER_VERDICT",
      verifier: binding.verifierKeyId,
      digest: binding.verifierVerdictDigest,
      launchMeasurement: binding.launchMeasurement,
      reportedTcbDigest: binding.reportedTcbDigest,
      signerChainDigest: binding.signerChainDigest,
      challengeDigest: binding.challengeDigest,
      baseChallengeDigest: binding.baseChallengeDigest,
      passportId: binding.passportId,
      deploymentDigest: binding.deploymentDigest,
      runtimePublicKeyDigest: binding.runtimePublicKeyDigest,
      continuationRoot: binding.continuationRoot,
      processId: binding.processId,
      generation: binding.generation,
      ...(binding.executionPolicyDigest == null ? {} : { executionPolicyDigest: binding.executionPolicyDigest }),
      ...(binding.strictAdmissionBindingDigest == null ? {} : { strictAdmissionBindingDigest: binding.strictAdmissionBindingDigest }),
      ...(binding.topologyAttestationDigest == null ? {} : { topologyAttestationDigest: binding.topologyAttestationDigest }),
      ...(binding.failureAssessmentDigest == null ? {} : { failureAssessmentDigest: binding.failureAssessmentDigest }),
    })]),
  });
}

module.exports = { CHALLENGE_SCHEMA, BINDING_SCHEMA, HARDWARE_EVIDENCE_SCHEMA, buildContinuationChallenge, verifiedContinuationBinding, attachContinuationReceiptMetadata, toReceiptHardwareEvidence };
