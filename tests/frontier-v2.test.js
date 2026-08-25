const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
global.window = global;
const S = require(path.join(root, "js/substrate.js"));
const catalog = require(path.join(root, "data/catalog.js"));
const EnergyEngine = require(path.join(root, "js/energy.js"));
const { Fleet } = require(path.join(root, "js/fleet.js"));
const { PricingEngine } = require(path.join(root, "js/pricing.js"));
const E = require(path.join(root, "js/evidence.js"));
require(path.join(root, "js/uor.js"));
const { ExecutionEngine } = require(path.join(root, "js/execution.js"));
require(path.join(root, "js/execution-evidence.js"));
const P = require(path.join(root, "js/projection.js"));
const C = require(path.join(root, "js/w33-transition-certificate.js"));
const G = require(path.join(root, "js/gluing.js"));
const Cap = require(path.join(root, "js/capability-market.js"));
const Sig = require(path.join(root, "js/signing.js"));
const MVM = require(path.join(root, "js/gomicrovm-adapter.js"));
const W = require(path.join(root, "js/w33-scheduler.js"));
const L = require(path.join(root, "js/lineage.js"));
const Challenge = require(path.join(root, "js/challenge-market.js"));
const Cache = require(path.join(root, "js/certified-cache.js"));

function build(seed) {
  const energy = new EnergyEngine(catalog.DATACENTERS, `${seed}-energy`);
  const fleet = new Fleet({
    datacenters: catalog.DATACENTERS,
    hardware: catalog.HARDWARE,
    workloads: catalog.WORKLOADS,
    operators: catalog.OPERATORS,
    size: 120,
    seed: `${seed}-fleet`,
  });
  const pricing = new PricingEngine(fleet, energy, catalog.WORKLOADS);
  return new ExecutionEngine(fleet, pricing, energy, catalog.WORKLOADS);
}

function register(exec, id, extra = {}) {
  return exec.registerEvidence({
    id,
    subject: id,
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: `Regression certificate ${id}`,
    createdAt: extra.createdAt || 1,
    ...extra,
  });
}

function settle(exec, pe, projection, seconds = 1, outputSpec = {}) {
  const created = pe.createPlan(projection, { requestedSeconds: seconds });
  const candidate = exec.place(created.plan, { limit: 8 })[0];
  assert.ok(candidate, `no placement for ${projection.id}`);
  assert.equal(exec.launch(created.plan, candidate.node).ok, true);
  const receipt = exec.meter(seconds).find((row) => row.planId === created.plan.id);
  assert.ok(receipt);
  const emission = pe.emit(projection, created.plan, receipt, outputSpec);
  const certificate = C.buildCertificate({ projection, plan: created.plan, receipt, emission, executionEngine: exec, projectionEngine: pe });
  return { projection, plan: created.plan, receipt, emission, certificate, pe };
}

function certified(seed, resultDigest = null) {
  const exec = build(seed);
  register(exec, `cert:${seed}`);
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: `projection:${seed}`,
    workloadId: "genomics",
    inputs: [new P.ResourceRef({
      id: `input:${seed}`,
      role: "source",
      kind: "dataset",
      digest: `sha256:${seed.charCodeAt(0).toString(16).padStart(2, "0").repeat(32)}`,
    })],
    evidenceRefs: [`cert:${seed}`],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
    metadata: { deterministic: true },
  });
  const outputSpec = resultDigest ? { metadata: { resultDigest } } : {};
  return { exec, ...settle(exec, pe, projection, 1, outputSpec) };
}

test("evidence-aware gluing separates structural truth from current admissibility", () => {
  const exec = build("glue-v2");
  register(exec, "cert:glue-v1");
  const sections = [
    { id: "policy", values: { execution: { region: "US", network: "deny" } }, evidenceRefs: ["cert:glue-v1"] },
    { id: "capability", values: { execution: { region: "US" }, node: { accelerator: "gpu" } }, evidenceRefs: ["cert:glue-v1"] },
  ];
  const first = G.admit(sections, exec.evidenceLedger, { requiredPaths: ["execution.region", "execution.network", "node.accelerator"], evidencePolicy: E.POLICY.VERIFIED });
  assert.equal(first.ok, true);
  register(exec, "cert:glue-v2", { supersedes: ["cert:glue-v1"], createdAt: 2 });
  const stale = G.admit(sections, exec.evidenceLedger, { requiredPaths: ["execution.region", "execution.network", "node.accelerator"], evidencePolicy: E.POLICY.VERIFIED });
  assert.equal(stale.structural.ok, true);
  assert.equal(stale.ok, false);
  assert.ok(stale.blockers.some((b) => b.code === "SUPERSEDED_EVIDENCE"));
});

test("capability market selects the cheapest exact bundle and emits one atomic profile generation", () => {
  const exec = build("cap-v2");
  register(exec, "cert:profile"); register(exec, "cert:a"); register(exec, "cert:b");
  const profile = Cap.profileResource({ nodeId: "NODE-CAP", hardwareKind: "gpu", capabilities: ["fp16"], evidenceRefs: ["cert:profile"] });
  const offers = [
    new Cap.CapabilityOffer({ id: "combo", vendor: "A", capabilities: ["int8", "sparse"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:a"], price: 8 }),
    new Cap.CapabilityOffer({ id: "int8", vendor: "B", capabilities: ["int8"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:b"], price: 2 }),
    new Cap.CapabilityOffer({ id: "sparse", vendor: "B", capabilities: ["sparse"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:b"], price: 3 }),
  ];
  const best = new Cap.CapabilityExchange(offers).bestBundle(profile, ["int8", "sparse"]);
  assert.deepEqual(best.offerIds, ["int8", "sparse"]);
  assert.equal(best.totalPrice, 5);
  const pe = new P.ProjectionEngine(exec);
  const engine = new Cap.CapabilityTransitionEngine(pe);
  const projection = engine.bundleProjection(profile, best.offers, { workloadId: "finetune" });
  const created = pe.createPlan(projection, { requestedSeconds: 1 });
  const node = exec.place(created.plan, { limit: 8 })[0].node;
  assert.equal(exec.launch(created.plan, node).ok, true);
  const receipt = exec.meter(1).find((row) => row.planId === created.plan.id);
  const emission = engine.emitBundleProfile(projection, created.plan, receipt, profile, best.offers);
  assert.deepEqual(emission.output.metadata.capabilities, ["fp16", "int8", "sparse"]);
  assert.equal(emission.output.metadata.generation, 1);
  assert.equal(emission.output.metadata.transitionPrice, 5);
});

test("strict DSSE threshold verification uses external trusted keys; keyid remains a hint", () => {
  const t = certified("threshold-v2");
  const k1 = Sig.generateKeyPair(), k2 = Sig.generateKeyPair(), k3 = Sig.generateKeyPair();
  const envelope = Sig.signDSSE(t.certificate, [k1, k2]);
  assert.deepEqual(Object.keys(envelope).sort(), ["payload", "payloadType", "signatures"]);
  const trusted = new Map([["a", k1.publicKey], ["b", k2.publicKey], ["c", k3.publicKey]]);
  assert.equal(Sig.verifyThreshold(envelope, trusted, { threshold: 2, expectedPayload: t.certificate, expectedPayloadType: Sig.PAYLOAD_TYPE }).ok, true);
  const forgedHint = JSON.parse(JSON.stringify(envelope));
  forgedHint.signatures[0].keyid = Sig.keyId(k3.publicKey);
  assert.equal(Sig.verifyThreshold(forgedHint, trusted, { threshold: 2, expectedPayload: t.certificate }).ok, true);
  assert.equal(Sig.verifyThreshold(envelope, new Map([["one", k1.publicKey]]), { threshold: 2 }).code, "INSUFFICIENT_TRUSTED_KEYS");
});

test("GoMicroVM reconciliation refuses weakened seccomp or a guest network device", () => {
  const exec = build("mvm-v2");
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({ id: "projection:mvm-v2", workloadId: "genomics", inputs: [new P.ResourceRef({ id: "in:mvm", role: "source", digest: `sha256:${"4".repeat(64)}` })], grants: { network: [], services: ["object-store"], secrets: [] } });
  const { plan } = pe.createPlan(projection, { requestedSeconds: 2 });
  const contract = MVM.compile(plan);
  const snapshot = {
    contractDigest: contract.digest,
    nonce: contract.admission.nonce,
    artifacts: contract.artifacts,
    authority: contract.authority,
    policyRefs: contract.admission.policyRefs,
    seccompTier: contract.admission.seccompTier,
    guestNetworkDevicePresent: false,
    auditChainSigned: true,
    rootfsSealed: true,
  };
  assert.equal(MVM.reconcileAdmissionSnapshot(contract, snapshot, { now: contract.admission.validFrom }).ok, true);
  const bad = MVM.reconcileAdmissionSnapshot(contract, { ...snapshot, seccompTier: "unrestricted", guestNetworkDevicePresent: true }, { now: contract.admission.validFrom });
  assert.equal(bad.ok, false);
  assert.ok(bad.blockers.some((b) => b.code === "SECCOMP_WEAKENED"));
  assert.ok(bad.blockers.some((b) => b.code === "GUEST_NETWORK_DEVICE_PRESENT_OR_UNKNOWN"));
});

test("W33 scheduler reproduces the complete 36-spread / nine-occurrence theorem", () => {
  assert.equal(W.spreads().length, 36);
  const cert = W.spreadCertificate(0);
  assert.equal(cert.valid, true);
  assert.equal(cert.anchorLines.length, 4);
  assert.deepEqual([...new Set(cert.lineOccurrenceDistribution)], [9]);
  assert.deepEqual([...new Set(Object.values(cert.sectorCounts))], [9]);
  assert.ok(Object.values(cert.theorem).every(Boolean));
  assert.equal(new Set(W.spreads()[0].flatMap((lineId) => S.LINES[lineId])).size, 40);
});

test("lineage refresh automatically quarantines stale certified ancestors and descendants", () => {
  const first = certified("lineage-v2");
  const secondProjection = new P.Projection({ id: "projection:lineage-child", workloadId: "genomics", inputs: [first.emission.output], evidenceRefs: ["cert:lineage-v2"], evidencePolicy: E.POLICY.VERIFIED });
  const second = settle(first.exec, first.pe, secondProjection);
  const graph = new L.ResourceLineage();
  graph.addCertifiedEmission(first.emission, first.certificate);
  graph.addCertifiedEmission(second.emission, second.certificate);
  register(first.exec, "cert:lineage-v2:new", { supersedes: ["cert:lineage-v2"], createdAt: 2 });
  const refresh = graph.refreshEvidence(first.exec);
  assert.ok(refresh.staleRoots.includes(first.emission.output.digest));
  assert.ok(refresh.affected.includes(second.emission.output.digest));
  assert.equal(graph.reusable(second.emission.output.digest), false);
});

test("certified replay quorum compares semantic result identity, not execution provenance", () => {
  const resultA = `sha256:${"a".repeat(64)}`;
  const resultB = `sha256:${"b".repeat(64)}`;
  const exec = build("quorum-v2");
  register(exec, "cert:quorum-v2");
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: "projection:quorum-v2",
    workloadId: "genomics",
    inputs: [new P.ResourceRef({ id: "input:quorum-v2", role: "source", digest: `sha256:${"9".repeat(64)}` })],
    evidenceRefs: ["cert:quorum-v2"], evidencePolicy: E.POLICY.VERIFIED,
    metadata: { deterministic: true },
  });
  const original = settle(exec, pe, projection, 1, { metadata: { resultDigest: resultA } });
  const replay1 = settle(exec, pe, projection, 1, { metadata: { resultDigest: resultA } });
  const replay2 = settle(exec, pe, projection, 1, { metadata: { resultDigest: resultA } });
  assert.notEqual(original.certificate.element.digest, replay1.certificate.element.digest, "independent provenance differs");

  const pool = new Challenge.ChallengePool();
  const challenge = pool.open(original.certificate, { emission: original.emission, deterministic: true, bounty: 9 });
  const confirmed = pool.resolveQuorum(challenge, [
    { certificate: replay1.certificate, emission: replay1.emission },
    { certificate: replay2.certificate, emission: replay2.emission },
  ], { minimum: 2 });
  assert.equal(confirmed.match, true);

  const mismatchReplay = settle(exec, pe, projection, 1, { metadata: { resultDigest: resultB } });
  const challenge2 = pool.open(original.certificate, { emission: original.emission, deterministic: true, bounty: 4 });
  const disagreed = pool.resolveQuorum(challenge2, [
    { certificate: replay1.certificate, emission: replay1.emission },
    { certificate: mismatchReplay.certificate, emission: mismatchReplay.emission },
  ], { minimum: 2 });
  assert.equal(disagreed.match, false);
  const correction = pool.correctionForMismatch(challenge2, { createdAt: 3 });
  assert.equal(correction.metadata.correctionReady, true);
  assert.equal(correction.metadata.semanticResultIdentityCompared, true);
});

test("certified cache emits a threshold-trusted reuse receipt without recomputation", () => {
  const t = certified("cache-v2");
  const k1 = Sig.generateKeyPair(), k2 = Sig.generateKeyPair();
  const dsseEnvelope = Sig.signDSSE(t.certificate, [k1, k2]);
  const graph = new L.ResourceLineage();
  graph.addCertifiedEmission(t.emission, t.certificate);
  const cache = new Cache.CertifiedResultCache();
  cache.put({ projection: t.projection, plan: t.plan, emission: t.emission, certificate: t.certificate, dsseEnvelope, deterministic: true });
  const reused = cache.reuseReceipt(t.projection, t.exec, {
    lineage: graph,
    trustedKeys: new Map([["a", k1.publicKey], ["b", k2.publicKey]]),
    signatureThreshold: 2,
  });
  assert.equal(reused.hit, true);
  assert.equal(reused.reuseReceipt.recomputationPerformed, false);
  assert.equal(reused.reuseReceipt.signatureVerified, true);
  assert.equal(reused.reuseReceipt.nodeSecondsAvoided, t.receipt.nodeSeconds);
  assert.equal(cache.stats().nodeSecondsAvoidedRecorded, t.receipt.nodeSeconds);
});
