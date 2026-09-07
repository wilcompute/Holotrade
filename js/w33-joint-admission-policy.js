"use strict";

// Verify the compact checkpoint/snapshot policy certificate exported by W33.
//
// The execution-policy digest is intentionally separate from continuation
// identity. A single immutable continuation may be replayed under different
// checkpoint/snapshot policies; pricing and hardware attestation must therefore
// bind the exact policy selected for this execution.

const crypto = require("node:crypto");

const SCHEMA = "w33.holotrade-joint-admission-policy.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;
}

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function natural(value, name) {
  if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`);
  return value;
}

function policyBody(raw) {
  if (!raw || typeof raw !== "object" || raw.schema !== SCHEMA) throw new TypeError("W33 joint admission policy required");
  for (const name of [
    "problemRoot", "continuationRoot", "processId", "strategyDigest",
    "snapshotProblemRoot", "placementDigest",
  ]) {
    if (!isDigest(raw[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  }
  natural(raw.generation, "generation");
  for (const name of ["checkpointPeakBytes", "snapshotPayloadBytes", "combinedBytes", "capacityBytes"]) {
    natural(raw[name], name);
  }
  if (raw.checkpointPeakBytes + raw.snapshotPayloadBytes !== raw.combinedBytes) {
    throw new Error("joint policy component byte accounts do not sum to combinedBytes");
  }
  if (raw.combinedBytes > raw.capacityBytes) throw new Error("joint policy exceeds its certified capacity");
  return Object.freeze({
    schema: SCHEMA,
    problemRoot: raw.problemRoot,
    continuationRoot: raw.continuationRoot,
    processId: raw.processId,
    generation: raw.generation,
    strategyDigest: raw.strategyDigest,
    checkpointPeakBytes: raw.checkpointPeakBytes,
    snapshotPayloadBytes: raw.snapshotPayloadBytes,
    combinedBytes: raw.combinedBytes,
    capacityBytes: raw.capacityBytes,
    snapshotProblemRoot: raw.snapshotProblemRoot,
    placementDigest: raw.placementDigest,
  });
}

function verifyPolicy(raw, expected = null) {
  const body = policyBody(raw);
  const executionPolicyDigest = sha256(body);
  if (!isDigest(raw.executionPolicyDigest) || raw.executionPolicyDigest !== executionPolicyDigest) {
    throw new Error("joint execution policy digest mismatch");
  }
  if (raw.status != null && raw.status !== "PASS") throw new Error("W33 joint policy did not pass its source certificate");
  if (expected) {
    if (body.continuationRoot !== expected.continuationRoot) throw new Error("joint policy continuation mismatch");
    if (body.processId !== expected.processId) throw new Error("joint policy process mismatch");
    if (body.generation !== expected.generation) throw new Error("joint policy generation mismatch");
  }
  return Object.freeze({ ...body, executionPolicyDigest });
}

module.exports = {
  SCHEMA,
  stable,
  sha256,
  isDigest,
  policyBody,
  verifyPolicy,
};
