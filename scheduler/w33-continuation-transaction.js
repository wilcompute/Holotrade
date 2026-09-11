"use strict";

// Replayable end-to-end HoloVM continuation transaction.
//
// One invocation owns scheduler selection -> continuation/execution-context-
// bound hardware challenge -> verifier verdict -> verified binding -> worker
// execution -> exact child continuation -> signed Holotrade delivery receipt.
//
// Strict admission, topology/failure context, optional accelerator state,
// typed signed-resource selection, price-independent representation market
// identity, and optional representation-history MMR root are first-class
// execution context. Resource coordinates A/A^2 are estimator/representation
// metadata, never physical energy surrogates.

const crypto = require("node:crypto");
const S = require("./w33-continuation-scheduler.js");
const C = require("../js/w33-continuation-attestation.js");

const EXECUTION_SCHEMA = "w33.holovm-cross-repo-execution.v1";
const DELIVERY_SCHEMA = "holotrade.w33-continuation-delivery.v1";
const SIGNED_SCHEMA = "holotrade.w33-signed-continuation-delivery.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }
function equalArray(a, b) { return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((x, i) => x === b[i]); }

function normalizeExecution(execution, request) {
  if (!execution || typeof execution !== "object") throw new TypeError("worker execution receipt required");
  if (execution.schema !== EXECUTION_SCHEMA) throw new TypeError("unexpected W33 execution schema");
  for (const name of ["parentContinuationRoot", "childContinuationRoot", "processId", "emissionId"]) if (!isDigest(execution[name])) throw new TypeError(`${name} must be a sha256 identity`);
  natural(execution.generationBefore, "generationBefore"); natural(execution.generationAfter, "generationAfter");
  if (!Array.isArray(execution.guestReceiptIds) || !execution.guestReceiptIds.length || !execution.guestReceiptIds.every(isDigest)) throw new TypeError("guestReceiptIds must be a nonempty digest array");
  if (execution.intermediateContinuationRoots != null && (!Array.isArray(execution.intermediateContinuationRoots) || !execution.intermediateContinuationRoots.length || !execution.intermediateContinuationRoots.every(isDigest))) throw new TypeError("intermediateContinuationRoots must be a nonempty digest array when supplied");
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
    ...(execution.intermediateContinuationRoots == null ? {} : { intermediateContinuationRoots: [...execution.intermediateContinuationRoots] }),
    stopReason: String(execution.stopReason || "unknown"),
  };
  return Object.freeze({ ...body, executionDigest: sha256(body) });
}

function executionContextAgreement(dispatch, binding) {
  if ((dispatch.executionPolicyDigest || null) !== (binding.executionPolicyDigest || null)) throw new Error("dispatch and hardware binding disagree on execution policy");
  if ((dispatch.strictAdmissionBindingDigest || null) !== (binding.strictAdmissionBindingDigest || null)) throw new Error("dispatch and hardware binding disagree on strict admission identity");
  if ((dispatch.acceleratorCertificateDigest || null) !== (binding.acceleratorCertificateDigest || null)) throw new Error("dispatch and hardware binding disagree on accelerator certificate");
  if ((dispatch.signedResourceCertificateDigest || null) !== (binding.signedResourceCertificateDigest || null)) throw new Error("dispatch and hardware binding disagree on signed-resource certificate");
  if ((dispatch.signedResourceSelectionDigest || null) !== (binding.signedResourceSelectionDigest || null)) throw new Error("dispatch and hardware binding disagree on signed-resource selection");
  if ((dispatch.representationMarketIdentityDigest || null) !== (binding.representationMarketIdentityDigest || null)) throw new Error("dispatch and hardware binding disagree on representation market identity");
  if ((dispatch.representationMarketHistoryRootDigest || null) !== (binding.representationMarketHistoryRootDigest || null)) throw new Error("dispatch and hardware binding disagree on representation market history root");
  if (dispatch.topologyAttestationDigest !== binding.topologyAttestationDigest) throw new Error("dispatch and hardware binding disagree on topology attestation");
  if ((dispatch.failureAssessmentDigest || null) !== (binding.failureAssessmentDigest || null)) throw new Error("dispatch and hardware binding disagree on failure assessment");
  return true;
}

function acceleratorExecutionAgreement(request, execution) {
  const cert = request.acceleratorCertificate;
  if (!cert) return true;
  if (execution.parentContinuationRoot !== cert.parentContinuationRoot) throw new Error("accelerated execution parent disagrees with certificate");
  if (execution.childContinuationRoot !== cert.childContinuationRoot) throw new Error("accelerated execution child disagrees with certificate");
  if (execution.processId !== cert.processId) throw new Error("accelerated execution process disagrees with certificate");
  if (execution.generationBefore !== cert.generationBefore || execution.generationAfter !== cert.generationAfter) throw new Error("accelerated execution generation span disagrees with certificate");
  if (!equalArray(execution.guestReceiptIds, cert.subreceiptIds)) throw new Error("accelerated execution receipt interval disagrees with certificate");
  if (!equalArray(execution.intermediateContinuationRoots, cert.intermediateContinuationRoots)) throw new Error("accelerated execution continuation interval disagrees with certificate");
  if (sha256(execution.guestReceiptIds) !== cert.receiptChainDigest) throw new Error("accelerated execution receipt-chain digest mismatch");
  if (sha256(execution.intermediateContinuationRoots) !== cert.continuationChainDigest) throw new Error("accelerated execution continuation-chain digest mismatch");
  return true;
}

function deliveryBody(dispatch, binding, execution) {
  executionContextAgreement(dispatch, binding);
  const body = {
    schema: DELIVERY_SCHEMA,
    dispatchDigest: dispatch.dispatchDigest,
    workerId: dispatch.workerId,
    attestationBindingDigest: binding.bindingDigest,
    verifierVerdictDigest: binding.verifierVerdictDigest,
    runtimePublicKeyDigest: binding.runtimePublicKeyDigest,
    topologyAttestationDigest: dispatch.topologyAttestationDigest,
    ...(dispatch.failureAssessmentDigest == null ? {} : {
      failureAssessmentDigest: dispatch.failureAssessmentDigest,
      additionalFailuresToBlockAllLines: dispatch.additionalFailuresToBlockAllLines,
      failureDistanceExact: dispatch.failureDistanceExact === true,
    }),
    ...(dispatch.executionPolicyDigest == null ? {} : { executionPolicyDigest: dispatch.executionPolicyDigest }),
    ...(dispatch.strictAdmissionBindingDigest == null ? {} : {
      strictAdmissionBindingDigest: dispatch.strictAdmissionBindingDigest,
      handoffDigest: dispatch.handoffDigest,
      jointPlanDigest: dispatch.jointPlanDigest,
      strategyDigest: dispatch.strategyDigest,
      strictPlacementDigest: dispatch.strictPlacementDigest,
      strictSnapshotProblemRoot: dispatch.strictSnapshotProblemRoot,
      baselineRetainedUnionBytes: dispatch.baselineRetainedUnionBytes,
      postAdmissionRetainedUnionBytes: dispatch.postAdmissionRetainedUnionBytes,
      retainedUnionDeltaBytes: dispatch.retainedUnionDeltaBytes,
    }),
    ...(dispatch.acceleratorCertificateDigest == null ? {} : {
      acceleratorCertificateDigest: dispatch.acceleratorCertificateDigest,
      acceleratorReceiptChainDigest: dispatch.acceleratorReceiptChainDigest,
      acceleratorContinuationChainDigest: dispatch.acceleratorContinuationChainDigest,
      acceleratorSymplecticFrameDigest: dispatch.acceleratorSymplecticFrameDigest,
      acceleratorSteinbergActionDigest: dispatch.acceleratorSteinbergActionDigest,
      acceleratorExecutableTransvections: dispatch.acceleratorExecutableTransvections,
      acceleratorCalibrationEpoch: dispatch.acceleratorCalibrationEpoch,
      acceleratorPhysicalCalibrationEvidenceDigest: dispatch.acceleratorPhysicalCalibrationEvidenceDigest,
    }),
    ...(dispatch.signedResourceCertificateDigest == null ? {} : {
      signedResourceCertificateDigest: dispatch.signedResourceCertificateDigest,
      signedResourceSelectionDigest: dispatch.signedResourceSelectionDigest,
      representationMarketIdentityDigest: dispatch.representationMarketIdentityDigest,
      ...(dispatch.representationMarketHistoryRootDigest == null ? {} : {
        representationMarketHistoryRootDigest: dispatch.representationMarketHistoryRootDigest,
        representationMarketHistoryEventCount: dispatch.representationMarketHistoryEventCount,
        representationMarketHistoryDigest: dispatch.representationMarketHistoryDigest,
      }),
      representationClass: dispatch.representationClass,
      representationAmplification: dispatch.representationAmplification,
      signedSamplingSecondMomentFactor: dispatch.signedSamplingSecondMomentFactor,
      signedResourceVector: dispatch.signedResourceVector,
      signedResourcePriceDigest: dispatch.signedResourcePriceDigest,
    }),
    parentContinuationRoot: execution.parentContinuationRoot,
    childContinuationRoot: execution.childContinuationRoot,
    processId: execution.processId,
    generationBefore: execution.generationBefore,
    generationAfter: execution.generationAfter,
    emissionId: execution.emissionId,
    guestReceiptIds: execution.guestReceiptIds,
    ...(execution.intermediateContinuationRoots == null ? {} : { intermediateContinuationRoots: execution.intermediateContinuationRoots }),
    executionDigest: execution.executionDigest,
  };
  return Object.freeze({ ...body, deliveryDigest: sha256(body) });
}

function signDelivery(delivery, privateKey, keyId = "holotrade-delivery") {
  if (!delivery || delivery.schema !== DELIVERY_SCHEMA || !isDigest(delivery.deliveryDigest)) throw new TypeError("delivery body required");
  if (!privateKey) throw new TypeError("delivery signing key required");
  const signature = crypto.sign(null, Buffer.from(stable(delivery)), privateKey).toString("base64");
  return Object.freeze({ schema: SIGNED_SCHEMA, body: delivery, keyId: String(keyId), signature, signedReceiptDigest: sha256({ schema: SIGNED_SCHEMA, body: delivery, keyId: String(keyId), signature }) });
}

function verifyDelivery(signed, publicKey) {
  if (!signed || signed.schema !== SIGNED_SCHEMA || !signed.body || signed.body.schema !== DELIVERY_SCHEMA) return Object.freeze({ ok: false, code: "DELIVERY_SCHEMA_INVALID" });
  const bare = { ...signed.body }; delete bare.deliveryDigest;
  if (sha256(bare) !== signed.body.deliveryDigest) return Object.freeze({ ok: false, code: "DELIVERY_DIGEST_MISMATCH" });
  const ok = crypto.verify(null, Buffer.from(stable(signed.body)), publicKey, Buffer.from(signed.signature, "base64"));
  if (!ok) return Object.freeze({ ok: false, code: "DELIVERY_SIGNATURE_INVALID" });
  return Object.freeze({ ok: true, code: "DELIVERY_VERIFIED", deliveryDigest: signed.body.deliveryDigest, signedReceiptDigest: signed.signedReceiptDigest });
}

function executeContinuationTransaction({ candidates, request, policy = {}, obtainSignedVerifierVerdict, signedVerifierVerdict, trustedVerifierPublicKey, executeWorker, deliveryPrivateKey, deliveryKeyId = "holotrade-delivery" }) {
  if (typeof executeWorker !== "function") throw new TypeError("executeWorker callback required");
  if (typeof obtainSignedVerifierVerdict !== "function" && !signedVerifierVerdict) throw new TypeError("obtainSignedVerifierVerdict callback or signedVerifierVerdict required");
  const selected = S.chooseContinuationWorker(candidates, request, policy);
  if (!selected.ok) throw new Error(selected.code);
  const dispatch = selected.dispatch;
  const normalizedRequest = selected.ranked.request;
  const verdict = typeof obtainSignedVerifierVerdict === "function" ? obtainSignedVerifierVerdict(Object.freeze({ challenge: dispatch.challenge, dispatch, request: normalizedRequest })) : signedVerifierVerdict;
  if (!verdict) throw new TypeError("verifier callback returned no signed verdict");
  const binding = C.verifiedContinuationBinding(normalizedRequest.passport, normalizedRequest.contract, dispatch.challenge, verdict, trustedVerifierPublicKey);
  executionContextAgreement(dispatch, binding);
  const rawExecution = executeWorker(Object.freeze({ dispatch, binding, request: normalizedRequest }));
  const execution = normalizeExecution(rawExecution, normalizedRequest);
  acceleratorExecutionAgreement(normalizedRequest, execution);
  const delivery = deliveryBody(dispatch, binding, execution);
  const signedDelivery = signDelivery(delivery, deliveryPrivateKey, deliveryKeyId);
  return Object.freeze({
    ok: true,
    code: "CONTINUATION_TRANSACTION_COMMITTED",
    dispatch,
    attestation: binding,
    execution,
    delivery: signedDelivery,
    transactionDigest: sha256({ dispatchDigest: dispatch.dispatchDigest, bindingDigest: binding.bindingDigest, executionDigest: execution.executionDigest, signedReceiptDigest: signedDelivery.signedReceiptDigest }),
  });
}

module.exports = { EXECUTION_SCHEMA, DELIVERY_SCHEMA, SIGNED_SCHEMA, sha256, normalizeExecution, executionContextAgreement, acceleratorExecutionAgreement, deliveryBody, signDelivery, verifyDelivery, executeContinuationTransaction };
