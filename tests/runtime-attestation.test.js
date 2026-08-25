"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const R = require("../runtime/index.js");

function fixedEd25519KeyPair() {
  // RFC 8032 test-vector seed/public key, wrapped in PKCS#8/SPKI DER.
  const seed = Buffer.from("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60", "hex");
  const point = Buffer.from("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "hex");
  return {
    privateKey: crypto.createPrivateKey({
      key: Buffer.concat([Buffer.from("302e020100300506032b657004220420", "hex"), seed]),
      type: "pkcs8",
      format: "der",
    }),
    publicKey: crypto.createPublicKey({
      key: Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), point]),
      type: "spki",
      format: "der",
    }),
  };
}

async function fixture(t, name = "runtime") {
  const root = await fs.promises.mkdtemp(path.join(os.tmpdir(), `holotrade-${name}-`));
  t.after(() => fs.promises.rm(root, { recursive: true, force: true }));
  return root;
}

test("artifact measurement hashes the actual bytes with SHA-256", async (t) => {
  const root = await fixture(t, "artifact");
  const artifact = path.join(root, "kernel.bin");
  await fs.promises.writeFile(artifact, Buffer.from("holotrade-kernel-fixture\n"));
  const record = await R.hashArtifact(artifact, { role: "guest-kernel" });

  assert.equal(record.role, "guest-kernel");
  assert.equal(record.bytes, 25);
  assert.equal(record.digest, R.sha256Bytes(Buffer.from("holotrade-kernel-fixture\n")));
  assert.match(record.digest, /^sha256:[0-9a-f]{64}$/);
});

test("deterministic CBOR and COSE Sign1 use a real Ed25519 signature", () => {
  const a = { z: "last", a: 7, nested: { two: 2, one: 1 } };
  const b = { nested: { one: 1, two: 2 }, a: 7, z: "last" };
  assert.deepEqual(R.cbor.encode(a), R.cbor.encode(b));

  const { privateKey, publicKey } = fixedEd25519KeyPair();
  const first = R.cose.signDeliveryReceipt(a, privateKey, { publicKey, keyId: "test-key" });
  const second = R.cose.signDeliveryReceipt(b, privateKey, { publicKey, keyId: "test-key" });
  assert.equal(first.coseSign1, second.coseSign1, "Ed25519 and deterministic CBOR produce identical envelopes");
  const verified = R.cose.verifyDeliveryReceipt(first, publicKey);
  assert.equal(verified.valid, true);
  assert.equal(verified.keyId, "test-key");
  assert.equal(verified.payload.a, 7);
  assert.equal(R.cose.verifyDeliveryReceipt(first, null).valid, false, "the embedded key is never silently trusted");

  const rsa = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
  assert.throws(() => R.cose.signDeliveryReceipt(a, rsa.privateKey), /Ed25519/);

  const tampered = { ...first, coseSign1: `${first.coseSign1.slice(0, -2)}AA` };
  assert.equal(R.cose.verifyDeliveryReceipt(tampered, publicKey).valid, false);
  assert.equal(R.cose.verifyDeliveryReceipt({ ...first, keyId: "attacker-key" }, publicKey).valid, false);
});

test("capability detection distinguishes absent, inaccessible and unverified surfaces", async (t) => {
  const root = await fixture(t, "capabilities");
  const report = await R.detectRuntimeCapabilities({
    now: 0,
    kvmPath: path.join(root, "missing-kvm"),
    tpmDevices: [path.join(root, "missing-tpm")],
    measuredBootLogs: [path.join(root, "missing-event-log")],
    imaLogs: [path.join(root, "missing-ima")],
    sevGuestPath: path.join(root, "missing-sev-guest"),
    sevHostPath: path.join(root, "missing-sev"),
    sevModulePath: path.join(root, "missing-sev-module"),
    powercapPath: path.join(root, "missing-powercap"),
    firecrackerBinary: path.join(root, "missing-firecracker"),
    env: {},
  });
  const byId = Object.fromEntries(report.findings.map((item) => [item.id, item]));

  assert.equal(report.observedAt, "1970-01-01T00:00:00.000Z");
  assert.equal(report.launchable, false);
  assert.equal(report.hardwareAttestationReady, false);
  assert.equal(byId.kvm.reasonCode, "DEVICE_NOT_FOUND");
  assert.equal(byId.measured_boot.reasonCode, "TPM_EVENT_LOG_NOT_FOUND");
  assert.equal(byId.sev_snp_guest_attestation.reasonCode, "SEV_GUEST_DEVICE_NOT_FOUND");
  assert.equal(byId.kepler.reasonCode, "METRICS_ENDPOINT_NOT_CONFIGURED");
});

test("RAPL metering reads real counter files and handles wraparound", async (t) => {
  const root = await fixture(t, "rapl");
  const zone = path.join(root, "intel-rapl-0");
  await fs.promises.mkdir(zone, { recursive: true });
  await fs.promises.writeFile(path.join(zone, "name"), "package-0\n");
  await fs.promises.writeFile(path.join(zone, "max_energy_range_uj"), "1000\n");
  await fs.promises.writeFile(path.join(zone, "energy_uj"), "900\n");
  const meter = await R.RaplMeter.discover(root);
  const before = await meter.snapshot(1000);
  await fs.promises.writeFile(path.join(zone, "energy_uj"), "125\n");
  const after = await meter.snapshot(1250);
  const delta = meter.delta(before, after);

  assert.equal(delta.status, "MEASURED");
  assert.equal(delta.durationMs, 250);
  assert.equal(delta.totalMicrojoules, 225n);
  assert.equal(delta.readings[0].wrapped, true);
});

test("Kepler metering consumes observed Prometheus counters rather than modeled watts", async () => {
  const bodies = [
    "# TYPE kepler_node_cpu_joules_total counter\nkepler_node_cpu_joules_total{node_name=\"n1\"} 10.25\n",
    "# TYPE kepler_node_cpu_joules_total counter\nkepler_node_cpu_joules_total{node_name=\"n1\"} 12.75\n",
  ];
  const fetchImpl = async () => ({ ok: true, status: 200, text: async () => bodies.shift() });
  const meter = new R.KeplerMeter("http://kepler.invalid/metrics", { fetchImpl });
  const before = await meter.snapshot(10);
  const after = await meter.snapshot(20);
  const delta = meter.delta(before, after);

  assert.equal(before.status, "OBSERVED");
  assert.equal(delta.status, "MEASURED");
  assert.equal(delta.totalMicrojoules, 2_500_000n);
});

test("hardware bytes are bound but never called attested without a verifier", async (t) => {
  const root = await fixture(t, "hardware-evidence");
  const report = path.join(root, "snp-report.bin");
  await fs.promises.writeFile(report, Buffer.alloc(1184, 0xa5));

  const bound = await R.collectHardwareEvidence({ sevSnpReportPath: report });
  const snp = bound.evidence.find((item) => item.kind === "SEV_SNP_REPORT");
  assert.equal(snp.status, "BOUND_UNVERIFIED");
  assert.equal(bound.hardwareAttested, false);

  const verified = await R.collectHardwareEvidence({
    sevSnpReportPath: report,
    verifySevSnpReport: async (_path, evidence) => ({ valid: evidence.bytes === 1184, verifier: "test-only" }),
  });
  assert.equal(verified.hardwareAttested, true);
  assert.equal(verified.evidence.find((item) => item.kind === "SEV_SNP_REPORT").status, "VERIFIED");
});

test("delivery receipt binds artifact, capability, energy and hardware evidence", async (t) => {
  const root = await fixture(t, "receipt");
  const file = path.join(root, "rootfs.ext4");
  await fs.promises.writeFile(file, Buffer.from("rootfs fixture"));
  const artifact = await R.hashArtifact(file, { role: "rootfs" });
  const capabilities = { findings: [{ id: "kvm", status: "INACCESSIBLE", reasonCode: "READ_WRITE_ACCESS_REQUIRED" }] };
  const hardwareEvidence = await R.collectHardwareEvidence();
  const { privateKey, publicKey } = crypto.generateKeyPairSync("ed25519");
  const signed = R.createSignedDeliveryReceipt({
    executionId: "exec-1",
    nodeId: "node-1",
    outcome: "UNAVAILABLE",
    artifacts: [artifact],
    capabilities,
    energy: { source: "RAPL", status: "UNAVAILABLE", totalMicrojoules: 0n },
    hardwareEvidence,
    startedAtMs: 1000,
    finishedAtMs: 1000,
    nonce: "challenge-123",
  }, privateKey, { publicKey, keyId: "operator-a" });

  const result = R.verifyDeliveryReceipt(signed.envelope, publicKey);
  assert.equal(result.valid, true);
  assert.equal(result.payload.runtime.microvmExecuted, false);
  assert.equal(result.payload.runtime.hardwareAttested, false);
  assert.equal(result.payload.artifacts[0].digest, artifact.digest);
});

test("Firecracker launch refuses before spawn when KVM or artifacts are unavailable", async (t) => {
  const root = await fixture(t, "firecracker-refusal");
  const artifact = path.join(root, "artifact.bin");
  await fs.promises.writeFile(artifact, "not a boot image");
  let spawned = false;
  const runtime = new R.FirecrackerRuntime({
    binary: "/bin/true",
    spawnImpl: () => { spawned = true; throw new Error("must not spawn"); },
    capabilityOptions: {
      now: 0,
      kvmPath: path.join(root, "missing-kvm"),
      tpmDevices: [],
      measuredBootLogs: [],
      imaLogs: [],
      sevGuestPath: path.join(root, "missing-sev-guest"),
      sevHostPath: path.join(root, "missing-sev"),
      sevModulePath: path.join(root, "missing-sev-module"),
      powercapPath: path.join(root, "missing-powercap"),
      env: {},
    },
  });
  const result = await runtime.launch({ kernelPath: artifact, rootfsPath: artifact, now: 0 });

  assert.equal(result.status, "UNAVAILABLE");
  assert.equal(result.executed, false);
  assert.equal(spawned, false);
  assert.ok(result.preflight.blockers.some((item) => item.code.startsWith("KVM_")));
  assert.equal(result.preflight.artifacts.length, 2, "both launch inputs are hashed even when KVM is unavailable");
});
