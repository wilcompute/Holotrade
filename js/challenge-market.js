// ======================================================================
// HOLOTRADE RE-EXECUTION CHALLENGE MARKET
//
// Provenance identity and semantic result identity are deliberately separate.
// Certified replay uses first-class result commitments as authority. Legacy
// metadata-only result digests remain an explicitly advisory compatibility
// path and can never trigger automatic evidence invalidation.
// ======================================================================
(function (root) {
  "use strict";
  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  const C = root.HolotradeW33TransitionCertificate || (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  const R = root.HolotradeResultContract || (typeof require !== "undefined" ? require("./result-contract.js") : null);
  if (!E || !C || !R) throw new Error("challenge-market requires evidence, W33 transition certificates, and result contracts");
  const SCHEMA = "holotrade.reexecution-challenge.v3";
  let SEQ = 1;

  function resultDigestOf(emission) {
    return R.resultDigestOf(emission);
  }

  function certifiedReplay(challenge, bundle) {
    if (!challenge.expectedResultDigest) throw new Error("challenge was opened in legacy provenance mode; semantic certified replay unavailable");
    const cert = bundle?.certificate;
    const emission = bundle?.emission;
    const shape = C.validateShape(cert);
    if (!shape.conforms) throw new Error(`invalid replay certificate: ${shape.violations.join(", ")}`);
    if (C.sha256Digest(emission) !== cert.element.digest) throw new Error("replay emission is not bound by supplied certificate");
    const projectionDigest = cert.trace?.projection?.digest || null;
    if (projectionDigest !== challenge.projectionDigest) throw new Error("replay certificate does not bind challenged projection digest");
    const observedIdentity = R.resultIdentityOf(emission, { allowLegacy: challenge.resultIdentityMode === "legacy-metadata" });
    const observedResultDigest = observedIdentity.digest;
    const authoritativeSemanticIdentity = challenge.authoritativeSemanticIdentity === true && observedIdentity.authoritative === true;
    return Object.freeze({
      certificateDigest: cert.certificateDigest,
      provenanceElementDigest: cert.element.digest,
      projectionDigest,
      observedResultDigest,
      expectedResultDigest: challenge.expectedResultDigest,
      resultIdentityMode: observedIdentity.mode,
      authoritativeSemanticIdentity,
      manualReviewRequired: !authoritativeSemanticIdentity,
      match: observedResultDigest === challenge.expectedResultDigest,
    });
  }

  class ChallengePool {
    constructor() { this.challenges = []; this.totalBounty = 0; }

    open(certificate, { emission = null, bounty = 0, deterministic = false, sponsor = "anonymous" } = {}) {
      if (!certificate || certificate.status !== "PASS") throw new TypeError("PASS transition certificate required");
      if (!deterministic) throw new Error("re-execution equality challenges require a deterministic transition declaration");
      if (!Number.isFinite(bounty) || bounty < 0) throw new RangeError("bounty must be non-negative");
      const projectionDigest = certificate.trace?.projection?.digest;
      if (!projectionDigest) throw new Error("certificate is missing projection digest");
      let expectedResultDigest = null;
      let resultIdentityMode = null;
      let authoritativeSemanticIdentity = false;
      let mode = "legacy-provenance";
      if (emission) {
        if (C.sha256Digest(emission) !== certificate.element.digest) throw new Error("source emission is not bound by challenge certificate");
        // allowLegacy is deliberate here: old v2 certificates can still be
        // compared, but the challenge records that they are advisory and the
        // correction path will require manual review.
        const identity = R.resultIdentityOf(emission, { allowLegacy: true });
        expectedResultDigest = identity.digest;
        resultIdentityMode = identity.mode;
        authoritativeSemanticIdentity = identity.authoritative === true;
        mode = authoritativeSemanticIdentity ? "semantic-certified" : "semantic-legacy-advisory";
      }
      const row = {
        schema: SCHEMA,
        id: `CHALLENGE-${String(SEQ++).padStart(5, "0")}`,
        certificateDigest: certificate.certificateDigest,
        projectionId: certificate.source?.projectionId || null,
        projectionDigest,
        sourceProvenanceElementDigest: certificate.element.digest,
        expectedResultDigest,
        resultIdentityMode,
        authoritativeSemanticIdentity,
        manualReviewRequired: !!emission && !authoritativeSemanticIdentity,
        historicalEvidenceRefs: [...(certificate.proof?.historical_evidence_admission?.refs || [])],
        sponsor: String(sponsor), bounty, deterministic: true,
        mode,
        status: "open", result: null,
      };
      this.challenges.push(row); this.totalBounty += bounty; return row;
    }

    resolve(challenge, replayEmission) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const observed = C.sha256Digest(replayEmission);
      const match = observed === challenge.sourceProvenanceElementDigest;
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "legacy-provenance-comparison",
        observedElementDigest: observed,
        expectedElementDigest: challenge.sourceProvenanceElementDigest,
        observedResultDigest: null,
        expectedResultDigest: challenge.expectedResultDigest,
        authoritativeSemanticIdentity: false,
        manualReviewRequired: true,
        match,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
        warning: "Legacy mode compares provenance identity, not semantic deterministic result identity.",
      });
      this.totalBounty -= challenge.bounty; return challenge.result;
    }

    resolveCertified(challenge, replayBundle) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const replay = certifiedReplay(challenge, replayBundle);
      challenge.status = replay.match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({ mode: "certified-semantic-replay", ...replay, bountyDisposition: replay.match ? "return-to-sponsor" : "pay-challenger-model" });
      this.totalBounty -= challenge.bounty; return challenge.result;
    }

    resolveQuorum(challenge, replayBundles, { minimum = 2 } = {}) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      if (!Number.isInteger(minimum) || minimum < 2) throw new RangeError("minimum quorum must be >= 2");
      if (!Array.isArray(replayBundles)) throw new TypeError("replayBundles must be an array");
      const seen = new Set(), replays = [];
      for (const bundle of replayBundles) {
        const replay = certifiedReplay(challenge, bundle);
        if (!seen.has(replay.certificateDigest)) { seen.add(replay.certificateDigest); replays.push(replay); }
      }
      if (replays.length < minimum) return Object.freeze({ mode: "certified-semantic-quorum", resolved: false, code: "QUORUM_NOT_MET", minimum, distinctReplays: replays.length, replays });
      const mismatches = replays.filter((row) => !row.match);
      const match = mismatches.length === 0;
      const authoritativeSemanticIdentity = challenge.authoritativeSemanticIdentity === true && replays.every((row) => row.authoritativeSemanticIdentity === true);
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "certified-semantic-quorum", resolved: true, minimum,
        distinctReplays: replays.length, match,
        matchingCount: replays.length - mismatches.length, mismatchCount: mismatches.length,
        replays: Object.freeze(replays),
        observedResultDigest: match ? challenge.expectedResultDigest : mismatches[0].observedResultDigest,
        expectedResultDigest: challenge.expectedResultDigest,
        authoritativeSemanticIdentity,
        manualReviewRequired: !authoritativeSemanticIdentity,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty; return challenge.result;
    }

    correctionForMismatch(challenge, { createdAt = Date.now(), challenger = "independent-replay" } = {}) {
      if (!challenge || challenge.status !== "mismatch" || !challenge.result) throw new Error("a resolved mismatch challenge is required");
      const invalidates = [...challenge.historicalEvidenceRefs].sort();
      const semantic = challenge.result.mode !== "legacy-provenance-comparison";
      const authoritative = semantic && challenge.result.authoritativeSemanticIdentity === true;
      return {
        id: `replay-mismatch:${challenge.id}`,
        subject: `Re-execution mismatch for ${challenge.certificateDigest}`,
        status: E.STATUS.VERIFIED,
        evidenceClass: E.EVIDENCE_CLASS.MODEL_RESULT,
        scope: E.SCOPE.REGRESSION,
        claim: semantic
          ? (authoritative
            ? "One or more independently certified deterministic re-executions of the same projection produced a different authoritative semantic result SHA-256 commitment."
            : "One or more certified deterministic re-executions disagreed on a legacy metadata-only result digest; this is advisory compatibility evidence and requires manual review.")
          : "A replay emission did not match the original provenance commitment; this legacy comparison does not establish semantic nondeterminism.",
        invalidates,
        createdAt,
        source: {
          challengeId: challenge.id, challenger,
          certificateDigest: challenge.certificateDigest,
          projectionDigest: challenge.projectionDigest,
          expectedResultDigest: challenge.result.expectedResultDigest || null,
          observedResultDigest: challenge.result.observedResultDigest || null,
          expectedElementDigest: challenge.result.expectedElementDigest || null,
          observedElementDigest: challenge.result.observedElementDigest || null,
          resolutionMode: challenge.result.mode,
          resultIdentityMode: challenge.result.resultIdentityMode || challenge.result.replays?.[0]?.resultIdentityMode || null,
          distinctReplays: challenge.result.distinctReplays || 1,
        },
        metadata: {
          // correctionReady means a correction record can be produced. Only an
          // authoritative first-class mismatch may automatically invalidate.
          correctionReady: semantic,
          automaticInvalidationScope: authoritative && invalidates.length ? "referenced-evidence" : "manual-review-required",
          authoritativeSemanticIdentity: authoritative,
          manualReviewRequired: !authoritative,
          physicalAttestationClaimed: false,
          provenanceIdentityCompared: !semantic,
          semanticResultIdentityCompared: semantic,
        },
      };
    }
  }
  const API = { SCHEMA, ChallengePool, certifiedReplay, resultDigestOf };
  root.HolotradeChallengeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
