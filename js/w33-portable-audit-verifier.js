"use strict";

const crypto = require("node:crypto");
const Receipt = require("../runtime/receipt.js");
const Native = require("./w33-native-attestation.js");
const TPM = require("./w33-tpm-eventlog-provenance.js");
const TPMWire = require("./w33-tpm-wire-signature.js");
const Flight = require("./w33-attested-replay-receipt.js");
const Passport = require("./w33-passport-deployment.js");

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(typeof value === "string" ? value : stable(value)).digest("hex")}`; }
function bytes64(s, name) { if (typeof s !== "string") throw new TypeError(`${name} base64 required`); return Buffer.from(s, "base64"); }

function verifyPassportContentId(passport) {
  if (!passport || typeof passport !== "object" || !/^sha256:[0-9a-f]{64}$/.test(passport.passportId || "")) return false;
  const { passportId, ...core } = passport;
  return Passport.sha256(core) === passportId;
}

function verifyAuthorityCertificate(cert, publicKeys, expectedThreshold = 4, expectedPopulation = 5) {
  if (!cert || cert.schema !== "w33.capability-epoch-quorum-certificate.v1" || !cert.body || !Array.isArray(cert.signatures)) return { ok: false, code: "EPOCH_CERTIFICATE_MALFORMED" };
  if (Number(cert.threshold) !== expectedThreshold || Number(cert.population) !== expectedPopulation) return { ok: false, code: "EPOCH_CERTIFICATE_PARAMETERS" };
  const seen = new Set();
  for (const row of cert.signatures) {
    if (!row || typeof row.member_id !== "string" || seen.has(row.member_id) || !publicKeys[row.member_id]) return { ok: false, code: "EPOCH_CERTIFICATE_SIGNER" };
    seen.add(row.member_id);
    try {
      const key = crypto.createPublicKey(publicKeys[row.member_id]);
      if (key.asymmetricKeyType !== "ed25519") return { ok: false, code: "EPOCH_AUTHORITY_KEY_TYPE" };
      if (!crypto.verify(null, Buffer.from(stable(cert.body)), key, Buffer.from(row.signature_b64, "base64"))) return { ok: false, code: "EPOCH_CERTIFICATE_SIGNATURE" };
    } catch (error) { return { ok: false, code: "EPOCH_CERTIFICATE_SIGNATURE", error: error.message }; }
  }
  if (seen.size < expectedThreshold) return { ok: false, code: "EPOCH_CERTIFICATE_NO_QUORUM" };
  return { ok: true, signers: [...seen].sort() };
}

function verifyAuthorityChain(certificates, publicKeys) {
  if (!Array.isArray(certificates)) return { ok: false, code: "EPOCH_CHAIN_REQUIRED" };
  const rows = certificates.map((cert, index) => ({ index, result: verifyAuthorityCertificate(cert, publicKeys) }));
  const bad = rows.find((x) => !x.result.ok);
  return bad ? { ok: false, code: bad.result.code, index: bad.index, detail: bad.result } : { ok: true, count: rows.length };
}

function verifyHardware(bundle) {
  const h = bundle && bundle.hardware;
  if (!h || typeof h !== "object") return { ok: false, code: "RAW_HARDWARE_EVIDENCE_REQUIRED" };
  if (h.provider === "TPM2") {
    if (h.tpmtSignatureBase64) {
      return TPMWire.verifyTpmQuoteWire({
        rawEventLog: bytes64(h.rawEventLogBase64, "rawEventLog"),
        tpmtSignature: bytes64(h.tpmtSignatureBase64, "TPMT_SIGNATURE"),
        attestation: bytes64(h.attestationBase64, "attestation"),
        akPublicKey: h.akPublicKeyPem,
        challenge: h.challenge,
        akTrust: h.akTrust || "PORTABLE_TRUSTED_AK",
      });
    }
    return TPM.verifyTpmQuoteFromRawEventLog({
      rawEventLog: bytes64(h.rawEventLogBase64, "rawEventLog"),
      attestation: bytes64(h.attestationBase64, "attestation"),
      signature: bytes64(h.signatureBase64, "signature"),
      akPublicKey: h.akPublicKeyPem,
      challenge: h.challenge,
      quoteHashAlgorithm: h.quoteHashAlgorithm || "sha256",
      akTrust: h.akTrust || "PORTABLE_TRUSTED_AK",
    });
  }
  if (h.provider === "SEV_SNP") {
    return Native.verifySnpReportNative({
      report: bytes64(h.reportBase64, "SEV-SNP report"),
      challenge: h.challenge,
      expectedMeasurement: h.expectedMeasurement || null,
      minimumReportedTcb: h.minimumReportedTcb == null ? 0n : BigInt(h.minimumReportedTcb),
      pinnedVcekPublicKey: h.pinnedVcekPublicKeyPem || null,
      vcekCertificatePem: h.vcekCertificatePem || null,
      askCertificatePem: h.askCertificatePem || null,
      arkCertificatePem: h.arkCertificatePem || null,
    });
  }
  return { ok: false, code: "UNSUPPORTED_HARDWARE_PROVIDER" };
}

function verifyPortableBundle(bundle, trustedReceiptPublicKey) {
  try {
    if (!bundle || typeof bundle !== "object" || !bundle.envelope) return Object.freeze({ ok: false, code: "PORTABLE_BUNDLE_MALFORMED" });
    const signed = Receipt.verifyDeliveryReceipt(bundle.envelope, trustedReceiptPublicKey);
    if (!signed.valid) return Object.freeze({ ok: false, code: "DELIVERY_RECEIPT_SIGNATURE_INVALID", error: signed.error });
    const payload = signed.payload;
    const signedRecorder = payload && payload.metadata && payload.metadata.w33FlightRecorder;
    if (!Flight.verifyFlightRecorderRoot(signedRecorder)) return Object.freeze({ ok: false, code: "SIGNED_FLIGHT_RECORDER_INVALID" });
    if (!verifyPassportContentId(bundle.passport)) return Object.freeze({ ok: false, code: "PASSPORT_CONTENT_ID_INVALID" });
    if (bundle.passport.deploymentDigest !== signedRecorder.deploymentDigest) return Object.freeze({ ok: false, code: "PASSPORT_DEPLOYMENT_MISMATCH" });
    if (bundle.context && !Passport.validatePassportIdentity(bundle.passport, bundle.context.plan, bundle.context.profile, bundle.context.vm, bundle.context.contract || null)) return Object.freeze({ ok: false, code: "PASSPORT_CONTEXT_INVALID" });

    const authority = verifyAuthorityChain(bundle.epochCertificates, bundle.authorityPublicKeys || {});
    if (!authority.ok) return Object.freeze({ ok: false, code: authority.code, authority });
    const hardware = verifyHardware(bundle);
    if (!hardware.ok) return Object.freeze({ ok: false, code: hardware.code || "HARDWARE_VERIFICATION_FAILED", hardware });

    const rebuilt = Flight.buildFlightRecorder({
      passport: bundle.passport,
      deploymentDigest: bundle.passport.deploymentDigest,
      nativeVerification: hardware,
      epochCertificates: bundle.epochCertificates,
      gcEvolution: bundle.gcEvolution,
      magicEvents: bundle.magicEvents,
      artifacts: payload.artifacts,
    });
    if (rebuilt.flightRecorderRoot !== signedRecorder.flightRecorderRoot) return Object.freeze({ ok: false, code: "FLIGHT_RECORDER_REBUILD_MISMATCH", rebuilt: rebuilt.flightRecorderRoot, signed: signedRecorder.flightRecorderRoot });
    if (Flight.artifactRoot(payload.artifacts) !== signedRecorder.artifacts.artifactRoot) return Object.freeze({ ok: false, code: "FINAL_ARTIFACT_ROOT_MISMATCH" });
    if (bundle.concurrency) {
      const c = bundle.concurrency;
      if (c.waitForRoot !== bundle.passport.waitForRoot || c.cancellationRoot !== bundle.passport.cancellationRoot || c.asyncScheduleRoot !== bundle.passport.asyncScheduleRoot) return Object.freeze({ ok: false, code: "CONCURRENCY_IDENTITY_MISMATCH" });
    }
    return Object.freeze({
      ok: true, code: "PORTABLE_W33_AUDIT_PASS", flightRecorderRoot: rebuilt.flightRecorderRoot,
      passportId: bundle.passport.passportId, hardwareProvider: hardware.evidence.provider,
      epochCertificateCount: authority.count, artifactCount: payload.artifacts.length,
      checks: Object.freeze({ receiptSignature: true, passportContentId: true, passportContext: bundle.context ? true : "NOT_SUPPLIED", authorityQuorums: true, rawHardwareEvidence: true, replayRoot: true, artifacts: true, concurrencyIdentity: bundle.concurrency ? true : "NOT_SUPPLIED" }),
    });
  } catch (error) { return Object.freeze({ ok: false, code: "PORTABLE_W33_AUDIT_ERROR", error: error.message }); }
}

module.exports = { stable, sha256, verifyPassportContentId, verifyAuthorityCertificate, verifyAuthorityChain, verifyHardware, verifyPortableBundle };
