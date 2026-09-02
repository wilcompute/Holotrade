"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const test = require("node:test");
const Host = require("../js/w33-host-audit-bundle.js");
const Settlement = require("../js/w33-hardware-evidence-settlement.js");
const Native = require("../js/w33-native-attestation.js");
const Passport = require("../js/w33-passport-deployment.js");
const Receipt = require("../runtime/receipt.js");

function d(s) { return `sha256:${crypto.createHash("sha256").update(s).digest("hex")}`; }

function fixture() {
  const challenge = { challengeDigest: d("host-challenge-settle"), runtimePublicKeyDigest: d("host-runtime-key-settle") };
  const p384 = crypto.generateKeyPairSync("ec", { namedCurve: "secp384r1" });
  const report = Buffer.alloc(Native.SNP.REPORT_BYTES);
  report.writeUInt32LE(5, 0); report.writeUInt32LE(1, 0x34); report.writeBigUInt64LE(9n, 0x180);
  Buffer.concat([Native.digestBytes(challenge.challengeDigest), Native.digestBytes(challenge.runtimePublicKeyDigest)]).copy(report, 0x50);
  const measurement = crypto.createHash("sha384").update("host-launch-settle").digest(); measurement.copy(report, 0x90);
  crypto.createHash("sha512").update("host-chip-settle").digest().copy(report, 0x1a0);
  const sig = crypto.sign("sha384", report.subarray(0, Native.SNP.SIGNED_BYTES), p384.privateKey);
  Native.derSignatureToSnpRaw(sig).copy(report, Native.SNP.SIGNATURE_OFFSET);
  const native = Native.verifySnpReportNative({ report, challenge, expectedMeasurement: measurement, minimumReportedTcb: 8n, pinnedVcekPublicKey: p384.publicKey });
  assert.equal(native.ok, true);

  const core = {
    schema: "holotrade.w33-execution-passport.v2", deploymentDigest: d("deployment-settle"),
    machineType: "w33.circuit216.steinberg81", logicalDimension: 81,
    capabilityEpoch: 0, revocationRoot: d("revocation0-settle"), waitForRoot: d("wait-settle"),
    cancellationRoot: d("cancel-settle"), asyncScheduleRoot: d("schedule-settle"), gcRegistryRoot: d("gc-settle"), magicBudget: 2,
  };
  const passport = Object.freeze({ ...core, passportId: Passport.sha256(core) });
  const telemetry = Host.normalizeTelemetry({ nodeId: "node-settle", rapl: { beforeUj: 1000000, afterUj: 2500000, maxRangeUj: 10000000 } });
  const artifacts = [{ role: "output", bytes: 4, digest: d("artifact-settle") }];
  const receiptKeys = crypto.generateKeyPairSync("ed25519");
  const signed = Host.createMeasuredAttestedReplayReceipt({
    receiptSpec: { executionId: "exec-host-settle", nodeId: "node-settle", outcome: "settled", artifacts, capabilities: { findings: [] }, startedAtMs: 1, finishedAtMs: 2, nonce: "host-settle-nonce", microvmExecuted: true },
    passport, deploymentDigest: passport.deploymentDigest, nativeVerification: native, epochCertificates: [], gcEvolution: [passport.gcRegistryRoot], magicEvents: [],
  }, receiptKeys.privateKey, { publicKey: receiptKeys.publicKey, keyId: "host-receipt-settle" }, telemetry);
  const hardware = { provider: "SEV_SNP", reportBase64: report.toString("base64"), challenge, expectedMeasurement: `sha384:${measurement.toString("hex")}`, minimumReportedTcb: "8", pinnedVcekPublicKeyPem: p384.publicKey.export({ type: "spki", format: "pem" }) };
  const bundle = Host.buildHostBundle({ signedReceipt: signed, passport, epochCertificates: [], authorityPublicKeys: {}, gcEvolution: [passport.gcRegistryRoot], magicEvents: [], hardware, telemetry }, receiptKeys.publicKey);
  return { bundle, receiptKeys, passport, telemetry };
}

test("verified host bundle becomes second-stage signed settlement evidence", () => {
  const f = fixture();
  const evidence = Settlement.admitVerifiedHostBundle(f.bundle, f.receiptKeys.publicKey);
  assert.equal(evidence.verified, true);
  assert.match(evidence.hostBundleDigest, /^sha256:[0-9a-f]{64}$/);
  assert.equal(evidence.passportId, f.passport.passportId);

  const settlementKeys = crypto.generateKeyPairSync("ed25519");
  const spec = {
    executionId: "exec-settlement-1", nodeId: "market-settlement", outcome: "hardware-audit-settled",
    artifacts: [{ role: "verified-host-bundle", bytes: 1, digest: evidence.hostBundleDigest }], capabilities: { findings: [] },
    startedAtMs: 10, finishedAtMs: 11, nonce: "settlement-nonce", metadata: { settlementClass: "REAL_HOST_EVIDENCE_BINDING" }, microvmExecuted: false,
  };
  const signed = Settlement.createHardwareBoundSettlementReceipt(spec, evidence, settlementKeys.privateKey, { publicKey: settlementKeys.publicKey, keyId: "settlement-key" });
  const v = Settlement.verifyHardwareBoundSettlementReceipt(signed.envelope, settlementKeys.publicKey, evidence);
  assert.equal(v.ok, true);
  assert.equal(v.code, "W33_HARDWARE_BOUND_SETTLEMENT_PASS");

  const raw = Receipt.verifyDeliveryReceipt(signed.envelope, settlementKeys.publicKey);
  assert.equal(raw.valid, true);
  assert.equal(raw.payload.metadata.w33VerifiedHostBundleDigest, evidence.hostBundleDigest);
});

test("mutated host bundle is rejected before second-stage binding", () => {
  const f = fixture();
  const bad = { ...f.bundle, telemetry: { ...f.bundle.telemetry, nodeId: "mutated" } };
  assert.throws(() => Settlement.admitVerifiedHostBundle(bad, f.receiptKeys.publicKey), /not admissible verified evidence/);
});

test("unverified evidence cannot be signed into settlement metadata", () => {
  const keys = crypto.generateKeyPairSync("ed25519");
  const spec = { executionId: "x", nodeId: "n", outcome: "o", artifacts: [{ role: "a", bytes: 1, digest: d("a") }], capabilities: { findings: [] }, startedAtMs: 1, finishedAtMs: 2, nonce: "n" };
  assert.throws(() => Settlement.createHardwareBoundSettlementReceipt(spec, { verified: false }, keys.privateKey), /verified W33 host evidence required/);
});
