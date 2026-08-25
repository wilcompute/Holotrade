// ======================================================================
// HOLOTRADE RE-EXECUTION CHALLENGE MARKET
//
// Deterministic results can be challenged by independent certified replay.
// Crucial distinction:
//   - certificate.element.digest = SHA-256 of execution PROVENANCE/emission;
//   - emission.output.metadata.resultDigest = semantic RESULT identity.
//
// Independent executions are expected to have different provenance digests,
// so equality challenges compare resultDigest only after verifying that each
// replay emission is actually bound by its supplied transition certificate.
// Bounties remain accounting-model numbers only.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  const C = root.HolotradeW33TransitionCertificate || (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  if (!E || !C) throw new Error("challenge-market requires evidence and W33 transition certificates");

  const SCHEMA = "holotrade.reexecution-challenge.v3";
  let SEQ = 1;

  function resultDigestOf(emission) {
    const digest = emission?.output?.metadata?.resultDigest;
    if (typeof digest !== "string" || !/^sha256:[0-9a-f]{64}$/.test(digest)) {
      throw new Error("deterministic replay requires emission.output.metadata.resultDigest as canonical SHA-256");
    }
    return digest;
  }

  function certifiedReplay(challenge, bundle) {
    const replayCertificate = bundle?.certificate;
    const replayEmission = bundle?.emission;
    const shape = C.validateShape(replayCertificate);
    if (!shape.conforms) throw new Error(`invalid replay certificate: ${shape.violations.join(", ")}`);
    if (C.sha256Digest(replayEmission) !== replayCertificate.element.digest) {
      throw new Error("replay emission is not bound by the supplied transition certificate element");
    }
    const projectionDigest = replayCertificate.trace?.projection?.digest || null;
    if (projectionDigest !== challenge.projectionDigest) throw new Error("replay certificate does not bind the challenged projection digest");
    const observedResultDigest = resultDigestOf(replayEmission);
    return Object.freeze({
      certificateDigest: replayCertificate.certificateDigest,
      provenanceElementDigest: replayCertificate.element.digest,
      projectionDigest,
      observedResultDigest,
      expectedResultDigest: challenge.expectedResultDigest,
      match: observedResultDigest === challenge.expectedResultDigest,
    });
  }

  class ChallengePool {
    constructor() {
      this.challenges = [];
      this.totalBounty = 0;
    }

    open(certificate, { emission, bounty = 0, deterministic = false, sponsor = "anonymous" } = {}) {
      if (!certificate || certificate.status !== "PASS") throw new TypeError("PASS transition certificate required");
      if (!deterministic) throw new Error("re-execution equality challenges require a deterministic transition declaration");
      if (!Number.isFinite(bounty) || bounty < 0) throw new RangeError("bounty must be non-negative");
      if (C.sha256Digest(emission) !== certificate.element.digest) throw new Error("source emission is not bound by the challenge certificate");
      const projectionDigest = certificate.trace?.projection?.digest;
      if (!projectionDigest) throw new Error("certificate is missing projection digest");
      const expectedResultDigest = resultDigestOf(emission);
      const row = {
        schema: SCHEMA,
        id: `CHALLENGE-${String(SEQ++).padStart(5, "0")}`,
        certificateDigest: certificate.certificateDigest,
        projectionId: certificate.source?.projectionId || null,
        projectionDigest,
        sourceProvenanceElementDigest: certificate.element.digest,
        expectedResultDigest,
        historicalEvidenceRefs: [...(certificate.proof?.historical_evidence_admission?.refs || [])],
        sponsor: String(sponsor),
        bounty,
        deterministic: true,
        status: "open",
        result: null,
      };
      this.challenges.push(row);
      this.totalBounty += bounty;
      return row;
    }

    /** Legacy provenance comparison retained only for historical callers. */
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
        match,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
        warning: "This legacy mode compares provenance identity, not semantic deterministic result identity.",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    resolveCertified(challenge, replayBundle) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const replay = certifiedReplay(challenge, replayBundle);
      challenge.status = replay.match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "certified-semantic-replay",
        ...replay,
        bountyDisposition: replay.match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    resolveQuorum(challenge, replayBundles, { minimum = 2 } = {}) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      if (!Number.isInteger(minimum) || minimum < 2) throw new RangeError("minimum quorum must be >= 2");
      if (!Array.isArray(replayBundles)) throw new TypeError("replayBundles must be an array");
      const seen = new Set();
      const replays = [];
      for (const bundle of replayBundles) {
        const replay = certifiedReplay(challenge, bundle);
        if (seen.has(replay.certificateDigest)) continue;
        seen.add(replay.certificateDigest);
        replays.push(replay);
      }
      if (replays.length < minimum) {
        return Object.freeze({ mode: "certified-semantic-quorum", resolved: false, code: "QUORUM_NOT_MET", minimum, distinctReplays: replays.length, replays });
      }
      const mismatches = replays.filter((row) => !row.match);
      const match = mismatches.length === 0;
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "certified-semantic-quorum",
        resolved: true,
        minimum,
        distinctReplays: replays.length,
        match,
        matchingCount: replays.length - mismatches.length,
        mismatchCount: mismatches.length,
        replays: Object.freeze(replays),
        observedResultDigest: match ? challenge.expectedResultDigest : mismatches[0].observedResultDigest,
        expectedResultDigest: challenge.expectedResultDigest,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    correctionForMismatch(challenge, { createdAt = Date.now(), challenger = "independent-replay" } = {}) {
      if (!challenge || challenge.status !== "mismatch" || !challenge.result) throw new Error("a resolved mismatch challenge is required");
      const invalidates = [...challenge.historicalEvidenceRefs].sort();
      return {
        id: `replay-mismatch:${challenge.id}`,
        subject: `Re-execution mismatch for ${challenge.certificateDigest}`,
        status: E.STATUS.VERIFIED,
        evidenceClass: E.EVIDENCE_CLASS.MODEL_RESULT,
        scope: E.SCOPE.REGRESSION,
        claim: "One or more independently certified deterministic re-executions of the same projection produced a different semantic result SHA-256 commitment.",
        invalidates,
        createdAt,
        source: {
          challengeId: challenge.id,
          challenger,
          certificateDigest: challenge.certificateDigest,
          projectionDigest: challenge.projectionDigest,
          expectedResultDigest: challenge.result.expectedResultDigest,
          observedResultDigest: challenge.result.observedResultDigest,
          resolutionMode: challenge.result.mode,
          distinctReplays: challenge.result.distinctReplays || 1,
        },
        metadata: {
          correctionReady: true,
          automaticInvalidationScope: invalidates.length ? "referenced-evidence" : "manual-review-required",
          physicalAttestationClaimed: false,
          provenanceIdentityCompared: false,
          semanticResultIdentityCompared: true,
        },
      };
    }
  }

  const API = { SCHEMA, ChallengePool, certifiedReplay, resultDigestOf };
  root.HolotradeChallengeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
