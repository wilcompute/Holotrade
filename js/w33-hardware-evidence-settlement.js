"use strict";

const crypto = require("node:crypto");
const Host = require("./w33-host-audit-bundle.js");
const Receipt = require("../runtime/receipt.js");

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(typeof value === "string" ? value : stable(value)).digest("hex")}`;
}

function admitVerifiedHostBundle(bundle, trustedReceiptPublicKey) {
  if (!bundle || typeof bundle !== "object") throw new TypeError("host bundle required");
  const verification = Host.verifyHostBundle(bundle, trustedReceiptPublicKey);
  if (!verification || verification.ok !== true || verification.code !== "PORTABLE_W33_HOST_AUDIT_PASS") {
    throw new Error(`host bundle is not admissible verified evidence: ${verification?.code || "UNKNOWN"}`);
  }
  if (!bundle.passport || !/^sha256:[0-9a-f]{64}$/.test(bundle.passport.passportId || "")) {
    throw new Error("verified host bundle lacks a valid passportId");
  }
  const evidence = Object.freeze({
    schema: "holotrade.w33-verified-host-evidence.v1",
    verified: true,
    verifierCode: verification.code,
    hostBundleDigest: sha256(bundle),
    telemetryDigest: verification.telemetryDigest,
    passportId: bundle.passport.passportId,
    hardwareProvider: verification.hardwareProvider || bundle.hardware?.provider || null,
    telemetrySources: Object.freeze([...(verification.telemetrySources || [])]),
  });
  return evidence;
}

function bindVerifiedHostEvidence(receiptSpec, evidence) {
  if (!receiptSpec || typeof receiptSpec !== "object") throw new TypeError("receiptSpec required");
  if (!evidence || evidence.schema !== "holotrade.w33-verified-host-evidence.v1" || evidence.verified !== true) {
    throw new TypeError("verified W33 host evidence required");
  }
  if (!/^sha256:[0-9a-f]{64}$/.test(evidence.hostBundleDigest || "") || !/^sha256:[0-9a-f]{64}$/.test(evidence.passportId || "")) {
    throw new TypeError("verified host evidence digests are malformed");
  }
  return Object.freeze({
    ...receiptSpec,
    metadata: Object.freeze({
      ...(receiptSpec.metadata || {}),
      w33VerifiedHostEvidenceSchema: evidence.schema,
      w33VerifiedHostBundleDigest: evidence.hostBundleDigest,
      w33VerifiedHostPassportId: evidence.passportId,
      w33VerifiedHostTelemetryDigest: evidence.telemetryDigest,
      w33VerifiedHostHardwareProvider: evidence.hardwareProvider,
      w33VerifiedHostVerifierCode: evidence.verifierCode,
    }),
  });
}

function createHardwareBoundSettlementReceipt(receiptSpec, evidence, privateKey, options = {}) {
  const bound = bindVerifiedHostEvidence(receiptSpec, evidence);
  return Receipt.createSignedDeliveryReceipt(bound, privateKey, options);
}

function verifyHardwareBoundSettlementReceipt(envelope, trustedSettlementPublicKey, evidence) {
  const verified = Receipt.verifyDeliveryReceipt(envelope, trustedSettlementPublicKey);
  if (!verified.valid) return Object.freeze({ ok: false, code: "SETTLEMENT_SIGNATURE_INVALID", error: verified.error || null });
  const md = verified.payload?.metadata || {};
  if (!evidence || evidence.verified !== true) return Object.freeze({ ok: false, code: "VERIFIED_HOST_EVIDENCE_REQUIRED" });
  if (md.w33VerifiedHostBundleDigest !== evidence.hostBundleDigest) return Object.freeze({ ok: false, code: "HOST_BUNDLE_DIGEST_BINDING_MISMATCH" });
  if (md.w33VerifiedHostPassportId !== evidence.passportId) return Object.freeze({ ok: false, code: "HOST_PASSPORT_BINDING_MISMATCH" });
  if (md.w33VerifiedHostTelemetryDigest !== evidence.telemetryDigest) return Object.freeze({ ok: false, code: "HOST_TELEMETRY_BINDING_MISMATCH" });
  return Object.freeze({
    ok: true,
    code: "W33_HARDWARE_BOUND_SETTLEMENT_PASS",
    hostBundleDigest: evidence.hostBundleDigest,
    passportId: evidence.passportId,
    telemetryDigest: evidence.telemetryDigest,
    hardwareProvider: evidence.hardwareProvider,
  });
}

module.exports = {
  stable,
  sha256,
  admitVerifiedHostBundle,
  bindVerifiedHostEvidence,
  createHardwareBoundSettlementReceipt,
  verifyHardwareBoundSettlementReceipt,
};
