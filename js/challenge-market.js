// ======================================================================
// HOLOTRADE RE-EXECUTION CHALLENGE MARKET
//
// Certified deterministic results can be challenged by independent replay.
// v2 requires replay certificates to bind the SAME projection digest and can
// resolve a challenge from a quorum of distinct certified re-executions.
//
// A mismatch is correction-ready evidence; it does not rewrite the original
// settlement. Bounties remain accounting-model numbers only.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const C = root.HolotradeW33TransitionCertificate ||
    (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  if (!E || !C) throw new Error("challenge-market requires evidence and W33 transition certificates");

  const SCHEMA = "holotrade.reexecution-challenge.v2";
  let SEQ = 1;

  function certifiedReplay(challenge, replayCertificate) {
    const shape = C.validateShape(replayCertificate);
    if (!shape.conforms) throw new Error(`invalid replay certificate: ${shape.violations.join(", ")}`);
    const projectionDigest = replayCertificate.trace?.projection?.digest || null;
    if (projectionDigest !== challenge.projectionDigest) {
      throw new Error("replay certificate does not bind the challenged projection digest");
    }
    return Object.freeze({
      certificateDigest: replayCertificate.certificateDigest,
      projectionDigest,
      observedElementDigest: replayCertificate.element.digest,
      expectedElementDigest: challenge.expectedElementDigest,
      match: replayCertificate.element.digest === challenge.expectedElementDigest,
    });
  }

  class ChallengePool {
    constructor() {
      this.challenges = [];
      this.totalBounty = 0;
    }

    open(certificate, { bounty = 0, deterministic = false, sponsor = "anonymous" } = {}) {
      if (!certificate || certificate.status !== "PASS") throw new TypeError("PASS transition certificate required");
      if (!deterministic) throw new Error("re-execution equality challenges require a deterministic transition declaration");
      if (!Number.isFinite(bounty) || bounty < 0) throw new RangeError("bounty must be non-negative");
      const projectionDigest = certificate.trace?.projection?.digest;
      if (!projectionDigest) throw new Error("certificate is missing projection digest");
      const row = {
        schema: SCHEMA,
        id: `CHALLENGE-${String(SEQ++).padStart(5, "0")}`,
        certificateDigest: certificate.certificateDigest,
        projectionId: certificate.source?.projectionId || null,
        projectionDigest,
        expectedElementDigest: certificate.element.digest,
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

    /** Legacy raw-emission comparison; useful only when the replay path itself is trusted by the caller. */
    resolve(challenge, replayEmission) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const observed = C.sha256Digest(replayEmission);
      const match = observed === challenge.expectedElementDigest;
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "raw-emission",
        observedElementDigest: observed,
        expectedElementDigest: challenge.expectedElementDigest,
        match,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    resolveCertified(challenge, replayCertificate) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const replay = certifiedReplay(challenge, replayCertificate);
      challenge.status = replay.match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "certified-replay",
        ...replay,
        bountyDisposition: replay.match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    /**
     * Conservative quorum rule: once `minimum` distinct valid replay
     * certificates exist, ANY mismatch makes the deterministic result
     * correction-ready. All matching replays confirm it.
     */
    resolveQuorum(challenge, replayCertificates, { minimum = 2 } = {}) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      if (!Number.isInteger(minimum) || minimum < 2) throw new RangeError("minimum quorum must be >= 2");
      if (!Array.isArray(replayCertificates)) throw new TypeError("replayCertificates must be an array");
      const seen = new Set();
      const replays = [];
      for (const cert of replayCertificates) {
        const replay = certifiedReplay(challenge, cert);
        if (seen.has(replay.certificateDigest)) continue;
        seen.add(replay.certificateDigest);
        replays.push(replay);
      }
      if (replays.length < minimum) {
        return Object.freeze({
          mode: "certified-quorum",
          resolved: false,
          code: "QUORUM_NOT_MET",
          minimum,
          distinctReplays: replays.length,
          replays,
        });
      }
      const mismatches = replays.filter((row) => !row.match);
      const match = mismatches.length === 0;
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        mode: "certified-quorum",
        resolved: true,
        minimum,
        distinctReplays: replays.length,
        match,
        matchingCount: replays.length - mismatches.length,
        mismatchCount: mismatches.length,
        replays: Object.freeze(replays),
        observedElementDigest: match ? challenge.expectedElementDigest : mismatches[0].observedElementDigest,
        expectedElementDigest: challenge.expectedElementDigest,
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
        claim: "One or more independently supplied deterministic replay certificates did not match the certified canonical emission digest for the same projection digest.",
        invalidates,
        createdAt,
        source: {
          challengeId: challenge.id,
          challenger,
          certificateDigest: challenge.certificateDigest,
          projectionDigest: challenge.projectionDigest,
          expectedElementDigest: challenge.result.expectedElementDigest,
          observedElementDigest: challenge.result.observedElementDigest,
          resolutionMode: challenge.result.mode,
          distinctReplays: challenge.result.distinctReplays || 1,
        },
        metadata: {
          correctionReady: true,
          automaticInvalidationScope: invalidates.length ? "referenced-evidence" : "manual-review-required",
          physicalAttestationClaimed: false,
        },
      };
    }
  }

  const API = { SCHEMA, ChallengePool, certifiedReplay };
  root.HolotradeChallengeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
