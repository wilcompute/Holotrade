// ======================================================================
// HOLOTRADE eight-way frontier integration suite
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

function build(seed = "frontier") {
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
  return { energy, fleet, pricing, exec };
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

function settle(exec, pe, projection, seconds = 2) {
  const created = pe.createPlan(projection, { requestedSeconds: seconds });
  const candidates = exec.place(created.plan, { limit: 8 });
  assert.ok(candidates.length > 0, `no placement for ${projection.id}`);
  const launch = exec.launch(created.plan, candidates[0].node);
  assert.equal(launch.ok, true, launch.reason || "launch failed");
  const receipts = exec.meter(seconds);
  const receipt = receipts.find((row) => row.planId === created.plan.id);
  assert.ok(receipt, `no settled receipt for ${projection.id}`);
  const emission = pe.emit(projection, created.plan, receipt);
  return { projection, plan: created.plan, receipt, emission, pe };
}

function certifiedTransition(seed = "certified", deterministic = true) {
  const { exec } = build(seed);
  register(exec, `cert:${seed}`);
  const pe = new P.ProjectionEngine(exec);
  const input = new P.ResourceRef({
    id: `input:${seed}`,
    kind: "dataset",
    role: "source",
    digest: `sha256:${"a".repeat(63)}${seed.length % 10}`,
  });
  const projection = new P.Projection({
    id: `projection:${seed}`,
    name: `projection ${seed}`,
    workloadId: "genomics",
    inputs: [input],
    evidenceRefs: [`cert:${seed}`],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
    metadata: { deterministic },
  });
  const t = settle(exec, pe, projection);
  const certificate = C.buildCertificate({ ...t, executionEngine: exec, projectionEngine: pe });
  return { exec, ...t, certificate };
}

test("local policy and capability sections glue uniquely and conflicts fail closed", () => {
  const good = G.glue([
    { id: "policy", values: { execution: { region: "US", network: "deny" }, trust: { tier: "verified" } } },
    { id: "capability", values: { execution: { region: "US" }, node: { accelerator: "gpu" } } },
    { id: "residency", values: { execution: { network: "deny" }, node: { accelerator: "gpu" } } },
  ], { requiredPaths: ["execution.region", "execution.network", "node.accelerator", "trust.tier"] });
  assert.equal(good.ok, true);
  assert.equal(good.unique, true);
  assert.equal(good.globalSection.execution.region, "US");
  assert.ok(good.overlaps.length >= 2);

  const bad = G.glue([
    { id: "a", values: { execution: { region: "US" } } },
    { id: "b", values: { execution: { region: "EU" } } },
  ]);
  assert.equal(bad.ok, false);
  assert.equal(bad.globalSection, null);
  assert.equal(bad.conflicts[0].path, "execution.region");
});

test("capability offers become auditable profile transitions instead of mutable flags", () => {
  const { exec } = build("capability");
  register(exec, "cert:profile");
  register(exec, "cert:vendor");
  const pe = new P.ProjectionEngine(exec);
  const profile = Cap.profileResource({
    nodeId: "NODE-CAP-1",
    hardwareKind: "gpu",
    capabilities: ["fp16"],
    evidenceRefs: ["cert:profile"],
  });
  const offer = new Cap.CapabilityOffer({
    id: "vendor:int8-v1",
    vendor: "Example Vendor",
    capabilities: ["int8", "sparse-kernels"],
    hardwareKinds: ["gpu"],
    evidenceRefs: ["cert:vendor"],
    price: 12.5,
  });
  const market = new Cap.CapabilityExchange([offer]);
  const listed = market.list(profile, ["int8"]);
  assert.equal(listed[0].complete, true);
  const engine = new Cap.CapabilityTransitionEngine(pe);
  const projection = engine.projection(profile, offer, { workloadId: "finetune" });
  const created = pe.createPlan(projection, { requestedSeconds: 1 });
  const candidates = exec.place(created.plan, { limit: 8 });
  assert.ok(candidates.length > 0);
  assert.equal(exec.launch(created.plan, candidates[0].node).ok, true);
  const receipt = exec.meter(1).find((row) => row.planId === created.plan.id);
  assert.ok(receipt);
  const emission = engine.emitProfile(projection, created.plan, receipt, profile, offer);
  assert.deepEqual(emission.output.metadata.capabilities, ["fp16", "int8", "sparse-kernels"]);
  assert.equal(emission.output.metadata.generation, 1);
  assert.equal(profile.metadata.generation, 0, "the old profile remains immutable");
});

test("Ed25519 envelopes authenticate canonical certificates and reject tampering", () => {
  const t = certifiedTransition("signed");
  const { publicKey, privateKey } = Sig.generateKeyPair();
  const envelope = Sig.sign(t.certificate, privateKey, publicKey);
  const verified = Sig.verify(envelope, t.certificate);
  assert.equal(verified.ok, true);
  assert.equal(envelope.securityMode, "ED25519_LOCAL_SIGNATURE");
  assert.equal(envelope.remotelyAttested, false);

  const changed = JSON.parse(JSON.stringify(t.certificate));
  changed.source.planId = "PLAN-TAMPERED";
  assert.equal(Sig.verify(envelope, changed).code, "PAYLOAD_MISMATCH");
  const broken = { ...envelope, payload: Buffer.from("{}", "utf8").toString("base64") };
  assert.equal(Sig.verify(broken).ok, false);
});

test("GoMicroVM adapter compiles fail-closed authority and distinguishes signatures from attestation", () => {
  const { exec } = build("mvm");
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: "projection:mvm",
    workloadId: "genomics",
    inputs: [new P.ResourceRef({ id: "input:mvm", digest: `sha256:${"c".repeat(64)}`, role: "source" })],
    grants: { network: [], services: ["object-store"], secrets: ["secret://tenant/key"] },
  });
  const { plan } = pe.createPlan(projection, { requestedSeconds: 3 });
  const contract = MVM.compile(plan, { invocation: { mode: "invoke", commandHash: "sha256:command", envKeyNames: ["TOKEN"] } });
  assert.equal(contract.admission.seccompTier, "minimal");
  assert.equal(contract.boundary.microvmLaunched, false);
  assert.equal(MVM.authoritySubset(contract, plan), true);
  const dry = MVM.dryRunRequest(contract);
  assert.equal(dry.mode, "preflight-only");
  assert.equal(JSON.stringify(dry).includes("secret://tenant/key"), false, "dry-run descriptor excludes secret refs/values");

  const signedOnly = MVM.receiptEvidence(contract, { id: "mvm-rx", contractDigest: contract.digest, exitCode: 0 }, {
    signatureVerified: true,
    attestationVerified: false,
  });
  assert.equal(signedOnly.status, E.STATUS.VERIFIED);
  assert.equal(signedOnly.evidenceClass, E.EVIDENCE_CLASS.EXTERNAL_VERIFIED);
  assert.equal(signedOnly.attested, false);

  const attested = MVM.receiptEvidence(contract, { id: "mvm-rx-2", contractDigest: contract.digest, exitCode: 0 }, {
    signatureVerified: true,
    attestationVerified: true,
  });
  assert.equal(attested.evidenceClass, E.EVIDENCE_CLASS.RUNTIME_ATTESTATION);
  assert.equal(attested.attested, true);
});

test("exact W33 spread frames are conflict-free and can shadow-price placement", () => {
  const catalogSpreads = W.spreads();
  assert.ok(catalogSpreads.length > 0);
  const first = catalogSpreads[0];
  assert.equal(first.length, 10);
  const covered = new Set(first.flatMap((lineId) => S.LINES[lineId]));
  assert.equal(covered.size, 40);

  const { exec } = build("scheduler");
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: "projection:scheduler",
    workloadId: "genomics",
    inputs: [
      new P.ResourceRef({ id: "sched:a", digest: `sha256:${"d".repeat(64)}`, role: "a" }),
      new P.ResourceRef({ id: "sched:b", digest: `sha256:${"e".repeat(64)}`, role: "b" }),
    ],
  });
  const { plan } = pe.createPlan(projection, { requestedSeconds: 3 });
  const ledger = new W.LineCongestionLedger();
  const ranked = W.rankPlacement(exec, plan, projection, ledger, { limit: 5, shadowUnit: 0.001 });
  assert.ok(ranked.length > 0);
  assert.ok(ranked.every((row) => row.w33.schedule.conflictFree));
  const winner = ranked[0];
  ledger.charge(winner.w33.demands, 10);
  const reranked = W.rankPlacement(exec, plan, projection, ledger, { limit: 5, shadowUnit: 0.001 });
  assert.ok(reranked.every((row) => row.scoreWithW33 >= row.score));
  assert.ok(ledger.snapshot().max >= 10);
});

test("ancestor correction quarantines every descendant without deleting history", () => {
  const { exec } = build("lineage");
  register(exec, "cert:lineage");
  const pe = new P.ProjectionEngine(exec);
  const firstProjection = new P.Projection({
    id: "projection:lineage-1",
    workloadId: "genomics",
    inputs: [new P.ResourceRef({ id: "raw:lineage", digest: `sha256:${"f".repeat(64)}`, role: "source" })],
    evidenceRefs: ["cert:lineage"], evidencePolicy: E.POLICY.VERIFIED,
  });
  const first = settle(exec, pe, firstProjection, 1);
  const secondProjection = new P.Projection({
    id: "projection:lineage-2",
    workloadId: "genomics",
    inputs: [first.emission.output],
    evidenceRefs: ["cert:lineage"], evidencePolicy: E.POLICY.VERIFIED,
  });
  const second = settle(exec, pe, secondProjection, 1);
  const graph = new L.ResourceLineage();
  graph.addEmission(first.emission);
  graph.addEmission(second.emission);
  assert.equal(graph.reusable(second.emission.output.digest), true);
  const q = graph.quarantineFrom(first.emission.output.digest, "ancestor evidence superseded", "cert:lineage");
  assert.ok(q.affected.includes(second.emission.output.digest));
  assert.equal(graph.reusable(first.emission.output.digest), false);
  assert.equal(graph.reusable(second.emission.output.digest), false);
  assert.equal(graph.nodes.has(second.emission.output.digest), true, "history remains present");
});

test("deterministic replay challenges confirm matches and emit correction-ready mismatch evidence", () => {
  const t = certifiedTransition("challenge");
  const pool = new Challenge.ChallengePool();
  const good = pool.open(t.certificate, { bounty: 5, deterministic: true, sponsor: "buyer" });
  assert.equal(pool.resolve(good, t.emission).match, true);

  const bad = pool.open(t.certificate, { bounty: 7, deterministic: true, sponsor: "buyer" });
  const replay = JSON.parse(JSON.stringify(t.emission));
  replay.output.metadata = { ...replay.output.metadata, corrupted: true };
  const result = pool.resolve(bad, replay);
  assert.equal(result.match, false);
  const correction = pool.correctionForMismatch(bad, { createdAt: 2 });
  assert.ok(correction.invalidates.includes("cert:challenge"));
  assert.equal(correction.metadata.correctionReady, true);
  assert.equal(pool.totalBounty, 0);
});

test("certified result cache avoids duplicate node-seconds only while evidence and lineage stay admissible", () => {
  const t = certifiedTransition("cache");
  const { publicKey, privateKey } = Sig.generateKeyPair();
  const signedEnvelope = Sig.sign(t.certificate, privateKey, publicKey);
  const graph = new L.ResourceLineage();
  graph.addEmission(t.emission);
  const cache = new Cache.CertifiedResultCache();
  cache.put({
    projection: t.projection,
    plan: t.plan,
    emission: t.emission,
    certificate: t.certificate,
    signedEnvelope,
    deterministic: true,
  });
  const hit = cache.lookup(t.projection, t.exec, { lineage: graph });
  assert.equal(hit.hit, true);
  assert.equal(hit.code, "CERTIFIED_REUSE");
  assert.equal(hit.nodeSecondsAvoided, t.receipt.nodeSeconds);

  register(t.exec, "cert:cache:v2", { supersedes: ["cert:cache"], createdAt: 2 });
  const stale = cache.lookup(t.projection, t.exec, { lineage: graph });
  assert.equal(stale.hit, false);
  assert.equal(stale.code, "EVIDENCE_STALE");

  const t2 = certifiedTransition("cache-lineage");
  const cache2 = new Cache.CertifiedResultCache();
  cache2.put({ projection: t2.projection, plan: t2.plan, emission: t2.emission, certificate: t2.certificate, deterministic: true });
  const graph2 = new L.ResourceLineage();
  graph2.addEmission(t2.emission);
  graph2.quarantineFrom(t2.emission.output.digest, "manual challenge quarantine");
  assert.equal(cache2.lookup(t2.projection, t2.exec, { lineage: graph2 }).code, "LINEAGE_QUARANTINED");
});
