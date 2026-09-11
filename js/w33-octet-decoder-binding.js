"use strict";

// Content-addressed execution contract for the certified W33 octet decoder.
//
// The pre-execution policy binds the exact finite decoder library/version and an
// independently trusted exact-depth certificate into measured boot.  The worker
// may then return a decoder receipt, but the receipt is accepted as OPTIMUM only
// when its strict-descent chain ends at the policy's certified exact depth.
// Consequently a radius-two local minimum cannot be substituted for the exact
// decoded result merely because the local move set stalls there.

const crypto = require("node:crypto");

const POLICY_SCHEMA = "holotrade.w33-octet-decoder-policy.v1";
const RECEIPT_SCHEMA = "holotrade.w33-octet-decoder-receipt.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }
function digest(value,name) { if (!isDigest(value)) throw new TypeError(`${name} must be a sha256 content identity`); return value; }

function verifyDecoderPolicy(policy) {
  if (!policy || policy.schema !== POLICY_SCHEMA) throw new TypeError("certified octet decoder policy required");
  const body = {
    schema: POLICY_SCHEMA,
    decoderVersion: String(policy.decoderVersion || ""),
    radiusTwoLibraryDigest: digest(policy.radiusTwoLibraryDigest,"radiusTwoLibraryDigest"),
    circuitLibraryDigest: digest(policy.circuitLibraryDigest,"circuitLibraryDigest"),
    decoderLibraryDigest: digest(policy.decoderLibraryDigest,"decoderLibraryDigest"),
    decoderCertificateDigest: digest(policy.decoderCertificateDigest,"decoderCertificateDigest"),
    exactDepthCertificateDigest: digest(policy.exactDepthCertificateDigest,"exactDepthCertificateDigest"),
    inputPreimageDigest: digest(policy.inputPreimageDigest,"inputPreimageDigest"),
    fiberDigest: digest(policy.fiberDigest,"fiberDigest"),
    certifiedExactDepth: natural(policy.certifiedExactDepth,"certifiedExactDepth"),
  };
  if (!body.decoderVersion) throw new TypeError("decoderVersion required");
  const decoderPolicyDigest = sha256(body);
  if (policy.decoderPolicyDigest != null && policy.decoderPolicyDigest !== decoderPolicyDigest) throw new Error("decoderPolicyDigest mismatch");
  return Object.freeze({ ...body, decoderPolicyDigest });
}

function verifyDecoderReceipt(receipt, verifiedPolicy) {
  const policy = verifiedPolicy && verifiedPolicy.decoderPolicyDigest ? verifiedPolicy : verifyDecoderPolicy(verifiedPolicy);
  if (!receipt || receipt.schema !== RECEIPT_SCHEMA) throw new TypeError("octet decoder receipt required");
  if (receipt.decoderPolicyDigest !== policy.decoderPolicyDigest) throw new Error("decoder receipt policy identity drift");
  const initialNegativeMass = natural(receipt.initialNegativeMass,"initialNegativeMass");
  const finalNegativeMass = natural(receipt.finalNegativeMass,"finalNegativeMass");
  if (receipt.status !== "OPTIMUM") throw new Error("certified decoder delivery requires OPTIMUM status");
  if (finalNegativeMass !== policy.certifiedExactDepth) throw new Error("decoder result does not reach independently certified exact depth");
  if (finalNegativeMass > initialNegativeMass) throw new Error("decoder receipt increases negativity");
  digest(receipt.finalPreimageDigest,"finalPreimageDigest");
  if (!Array.isArray(receipt.steps)) throw new TypeError("decoder receipt steps must be an array");
  let cursor = initialNegativeMass;
  const steps = receipt.steps.map((step,i) => {
    if (!step || typeof step !== "object") throw new TypeError(`decoder step ${i} invalid`);
    const before=natural(step.before,`steps[${i}].before`), after=natural(step.after,`steps[${i}].after`);
    if (before !== cursor) throw new Error(`decoder step ${i} chain discontinuity`);
    if (!(after < before)) throw new Error(`decoder step ${i} must strictly decrease negativity`);
    if (step.kind !== "radius2" && step.kind !== "circuit") throw new TypeError(`decoder step ${i} has unknown move kind`);
    digest(step.moveDigest,`steps[${i}].moveDigest`);
    cursor=after;
    return Object.freeze({ kind:step.kind,before,after,moveDigest:step.moveDigest });
  });
  if (cursor !== finalNegativeMass) throw new Error("decoder step chain does not terminate at declared final negativity");
  const body={
    schema:RECEIPT_SCHEMA,
    decoderPolicyDigest:policy.decoderPolicyDigest,
    status:"OPTIMUM",
    initialNegativeMass,
    finalNegativeMass,
    finalPreimageDigest:receipt.finalPreimageDigest,
    steps,
  };
  const decoderResultDigest=sha256(body);
  if (receipt.decoderResultDigest != null && receipt.decoderResultDigest !== decoderResultDigest) throw new Error("decoderResultDigest mismatch");
  return Object.freeze({ ...body, decoderResultDigest });
}

module.exports={ POLICY_SCHEMA, RECEIPT_SCHEMA, sha256, verifyDecoderPolicy, verifyDecoderReceipt };
