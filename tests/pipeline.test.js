// ======================================================================
// HOLOTRADE end-to-end projection pipeline
//
// This is deliberately a real simulator integration test: actual seeded
// fleet -> pricing -> evidence admission -> placement -> launch -> meter ->
// settlement -> emission, twice. It proves compositional closure inside the
// prototype without claiming a physical microVM was launched.
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

function build() {
  const energy = new EnergyEngine(catalog.DATACENTERS, "projection-pipeline-energy");
  const fleet = new Fleet({
    datacenters: catalog.DATACENTERS,
    hardware: catalog.HARDWARE,
    workloads: catalog.WORKLOADS,
    operators: catalog.OPERATORS,
    size: 120,
    seed: "projection-pipeline-fleet",
  });
  const pricing = new PricingEngine(fleet, energy, catalog.WORKLOADS);
  const exec = new ExecutionEngine(fleet, pricing, energy, catalog.WORKLOADS);
  return { energy, fleet, pricing, exec };
}

function runStage(pe, exec, projection, seconds = 2) {
  const created = pe.createPlan(projection, { requestedSeconds: seconds });
  const candidates = exec.place(created.plan, { limit: 5 });
  assert.ok(candidates.length > 0, "evidence-approved projection has at least one serviceable placement");
  const launch = exec.launch(created.plan, candidates[0].node);
  assert.equal(launch.ok, true, launch.reason || "launch should be admitted");
  const receipts = exec.meter(seconds);
  assert.equal(receipts.length, 1, "the exact final interval settles the stage");
  const receipt = receipts[0];
  assert.equal(receipt.outcome, "settled");
  assert.equal(receipt.planDigest, created.plan.digest);
  assert.match(receipt.evidenceDigest, /^demo:/);
  assert.equal(receipt.cryptographicallyAttested, false);
  assert.match(receipt.evidenceEnvelope.statement.predicate.threeDigestBOM.identityDigest, /^demo:/);
  return {
    created,
    receipt,
    emission: pe.emit(projection, created.plan, receipt),
  };
}

test("a real simulated receipt can feed the next evidence-gated projection", () => {
  const { exec } = build();
  exec.registerEvidence({
    id: "cert:pipeline-v1",
    subject: "projection pipeline regression",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: "The projection compiler and simulator lifecycle are covered by this checked regression path.",
    source: { repository: "wilcompute/Holotrade", test: "tests/pipeline.test.js" },
    createdAt: 1,
  });

  const pe = new P.ProjectionEngine(exec);
  const raw = new P.ResourceRef({
    id: "dataset:raw-genomics",
    role: "source",
    kind: "dataset",
    digest: "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    metadata: { classification: "synthetic-demo-input" },
  });

  const normalize = new P.Projection({
    id: "projection:normalize-genomics",
    name: "normalize genomics shard",
    service: "data-transform",
    workloadId: "genomics",
    inputs: [raw],
    grants: { network: [], services: [], secrets: [] },
    evidenceRefs: ["cert:pipeline-v1"],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
    metadata: { stage: 1 },
  });
  const stage1 = runStage(pe, exec, normalize);
  assert.match(stage1.emission.output.address, /^uor:[0-9a-f]{16}$/);
  assert.equal(stage1.emission.output.metadata.projectionDigest, normalize.digest);

  const analyze = new P.Projection({
    id: "projection:analyze-genomics",
    name: "analyze normalized genomics shard",
    service: "analysis",
    workloadId: "genomics",
    inputs: [stage1.emission.output],
    grants: { network: [], services: [], secrets: [] },
    evidenceRefs: ["cert:pipeline-v1"],
    evidencePolicy: E.POLICY.VERIFIED,
    outputKind: "dataset",
    metadata: { stage: 2 },
  });
  const stage2 = runStage(pe, exec, analyze);

  const stage2Artifacts = new Set(stage2.created.plan.artifacts.map((a) => a.digest));
  assert.ok(stage2Artifacts.has(stage1.emission.output.digest),
    "stage 2 plan pins the exact emitted state from stage 1");
  assert.equal(stage2.emission.parents[0].digest, stage1.emission.output.digest);
  assert.notEqual(stage2.emission.output.digest, stage1.emission.output.digest);

  // The topology still participates in the real placement path. This assertion
  // merely checks the named node resolves to one of the exact 40 point labels;
  // it does not promote the simulator route to a physical-network claim.
  const node = exec.fleet.get(stage2.receipt.nodeId);
  assert.ok(node);
  assert.ok(Number.isInteger(node.cellPoint) && node.cellPoint >= 0 && node.cellPoint < S.POINTS.length);
});
