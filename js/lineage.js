// ======================================================================
// HOLOTRADE RESOURCE LINEAGE + TRANSITIVE QUARANTINE
//
// Evidence corrections propagate through the emitted-resource DAG. History is
// retained; only future reuse is quarantined. v2 links certified emissions to
// the evidence that admitted them and can refresh the DAG directly from the
// current EvidenceLedger, removing the need for manual quarantine calls.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("lineage requires evidence.js");

  const SCHEMA = "holotrade.resource-lineage.v2";

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) throw new TypeError(`${name} must be a non-empty string`);
    return value.trim();
  }

  class ResourceLineage {
    constructor() {
      this.nodes = new Map();
      this.children = new Map();
      this.quarantine = new Map();
      this.certifiedEvidence = new Map();
    }

    addEmission(emission, metadata = {}) {
      if (!emission || !emission.output || !emission.output.digest) throw new TypeError("emission with output digest required");
      const digest = text(emission.output.digest, "output digest");
      const parents = [...new Set((emission.parents || []).map((p) => text(p.digest, "parent digest")))].sort();
      if (parents.includes(digest)) throw new Error("lineage self-cycle refused");
      if (this.nodes.has(digest)) {
        const prior = this.nodes.get(digest);
        if (prior.emissionDigest !== emission.digest) throw new Error("same resource digest already has different emission provenance");
        return prior;
      }
      for (const parent of parents) if (this.descendants(digest).has(parent)) throw new Error("lineage cycle refused");
      const node = Object.freeze({
        schema: SCHEMA,
        digest,
        resourceId: emission.output.id,
        emissionDigest: emission.digest,
        projectionDigest: emission.projection?.digest || null,
        planDigest: emission.execution?.planDigest || null,
        parents,
        metadata: JSON.parse(E.canonicalJson(metadata)),
      });
      this.nodes.set(digest, node);
      if (!this.children.has(digest)) this.children.set(digest, new Set());
      for (const parent of parents) {
        if (!this.children.has(parent)) this.children.set(parent, new Set());
        this.children.get(parent).add(digest);
      }
      return node;
    }

    addCertifiedEmission(emission, certificate, metadata = {}) {
      const node = this.addEmission(emission, metadata);
      if (!certificate || certificate.status !== "PASS") throw new TypeError("PASS transition certificate required");
      if (certificate.element?.digest && certificate.element.digest !== `sha256:${certificate.element.canonicalBytesSha256}`) {
        throw new Error("certificate element digest malformed");
      }
      const historical = certificate.proof?.historical_evidence_admission || {};
      const binding = Object.freeze({
        certificateDigest: certificate.certificateDigest,
        elementDigest: certificate.element?.digest || null,
        evidenceRefs: [...new Set(historical.refs || [])].sort(),
        evidencePolicy: historical.policy || E.POLICY.DEMO,
        historicalDecisionDigest: historical.digest || null,
      });
      const existing = this.certifiedEvidence.get(node.digest);
      if (existing && existing.certificateDigest !== binding.certificateDigest) {
        throw new Error("resource digest already bound to a different transition certificate");
      }
      this.certifiedEvidence.set(node.digest, binding);
      return Object.freeze({ node, binding });
    }

    descendants(digest) {
      const out = new Set();
      const stack = [...(this.children.get(digest) || [])];
      while (stack.length) {
        const current = stack.pop();
        if (out.has(current)) continue;
        out.add(current);
        for (const child of this.children.get(current) || []) stack.push(child);
      }
      return out;
    }

    ancestors(digest) {
      const out = new Set();
      const stack = [...(this.nodes.get(digest)?.parents || [])];
      while (stack.length) {
        const current = stack.pop();
        if (out.has(current)) continue;
        out.add(current);
        for (const parent of this.nodes.get(current)?.parents || []) stack.push(parent);
      }
      return out;
    }

    quarantineFrom(digest, reason, evidenceRef = null) {
      const affected = [digest, ...this.descendants(digest)];
      const record = {
        reason: text(reason, "reason"),
        evidenceRef: evidenceRef ? text(evidenceRef, "evidenceRef") : null,
        rootDigest: digest,
      };
      const key = E.demoDigest(record);
      for (const item of affected) {
        const existing = this.quarantine.get(item) || [];
        if (!existing.some((row) => row.key === key)) existing.push(Object.freeze({ ...record, key }));
        this.quarantine.set(item, existing);
      }
      return Object.freeze({ rootDigest: digest, affected: affected.sort(), reason: record.reason, evidenceRef: record.evidenceRef, key });
    }

    /**
     * Re-evaluate every certified resource against the current ledger. Any
     * stale root is quarantined together with all descendants. This operation
     * is monotone: corrections add quarantine; they never erase history.
     */
    refreshEvidence(executionEngine) {
      const ledger = executionEngine?.evidenceLedger;
      if (!ledger || typeof ledger.evaluate !== "function") throw new TypeError("execution engine with EvidenceLedger required");
      const decisions = [];
      const newlyQuarantined = new Set();
      for (const [digest, binding] of this.certifiedEvidence) {
        const decision = ledger.evaluate(binding.evidenceRefs, { policy: binding.evidencePolicy });
        decisions.push({ digest, certificateDigest: binding.certificateDigest, decision });
        if (!decision.ok) {
          const codes = [...new Set(decision.blockers.map((x) => x.code))].sort().join(",") || "EVIDENCE_STALE";
          const q = this.quarantineFrom(digest, `current evidence refused: ${codes}`, binding.evidenceRefs[0] || null);
          for (const item of q.affected) newlyQuarantined.add(item);
        }
      }
      const body = {
        schema: "holotrade.resource-lineage-evidence-refresh.v1",
        checked: decisions.length,
        staleRoots: decisions.filter((row) => !row.decision.ok).map((row) => row.digest).sort(),
        affected: [...newlyQuarantined].sort(),
        decisions: decisions.map((row) => ({
          digest: row.digest,
          certificateDigest: row.certificateDigest,
          evidenceDecisionDigest: row.decision.digest,
          ok: row.decision.ok,
          blockers: row.decision.blockers,
        })),
      };
      return Object.freeze({ ...body, digest: E.demoDigest(body) });
    }

    reusable(digest) {
      return this.nodes.has(digest) && !this.quarantine.has(digest);
    }

    status(digest) {
      return Object.freeze({
        known: this.nodes.has(digest),
        reusable: this.reusable(digest),
        certifiedEvidence: this.certifiedEvidence.get(digest) || null,
        quarantines: Object.freeze([...(this.quarantine.get(digest) || [])]),
        ancestors: Object.freeze([...this.ancestors(digest)].sort()),
        descendants: Object.freeze([...this.descendants(digest)].sort()),
      });
    }
  }

  const API = { SCHEMA, ResourceLineage };
  root.HolotradeLineage = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
