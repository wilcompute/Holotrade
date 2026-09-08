"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");

const D = require("../js/w33-passport-deployment.js");
const X = require("../js/w33-accelerator-certificate.js");
const S = require("../scheduler/w33-continuation-scheduler.js");
const Q = require("../scheduler/w33-cache-aware-accelerator-scheduler.js");

function d(x) { return S.sha256(x); }
function load(pathEnv) {
  const p = process.env[pathEnv];
  if (!p) throw new Error(`${pathEnv} is required`);
  return JSON.parse(fs.readFileSync(p, "utf8"));
}
function fixture(cert, artifactId) {
  const deploymentDigest = d("cache-economics-deployment");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: d("cache-economics-passport"),
    deploymentDigest,
    machineType: cert.machineType,
    logicalDimension: 81,
    capabilityEpoch: 37,
    revocationRoot: d("cache-economics-revocations"),
  });
  const request = Object.freeze({
    continuationRoot: cert.parentContinuationRoot,
    processId: cert.processId,
    generation: cert.generationBefore,
    passport,
    contract: Object.freeze({ deploymentDigest }),
    acceleratorCertificate: cert,
    evidenceFloor: S.EVIDENCE.HARDWARE_ATTESTED,
    durationSeconds: 10,
  });
  const common = {
    evidenceLevel: S.EVIDENCE.HARDWARE_ATTESTED,
    runtimePublicKeyDigest: d("shared-cache-runtime"),
    topology: Object.freeze({ attested: true, attestationDigest: d("shared-cache-topology"), points: Array.from({ length: 40 }, (_, i) => i), failurePoints: [] }),
    retainedUnionDeltaBytes: { [cert.parentContinuationRoot]: 2048 },
    computePerSecondUSD: 0.02,
    startupUSD: 0.01,
    controlCompileUSD: 0.40,
    controlSetupUSD: 0.10,
    cachedControlSetupUSD: 0.02,
  };
  const cold = Object.freeze({ id: "cold-worker", ...common });
  const hot = Object.freeze({
    id: "hot-worker", ...common,
    controlArtifactCache: Object.freeze({
      [artifactId]: Object.freeze({ present: true, calibrationEpoch: cert.calibrationEpoch, compiledArtifactDigest: d("compiled-control-binary") }),
    }),
  });
  return { request, cold, hot };
}

test("Holotrade derives exactly the W33 process-independent control artifact id", () => {
  const cert = X.verifyAcceleratorCertificate(load("W33_ACCELERATOR_CERTIFICATE"));
  const identity = load("W33_CONTROL_ARTIFACT_IDENTITY");
  assert.equal(identity.status, "PASS");
  assert.equal(Q.controlArtifactId(cert), identity.controlArtifact.artifact_id);
  const body = Q.controlArtifactBody(cert);
  for (const forbidden of ["processId", "parentContinuationRoot", "childContinuationRoot", "generationBefore", "generationAfter", "receiptChainDigest"]) {
    assert.equal(Object.hasOwn(body, forbidden), false);
  }
});

test("cache hit reduces only control compilation/setup economics and never semantic work", () => {
  const cert = X.verifyAcceleratorCertificate(load("W33_ACCELERATOR_CERTIFICATE"));
  const artifactId = Q.controlArtifactId(cert);
  const f = fixture(cert, artifactId);
  const ranked = Q.quoteCacheAware([f.cold, f.hot], f.request, { retainedByteSecondUSD: 0.000001, transferByteUSD: 0.00001 });
  assert.equal(ranked.eligible.length, 2);
  assert.equal(ranked.winner.workerId, "hot-worker");
  const hot = ranked.eligible.find((x) => x.workerId === "hot-worker");
  const cold = ranked.eligible.find((x) => x.workerId === "cold-worker");
  assert.equal(hot.cacheHit, true);
  assert.equal(cold.cacheHit, false);
  assert.equal(hot.controlCompilationUSD, 0);
  assert.equal(cold.controlCompilationUSD, 0.40);
  assert.ok(hot.controlSetupUSD < cold.controlSetupUSD);
  assert.equal(hot.semanticComputeUSD, cold.semanticComputeUSD);
  assert.equal(hot.retainedStateUSD, cold.retainedStateUSD);
  assert.equal(hot.transferUSD, cold.transferUSD);
  assert.equal(hot.genericStartupUSD, cold.genericStartupUSD);
  assert.equal(hot.retainedUnionDeltaBytes, cold.retainedUnionDeltaBytes);
  assert.deepEqual(hot.semanticWork, cold.semanticWork);
  assert.equal(hot.semanticWork.receiptCount, cert.subreceiptIds.length);
  assert.equal(hot.semanticWork.generationSpan, cert.generationAfter - cert.generationBefore);
  assert.ok(hot.totalUSD < cold.totalUSD);
});

test("cache entry from wrong calibration epoch is a miss", () => {
  const cert = X.verifyAcceleratorCertificate(load("W33_ACCELERATOR_CERTIFICATE"));
  const artifactId = Q.controlArtifactId(cert);
  const f = fixture(cert, artifactId);
  const stale = Object.freeze({
    ...f.hot,
    id: "stale-worker",
    controlArtifactCache: Object.freeze({ [artifactId]: Object.freeze({ present: true, calibrationEpoch: cert.calibrationEpoch + "-stale", compiledArtifactDigest: d("stale-binary") }) }),
  });
  const ranked = Q.quoteCacheAware([stale], f.request);
  assert.equal(ranked.eligible[0].cacheHit, false);
  assert.equal(ranked.eligible[0].controlCompilationUSD, 0.40);
});
