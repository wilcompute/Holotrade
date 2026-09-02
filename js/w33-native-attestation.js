"use strict";

// Native cryptographic verification for W33 execution attestation.
//
// SEV-SNP: parse the AMD 1184-byte attestation report, bind REPORT_DATA to
// {challengeDigest,runtimePublicKeyDigest}, enforce launch-measurement / TCB
// policy, convert the firmware's little-endian P-384 R/S signature into DER,
// and verify SHA-384 directly with a VCEK public key.  When ARK/ASK/VCEK
// certificates are supplied, their signatures are verified in-process.
//
// TPM2: parse TPMS_ATTEST for TPM_ST_ATTEST_QUOTE, bind extraData to the W33
// challenge, replay supplied event digests into PCR values, recompute the quote
// PCR digest in selection order, and verify the AK signature directly.
//
// This module intentionally distinguishes cryptographic evidence validity from
// trust-anchor provenance. A pinned VCEK/AK can prove a report/quote is signed
// by that key; only an explicitly verified vendor/deployment trust chain can
// elevate provenance beyond the pin.

const crypto = require("node:crypto");

const SNP = Object.freeze({
  REPORT_BYTES: 0x4a0,
  SIGNED_BYTES: 0x2a0,
  REPORT_DATA_OFFSET: 0x50,
  REPORT_DATA_BYTES: 64,
  MEASUREMENT_OFFSET: 0x90,
  MEASUREMENT_BYTES: 48,
  REPORTED_TCB_OFFSET: 0x180,
  CHIP_ID_OFFSET: 0x1a0,
  CHIP_ID_BYTES: 64,
  SIGNATURE_OFFSET: 0x2a0,
  SIGNATURE_BYTES: 0x200,
});

const TPM = Object.freeze({
  GENERATED_VALUE: 0xff544347,
  ST_ATTEST_QUOTE: 0x8018,
  ALG: Object.freeze({ 0x0004: "sha1", 0x000b: "sha256", 0x000c: "sha384", 0x000d: "sha512" }),
});

function digestBytes(value) {
  if (typeof value !== "string" || !/^sha256:[0-9a-f]{64}$/.test(value)) throw new TypeError("sha256 digest required");
  return Buffer.from(value.slice(7), "hex");
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(value).digest("hex")}`;
}

function constantEqual(a, b) {
  return Buffer.isBuffer(a) && Buffer.isBuffer(b) && a.length === b.length && crypto.timingSafeEqual(a, b);
}

function readU64LE(buf, off) {
  return buf.readBigUInt64LE(off);
}

function trimUnsigned(bytes) {
  let i = 0;
  while (i < bytes.length - 1 && bytes[i] === 0) i++;
  let out = bytes.subarray(i);
  if (out[0] & 0x80) out = Buffer.concat([Buffer.from([0]), out]);
  return out;
}

function derLength(n) {
  if (n < 0x80) return Buffer.from([n]);
  if (n < 0x100) return Buffer.from([0x81, n]);
  return Buffer.from([0x82, n >> 8, n & 0xff]);
}

function derInteger(bytes) {
  const v = trimUnsigned(bytes);
  return Buffer.concat([Buffer.from([0x02]), derLength(v.length), v]);
}

function snpSignatureToDer(signature) {
  if (!Buffer.isBuffer(signature) || signature.length < 0x90) throw new TypeError("SEV-SNP signature block required");
  // AMD stores each 384-bit value in a 72-byte little-endian field.
  const r = Buffer.from(signature.subarray(0x00, 0x48)).reverse();
  const s = Buffer.from(signature.subarray(0x48, 0x90)).reverse();
  const body = Buffer.concat([derInteger(r), derInteger(s)]);
  return Buffer.concat([Buffer.from([0x30]), derLength(body.length), body]);
}

function parseDerInteger(buf, state) {
  if (buf[state.i++] !== 0x02) throw new Error("ECDSA DER integer expected");
  let len = buf[state.i++];
  if (len & 0x80) {
    const count = len & 0x7f;
    len = 0;
    for (let j = 0; j < count; j++) len = (len << 8) | buf[state.i++];
  }
  const out = buf.subarray(state.i, state.i + len);
  state.i += len;
  return out[0] === 0 ? out.subarray(1) : out;
}

function derSignatureToSnpRaw(der) {
  if (!Buffer.isBuffer(der) || der[0] !== 0x30) throw new TypeError("ECDSA DER signature required");
  let i = 1;
  let seqLen = der[i++];
  if (seqLen & 0x80) i += seqLen & 0x7f;
  const state = { i };
  const r = parseDerInteger(der, state);
  const s = parseDerInteger(der, state);
  if (r.length > 48 || s.length > 48) throw new Error("P-384 signature component too large");
  const out = Buffer.alloc(SNP.SIGNATURE_BYTES);
  Buffer.concat([Buffer.alloc(72 - r.length), r]).reverse().copy(out, 0);
  Buffer.concat([Buffer.alloc(72 - s.length), s]).reverse().copy(out, 0x48);
  return out;
}

function parseSnpReport(report) {
  if (!Buffer.isBuffer(report) || report.length !== SNP.REPORT_BYTES) throw new RangeError(`SEV-SNP report must be ${SNP.REPORT_BYTES} bytes`);
  const version = report.readUInt32LE(0x00);
  const signatureAlgorithm = report.readUInt32LE(0x34);
  if (version < 2 || version > 5) throw new Error(`unsupported SEV-SNP report version ${version}`);
  if (![1, 0x102].includes(signatureAlgorithm)) throw new Error(`unsupported SEV-SNP signature algorithm ${signatureAlgorithm}`);
  return Object.freeze({
    version,
    guestSvn: report.readUInt32LE(0x04),
    policy: readU64LE(report, 0x08),
    vmpl: report.readUInt32LE(0x30),
    signatureAlgorithm,
    currentTcb: readU64LE(report, 0x38),
    platformInfo: readU64LE(report, 0x40),
    reportData: Buffer.from(report.subarray(SNP.REPORT_DATA_OFFSET, SNP.REPORT_DATA_OFFSET + SNP.REPORT_DATA_BYTES)),
    measurement: Buffer.from(report.subarray(SNP.MEASUREMENT_OFFSET, SNP.MEASUREMENT_OFFSET + SNP.MEASUREMENT_BYTES)),
    reportedTcb: readU64LE(report, SNP.REPORTED_TCB_OFFSET),
    chipId: Buffer.from(report.subarray(SNP.CHIP_ID_OFFSET, SNP.CHIP_ID_OFFSET + SNP.CHIP_ID_BYTES)),
    signedBody: Buffer.from(report.subarray(0, SNP.SIGNED_BYTES)),
    signatureRaw: Buffer.from(report.subarray(SNP.SIGNATURE_OFFSET, SNP.SIGNATURE_OFFSET + SNP.SIGNATURE_BYTES)),
  });
}

function certValidNow(cert, now = Date.now()) {
  const t = Number(now);
  return Number.isFinite(t) && Date.parse(cert.validFrom) <= t && t <= Date.parse(cert.validTo);
}

function verifyAmdCertificateChain({ vcekCertificatePem, askCertificatePem, arkCertificatePem, now = Date.now() }) {
  try {
    const vcek = new crypto.X509Certificate(vcekCertificatePem);
    const ask = new crypto.X509Certificate(askCertificatePem);
    const ark = new crypto.X509Certificate(arkCertificatePem);
    const checks = {
      vcekTimeValid: certValidNow(vcek, now),
      askTimeValid: certValidNow(ask, now),
      arkTimeValid: certValidNow(ark, now),
      vcekSignedByAsk: vcek.verify(ask.publicKey),
      askSignedByArk: ask.verify(ark.publicKey),
      arkSelfSigned: ark.verify(ark.publicKey),
    };
    return Object.freeze({ ok: Object.values(checks).every(Boolean), checks, vcekPublicKey: vcek.publicKey });
  } catch (error) {
    return Object.freeze({ ok: false, code: "AMD_CERTIFICATE_CHAIN_MALFORMED", error: error.message });
  }
}

function verifySnpReportNative({
  report,
  challenge,
  expectedMeasurement = null,
  minimumReportedTcb = 0n,
  vcekCertificatePem = null,
  askCertificatePem = null,
  arkCertificatePem = null,
  pinnedVcekPublicKey = null,
  now = Date.now(),
}) {
  let parsed;
  try { parsed = parseSnpReport(report); }
  catch (error) { return Object.freeze({ ok: false, code: "SNP_REPORT_MALFORMED", error: error.message }); }
  if (!challenge) return Object.freeze({ ok: false, code: "W33_CHALLENGE_REQUIRED" });
  const expectedReportData = Buffer.concat([digestBytes(challenge.challengeDigest), digestBytes(challenge.runtimePublicKeyDigest)]);
  if (!constantEqual(parsed.reportData, expectedReportData)) return Object.freeze({ ok: false, code: "SNP_REPORT_DATA_MISMATCH" });
  if (expectedMeasurement) {
    const expected = Buffer.isBuffer(expectedMeasurement) ? expectedMeasurement : Buffer.from(String(expectedMeasurement).replace(/^sha384:/, ""), "hex");
    if (expected.length !== 48 || !constantEqual(parsed.measurement, expected)) return Object.freeze({ ok: false, code: "SNP_LAUNCH_MEASUREMENT_MISMATCH" });
  }
  const minTcb = typeof minimumReportedTcb === "bigint" ? minimumReportedTcb : BigInt(minimumReportedTcb);
  if (parsed.reportedTcb < minTcb) return Object.freeze({ ok: false, code: "SNP_REPORTED_TCB_BELOW_POLICY" });

  let publicKey = pinnedVcekPublicKey;
  let trustMode = "PINNED_VCEK";
  let chain = null;
  if (vcekCertificatePem || askCertificatePem || arkCertificatePem) {
    if (!(vcekCertificatePem && askCertificatePem && arkCertificatePem)) return Object.freeze({ ok: false, code: "AMD_CERTIFICATE_CHAIN_INCOMPLETE" });
    chain = verifyAmdCertificateChain({ vcekCertificatePem, askCertificatePem, arkCertificatePem, now });
    if (!chain.ok) return Object.freeze({ ok: false, code: "AMD_CERTIFICATE_CHAIN_INVALID", chain });
    publicKey = chain.vcekPublicKey;
    trustMode = "AMD_ARK_ASK_VCEK_CHAIN";
  }
  if (!publicKey) return Object.freeze({ ok: false, code: "VCEK_TRUST_ANCHOR_REQUIRED" });
  const der = snpSignatureToDer(parsed.signatureRaw);
  const signatureValid = crypto.verify("sha384", parsed.signedBody, publicKey, der);
  if (!signatureValid) return Object.freeze({ ok: false, code: "SNP_REPORT_SIGNATURE_INVALID" });
  const evidence = {
    schema: "holotrade.w33-native-snp-verification.v1",
    provider: "SEV_SNP",
    trustMode,
    version: parsed.version,
    measurement: `sha384:${parsed.measurement.toString("hex")}`,
    reportedTcb: parsed.reportedTcb.toString(),
    chipIdDigest: sha256(parsed.chipId),
    challengeDigest: challenge.challengeDigest,
    runtimePublicKeyDigest: challenge.runtimePublicKeyDigest,
    reportDigest: sha256(report),
    vendorChainVerified: trustMode === "AMD_ARK_ASK_VCEK_CHAIN",
  };
  return Object.freeze({ ok: true, code: "SNP_REPORT_CRYPTOGRAPHICALLY_VERIFIED", hardwareBacked: true, evidence: Object.freeze(evidence) });
}

function tpm2b(buf, state) {
  if (state.i + 2 > buf.length) throw new RangeError("truncated TPM2B");
  const n = buf.readUInt16BE(state.i); state.i += 2;
  if (state.i + n > buf.length) throw new RangeError("truncated TPM2B payload");
  const out = Buffer.from(buf.subarray(state.i, state.i + n)); state.i += n;
  return out;
}

function parseTpmQuoteAttest(attestation) {
  if (!Buffer.isBuffer(attestation)) throw new TypeError("TPMS_ATTEST bytes required");
  const state = { i: 0 };
  if (attestation.length < 6) throw new RangeError("truncated TPMS_ATTEST");
  const magic = attestation.readUInt32BE(state.i); state.i += 4;
  const type = attestation.readUInt16BE(state.i); state.i += 2;
  if (magic !== TPM.GENERATED_VALUE) throw new Error("TPM_GENERATED_VALUE mismatch");
  if (type !== TPM.ST_ATTEST_QUOTE) throw new Error("TPMS_ATTEST is not a quote");
  const qualifiedSigner = tpm2b(attestation, state);
  const extraData = tpm2b(attestation, state);
  if (state.i + 25 > attestation.length) throw new RangeError("truncated TPMS_ATTEST clock/firmware fields");
  const clockInfo = Buffer.from(attestation.subarray(state.i, state.i + 17)); state.i += 17;
  const firmwareVersion = attestation.readBigUInt64BE(state.i); state.i += 8;
  if (state.i + 4 > attestation.length) throw new RangeError("truncated TPML_PCR_SELECTION");
  const count = attestation.readUInt32BE(state.i); state.i += 4;
  if (count > 16) throw new RangeError("unreasonable TPM PCR selection count");
  const selections = [];
  for (let j = 0; j < count; j++) {
    if (state.i + 3 > attestation.length) throw new RangeError("truncated TPMS_PCR_SELECTION");
    const hashAlg = attestation.readUInt16BE(state.i); state.i += 2;
    const size = attestation[state.i++];
    if (!TPM.ALG[hashAlg]) throw new Error(`unsupported PCR bank algorithm 0x${hashAlg.toString(16)}`);
    if (state.i + size > attestation.length) throw new RangeError("truncated pcrSelect bitmap");
    const bitmap = Buffer.from(attestation.subarray(state.i, state.i + size)); state.i += size;
    selections.push(Object.freeze({ hashAlg, hashName: TPM.ALG[hashAlg], bitmap }));
  }
  const pcrDigest = tpm2b(attestation, state);
  if (state.i !== attestation.length) throw new Error("unexpected trailing TPMS_ATTEST bytes");
  return Object.freeze({ magic, type, qualifiedSigner, extraData, clockInfo, firmwareVersion, selections: Object.freeze(selections), pcrDigest });
}

function replayPcrEventDigests(events) {
  if (!Array.isArray(events)) throw new TypeError("event digest array required");
  const state = new Map();
  for (const event of events) {
    const pcr = Number(event.pcr);
    const hashName = String(event.hashAlgorithm || event.hashAlg || "").toLowerCase();
    if (!Number.isInteger(pcr) || pcr < 0 || pcr > 63 || !crypto.getHashes().includes(hashName)) throw new TypeError("invalid event digest record");
    const digest = Buffer.from(String(event.digestHex || ""), "hex");
    const width = crypto.createHash(hashName).digest().length;
    if (digest.length !== width) throw new TypeError("event digest width does not match PCR bank");
    const key = `${hashName}:${pcr}`;
    const old = state.get(key) || Buffer.alloc(width);
    state.set(key, crypto.createHash(hashName).update(old).update(digest).digest());
  }
  return state;
}

function selectedPcrBytes(selections, pcrState) {
  const chunks = [];
  for (const selection of selections) {
    for (let byte = 0; byte < selection.bitmap.length; byte++) {
      for (let bit = 0; bit < 8; bit++) {
        if (!(selection.bitmap[byte] & (1 << bit))) continue;
        const pcr = byte * 8 + bit;
        const key = `${selection.hashName}:${pcr}`;
        const value = pcrState.get(key);
        if (!value) throw new Error(`selected PCR ${key} has no replayed value`);
        chunks.push(value);
      }
    }
  }
  return Buffer.concat(chunks);
}

function verifyTpmQuoteNative({ attestation, signature, akPublicKey, challenge, eventDigests, quoteHashAlgorithm = "sha256", akTrust = "PINNED_AK" }) {
  let parsed;
  try { parsed = parseTpmQuoteAttest(attestation); }
  catch (error) { return Object.freeze({ ok: false, code: "TPM_QUOTE_MALFORMED", error: error.message }); }
  if (!challenge) return Object.freeze({ ok: false, code: "W33_CHALLENGE_REQUIRED" });
  if (!constantEqual(parsed.extraData, digestBytes(challenge.challengeDigest))) return Object.freeze({ ok: false, code: "TPM_QUOTE_NONCE_MISMATCH" });
  if (!akPublicKey) return Object.freeze({ ok: false, code: "TPM_AK_PUBLIC_KEY_REQUIRED" });
  let signatureValid = false;
  try { signatureValid = crypto.verify(quoteHashAlgorithm, attestation, akPublicKey, signature); }
  catch (error) { return Object.freeze({ ok: false, code: "TPM_QUOTE_SIGNATURE_ERROR", error: error.message }); }
  if (!signatureValid) return Object.freeze({ ok: false, code: "TPM_QUOTE_SIGNATURE_INVALID" });
  let replay;
  let expectedPcrDigest;
  try {
    replay = replayPcrEventDigests(eventDigests);
    expectedPcrDigest = crypto.createHash(quoteHashAlgorithm).update(selectedPcrBytes(parsed.selections, replay)).digest();
  } catch (error) {
    return Object.freeze({ ok: false, code: "TPM_EVENT_LOG_REPLAY_FAILED", error: error.message });
  }
  if (!constantEqual(parsed.pcrDigest, expectedPcrDigest)) return Object.freeze({ ok: false, code: "TPM_QUOTED_PCR_DIGEST_MISMATCH" });
  const evidence = {
    schema: "holotrade.w33-native-tpm2-verification.v1",
    provider: "TPM2",
    akTrust,
    challengeDigest: challenge.challengeDigest,
    attestationDigest: sha256(attestation),
    quotedPcrDigest: parsed.pcrDigest.toString("hex"),
    quoteHashAlgorithm,
    selectedBanks: parsed.selections.map((x) => ({ hashAlgorithm: x.hashName, bitmapHex: x.bitmap.toString("hex") })),
    eventDigestCount: eventDigests.length,
  };
  return Object.freeze({ ok: true, code: "TPM_QUOTE_AND_PCR_REPLAY_VERIFIED", hardwareBacked: true, evidence: Object.freeze(evidence) });
}

function toReceiptHardwareEvidence(nativeVerification) {
  if (!nativeVerification || nativeVerification.ok !== true || nativeVerification.hardwareBacked !== true) throw new Error("native hardware verification required");
  const kind = nativeVerification.evidence.provider === "SEV_SNP" ? "SEV_SNP_REPORT" : "TPM_QUOTE";
  return Object.freeze({
    schema: "holotrade.hardware-evidence.v1",
    hardwareAttested: true,
    evidence: Object.freeze([Object.freeze({
      kind,
      status: "VERIFIED",
      reasonCode: "NATIVE_CRYPTOGRAPHIC_VERIFIER_ACCEPTED",
      digest: nativeVerification.evidence.reportDigest || nativeVerification.evidence.attestationDigest,
      verification: nativeVerification.evidence,
    })]),
  });
}

module.exports = {
  SNP,
  TPM,
  sha256,
  digestBytes,
  snpSignatureToDer,
  derSignatureToSnpRaw,
  parseSnpReport,
  verifyAmdCertificateChain,
  verifySnpReportNative,
  parseTpmQuoteAttest,
  replayPcrEventDigests,
  selectedPcrBytes,
  verifyTpmQuoteNative,
  toReceiptHardwareEvidence,
};
