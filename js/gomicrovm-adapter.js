// ======================================================================
// HOLOTRADE -> GoMicroVM CONTRACT ADAPTER
//
// Compiles HoloTrade ExecutionPlans into the GoMicroVM security vocabulary:
// pinned artifacts, explicit grants, policy refs, validity/nonce, seccomp
// posture, redacted invocation metadata, and receipt evidence.
//
// v2 also reconciles an externally supplied admission snapshot against the
// contract. The adapter itself still does NOT invoke mvmctl/Firecracker or
// infer remote execution/hardware attestation from a signed receipt.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("gomicrovm-adapter requires evidence.js");

  const SCHEMA = "holotrade.gomicrovm-adapter.v2";
  const CONTRACT_SCHEMA = "holotrade.gomicrovm-execution-contract.v2";
  const SECCOMP_RANK = Object.freeze({ essential: 0, minimal: 1, standard: 2, network: 3, unrestricted: 4 });

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) throw new TypeError(`${name} must be a non-empty string`);
    return value.trim();
  }
  function canonical(value) { return JSON.parse(E.canonicalJson(value)); }
  function strings(value) { return [...new Set((value || []).map((x) => text(x, "string entry")))].sort(); }

  function seccompTier(plan) {
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
    const requestedTier = options.seccompTier || seccompTier(plan);
    if (!Object.hasOwn(SECCOMP_RANK, requestedTier)) throw new RangeError(`unsupported seccomp tier: ${requestedTier}`);
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
        seccompTier: requestedTier,
        auditChainSigningRequired: options.auditChainSigningRequired !== false,
        guestNetworkDeviceExpected: false,
        artifactReverificationRequired: true,
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
        runtimeSnapshotVerified: false,
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
        "Request descriptor only. It excludes secret values/raw argv/host paths/stdout/stderr and does not execute mvmctl.",
    });
  }

  function setEqual(a, b) {
    const aa = strings(a); const bb = strings(b);
    return aa.length === bb.length && aa.every((value, i) => value === bb[i]);
  }

  function artifactMap(rows) {
    return new Map((rows || []).map((row) => [text(row.name || row.digest, "artifact name"), text(row.digest, "artifact digest")]));
  }

  /**
   * Reconcile an externally obtained admission/runtime snapshot. A snapshot is
   * only evidence about what its producer reported; this function does not
   * authenticate the producer. Every security-sensitive mismatch fails closed.
   */
  function reconcileAdmissionSnapshot(contract, snapshot, { now = Date.now() } = {}) {
    if (!contract || contract.schema !== CONTRACT_SCHEMA) throw new TypeError("compiled GoMicroVM contract required");
    if (!snapshot || typeof snapshot !== "object") throw new TypeError("admission snapshot required");
    const blockers = [];
    const checks = {};

    checks.contractDigest = snapshot.contractDigest === contract.digest;
    if (!checks.contractDigest) blockers.push({ code: "CONTRACT_DIGEST_MISMATCH" });

    checks.nonce = snapshot.nonce === contract.admission.nonce;
    if (!checks.nonce) blockers.push({ code: "NONCE_MISMATCH" });

    checks.validityWindow = now >= contract.admission.validFrom && now <= contract.admission.validUntil;
    if (!checks.validityWindow) blockers.push({ code: "WINDOW" });

    const expectedArtifacts = artifactMap(contract.artifacts);
    const observedArtifacts = artifactMap(snapshot.artifacts || []);
    checks.artifacts = expectedArtifacts.size === observedArtifacts.size && [...expectedArtifacts].every(([name, digest]) => observedArtifacts.get(name) === digest);
    if (!checks.artifacts) blockers.push({ code: "ARTIFACT_REVERIFICATION_MISMATCH" });

    checks.networkAuthority = setEqual(snapshot.authority?.network || [], contract.authority.network);
    checks.serviceAuthority = setEqual(snapshot.authority?.services || [], contract.authority.services);
    checks.secretAuthority = setEqual(snapshot.authority?.secrets || [], contract.authority.secrets);
    if (!checks.networkAuthority || !checks.serviceAuthority || !checks.secretAuthority) blockers.push({ code: "AUTHORITY_MISMATCH" });

    checks.policyRefs = setEqual(snapshot.policyRefs || [], contract.admission.policyRefs);
    if (!checks.policyRefs) blockers.push({ code: "POLICY_REF_MISMATCH" });

    const observedTier = snapshot.seccompTier;
    checks.seccompTierKnown = Object.hasOwn(SECCOMP_RANK, observedTier);
    checks.seccompNotWeaker = checks.seccompTierKnown && SECCOMP_RANK[observedTier] <= SECCOMP_RANK[contract.admission.seccompTier];
    if (!checks.seccompNotWeaker) blockers.push({ code: "SECCOMP_WEAKENED" });

    checks.noGuestNetworkDevice = snapshot.guestNetworkDevicePresent === false;
    if (!checks.noGuestNetworkDevice) blockers.push({ code: "GUEST_NETWORK_DEVICE_PRESENT_OR_UNKNOWN" });

    checks.auditChainSigned = contract.admission.auditChainSigningRequired ? snapshot.auditChainSigned === true : true;
    if (!checks.auditChainSigned) blockers.push({ code: "AUDIT_CHAIN_UNSIGNED" });

    checks.rootfsSealed = snapshot.rootfsSealed === true;
    if (!checks.rootfsSealed) blockers.push({ code: "ROOTFS_NOT_REPORTED_SEALED" });

    const body = {
      schema: "holotrade.gomicrovm-admission-reconciliation.v1",
      contractDigest: contract.digest,
      ok: blockers.length === 0,
      checks,
      blockers,
      sourceAuthentication: "not-performed-by-adapter",
      remoteExecutionVerified: false,
      hardwareAttestationVerified: false,
      boundary:
        "Fail-closed reconciliation of a caller-supplied snapshot against the compiled contract. The snapshot must be independently authenticated before treating this result as external runtime evidence.",
    };
    return Object.freeze({ ...body, digest: E.demoDigest(body) });
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
      evidenceClass: attested ? E.EVIDENCE_CLASS.RUNTIME_ATTESTATION : (verified ? E.EVIDENCE_CLASS.EXTERNAL_VERIFIED : E.EVIDENCE_CLASS.MODEL_RESULT),
      scope: E.SCOPE.RUNTIME,
      claim: attested
        ? "The supplied GoMicroVM receipt signature, binding, successful exit, and an additional runtime-attestation check were reported verified by the caller."
        : verified
          ? "The supplied GoMicroVM receipt signature, binding, and successful exit were reported verified by the caller; no remote/hardware attestation is inferred."
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
        executionReportedByReceipt: true,
        receiptSignatureVerified: signatureVerified,
        contractBindingVerified: digestMatches,
        successfulExitReported: successful,
        cryptographicReceiptVerified: verified,
        remoteExecutionVerified: false,
        hardwareOrRuntimeAttestationVerified: attested,
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

  const API = {
    SCHEMA,
    CONTRACT_SCHEMA,
    SECCOMP_RANK,
    compile,
    dryRunRequest,
    reconcileAdmissionSnapshot,
    receiptEvidence,
    authoritySubset,
    seccompTier,
  };
  root.HolotradeGoMicroVM = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
