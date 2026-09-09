"use strict";

// Typed cross-repo pricing for W33 signed-representation resource certificates.
// A/A^2 remain estimator/representation coordinates, never energy surrogates.

const crypto = require("node:crypto");

const CERT_SCHEMA = "w33.holovm-signed-representation-economics.v1";
const RESOURCE_SCHEMA = "holotrade.w33-signed-resource-selection.v1";
const PRICE_SCHEMA = "holotrade.w33-signed-resource-price.v1";

const CLASSES = Object.freeze({
  "positive-depth0": Object.freeze({ depth: 0, A: "1", A2: "1", excessA: 0, excessA2: 0 }),
  "exception-depth1": Object.freeze({ depth: 1, A: "3/2", A2: "9/4", excessA: 0.5, excessA2: 1.25 }),
  "exception-depth2": Object.freeze({ depth: 2, A: "2", A2: "4", excessA: 1, excessA2: 3 }),
});

const PRICE_FIELDS = Object.freeze([
  "semanticGuestStepUSD",
  "w33RouteHopUSD",
  "authenticatedRetainedByteTickUSD",
  "authenticatedSweptPayloadByteUSD",
  "deterministicReplayStepUSD",
  "representationExcessUSD",
  "samplingExcessUSD",
]);

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }
function finiteNonnegative(value, name) { const n=Number(value); if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`); return n; }

function sameWork(a,b) {
  const fields=["semantic_guest_steps","w33_route_hops","authenticated_retained_byte_ticks","authenticated_swept_payload_bytes","deterministic_replay_steps"];
  return fields.every((f)=>a[f]===b[f]);
}

function verifySignedResourceCertificate(cert, representationClass) {
  if (!cert || cert.schema !== CERT_SCHEMA || cert.status !== "PASS") throw new TypeError("PASS W33 signed-representation economics certificate required");
  if (!cert.checks || !Object.values(cert.checks).every((v)=>v===true)) throw new Error("W33 signed-resource certificate contains a failed check");
  const vectors=cert.resource_vectors;
  if (!vectors || typeof vectors !== "object") throw new TypeError("resource_vectors required");
  for (const name of Object.keys(CLASSES)) if (!vectors[name]) throw new TypeError(`missing W33 resource class ${name}`);
  const base=vectors["positive-depth0"];
  for (const name of Object.keys(CLASSES)) {
    const row=vectors[name], expected=CLASSES[name];
    if (row.representation_class !== name) throw new Error("representation class identity drift");
    if (String(row.representation_amplification) !== expected.A || String(row.signed_sampling_second_moment_factor) !== expected.A2) throw new Error(`exact signed-resource factor drift for ${name}`);
    if (!sameWork(base,row)) throw new Error("representation class changed semantic/authenticated HoloVM work coordinates");
    natural(row.semantic_guest_steps,"semantic_guest_steps"); natural(row.w33_route_hops,"w33_route_hops");
    natural(row.authenticated_retained_byte_ticks,"authenticated_retained_byte_ticks"); natural(row.authenticated_swept_payload_bytes,"authenticated_swept_payload_bytes"); natural(row.deterministic_replay_steps,"deterministic_replay_steps");
  }
  if (!(representationClass in CLASSES)) throw new RangeError("unknown signed representation class");
  const row=vectors[representationClass], expected=CLASSES[representationClass];
  const body={
    schema: RESOURCE_SCHEMA,
    certificateDigest: sha256(cert),
    representationClass,
    depth: expected.depth,
    representationAmplification: expected.A,
    signedSamplingSecondMomentFactor: expected.A2,
    semanticGuestSteps: row.semantic_guest_steps,
    w33RouteHops: row.w33_route_hops,
    authenticatedRetainedByteTicks: row.authenticated_retained_byte_ticks,
    authenticatedSweptPayloadBytes: row.authenticated_swept_payload_bytes,
    deterministicReplaySteps: row.deterministic_replay_steps,
    representationExcessAminus1: expected.excessA,
    samplingExcessA2minus1: expected.excessA2,
  };
  return Object.freeze({ ...body, selectionDigest: sha256(body) });
}

function validateUnitPrices(prices) {
  if (!prices || typeof prices !== "object") throw new TypeError("complete signed-resource unit-price vector required");
  const keys=Object.keys(prices).sort(), expected=[...PRICE_FIELDS].sort();
  if (JSON.stringify(keys)!==JSON.stringify(expected)) throw new TypeError(`signed-resource unit prices must contain exactly ${PRICE_FIELDS.join(",")}`);
  const out={}; for (const k of PRICE_FIELDS) out[k]=finiteNonnegative(prices[k],k);
  return Object.freeze(out);
}

function priceSignedResource(selection, rawPrices) {
  if (!selection || selection.schema !== RESOURCE_SCHEMA) throw new TypeError("verified signed-resource selection required");
  const p=validateUnitPrices(rawPrices);
  const components=Object.freeze({
    semanticGuestStepsUSD: selection.semanticGuestSteps*p.semanticGuestStepUSD,
    w33RouteHopsUSD: selection.w33RouteHops*p.w33RouteHopUSD,
    authenticatedRetainedByteTicksUSD: selection.authenticatedRetainedByteTicks*p.authenticatedRetainedByteTickUSD,
    authenticatedSweptPayloadBytesUSD: selection.authenticatedSweptPayloadBytes*p.authenticatedSweptPayloadByteUSD,
    deterministicReplayStepsUSD: selection.deterministicReplaySteps*p.deterministicReplayStepUSD,
    representationExcessUSD: selection.representationExcessAminus1*p.representationExcessUSD,
    samplingExcessUSD: selection.samplingExcessA2minus1*p.samplingExcessUSD,
  });
  const totalUSD=Object.values(components).reduce((a,b)=>a+b,0);
  const body={schema:PRICE_SCHEMA,selectionDigest:selection.selectionDigest,representationClass:selection.representationClass,unitPrices:p,components,totalUSD};
  return Object.freeze({...body,priceDigest:sha256(body)});
}

module.exports={CERT_SCHEMA,RESOURCE_SCHEMA,PRICE_SCHEMA,CLASSES,PRICE_FIELDS,sha256,verifySignedResourceCertificate,validateUnitPrices,priceSignedResource};
