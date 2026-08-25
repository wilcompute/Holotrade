// ======================================================================
// HOLOTRADE evidence-contract regression suite
//
// These tests exercise the correction-aware evidence layer as an actual
// execution admission contract. They intentionally verify the honesty
// boundary too: demo digests are deterministic integrity checks, not
// cryptographic signatures or remote attestation.
// ======================================================================

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
require(path.join(root, "js/substrate.js"));
const E = require(path.join(root, "js/evidence.js"));
const X = require(path.join(root, "js/execution.js"));
require(path.join(root, "js/execution-evidence.js"));

function engine() {
  return new X.ExecutionEngine(
    { listedNodes: () => [], get: () => null },
    { quote: () => ({ serviceable: false, price: null }) },
    { datacenters: [] },
    [{ id: "noop", magicBudget: 0 }]
  );
}

function repoCertificate(id = "w33:srg") {
  return {
    id,
    subject: "W(3,3) level-1 geometry",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.REPO_CERTIFICATE,
    scope: E.SCOPE.EXACT,
    claim: "The configured level-1 substrate is SRG(40,12,2,4).",
    source: { repository: "wilcompute/W33-Theory", certificate: "exact-level1" },
    createdAt: 1,
  };
}

test("canonical evidence digests do not depend on object-key insertion order", () => {
  const a = new E.EvidenceRecord({
    ...repoCertificate("canonical:a"),
    metadata: { beta: 2, alpha: { z: 3, a: 1 } },
  });
  const b = new E.EvidenceRecord({
    ...repoCertificate("canonical:a"),
    metadata: { alpha: { a: 1, z: 3 }, beta: 2 },
  });
  assert.equal(a.digest, b.digest);
  assert.equal(a.verify(), true);
});

test("evidence ids are immutable", () => {
  const ledger = new E.EvidenceLedger();
  ledger.add(repoCertificate("immutable"));
  assert.throws(() => ledger.add({
    ...repoCertificate("immutable"),
    claim: "A different claim under the same identity.",
  }), /immutable/);
});

test("a later correction changes admissibility without rewriting history", () => {
  const ledger = new E.EvidenceLedger();
  const old = ledger.add(repoCertificate("claim:old"));
  const corrected = ledger.add({
    ...repoCertificate("claim:corrected"),
    claim: "Corrected certificate after a wider control sample.",
    supersedes: [old.id],
    createdAt: 2,
  });

  const oldResolution = ledger.resolve(old.id);
  assert.equal(oldResolution.record.digest, old.digest, "historical record is preserved byte-for-byte");
  assert.equal(oldResolution.effectiveStatus, E.STATUS.SUPERSEDED);
  assert.deepEqual(oldResolution.supersededBy, [corrected.id]);

  const oldDecision = ledger.evaluate([old.id], { policy: E.POLICY.VERIFIED });
  assert.equal(oldDecision.ok, false);
  assert.ok(oldDecision.blockers.some((b) => b.code === "SUPERSEDED_EVIDENCE"));

  const correctedDecision = ledger.evaluate([corrected.id], { policy: E.POLICY.VERIFIED });
  assert.equal(correctedDecision.ok, true);
});

test("research policy can carry a hypothesis but verified policy cannot", () => {
  const ledger = new E.EvidenceLedger([{ 
    id: "research:hypothesis",
    subject: "research bridge",
    status: E.STATUS.HYPOTHESIS,
    evidenceClass: E.EVIDENCE_CLASS.MODEL_RESULT,
    scope: E.SCOPE.DESIGN_SKETCH,
    claim: "A proposed bridge that has not been established.",
    createdAt: 1,
  }]);

  const research = ledger.evaluate(["research:hypothesis"], { policy: E.POLICY.RESEARCH });
  assert.equal(research.ok, true);
  assert.ok(research.warnings.some((w) => w.code === E.STATUS.HYPOTHESIS));

  const verified = ledger.evaluate(["research:hypothesis"], { policy: E.POLICY.VERIFIED });
  assert.equal(verified.ok, false);
  assert.ok(verified.blockers.some((b) => b.code === "STATUS_NOT_VERIFIED"));
});

test("runtime-attested policy requires an explicit verified runtime attestation", () => {
  const ledger = new E.EvidenceLedger([repoCertificate("repo-only")]);
  const missing = ledger.evaluate(["repo-only"], { policy: E.POLICY.RUNTIME_ATTESTED });
  assert.equal(missing.ok, false);
  assert.ok(missing.blockers.some((b) => b.code === "RUNTIME_ATTESTATION_REQUIRED"));

  ledger.add({
    id: "runtime:attestation",
    subject: "runtime attestation",
    status: E.STATUS.VERIFIED,
    evidenceClass: E.EVIDENCE_CLASS.RUNTIME_ATTESTATION,
    scope: E.SCOPE.RUNTIME,
    claim: "A runtime attestation accepted by the configured verifier.",
    attested: true,
    createdAt: 2,
  });
  const present = ledger.evaluate(["repo-only", "runtime:attestation"], {
    policy: E.POLICY.RUNTIME_ATTESTED,
  });
  assert.equal(present.ok, true);
});

test("execution plans bind the evidence contract into their integrity seal", () => {
  const exec = engine();
  exec.registerEvidence(repoCertificate("plan:certificate"));
  const plan = exec.createPlan({
    workloadId: "noop",
    name: "evidence-bound plan",
    requestedSeconds: 1,
    evidenceRefs: ["plan:certificate"],
    evidencePolicy: E.POLICY.VERIFIED,
  });

  assert.equal(plan.verify(), true);
  assert.deepEqual(plan.evidenceRefs, ["plan:certificate"]);
  assert.equal(plan.evidencePolicy, E.POLICY.VERIFIED);

  plan.evidenceRefs = ["some-other-record"];
  assert.equal(plan.verify(), false, "editing evidence references after signing breaks the plan seal");
});

test("execution admission fails closed when evidence is missing", () => {
  const exec = engine();
  const plan = exec.createPlan({
    workloadId: "noop",
    name: "missing-evidence plan",
    requestedSeconds: 1,
    evidenceRefs: ["missing:certificate"],
    evidencePolicy: E.POLICY.VERIFIED,
  });
  const result = exec.launch(plan, { id: "NODE-DEMO" });
  assert.equal(result.ok, false);
  assert.equal(result.code, "EVIDENCE_POLICY");
  assert.ok(result.evidence.blockers.some((b) => b.code === "MISSING_EVIDENCE"));
});

test("execution evidence envelopes expose a three-digest BOM without claiming cryptography", () => {
  const ledger = new E.EvidenceLedger([repoCertificate("envelope:certificate")]);
  const envelope = ledger.executionEnvelope({
    plan: {
      id: "PLAN-TEST",
      digest: "0123456789abcdef",
      nodeCount: 1,
      evidenceRefs: ["envelope:certificate"],
      evidencePolicy: E.POLICY.VERIFIED,
    },
    vm: {
      id: "VM-TEST",
      state: "halted",
      secondsRun: 3,
      stateBlobs: 7,
      bootMs: 171.5,
      cost: 0.01,
      energyJoules: 42,
    },
    node: { id: "NODE-TEST", address: "uor:0000000000000000", hardware: { id: "cpu", kind: "cpu" } },
    outcome: "settled",
    auditHash: "deadbeef",
  });

  assert.equal(envelope.integrityMode, E.INTEGRITY_MODE);
  assert.equal(envelope.statement._type, "https://in-toto.io/Statement/v1");
  assert.equal(envelope.statement.predicate.cryptographicallyAttested, false);
  const bom = envelope.statement.predicate.threeDigestBOM;
  assert.match(bom.identityDigest, /^demo:/);
  assert.match(bom.stateDigest, /^demo:/);
  assert.match(bom.runtimeDigest, /^demo:/);
});
