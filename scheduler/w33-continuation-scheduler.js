"use strict";

// Continuation-native distributed scheduler for HoloVM work.
//
// Scheduling identity is the immutable continuation tuple, optionally refined
// by an independently content-addressed W33 execution policy and its stricter
// baseline-aware joint-admission binding. A replay worker is eligible only when
// evidence, topology, exact retained-union accounting and (when requested) W33
// line-resilience checks all pass. The selected execution context is included
// in the measured-boot challenge, not appended after hardware verification.
//
// Resilience has two deterministic layers: all-lines-hit remains a hard veto;
// otherwise exactAdditionalFailuresToBlockAllLines is the minimum number of
// extra W33 point failures needed to reach that veto. It is an exact
// combinatorial distance, not a probability estimate.

const crypto = require("node:crypto");
const C = require("../js/w33-continuation-attestation.js");
const J = require("../js/w33-joint-admission-policy.js");
const H = require("../js/w33-strict-admission-binding.js");
const R = require("./w33-topology-resilience.js");
const D = require("./w33-failure-distance.js");

const SCHEMA = "holotrade.w33-continuation-dispatch.v1";
const MIGRATION_SCHEMA = "holotrade.w33-continuation-worker-migration.v1";
const EVIDENCE = Object.freeze({ NONE: 0, SOFTWARE_VERIFIED: 1, SIGNED_RUNTIME: 2, HARDWARE_ATTESTED: 3 });

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function finiteNonnegative(value, name) { const n = Number(value); if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`); return n; }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }

function normalizeRequest(request) {
  if (!request || typeof request !== "object") throw new TypeError("continuation request required");
  for (const name of ["continuationRoot", "processId"]) if (!isDigest(request[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  natural(request.generation, "generation");
  const evidenceFloor = request.evidenceFloor == null ? EVIDENCE.SOFTWARE_VERIFIED : request.evidenceFloor;
  natural(evidenceFloor, "evidenceFloor");
  if (evidenceFloor > EVIDENCE.HARDWARE_ATTESTED) throw new RangeError("unknown evidence floor");
  const requiredPoints = [...(request.requiredPoints || [])];
  for (const point of requiredPoints) if (!Number.isInteger(point) || point < 0 || point >= 40) throw new RangeError("required W33 point outside 0..39");
  if (new Set(requiredPoints).size !== requiredPoints.length) throw new RangeError("required W33 points must be unique");
  if (!request.passport || !request.contract) throw new TypeError("passport and deployment contract required");

  const requireLineResilience = request.requireLineResilience === true;
  if (!requireLineResilience && request.minimumAdditionalFailuresToBlockAllLines != null) {
    throw new TypeError("minimumAdditionalFailuresToBlockAllLines requires requireLineResilience=true");
  }
  const minimumAdditionalFailuresToBlockAllLines = requireLineResilience
    ? natural(request.minimumAdditionalFailuresToBlockAllLines == null ? 1 : request.minimumAdditionalFailuresToBlockAllLines, "minimumAdditionalFailuresToBlockAllLines")
    : 0;

  let executionPolicy = null;
  let executionPolicyDigest = null;
  if (request.executionPolicy != null) {
    executionPolicy = J.verifyPolicy(request.executionPolicy, request);
    executionPolicyDigest = executionPolicy.executionPolicyDigest;
    if (request.executionPolicyDigest != null && request.executionPolicyDigest !== executionPolicyDigest) throw new Error("request executionPolicyDigest disagrees with verified W33 policy");
  } else if (request.executionPolicyDigest != null) {
    throw new TypeError("executionPolicyDigest requires the full verifiable W33 executionPolicy certificate");
  }

  let strictAdmissionBinding = null;
  let strictAdmissionBindingDigest = null;
  if (request.strictAdmissionBinding != null) {
    if (!executionPolicy) throw new TypeError("strictAdmissionBinding requires the full W33 executionPolicy certificate");
    strictAdmissionBinding = H.verifyStrictBinding(request.strictAdmissionBinding, executionPolicy, request);
    strictAdmissionBindingDigest = strictAdmissionBinding.strictBindingDigest;
  } else if (request.strictAdmissionBindingDigest != null) {
    throw new TypeError("strictAdmissionBindingDigest requires the full verifiable strictAdmissionBinding certificate");
  }
  if (request.strictAdmissionBindingDigest != null && request.strictAdmissionBindingDigest !== strictAdmissionBindingDigest) throw new Error("request strictAdmissionBindingDigest disagrees with verified W33 strict binding");

  return Object.freeze({
    ...request,
    evidenceFloor,
    requiredPoints: Object.freeze(requiredPoints),
    executionPolicy,
    executionPolicyDigest,
    strictAdmissionBinding,
    strictAdmissionBindingDigest,
    requireLineResilience,
    minimumAdditionalFailuresToBlockAllLines,
  });
}

function pointSubset(required, available) { const set = new Set(available); return required.every((p) => set.has(p)); }

function exactDelta(candidate, request) {
  let delta;
  if (request.executionPolicyDigest) {
    const table = candidate.retainedUnionDeltaBytesByPolicy;
    if (!table || typeof table !== "object" || !(request.executionPolicyDigest in table)) throw new TypeError(`candidate ${candidate.id} lacks exact retained-union delta for execution policy`);
    delta = finiteNonnegative(table[request.executionPolicyDigest], "policy-specific retained union delta bytes");
  } else {
    const table = candidate.retainedUnionDeltaBytes;
    if (!table || typeof table !== "object" || !(request.continuationRoot in table)) throw new TypeError(`candidate ${candidate.id} lacks exact retained-union delta for continuation`);
    delta = finiteNonnegative(table[request.continuationRoot], "retained union delta bytes");
  }
  if (request.strictAdmissionBinding && delta !== request.strictAdmissionBinding.retainedUnionDeltaBytes) {
    throw new Error("worker retained-union delta disagrees with strict W33 admission binding");
  }
  return delta;
}

function resilienceAssessment(candidate, request) {
  if (!request.requireLineResilience) return null;
  const topology = candidate && candidate.topology;
  if (!topology || !Array.isArray(topology.failurePoints)) throw new TypeError("attested topology failurePoints required for W33 line resilience");
  const base = R.assessFailures(topology.failurePoints);
  const distance = D.exactFailureDistance(topology.failurePoints);
  return Object.freeze({
    ...base,
    additionalFailuresToBlockAllLines: distance.distance,
    failureDistanceWitness: distance.witnessAdditionalFailures,
    failureDistanceExact: distance.exact,
    failureDistanceSearchLowerBound: distance.searchLowerBound ?? 0,
    failureDistanceGreedyUpperBound: distance.greedyUpperBound ?? 0,
  });
}

function eligibility(candidate, request) {
  if (!candidate || typeof candidate !== "object" || !candidate.id) return Object.freeze({ ok: false, code: "CANDIDATE_INVALID" });
  if (!isDigest(candidate.runtimePublicKeyDigest)) return Object.freeze({ ok: false, code: "RUNTIME_KEY_DIGEST_MISSING" });
  const evidenceLevel = Number(candidate.evidenceLevel ?? EVIDENCE.NONE);
  if (!Number.isInteger(evidenceLevel) || evidenceLevel < request.evidenceFloor) return Object.freeze({ ok: false, code: "EVIDENCE_FLOOR_UNMET" });
  const topology = candidate.topology;
  if (!topology || topology.attested !== true || !isDigest(topology.attestationDigest) || !Array.isArray(topology.points)) return Object.freeze({ ok: false, code: "TOPOLOGY_ATTESTATION_REQUIRED" });
  if (!pointSubset(request.requiredPoints, topology.points)) return Object.freeze({ ok: false, code: "REQUIRED_W33_POINTS_UNAVAILABLE" });
  let resilience = null;
  try { resilience = resilienceAssessment(candidate, request); }
  catch (_) { return Object.freeze({ ok: false, code: "FAILURE_SET_ATTESTATION_REQUIRED" }); }
  if (resilience && resilience.allLinesHit) return Object.freeze({ ok: false, code: "W33_CORRELATED_FAILURE_BLOCKS_ALL_LINES", resilience });
  if (resilience && resilience.additionalFailuresToBlockAllLines < request.minimumAdditionalFailuresToBlockAllLines) {
    return Object.freeze({ ok: false, code: "W33_FAILURE_DISTANCE_FLOOR_UNMET", resilience });
  }
  try { exactDelta(candidate, request); }
  catch (_) {
    const code = request.strictAdmissionBinding ? "EXACT_STRICT_RETAINED_DELTA_REQUIRED" : request.executionPolicyDigest ? "EXACT_POLICY_RETAINED_DELTA_REQUIRED" : "EXACT_RETAINED_DELTA_REQUIRED";
    return Object.freeze({ ok: false, code });
  }
  return Object.freeze({ ok: true, code: "ELIGIBLE", resilience });
}

function priceCandidate(candidate, request, policy = {}) {
  const deltaBytes = exactDelta(candidate, request);
  const durationSeconds = finiteNonnegative(request.durationSeconds ?? 0, "durationSeconds");
  const computePerSecondUSD = finiteNonnegative(candidate.computePerSecondUSD ?? 0, "computePerSecondUSD");
  const retainedByteSecondUSD = finiteNonnegative(policy.retainedByteSecondUSD ?? 0, "retainedByteSecondUSD");
  const transferByteUSD = finiteNonnegative(policy.transferByteUSD ?? 0, "transferByteUSD");
  const startupUSD = finiteNonnegative(candidate.startupUSD ?? 0, "startupUSD");
  const computeUSD = durationSeconds * computePerSecondUSD;
  const retainedUSD = deltaBytes * durationSeconds * retainedByteSecondUSD;
  const transferUSD = deltaBytes * transferByteUSD;
  return Object.freeze({ deltaBytes, computeUSD, retainedUSD, transferUSD, startupUSD, totalUSD: computeUSD + retainedUSD + transferUSD + startupUSD });
}

function dispatchFor(candidate, request, policy = {}) {
  const gate = eligibility(candidate, request);
  if (!gate.ok) throw new Error(`candidate ${candidate && candidate.id}: ${gate.code}`);
  const price = priceCandidate(candidate, request, policy);
  const resilience = gate.resilience;
  const failureAssessmentDigest = resilience == null ? null : sha256(resilience);
  const strictBinding = request.strictAdmissionBinding;
  const challenge = C.buildContinuationChallenge({
    passport: request.passport,
    contract: request.contract,
    runtimePublicKeyDigest: candidate.runtimePublicKeyDigest,
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
    executionPolicyDigest: request.executionPolicyDigest,
    strictAdmissionBindingDigest: request.strictAdmissionBindingDigest,
    topologyAttestationDigest: candidate.topology.attestationDigest,
    failureAssessmentDigest,
  });
  const body = {
    schema: SCHEMA,
    workerId: String(candidate.id),
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
    ...(request.executionPolicyDigest == null ? {} : { executionPolicyDigest: request.executionPolicyDigest, executionPolicyProblemRoot: request.executionPolicy.problemRoot }),
    ...(strictBinding == null ? {} : {
      strictAdmissionBindingDigest: strictBinding.strictBindingDigest,
      handoffDigest: strictBinding.handoffDigest,
      jointPlanDigest: strictBinding.jointPlanDigest,
      strategyDigest: strictBinding.strategyDigest,
      strictPlacementDigest: strictBinding.placementDigest,
      strictSnapshotProblemRoot: strictBinding.snapshotProblemRoot,
      baselineRetainedUnionBytes: strictBinding.baselineRetainedUnionBytes,
      postAdmissionRetainedUnionBytes: strictBinding.postAdmissionRetainedUnionBytes,
    }),
    evidenceFloor: request.evidenceFloor,
    workerEvidenceLevel: candidate.evidenceLevel,
    topologyAttestationDigest: candidate.topology.attestationDigest,
    requiredPoints: request.requiredPoints,
    ...(resilience == null ? {} : {
      failureAssessmentDigest,
      intactW33LineCount: resilience.intactLineCount,
      additionalFailuresToBlockAllLines: resilience.additionalFailuresToBlockAllLines,
      failureDistanceExact: true,
    }),
    retainedUnionDeltaBytes: price.deltaBytes,
    price,
    runtimePublicKeyDigest: candidate.runtimePublicKeyDigest,
    attestationChallengeDigest: challenge.challengeDigest,
    baseMeasuredBootChallengeDigest: challenge.baseChallengeDigest,
  };
  return Object.freeze({ ...body, dispatchDigest: sha256(body), challenge, resilience });
}

function rankContinuations(candidates, rawRequest, policy = {}) {
  const request = normalizeRequest(rawRequest); const rejected = [], eligible = [];
  for (const candidate of candidates || []) {
    const gate = eligibility(candidate, request);
    if (!gate.ok) { rejected.push(Object.freeze({ workerId: candidate && candidate.id, code: gate.code, ...(gate.resilience ? { resilience: gate.resilience } : {}) })); continue; }
    eligible.push(dispatchFor(candidate, request, policy));
  }
  eligible.sort((a, b) =>
    a.price.totalUSD - b.price.totalUSD ||
    (b.additionalFailuresToBlockAllLines ?? 0) - (a.additionalFailuresToBlockAllLines ?? 0) ||
    a.retainedUnionDeltaBytes - b.retainedUnionDeltaBytes ||
    a.workerId.localeCompare(b.workerId)
  );
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
  if (existingDispatch.continuationRoot !== request.continuationRoot || existingDispatch.processId !== request.processId || existingDispatch.generation !== request.generation) throw new Error("worker migration may not mutate process continuation identity");
  if ((existingDispatch.executionPolicyDigest || null) !== (request.executionPolicyDigest || null)) throw new Error("worker migration may not mutate execution policy identity");
  if ((existingDispatch.strictAdmissionBindingDigest || null) !== (request.strictAdmissionBindingDigest || null)) throw new Error("worker migration may not mutate strict W33 admission binding identity");
  const next = dispatchFor(targetCandidate, request, policy);
  const body = {
    schema: MIGRATION_SCHEMA,
    fromWorkerId: existingDispatch.workerId,
    toWorkerId: next.workerId,
    continuationRoot: request.continuationRoot,
    processId: request.processId,
    generation: request.generation,
    ...(request.executionPolicyDigest == null ? {} : { executionPolicyDigest: request.executionPolicyDigest }),
    ...(request.strictAdmissionBindingDigest == null ? {} : { strictAdmissionBindingDigest: request.strictAdmissionBindingDigest, jointPlanDigest: request.strictAdmissionBinding.jointPlanDigest, strategyDigest: request.strictAdmissionBinding.strategyDigest, strictPlacementDigest: request.strictAdmissionBinding.placementDigest }),
    oldChallengeDigest: existingDispatch.attestationChallengeDigest,
    newChallengeDigest: next.attestationChallengeDigest,
    oldRuntimePublicKeyDigest: existingDispatch.runtimePublicKeyDigest,
    newRuntimePublicKeyDigest: next.runtimePublicKeyDigest,
    oldTopologyAttestationDigest: existingDispatch.topologyAttestationDigest,
    newTopologyAttestationDigest: next.topologyAttestationDigest,
    oldFailureAssessmentDigest: existingDispatch.failureAssessmentDigest || null,
    newFailureAssessmentDigest: next.failureAssessmentDigest || null,
    oldAdditionalFailuresToBlockAllLines: existingDispatch.additionalFailuresToBlockAllLines ?? null,
    newAdditionalFailuresToBlockAllLines: next.additionalFailuresToBlockAllLines ?? null,
    processIdentityPreserved: true,
    workerIdentityChanged: existingDispatch.workerId !== next.workerId,
    attestationMustBeRenewed: existingDispatch.attestationChallengeDigest !== next.attestationChallengeDigest,
  };
  return Object.freeze({ ...body, migrationDigest: sha256(body), dispatch: next });
}

module.exports = { SCHEMA, MIGRATION_SCHEMA, EVIDENCE, sha256, normalizeRequest, exactDelta, resilienceAssessment, eligibility, priceCandidate, dispatchFor, rankContinuations, chooseContinuationWorker, migrateWorker };
