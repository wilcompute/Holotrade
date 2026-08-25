// ======================================================================
// HOLOTRADE EXECUTION <-> EVIDENCE ADAPTER
//
// Installs evidence policy as a real admission gate without changing the
// legacy execution engine's default demo behaviour. Plans created through
// ExecutionEngine.createPlan bind evidence refs/policy into the integrity
// digest. Settlement emits a three-digest evidence envelope.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const X = root.HolotradeExecution ||
    (typeof require !== "undefined" ? require("./execution.js") : null);

  if (!E || !X) throw new Error("execution-evidence requires evidence.js and execution.js");

  const { ExecutionEngine, ExecutionPlan } = X;
  const INSTALL = Symbol.for("holotrade.execution-evidence.installed.v1");

  function refs(value) {
    if (value === undefined || value === null) return [];
    if (!Array.isArray(value)) throw new TypeError("evidenceRefs must be an array");
    return [...new Set(value.map((x) => {
      if (typeof x !== "string" || x.trim().length === 0) throw new TypeError("evidenceRefs entries must be non-empty strings");
      return x.trim();
    }))].sort();
  }

  function policy(value) {
    const p = value || E.POLICY.DEMO;
    if (!Object.values(E.POLICY).includes(p)) throw new RangeError(`unsupported evidencePolicy: ${String(p)}`);
    return p;
  }

  function ensureLedger(engine) {
    if (!engine.evidenceLedger) engine.evidenceLedger = new E.EvidenceLedger();
    return engine.evidenceLedger;
  }

  function install() {
    if (ExecutionEngine.prototype[INSTALL]) return X;

    const baseComputeDigest = ExecutionPlan.prototype.computeDigest;
    ExecutionPlan.prototype.computeDigest = function evidenceBoundComputeDigest() {
      const base = baseComputeDigest.call(this);
      const bound = {
        base,
        evidenceRefs: refs(this.evidenceRefs),
        evidencePolicy: policy(this.evidencePolicy),
      };
      // Keep the existing 16-hex plan-digest wire shape. The evidence module
      // itself carries the longer explicit `demo:` digest and honesty label.
      return E.demoDigest(bound).slice(5, 21);
    };

    ExecutionEngine.prototype.registerEvidence = function registerEvidence(spec) {
      return ensureLedger(this).add(spec);
    };

    ExecutionEngine.prototype.evidenceDecision = function evidenceDecision(plan) {
      return ensureLedger(this).evaluate(plan.evidenceRefs || [], {
        policy: plan.evidencePolicy || E.POLICY.DEMO,
      });
    };

    ExecutionEngine.prototype.evidenceCheckpoint = function evidenceCheckpoint(label, payload, parentDigest = null) {
      return ensureLedger(this).checkpoint(label, payload, parentDigest);
    };

    const baseCreatePlan = ExecutionEngine.prototype.createPlan;
    ExecutionEngine.prototype.createPlan = function createEvidenceBoundPlan(spec = {}) {
      // Preserve the legacy behavior exactly for a demo plan with no evidence
      // declaration. For evidence-aware plans, reproduce the tiny creation
      // routine so refs/policy are bound before the public digest is finalized.
      const requestedRefs = refs(spec.evidenceRefs);
      const requestedPolicy = policy(spec.evidencePolicy);
      if (requestedRefs.length === 0 && requestedPolicy === E.POLICY.DEMO) {
        const plan = baseCreatePlan.call(this, spec);
        plan.evidenceRefs = [];
        plan.evidencePolicy = E.POLICY.DEMO;
        // Recompute because the patched plan digest explicitly binds the empty
        // evidence contract. This remains a deterministic demo integrity seal.
        plan.digest = plan.computeDigest();
        plan.signature = plan.sign();
        return plan;
      }

      const w = this.workloads.find((x) => x.id === spec.workloadId);
      const plan = new ExecutionPlan({ ...spec, magicBudget: w ? w.magicBudget : 0 });
      plan.evidenceRefs = requestedRefs;
      plan.evidencePolicy = requestedPolicy;
      plan.digest = plan.computeDigest();
      plan.signature = plan.sign();
      this.plans.unshift(plan);
      this.append("plan.signed", `${plan.name} (${plan.workloadId}) t=${plan.magicBudget}; evidence=${requestedPolicy}`, {
        planId: plan.id,
        digest: plan.digest,
        evidencePolicy: plan.evidencePolicy,
        evidenceRefs: plan.evidenceRefs,
      });
      return plan;
    };

    const basePlace = ExecutionEngine.prototype.place;
    ExecutionEngine.prototype.place = function placeWithEvidence(plan, options) {
      const decision = this.evidenceDecision(plan);
      if (!decision.ok) return [];
      return basePlace.call(this, plan, options);
    };

    const baseLaunch = ExecutionEngine.prototype.launch;
    ExecutionEngine.prototype.launch = function launchWithEvidence(plan, node) {
      const decision = this.evidenceDecision(plan);
      if (!decision.ok) {
        plan.status = "rejected";
        const codes = [...new Set(decision.blockers.map((x) => x.code))].join(",");
        const reason = `evidence policy ${decision.policy} refused: ${codes || "unsatisfied"}`;
        this.append("plan.failed", `EVIDENCE_POLICY: ${reason}`, {
          planId: plan.id,
          nodeId: node && node.id,
          evidenceDecision: decision.digest,
          evidencePolicy: decision.policy,
        });
        return { ok: false, reason, code: "EVIDENCE_POLICY", evidence: decision };
      }
      plan.evidenceDecision = decision;
      return baseLaunch.call(this, plan, node);
    };

    const baseSettle = ExecutionEngine.prototype.settle;
    ExecutionEngine.prototype.settle = function settleWithEvidence(vm, plan, node, outcome) {
      const receipt = baseSettle.call(this, vm, plan, node, outcome);
      const envelope = ensureLedger(this).executionEnvelope({
        plan,
        vm,
        node,
        outcome: receipt.outcome,
        auditHash: receipt.chainHash,
      });
      receipt.evidenceEnvelope = envelope;
      receipt.evidenceDigest = envelope.digest;
      receipt.evidencePolicy = plan.evidencePolicy || E.POLICY.DEMO;
      receipt.cryptographicallyAttested = false;
      return receipt;
    };

    Object.defineProperty(ExecutionEngine.prototype, INSTALL, {
      value: true,
      configurable: false,
      enumerable: false,
      writable: false,
    });
    return X;
  }

  const API = { install, ensureLedger };
  install();
  root.HolotradeExecutionEvidence = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
