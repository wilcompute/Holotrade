"use strict";

// Continuation-bound measured-boot challenge for HoloVM process execution.
//
// The challenge commits the exact immutable continuation tuple and, when one is
// selected, the exact W33 checkpoint/snapshot execution-policy digest. This
// prevents a signed hardware verdict for one retention/recovery policy from
// being replayed for a different policy on the same continuation.
//
// No vendor evidence is parsed here; TPM2/SEV-SNP verification remains owned by
// w33-native-attestation.js and w33-measured-boot-attestation.js.

const A = require("./w33-measured-boot-attestation.js");

const CHALLENGE_SCHEMA = "holotrade.w33-continuation-attestation-challenge.v1";
const BINDING_SCHEMA = "holotrade.w33-continuation-attestation-binding.v1";
const HARDWARE_EVIDENCE_SCHEMA = "holotrade.hardware-evidence.v1";

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function natural(value, name) {
  if (!Number.isInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`);
  return value;
}

function buildContinuationChallenge({
  passport,
  contract,
  runtimePublicKeyDigest,
  continuationRoot,
  processId,
  generation,
  executionPolicyDigest = null,
}) {
  if (!isDigest(continuationRoot)) throw new TypeError("continuationRoot must be a sha256 content identity");
  if (!isDigest(processId)) throw new TypeError("processId must be a sha256 content identity");
  natural(generation, "generation");
  if (executionPolicyDigest != null && !isDigest(executionPolicyDigest)) {
    throw new TypeError("executionPolicyDigest must be a sha256 content identity");
  }

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
  };
  return Object.freeze({ ...body, challengeDigest: A.sha256(body) });
}

function verifiedContinuationBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  if (!challenge || challenge.schema !== CHALLENGE_SCHEMA) throw new TypeError("continuation-bound attestation challenge required");
  const verification = A.verifyVerifierVerdict(signedVerdict, challenge, trustedVerifierPublicKey, { requireHardware: true });
  if (!verification.ok) throw new Error(`refusing unattested HoloVM continuation: ${verification.code}`);
  if (challenge.passportId !== passport.passportId || challenge.deploymentDigest !== contract.deploymentDigest) {
    throw new Error("continuation challenge does not bind this passport/deployment");
  }
  if (!isDigest(challenge.continuationRoot) || !isDigest(challenge.processId)) throw new Error("continuation challenge lost process identity");
  natural(challenge.generation, "generation");
  if (challenge.executionPolicyDigest != null && !isDigest(challenge.executionPolicyDigest)) {
    throw new Error("continuation challenge lost execution policy identity");
  }

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
  return Object.freeze({
    schema: HARDWARE_EVIDENCE_SCHEMA,
    hardwareAttested: true,
    evidence: Object.freeze([
      Object.freeze({
        kind,
        status: "VERIFIED",
        reasonCode: binding.executionPolicyDigest ? "CONTINUATION_AND_POLICY_BOUND_SIGNED_VERIFIER_VERDICT" : "CONTINUATION_BOUND_SIGNED_VERIFIER_VERDICT",
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
      }),
    ]),
  });
}

module.exports = {
  CHALLENGE_SCHEMA,
  BINDING_SCHEMA,
  HARDWARE_EVIDENCE_SCHEMA,
  buildContinuationChallenge,
  verifiedContinuationBinding,
  attachContinuationReceiptMetadata,
  toReceiptHardwareEvidence,
};
