"use strict";

// Cryptographic flight recorder for W33/Holotrade execution.
//
// One delivery receipt binds:
//   execution passport + GoMicroVM deployment,
//   native TPM2/SEV-SNP verification evidence,
//   complete capability-epoch transition chain,
//   wait/cancellation/wake-schedule replay identities,
//   temporal GC registry evolution,
//   magic-token reservation/consumption events,
//   final artifact set.
//
// The final object is signed through Holotrade's existing deterministic
// CBOR/COSE Ed25519 delivery-receipt path.  This module does not claim that a
// hash root alone makes an event physically true; it makes substitution,
// omission and reordering visible once the constituent evidence is trusted.

const crypto = require("node:crypto");
const Receipt = require("../runtime/receipt.js");
const Native = require("./w33-native-attestation.js");

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(typeof value === "string" ? value : stable(value)).digest("hex")}`;
}

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function bodyOfCertificate(cert) {
  if (!cert || typeof cert !== "object") throw new TypeError("epoch certificate object required");
  return cert.body || cert.transition || cert;
}

function transitionId(body) {
  return sha256(body);
}

function validateEpochChain(epochCertificates, passport) {
  if (!Array.isArray(epochCertificates)) throw new TypeError("epoch certificate chain required");
  if (!passport || !Number.isSafeInteger(passport.capabilityEpoch) || !isDigest(passport.revocationRoot)) throw new TypeError("authority-aware passport required");
  if (epochCertificates.length === 0) {
    return Object.freeze({ ok: passport.capabilityEpoch === 0, count: 0, chainRoot: sha256([]), finalEpoch: 0, finalRoot: passport.capabilityEpoch === 0 ? passport.revocationRoot : null });
  }
  let previous = null;
  let previousId = null;
  for (let i = 0; i < epochCertificates.length; i++) {
    const body = bodyOfCertificate(epochCertificates[i]);
    const fromEpoch = body.from_epoch ?? body.fromEpoch;
    const toEpoch = body.to_epoch ?? body.toEpoch;
    const fromRoot = body.from_root ?? body.fromRoot;
    const toRoot = body.to_root ?? body.toRoot;
    const prevId = body.previous_transition_id ?? body.previousTransitionId ?? null;
    if (!Number.isSafeInteger(fromEpoch) || !Number.isSafeInteger(toEpoch) || toEpoch !== fromEpoch + 1 || !isDigest(fromRoot) || !isDigest(toRoot)) {
      return Object.freeze({ ok: false, code: "EPOCH_CHAIN_MALFORMED", index: i });
    }
    if (i > 0) {
      const priorBody = bodyOfCertificate(previous);
      const priorToEpoch = priorBody.to_epoch ?? priorBody.toEpoch;
      const priorToRoot = priorBody.to_root ?? priorBody.toRoot;
      if (fromEpoch !== priorToEpoch || fromRoot !== priorToRoot || prevId !== previousId) {
        return Object.freeze({ ok: false, code: "EPOCH_CHAIN_LINK_MISMATCH", index: i });
      }
    } else if (prevId !== null) {
      return Object.freeze({ ok: false, code: "EPOCH_CHAIN_GENESIS_PREDECESSOR_NON_NULL", index: 0 });
    }
    previous = epochCertificates[i];
    previousId = transitionId(body);
  }
  const finalBody = bodyOfCertificate(epochCertificates[epochCertificates.length - 1]);
  const finalEpoch = finalBody.to_epoch ?? finalBody.toEpoch;
  const finalRoot = finalBody.to_root ?? finalBody.toRoot;
  if (finalEpoch !== passport.capabilityEpoch || finalRoot !== passport.revocationRoot) {
    return Object.freeze({ ok: false, code: "EPOCH_CHAIN_DOES_NOT_REACH_PASSPORT", finalEpoch, finalRoot });
  }
  return Object.freeze({ ok: true, count: epochCertificates.length, chainRoot: sha256(epochCertificates), finalEpoch, finalRoot });
}

function artifactRoot(artifacts) {
  if (!Array.isArray(artifacts) || artifacts.length === 0) throw new TypeError("final artifacts required");
  const rows = artifacts.map((x) => {
    if (!isDigest(x.digest)) throw new TypeError("artifact SHA-256 digest required");
    return { role: x.role || null, bytes: Number(x.bytes || 0), digest: x.digest };
  }).sort((a, b) => (a.role || "").localeCompare(b.role || "") || a.digest.localeCompare(b.digest));
  return sha256(rows);
}

function buildFlightRecorder({ passport, deploymentDigest, nativeVerification, epochCertificates, gcEvolution, magicEvents, artifacts }) {
  if (!passport || !isDigest(passport.passportId)) throw new TypeError("execution passport required");
  if (!isDigest(deploymentDigest) || passport.deploymentDigest !== deploymentDigest) throw new Error("passport/deployment digest mismatch");
  if (!nativeVerification || nativeVerification.ok !== true || nativeVerification.hardwareBacked !== true) throw new Error("successful native hardware verification required");
  const epoch = validateEpochChain(epochCertificates, passport);
  if (!epoch.ok) throw new Error(`epoch chain invalid: ${epoch.code}`);
  if (!Array.isArray(gcEvolution) || gcEvolution.length === 0 || !gcEvolution.every((x) => isDigest(x))) throw new TypeError("GC registry-root evolution required");
  if (gcEvolution[gcEvolution.length - 1] !== passport.gcRegistryRoot) throw new Error("GC evolution does not reach passport root");
  if (!Array.isArray(magicEvents)) throw new TypeError("magic event list required");

  const body = {
    schema: "holotrade.w33-attested-replay-flight-recorder.v1",
    passportId: passport.passportId,
    deploymentDigest,
    machineType: passport.machineType,
    logicalDimension: passport.logicalDimension,
    authority: Object.freeze({ capabilityEpoch: passport.capabilityEpoch, revocationRoot: passport.revocationRoot, epochChainRoot: epoch.chainRoot, epochTransitionCount: epoch.count }),
    concurrency: Object.freeze({
      waitForRoot: passport.waitForRoot,
      cancellationRoot: passport.cancellationRoot,
      asyncScheduleRoot: passport.asyncScheduleRoot,
      combinedRoot: sha256([passport.waitForRoot, passport.cancellationRoot, passport.asyncScheduleRoot]),
    }),
    persistence: Object.freeze({ gcRegistryRoot: passport.gcRegistryRoot, gcEvolutionRoot: sha256(gcEvolution), gcTransitionCount: gcEvolution.length }),
    magic: Object.freeze({ eventRoot: sha256(magicEvents), eventCount: magicEvents.length, budget: passport.magicBudget }),
    attestation: Object.freeze({ provider: nativeVerification.evidence.provider, evidenceRoot: sha256(nativeVerification.evidence), evidenceDigest: nativeVerification.evidence.reportDigest || nativeVerification.evidence.attestationDigest }),
    artifacts: Object.freeze({ artifactRoot: artifactRoot(artifacts), count: artifacts.length }),
  };
  return Object.freeze({ ...body, flightRecorderRoot: sha256(body) });
}

function verifyFlightRecorderRoot(recorder) {
  if (!recorder || recorder.schema !== "holotrade.w33-attested-replay-flight-recorder.v1" || !isDigest(recorder.flightRecorderRoot)) return false;
  const { flightRecorderRoot, ...body } = recorder;
  return sha256(body) === flightRecorderRoot;
}

function createAttestedReplayReceipt({
  receiptSpec,
  passport,
  deploymentDigest,
  nativeVerification,
  epochCertificates,
  gcEvolution,
  magicEvents,
}, privateKey, options = {}) {
  if (!receiptSpec || !Array.isArray(receiptSpec.artifacts)) throw new TypeError("receiptSpec with artifacts required");
  const recorder = buildFlightRecorder({ passport, deploymentDigest, nativeVerification, epochCertificates, gcEvolution, magicEvents, artifacts: receiptSpec.artifacts });
  const hardwareEvidence = Native.toReceiptHardwareEvidence(nativeVerification);
  const metadata = Object.freeze({ ...(receiptSpec.metadata || {}), w33FlightRecorder: recorder });
  const signed = Receipt.createSignedDeliveryReceipt({ ...receiptSpec, metadata, hardwareEvidence }, privateKey, options);
  return Object.freeze({ ...signed, flightRecorderRoot: recorder.flightRecorderRoot });
}

function verifyAttestedReplayReceipt(signedReceipt, publicKey) {
  if (!signedReceipt || !signedReceipt.envelope) return Object.freeze({ ok: false, code: "SIGNED_RECEIPT_REQUIRED" });
  const verified = Receipt.verifyDeliveryReceipt(signedReceipt.envelope, publicKey);
  if (!verified.valid) return Object.freeze({ ok: false, code: "DELIVERY_RECEIPT_SIGNATURE_INVALID" });
  const payload = verified.payload;
  const recorder = payload && payload.metadata && payload.metadata.w33FlightRecorder;
  if (!verifyFlightRecorderRoot(recorder)) return Object.freeze({ ok: false, code: "FLIGHT_RECORDER_ROOT_INVALID" });
  if (!payload.runtime || payload.runtime.hardwareAttested !== true) return Object.freeze({ ok: false, code: "HARDWARE_ATTESTATION_NOT_BOUND" });
  if (artifactRoot(payload.artifacts) !== recorder.artifacts.artifactRoot) return Object.freeze({ ok: false, code: "FINAL_ARTIFACT_SET_MISMATCH" });
  return Object.freeze({ ok: true, code: "ATTESTED_REPLAY_RECEIPT_VERIFIED", flightRecorderRoot: recorder.flightRecorderRoot, passportId: recorder.passportId, payload });
}

module.exports = {
  sha256,
  transitionId,
  validateEpochChain,
  artifactRoot,
  buildFlightRecorder,
  verifyFlightRecorderRoot,
  createAttestedReplayReceipt,
  verifyAttestedReplayReceipt,
};
