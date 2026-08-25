// ======================================================================
// HOLOTRADE W33/UOR transition certificate integration tests
// ======================================================================

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
global.window = global;
require(path.join(root, "js/substrate.js"));
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

function build() {
  const energy = new EnergyEngine(catalog.DATACENTERS, "w33-cert-energy");
  const fleet = new Fleet({
    datacenters: catalog.DATACENTERS,
    hardware: catalog.HARDWARE,
    workloads: catalog.WORKLOADS,
    operators: catalog.OPERATORS,
    size: 120,
    seed: "w33-cert-fleet",
  });
  const pricing = new PricingEngine(fleet, energy, catalog.WORKLOADS);
  const exec = new ExecutionEngine(fleet, pricing, energy, catalog.WORKLOADS);
  return { exec };
}

function settleTransition(exec) {
  exec.registerEvidence({
    id: "cert:w33-transition-v1",
    subject: "W33 transition regression",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: "The transition certificate path is covered by the checked HoloTrade regression suite.",
    source: { repository: "wilcompute/Holotrade", test: "tests/w33-transition-certificate.test.js" },
    createdAt: 1,
  });
  const pe = new P.ProjectionEngine(exec);
  const projection = new P.Projection({
    id: "projection:w33-certified",
    name: "certified genomics transform",
    service: "data-transform",
    workloadId: "genomics",
    inputs: [
      new P.ResourceRef({
        id: "dataset:alpha",
        role: "source",
        kind: "dataset",
        digest: "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      }),
      new P.ResourceRef({
        id: "model:beta",
        role: "weights",
        kind: "model",
        digest: "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      }),
    ],
    grants: { network: [], services: [], secrets: [] },
    evidenceRefs: ["cert:w33-transition-v1"],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
  });
  const created = pe.createPlan(projection, { requestedSeconds: 2 });
  const candidates = exec.place(created.plan, { limit: 5 });
  assert.ok(candidates.length > 0);
  const launched = exec.launch(created.plan, candidates[0].node);
  assert.equal(launched.ok, true, launched.reason || "launch should succeed");
  const receipts = exec.meter(2);
  assert.equal(receipts.length, 1);
  const receipt = receipts[0];
  const emission = pe.emit(projection, created.plan, receipt, { metadata: { format: "parquet" } });
  return { pe, projection, plan: created.plan, receipt, emission };
}

test("settled emissions receive real SHA-256 content addresses and exact W33 route witnesses", () => {
  const { exec } = build();
  const t = settleTransition(exec);
  const cert = C.buildCertificate({
    ...t,
    executionEngine: exec,
    projectionEngine: t.pe,
  });

  assert.equal(cert.status, "PASS");
  assert.equal(cert.certificate.valid, true);
  assert.equal(cert.uor_alignment.nativeCertification, false);
  assert.match(cert.element.digest, /^sha256:[0-9a-f]{64}$/);
  assert.match(cert.certificateDigest, /^sha256:[0-9a-f]{64}$/);
  assert.equal(cert.element.digest, C.sha256Digest(t.emission));
  assert.equal(cert.transport_partition.complete, true);
  assert.ok(cert.trace.transition_steps.length === t.projection.inputs.length + 1);
  assert.ok(cert.trace.transition_steps.every((step) => step.hops <= 2));
  assert.ok(cert.trace.transition_steps
    .filter((step) => step.hops === 2)
    .every((step) => step.relayAlternates === 3), "mu=4 gives one selected relay plus three alternates");
  assert.equal(cert.proof.historical_evidence_admission.ok, true);
  assert.equal(cert.proof.current_evidence_admissibility_at_issue.ok, true);
  assert.deepEqual(C.validateShape(cert), { conforms: true, violations: [] });
});

test("later evidence correction blocks reuse without changing the historical transition element", () => {
  const { exec } = build();
  const t = settleTransition(exec);
  const before = C.buildCertificate({
    ...t,
    executionEngine: exec,
    projectionEngine: t.pe,
  });
  assert.equal(C.reevaluateEvidence(before, exec, t.plan).reusableNow, true);

  exec.registerEvidence({
    id: "cert:w33-transition-v2",
    subject: "W33 transition regression correction",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: "A later control superseded the earlier execution-eligibility certificate.",
    supersedes: ["cert:w33-transition-v1"],
    source: { repository: "wilcompute/Holotrade", reason: "correction-semantics-regression" },
    createdAt: 2,
  });

  const current = C.reevaluateEvidence(before, exec, t.plan);
  assert.equal(current.historicalAdmission.ok, true, "settlement-time admission stays part of history");
  assert.equal(current.current.ok, false, "the same evidence ref is no longer admissible now");
  assert.equal(current.reusableNow, false);
  assert.ok(current.current.blockers.some((b) => b.code === "SUPERSEDED_EVIDENCE"));

  const after = C.buildCertificate({
    ...t,
    executionEngine: exec,
    projectionEngine: t.pe,
  });
  assert.equal(after.status, "PASS", "a later correction does not retroactively falsify the settled transition");
  assert.equal(after.element.digest, before.element.digest,
    "the SHA-256 content address of the historical emission is immutable");
  assert.equal(after.proof.historical_evidence_admission.digest, before.proof.historical_evidence_admission.digest);
  assert.equal(after.proof.current_evidence_admissibility_at_issue.ok, false);
  assert.notEqual(after.certificateDigest, before.certificateDigest,
    "a newly issued wrapper records the new current-admissibility snapshot without rewriting the old certificate");
});

test("certificate shape validation detects proof or digest tampering", () => {
  const { exec } = build();
  const t = settleTransition(exec);
  const cert = C.buildCertificate({ ...t, executionEngine: exec, projectionEngine: t.pe });
  const tampered = JSON.parse(JSON.stringify(cert));
  tampered.trace.transition_steps[0].hops = 9;
  const result = C.validateShape(tampered);
  assert.equal(result.conforms, false);
  assert.ok(result.violations.includes("certificateDigest mismatch"));
});
