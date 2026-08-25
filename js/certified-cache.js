// ======================================================================
// HOLOTRADE CERTIFIED RESULT CACHE
//
// A fully committed deterministic Projection is a cache key. Reuse is allowed
// only while certificate shape, current evidence, lineage, and any configured
// signature policy remain valid.
//
// v2 makes reuse itself auditable: every accepted hit can emit a new immutable
// reuse receipt committing to the old certificate, current evidence decision,
// output digest, lineage state, signature verification, and node-seconds
// avoided. This is still an in-memory prototype cache, not distributed storage.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const C = root.HolotradeW33TransitionCertificate ||
    (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  const Sig = root.HolotradeSigning ||
    (typeof require !== "undefined" ? require("./signing.js") : null);
  if (!E || !C) throw new Error("certified-cache requires evidence and W33 transition certificates");

  const SCHEMA = "holotrade.certified-result-cache.v2";
  const REUSE_SCHEMA = "holotrade.certified-reuse-receipt.v1";

  class CertifiedResultCache {
    constructor() {
      this.entries = new Map();
      this.hits = 0;
      this.misses = 0;
      this.refusals = 0;
      this.reuseReceipts = [];
    }

    put({ projection, plan, emission, certificate, signedEnvelope = null, dsseEnvelope = null, deterministic = true } = {}) {
      if (!projection || !projection.digest) throw new TypeError("projection required");
      if (!deterministic) throw new Error("nondeterministic projections are not cacheable by exact result identity");
      const shape = C.validateShape(certificate);
      if (!shape.conforms) throw new Error(`invalid transition certificate: ${shape.violations.join(", ")}`);
      if (certificate.source.projectionId !== projection.id || certificate.source.planId !== plan.id) throw new Error("certificate does not bind projection/plan");
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
        dsseEnvelope,
        deterministic: true,
      });
      const existing = this.entries.get(entry.key);
      if (existing && existing.certificate.element.digest !== certificate.element.digest) throw new Error("same projection digest produced a conflicting certified result");
      this.entries.set(entry.key, entry);
      return entry;
    }

    lookup(projection, executionEngine, { lineage = null, trustedKeys = null, signatureThreshold = 1 } = {}) {
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
      const lineageStatus = lineage ? lineage.status(entry.emission.output.digest) : null;
      if (lineage && !lineageStatus.reusable) {
        this.refusals++;
        return { hit: false, code: "LINEAGE_QUARANTINED", current, lineageStatus };
      }
      let signature = { required: false, ok: true, mode: "none" };
      if (trustedKeys !== null) {
        if (!entry.dsseEnvelope || !Sig || typeof Sig.verifyThreshold !== "function") {
          this.refusals++;
          return { hit: false, code: "TRUSTED_SIGNATURE_REQUIRED", current, lineageStatus };
        }
        const verified = Sig.verifyThreshold(entry.dsseEnvelope, trustedKeys, {
          threshold: signatureThreshold,
          expectedPayload: entry.certificate,
          expectedPayloadType: Sig.PAYLOAD_TYPE,
        });
        signature = { required: true, mode: "dsse-threshold", ...verified };
        if (!verified.ok) {
          this.refusals++;
          return { hit: false, code: "SIGNATURE_POLICY_REFUSED", current, lineageStatus, signature };
        }
      } else if (entry.signedEnvelope && Sig) {
        const verified = Sig.verify(entry.signedEnvelope, entry.certificate);
        signature = { required: false, mode: "legacy-self-contained", ...verified };
        if (!verified.ok) {
          this.refusals++;
          return { hit: false, code: "SIGNATURE_INVALID", current, lineageStatus, signature };
        }
      }
      this.hits++;
      return {
        hit: true,
        code: "CERTIFIED_REUSE",
        emission: entry.emission,
        certificate: entry.certificate,
        current,
        lineageStatus,
        signature,
        nodeSecondsAvoided: entry.certificate.trace.execution.nodeSeconds || 0,
      };
    }

    reuseReceipt(projection, executionEngine, options = {}) {
      const result = this.lookup(projection, executionEngine, options);
      if (!result.hit) return result;
      const body = {
        schema: REUSE_SCHEMA,
        projectionDigest: projection.digest,
        sourceCertificateDigest: result.certificate.certificateDigest,
        sourceElementDigest: result.certificate.element.digest,
        outputDigest: result.emission.output.digest,
        currentEvidenceDecisionDigest: result.current.current.digest,
        currentEvidenceOk: result.current.current.ok,
        lineageReusable: result.lineageStatus ? result.lineageStatus.reusable : null,
        signatureMode: result.signature.mode,
        signatureVerified: result.signature.ok,
        nodeSecondsAvoided: result.nodeSecondsAvoided,
        recomputationPerformed: false,
        boundary:
          "This receipt proves a cache admission decision inside the HoloTrade prototype. It does not prove the source computation was physically replayed or that avoided node-seconds equal current market savings.",
      };
      const receipt = Object.freeze({ ...body, digest: E.demoDigest(body) });
      this.reuseReceipts.push(receipt);
      return { ...result, reuseReceipt: receipt };
    }

    stats() {
      return Object.freeze({
        entries: this.entries.size,
        hits: this.hits,
        misses: this.misses,
        refusals: this.refusals,
        reuseReceipts: this.reuseReceipts.length,
        nodeSecondsAvoidedRecorded: this.reuseReceipts.reduce((sum, row) => sum + row.nodeSecondsAvoided, 0),
      });
    }
  }

  const API = { SCHEMA, REUSE_SCHEMA, CertifiedResultCache };
  root.HolotradeCertifiedCache = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
