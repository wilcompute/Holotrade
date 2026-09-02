"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const test = require("node:test");
const N = require("../js/w33-native-attestation.js");

function digest(label) {
  return `sha256:${crypto.createHash("sha256").update(label).digest("hex")}`;
}

function challenge() {
  return Object.freeze({
    challengeDigest: digest("w33-native-challenge"),
    runtimePublicKeyDigest: digest("runtime-pubkey"),
  });
}

function syntheticSnpFixture() {
  const c = challenge();
  const keys = crypto.generateKeyPairSync("ec", { namedCurve: "secp384r1" });
  const report = Buffer.alloc(N.SNP.REPORT_BYTES);
  report.writeUInt32LE(5, 0x00);
  report.writeUInt32LE(7, 0x04);
  report.writeBigUInt64LE(0n, 0x08);
  report.writeUInt32LE(0, 0x30);
  report.writeUInt32LE(1, 0x34);
  report.writeBigUInt64LE(12n, 0x38);
  report.writeBigUInt64LE(0n, 0x40);
  Buffer.concat([N.digestBytes(c.challengeDigest), N.digestBytes(c.runtimePublicKeyDigest)]).copy(report, 0x50);
  const measurement = crypto.createHash("sha384").update("synthetic-launch").digest();
  measurement.copy(report, 0x90);
  report.writeBigUInt64LE(11n, 0x180);
  crypto.createHash("sha512").update("chip-id").digest().copy(report, 0x1a0);
  const der = crypto.sign("sha384", report.subarray(0, N.SNP.SIGNED_BYTES), keys.privateKey);
  N.derSignatureToSnpRaw(der).copy(report, N.SNP.SIGNATURE_OFFSET);
  return { c, keys, report, measurement };
}

function extend(hashName, oldValue, eventDigest) {
  return crypto.createHash(hashName).update(oldValue).update(eventDigest).digest();
}

function tpm2b(buf) {
  const out = Buffer.alloc(2 + buf.length);
  out.writeUInt16BE(buf.length, 0);
  buf.copy(out, 2);
  return out;
}

function syntheticTpmFixture() {
  const c = challenge();
  const ak = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const e0 = crypto.createHash("sha256").update("firmware-event").digest();
  const e7 = crypto.createHash("sha256").update("secureboot-event").digest();
  const p0 = extend("sha256", Buffer.alloc(32), e0);
  const p7 = extend("sha256", Buffer.alloc(32), e7);
  const quoted = crypto.createHash("sha256").update(Buffer.concat([p0, p7])).digest();

  const header = Buffer.alloc(6);
  header.writeUInt32BE(N.TPM.GENERATED_VALUE, 0);
  header.writeUInt16BE(N.TPM.ST_ATTEST_QUOTE, 4);
  const clock = Buffer.alloc(17);
  const firmware = Buffer.alloc(8);
  const count = Buffer.alloc(4); count.writeUInt32BE(1, 0);
  const selection = Buffer.alloc(6);
  selection.writeUInt16BE(0x000b, 0); // sha256 bank
  selection[2] = 3;
  selection[3] = 0x81; // PCR0 and PCR7
  selection[4] = 0x00;
  selection[5] = 0x00;
  const attestation = Buffer.concat([
    header,
    tpm2b(Buffer.alloc(0)),
    tpm2b(N.digestBytes(c.challengeDigest)),
    clock,
    firmware,
    count,
    selection,
    tpm2b(quoted),
  ]);
  const signature = crypto.sign("sha256", attestation, ak.privateKey);
  const eventDigests = [
    { pcr: 0, hashAlgorithm: "sha256", digestHex: e0.toString("hex") },
    { pcr: 7, hashAlgorithm: "sha256", digestHex: e7.toString("hex") },
  ];
  return { c, ak, attestation, signature, eventDigests };
}

test("native SEV-SNP verifier checks signed report, challenge binding, measurement and TCB", () => {
  const f = syntheticSnpFixture();
  const result = N.verifySnpReportNative({
    report: f.report,
    challenge: f.c,
    expectedMeasurement: f.measurement,
    minimumReportedTcb: 10n,
    pinnedVcekPublicKey: f.keys.publicKey,
  });
  assert.equal(result.ok, true);
  assert.equal(result.code, "SNP_REPORT_CRYPTOGRAPHICALLY_VERIFIED");
  assert.equal(result.evidence.trustMode, "PINNED_VCEK");
  assert.equal(result.evidence.vendorChainVerified, false);
  assert.equal(N.toReceiptHardwareEvidence(result).hardwareAttested, true);
});

test("native SEV-SNP verifier refuses report-data and signature tampering", () => {
  const f = syntheticSnpFixture();
  const wrongData = Buffer.from(f.report); wrongData[0x50] ^= 1;
  assert.equal(N.verifySnpReportNative({ report: wrongData, challenge: f.c, pinnedVcekPublicKey: f.keys.publicKey }).code, "SNP_REPORT_DATA_MISMATCH");

  const wrongSig = Buffer.from(f.report); wrongSig[0x2a0] ^= 1;
  assert.equal(N.verifySnpReportNative({ report: wrongSig, challenge: f.c, pinnedVcekPublicKey: f.keys.publicKey }).code, "SNP_REPORT_SIGNATURE_INVALID");
});

test("native TPM2 verifier parses quote, verifies AK signature and replays PCR event digests", () => {
  const f = syntheticTpmFixture();
  const result = N.verifyTpmQuoteNative({
    attestation: f.attestation,
    signature: f.signature,
    akPublicKey: f.ak.publicKey,
    challenge: f.c,
    eventDigests: f.eventDigests,
    quoteHashAlgorithm: "sha256",
  });
  assert.equal(result.ok, true);
  assert.equal(result.code, "TPM_QUOTE_AND_PCR_REPLAY_VERIFIED");
  assert.equal(result.evidence.akTrust, "PINNED_AK");
  assert.equal(N.toReceiptHardwareEvidence(result).hardwareAttested, true);
});

test("native TPM2 verifier refuses nonce, event-log and quote-signature tampering", () => {
  const f = syntheticTpmFixture();
  const badEvents = f.eventDigests.map((x, i) => i ? x : { ...x, digestHex: crypto.createHash("sha256").update("evil").digest("hex") });
  assert.equal(N.verifyTpmQuoteNative({ attestation: f.attestation, signature: f.signature, akPublicKey: f.ak.publicKey, challenge: f.c, eventDigests: badEvents }).code, "TPM_QUOTED_PCR_DIGEST_MISMATCH");

  const other = { ...f.c, challengeDigest: digest("other") };
  assert.equal(N.verifyTpmQuoteNative({ attestation: f.attestation, signature: f.signature, akPublicKey: f.ak.publicKey, challenge: other, eventDigests: f.eventDigests }).code, "TPM_QUOTE_NONCE_MISMATCH");

  const sig = Buffer.from(f.signature); sig[0] ^= 1;
  assert.equal(N.verifyTpmQuoteNative({ attestation: f.attestation, signature: sig, akPublicKey: f.ak.publicKey, challenge: f.c, eventDigests: f.eventDigests }).code, "TPM_QUOTE_SIGNATURE_INVALID");
});
