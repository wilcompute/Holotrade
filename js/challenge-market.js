// ======================================================================
// HOLOTRADE RE-EXECUTION CHALLENGE MARKET
//
// Outside-the-box idea #2: certified deterministic results can be challenged
// by independently re-running the transition and comparing the canonical
// output/emission commitment. A mismatch produces a correction-ready evidence
// record rather than rewriting the original receipt.
//
// Bounties here are accounting-model numbers only; no payment rail exists.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const C = root.HolotradeW33TransitionCertificate ||
    (typeof require !== "undefined" ? require("./w33-transition-certificate.js") : null);
  if (!E || !C) throw new Error("challenge-market requires evidence and W33 transition certificates");

  const SCHEMA = "holotrade.reexecution-challenge.v1";
  let SEQ = 1;

  class ChallengePool {
    constructor() {
      this.challenges = [];
      this.totalBounty = 0;
    }

    open(certificate, { bounty = 0, deterministic = false, sponsor = "anonymous" } = {}) {
      if (!certificate || certificate.status !== "PASS") throw new TypeError("PASS transition certificate required");
      if (!deterministic) throw new Error("re-execution equality challenges require a deterministic transition declaration");
      if (!Number.isFinite(bounty) || bounty < 0) throw new RangeError("bounty must be non-negative");
      const row = {
        schema: SCHEMA,
        id: `CHALLENGE-${String(SEQ++).padStart(5, "0")}`,
        certificateDigest: certificate.certificateDigest,
        expectedElementDigest: certificate.element.digest,
        historicalEvidenceRefs: [...(certificate.proof?.historical_evidence_admission?.refs || [])],
        sponsor: String(sponsor),
        bounty,
        status: "open",
        result: null,
      };
      this.challenges.push(row);
      this.totalBounty += bounty;
      return row;
    }

    resolve(challenge, replayEmission) {
      if (!challenge || challenge.status !== "open") throw new Error("open challenge required");
      const observed = C.sha256Digest(replayEmission);
      const match = observed === challenge.expectedElementDigest;
      challenge.status = match ? "confirmed" : "mismatch";
      challenge.result = Object.freeze({
        observedElementDigest: observed,
        expectedElementDigest: challenge.expectedElementDigest,
        match,
        bountyDisposition: match ? "return-to-sponsor" : "pay-challenger-model",
      });
      this.totalBounty -= challenge.bounty;
      return challenge.result;
    }

    correctionForMismatch(challenge, { createdAt = Date.now(), challenger = "independent-replay" } = {}) {
      if (!challenge || challenge.status !== "mismatch" || !challenge.result) {
        throw new Error("a resolved mismatch challenge is required");
      }
      const invalidates = [...challenge.historicalEvidenceRefs].sort();
      return {
        id: `replay-mismatch:${challenge.id}`,
        subject: `Re-execution mismatch for ${challenge.certificateDigest}`,
        status: E.STATUS.VERIFIED,
        evidenceClass: E.EVIDENCE_CLASS.MODEL_RESULT,
        scope: E.SCOPE.REGRESSION,
        claim: "An independently supplied deterministic replay emission did not match the certified canonical emission digest.",
        invalidates,
        createdAt,
        source: {
          challengeId: challenge.id,
          challenger,
          certificateDigest: challenge.certificateDigest,
          expectedElementDigest: challenge.result.expectedElementDigest,
          observedElementDigest: challenge.result.observedElementDigest,
        },
        metadata: {
          correctionReady: true,
          automaticInvalidationScope: invalidates.length ? "referenced-evidence" : "manual-review-required",
          physicalAttestationClaimed: false,
        },
      };
    }
  }

  const API = { SCHEMA, ChallengePool };
  root.HolotradeChallengeMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
