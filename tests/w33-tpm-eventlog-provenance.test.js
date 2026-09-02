"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const test = require("node:test");
const N = require("../js/w33-native-attestation.js");
const P = require("../js/w33-tpm-eventlog-provenance.js");

function digest(label) { return `sha256:${crypto.createHash("sha256").update(label).digest("hex")}`; }
function challenge() { return Object.freeze({ challengeDigest: digest("raw-eventlog-challenge"), runtimePublicKeyDigest: digest("runtime") }); }

function specIdEvent() {
  const sig = Buffer.alloc(16); Buffer.from("Spec ID Event03").copy(sig);
  const fixed = Buffer.alloc(12);
  fixed.writeUInt32LE(0, 0); // platformClass
  fixed[4] = 0; fixed[5] = 2; fixed[6] = 0; fixed[7] = 2; // minor, major, errata, uintnSize
  fixed.writeUInt32LE(1, 8); // one algorithm
  const alg = Buffer.alloc(4); alg.writeUInt16LE(0x000b, 0); alg.writeUInt16LE(32, 2);
  return Buffer.concat([sig, fixed, alg, Buffer.from([0])]);
}

function legacyFirst() {
  const event = specIdEvent();
  const b = Buffer.alloc(32);
  b.writeUInt32LE(0, 0);
  b.writeUInt32LE(P.EVENT.EV_NO_ACTION, 4);
  // 20-byte digest remains all zero
  b.writeUInt32LE(event.length, 28);
  return Buffer.concat([b, event]);
}

function event2(pcr, eventType, eventBytes) {
  const d = crypto.createHash("sha256").update(eventBytes).digest();
  const h = Buffer.alloc(12);
  h.writeUInt32LE(pcr, 0); h.writeUInt32LE(eventType, 4); h.writeUInt32LE(1, 8);
  const alg = Buffer.alloc(2); alg.writeUInt16LE(0x000b, 0);
  const size = Buffer.alloc(4); size.writeUInt32LE(eventBytes.length, 0);
  return { bytes: Buffer.concat([h, alg, d, size, eventBytes]), digest: d };
}

function extend(oldValue, eventDigest) { return crypto.createHash("sha256").update(oldValue).update(eventDigest).digest(); }
function tpm2b(buf) { const out = Buffer.alloc(2 + buf.length); out.writeUInt16BE(buf.length, 0); buf.copy(out, 2); return out; }

function fixture() {
  const c = challenge();
  const ak = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  const e0 = event2(0, P.EVENT.EV_POST_CODE, Buffer.from("firmware-event"));
  const informational = event2(0, P.EVENT.EV_NO_ACTION, Buffer.from("informational-only"));
  const e7 = event2(7, P.EVENT.EV_ACTION, Buffer.from("secureboot-event"));
  const rawEventLog = Buffer.concat([legacyFirst(), e0.bytes, informational.bytes, e7.bytes]);
  const p0 = extend(Buffer.alloc(32), e0.digest);
  const p7 = extend(Buffer.alloc(32), e7.digest);
  const quoted = crypto.createHash("sha256").update(Buffer.concat([p0, p7])).digest();

  const header = Buffer.alloc(6); header.writeUInt32BE(N.TPM.GENERATED_VALUE, 0); header.writeUInt16BE(N.TPM.ST_ATTEST_QUOTE, 4);
  const clock = Buffer.alloc(17); const firmware = Buffer.alloc(8); const count = Buffer.alloc(4); count.writeUInt32BE(1, 0);
  const selection = Buffer.alloc(6); selection.writeUInt16BE(0x000b, 0); selection[2] = 3; selection[3] = 0x81;
  const attestation = Buffer.concat([header, tpm2b(Buffer.alloc(0)), tpm2b(N.digestBytes(c.challengeDigest)), clock, firmware, count, selection, tpm2b(quoted)]);
  const signature = crypto.sign("sha256", attestation, ak.privateKey);
  return { c, ak, rawEventLog, attestation, signature };
}

test("parses Spec-ID transition and excludes EV_NO_ACTION from PCR replay", () => {
  const f = fixture();
  const parsed = P.parsePcClientEventLog(f.rawEventLog);
  assert.equal(parsed.spec.signature, "Spec ID Event03");
  assert.equal(parsed.recordCount, 4);
  assert.equal(parsed.replayDigestCount, 2);
  assert.deepEqual(parsed.replayDigests.map((x) => x.pcr), [0, 7]);
});

test("verifies quote directly from raw PC Client event-log bytes", () => {
  const f = fixture();
  const result = P.verifyTpmQuoteFromRawEventLog({
    rawEventLog: f.rawEventLog,
    attestation: f.attestation,
    signature: f.signature,
    akPublicKey: f.ak.publicKey,
    challenge: f.c,
    quoteHashAlgorithm: "sha256",
  });
  assert.equal(result.ok, true);
  assert.equal(result.code, "TPM_QUOTE_AND_RAW_PC_CLIENT_EVENT_LOG_VERIFIED");
  assert.equal(result.evidence.rawEventRecordCount, 4);
  assert.equal(result.evidence.replayDigestCount, 2);
});

test("raw-log tampering changes replay and is rejected by the quote", () => {
  const f = fixture();
  const parsed = P.parsePcClientEventLog(f.rawEventLog);
  const firstReplay = parsed.records[1];
  // Flip one byte inside the first Event2 digest rather than event text. The
  // parser consumes it, and PCR replay must then disagree with the quote.
  const tampered = Buffer.from(f.rawEventLog);
  const specLen = legacyFirst().length;
  const digestOffset = specLen + 12 + 2;
  tampered[digestOffset] ^= 1;
  const result = P.verifyTpmQuoteFromRawEventLog({ rawEventLog: tampered, attestation: f.attestation, signature: f.signature, akPublicKey: f.ak.publicKey, challenge: f.c });
  assert.equal(result.code, "TPM_QUOTED_PCR_DIGEST_MISMATCH");
  assert.notEqual(firstReplay.digests[0].digestHex, P.parsePcClientEventLog(tampered).records[1].digests[0].digestHex);
});
