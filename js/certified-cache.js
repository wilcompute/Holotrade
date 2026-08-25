// ======================================================================
// HOLOTRADE CERTIFIED RESULT CACHE
//
// Outside-the-box idea #3: a fully committed Projection is a cache key.
// If a previously settled result has a valid transition certificate AND its
// evidence remains admissible now, identical work can reuse the immutable
// output instead of buying more node-seconds.
//
// This is an in-memory prototype cache. It is not distributed storage and
// does not claim semantic equivalence for nondeterministic computations.
// ======================================================================

(function (root) {
  "use strict";

  const C = root.HolotradeW33TransitionCertificate ||
    (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  const Sig = root.HolotradeSigning ||
    (typeof require !== "undefined" ? require("./signing.js") : null);
  if (!C) throw new Error("certified-cache requires W33 transition certificates");

  const SCHEMA = "holotrade.certified-result-cache.v1";

  class CertifiedResultCache {
    constructor() {
      this.entries = new Map();
      this.hits = 0;
      this.misses = 0;
      this.refusals = 0;
    }

    put({ projection, plan, emission, certificate, signedEnvelope = null, deterministic = true } = {}) {
      if (!projection || !projection.digest) throw new TypeError("projection required");
      if (!deterministic) throw new Error("nondeterministic projections are not cacheable by exact result identity");
      const shape = C.validateShape(certificate);
      if (!shape.conforms) throw new Error(`invalid transition certificate: ${shape.violations.join(", ")}`);
      if (certificate.source.projectionId !== projection.id || certificate.source.planId !== plan.id) {
        throw new Error("certificate does not bind projection/plan");
      }
      if (signedEnvelope && Sig) {
        const verified = Sig.verify(signedEnvelope, certificate);
        if (!verified.ok) throw new Error(`signed certificate envelope failed verification: ${verified.code}`);
      }
      const entry = Object.freeze({
        schema: SCHEMA,
        key: projection.digest,
        projectionDigest: projection.digest,
        plan,
        emission,
        certificate,
        signedEnvelope,
        deterministic: true,
      });
      const existing = this.entries.get(entry.key);
      if (existing && existing.certificate.element.digest !== certificate.element.digest) {
        throw new Error("same projection digest produced a conflicting certified result");
      }
      this.entries.set(entry.key, entry);
      return entry;
    }

    lookup(projection, executionEngine, { lineage = null } = {}) {
      const key = projection?.digest;
      const entry = key ? this.entries.get(key) : null;
      if (!entry) {
        this.misses++;
        return { hit: false, code: "MISS" };
      }
      const current = C.reevaluateEvidence(entry.certificate, executionEngine, entry.plan);
      if (!current.reusableNow) {
        this.refusals++;
        return { hit: false, code: "EVIDENCE_STALE", current };
      }
      if (lineage && !lineage.reusable(entry.emission.output.digest)) {
        this.refusals++;
        return { hit: false, code: "LINEAGE_QUARANTINED", current };
      }
      if (entry.signedEnvelope && Sig) {
        const verified = Sig.verify(entry.signedEnvelope, entry.certificate);
        if (!verified.ok) {
          this.refusals++;
          return { hit: false, code: "SIGNATURE_INVALID", current };
        }
      }
      this.hits++;
      return {
        hit: true,
        code: "CERTIFIED_REUSE",
        emission: entry.emission,
        certificate: entry.certificate,
        current,
        nodeSecondsAvoided: entry.certificate.trace.execution.nodeSeconds || 0,
      };
    }

    stats() {
      return Object.freeze({ entries: this.entries.size, hits: this.hits, misses: this.misses, refusals: this.refusals });
    }
  }

  const API = { SCHEMA, CertifiedResultCache };
  root.HolotradeCertifiedCache = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
