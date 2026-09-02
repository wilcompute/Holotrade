// Carrier-safe automatic recovery selection for W33-profiled deployments.
//
// Policy order is structural, not merely economic:
//   1. prefer a healthy same-carrier host and FULL_RESTORE;
//   2. only when no same-carrier target exists, permit a cross-carrier
//      NEUTRAL_CONTINUATION at a verified syscall boundary;
//   3. never silently retype a full checkpoint.
//
// Within one recovery class, lower estimated recovery cost/latency wins.

"use strict";

const D = require("./w33-passport-deployment.js");

function finiteNonnegative(x, name) {
  const n = Number(x);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be nonnegative`);
  return n;
}

function normalizeCandidate(row) {
  if (!row || !row.profile || !row.nodeId) throw new TypeError("candidate requires nodeId and W33 profile");
  return Object.freeze({
    nodeId: String(row.nodeId),
    profile: row.profile,
    healthy: row.healthy !== false,
    estimatedRecoveryMs: finiteNonnegative(row.estimatedRecoveryMs ?? 0, "estimatedRecoveryMs"),
    estimatedCostUSD: finiteNonnegative(row.estimatedCostUSD ?? 0, "estimatedCostUSD"),
  });
}

function score(row) {
  // Latency dominates at millisecond scale; USD is deterministic tiebreak.
  return row.estimatedRecoveryMs + row.estimatedCostUSD * 1000;
}

function planRecovery({
  sourcePassport,
  candidates,
  neutralStateDigest = null,
  safePoint = null,
}) {
  if (!sourcePassport || sourcePassport.schema !== D.SCHEMA) {
    return Object.freeze({ ok: false, code: "SOURCE_PASSPORT_INVALID" });
  }
  const rows = (candidates || []).map(normalizeCandidate).filter((x) => x.healthy);

  const same = rows
    .filter((x) => x.profile.machineType === sourcePassport.machineType &&
                   x.profile.logicalDimension === sourcePassport.logicalDimension)
    .map((x) => ({ ...x, gate: D.checkpointAdmission({
      sourcePassport,
      targetProfile: x.profile,
      kind: D.CHECKPOINT.FULL_RESTORE,
    }) }))
    .filter((x) => x.gate.ok)
    .sort((a, b) => score(a) - score(b) || a.nodeId.localeCompare(b.nodeId));

  if (same.length) {
    const best = same[0];
    return Object.freeze({
      ok: true,
      mode: D.CHECKPOINT.FULL_RESTORE,
      nodeId: best.nodeId,
      targetMachineType: best.profile.machineType,
      targetLogicalDimension: best.profile.logicalDimension,
      startsNewMachineIdentity: false,
      estimatedRecoveryMs: best.estimatedRecoveryMs,
      estimatedCostUSD: best.estimatedCostUSD,
      reason: "same-carrier full checkpoint recovery preferred",
    });
  }

  const cross = rows
    .map((x) => ({ ...x, gate: D.checkpointAdmission({
      sourcePassport,
      targetProfile: x.profile,
      kind: D.CHECKPOINT.NEUTRAL_CONTINUATION,
      safePoint,
      neutralStateDigest,
    }) }))
    .filter((x) => x.gate.ok)
    .sort((a, b) => score(a) - score(b) || a.nodeId.localeCompare(b.nodeId));

  if (cross.length) {
    const best = cross[0];
    return Object.freeze({
      ok: true,
      mode: D.CHECKPOINT.NEUTRAL_CONTINUATION,
      nodeId: best.nodeId,
      targetMachineType: best.profile.machineType,
      targetLogicalDimension: best.profile.logicalDimension,
      startsNewMachineIdentity: best.gate.startsNewMachineIdentity === true,
      estimatedRecoveryMs: best.estimatedRecoveryMs,
      estimatedCostUSD: best.estimatedCostUSD,
      reason: "no same-carrier full-restore target; using typed neutral continuation",
    });
  }

  return Object.freeze({
    ok: false,
    code: rows.length ? "NO_ADMISSIBLE_RECOVERY_MODE" : "NO_HEALTHY_W33_TARGET",
  });
}

module.exports = { normalizeCandidate, planRecovery };
