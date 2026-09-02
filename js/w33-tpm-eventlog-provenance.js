"use strict";

// Raw PC Client TPM2 event-log parsing and provenance binding for W33.
//
// The parser follows the PC Client Firmware Profile crypto-agile transition:
//   1. first entry is the legacy TCG_PCClientPCREvent carrying Spec ID Event;
//   2. the Spec ID Event declares digest algorithm IDs and widths;
//   3. remaining entries are TCG_PCR_EVENT2 records with TPML_DIGEST_VALUES.
//
// EV_NO_ACTION records are informational and are not replayed into PCRs.
// Parsed replay digests feed directly into w33-native-attestation.js.
//
// Credential provenance is intentionally typed separately from quote validity.
// X.509 AK/EK chains can authenticate those public keys to configured roots,
// but that alone does not prove that a particular AK is resident behind a
// particular EK. A separate credential-activation ceremony/receipt is needed
// for that stronger statement.

const crypto = require("node:crypto");
const Native = require("./w33-native-attestation.js");

const EVENT = Object.freeze({
  EV_PREBOOT_CERT: 0x00000000,
  EV_POST_CODE: 0x00000001,
  EV_NO_ACTION: 0x00000003,
  EV_SEPARATOR: 0x00000004,
  EV_ACTION: 0x00000005,
  EV_EVENT_TAG: 0x00000006,
  EV_EFI_VARIABLE_DRIVER_CONFIG: 0x80000001,
});

const ALG = Object.freeze({
  0x0004: "sha1",
  0x000b: "sha256",
  0x000c: "sha384",
  0x000d: "sha512",
});

function need(buf, off, count, what) {
  if (!Buffer.isBuffer(buf) || off < 0 || count < 0 || off + count > buf.length) {
    throw new RangeError(`truncated ${what}`);
  }
}

function hexDigest(buf) { return buf.toString("hex"); }

function parseSpecIdEvent(event) {
  if (!Buffer.isBuffer(event)) throw new TypeError("Spec ID event bytes required");
  let i = 0;
  need(event, i, 16, "Spec ID signature");
  const signatureRaw = Buffer.from(event.subarray(i, i + 16)); i += 16;
  const signature = signatureRaw.toString("ascii").replace(/\0+$/, "");
  if (!signature.startsWith("Spec ID Event")) throw new Error(`unexpected Spec ID signature ${JSON.stringify(signature)}`);
  need(event, i, 8, "Spec ID fixed fields");
  const platformClass = event.readUInt32LE(i); i += 4;
  const specVersionMinor = event[i++];
  const specVersionMajor = event[i++];
  const specErrata = event[i++];
  const uintnSize = event[i++];
  need(event, i, 4, "Spec ID algorithm count");
  const numberOfAlgorithms = event.readUInt32LE(i); i += 4;
  if (numberOfAlgorithms < 1 || numberOfAlgorithms > 32) throw new RangeError("unreasonable Spec ID algorithm count");
  const algorithms = [];
  const digestSizes = new Map();
  for (let j = 0; j < numberOfAlgorithms; j++) {
    need(event, i, 4, "Spec ID algorithm descriptor");
    const algorithmId = event.readUInt16LE(i); i += 2;
    const digestSize = event.readUInt16LE(i); i += 2;
    if (digestSize < 1 || digestSize > 128 || digestSizes.has(algorithmId)) throw new Error("invalid/duplicate Spec ID digest descriptor");
    algorithms.push(Object.freeze({ algorithmId, hashAlgorithm: ALG[algorithmId] || null, digestSize }));
    digestSizes.set(algorithmId, digestSize);
  }
  need(event, i, 1, "Spec ID vendor-info size");
  const vendorInfoSize = event[i++];
  need(event, i, vendorInfoSize, "Spec ID vendor info");
  const vendorInfo = Buffer.from(event.subarray(i, i + vendorInfoSize)); i += vendorInfoSize;
  if (i !== event.length) throw new Error("unexpected trailing Spec ID bytes");
  return Object.freeze({
    signature,
    platformClass,
    specVersionMajor,
    specVersionMinor,
    specErrata,
    uintnSize,
    algorithms: Object.freeze(algorithms),
    vendorInfo,
    digestSizes,
  });
}

function parseLegacyFirstEvent(raw, offset = 0) {
  let i = offset;
  need(raw, i, 32, "legacy first event");
  const pcrIndex = raw.readUInt32LE(i); i += 4;
  const eventType = raw.readUInt32LE(i); i += 4;
  const sha1Digest = Buffer.from(raw.subarray(i, i + 20)); i += 20;
  const eventSize = raw.readUInt32LE(i); i += 4;
  need(raw, i, eventSize, "legacy first event payload");
  const event = Buffer.from(raw.subarray(i, i + eventSize)); i += eventSize;
  if (eventType !== EVENT.EV_NO_ACTION) throw new Error("first PC Client TPM2 event must be EV_NO_ACTION Spec ID Event");
  const spec = parseSpecIdEvent(event);
  return Object.freeze({
    nextOffset: i,
    record: Object.freeze({ index: 0, format: "TCG_PCClientPCREvent", pcrIndex, eventType, sha1DigestHex: hexDigest(sha1Digest), eventSize, eventDigest: Native.sha256(event) }),
    spec,
  });
}

function parseEvent2(raw, offset, digestSizes, index) {
  let i = offset;
  need(raw, i, 12, "TCG_PCR_EVENT2 header");
  const pcrIndex = raw.readUInt32LE(i); i += 4;
  const eventType = raw.readUInt32LE(i); i += 4;
  const digestCount = raw.readUInt32LE(i); i += 4;
  if (digestCount < 1 || digestCount > 32) throw new RangeError("unreasonable TCG_PCR_EVENT2 digest count");
  const digests = [];
  for (let j = 0; j < digestCount; j++) {
    need(raw, i, 2, "TPMT_HA algorithm ID");
    const algorithmId = raw.readUInt16LE(i); i += 2;
    const digestSize = digestSizes.get(algorithmId);
    if (!digestSize) throw new Error(`event uses algorithm 0x${algorithmId.toString(16)} absent from Spec ID`);
    need(raw, i, digestSize, "TPMT_HA digest");
    const digest = Buffer.from(raw.subarray(i, i + digestSize)); i += digestSize;
    digests.push(Object.freeze({ algorithmId, hashAlgorithm: ALG[algorithmId] || null, digestHex: hexDigest(digest), digestSize }));
  }
  need(raw, i, 4, "TCG_PCR_EVENT2 eventSize");
  const eventSize = raw.readUInt32LE(i); i += 4;
  need(raw, i, eventSize, "TCG_PCR_EVENT2 event bytes");
  const event = Buffer.from(raw.subarray(i, i + eventSize)); i += eventSize;
  return Object.freeze({
    nextOffset: i,
    record: Object.freeze({ index, format: "TCG_PCR_EVENT2", pcrIndex, eventType, digests: Object.freeze(digests), eventSize, eventDigest: Native.sha256(event) }),
  });
}

function parsePcClientEventLog(raw) {
  if (!Buffer.isBuffer(raw) || raw.length === 0) throw new TypeError("raw PC Client event-log bytes required");
  const first = parseLegacyFirstEvent(raw, 0);
  const records = [first.record];
  let offset = first.nextOffset;
  while (offset < raw.length) {
    const parsed = parseEvent2(raw, offset, first.spec.digestSizes, records.length);
    if (parsed.nextOffset <= offset) throw new Error("event-log parser made no progress");
    records.push(parsed.record);
    offset = parsed.nextOffset;
  }
  const replayDigests = [];
  for (const record of records.slice(1)) {
    if (record.eventType === EVENT.EV_NO_ACTION) continue;
    for (const row of record.digests) {
      if (!row.hashAlgorithm) continue; // safely consumed but cannot be replayed by Node crypto
      replayDigests.push(Object.freeze({ pcr: record.pcrIndex, hashAlgorithm: row.hashAlgorithm, digestHex: row.digestHex }));
    }
  }
  const body = {
    schema: "holotrade.w33-pcclient-eventlog.v1",
    spec: {
      signature: first.spec.signature,
      platformClass: first.spec.platformClass,
      specVersionMajor: first.spec.specVersionMajor,
      specVersionMinor: first.spec.specVersionMinor,
      specErrata: first.spec.specErrata,
      uintnSize: first.spec.uintnSize,
      algorithms: first.spec.algorithms.map((x) => ({ algorithmId: x.algorithmId, hashAlgorithm: x.hashAlgorithm, digestSize: x.digestSize })),
    },
    recordCount: records.length,
    replayDigestCount: replayDigests.length,
    records,
    rawDigest: Native.sha256(raw),
  };
  return Object.freeze({ ...body, replayDigests: Object.freeze(replayDigests) });
}

function verifyTpmQuoteFromRawEventLog({ rawEventLog, ...quote }) {
  let parsed;
  try { parsed = parsePcClientEventLog(rawEventLog); }
  catch (error) { return Object.freeze({ ok: false, code: "TPM_RAW_EVENT_LOG_MALFORMED", error: error.message }); }
  const result = Native.verifyTpmQuoteNative({ ...quote, eventDigests: parsed.replayDigests });
  if (!result.ok) return Object.freeze({ ...result, rawEventLogDigest: parsed.rawDigest });
  return Object.freeze({
    ...result,
    code: "TPM_QUOTE_AND_RAW_PC_CLIENT_EVENT_LOG_VERIFIED",
    evidence: Object.freeze({ ...result.evidence, rawEventLogDigest: parsed.rawDigest, rawEventRecordCount: parsed.recordCount, replayDigestCount: parsed.replayDigestCount }),
    parsedEventLog: parsed,
  });
}

function keySpkiDigest(key) {
  const publicKey = crypto.createPublicKey(key);
  const der = publicKey.export({ type: "spki", format: "der" });
  return Native.sha256(der);
}

function certSpkiDigest(cert) { return keySpkiDigest(cert.publicKey); }

function certValidNow(cert, now) {
  const t = Number(now);
  return Number.isFinite(t) && Date.parse(cert.validFrom) <= t && t <= Date.parse(cert.validTo);
}

function verifyX509Path({ leafPem, intermediatesPem = [], rootPem, expectedPublicKey = null, now = Date.now(), role = "CERTIFICATE" }) {
  try {
    const leaf = new crypto.X509Certificate(leafPem);
    const intermediates = intermediatesPem.map((x) => new crypto.X509Certificate(x));
    const root = new crypto.X509Certificate(rootPem);
    const chain = [leaf, ...intermediates, root];
    const checks = {
      allTimeValid: chain.every((cert) => certValidNow(cert, now)),
      signaturesValid: chain.slice(0, -1).every((cert, i) => cert.verify(chain[i + 1].publicKey)),
      rootSelfSigned: root.verify(root.publicKey),
      publicKeyMatches: expectedPublicKey ? certSpkiDigest(leaf) === keySpkiDigest(expectedPublicKey) : true,
    };
    return Object.freeze({
      ok: Object.values(checks).every(Boolean),
      role,
      checks,
      leafSpkiDigest: certSpkiDigest(leaf),
      rootSpkiDigest: certSpkiDigest(root),
      leafSubject: leaf.subject,
      leafIssuer: leaf.issuer,
    });
  } catch (error) {
    return Object.freeze({ ok: false, role, code: "X509_PATH_INVALID", error: error.message });
  }
}

function verifyTpmCredentialProvenance({
  akCertificatePem,
  akIntermediatesPem = [],
  akRootPem,
  akPublicKey,
  ekCertificatePem = null,
  ekIntermediatesPem = [],
  ekRootPem = null,
  activationReceipt = null,
  enrollmentServicePublicKey = null,
  now = Date.now(),
}) {
  const ak = verifyX509Path({ leafPem: akCertificatePem, intermediatesPem: akIntermediatesPem, rootPem: akRootPem, expectedPublicKey: akPublicKey, now, role: "AK" });
  if (!ak.ok) return Object.freeze({ ok: false, code: "AK_PROVENANCE_INVALID", ak });
  let ek = null;
  if (ekCertificatePem || ekRootPem) {
    if (!(ekCertificatePem && ekRootPem)) return Object.freeze({ ok: false, code: "EK_PROVENANCE_INCOMPLETE", ak });
    ek = verifyX509Path({ leafPem: ekCertificatePem, intermediatesPem: ekIntermediatesPem, rootPem: ekRootPem, now, role: "EK" });
    if (!ek.ok) return Object.freeze({ ok: false, code: "EK_PROVENANCE_INVALID", ak, ek });
  }

  let activation = Object.freeze({ ok: false, status: "NOT_PROVIDED", provesAkEkResidencyBinding: false });
  if (activationReceipt) {
    try {
      if (!enrollmentServicePublicKey) throw new Error("enrollment-service public key required");
      const body = activationReceipt.body;
      if (!body || body.akSpkiDigest !== ak.leafSpkiDigest || (ek && body.ekSpkiDigest !== ek.leafSpkiDigest)) throw new Error("activation receipt key binding mismatch");
      if (body.expectedSecretDigest !== body.returnedSecretDigest) throw new Error("credential activation secret mismatch");
      const bytes = Buffer.from(JSON.stringify(body));
      const sig = Buffer.from(activationReceipt.signatureBase64, "base64");
      const signatureValid = crypto.verify(null, bytes, enrollmentServicePublicKey, sig);
      if (!signatureValid) throw new Error("activation receipt signature invalid");
      activation = Object.freeze({ ok: true, status: "SIGNED_ACTIVATION_RECEIPT", provesAkEkResidencyBinding: Boolean(ek), receiptDigest: Native.sha256(Buffer.concat([bytes, sig])) });
    } catch (error) {
      return Object.freeze({ ok: false, code: "CREDENTIAL_ACTIVATION_RECEIPT_INVALID", ak, ek, error: error.message });
    }
  }

  return Object.freeze({
    ok: true,
    code: activation.provesAkEkResidencyBinding ? "TPM_AK_EK_PROVENANCE_AND_ACTIVATION_BOUND" : "TPM_AK_PROVENANCE_VERIFIED",
    ak,
    ek,
    activation,
    honestyBoundary: activation.provesAkEkResidencyBinding
      ? "The signed enrollment receipt records successful credential activation for the authenticated AK/EK keys; the verifier does not itself execute TPM2_MakeCredential/ActivateCredential."
      : "X.509 key provenance does not by itself prove AK residency behind a specific EK.",
  });
}

module.exports = {
  EVENT,
  ALG,
  parseSpecIdEvent,
  parseLegacyFirstEvent,
  parseEvent2,
  parsePcClientEventLog,
  verifyTpmQuoteFromRawEventLog,
  keySpkiDigest,
  verifyX509Path,
  verifyTpmCredentialProvenance,
};
