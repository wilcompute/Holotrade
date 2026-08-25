// ======================================================================
// HOLOTRADE projection -> execution -> emission regression suite
// ======================================================================

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
require(path.join(root, "js/substrate.js"));
const E = require(path.join(root, "js/evidence.js"));
require(path.join(root, "js/uor.js"));
const X = require(path.join(root, "js/execution.js"));
require(path.join(root, "js/execution-evidence.js"));
const P = require(path.join(root, "js/projection.js"));

function engine() {
  return new X.ExecutionEngine(
    { listedNodes: () => [], get: () => null },
    { quote: () => ({ serviceable: false, price: null }) },
    { datacenters: [] },
    [{ id: "noop", magicBudget: 0 }]
  );
}

function input(id, digest, role) {
  return new P.ResourceRef({ id, digest, role, kind: "dataset" });
}

function projectionSpec(inputs) {
  return {
    id: "proj:normalize",
    name: "normalize input",
    service: "transform",
    workloadId: "noop",
    outputKind: "dataset",
    inputs,
    grants: {
      network: ["objects.internal:443", "telemetry.internal:443"],
      services: ["object-store"],
      secrets: ["secret://tenant/signing-key"],
    },
    evidenceRefs: ["cert:projection-runtime"],
    evidencePolicy: E.POLICY.VERIFIED,
  };
}

test("projection identity is stable under set-like input and grant ordering", () => {
  const a = new P.Projection(projectionSpec([
    input("weights", "sha256:bbbb", "weights"),
    input("dataset", "sha256:aaaa", "dataset"),
  ]));
  const b = new P.Projection({
    ...projectionSpec([
      input("dataset", "sha256:aaaa", "dataset"),
      input("weights", "sha256:bbbb", "weights"),
    ]),
    grants: {
      network: ["telemetry.internal:443", "objects.internal:443"],
      services: ["object-store"],
      secrets: ["secret://tenant/signing-key"],
    },
  });
  assert.equal(a.digest, b.digest);
});

test("compile pins the projection plus every input into the execution plan", () => {
  const p = new P.Projection(projectionSpec([
    input("dataset", "sha256:aaaa", "dataset"),
    input("weights", "sha256:bbbb", "weights"),
  ]));
  const pe = new P.ProjectionEngine(engine());
  const compiled = pe.compile(p, { requestedSeconds: 5 });
  const digests = new Set(compiled.planSpec.artifacts.map((a) => a.digest));
  assert.ok(digests.has(p.digest));
  assert.ok(digests.has("sha256:aaaa"));
  assert.ok(digests.has("sha256:bbbb"));
  assert.equal(compiled.planSpec.evidencePolicy, E.POLICY.VERIFIED);
  assert.deepEqual(compiled.planSpec.evidenceRefs, ["cert:projection-runtime"]);
});

test("runtime authority may narrow a projection but cannot widen it", () => {
  const p = new P.Projection(projectionSpec([input("dataset", "sha256:aaaa", "dataset")]));
  const pe = new P.ProjectionEngine(engine());
  const narrow = pe.compile(p, {
    grants: {
      network: ["objects.internal:443"],
      services: [],
      secrets: [],
    },
  });
  assert.deepEqual(narrow.planSpec.grants.network, ["objects.internal:443"]);
  assert.deepEqual(narrow.planSpec.grants.services, []);

  assert.throws(() => pe.compile(p, {
    grants: { network: ["internet.example:443"] },
  }), /authority widening refused/);
});

test("runtime policy may strengthen evidence but cannot weaken it", () => {
  const p = new P.Projection(projectionSpec([input("dataset", "sha256:aaaa", "dataset")]));
  const pe = new P.ProjectionEngine(engine());
  const stronger = pe.compile(p, { evidencePolicy: E.POLICY.RUNTIME_ATTESTED });
  assert.equal(stronger.planSpec.evidencePolicy, E.POLICY.RUNTIME_ATTESTED);
  assert.throws(() => pe.compile(p, { evidencePolicy: E.POLICY.RESEARCH }), /policy weakening refused/);
});

test("runtime artifacts are refused instead of bypassing the projection resource set", () => {
  const p = new P.Projection(projectionSpec([input("dataset", "sha256:aaaa", "dataset")]));
  const pe = new P.ProjectionEngine(engine());
  assert.throws(() => pe.compile(p, {
    artifacts: [{ name: "surprise", digest: "sha256:cccc" }],
  }), /declare resources as projection inputs/);
});

test("created execution plans retain the projection/evidence binding", () => {
  const exec = engine();
  exec.registerEvidence({
    id: "cert:projection-runtime",
    subject: "projection certificate",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: "Projection compiler regression certificate.",
    createdAt: 1,
  });
  const p = new P.Projection(projectionSpec([input("dataset", "sha256:aaaa", "dataset")]));
  const pe = new P.ProjectionEngine(exec);
  const created = pe.createPlan(p, { requestedSeconds: 2 });
  assert.equal(created.plan.verify(), true);
  assert.equal(pe.verifyBinding(p, created.plan).ok, true);
  assert.equal(exec.evidenceDecision(created.plan).ok, true);
});

test("a settled projection emits an immutable reusable resource", () => {
  const exec = engine();
  exec.registerEvidence({
    id: "cert:projection-runtime",
    subject: "projection certificate",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.REGRESSION,
    claim: "Projection compiler regression certificate.",
    createdAt: 1,
  });
  const first = new P.Projection(projectionSpec([input("dataset", "sha256:aaaa", "dataset")]));
  const pe = new P.ProjectionEngine(exec);
  const { plan } = pe.createPlan(first, { requestedSeconds: 2 });
  plan.status = "settled";
  const receipt = {
    id: "RX-TEST",
    planId: plan.id,
    planDigest: plan.digest,
    nodeId: "NODE-TEST",
    nodeSeconds: 2,
    outcome: "settled",
    chainHash: "deadbeef",
    evidenceDigest: "demo:feedfacefeedfacefeedfacefeedface",
    ts: 1,
  };
  plan.receipt = receipt;

  const emission = pe.emit(first, plan, receipt, { metadata: { format: "parquet" } });
  assert.equal(emission.cryptographicallyAttested, false);
  assert.equal(emission.integrityMode, E.INTEGRITY_MODE);
  assert.equal(emission.output.role, "output");
  assert.match(emission.output.digest, /^demo:/);
  assert.match(emission.output.address, /^uor:[0-9a-f]{16}$/);
  assert.equal(pe.emit(first, plan, receipt).digest === emission.digest, false,
    "changing output metadata is a conflicting second emission, not an implicit overwrite");
});

test("emitted resources close composition by becoming the next projection input", () => {
  const exec = engine();
  const first = new P.Projection({
    id: "proj:first",
    workloadId: "noop",
    outputKind: "dataset",
    inputs: [input("raw", "sha256:raw", "source")],
    evidencePolicy: E.POLICY.DEMO,
  });
  const pe = new P.ProjectionEngine(exec);
  const { plan } = pe.createPlan(first, { requestedSeconds: 1 });
  plan.status = "settled";
  const receipt = {
    id: "RX-FIRST",
    planId: plan.id,
    planDigest: plan.digest,
    nodeId: "NODE-1",
    nodeSeconds: 1,
    outcome: "settled",
    chainHash: "abcd1234",
    ts: 1,
  };
  plan.receipt = receipt;
  const emitted = pe.emit(first, plan, receipt);

  const second = new P.Projection({
    id: "proj:second",
    workloadId: "noop",
    inputs: [emitted.output],
    outputKind: "dataset",
  });
  const compiled = pe.compile(second);
  assert.ok(compiled.planSpec.artifacts.some((a) => a.digest === emitted.output.digest));
  assert.notEqual(second.digest, first.digest);
});

test("failed or mismatched receipts cannot emit reusable resources", () => {
  const p = new P.Projection({
    id: "proj:guard",
    workloadId: "noop",
    inputs: [input("raw", "sha256:raw", "source")],
  });
  const pe = new P.ProjectionEngine(engine());
  const { plan } = pe.createPlan(p, { requestedSeconds: 1 });
  plan.status = "settled";

  assert.throws(() => pe.emit(p, plan, {
    id: "RX-FAILED", planId: plan.id, planDigest: plan.digest,
    nodeId: "NODE", nodeSeconds: 0, outcome: "service_halt", ts: 1,
  }), /receipt outcome/);

  assert.throws(() => pe.emit(p, plan, {
    id: "RX-WRONG", planId: plan.id, planDigest: "wrong",
    nodeId: "NODE", nodeSeconds: 1, outcome: "settled", ts: 1,
  }), /does not bind/);
});
