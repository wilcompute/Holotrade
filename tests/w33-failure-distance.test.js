"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");

const F = require("../scheduler/w33-failure-distance.js");
const R = require("../scheduler/w33-topology-resilience.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const D = require("../js/w33-passport-deployment.js");

function d(x) { return S.sha256(x); }

function request(overrides = {}) {
  const deploymentDigest = d("fd-deployment");
  return {
    continuationRoot: d("fd-continuation"),
    processId: d("fd-process"),
    generation: 3,
    passport: Object.freeze({
      schema: D.SCHEMA,
      passportId: d("fd-passport"),
      deploymentDigest,
      machineType: "w33.circuit216.steinberg81",
      logicalDimension: 81,
      capabilityEpoch: 1,
      revocationRoot: d("fd-revocations"),
    }),
    contract: Object.freeze({ deploymentDigest }),
    requireLineResilience: true,
    durationSeconds: 1,
    ...overrides,
  };
}

function worker(id, req, failurePoints, cost = 1) {
  return Object.freeze({
    id,
    evidenceLevel: S.EVIDENCE.SOFTWARE_VERIFIED,
    runtimePublicKeyDigest: d(`runtime-${id}`),
    topology: Object.freeze({
      attested: true,
      attestationDigest: d(`topology-${id}`),
      points: Array.from({ length: 40 }, (_, i) => i),
      failurePoints,
    }),
    retainedUnionDeltaBytes: { [req.continuationRoot]: 0 },
    computePerSecondUSD: cost,
  });
}

test("empty W33 failure set is exactly distance 11 from all-lines-hit", () => {
  const out = F.exactFailureDistance([]);
  assert.equal(out.exact, true);
  assert.equal(out.distance, 11);
  assert.equal(out.witnessAdditionalFailures.length, 11);
  assert.equal(R.assessFailures(out.witnessAdditionalFailures).allLinesHit, true);
});

test("all-lines-hit blocker has distance zero and deleting one blocker point has distance one", () => {
  const blocker = [...R.GEOMETRY.adjacency[0]];
  assert.equal(blocker.length, 12);
  assert.equal(F.exactFailureDistance(blocker).distance, 0);
  const almost = blocker.slice(1);
  const out = F.exactFailureDistance(almost);
  assert.equal(out.distance, 1);
  assert.equal(R.assessFailures([...almost, ...out.witnessAdditionalFailures]).allLinesHit, true);
});

test("scheduler can require an exact distance floor", () => {
  const req = request({ minimumAdditionalFailuresToBlockAllLines: 11 });
  const clean = worker("clean", req, [], 1);
  const degraded = worker("degraded", req, [0], 0);
  const ranked = S.rankContinuations([degraded, clean], req);
  assert.equal(ranked.eligible.length, 1);
  assert.equal(ranked.eligible[0].workerId, "clean");
  assert.equal(ranked.eligible[0].additionalFailuresToBlockAllLines, 11);
  assert.equal(ranked.rejected.length, 1);
  assert.equal(ranked.rejected[0].code, "W33_FAILURE_DISTANCE_FLOOR_UNMET");
  assert.ok(ranked.rejected[0].resilience.additionalFailuresToBlockAllLines < 11);
});

test("at equal price the farther worker wins only as an explicit deterministic tiebreaker", () => {
  const req = request();
  const clean = worker("clean", req, [], 1);
  const degraded = worker("degraded", req, [0], 1);
  const ranked = S.rankContinuations([degraded, clean], req);
  assert.equal(ranked.eligible.length, 2);
  assert.equal(ranked.eligible[0].price.totalUSD, ranked.eligible[1].price.totalUSD);
  assert.ok(ranked.eligible[0].additionalFailuresToBlockAllLines >= ranked.eligible[1].additionalFailuresToBlockAllLines);
  assert.equal(ranked.eligible[0].workerId, "clean");
});

test("failure distance is inside the attested failure-assessment digest", () => {
  const req = request();
  const a = S.chooseContinuationWorker([worker("a", req, [])], req);
  const b = S.chooseContinuationWorker([worker("b", req, [0])], req);
  assert.equal(a.ok, true); assert.equal(b.ok, true);
  assert.notEqual(a.dispatch.failureAssessmentDigest, b.dispatch.failureAssessmentDigest);
  assert.notEqual(a.dispatch.attestationChallengeDigest, b.dispatch.attestationChallengeDigest);
  assert.notEqual(a.dispatch.additionalFailuresToBlockAllLines, b.dispatch.additionalFailuresToBlockAllLines);
});
