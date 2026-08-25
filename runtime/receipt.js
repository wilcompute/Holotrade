"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { sha256File } = require("./artifacts.js");
const { serializeMeasurement } = require("./metering.js");
const { signDeliveryReceipt, verifyDeliveryReceipt } = require("./cose.js");

const PAYLOAD_SCHEMA = "holotrade.delivery-receipt.payload.v1";
const HARDWARE_EVIDENCE_SCHEMA = "holotrade.hardware-evidence.v1";

async function bindEvidenceFile(kind, filePath, verifier = null) {
  if (!filePath) {
    return { kind, status: "UNAVAILABLE", reasonCode: "EVIDENCE_PATH_NOT_CONFIGURED" };
  }
  const absolutePath = path.resolve(filePath);
  try {
    const stat = await fs.promises.lstat(absolutePath);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      return { kind, status: "UNAVAILABLE", reasonCode: "EVIDENCE_NOT_REGULAR_FILE", path: absolutePath };
    }
    const evidence = {
      kind,
      status: "BOUND_UNVERIFIED",
      reasonCode: "BYTES_HASHED_SIGNATURE_NOT_VERIFIED",
      path: absolutePath,
      bytes: stat.size,
      digest: await sha256File(absolutePath),
    };
    if (typeof verifier === "function") {
      const result = await verifier(absolutePath, evidence);
      const accepted = result && result.valid === true && typeof result.verifier === "string" && result.verifier.length > 0;
      evidence.status = accepted ? "VERIFIED" : "REJECTED";
      evidence.reasonCode = accepted ? "EXTERNAL_VERIFIER_ACCEPTED" : "EXTERNAL_VERIFIER_REJECTED";
      evidence.verification = result || null;
    }
    return evidence;
  } catch (error) {
    return { kind, status: "UNAVAILABLE", reasonCode: "EVIDENCE_FILE_UNREADABLE", path: absolutePath, error: error.code || error.message };
  }
}

async function collectHardwareEvidence({
  measuredBootLogPath = null,
  tpmQuotePath = null,
  sevSnpReportPath = null,
  verifyTpmQuote = null,
  verifySevSnpReport = null,
} = {}) {
  const evidence = [
    await bindEvidenceFile("MEASURED_BOOT_EVENT_LOG", measuredBootLogPath),
    await bindEvidenceFile("TPM_QUOTE", tpmQuotePath, verifyTpmQuote),
    await bindEvidenceFile("SEV_SNP_REPORT", sevSnpReportPath, verifySevSnpReport),
  ];
  return {
    schema: HARDWARE_EVIDENCE_SCHEMA,
    hardwareAttested: evidence.some((item) =>
      ["TPM_QUOTE", "SEV_SNP_REPORT"].includes(item.kind) && item.status === "VERIFIED"
    ),
    evidence,
  };
}

function deliveryPayload({
  executionId,
  nodeId,
  outcome,
  artifacts,
  capabilities,
  energy = null,
  hardwareEvidence = null,
  startedAtMs,
  finishedAtMs,
  nonce,
  metadata = {},
  microvmExecuted = false,
}) {
  if (!executionId || !nodeId || !outcome || !nonce) {
    throw new TypeError("executionId, nodeId, outcome and nonce are required");
  }
  if (!Array.isArray(artifacts) || artifacts.length === 0 ||
      !artifacts.every((item) => /^sha256:[0-9a-f]{64}$/.test(item.digest))) {
    throw new TypeError("at least one SHA-256 artifact record is required");
  }
  if (!Number.isSafeInteger(startedAtMs) || !Number.isSafeInteger(finishedAtMs) || finishedAtMs < startedAtMs) {
    throw new RangeError("receipt timestamps must be ordered integer milliseconds");
  }
  const relevantCapabilities = capabilities && Array.isArray(capabilities.findings)
    ? capabilities.findings.map((item) => ({ id: item.id, status: item.status, reasonCode: item.reasonCode }))
    : [];
  const boundEvidence = hardwareEvidence || { schema: HARDWARE_EVIDENCE_SCHEMA, hardwareAttested: false, evidence: [] };
  return {
    schema: PAYLOAD_SCHEMA,
    executionId: String(executionId),
    nodeId: String(nodeId),
    outcome: String(outcome),
    nonce: String(nonce),
    startedAtMs,
    finishedAtMs,
    durationMs: finishedAtMs - startedAtMs,
    artifacts: artifacts.map((item) => ({ role: item.role, bytes: item.bytes, digest: item.digest })),
    runtime: {
      microvmExecuted: microvmExecuted === true,
      hardwareAttested: boundEvidence.hardwareAttested === true,
      capabilityFindings: relevantCapabilities,
    },
    energy: energy ? serializeMeasurement(energy) : { status: "UNAVAILABLE" },
    hardwareEvidence: boundEvidence,
    metadata,
  };
}

function createSignedDeliveryReceipt(spec, privateKey, options = {}) {
  const payload = deliveryPayload(spec);
  return { payload, envelope: signDeliveryReceipt(payload, privateKey, options) };
}

module.exports = {
  PAYLOAD_SCHEMA,
  HARDWARE_EVIDENCE_SCHEMA,
  bindEvidenceFile,
  collectHardwareEvidence,
  deliveryPayload,
  createSignedDeliveryReceipt,
  verifyDeliveryReceipt,
};
