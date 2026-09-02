// Carrier-safe automatic recovery selection for W33-profiled deployments.
//
// Structural policy order:
//   1. FULL_RESTORE only to the same construction profile *and* the exact
//      capability epoch/revocation root pinned by the checkpoint;
//   2. otherwise permit a NEUTRAL_CONTINUATION only at a verified syscall
//      boundary and mint a fresh passport under the target's current authority;
//   3. never silently retype or re-authorize an old checkpoint.

"use strict";

const D = require("./w33-passport-deployment.js");

function finiteNonnegative(x, name) {
  const n = Number(x);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be nonnegative`);
  return n;
}

function normalizeCandidate(row) {
  if (!row || !row.profile || !row.nodeId) throw new TypeError("candidate requires nodeId and W33 profile");
  if (!Number.isSafeInteger(row.capabilityEpoch) || row.capabilityEpoch < 0) {
    throw new TypeError("candidate requires current capabilityEpoch");
  }
  if (!D.isDigest(row.revocationRoot)) throw new TypeError("candidate requires current revocationRoot");
  return Object.freeze({
    nodeId: String(row.nodeId),
    profile: row.profile,
    capabilityEpoch: row.capabilityEpoch,
    revocationRoot: row.revocationRoot,
    healthy: row.healthy !== false,
    estimatedRecoveryMs: finiteNonnegative(row.estimatedRecoveryMs ?? 0, "estimatedRecoveryMs"),
    estimatedCostUSD: finiteNonnegative(row.estimatedCostUSD ?? 0, "estimatedCostUSD"),
  });
}

function score(row) {
  return row.estimatedRecoveryMs + row.estimatedCostUSD * 1000;
}

function sameAuthority(sourcePassport, candidate) {
  return candidate.capabilityEpoch === sourcePassport.capabilityEpoch &&
    candidate.revocationRoot === sourcePassport.revocationRoot;
}

function planRecovery({ sourcePassport, candidates, neutralStateDigest = null, safePoint = null }) {
  if (!sourcePassport || sourcePassport.schema !== D.SCHEMA) {
    return Object.freeze({ ok: false, code: "SOURCE_PASSPORT_INVALID" });
  }
  const rows = (candidates || []).map(normalizeCandidate).filter((x) => x.healthy);

  const same = rows
    .map((x) => ({ ...x, gate: D.checkpointAdmission({
      sourcePassport,
      targetProfile: x.profile,
      kind: D.CHECKPOINT.FULL_RESTORE,
    }) }))
    .filter((x) => x.gate.ok && sameAuthority(sourcePassport, x))
    .sort((a, b) => score(a) - score(b) || a.nodeId.localeCompare(b.nodeId));

  if (same.length) {
    const best = same[0];
    return Object.freeze({
      ok: true,
      mode: D.CHECKPOINT.FULL_RESTORE,
      nodeId: best.nodeId,
      targetMachineType: best.profile.machineType,
      targetLogicalDimension: best.profile.logicalDimension,
      targetCapabilityEpoch: best.capabilityEpoch,
      targetRevocationRoot: best.revocationRoot,
      startsNewMachineIdentity: false,
      requiresPassportRemint: false,
      estimatedRecoveryMs: best.estimatedRecoveryMs,
      estimatedCostUSD: best.estimatedCostUSD,
      reason: "same-profile same-authority full checkpoint recovery preferred",
    });
  }

  const cross = rows
    .map((x) => ({
      ...x,
      authorityChanged: !sameAuthority(sourcePassport, x),
      gate: D.checkpointAdmission({
        sourcePassport,
        targetProfile: x.profile,
        kind: D.CHECKPOINT.NEUTRAL_CONTINUATION,
        safePoint,
        neutralStateDigest,
      }),
    }))
    .filter((x) => x.gate.ok)
    .sort((a, b) => score(a) - score(b) || a.nodeId.localeCompare(b.nodeId));

  if (cross.length) {
    const best = cross[0];
    const remint = best.authorityChanged || best.gate.startsNewMachineIdentity === true;
    return Object.freeze({
      ok: true,
      mode: D.CHECKPOINT.NEUTRAL_CONTINUATION,
      nodeId: best.nodeId,
      targetMachineType: best.profile.machineType,
      targetLogicalDimension: best.profile.logicalDimension,
      targetCapabilityEpoch: best.capabilityEpoch,
      targetRevocationRoot: best.revocationRoot,
      startsNewMachineIdentity: remint,
      requiresPassportRemint: remint,
      estimatedRecoveryMs: best.estimatedRecoveryMs,
      estimatedCostUSD: best.estimatedCostUSD,
      reason: best.authorityChanged
        ? "checkpoint authority is stale on target; use typed neutral continuation and fresh passport"
        : "no admissible full-restore target; use typed neutral continuation",
    });
  }

  return Object.freeze({
    ok: false,
    code: rows.length ? "NO_ADMISSIBLE_RECOVERY_MODE" : "NO_HEALTHY_W33_TARGET",
  });
}

function materializeRecoveryPassport({
  recovery,
  sourcePassport,
  neutralStateDigest,
  plan,
  profile,
  vm,
  contract,
  targetState,
}) {
  if (!recovery || !recovery.ok || recovery.mode !== D.CHECKPOINT.NEUTRAL_CONTINUATION) {
    throw new Error("neutral-continuation recovery plan required");
  }
  if (!D.isDigest(neutralStateDigest)) throw new TypeError("neutralStateDigest required");
  const required = ["memoryCapabilityDigest", "historyRoot", "waitForRoot", "cancellationRoot", "asyncScheduleRoot", "gcRegistryRoot"];
  for (const key of required) {
    if (!targetState || !D.isDigest(targetState[key])) throw new TypeError(`targetState.${key} required`);
  }
  if (recovery.targetCapabilityEpoch !== targetState.capabilityEpoch ||
      recovery.targetRevocationRoot !== targetState.revocationRoot) {
    throw new Error("target authority changed after recovery planning");
  }

  return D.bindPassport({
    plan,
    profile,
    vm,
    contract,
    guestImage: sourcePassport.guestImage,
    memoryRoot: neutralStateDigest,
    memoryCapabilityDigest: targetState.memoryCapabilityDigest,
    componentLinkDigest: sourcePassport.componentLinkDigest,
    packetRefinementDigest: sourcePassport.packetRefinementDigest,
    historyRoot: targetState.historyRoot,
    capabilityEpoch: targetState.capabilityEpoch,
    revocationRoot: targetState.revocationRoot,
    waitForRoot: targetState.waitForRoot,
    cancellationRoot: targetState.cancellationRoot,
    asyncScheduleRoot: targetState.asyncScheduleRoot,
    gcRegistryRoot: targetState.gcRegistryRoot,
    erasurePolicy: sourcePassport.erasurePolicy,
    magicBudget: sourcePassport.magicBudget,
  });
}

module.exports = { normalizeCandidate, sameAuthority, planRecovery, materializeRecoveryPassport };
