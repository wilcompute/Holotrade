// ======================================================================
// HOLOTRADE second-pass eight-way frontier integration suite
// ======================================================================

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

function build(seed = "frontier-v2") {
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
  const exec = new ExecutionEngine(fleet, pricing, energy, catalog.WORKLOADS);
  return { exec };
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

function settle(exec, pe, projection, seconds = 1) {
  const created = pe.createPlan(projection, { requestedSeconds: seconds });
  const candidates = exec.place(created.plan, { limit: 8 });
  assert.ok(candidates.length > 0, `no placement for ${projection.id}`);
  assert.equal(exec.launch(created.plan, candidates[0].node).ok, true);
  const receipt = exec.meter(seconds).find((row) => row.planId === created.plan.id);
  assert.ok(receipt);
  const emission = pe.emit(projection, created.plan, receipt);
  return { projection, plan: created.plan, receipt, emission, pe };
}

function certifiedTransition(seed = "v2") {
  const { exec } = build(seed);
  register(exec, `cert:${seed}`);
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: `projection:${seed}`,
    workloadId: "genomics",
    inputs: [new P.ResourceRef({
      id: `input:${seed}`,
      kind: "dataset",
      role: "source",
      digest: `sha256:${seed.charCodeAt(0).toString(16).padStart(2, "0").repeat(32)}`,
    })],
    evidenceRefs: [`cert:${seed}`],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
    metadata: { deterministic: true },
  });
  const t = settle(exec, pe, projection);
  const certificate = C.buildCertificate({ ...t, executionEngine: exec, projectionEngine: pe });
  return { exec, ...t, certificate };
}

test("evidence-aware gluing refuses a structurally valid global section after supporting evidence is superseded", () => {
  const { exec } = build("glue-v2");
  register(exec, "cert:policy-v1");
  const sections = [
    { id: "policy", values: { execution: { region: "US", network: "deny" } }, evidenceRefs: ["cert:policy-v1"] },
    { id: "cap", values: { execution: { region: "US" }, node: { accelerator: "gpu" } }, evidenceRefs: ["cert:policy-v1"] },
  ];
  const admitted = G.admit(sections, exec.evidenceLedger, {
    requiredPaths: ["execution.region", "execution.network", "node.accelerator"],
    evidencePolicy: E.POLICY.VERIFIED,
  });
  assert.equal(admitted.ok, true);
  assert.equal(admitted.structural.unique, true);

  register(exec, "cert:policy-v2", { supersedes: ["cert:policy-v1"], createdAt: 2 });
  const stale = G.admit(sections, exec.evidenceLedger, {
    requiredPaths: ["execution.region", "execution.network", "node.accelerator"],
    evidencePolicy: E.POLICY.VERIFIED,
  });
  assert.equal(stale.structural.ok, true, "structural theorem remains true");
  assert.equal(stale.ok, false, "current epistemic admission changes independently");
  assert.ok(stale.blockers.some((b) => b.code === "SUPERSEDED_EVIDENCE"));
});

test("capability exchange finds a minimum-price exact bundle and applies it atomically", () => {
  const { exec } = build("cap-bundle");
  register(exec, "cert:profile");
  register(exec, "cert:vendor-a");
  register(exec, "cert:vendor-b");
  const profile = Cap.profileResource({
    nodeId: "NODE-BUNDLE",
    hardwareKind: "gpu",
    capabilities: ["fp16"],
    evidenceRefs: ["cert:profile"],
  });
  const offers = [
    new Cap.CapabilityOffer({ id: "combo", vendor: "A", capabilities: ["int8", "sparse"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:vendor-a"], price: 8 }),
    new Cap.CapabilityOffer({ id: "int8-only", vendor: "B", capabilities: ["int8"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:vendor-b"], price: 2 }),
    new Cap.CapabilityOffer({ id: "sparse-only", vendor: "B", capabilities: ["sparse"], hardwareKinds: ["gpu"], evidenceRefs: ["cert:vendor-b"], price: 3 }),
  ];
  const market = new Cap.CapabilityExchange(offers);
  const best = market.bestBundle(profile, ["int8", "sparse"]);
  assert.equal(best.complete, true);
  assert.deepEqual(best.offerIds, ["int8-only", "sparse-only"]);
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
  assert.equal(emission.output.metadata.transitionPrice, 5);
  assert.equal(emission.output.metadata.generation, 1);
});

test("strict DSSE threshold verification trusts caller-supplied keys rather than keyid hints", () => {
  const t = certifiedTransition("threshold");
  const k1 = Sig.generateKeyPair();
  const k2 = Sig.generateKeyPair();
  const k3 = Sig.generateKeyPair();
  const envelope = Sig.signDSSE(t.certificate, [k1, k2]);
  assert.deepEqual(Object.keys(envelope).sort(), ["payload", "payloadType", "signatures"]);
  const trusted = new Map([
    ["operator-a", k1.publicKey],
    ["operator-b", k2.publicKey],
    ["outsider", k3.publicKey],
  ]);
  const ok = Sig.verifyThreshold(envelope, trusted, {
    threshold: 2,
    expectedPayload: t.certificate,
    expectedPayloadType: Sig.PAYLOAD_TYPE,
  });
  assert.equal(ok.ok, true);
  assert.equal(ok.verifiedCount, 2);

  const forgedHint = JSON.parse(JSON.stringify(envelope));
  forgedHint.signatures[0].keyid = Sig.keyId(k3.publicKey);
  const stillOk = Sig.verifyThreshold(forgedHint, trusted, { threshold: 2, expectedPayload: t.certificate });
  assert.equal(stillOk.ok, true, "keyid is only a hint; cryptographic verification finds the actual trusted key");
  assert.equal(Sig.verifyThreshold(envelope, new Map([["only-one", k1.publicKey]]), { threshold: 2 }).code, "INSUFFICIENT_TRUSTED_KEYS");
});

test("GoMicroVM admission reconciliation fails closed on widened runtime posture", () => {
  const { exec } = build("mvm-v2");
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: "projection:mvm-v2",
    workloadId: "genomics",
    inputs: [new P.ResourceRef({ id: "input:mvm-v2", digest: `sha256:${"4".repeat(64)}`, role: "source" })],
    grants: { network: [], services: ["object-store"], secrets: [] },
  });
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
  const good = MVM.reconcileAdmissionSnapshot(contract, snapshot, { now: contract.admission.validFrom });
  assert.equal(good.ok, true);
  assert.equal(good.remoteExecutionVerified, false);

  const widened = MVM.reconcileAdmissionSnapshot(contract, {
    ...snapshot,
    guestNetworkDevicePresent: true,
    seccompTier: "unrestricted",
  }, { now: contract.admission.validFrom });
  assert.equal(widened.ok, false);
  assert.ok(widened.blockers.some((b) => b.code === "GUEST_NETWORK_DEVICE_PRESENT_OR_UNKNOWN"));
  assert.ok(widened.blockers.some((b) => b.code === "SECCOMP_WEAKENED"));
});

test("W33 scheduler closes the exact 36-spread and nine-occurrence census", () => {
  const spreads = W.spreads();
  assert.equal(spreads.length, 36);
  const cert = W.spreadCertificate(0);
  assert.equal(cert.valid, true);
  assert.equal(cert.spreadCount, 36);
  assert.equal(cert.anchorLines.length, 4);
  assert.deepEqual([...new Set(cert.lineOccurrenceDistribution)], [9]);
  assert.deepEqual([...new Set(Object.values(cert.sectorCounts))], [9]);
  assert.ok(Object.values(cert.theorem).every(Boolean));
});

test("certified lineage automatically quarantines descendants when current evidence turns stale", () => {
  const first = certifiedTransition("lineage-v2");
  const secondProjection = new P.Projection({
    id: "projection:lineage-v2-child",
    workloadId: "genomics",
    inputs: [first.emission.output],
    evidenceRefs: ["cert:lineage-v2"],
    evidencePolicy: E.POLICY.VERIFIED,
  });
  const second = settle(first.exec, first.pe, secondProjection);
  const secondCertificate = C.buildCertificate({ ...second, executionEngine: first.exec, projectionEngine: first.pe });
  const graph = new L.ResourceLineage();
  graph.addCertifiedEmission(first.emission, first.certificate);
  graph.addCertifiedEmission(second.emission, secondCertificate);
  assert.equal(graph.reusable(second.emission.output.digest), true);

  register(first.exec, "cert:lineage-v2:new", { supersedes: ["cert:lineage-v2"], createdAt: 2 });
  const refresh = graph.refreshEvidence(first.exec);
  assert.ok(refresh.staleRoots.includes(first.emission.output.digest));
  assert.ok(refresh.affected.includes(second.emission.output.digest));
  assert.equal(graph.reusable(second.emission.output.digest), false);
});

test("certified replay quorum requires the same projection digest and conservatively flags any mismatch", () => {
  const original = certifiedTransition("quorum");
  const pool = new Challenge.ChallengePool();
  const challenge = pool.open(original.certificate, { deterministic: true, bounty: 9, sponsor: "buyer" });

  // A second certificate wrapper over the same settled transition is a distinct
  // certificate digest only if its current-admissibility snapshot changes, so
  // create two replay wrappers manually from independent certificate objects.
  const replay1 = JSON.parse(JSON.stringify(original.certificate));
  replay1.certificateDigest = C.sha256Digest((() => { const b = { ...replay1 }; delete b.certificateDigest; return b; })());
  const replay2 = JSON.parse(JSON.stringify(original.certificate));
  replay2.certificate.currentAdmissibilityAtIssue = original.certificate.certificate.currentAdmissibilityAtIssue;
  replay2.proof.current_evidence_admissibility_at_issue = { ...replay2.proof.current_evidence_admissibility_at_issue, digest: "demo:alternate-wrapper" };
  replay2.certificateDigest = C.sha256Digest((() => { const b = { ...replay2 }; delete b.certificateDigest; return b; })());
  assert.equal(C.validateShape(replay1).conforms, true);
  assert.equal(C.validateShape(replay2).conforms, true);
  const confirmed = pool.resolveQuorum(challenge, [replay1, replay2], { minimum: 2 });
  assert.equal(confirmed.match, true);
  assert.equal(confirmed.distinctReplays, 2);

  const challenge2 = pool.open(original.certificate, { deterministic: true, bounty: 4 });
  const mismatch = JSON.parse(JSON.stringify(replay2));
  mismatch.element.digest = `sha256:${"0".repeat(64)}`;
  mismatch.element.canonicalBytesSha256 = "0".repeat(64);
  mismatch.certificateDigest = C.sha256Digest((() => { const b = { ...mismatch }; delete b.certificateDigest; return b; })());
  // Shape must remain valid for a certified disagreement; the wrapper's own
  // digest is self-consistent even though its element differs from original.
  assert.equal(C.validateShape(mismatch).conforms, true);
  const disagreed = pool.resolveQuorum(challenge2, [replay1, mismatch], { minimum: 2 });
  assert.equal(disagreed.match, false);
  const correction = pool.correctionForMismatch(challenge2, { createdAt: 3 });
  assert.equal(correction.metadata.correctionReady, true);
});

test("certified cache issues an auditable reuse receipt under threshold trust and records avoided node-seconds", () => {
  const t = certifiedTransition("cache-v2");
  const k1 = Sig.generateKeyPair();
  const k2 = Sig.generateKeyPair();
  const dsseEnvelope = Sig.signDSSE(t.certificate, [k1, k2]);
  const graph = new L.ResourceLineage();
  graph.addCertifiedEmission(t.emission, t.certificate);
  const cache = new Cache.CertifiedResultCache();
  cache.put({
    projection: t.projection,
    plan: t.plan,
    emission: t.emission,
    certificate: t.certificate,
    dsseEnvelope,
    deterministic: true,
  });
  const trusted = new Map([["k1", k1.publicKey], ["k2", k2.publicKey]]);
  const reused = cache.reuseReceipt(t.projection, t.exec, {
    lineage: graph,
    trustedKeys: trusted,
    signatureThreshold: 2,
  });
  assert.equal(reused.hit, true);
  assert.equal(reused.reuseReceipt.recomputationPerformed, false);
  assert.equal(reused.reuseReceipt.signatureVerified, true);
  assert.equal(reused.reuseReceipt.nodeSecondsAvoided, t.receipt.nodeSeconds);
  assert.equal(cache.stats().nodeSecondsAvoidedRecorded, t.receipt.nodeSeconds);
});
