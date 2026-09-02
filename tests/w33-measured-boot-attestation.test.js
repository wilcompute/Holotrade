const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");
const crypto = require("node:crypto");

global.window = global;
const root = path.resolve(__dirname, "..");
const { ExecutionPlan } = require(path.join(root, "js/execution.js"));
const P = require(path.join(root, "js/w33-execution-profile.js"));
const X = require(path.join(root, "js/w33-profiled-execution.js"));
const D = require(path.join(root, "js/w33-passport-deployment.js"));
const A = require(path.join(root, "js/w33-measured-boot-attestation.js"));
const Receipt = require(path.join(root, "runtime/receipt.js"));

function d(label) { return D.sha256({ label }); }

function fixture() {
  const plan = new ExecutionPlan({ name: "attested", workloadId: "llm-train", requestedSeconds: 1, artifacts: [{ name: "img", digest: "sha256:demo" }], magicBudget: 1 });
  plan.magicBudget = 1; plan.digest = plan.computeDigest(); plan.signature = plan.sign();
  const node = { id: "attested81" };
  const base = { place: () => [{ node, score: 1 }], launch: (_p, n) => ({ ok: true, vm: { id: `vm-${n.id}` }, node: n }) };
  const registry = new X.W33HostRegistry(); registry.register(node.id, P.MACHINE_TYPE.CIRCUIT_ST81);
  const engine = new X.ProfiledExecutionEngine(base, registry);
  const profile = P.bind(plan, P.MACHINE_TYPE.CIRCUIT_ST81);
  const vm = engine.launch(plan, profile, node).vm;
  const contract = engine.compileGoMicroVM(plan, profile);
  const passport = D.bindPassport({
    plan, profile, vm, contract,
    guestImage: d("guest"), memoryRoot: d("memory"), memoryCapabilityDigest: d("cap"), componentLinkDigest: d("link"), packetRefinementDigest: d("packet"), historyRoot: d("history"),
    capabilityEpoch: 3, revocationRoot: d("rev3"), waitForRoot: d("wait"), cancellationRoot: d("cancel"), asyncScheduleRoot: d("schedule"), gcRegistryRoot: d("gc"), magicBudget: 1,
  });
  return { plan, profile, vm, node, contract, passport };
}

function signedVerdict(challenge, key, provider = A.PROVIDER.SEV_SNP, hardwareBacked = true) {
  return A.signVerifierVerdict({
    provider,
    challengeDigest: challenge.challengeDigest,
    launchMeasurement: d("launch-measurement"),
    reportedTcbDigest: d("reported-tcb"),
    signerChainDigest: d("vendor-chain"),
    hardwareBacked,
    vendorSignatureVerified: true,
    measurementPolicyVerified: true,
    tcbPolicyVerified: true,
    runtimeKeyBound: true,
    verifierKeyId: "verifier-ed25519-demo",
  }, key);
}

test("SEV-SNP verifier verdict flows from passport challenge through a signed delivery receipt", () => {
  const f = fixture();
  const verifierKeys = crypto.generateKeyPairSync("ed25519");
  const receiptKeys = crypto.generateKeyPairSync("ed25519");
  const challenge = A.buildChallenge({ passport: f.passport, contract: f.contract, runtimePublicKeyDigest: d("runtime-pubkey") });
  const verdict = signedVerdict(challenge, verifierKeys.privateKey);
  const checked = A.verifyVerifierVerdict(verdict, challenge, verifierKeys.publicKey);
  assert.equal(checked.ok, true); assert.equal(checked.code, "HARDWARE_ATTESTATION_VERIFIED");

  const passportMetadata = D.attachPassportReceiptMetadata({}, f.plan, f.profile, f.vm, f.contract, f.passport);
  const metadata = A.attachAttestationReceiptMetadata(passportMetadata, f.passport, f.contract, challenge, verdict, verifierKeys.publicKey);
  const hardwareEvidence = A.toReceiptHardwareEvidence(f.passport, f.contract, challenge, verdict, verifierKeys.publicKey);
  const signed = Receipt.createSignedDeliveryReceipt({
    executionId: "attested-exec", nodeId: f.node.id, outcome: "settled",
    artifacts: [{ role: "output", bytes: 1, digest: d("attested-output") }],
    capabilities: { findings: [] }, hardwareEvidence,
    startedAtMs: 1, finishedAtMs: 2, nonce: "attested-nonce", metadata,
    microvmExecuted: true,
  }, receiptKeys.privateKey, { publicKey: receiptKeys.publicKey, keyId: "holotrade-operator" });
  const verifiedReceipt = Receipt.verifyDeliveryReceipt(signed.envelope, receiptKeys.publicKey);
  assert.equal(verifiedReceipt.valid, true);
  assert.equal(verifiedReceipt.payload.runtime.hardwareAttested, true);
  assert.equal(verifiedReceipt.payload.runtime.microvmExecuted, true);
  assert.equal(verifiedReceipt.payload.metadata.w33MeasuredBoot.passportId, f.passport.passportId);
  assert.equal(verifiedReceipt.payload.metadata.w33MeasuredBoot.deploymentDigest, f.contract.deploymentDigest);
  assert.equal(verifiedReceipt.payload.metadata.w33MeasuredBoot.runtimePublicKeyDigest, d("runtime-pubkey"));
  assert.equal(verifiedReceipt.payload.hardwareEvidence.evidence[0].reasonCode, "SIGNED_NORMALIZED_EXTERNAL_VERIFIER_VERDICT");
});

test("TPM2 normalized verdict uses same fail-closed passport challenge", () => {
  const f = fixture(); const keys = crypto.generateKeyPairSync("ed25519");
  const challenge = A.buildChallenge({ passport: f.passport, contract: f.contract, runtimePublicKeyDigest: d("runtime-key") });
  const verdict = signedVerdict(challenge, keys.privateKey, A.PROVIDER.TPM2);
  assert.equal(A.verifyVerifierVerdict(verdict, challenge, keys.publicKey).ok, true);
  assert.equal(A.toReceiptHardwareEvidence(f.passport, f.contract, challenge, verdict, keys.publicKey).evidence[0].kind, "TPM_QUOTE");
});

test("tampered verifier verdict and wrong challenge are refused", () => {
  const f = fixture(); const keys = crypto.generateKeyPairSync("ed25519");
  const challenge = A.buildChallenge({ passport: f.passport, contract: f.contract, runtimePublicKeyDigest: d("runtime-key") });
  const verdict = signedVerdict(challenge, keys.privateKey);
  const tampered = { body: { ...verdict.body, launchMeasurement: d("attacker") }, signature: verdict.signature };
  assert.equal(A.verifyVerifierVerdict(tampered, challenge, keys.publicKey).code, "ATTESTATION_VERIFIER_SIGNATURE_INVALID");
  const other = { ...challenge, challengeDigest: d("other-challenge") };
  assert.equal(A.verifyVerifierVerdict(verdict, other, keys.publicKey).code, "ATTESTATION_CHALLENGE_MISMATCH");
});

test("software-only verifier evidence cannot be relabelled hardware-backed", () => {
  const f = fixture(); const keys = crypto.generateKeyPairSync("ed25519");
  const challenge = A.buildChallenge({ passport: f.passport, contract: f.contract, runtimePublicKeyDigest: d("runtime-key") });
  const verdict = signedVerdict(challenge, keys.privateKey, A.PROVIDER.SEV_SNP, false);
  assert.equal(A.verifyVerifierVerdict(verdict, challenge, keys.publicKey).code, "HARDWARE_BACKING_REQUIRED");
  assert.equal(A.verifyVerifierVerdict(verdict, challenge, keys.publicKey, { requireHardware: false }).code, "VERIFIER_CONTRACT_ONLY");
  assert.throws(() => A.toReceiptHardwareEvidence(f.passport, f.contract, challenge, verdict, keys.publicKey), /refusing unattested W33 receipt/);
});
