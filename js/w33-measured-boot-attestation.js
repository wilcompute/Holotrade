// W33 measured-boot / confidential-VM attestation binding.
//
// This module deliberately separates two trust layers:
//   1. a hardware/vendor-specific verifier evaluates TPM2 quotes/PCR logs or
//      AMD SEV-SNP reports; and
//   2. Holotrade verifies an Ed25519-signed *normalized verifier verdict* that
//      binds that hardware evidence to the exact W33 execution passport,
//      GoMicroVM deployment digest, and runtime public key.
//
// Holotrade does not parse AMD certificates, TPM event logs, VCEKs, or quotes
// here. A verdict can be called hardware-backed only when the trusted external
// verifier says the vendor signature, measurement policy, TCB policy, and
// runtime-key binding all passed. The verified normalized result can then be
// inserted both into receipt metadata and into the generic receipt hardware-
// evidence field before the receipt is COSE/Ed25519 signed.

"use strict";

const crypto = require("node:crypto");
const D = require("./w33-passport-deployment.js");

const PROVIDER = Object.freeze({ TPM2: "TPM2", SEV_SNP: "SEV_SNP" });
const VERDICT_SCHEMA = "holotrade.w33-attestation-verdict.v1";
const BINDING_SCHEMA = "holotrade.w33-measured-boot-binding.v1";
const HARDWARE_EVIDENCE_SCHEMA = "holotrade.hardware-evidence.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;
}

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function buildChallenge({ passport, contract, runtimePublicKeyDigest }) {
  if (!passport || passport.schema !== D.SCHEMA || !isDigest(passport.passportId)) {
    throw new TypeError("valid W33 execution passport required");
  }
  if (!contract || !isDigest(contract.deploymentDigest)) {
    throw new TypeError("GoMicroVM deployment digest required");
  }
  if (passport.deploymentDigest !== contract.deploymentDigest) {
    throw new Error("passport and GoMicroVM deployment digest disagree");
  }
  if (!isDigest(runtimePublicKeyDigest)) throw new TypeError("runtime public key digest required");
  const body = {
    schema: "holotrade.w33-attestation-challenge.v1",
    passportId: passport.passportId,
    deploymentDigest: contract.deploymentDigest,
    runtimePublicKeyDigest,
    machineType: passport.machineType,
    logicalDimension: passport.logicalDimension,
    capabilityEpoch: passport.capabilityEpoch,
    revocationRoot: passport.revocationRoot,
  };
  return Object.freeze({ ...body, challengeDigest: sha256(body) });
}

function verdictBody({
  provider,
  challengeDigest,
  launchMeasurement,
  reportedTcbDigest,
  signerChainDigest,
  hardwareBacked,
  vendorSignatureVerified,
  measurementPolicyVerified,
  tcbPolicyVerified,
  runtimeKeyBound,
  verifierKeyId,
}) {
  if (!Object.values(PROVIDER).includes(provider)) throw new TypeError("unknown attestation provider");
  for (const [name, value] of Object.entries({ challengeDigest, launchMeasurement, reportedTcbDigest, signerChainDigest })) {
    if (!isDigest(value)) throw new TypeError(`${name} must be sha256 content identity`);
  }
  if (!verifierKeyId) throw new TypeError("verifierKeyId required");
  return Object.freeze({
    schema: VERDICT_SCHEMA,
    provider,
    challengeDigest,
    launchMeasurement,
    reportedTcbDigest,
    signerChainDigest,
    hardwareBacked: hardwareBacked === true,
    vendorSignatureVerified: vendorSignatureVerified === true,
    measurementPolicyVerified: measurementPolicyVerified === true,
    tcbPolicyVerified: tcbPolicyVerified === true,
    runtimeKeyBound: runtimeKeyBound === true,
    verifierKeyId: String(verifierKeyId),
  });
}

function signVerifierVerdict(body, privateKey) {
  const normalized = verdictBody(body);
  const signature = crypto.sign(null, Buffer.from(stable(normalized)), privateKey).toString("base64");
  return Object.freeze({ body: normalized, signature });
}

function verifyVerifierVerdict(signedVerdict, challenge, trustedVerifierPublicKey, options = {}) {
  const requireHardware = options.requireHardware !== false;
  if (!signedVerdict || !signedVerdict.body || typeof signedVerdict.signature !== "string") {
    return Object.freeze({ ok: false, code: "ATTESTATION_VERDICT_MALFORMED" });
  }
  let body;
  try { body = verdictBody(signedVerdict.body); }
  catch (_) { return Object.freeze({ ok: false, code: "ATTESTATION_VERDICT_MALFORMED" }); }

  const signatureValid = crypto.verify(
    null,
    Buffer.from(stable(body)),
    trustedVerifierPublicKey,
    Buffer.from(signedVerdict.signature, "base64")
  );
  if (!signatureValid) return Object.freeze({ ok: false, code: "ATTESTATION_VERIFIER_SIGNATURE_INVALID" });
  if (!challenge || body.challengeDigest !== challenge.challengeDigest) {
    return Object.freeze({ ok: false, code: "ATTESTATION_CHALLENGE_MISMATCH" });
  }
  if (!body.vendorSignatureVerified) return Object.freeze({ ok: false, code: "VENDOR_ATTESTATION_SIGNATURE_UNVERIFIED" });
  if (!body.measurementPolicyVerified) return Object.freeze({ ok: false, code: "MEASURED_BOOT_POLICY_UNVERIFIED" });
  if (!body.tcbPolicyVerified) return Object.freeze({ ok: false, code: "ATTESTED_TCB_POLICY_UNVERIFIED" });
  if (!body.runtimeKeyBound) return Object.freeze({ ok: false, code: "RUNTIME_KEY_NOT_BOUND_TO_ATTESTATION" });
  if (requireHardware && !body.hardwareBacked) return Object.freeze({ ok: false, code: "HARDWARE_BACKING_REQUIRED" });

  return Object.freeze({
    ok: true,
    code: body.hardwareBacked ? "HARDWARE_ATTESTATION_VERIFIED" : "VERIFIER_CONTRACT_ONLY",
    provider: body.provider,
    verdictDigest: sha256(body),
    hardwareBacked: body.hardwareBacked,
  });
}

function verifiedBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  const verification = verifyVerifierVerdict(signedVerdict, challenge, trustedVerifierPublicKey, { requireHardware: true });
  if (!verification.ok) throw new Error(`refusing unattested W33 receipt: ${verification.code}`);
  if (challenge.passportId !== passport.passportId || challenge.deploymentDigest !== contract.deploymentDigest) {
    throw new Error("attestation challenge does not bind this passport/deployment");
  }
  const binding = {
    schema: BINDING_SCHEMA,
    passportId: passport.passportId,
    deploymentDigest: contract.deploymentDigest,
    runtimePublicKeyDigest: challenge.runtimePublicKeyDigest,
    challengeDigest: challenge.challengeDigest,
    provider: signedVerdict.body.provider,
    launchMeasurement: signedVerdict.body.launchMeasurement,
    reportedTcbDigest: signedVerdict.body.reportedTcbDigest,
    signerChainDigest: signedVerdict.body.signerChainDigest,
    verifierKeyId: signedVerdict.body.verifierKeyId,
    verifierVerdictDigest: verification.verdictDigest,
    hardwareBacked: true,
  };
  return Object.freeze({ ...binding, bindingDigest: sha256(binding) });
}

function attachAttestationReceiptMetadata(metadata, passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  const binding = verifiedBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey);
  return Object.freeze({ ...(metadata || {}), w33MeasuredBoot: binding });
}

function toReceiptHardwareEvidence(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey) {
  const binding = verifiedBinding(passport, contract, challenge, signedVerdict, trustedVerifierPublicKey);
  const kind = binding.provider === PROVIDER.TPM2 ? "TPM_QUOTE" : "SEV_SNP_REPORT";
  return Object.freeze({
    schema: HARDWARE_EVIDENCE_SCHEMA,
    hardwareAttested: true,
    evidence: Object.freeze([
      Object.freeze({
        kind,
        status: "VERIFIED",
        reasonCode: "SIGNED_NORMALIZED_EXTERNAL_VERIFIER_VERDICT",
        verifier: binding.verifierKeyId,
        digest: binding.verifierVerdictDigest,
        launchMeasurement: binding.launchMeasurement,
        reportedTcbDigest: binding.reportedTcbDigest,
        signerChainDigest: binding.signerChainDigest,
        challengeDigest: binding.challengeDigest,
        passportId: binding.passportId,
        deploymentDigest: binding.deploymentDigest,
        runtimePublicKeyDigest: binding.runtimePublicKeyDigest,
      }),
    ]),
  });
}

module.exports = {
  PROVIDER,
  VERDICT_SCHEMA,
  BINDING_SCHEMA,
  HARDWARE_EVIDENCE_SCHEMA,
  sha256,
  buildChallenge,
  verdictBody,
  signVerifierVerdict,
  verifyVerifierVerdict,
  verifiedBinding,
  attachAttestationReceiptMetadata,
  toReceiptHardwareEvidence,
};
