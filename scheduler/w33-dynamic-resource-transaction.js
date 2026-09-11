"use strict";

// Dynamic-resource wrapper around the existing authenticated continuation
// transaction. Workers do not supply unauthenticated unit prices on this path:
// their seven-coordinate price vector is taken only from verified Ed25519
// telemetry bound to worker identity, runtime key, calibration/pricing epochs,
// and the continuation generation. Representation market identity and optional
// market-history root remain price-independent across those telemetry updates.

const crypto = require("node:crypto");
const S = require("./w33-continuation-scheduler.js");
const Q = require("./w33-continuation-transaction.js");
const T = require("../js/w33-signed-resource-telemetry.js");

const SCHEMA = "holotrade.w33-dynamic-resource-delivery.v1";
const SIGNED_SCHEMA = "holotrade.w33-signed-dynamic-resource-delivery.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }

function verifiedTelemetryCandidates(candidates, request, { trustedPricingPublicKeys, minimumCalibrationEpoch = 0, minimumPricingEpoch = 0 } = {}) {
  const normalizedRequest = S.normalizeRequest(request);
  if (!normalizedRequest.signedResource) return Object.freeze({ request: normalizedRequest, candidates: Object.freeze([...(candidates || [])]), telemetryByWorker: Object.freeze({}) });
  if (!trustedPricingPublicKeys || typeof trustedPricingPublicKeys !== "object") throw new TypeError("trustedPricingPublicKeys required for dynamic signed-resource scheduling");
  const out=[], telemetryByWorker={};
  for (const c of candidates || []) {
    if (!c || !c.id) throw new TypeError("candidate id required");
    const signed=c.signedResourcePricingTelemetry;
    if (!signed || !signed.keyId) throw new TypeError(`candidate ${c.id} lacks signed resource pricing telemetry`);
    const key=trustedPricingPublicKeys[signed.keyId];
    if (!key) throw new Error(`candidate ${c.id} uses untrusted resource pricing key ${signed.keyId}`);
    const t=T.verifyPricingTelemetry(signed,key,{ workerId:c.id, runtimePublicKeyDigest:c.runtimePublicKeyDigest,
      generation:normalizedRequest.generation, minimumCalibrationEpoch, minimumPricingEpoch });
    if (telemetryByWorker[String(c.id)]) throw new Error("duplicate candidate worker id in pricing telemetry set");
    telemetryByWorker[String(c.id)]=t;
    out.push(Object.freeze({ ...c, signedResourceUnitPrices:t.unitPrices }));
  }
  return Object.freeze({ request:normalizedRequest, candidates:Object.freeze(out), telemetryByWorker:Object.freeze(telemetryByWorker) });
}

function signDynamicBody(body, privateKey, keyId) {
  const signature=crypto.sign(null,Buffer.from(stable(body)),privateKey).toString("base64");
  const signed={schema:SIGNED_SCHEMA,body,keyId:String(keyId),signature};
  return Object.freeze({ ...signed, signedDynamicDeliveryDigest:sha256(signed) });
}

function executeDynamicResourceTransaction({ candidates, request, policy = {}, trustedPricingPublicKeys, minimumCalibrationEpoch = 0, minimumPricingEpoch = 0,
  obtainSignedVerifierVerdict, signedVerifierVerdict, trustedVerifierPublicKey, executeWorker, deliveryPrivateKey, deliveryKeyId = "holotrade-delivery" }) {
  const verified=verifiedTelemetryCandidates(candidates,request,{trustedPricingPublicKeys,minimumCalibrationEpoch,minimumPricingEpoch});
  const tx=Q.executeContinuationTransaction({ candidates:verified.candidates, request, policy, obtainSignedVerifierVerdict, signedVerifierVerdict,
    trustedVerifierPublicKey, executeWorker, deliveryPrivateKey, deliveryKeyId });
  const telemetry=verified.telemetryByWorker[tx.dispatch.workerId];
  if (verified.request.signedResource && !telemetry) throw new Error("selected worker lost verified pricing telemetry");
  if (!telemetry) return Object.freeze({ ...tx, dynamicResource:null });
  if (tx.dispatch.signedResourceSelectionDigest !== verified.request.signedResourceSelectionDigest) throw new Error("dynamic pricing mutated signed-resource selection identity");
  if (tx.dispatch.representationMarketIdentityDigest !== verified.request.representationMarketIdentityDigest) throw new Error("dynamic pricing mutated representation market identity");
  if ((tx.dispatch.representationMarketHistoryRootDigest||null) !== (verified.request.representationMarketHistoryRootDigest||null)) throw new Error("dynamic pricing mutated representation market history root");
  if (tx.delivery.body.signedResourcePriceDigest !== tx.dispatch.signedResourcePriceDigest) throw new Error("delivery lost selected resource price identity");
  if (tx.delivery.body.representationMarketIdentityDigest !== tx.dispatch.representationMarketIdentityDigest) throw new Error("delivery lost representation market identity");
  if ((tx.delivery.body.representationMarketHistoryRootDigest||null) !== (tx.dispatch.representationMarketHistoryRootDigest||null)) throw new Error("delivery lost representation market history root");
  const body=Object.freeze({
    schema:SCHEMA,
    baseTransactionDigest:tx.transactionDigest,
    baseDeliveryDigest:tx.delivery.body.deliveryDigest,
    baseSignedReceiptDigest:tx.delivery.signedReceiptDigest,
    workerId:tx.dispatch.workerId,
    continuationRoot:tx.dispatch.continuationRoot,
    processId:tx.dispatch.processId,
    generation:tx.dispatch.generation,
    signedResourceSelectionDigest:tx.dispatch.signedResourceSelectionDigest,
    representationMarketIdentityDigest:tx.dispatch.representationMarketIdentityDigest,
    ...(tx.dispatch.representationMarketHistoryRootDigest == null ? {} : { representationMarketHistoryRootDigest:tx.dispatch.representationMarketHistoryRootDigest,
      representationMarketHistoryEventCount:tx.dispatch.representationMarketHistoryEventCount,representationMarketHistoryDigest:tx.dispatch.representationMarketHistoryDigest }),
    representationClass:tx.dispatch.representationClass,
    signedResourcePriceDigest:tx.dispatch.signedResourcePriceDigest,
    pricingTelemetryDigest:telemetry.telemetryDigest,
    signedPricingTelemetryDigest:telemetry.signedTelemetryDigest,
    pricingKeyId:telemetry.keyId,
    calibrationEpoch:telemetry.calibrationEpoch,
    pricingEpoch:telemetry.pricingEpoch,
    pricingMeasurementDigest:telemetry.measurementDigest,
  });
  const dynamic=signDynamicBody(Object.freeze({ ...body, dynamicDeliveryDigest:sha256(body) }),deliveryPrivateKey,deliveryKeyId);
  return Object.freeze({ ...tx, dynamicResource:Object.freeze({ telemetry, delivery:dynamic }) });
}

function verifyDynamicResourceDelivery(result, deliveryPublicKey) {
  if (!result || !result.delivery || !result.dynamicResource || !result.dynamicResource.delivery) return Object.freeze({ok:false,code:"DYNAMIC_DELIVERY_MISSING"});
  const base=Q.verifyDelivery(result.delivery,deliveryPublicKey); if (!base.ok) return base;
  const signed=result.dynamicResource.delivery;
  if (signed.schema!==SIGNED_SCHEMA || !signed.body || signed.body.schema!==SCHEMA) return Object.freeze({ok:false,code:"DYNAMIC_DELIVERY_SCHEMA_INVALID"});
  const d={...signed.body}; delete d.dynamicDeliveryDigest;
  if (sha256(d)!==signed.body.dynamicDeliveryDigest) return Object.freeze({ok:false,code:"DYNAMIC_DELIVERY_DIGEST_MISMATCH"});
  const signedBare={schema:SIGNED_SCHEMA,body:signed.body,keyId:signed.keyId,signature:signed.signature};
  if (sha256(signedBare)!==signed.signedDynamicDeliveryDigest) return Object.freeze({ok:false,code:"DYNAMIC_SIGNED_IDENTITY_MISMATCH"});
  if (!crypto.verify(null,Buffer.from(stable(signed.body)),deliveryPublicKey,Buffer.from(signed.signature,"base64"))) return Object.freeze({ok:false,code:"DYNAMIC_DELIVERY_SIGNATURE_INVALID"});
  if (signed.body.baseDeliveryDigest!==result.delivery.body.deliveryDigest || signed.body.baseSignedReceiptDigest!==result.delivery.signedReceiptDigest) return Object.freeze({ok:false,code:"DYNAMIC_BASE_DELIVERY_DRIFT"});
  if (signed.body.continuationRoot!==result.delivery.body.parentContinuationRoot || signed.body.processId!==result.delivery.body.processId || signed.body.generation!==result.delivery.body.generationBefore) return Object.freeze({ok:false,code:"DYNAMIC_CONTINUATION_DRIFT"});
  if (signed.body.signedResourceSelectionDigest!==result.dispatch.signedResourceSelectionDigest || signed.body.signedResourcePriceDigest!==result.dispatch.signedResourcePriceDigest ||
      signed.body.representationMarketIdentityDigest!==result.dispatch.representationMarketIdentityDigest || result.delivery.body.representationMarketIdentityDigest!==result.dispatch.representationMarketIdentityDigest ||
      (signed.body.representationMarketHistoryRootDigest||null)!==(result.dispatch.representationMarketHistoryRootDigest||null) ||
      (result.delivery.body.representationMarketHistoryRootDigest||null)!==(result.dispatch.representationMarketHistoryRootDigest||null)) return Object.freeze({ok:false,code:"DYNAMIC_RESOURCE_IDENTITY_DRIFT"});
  return Object.freeze({ok:true,code:"DYNAMIC_RESOURCE_DELIVERY_VERIFIED",dynamicDeliveryDigest:signed.body.dynamicDeliveryDigest,signedDynamicDeliveryDigest:signed.signedDynamicDeliveryDigest,
    representationMarketIdentityDigest:signed.body.representationMarketIdentityDigest,representationMarketHistoryRootDigest:signed.body.representationMarketHistoryRootDigest||null});
}

module.exports={SCHEMA,SIGNED_SCHEMA,sha256,verifiedTelemetryCandidates,executeDynamicResourceTransaction,verifyDynamicResourceDelivery};
