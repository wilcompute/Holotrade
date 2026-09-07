"use strict";

// Continuation-native distributed scheduler for HoloVM work.
//
// A mutable worker/VM instance is not the scheduling identity. The scheduled
// object is the exact immutable continuation tuple
//   (continuationRoot, processId, generation)
// and a worker is merely one attested replay engine chosen to advance it.
//
// The scheduler is deliberately strict about four independent dimensions:
//   1. exact continuation identity;
//   2. exact retained-union delta supplied by the archive/accounting layer;
//   3. minimum evidence tier;
//   4. attested physical binding of the required W33 topology points.
//
// Migration between workers preserves the process tuple and creates a new
// continuation-bound measured-boot challenge. It is not cross-carrier state
// conversion and it does not infer topology attestation from graph theory.

const crypto = require("node:crypto");
const C = require("../js/w33-continuation-attestation.js");

const SCHEMA = "holotrade.w33-continuation-dispatch.v1";
const MIGRATION_SCHEMA = "holotrade.w33-continuation-worker-migration.v1";

const EVIDENCE = Object.freeze({
  NONE: 0,
  SOFTWARE_VERIFIED: 1,
  SIGNED_RUNTIME: 2,
  HARDWARE_ATTESTED: 3,
});

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

function finiteNonnegative(value, name) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`);
  return n;
}

function natural(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`);
  return value;
}

function normalizeRequest(request) {
  if (!request || typeof request !== "object") throw new TypeError("continuation request required");
  for (const name of ["continuationRoot", "processId"]) {
    if (!isDigest(request[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  }
  natural(request.generation, "generation");
  const evidenceFloor = request.evidenceFloor == null ? EVIDENCE.SOFTWARE_VERIFIED : request.evidenceFloor;
  natural(evidenceFloor, "evidenceFloor");
  if (evidenceFloor > EVIDENCE.HARDWARE_ATTESTED) throw new RangeError("unknown evidence floor");
  const requiredPoints = [...(request.requiredPoints || [])];
  for (const point of requiredPoints) {
    if (!Number.isInteger(point) || point < 0 || point >= 40) throw new RangeError("required W33 point outside 0..39");
  }
  if (new Set(requiredPoints).size !== requiredPoints.length) throw new RangeError("required W33 points must be unique");
  if (!request.passport || !request.contract) throw new TypeError("passport and deployment contract required");
  return Object.freeze({ ...request, evidenceFloor, requiredPoints: Object.freeze(requiredPoints) });
}

function pointSubset(required, available) {
  const set = new Set(available);
  return required.every((p) => set.has(p));
}

function exactDelta(candidate, continuationRoot) {
  const table = candidate.retainedUnionDeltaBytes;
  if (!table || typeof table !== "object" || !(continuationRoot in table)) {
    throw new TypeError(`candidate ${candidate.id} lacks exact retained-union delta for continuation`);
  }
  return finiteNonnegative(table[continuationRoot], "retained union delta bytes");
}

function eligibility(candidate, request) {
  if (!candidate || typeof candidate !== "object" || !candidate.id) return Object.freeze({ ok: false, code: "CANDIDATE_INVALID" });
  if (!isDigest(candidate.runtimePublicKeyDigest)) return Object.freeze({ ok: false, code: "RUNTIME_KEY_DIGEST_MISSING" });
  const evidenceLevel = Number(candidate.evidenceLevel ?? EVIDENCE.NONE);
  if (!Number.isInteger(evidenceLevel) || evidenceLevel < request.evidenceFloor) {
    return Object.freeze({ ok: false, code: "EVIDENCE_FLOOR_UNMET" });
  }
  const topology = candidate.topology;
  if (!topology || topology.attested !== true || !isDigest(topology.attestationDigest) || !Array.isArray(topology.points)) {
    return Object.freeze({ ok: false, code: "TOPOLOGY_ATTESTATION_REQUIRED" });
  }
  if (!pointSubset(request.requiredPoints, topology.points)) {
    return Object.freeze({ ok: false, code: "REQUIRED_W33_POINTS_UNAVAILABLE" });
  }
  try { exactDelta(candidate, request.continuationRoot); }
  catch (_) { return Object.freeze({ ok: false, code: "EXACT_RETAINED_DELTA_REQUIRED" }); }
  return Object.freeze({ ok: true, code: "ELIGIBLE" });
}

function priceCandidate(candidate, request, policy = {}) {
  const deltaBytes = exactDelta(candidate, request.continuationRoot);
  const durationSeconds = finiteNonnegative(request.durationSeconds ?? 0, "durationSeconds");
  const computePerSecondUSD = finiteNonnegative(candidate.computePerSecondUSD ?? 0, "computePerSecondUSD");
  const retainedByteSecondUSD = finiteNonnegative(policy.retainedByteSecondUSD ?? 0, "retainedByteSecondUSD");
  const transferByteUSD = finiteNonnegative(policy.transferByteUSD ?? 0, "transferByteUSD");
  const startupUSD = finiteNonnegative(candidate.startupUSD ?? 0, "startupUSD");
  const computeUSD = durationSeconds * computePerSecondUSD;
  const retainedUSD = deltaBytes * durationSeconds * retainedByteSecondUSD;
  const transferUSD = deltaBytes * transferByteUSD;
  return Object.freeze({
    deltaBytes,
    computeUSD,
    retainedUSD,
    transferUSD,
    startupUSD,
    totalUSD: computeUSD + retainedUSD + transferUSD + startupUSD,
  });
}

function dispatchFor(candidate, request, policy = {}) {
  const gate = eligibility(candidate, request);
  if (!gate.ok) throw new Error(`candidate ${candidate && candidate.id}: ${gate.code}`);
  const price = priceCandidate(candidate, request, policy);
  const challenge = C.buildContinuationChallenge({
    passport: request.passport,
    contract: request.contract,
    runtimePublicKeyDigest: candidate.runtimePublicKeyDigest,
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
  });
  const body = {
    schema: SCHEMA,
    workerId: String(candidate.id),
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
    evidenceFloor: request.evidenceFloor,
    workerEvidenceLevel: candidate.evidenceLevel,
    topologyAttestationDigest: candidate.topology.attestationDigest,
    requiredPoints: request.requiredPoints,
    retainedUnionDeltaBytes: price.deltaBytes,
    price,
    runtimePublicKeyDigest: candidate.runtimePublicKeyDigest,
    attestationChallengeDigest: challenge.challengeDigest,
    baseMeasuredBootChallengeDigest: challenge.baseChallengeDigest,
  };
  return Object.freeze({ ...body, dispatchDigest: sha256(body), challenge });
}

function rankContinuations(candidates, rawRequest, policy = {}) {
  const request = normalizeRequest(rawRequest);
  const rejected = [];
  const eligible = [];
  for (const candidate of candidates || []) {
    const gate = eligibility(candidate, request);
    if (!gate.ok) {
      rejected.push(Object.freeze({ workerId: candidate && candidate.id, code: gate.code }));
      continue;
    }
    eligible.push(dispatchFor(candidate, request, policy));
  }
  eligible.sort((a, b) => a.price.totalUSD - b.price.totalUSD || a.retainedUnionDeltaBytes - b.retainedUnionDeltaBytes || a.workerId.localeCompare(b.workerId));
  return Object.freeze({ request, eligible: Object.freeze(eligible), rejected: Object.freeze(rejected) });
}

function chooseContinuationWorker(candidates, request, policy = {}) {
  const ranked = rankContinuations(candidates, request, policy);
  if (!ranked.eligible.length) return Object.freeze({ ok: false, code: "NO_ELIGIBLE_CONTINUATION_WORKER", ranked });
  return Object.freeze({ ok: true, code: "CONTINUATION_WORKER_SELECTED", dispatch: ranked.eligible[0], ranked });
}

function migrateWorker(existingDispatch, targetCandidate, rawRequest, policy = {}) {
  if (!existingDispatch || existingDispatch.schema !== SCHEMA) throw new TypeError("valid continuation dispatch required");
  const request = normalizeRequest(rawRequest);
  if (
    existingDispatch.continuationRoot !== request.continuationRoot ||
    existingDispatch.processId !== request.processId ||
    existingDispatch.generation !== request.generation
  ) {
    throw new Error("worker migration may not mutate process continuation identity");
  }
  const next = dispatchFor(targetCandidate, request, policy);
  const body = {
    schema: MIGRATION_SCHEMA,
    fromWorkerId: existingDispatch.workerId,
    toWorkerId: next.workerId,
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
    oldChallengeDigest: existingDispatch.attestationChallengeDigest,
    newChallengeDigest: next.attestationChallengeDigest,
    oldRuntimePublicKeyDigest: existingDispatch.runtimePublicKeyDigest,
    newRuntimePublicKeyDigest: next.runtimePublicKeyDigest,
    processIdentityPreserved: true,
    workerIdentityChanged: existingDispatch.workerId !== next.workerId,
    attestationMustBeRenewed:
      existingDispatch.attestationChallengeDigest !== next.attestationChallengeDigest,
  };
  return Object.freeze({ ...body, migrationDigest: sha256(body), dispatch: next });
}

module.exports = {
  SCHEMA,
  MIGRATION_SCHEMA,
  EVIDENCE,
  sha256,
  normalizeRequest,
  eligibility,
  priceCandidate,
  dispatchFor,
  rankContinuations,
  chooseContinuationWorker,
  migrateWorker,
};
