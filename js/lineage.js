// ======================================================================
// HOLOTRADE RESOURCE LINEAGE + TRANSITIVE QUARANTINE
//
// Outside-the-box idea #1: evidence corrections should propagate through the
// emitted-resource DAG. If an ancestor becomes inadmissible, descendants are
// not erased; they are quarantined for future reuse while history remains.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("lineage requires evidence.js");

  const SCHEMA = "holotrade.resource-lineage.v1";

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) throw new TypeError(`${name} must be a non-empty string`);
    return value.trim();
  }

  class ResourceLineage {
    constructor() {
      this.nodes = new Map();
      this.children = new Map();
      this.quarantine = new Map();
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
      // Refuse cycles even if callers inject historical nodes out of order.
      for (const parent of parents) {
        if (this.descendants(digest).has(parent)) throw new Error("lineage cycle refused");
      }
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
      for (const item of affected) {
        const existing = this.quarantine.get(item) || [];
        existing.push(record);
        this.quarantine.set(item, existing);
      }
      return Object.freeze({ rootDigest: digest, affected: affected.sort(), reason: record.reason, evidenceRef: record.evidenceRef });
    }

    reusable(digest) {
      return this.nodes.has(digest) && !this.quarantine.has(digest);
    }

    status(digest) {
      return Object.freeze({
        known: this.nodes.has(digest),
        reusable: this.reusable(digest),
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
