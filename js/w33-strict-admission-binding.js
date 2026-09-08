"use strict";

// Verify the cross-language-stable projection of W33's strict joint-admission
// handoff. The full W33 handoff retains floating diagnostic policy values whose
// lexical JSON forms are language-dependent (e.g. 0.0 versus 0). W33 therefore
// exports this projection using only strings, natural numbers and string arrays;
// the same sorted compact JSON convention is byte-stable in Python and JS.
//
// This binding is stronger than the compact execution policy: it commits the
// full jointPlanDigest and the baseline-aware exact retained-union delta.

const crypto = require("node:crypto");
const J = require("./w33-joint-admission-policy.js");

const SCHEMA = "w33.holotrade-strict-binding.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }

function verifyStrictBinding(raw, rawPolicy, expected = null) {
  if (!raw || typeof raw !== "object" || raw.schema !== SCHEMA) throw new TypeError("strict W33 admission binding required");
  const policy = J.verifyPolicy(rawPolicy, expected);
  for (const name of [
    "executionPolicyDigest", "handoffDigest", "continuationRoot", "processId",
    "problemRoot", "jointPlanDigest", "strategyDigest", "placementDigest",
    "snapshotProblemRoot", "strictBindingDigest",
  ]) if (!isDigest(raw[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  for (const name of [
    "generation", "baselineRetainedUnionBytes", "postAdmissionRetainedUnionBytes",
    "retainedUnionDeltaBytes", "checkpointPeakBytes", "combinedPolicyBytes", "capacityBytes",
  ]) natural(raw[name], name);
  if (!Array.isArray(raw.selectedSnapshotIds) || !raw.selectedSnapshotIds.every((x) => typeof x === "string" && x.length)) {
    throw new TypeError("selectedSnapshotIds must be an array of nonempty strings");
  }
  if (new Set(raw.selectedSnapshotIds).size !== raw.selectedSnapshotIds.length) throw new Error("selectedSnapshotIds must be unique");
  const body = { ...raw }; delete body.strictBindingDigest;
  if (sha256(body) !== raw.strictBindingDigest) throw new Error("strict W33 admission binding digest mismatch");
  if (raw.executionPolicyDigest !== policy.executionPolicyDigest) throw new Error("strict binding execution policy mismatch");
  if (raw.continuationRoot !== policy.continuationRoot || raw.processId !== policy.processId || raw.generation !== policy.generation) throw new Error("strict binding continuation tuple mismatch");
  if (raw.problemRoot !== policy.problemRoot || raw.strategyDigest !== policy.strategyDigest || raw.snapshotProblemRoot !== policy.snapshotProblemRoot) throw new Error("strict binding policy provenance mismatch");
  if (raw.postAdmissionRetainedUnionBytes !== policy.snapshotPayloadBytes) throw new Error("strict post-admission retained total disagrees with policy snapshot payload");
  if (raw.checkpointPeakBytes !== policy.checkpointPeakBytes || raw.combinedPolicyBytes !== policy.combinedBytes || raw.capacityBytes !== policy.capacityBytes) throw new Error("strict byte accounts disagree with policy");
  if (raw.retainedUnionDeltaBytes !== raw.postAdmissionRetainedUnionBytes - raw.baselineRetainedUnionBytes) throw new Error("strict retained-union delta is not post minus baseline");
  if (raw.retainedUnionDeltaBytes > raw.postAdmissionRetainedUnionBytes) throw new Error("strict retained-union delta exceeds retained total");
  return Object.freeze({ ...body, strictBindingDigest: raw.strictBindingDigest, executionPolicy: policy });
}

module.exports = { SCHEMA, stable, sha256, isDigest, verifyStrictBinding };
