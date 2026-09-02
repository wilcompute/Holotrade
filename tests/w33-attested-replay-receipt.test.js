"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const test = require("node:test");
const F = require("../js/w33-attested-replay-receipt.js");

function d(label) {
  return `sha256:${crypto.createHash("sha256").update(label).digest("hex")}`;
}

function fixture() {
  const r0 = d("revocation-0"), r1 = d("revocation-1"), r2 = d("revocation-2");
  const b0 = { schema: "w33.capability-epoch-transition.v1", issuer: "w33-runtime-root", from_epoch: 0, from_root: r0, to_epoch: 1, to_root: r1, previous_transition_id: null };
  const b1 = { schema: "w33.capability-epoch-transition.v1", issuer: "w33-runtime-root", from_epoch: 1, from_root: r1, to_epoch: 2, to_root: r2, previous_transition_id: F.transitionId(b0) };
  const gc0 = d("gc0"), gc1 = d("gc1"), gc2 = d("gc2");
  const passport = {
    passportId: d("passport"),
    deploymentDigest: d("deployment"),
    machineType: "w33.circuit216.steinberg81",
    logicalDimension: 81,
    capabilityEpoch: 2,
    revocationRoot: r2,
    waitForRoot: d("wait"),
    cancellationRoot: d("cancel"),
    asyncScheduleRoot: d("schedule"),
    gcRegistryRoot: gc2,
    magicBudget: 3,
  };
  const nativeVerification = {
    ok: true,
    hardwareBacked: true,
    evidence: {
      schema: "holotrade.w33-native-snp-verification.v1",
      provider: "SEV_SNP",
      trustMode: "AMD_ARK_ASK_VCEK_CHAIN",
      reportDigest: d("snp-report"),
      measurement: `sha384:${"11".repeat(48)}`,
      reportedTcb: "12",
      challengeDigest: d("challenge"),
      runtimePublicKeyDigest: d("runtime-key"),
      vendorChainVerified: true,
    },
  };
  const artifacts = [{ role: "output", bytes: 5, digest: d("output-artifact") }];
  return {
    passport,
    nativeVerification,
    epochCertificates: [
      { schema: "w33.capability-epoch-quorum-certificate.v1", body: b0, signatures: [{ member_id: "a0", signature_b64: "bound-elsewhere" }] },
      { schema: "w33.capability-epoch-quorum-certificate.v1", body: b1, signatures: [{ member_id: "a0", signature_b64: "bound-elsewhere" }] },
    ],
    gcEvolution: [gc0, gc1, gc2],
    magicEvents: [
      { seq: 1, op: "reserve", token: d("magic-1"), packet: 7 },
      { seq: 2, op: "consume", token: d("magic-1"), packet: 7 },
    ],
    artifacts,
  };
}

test("flight recorder binds authority, concurrency, GC, magic, attestation and artifacts", () => {
  const f = fixture();
  const recorder = F.buildFlightRecorder({
    passport: f.passport,
    deploymentDigest: f.passport.deploymentDigest,
    nativeVerification: f.nativeVerification,
    epochCertificates: f.epochCertificates,
    gcEvolution: f.gcEvolution,
    magicEvents: f.magicEvents,
    artifacts: f.artifacts,
  });
  assert.equal(F.verifyFlightRecorderRoot(recorder), true);
  assert.equal(recorder.authority.epochTransitionCount, 2);
  assert.equal(recorder.persistence.gcTransitionCount, 3);
  assert.equal(recorder.magic.eventCount, 2);
  assert.equal(recorder.artifacts.count, 1);
});

test("flight recorder refuses incomplete epoch or GC history", () => {
  const f = fixture();
  assert.throws(() => F.buildFlightRecorder({ ...f, deploymentDigest: f.passport.deploymentDigest, epochCertificates: f.epochCertificates.slice(0, 1) }), /epoch chain invalid/);
  assert.throws(() => F.buildFlightRecorder({ ...f, deploymentDigest: f.passport.deploymentDigest, gcEvolution: f.gcEvolution.slice(0, 2) }), /GC evolution/);
});

test("COSE delivery receipt verifies the complete W33 flight-recorder root", () => {
  const f = fixture();
  const keys = crypto.generateKeyPairSync("ed25519");
  const signed = F.createAttestedReplayReceipt({
    receiptSpec: {
      executionId: "exec-flight-1",
      nodeId: "node-81",
      outcome: "settled",
      artifacts: f.artifacts,
      capabilities: { findings: [] },
      startedAtMs: 10,
      finishedAtMs: 20,
      nonce: "flight-recorder-nonce",
      microvmExecuted: true,
    },
    passport: f.passport,
    deploymentDigest: f.passport.deploymentDigest,
    nativeVerification: f.nativeVerification,
    epochCertificates: f.epochCertificates,
    gcEvolution: f.gcEvolution,
    magicEvents: f.magicEvents,
  }, keys.privateKey, { publicKey: keys.publicKey, keyId: "flight-recorder-key" });

  const verified = F.verifyAttestedReplayReceipt(signed, keys.publicKey);
  assert.equal(verified.ok, true);
  assert.equal(verified.code, "ATTESTED_REPLAY_RECEIPT_VERIFIED");
  assert.equal(verified.flightRecorderRoot, signed.flightRecorderRoot);
  assert.equal(verified.payload.runtime.hardwareAttested, true);
});

test("changing any replay history changes the committed flight-recorder root", () => {
  const f = fixture();
  const a = F.buildFlightRecorder({ ...f, deploymentDigest: f.passport.deploymentDigest });
  const b = F.buildFlightRecorder({ ...f, deploymentDigest: f.passport.deploymentDigest, magicEvents: [...f.magicEvents, { seq: 3, op: "cancel", token: d("magic-2") }] });
  const c = F.buildFlightRecorder({ ...f, deploymentDigest: f.passport.deploymentDigest, gcEvolution: [d("other-gc"), ...f.gcEvolution] });
  assert.notEqual(a.flightRecorderRoot, b.flightRecorderRoot);
  assert.notEqual(a.flightRecorderRoot, c.flightRecorderRoot);
});
