// ======================================================================
// HOLOTRADE ED25519 / DSSE SIGNING BOUNDARY
//
// Real Ed25519 signatures over DSSE v1 pre-authentication encoding (PAE).
// Trust establishment is explicitly external: DSSE keyid is only a hint, so
// threshold verification accepts an application-supplied trusted-key set.
//
// Legacy `sign()` keeps the self-contained demo envelope used by the browser
// tests. `signDSSE()` emits the strict DSSE JSON shape: payloadType, payload,
// signatures. Neither path is remote attestation or transparency logging.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  let crypto = null;
  if (typeof require !== "undefined") {
    try { crypto = require("node:crypto"); } catch (_) { crypto = null; }
  }
  if (!E || !crypto) throw new Error("signing requires evidence.js and node:crypto");

  const SCHEMA = "holotrade.dsse-shaped.v1";
  const PAYLOAD_TYPE = "application/vnd.holotrade.transition-certificate+json";

  function bytes(value) {
    if (Buffer.isBuffer(value)) return value;
    if (value instanceof Uint8Array) return Buffer.from(value);
    return Buffer.from(typeof value === "string" ? value : E.canonicalJson(value), "utf8");
  }

  function keyId(publicKey) {
    const key = publicKey && publicKey.type ? publicKey : crypto.createPublicKey(publicKey);
    const der = key.export({ type: "spki", format: "der" });
    return crypto.createHash("sha256").update(der).digest("hex");
  }

  function preauth(payloadType, payload) {
    const type = bytes(payloadType);
    const p = bytes(payload);
    return Buffer.concat([
      Buffer.from("DSSEv1 ", "utf8"),
      Buffer.from(String(type.length), "utf8"),
      Buffer.from(" ", "utf8"),
      type,
      Buffer.from(" ", "utf8"),
      Buffer.from(String(p.length), "utf8"),
      Buffer.from(" ", "utf8"),
      p,
    ]);
  }

  function generateKeyPair() {
    return crypto.generateKeyPairSync("ed25519");
  }

  /** Legacy self-contained local-signature envelope. */
  function sign(payload, privateKey, publicKey, payloadType = PAYLOAD_TYPE) {
    if (!privateKey || !publicKey) throw new TypeError("privateKey and publicKey are required");
    const canonical = bytes(payload);
    const signature = crypto.sign(null, preauth(payloadType, canonical), privateKey);
    const envelope = {
      schema: SCHEMA,
      securityMode: "ED25519_LOCAL_SIGNATURE",
      cryptographicallySigned: true,
      remotelyAttested: false,
      payloadType,
      payload: canonical.toString("base64"),
      signatures: [{ keyid: keyId(publicKey), sig: signature.toString("base64"), algorithm: "ed25519" }],
      publicKey: publicKey.export({ type: "spki", format: "pem" }).toString(),
      boundary:
        "Real local Ed25519 signature over DSSE PAE bytes. Embedded publicKey makes this self-contained for verification but is not a trust root, CA binding, transparency proof, or remote attestation.",
    };
    return Object.freeze(envelope);
  }

  function verify(envelope, expectedPayload = null) {
    if (!envelope || envelope.schema !== SCHEMA || !Array.isArray(envelope.signatures) || envelope.signatures.length !== 1) {
      return { ok: false, code: "SHAPE" };
    }
    try {
      const payload = Buffer.from(envelope.payload, "base64");
      if (expectedPayload !== null && !payload.equals(bytes(expectedPayload))) return { ok: false, code: "PAYLOAD_MISMATCH" };
      const publicKey = crypto.createPublicKey(envelope.publicKey);
      if (keyId(publicKey) !== envelope.signatures[0].keyid) return { ok: false, code: "KEYID" };
      const signature = Buffer.from(envelope.signatures[0].sig, "base64");
      const ok = crypto.verify(null, preauth(envelope.payloadType, payload), publicKey, signature);
      return { ok, code: ok ? "OK" : "BAD_SIGNATURE", payload: ok ? JSON.parse(payload.toString("utf8")) : null };
    } catch (error) {
      return { ok: false, code: "VERIFY_ERROR", error: String(error.message || error) };
    }
  }

  /**
   * Strict DSSE JSON envelope. Signers are [{privateKey, publicKey}].
   * No algorithm/public-key fields are placed inside DSSE signatures because
   * the DSSE spec deliberately leaves cryptographic choice and trust external.
   */
  function signDSSE(payload, signers, payloadType = PAYLOAD_TYPE) {
    if (!Array.isArray(signers) || signers.length === 0) throw new TypeError("at least one signer is required");
    const canonical = bytes(payload);
    const pae = preauth(payloadType, canonical);
    const signatures = signers.map(({ privateKey, publicKey }) => {
      if (!privateKey || !publicKey) throw new TypeError("each signer requires privateKey and publicKey");
      return Object.freeze({
        keyid: keyId(publicKey),
        sig: crypto.sign(null, pae, privateKey).toString("base64"),
      });
    }).sort((a, b) => a.keyid.localeCompare(b.keyid));
    const seen = new Set();
    for (const row of signatures) {
      if (seen.has(row.keyid)) throw new Error(`duplicate signer keyid ${row.keyid}`);
      seen.add(row.keyid);
    }
    return Object.freeze({ payloadType, payload: canonical.toString("base64"), signatures: Object.freeze(signatures) });
  }

  function normalizeTrustedKeys(trustedKeys) {
    const rows = trustedKeys instanceof Map ? [...trustedKeys.entries()] : Object.entries(trustedKeys || {});
    const out = new Map();
    for (const [label, keyValue] of rows) {
      const key = keyValue && keyValue.type ? keyValue : crypto.createPublicKey(keyValue);
      const fingerprint = keyId(key);
      // Callers may key the map by arbitrary label or by the fingerprint. The
      // actual security identity is recomputed from the supplied key bytes.
      out.set(fingerprint, { key, label: String(label) });
    }
    return out;
  }

  /**
   * Verify t-of-n DSSE signatures against APPLICATION-SUPPLIED trusted keys.
   * keyid is used only to order candidate verification attempts; a signature
   * counts only after cryptographic verification by a trusted public key.
   */
  function verifyThreshold(envelope, trustedKeys, { threshold = 1, expectedPayload = null, expectedPayloadType = null } = {}) {
    if (!envelope || typeof envelope !== "object" || typeof envelope.payloadType !== "string" ||
        typeof envelope.payload !== "string" || !Array.isArray(envelope.signatures) || envelope.signatures.length === 0) {
      return { ok: false, code: "SHAPE", verifiedKeyIds: [], threshold };
    }
    if (!Number.isInteger(threshold) || threshold < 1) throw new RangeError("threshold must be a positive integer");
    try {
      const payload = Buffer.from(envelope.payload, "base64");
      if (expectedPayloadType !== null && envelope.payloadType !== expectedPayloadType) {
        return { ok: false, code: "PAYLOAD_TYPE_MISMATCH", verifiedKeyIds: [], threshold };
      }
      if (expectedPayload !== null && !payload.equals(bytes(expectedPayload))) {
        return { ok: false, code: "PAYLOAD_MISMATCH", verifiedKeyIds: [], threshold };
      }
      const trusted = normalizeTrustedKeys(trustedKeys);
      if (trusted.size < threshold) return { ok: false, code: "INSUFFICIENT_TRUSTED_KEYS", verifiedKeyIds: [], threshold };
      const pae = preauth(envelope.payloadType, payload);
      const verified = new Set();
      const signatureResults = [];
      for (const sigRow of envelope.signatures) {
        let matched = null;
        const candidates = [];
        if (sigRow.keyid && trusted.has(sigRow.keyid)) candidates.push([sigRow.keyid, trusted.get(sigRow.keyid)]);
        for (const entry of trusted.entries()) if (!candidates.some(([id]) => id === entry[0])) candidates.push(entry);
        const sigBytes = Buffer.from(sigRow.sig, "base64");
        for (const [fingerprint, row] of candidates) {
          if (verified.has(fingerprint)) continue;
          if (crypto.verify(null, pae, row.key, sigBytes)) {
            matched = fingerprint;
            verified.add(fingerprint);
            break;
          }
        }
        signatureResults.push({ hintedKeyId: sigRow.keyid || null, verifiedKeyId: matched, ok: matched !== null });
      }
      const ok = verified.size >= threshold;
      return {
        ok,
        code: ok ? "OK" : "THRESHOLD_NOT_MET",
        threshold,
        verifiedCount: verified.size,
        verifiedKeyIds: [...verified].sort(),
        signatureResults,
        payload: ok ? JSON.parse(payload.toString("utf8")) : null,
        trustBoundary: "Only caller-supplied trusted public keys can satisfy threshold verification; DSSE keyid is never treated as authority.",
      };
    } catch (error) {
      return { ok: false, code: "VERIFY_ERROR", error: String(error.message || error), verifiedKeyIds: [], threshold };
    }
  }

  const API = {
    SCHEMA,
    PAYLOAD_TYPE,
    preauth,
    generateKeyPair,
    sign,
    verify,
    signDSSE,
    verifyThreshold,
    keyId,
  };
  root.HolotradeSigning = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
