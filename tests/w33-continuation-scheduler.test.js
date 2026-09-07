"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");

const D = require("../js/w33-passport-deployment.js");
const S = require("../scheduler/w33-continuation-scheduler.js");

function d(label) { return S.sha256(label); }

function fixture() {
  const deploymentDigest = d("deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("passport"),
    deploymentDigest,
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 9,
    revocationRoot: d("revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  const continuationRoot = d("continuation");
  const processId = d("process");
  const request = Object.freeze({
    continuationRoot,
    processId,
    generation: 4,
    passport,
    contract,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints: [0, 1, 2, 3],
    durationSeconds: 10,
  });
  const topology = (label, points = [0, 1, 2, 3, 4, 5]) => Object.freeze({
    attested: true,
    attestationDigest: d(`topology-${label}`),
    points,
  });
  const worker = (id, opts = {}) => Object.freeze({
    id,
    evidenceLevel: opts.evidenceLevel ?? S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d(`runtime-${id}`),
    topology: opts.topology || topology(id),
    retainedUnionDeltaBytes: opts.retainedUnionDeltaBytes || { [continuationRoot]: 2000 },
    computePerSecondUSD: opts.computePerSecondUSD ?? 0.01,
    startupUSD: opts.startupUSD ?? 0,
  });
  return { request, worker, continuationRoot, processId };
}

const policy = Object.freeze({
  retainedByteSecondUSD: 0.000001,
  transferByteUSD: 0.00001,
});

test("scheduler chooses by exact retained-union delta after evidence/topology gates", () => {
  const f = fixture();
  const cheapButUnattested = f.worker("unattested", {
    evidenceLevel: S.EVIDENCE.SIGNED_RUNTIME,
    retainedUnionDeltaBytes: { [f.continuationRoot]: 0 },
    computePerSecondUSD: 0,
  });
  const cold = f.worker("cold", {
    retainedUnionDeltaBytes: { [f.continuationRoot]: 5000 },
  });
  const warm = f.worker("warm", {
    retainedUnionDeltaBytes: { [f.continuationRoot]: 500 },
  });
  const out = S.chooseContinuationWorker([cheapButUnattested, cold, warm], f.request, policy);
  assert.equal(out.ok, true);
  assert.equal(out.dispatch.workerId, "warm");
  assert.equal(out.dispatch.retainedUnionDeltaBytes, 500);
  assert.equal(out.ranked.rejected[0].code, "EVIDENCE_FLOOR_UNMET");
});

test("missing exact retained delta fails closed rather than guessing deduplication", () => {
  const f = fixture();
  const worker = f.worker("missing", { retainedUnionDeltaBytes: {} });
  const out = S.rankContinuations([worker], f.request, policy);
  assert.equal(out.eligible.length, 0);
  assert.equal(out.rejected[0].code, "EXACT_RETAINED_DELTA_REQUIRED");
});

test("abstract geometry without runtime topology attestation is not dispatchable", () => {
  const f = fixture();
  const worker = f.worker("abstract", {
    topology: { attested: false, attestationDigest: d("abstract"), points: [0, 1, 2, 3] },
  });
  const out = S.rankContinuations([worker], f.request, policy);
  assert.equal(out.eligible.length, 0);
  assert.equal(out.rejected[0].code, "TOPOLOGY_ATTESTATION_REQUIRED");
});

test("worker migration preserves process tuple and renews hardware challenge", () => {
  const f = fixture();
  const a = f.worker("A", { retainedUnionDeltaBytes: { [f.continuationRoot]: 100 } });
  const b = f.worker("B", { retainedUnionDeltaBytes: { [f.continuationRoot]: 900 } });
  const first = S.dispatchFor(a, S.normalizeRequest(f.request), policy);
  const migration = S.migrateWorker(first, b, f.request, policy);
  assert.equal(migration.processIdentityPreserved, true);
  assert.equal(migration.continuationRoot, f.continuationRoot);
  assert.equal(migration.processId, f.processId);
  assert.equal(migration.generation, 4);
  assert.equal(migration.workerIdentityChanged, true);
  assert.equal(migration.attestationMustBeRenewed, true);
  assert.notEqual(migration.oldChallengeDigest, migration.newChallengeDigest);
  assert.notEqual(migration.oldRuntimePublicKeyDigest, migration.newRuntimePublicKeyDigest);
});

test("migration cannot silently substitute a different continuation", () => {
  const f = fixture();
  const a = f.worker("A");
  const first = S.dispatchFor(a, S.normalizeRequest(f.request), policy);
  assert.throws(
    () => S.migrateWorker(first, f.worker("B"), { ...f.request, continuationRoot: d("other") }, policy),
    /may not mutate process continuation identity/
  );
});

test("dispatch challenge commits exact continuation generation and worker runtime key", () => {
  const f = fixture();
  const a = f.worker("A");
  const dispatch = S.dispatchFor(a, S.normalizeRequest(f.request), policy);
  assert.equal(dispatch.challenge.continuationRoot, f.continuationRoot);
  assert.equal(dispatch.challenge.processId, f.processId);
  assert.equal(dispatch.challenge.generation, 4);
  assert.equal(dispatch.challenge.runtimePublicKeyDigest, a.runtimePublicKeyDigest);
  assert.match(dispatch.dispatchDigest, /^sha256:[0-9a-f]{64}$/);
});
