"use strict";

const crypto = require("node:crypto");
const { CborTag, encode, decode, mapToObject } = require("./cbor.js");
const { sha256Bytes } = require("./artifacts.js");

const COSE_SIGN1_TAG = 18;
const COSE_ALG_HEADER = 1;
const COSE_KID_HEADER = 4;
const COSE_EDDSA = -8;
const RECEIPT_SCHEMA = "holotrade.delivery-receipt.cose.v1";

function asBytes(value, name) {
  if (Buffer.isBuffer(value) || value instanceof Uint8Array) return Buffer.from(value);
  if (typeof value === "string") return Buffer.from(value, "utf8");
  throw new TypeError(`${name} must be bytes or a string`);
}

function protectedHeaders(keyId) {
  return encode(new Map([
    [COSE_ALG_HEADER, COSE_EDDSA],
    [COSE_KID_HEADER, asBytes(keyId, "keyId")],
  ]));
}

function signatureStructure(protectedBytes, payloadBytes, externalAAD = Buffer.alloc(0)) {
  return encode(["Signature1", protectedBytes, asBytes(externalAAD, "externalAAD"), payloadBytes]);
}

function signCoseSign1(payload, privateKey, { keyId = "holotrade-runtime", externalAAD = Buffer.alloc(0) } = {}) {
  if (!privateKey) throw new TypeError("an Ed25519 private key is required");
  const signingKey = privateKey && privateKey.type === "private" ? privateKey : crypto.createPrivateKey(privateKey);
  if (signingKey.asymmetricKeyType !== "ed25519") throw new TypeError("COSE EdDSA profile requires an Ed25519 private key");
  const payloadBytes = Buffer.isBuffer(payload) ? Buffer.from(payload) : encode(payload);
  const protectedBytes = protectedHeaders(keyId);
  const toSign = signatureStructure(protectedBytes, payloadBytes, externalAAD);
  const signature = crypto.sign(null, toSign, signingKey);
  const object = new CborTag(COSE_SIGN1_TAG, [
    protectedBytes,
    new Map(),
    payloadBytes,
    signature,
  ]);
  return encode(object);
}

function parseCoseSign1(coseBytes) {
  const decoded = decode(coseBytes);
  if (!(decoded instanceof CborTag) || decoded.tag !== COSE_SIGN1_TAG) {
    throw new Error("expected tagged COSE_Sign1 (CBOR tag 18)");
  }
  if (!Array.isArray(decoded.value) || decoded.value.length !== 4) {
    throw new Error("COSE_Sign1 must contain four fields");
  }
  const [protectedBytes, unprotected, payloadBytes, signature] = decoded.value;
  if (!Buffer.isBuffer(protectedBytes) || !(unprotected instanceof Map) ||
      !Buffer.isBuffer(payloadBytes) || !Buffer.isBuffer(signature)) {
    throw new Error("invalid COSE_Sign1 field types");
  }
  const headers = decode(protectedBytes);
  if (!(headers instanceof Map) || headers.get(COSE_ALG_HEADER) !== COSE_EDDSA) {
    throw new Error("COSE_Sign1 is not protected by EdDSA (-8)");
  }
  return { protectedBytes, headers, unprotected, payloadBytes, signature };
}

function verifyCoseSign1(coseBytes, publicKey, { externalAAD = Buffer.alloc(0) } = {}) {
  if (!publicKey) throw new TypeError("a trusted Ed25519 public key is required");
  try {
    const verificationKey = publicKey && publicKey.type === "public" ? publicKey : crypto.createPublicKey(publicKey);
    if (verificationKey.asymmetricKeyType !== "ed25519") throw new TypeError("COSE EdDSA profile requires an Ed25519 public key");
    const parsed = parseCoseSign1(coseBytes);
    const valid = crypto.verify(
      null,
      signatureStructure(parsed.protectedBytes, parsed.payloadBytes, externalAAD),
      verificationKey,
      parsed.signature
    );
    return {
      valid,
      algorithm: "EdDSA",
      coseAlgorithm: COSE_EDDSA,
      keyId: parsed.headers.has(COSE_KID_HEADER)
        ? Buffer.from(parsed.headers.get(COSE_KID_HEADER)).toString("utf8")
        : null,
      payloadBytes: Buffer.from(parsed.payloadBytes),
      payload: mapToObject(decode(parsed.payloadBytes)),
    };
  } catch (error) {
    return { valid: false, error: error.message, payload: null, payloadBytes: null };
  }
}

function signDeliveryReceipt(payload, privateKey, {
  publicKey = null,
  keyId = "holotrade-runtime",
  externalAAD = Buffer.alloc(0),
} = {}) {
  const coseBytes = signCoseSign1(payload, privateKey, { keyId, externalAAD });
  const trustedPublicKey = publicKey || crypto.createPublicKey(privateKey);
  return Object.freeze({
    schema: RECEIPT_SCHEMA,
    mediaType: "application/cose; cose-type=\"cose-sign1\"",
    algorithm: "EdDSA",
    keyId,
    payloadDigest: sha256Bytes(encode(payload)),
    coseDigest: sha256Bytes(coseBytes),
    coseSign1: coseBytes.toString("base64url"),
    publicKeySpki: trustedPublicKey.export({ type: "spki", format: "der" }).toString("base64url"),
    trustBoundary: "The embedded public key is transport metadata; a verifier must supply a trusted key.",
  });
}

function verifyDeliveryReceipt(envelope, trustedPublicKey, { externalAAD = Buffer.alloc(0) } = {}) {
  if (!envelope || envelope.schema !== RECEIPT_SCHEMA) {
    return { valid: false, error: "unsupported delivery receipt schema" };
  }
  if (!trustedPublicKey) {
    return { valid: false, error: "trusted public key is required; embedded key is not a trust root" };
  }
  const coseBytes = Buffer.from(envelope.coseSign1, "base64url");
  if (sha256Bytes(coseBytes) !== envelope.coseDigest) {
    return { valid: false, error: "COSE envelope digest mismatch" };
  }
  const result = verifyCoseSign1(coseBytes, trustedPublicKey, { externalAAD });
  if (!result.valid) return result;
  if (result.keyId !== envelope.keyId) {
    return { ...result, valid: false, error: "protected key id does not match envelope metadata" };
  }
  if (sha256Bytes(result.payloadBytes) !== envelope.payloadDigest) {
    return { ...result, valid: false, error: "signed payload digest mismatch" };
  }
  return result;
}

module.exports = {
  COSE_SIGN1_TAG,
  COSE_EDDSA,
  RECEIPT_SCHEMA,
  signCoseSign1,
  parseCoseSign1,
  verifyCoseSign1,
  signDeliveryReceipt,
  verifyDeliveryReceipt,
};
