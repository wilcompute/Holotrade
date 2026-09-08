"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");

const A = require("../js/w33-measured-boot-attestation.js");
const C = require("../js/w33-continuation-attestation.js");
const D = require("../js/w33-passport-deployment.js");
const J = require("../js/w33-joint-admission-policy.js");
const R = require("../scheduler/w33-topology-resilience.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const T = require("../scheduler/w33-continuation-transaction.js");

function d(label) { return S.sha256(label); }

function makePolicy(continuationRoot, processId, generation, suffix = "A") {
  const body = {
    schema: J.SCHEMA,
    problemRoot: d(`problem-${suffix}`),
    continuationRoot,
    processId,
    generation,
    strategyDigest: d(`strategy-${suffix}`),
    checkpointPeakBytes: 3000,
    snapshotPayloadBytes: 1200,
    combinedBytes: 4200,
    capacityBytes: 5000,
    snapshotProblemRoot: d(`snapshot-${suffix}`),
    placementDigest: d(`placement-${suffix}`),
  };
  return Object.freeze({ ...body, executionPolicyDigest: J.sha256(body), status: "PASS" });
}

function fixture() {
  const verifierKeys = crypto.generateKeyPairSync("ed25519");
  const deliveryKeys = crypto.generateKeyPairSync("ed25519");
  const deploymentDigest = d("policy-deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("policy-passport"),
    deploymentDigest,
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 17,
    revocationRoot: d("policy-revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const continuationRoot = d("policy-continuation");
  const processId = d("policy-process");
  const generation = 9;
  const executionPolicy = makePolicy(continuationRoot, processId, generation);
  const request = Object.freeze({
    continuationRoot, processId, generation, passport, contract, executionPolicy,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints: [0, 1],
    requireLineResilience: true,
    durationSeconds: 2,
  });
  return { verifierKeys, deliveryKeys, passport, contract, continuationRoot, processId, generation, executionPolicy, request };
}

function worker(id, f, opts = {}) {
  return Object.freeze({
    id,
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: opts.runtimePublicKeyDigest || d(`runtime-${id}`),
    topology: Object.freeze({
      attested: true,
      attestationDigest: opts.topologyAttestationDigest || d(`topology-${id}`),
      points: [0, 1, 2, 3, 4, 5],
      failurePoints: opts.failurePoints || [],
    }),
    retainedUnionDeltaBytesByPolicy: opts.deltaTable || { [f.executionPolicy.executionPolicyDigest]: opts.delta ?? 1000 },
    computePerSecondUSD: opts.computePerSecondUSD ?? 0.01,
  });
}

function signVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("policy-launch"),
    reportedTcbDigest: d("policy-tcb"),
    signerChainDigest: d("policy-vcek"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "policy-fixture-verifier",
  }, privateKey);
}

test("exact W33 geometry has 40 points, 40 lines and degree 12", () => {
  assert.equal(R.GEOMETRY.points.length, 40);
  assert.equal(R.GEOMETRY.lines.length, 40);
  assert.ok(R.GEOMETRY.adjacency.every((x) => x.size === 12));
});

test("neighbourhood failure is the census equal-pencil 12-point blocker", () => {
  const failures = [...R.GEOMETRY.adjacency[0]];
  const out = R.assessFailures(failures);
  assert.equal(out.failureCount, 12);
  assert.equal(out.allLinesHit, true);
  assert.deepEqual(out.twelvePointBlocker.pair, [0, 0]);
  assert.equal(out.twelvePointBlocker.pairType, "equal");
  assert.equal(out.twelvePointBlocker.expectedSupportsForFixedPair, 10);
});

test("correlated all-lines-hit worker is rejected before a cheaper price can win", () => {
  const f = fixture();
  const blocked = worker("blocked-cheap", f, { failurePoints: [...R.GEOMETRY.adjacency[0]], delta: 1, computePerSecondUSD: 0 });
  const healthy = worker("healthy", f, { failurePoints: [], delta: 900, computePerSecondUSD: 0.02 });
  const ranked = S.rankContinuations([blocked, healthy], f.request);
  assert.equal(ranked.eligible.length, 1);
  assert.equal(ranked.eligible[0].workerId, "healthy");
  assert.equal(ranked.rejected[0].code, "W33_CORRELATED_FAILURE_BLOCKS_ALL_LINES");
  assert.equal(ranked.rejected[0].resilience.twelvePointBlocker.pairType, "equal");
});

test("policy-specific delta is mandatory and stale continuation-only delta cannot price replay", () => {
  const f = fixture();
  const stale = Object.freeze({ ...worker("stale", f), retainedUnionDeltaBytesByPolicy: undefined, retainedUnionDeltaBytes: { [f.continuationRoot]: 1 } });
  const ranked = S.rankContinuations([stale], f.request);
  assert.equal(ranked.eligible.length, 0);
  assert.equal(ranked.rejected[0].code, "EXACT_POLICY_RETAINED_DELTA_REQUIRED");
});

test("changing only checkpoint/snapshot policy changes challenge and requires a new exact quote", () => {
  const f = fixture();
  const p2 = makePolicy(f.continuationRoot, f.processId, f.generation, "B");
  const w = worker("A", f);
  const a = S.chooseContinuationWorker([w], f.request);
  const request2 = { ...f.request, executionPolicy: p2 };
  const b = S.chooseContinuationWorker([w], request2);
  assert.equal(a.ok, true);
  assert.equal(b.ok, false);
  assert.equal(b.ranked.rejected[0].code, "EXACT_POLICY_RETAINED_DELTA_REQUIRED");
  const w2 = Object.freeze({ ...w, retainedUnionDeltaBytesByPolicy: { ...w.retainedUnionDeltaBytesByPolicy, [p2.executionPolicyDigest]: 1000 } });
  const b2 = S.chooseContinuationWorker([w2], request2);
  assert.equal(b2.ok, true);
  assert.notEqual(a.dispatch.challenge.challengeDigest, b2.dispatch.challenge.challengeDigest);
});

test("topology-attestation substitution changes challenge and rejects verdict replay", () => {
  const f = fixture();
  const runtime = d("shared-runtime-topology-replay");
  const aWorker = worker("topo-A", f, { runtimePublicKeyDigest: runtime, topologyAttestationDigest: d("topology-version-A") });
  const bWorker = worker("topo-B", f, { runtimePublicKeyDigest: runtime, topologyAttestationDigest: d("topology-version-B") });
  const a = S.chooseContinuationWorker([aWorker], f.request);
  const b = S.chooseContinuationWorker([bWorker], f.request);
  assert.equal(a.ok, true); assert.equal(b.ok, true);
  assert.notEqual(a.dispatch.challenge.challengeDigest, b.dispatch.challenge.challengeDigest);
  const verdictA = signVerdict(a.dispatch.challenge, f.verifierKeys.privateKey);
  assert.throws(() => C.verifiedContinuationBinding(f.passport, f.contract, b.dispatch.challenge, verdictA, f.verifierKeys.publicKey), /ATTESTATION_CHALLENGE_MISMATCH/);
});

test("failure-assessment substitution changes challenge even under one topology attestation", () => {
  const f = fixture();
  const runtime = d("shared-runtime-failure-replay");
  const topologyDigest = d("one-topology-attestation");
  const clean = worker("failure-clean", f, { runtimePublicKeyDigest: runtime, topologyAttestationDigest: topologyDigest, failurePoints: [] });
  const degraded = worker("failure-degraded", f, { runtimePublicKeyDigest: runtime, topologyAttestationDigest: topologyDigest, failurePoints: [7] });
  const a = S.chooseContinuationWorker([clean], f.request);
  const b = S.chooseContinuationWorker([degraded], f.request);
  assert.equal(a.ok, true); assert.equal(b.ok, true);
  assert.equal(a.dispatch.topologyAttestationDigest, b.dispatch.topologyAttestationDigest);
  assert.notEqual(a.dispatch.failureAssessmentDigest, b.dispatch.failureAssessmentDigest);
  assert.notEqual(a.dispatch.challenge.challengeDigest, b.dispatch.challenge.challengeDigest);
  const verdictA = signVerdict(a.dispatch.challenge, f.verifierKeys.privateKey);
  assert.throws(() => C.verifiedContinuationBinding(f.passport, f.contract, b.dispatch.challenge, verdictA, f.verifierKeys.publicKey), /ATTESTATION_CHALLENGE_MISMATCH/);
});

test("signed end-to-end delivery carries the same policy topology and failure assessment attested by hardware", () => {
  const f = fixture();
  const w = worker("tx", f);
  const tx = T.executeContinuationTransaction({
    candidates: [w],
    request: f.request,
    obtainSignedVerifierVerdict: ({ challenge }) => signVerdict(challenge, f.verifierKeys.privateKey),
    trustedVerifierPublicKey: f.verifierKeys.publicKey,
    executeWorker: ({ request }) => Object.freeze({
      schema: T.EXECUTION_SCHEMA,
      parentContinuationRoot: request.continuationRoot,
      childContinuationRoot: d("policy-child"),
      processId: request.processId,
      generationBefore: request.generation,
      generationAfter: request.generation + 1,
      emissionId: d("policy-emission"),
      guestReceiptIds: [d("policy-guest-receipt")],
      stopReason: "fuel-exhausted",
    }),
    deliveryPrivateKey: f.deliveryKeys.privateKey,
  });
  assert.equal(tx.dispatch.executionPolicyDigest, f.executionPolicy.executionPolicyDigest);
  assert.equal(tx.attestation.executionPolicyDigest, f.executionPolicy.executionPolicyDigest);
  assert.equal(tx.attestation.topologyAttestationDigest, tx.dispatch.topologyAttestationDigest);
  assert.equal(tx.attestation.failureAssessmentDigest, tx.dispatch.failureAssessmentDigest);
  assert.equal(tx.delivery.body.executionPolicyDigest, f.executionPolicy.executionPolicyDigest);
  assert.equal(tx.delivery.body.topologyAttestationDigest, tx.dispatch.topologyAttestationDigest);
  assert.equal(tx.delivery.body.failureAssessmentDigest, tx.dispatch.failureAssessmentDigest);
  assert.equal(T.verifyDelivery(tx.delivery, f.deliveryKeys.publicKey).ok, true);
});
