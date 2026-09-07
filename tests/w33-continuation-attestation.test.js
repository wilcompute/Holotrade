"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const crypto = require("node:crypto");

const A = require("../js/w33-measured-boot-attestation.js");
const C = require("../js/w33-continuation-attestation.js");
const D = require("../js/w33-passport-deployment.js");

function fixture() {
  const keys = crypto.generateKeyPairSync("ed25519");
  const deploymentDigest = A.sha256("deployment");
  const runtimePublicKeyDigest = A.sha256("runtime-public-key");
  const passport = Object.freeze({
    schema: D.SCHEMA,
    passportId: A.sha256("passport"),
    deploymentDigest,
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 7,
    revocationRoot: A.sha256("revocations"),
  });
  const contract = Object.freeze({ deploymentDigest });
  return { keys, passport, contract, runtimePublicKeyDigest };
}

function signedVerdict(challenge, privateKey) {
  return A.signVerifierVerdict({
    provider: A.PROVIDER.SEV_SNP,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: A.sha256("launch"),
    reportedTcbDigest: A.sha256("tcb"),
    signerChainDigest: A.sha256("vcek-chain"),
    hardwareBacked: true,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "fixture-verifier",
  }, privateKey);
}

function challenge(f, label = "A", generation = 3) {
  return C.buildContinuationChallenge({
    passport: f.passport,
    contract: f.contract,
    runtimePublicKeyDigest: f.runtimePublicKeyDigest,
    continuationRoot: A.sha256(`continuation-${label}`),
    processId: A.sha256(`process-${label}`),
    generation,
  });
}

test("continuation identity extends rather than replaces base measured-boot challenge", () => {
  const f = fixture();
  const a = challenge(f, "A", 3);
  const base = A.buildChallenge({
    passport: f.passport,
    contract: f.contract,
    runtimePublicKeyDigest: f.runtimePublicKeyDigest,
  });
  assert.equal(a.baseChallengeDigest, base.challengeDigest);
  assert.equal(a.passportId, f.passport.passportId);
  assert.equal(a.deploymentDigest, f.contract.deploymentDigest);
  assert.match(a.continuationRoot, /^sha256:/);
  assert.match(a.processId, /^sha256:/);
  assert.equal(a.generation, 3);
});

test("different fork or generation produces a different hardware challenge", () => {
  const f = fixture();
  const a = challenge(f, "A", 3);
  const fork = challenge(f, "B", 3);
  const next = challenge(f, "A", 4);
  assert.notEqual(a.challengeDigest, fork.challengeDigest);
  assert.notEqual(a.challengeDigest, next.challengeDigest);
  assert.equal(a.baseChallengeDigest, fork.baseChallengeDigest);
  assert.equal(a.baseChallengeDigest, next.baseChallengeDigest);
});

test("verdict signed for one continuation cannot authorize another", () => {
  const f = fixture();
  const a = challenge(f, "A", 3);
  const b = challenge(f, "B", 3);
  const verdict = signedVerdict(a, f.keys.privateKey);
  assert.throws(
    () => C.verifiedContinuationBinding(
      f.passport, f.contract, b, verdict, f.keys.publicKey
    ),
    /ATTESTATION_CHALLENGE_MISMATCH/
  );
});

test("verified binding and receipt evidence carry exact process identity", () => {
  const f = fixture();
  const a = challenge(f, "A", 3);
  const verdict = signedVerdict(a, f.keys.privateKey);
  const binding = C.verifiedContinuationBinding(
    f.passport, f.contract, a, verdict, f.keys.publicKey
  );
  assert.equal(binding.hardwareBacked, true);
  assert.equal(binding.continuationRoot, a.continuationRoot);
  assert.equal(binding.processId, a.processId);
  assert.equal(binding.generation, 3);
  assert.equal(binding.challengeDigest, a.challengeDigest);

  const evidence = C.toReceiptHardwareEvidence(
    f.passport, f.contract, a, verdict, f.keys.publicKey
  );
  assert.equal(evidence.hardwareAttested, true);
  assert.equal(evidence.evidence.length, 1);
  assert.equal(evidence.evidence[0].continuationRoot, a.continuationRoot);
  assert.equal(evidence.evidence[0].processId, a.processId);
  assert.equal(evidence.evidence[0].generation, 3);
  assert.equal(
    evidence.evidence[0].reasonCode,
    "CONTINUATION_BOUND_SIGNED_VERIFIER_VERDICT"
  );
});

test("metadata attachment is immutable and continuation-bound", () => {
  const f = fixture();
  const a = challenge(f, "A", 3);
  const verdict = signedVerdict(a, f.keys.privateKey);
  const out = C.attachContinuationReceiptMetadata(
    { requestId: "job-7" },
    f.passport,
    f.contract,
    a,
    verdict,
    f.keys.publicKey
  );
  assert.equal(out.requestId, "job-7");
  assert.equal(
    out.w33ContinuationAttestation.continuationRoot,
    a.continuationRoot
  );
  assert.ok(Object.isFrozen(out));
  assert.ok(Object.isFrozen(out.w33ContinuationAttestation));
});

test("malformed process identity or generation fails before attestation", () => {
  const f = fixture();
  assert.throws(
    () => C.buildContinuationChallenge({
      passport: f.passport,
      contract: f.contract,
      runtimePublicKeyDigest: f.runtimePublicKeyDigest,
      continuationRoot: "not-a-digest",
      processId: A.sha256("process"),
      generation: 0,
    }),
    /continuationRoot/
  );
  assert.throws(
    () => C.buildContinuationChallenge({
      passport: f.passport,
      contract: f.contract,
      runtimePublicKeyDigest: f.runtimePublicKeyDigest,
      continuationRoot: A.sha256("continuation"),
      processId: A.sha256("process"),
      generation: -1,
    }),
    /generation/
  );
});
