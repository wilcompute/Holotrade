"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const test = require("node:test");
const Native = require("../js/w33-native-attestation.js");
const Flight = require("../js/w33-attested-replay-receipt.js");
const Passport = require("../js/w33-passport-deployment.js");
const V = require("../js/w33-portable-audit-verifier.js");

function d(label) { return `sha256:${crypto.createHash("sha256").update(label).digest("hex")}`; }
function pem(key) { return key.export({ type: "spki", format: "pem" }); }

function snpFixture() {
  const challenge = { challengeDigest: d("portable-challenge"), runtimePublicKeyDigest: d("portable-runtime-key") };
  const vcek = crypto.generateKeyPairSync("ec", { namedCurve: "secp384r1" });
  const report = Buffer.alloc(Native.SNP.REPORT_BYTES);
  report.writeUInt32LE(5, 0); report.writeUInt32LE(1, 0x34); report.writeBigUInt64LE(12n, 0x180);
  Buffer.concat([Native.digestBytes(challenge.challengeDigest), Native.digestBytes(challenge.runtimePublicKeyDigest)]).copy(report, 0x50);
  const measurement = crypto.createHash("sha384").update("portable-launch").digest(); measurement.copy(report, 0x90);
  const der = crypto.sign("sha384", report.subarray(0, Native.SNP.SIGNED_BYTES), vcek.privateKey);
  Native.derSignatureToSnpRaw(der).copy(report, Native.SNP.SIGNATURE_OFFSET);
  const verification = Native.verifySnpReportNative({ report, challenge, expectedMeasurement: measurement, minimumReportedTcb: 10n, pinnedVcekPublicKey: vcek.publicKey });
  assert.equal(verification.ok, true);
  return { challenge, vcek, report, measurement, verification };
}

function authorityCertificate(body) {
  const keys = Array.from({ length: 5 }, () => crypto.generateKeyPairSync("ed25519"));
  const signatures = keys.slice(0, 4).map((k, i) => ({ member_id: `authority-${i}`, signature_b64: crypto.sign(null, Buffer.from(V.stable(body)), k.privateKey).toString("base64") }));
  return {
    cert: { schema: "w33.capability-epoch-quorum-certificate.v1", body, threshold: 4, population: 5, signatures },
    publicKeys: Object.fromEntries(keys.map((k, i) => [`authority-${i}`, pem(k.publicKey)])),
  };
}

function fixture() {
  const snp = snpFixture();
  const r0 = d("portable-r0"), r1 = d("portable-r1");
  const body = { schema: "w33.capability-epoch-transition.v1", issuer: "w33-runtime-root", from_epoch: 0, from_root: r0, to_epoch: 1, to_root: r1, previous_transition_id: null };
  const authority = authorityCertificate(body);
  const gc0 = d("portable-gc0"), gc1 = d("portable-gc1");
  const core = {
    schema: "holotrade.w33-execution-passport.v2",
    planDigest: d("plan"), profileDigest: d("profile"), machineType: "w33.circuit216.steinberg81", logicalDimension: 81,
    vmId: "VM-portable", deploymentDigest: d("deployment"), guestImage: d("guest"), memoryRoot: d("memory"),
    memoryCapabilityDigest: d("memcap"), componentLinkDigest: d("component"), packetRefinementDigest: d("packet"), historyRoot: d("history"),
    capabilityEpoch: 1, revocationRoot: r1, waitForRoot: d("wait"), cancellationRoot: d("cancel"), asyncScheduleRoot: d("schedule"),
    gcRegistryRoot: gc1, erasurePolicy: "EXPLICIT_DISCARD_ONLY", magicBudget: 1, runtimeRetype: "FORBIDDEN",
    symmetryNamespaces: { cliffordLift: "Sp(4,3)-clifford-lift", projectiveWeyl: "PGSp(4,3)-projective-weyl" },
  };
  const passport = Object.freeze({ ...core, passportId: Passport.sha256(core) });
  const artifacts = [{ role: "output", bytes: 9, digest: d("portable-output") }];
  const gcEvolution = [gc0, gc1];
  const magicEvents = [{ seq: 1, op: "consume", token: d("portable-magic") }];
  const receiptKeys = crypto.generateKeyPairSync("ed25519");
  const signed = Flight.createAttestedReplayReceipt({
    receiptSpec: { executionId: "portable-exec", nodeId: "node-81", outcome: "settled", artifacts, capabilities: { findings: [] }, startedAtMs: 1, finishedAtMs: 2, nonce: "portable-nonce", microvmExecuted: true },
    passport, deploymentDigest: passport.deploymentDigest, nativeVerification: snp.verification, epochCertificates: [authority.cert], gcEvolution, magicEvents,
  }, receiptKeys.privateKey, { publicKey: receiptKeys.publicKey, keyId: "portable-receipt" });
  const bundle = {
    envelope: signed.envelope,
    passport,
    epochCertificates: [authority.cert],
    authorityPublicKeys: authority.publicKeys,
    gcEvolution,
    magicEvents,
    concurrency: { waitForRoot: passport.waitForRoot, cancellationRoot: passport.cancellationRoot, asyncScheduleRoot: passport.asyncScheduleRoot },
    hardware: {
      provider: "SEV_SNP",
      reportBase64: snp.report.toString("base64"),
      challenge: snp.challenge,
      expectedMeasurement: `sha384:${snp.measurement.toString("hex")}`,
      minimumReportedTcb: "10",
      pinnedVcekPublicKeyPem: pem(snp.vcek.publicKey),
    },
  };
  return { bundle, receiptKeys };
}

test("portable verifier rebuilds hardware, authority and replay evidence before accepting COSE receipt", () => {
  const f = fixture();
  const result = V.verifyPortableBundle(f.bundle, f.receiptKeys.publicKey);
  assert.equal(result.ok, true);
  assert.equal(result.code, "PORTABLE_W33_AUDIT_PASS");
  assert.equal(result.hardwareProvider, "SEV_SNP");
  assert.equal(result.epochCertificateCount, 1);
});

test("portable verifier rejects an authority-signature substitution", () => {
  const f = fixture();
  const bad = structuredClone(f.bundle);
  bad.epochCertificates[0].signatures[0].signature_b64 = Buffer.alloc(64, 7).toString("base64");
  const result = V.verifyPortableBundle(bad, f.receiptKeys.publicKey);
  assert.equal(result.ok, false);
  assert.equal(result.code, "EPOCH_CERTIFICATE_SIGNATURE");
});

test("portable verifier rejects raw hardware substitution even when the signed receipt is intact", () => {
  const f = fixture();
  const bad = structuredClone(f.bundle);
  const report = Buffer.from(bad.hardware.reportBase64, "base64"); report[0x50] ^= 1; bad.hardware.reportBase64 = report.toString("base64");
  const result = V.verifyPortableBundle(bad, f.receiptKeys.publicKey);
  assert.equal(result.ok, false);
  assert.equal(result.code, "SNP_REPORT_DATA_MISMATCH");
});
