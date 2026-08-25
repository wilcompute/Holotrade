// ======================================================================
// HOLOTRADE ED25519 SIGNING BOUNDARY
//
// Adds a real asymmetric signature around canonical transition-certificate
// bytes while preserving the distinction between integrity, signatures, and
// remote attestation. This is local Ed25519 signing with Node.js crypto.
//
// The envelope is DSSE-shaped (payloadType + base64 payload + signatures)
// but is intentionally named holotrade.dsse-shaped.v1 rather than claiming
// standards conformance without a reference-library interoperability test.
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
    return Buffer.from(typeof value === "string" ? value : E.canonicalJson(value), "utf8");
  }

  function keyId(publicKey) {
    const der = publicKey.export({ type: "spki", format: "der" });
    return crypto.createHash("sha256").update(der).digest("hex");
  }

  function preauth(payloadType, payload) {
    const type = bytes(payloadType);
    const p = Buffer.isBuffer(payload) ? payload : bytes(payload);
    return Buffer.concat([
      Buffer.from("DSSEv1 "),
      Buffer.from(String(type.length)),
      Buffer.from(" "),
      type,
      Buffer.from(" "),
      Buffer.from(String(p.length)),
      Buffer.from(" "),
      p,
    ]);
  }

  function generateKeyPair() {
    return crypto.generateKeyPairSync("ed25519");
  }

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
      signatures: [{
        keyid: keyId(publicKey),
        sig: signature.toString("base64"),
        algorithm: "ed25519",
      }],
      publicKey: publicKey.export({ type: "spki", format: "pem" }).toString(),
      boundary:
        "Real local Ed25519 signature over DSSE-style pre-authentication bytes. No remote attestation, key transparency, certificate authority, Sigstore bundle, or external timestamp is claimed.",
    };
    return Object.freeze(envelope);
  }

  function verify(envelope, expectedPayload = null) {
    if (!envelope || envelope.schema !== SCHEMA || !Array.isArray(envelope.signatures) || envelope.signatures.length !== 1) {
      return { ok: false, code: "SHAPE" };
    }
    try {
      const payload = Buffer.from(envelope.payload, "base64");
      if (expectedPayload !== null && !payload.equals(bytes(expectedPayload))) {
        return { ok: false, code: "PAYLOAD_MISMATCH" };
      }
      const publicKey = crypto.createPublicKey(envelope.publicKey);
      if (keyId(publicKey) !== envelope.signatures[0].keyid) return { ok: false, code: "KEYID" };
      const signature = Buffer.from(envelope.signatures[0].sig, "base64");
      const ok = crypto.verify(null, preauth(envelope.payloadType, payload), publicKey, signature);
      return { ok, code: ok ? "OK" : "BAD_SIGNATURE", payload: ok ? JSON.parse(payload.toString("utf8")) : null };
    } catch (error) {
      return { ok: false, code: "VERIFY_ERROR", error: String(error.message || error) };
    }
  }

  const API = { SCHEMA, PAYLOAD_TYPE, preauth, generateKeyPair, sign, verify, keyId };
  root.HolotradeSigning = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
