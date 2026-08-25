// ======================================================================
// HOLOTRADE -> GoMicroVM CONTRACT ADAPTER
//
// Compiles a HoloTrade ExecutionPlan into a payload-ready contract matching
// the currently documented GoMicroVM/mvm security vocabulary: pinned
// artifacts, explicit authority, policy refs, validity/nonce, seccomp posture,
// redacted invocation metadata, and signed-receipt ingestion.
//
// This adapter does NOT invoke mvmctl, Firecracker, Nix, a guest agent, or a
// hosted control plane. It is an offline contract compiler + receipt parser.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("gomicrovm-adapter requires evidence.js");

  const SCHEMA = "holotrade.gomicrovm-adapter.v1";
  const CONTRACT_SCHEMA = "holotrade.gomicrovm-execution-contract.v1";

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) throw new TypeError(`${name} must be a non-empty string`);
    return value.trim();
  }

  function canonical(value) {
    return JSON.parse(E.canonicalJson(value));
  }

  function strings(value) {
    return [...new Set((value || []).map((x) => text(x, "string entry")))].sort();
  }

  function seccompTier(plan) {
    // Current mvm docs expose essential/minimal/standard/network/unrestricted.
    // HoloTrade is deny-all by default, so network authority is the only
    // reason this compiler raises the suggested tier above minimal.
    return (plan.grants?.network || []).length > 0 ? "network" : "minimal";
  }

  function compile(plan, options = {}) {
    if (!plan || typeof plan !== "object" || !plan.id || !plan.digest) throw new TypeError("ExecutionPlan required");
    if (typeof plan.verify === "function" && !plan.verify()) throw new Error("refusing to compile a plan with an invalid HoloTrade integrity seal");
    const policyRefs = strings(options.policyRefs || ["local-default"]);
    if (policyRefs.length === 0) throw new Error("at least one policy ref is required");
    const artifacts = (plan.artifacts || []).map((artifact) => ({
      name: text(artifact.name || artifact.digest, "artifact name"),
      digest: text(artifact.digest, "artifact digest"),
    })).sort((a, b) => a.name.localeCompare(b.name) || a.digest.localeCompare(b.digest));
    const grants = {
      network: strings(plan.grants?.network),
      services: strings(plan.grants?.services),
      secrets: strings(plan.grants?.secrets),
    };
    const body = {
      schema: CONTRACT_SCHEMA,
      adapterSchema: SCHEMA,
      workloadId: plan.workloadId,
      holotrade: {
        planId: plan.id,
        planDigest: plan.digest,
        owner: plan.owner,
        evidenceRefs: strings(plan.evidenceRefs),
        evidencePolicy: plan.evidencePolicy || E.POLICY.DEMO,
      },
      artifacts,
      authority: grants,
      admission: {
        nonce: plan.nonce,
        validFrom: plan.validFrom,
        validUntil: plan.validUntil,
        policyRefs,
        seccompTier: options.seccompTier || seccompTier(plan),
        auditChainSigningRequired: options.auditChainSigningRequired !== false,
      },
      resources: {
        requestedSeconds: plan.requestedSeconds,
        nodeCount: plan.nodeCount,
        maxPricePerNodeSecond: plan.maxPricePerNodeSecond,
      },
      invocation: canonical(options.invocation || { mode: "invoke", commandHash: null, envKeyNames: [] }),
      boundary: {
        contractCompiled: true,
        microvmLaunched: false,
        firecrackerLaunched: false,
        receiptVerified: false,
      },
    };
    return Object.freeze({ ...body, digest: E.demoDigest(body) });
  }

  function dryRunRequest(contract) {
    if (!contract || contract.schema !== CONTRACT_SCHEMA) throw new TypeError("compiled GoMicroVM contract required");
    return Object.freeze({
      command: "mvmctl run --dry-run --json",
      mode: "preflight-only",
      contractDigest: contract.digest,
      policyRefs: contract.admission.policyRefs,
      seccompTier: contract.admission.seccompTier,
      artifactDigests: contract.artifacts.map((x) => x.digest),
      redacted: true,
      boundary:
        "Request descriptor only. It intentionally does not contain secret values, raw argv, host paths, stdout, or stderr and does not execute mvmctl.",
    });
  }

  function receiptEvidence(contract, receipt, { signatureVerified = false, attestationVerified = false } = {}) {
    if (!contract || contract.schema !== CONTRACT_SCHEMA) throw new TypeError("compiled GoMicroVM contract required");
    if (!receipt || typeof receipt !== "object") throw new TypeError("receipt object required");
    const boundDigest = receipt.contractDigest || receipt.planDigest || receipt.invocation?.contractDigest || null;
    const digestMatches = boundDigest === contract.digest || boundDigest === contract.holotrade.planDigest;
    const successful = Number(receipt.exitCode ?? receipt.exit_status ?? 1) === 0;
    const verified = signatureVerified && digestMatches && successful;
    const attested = verified && attestationVerified;
    return {
      id: text(receipt.id || `gomicrovm:${contract.holotrade.planId}:${E.demoDigest(receipt).slice(5, 17)}`, "evidence id"),
      subject: `GoMicroVM receipt for ${contract.holotrade.planId}`,
      status: verified ? E.STATUS.VERIFIED : E.STATUS.UNVERIFIED,
      evidenceClass: attested ? E.EVIDENCE_CLASS.RUNTIME_ATTESTATION :
        (verified ? E.EVIDENCE_CLASS.EXTERNAL_VERIFIED : E.EVIDENCE_CLASS.MODEL_RESULT),
      scope: E.SCOPE.RUNTIME,
      claim: verified
        ? "The supplied GoMicroVM receipt signature and plan/contract binding were reported verified by the caller."
        : "A GoMicroVM-shaped receipt was supplied, but signature/binding/success verification is incomplete.",
      source: {
        adapter: SCHEMA,
        contractDigest: contract.digest,
        receiptDigest: E.demoDigest(receipt),
        digestMatches,
        successful,
        signatureVerified,
        attestationVerified,
      },
      attested,
      metadata: {
        remotelyExecuted: true,
        cryptographicReceiptVerified: verified,
        hardwareAttestationVerified: attested,
        rawReceiptExcluded: true,
      },
    };
  }

  function authoritySubset(contract, plan) {
    const subset = (candidate, ceiling) => candidate.every((x) => new Set(ceiling || []).has(x));
    return subset(contract.authority.network, plan.grants?.network || []) &&
      subset(contract.authority.services, plan.grants?.services || []) &&
      subset(contract.authority.secrets, plan.grants?.secrets || []);
  }

  const API = { SCHEMA, CONTRACT_SCHEMA, compile, dryRunRequest, receiptEvidence, authoritySubset, seccompTier };
  root.HolotradeGoMicroVM = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
