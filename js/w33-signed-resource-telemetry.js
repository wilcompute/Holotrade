"use strict";

// Signed dynamic pricing telemetry for the seven typed W33 resource coordinates.
// The telemetry is an economic/control input, never a physical-energy claim.

const crypto = require("node:crypto");
const P = require("./w33-signed-resource-policy.js");

const TELEMETRY_SCHEMA = "holotrade.w33-resource-pricing-telemetry.v1";
const SIGNED_SCHEMA = "holotrade.w33-signed-resource-pricing-telemetry.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }

function buildPricingTelemetry({ workerId, runtimePublicKeyDigest, calibrationEpoch, pricingEpoch, validFromGeneration, validThroughGeneration, measurementDigest, unitPrices }) {
  if (!workerId) throw new TypeError("workerId required");
  if (!isDigest(runtimePublicKeyDigest)) throw new TypeError("runtimePublicKeyDigest must be sha256");
  if (!isDigest(measurementDigest)) throw new TypeError("measurementDigest must be sha256");
  natural(calibrationEpoch, "calibrationEpoch"); natural(pricingEpoch, "pricingEpoch");
  natural(validFromGeneration, "validFromGeneration"); natural(validThroughGeneration, "validThroughGeneration");
  if (validThroughGeneration < validFromGeneration) throw new RangeError("pricing telemetry generation interval is inverted");
  const prices = P.validateUnitPrices(unitPrices);
  const body = Object.freeze({
    schema: TELEMETRY_SCHEMA,
    workerId: String(workerId),
    runtimePublicKeyDigest,
    calibrationEpoch,
    pricingEpoch,
    validFromGeneration,
    validThroughGeneration,
    measurementDigest,
    unitPrices: prices,
  });
  return Object.freeze({ ...body, telemetryDigest: sha256(body) });
}

function signPricingTelemetry(telemetry, privateKey, keyId = "resource-pricing") {
  if (!telemetry || telemetry.schema !== TELEMETRY_SCHEMA || !isDigest(telemetry.telemetryDigest)) throw new TypeError("pricing telemetry body required");
  const bare = { ...telemetry }; delete bare.telemetryDigest;
  if (sha256(bare) !== telemetry.telemetryDigest) throw new Error("pricing telemetry digest mismatch before signing");
  if (!privateKey) throw new TypeError("pricing telemetry signing key required");
  const signature = crypto.sign(null, Buffer.from(stable(telemetry)), privateKey).toString("base64");
  const body = { schema: SIGNED_SCHEMA, telemetry, keyId: String(keyId), signature };
  return Object.freeze({ ...body, signedTelemetryDigest: sha256(body) });
}

function verifyPricingTelemetry(signed, trustedPublicKey, expected = {}) {
  if (!signed || signed.schema !== SIGNED_SCHEMA || !signed.telemetry || signed.telemetry.schema !== TELEMETRY_SCHEMA) throw new TypeError("signed pricing telemetry required");
  const t = signed.telemetry;
  const bare = { ...t }; delete bare.telemetryDigest;
  if (sha256(bare) !== t.telemetryDigest) throw new Error("pricing telemetry digest mismatch");
  const signedBare = { schema: SIGNED_SCHEMA, telemetry: t, keyId: signed.keyId, signature: signed.signature };
  if (sha256(signedBare) !== signed.signedTelemetryDigest) throw new Error("signed pricing telemetry identity mismatch");
  if (!trustedPublicKey) throw new TypeError("trusted pricing public key required");
  const ok = crypto.verify(null, Buffer.from(stable(t)), trustedPublicKey, Buffer.from(signed.signature, "base64"));
  if (!ok) throw new Error("pricing telemetry signature invalid");
  P.validateUnitPrices(t.unitPrices);
  if (expected.workerId != null && String(expected.workerId) !== t.workerId) throw new Error("pricing telemetry worker identity drift");
  if (expected.runtimePublicKeyDigest != null && expected.runtimePublicKeyDigest !== t.runtimePublicKeyDigest) throw new Error("pricing telemetry runtime key drift");
  if (expected.generation != null) {
    natural(expected.generation, "generation");
    if (expected.generation < t.validFromGeneration || expected.generation > t.validThroughGeneration) throw new Error("pricing telemetry not valid for continuation generation");
  }
  if (expected.minimumCalibrationEpoch != null && t.calibrationEpoch < natural(expected.minimumCalibrationEpoch, "minimumCalibrationEpoch")) throw new Error("pricing telemetry calibration epoch below floor");
  if (expected.minimumPricingEpoch != null && t.pricingEpoch < natural(expected.minimumPricingEpoch, "minimumPricingEpoch")) throw new Error("pricing telemetry pricing epoch below floor");
  return Object.freeze({ ...t, keyId: signed.keyId, signedTelemetryDigest: signed.signedTelemetryDigest });
}

module.exports = { TELEMETRY_SCHEMA, SIGNED_SCHEMA, sha256, buildPricingTelemetry, signPricingTelemetry, verifyPricingTelemetry };
