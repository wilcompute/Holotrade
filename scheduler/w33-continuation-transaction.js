"use strict";

// Replayable end-to-end HoloVM continuation transaction.
//
// One invocation now owns the exact sequence:
//   scheduler selection -> continuation-bound hardware challenge -> verifier
//   verdict -> verified binding -> worker execution receipt -> exact child
//   continuation -> signed Holotrade delivery receipt.
//
// The worker callback is an explicit cross-repository ABI. It must return the
// W33 HoloVM emission identity produced by the W33 process kernel; Holotrade
// does not reimplement guest semantics. Every identity is rebound into the
// final signed receipt and verification fails closed on parent/process/
// generation drift.

const crypto = require("node:crypto");
const S = require("./w33-continuation-scheduler.js");
const C = require("../js/w33-continuation-attestation.js");

const EXECUTION_SCHEMA = "w33.holovm-cross-repo-execution.v1";
const DELIVERY_SCHEMA = "holotrade.w33-continuation-delivery.v1";
const SIGNED_SCHEMA = "holotrade.w33-signed-continuation-delivery.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;
}

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function natural(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`);
  return value;
}

function normalizeExecution(execution, request) {
  if (!execution || typeof execution !== "object") throw new TypeError("worker execution receipt required");
  if (execution.schema !== EXECUTION_SCHEMA) throw new TypeError("unexpected W33 execution schema");
  for (const name of ["parentContinuationRoot", "childContinuationRoot", "processId", "emissionId"]) {
    if (!isDigest(execution[name])) throw new TypeError(`${name} must be a sha256 identity`);
  }
  natural(execution.generationBefore, "generationBefore");
  natural(execution.generationAfter, "generationAfter");
  if (!Array.isArray(execution.guestReceiptIds) || !execution.guestReceiptIds.length || !execution.guestReceiptIds.every(isDigest)) {
    throw new TypeError("guestReceiptIds must be a nonempty digest array");
  }
  if (execution.parentContinuationRoot !== request.continuationRoot) throw new Error("worker execution parent continuation drift");
  if (execution.processId !== request.processId) throw new Error("worker execution process identity drift");
  if (execution.generationBefore !== request.generation) throw new Error("worker execution generation-before drift");
  if (execution.generationAfter <= execution.generationBefore) throw new Error("worker execution must advance generation");
  const body = {
    schema: EXECUTION_SCHEMA,
    parentContinuationRoot: execution.parentContinuationRoot,
    childContinuationRoot: execution.childContinuationRoot,
    processId: execution.processId,
    generationBefore: execution.generationBefore,
    generationAfter: execution.generationAfter,
    emissionId: execution.emissionId,
    guestReceiptIds: [...execution.guestReceiptIds],
    stopReason: String(execution.stopReason || "unknown"),
  };
  return Object.freeze({ ...body, executionDigest: sha256(body) });
}

function deliveryBody(dispatch, binding, execution) {
  const body = {
    schema: DELIVERY_SCHEMA,
    dispatchDigest: dispatch.dispatchDigest,
    workerId: dispatch.workerId,
    attestationBindingDigest: binding.bindingDigest,
    verifierVerdictDigest: binding.verifierVerdictDigest,
    runtimePublicKeyDigest: binding.runtimePublicKeyDigest,
    topologyAttestationDigest: dispatch.topologyAttestationDigest,
    parentContinuationRoot: execution.parentContinuationRoot,
    childContinuationRoot: execution.childContinuationRoot,
    processId: execution.processId,
    generationBefore: execution.generationBefore,
    generationAfter: execution.generationAfter,
    emissionId: execution.emissionId,
    guestReceiptIds: execution.guestReceiptIds,
    executionDigest: execution.executionDigest,
  };
  return Object.freeze({ ...body, deliveryDigest: sha256(body) });
}

function signDelivery(delivery, privateKey, keyId = "holotrade-delivery") {
  if (!delivery || delivery.schema !== DELIVERY_SCHEMA || !isDigest(delivery.deliveryDigest)) throw new TypeError("delivery body required");
  if (!privateKey) throw new TypeError("delivery signing key required");
  const payload = Buffer.from(stable(delivery));
  const signature = crypto.sign(null, payload, privateKey).toString("base64");
  return Object.freeze({
    schema: SIGNED_SCHEMA,
    body: delivery,
    keyId: String(keyId),
    signature,
    signedReceiptDigest: sha256({ schema: SIGNED_SCHEMA, body: delivery, keyId: String(keyId), signature }),
  });
}

function verifyDelivery(signed, publicKey) {
  if (!signed || signed.schema !== SIGNED_SCHEMA || !signed.body || signed.body.schema !== DELIVERY_SCHEMA) {
    return Object.freeze({ ok: false, code: "DELIVERY_SCHEMA_INVALID" });
  }
  const bare = { ...signed.body };
  delete bare.deliveryDigest;
  if (sha256(bare) !== signed.body.deliveryDigest) return Object.freeze({ ok: false, code: "DELIVERY_DIGEST_MISMATCH" });
  const ok = crypto.verify(null, Buffer.from(stable(signed.body)), publicKey, Buffer.from(signed.signature, "base64"));
  if (!ok) return Object.freeze({ ok: false, code: "DELIVERY_SIGNATURE_INVALID" });
  return Object.freeze({ ok: true, code: "DELIVERY_VERIFIED", deliveryDigest: signed.body.deliveryDigest, signedReceiptDigest: signed.signedReceiptDigest });
}

function executeContinuationTransaction({
  candidates,
  request,
  policy = {},
  obtainSignedVerifierVerdict,
  signedVerifierVerdict,
  trustedVerifierPublicKey,
  executeWorker,
  deliveryPrivateKey,
  deliveryKeyId = "holotrade-delivery",
}) {
  if (typeof executeWorker !== "function") throw new TypeError("executeWorker callback required");
  if (typeof obtainSignedVerifierVerdict !== "function" && !signedVerifierVerdict) {
    throw new TypeError("obtainSignedVerifierVerdict callback or signedVerifierVerdict required");
  }
  const selected = S.chooseContinuationWorker(candidates, request, policy);
  if (!selected.ok) throw new Error(selected.code);
  const dispatch = selected.dispatch;
  const verdict = typeof obtainSignedVerifierVerdict === "function"
    ? obtainSignedVerifierVerdict(Object.freeze({ challenge: dispatch.challenge, dispatch, request }))
    : signedVerifierVerdict;
  if (!verdict) throw new TypeError("verifier callback returned no signed verdict");
  const binding = C.verifiedContinuationBinding(
    request.passport,
    request.contract,
    dispatch.challenge,
    verdict,
    trustedVerifierPublicKey
  );
  const rawExecution = executeWorker(Object.freeze({ dispatch, binding, request }));
  const execution = normalizeExecution(rawExecution, request);
  const delivery = deliveryBody(dispatch, binding, execution);
  const signedDelivery = signDelivery(delivery, deliveryPrivateKey, deliveryKeyId);
  return Object.freeze({
    ok: true,
    code: "CONTINUATION_TRANSACTION_COMMITTED",
    dispatch,
    attestation: binding,
    execution,
    delivery: signedDelivery,
    transactionDigest: sha256({
      dispatchDigest: dispatch.dispatchDigest,
      bindingDigest: binding.bindingDigest,
      executionDigest: execution.executionDigest,
      signedReceiptDigest: signedDelivery.signedReceiptDigest,
    }),
  });
}

module.exports = {
  EXECUTION_SCHEMA,
  DELIVERY_SCHEMA,
  SIGNED_SCHEMA,
  sha256,
  normalizeExecution,
  deliveryBody,
  signDelivery,
  verifyDelivery,
  executeContinuationTransaction,
};
