"use strict";

const crypto = require("node:crypto");

const SCHEMA = "w33.attested-accelerator-macro.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value) { return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`; }
function isDigest(value) { return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value); }
function natural(value, name) { if (!Number.isSafeInteger(value) || value < 0) throw new RangeError(`${name} must be a natural number`); return value; }

function verifyAcceleratorCertificate(raw, expected = null) {
  if (!raw || typeof raw !== "object" || raw.schema !== SCHEMA) throw new TypeError("W33 accelerator certificate required");
  for (const name of [
    "parentContinuationRoot", "childContinuationRoot", "processId",
    "receiptChainDigest", "continuationChainDigest", "symplecticFrameDigest",
    "steinbergBasisDigest", "actionTableDigest", "sequentialGroupEndpointDigest",
    "steinbergActionDigest", "acceleratorCertificateDigest",
  ]) if (!isDigest(raw[name])) throw new TypeError(`${name} must be a sha256 content identity`);
  for (const name of ["generationBefore", "generationAfter", "windowStart", "windowWidth", "naiveTransvections", "executableTransvections"]) natural(raw[name], name);
  if (!raw.windowWidth) throw new RangeError("windowWidth must be positive");
  if (raw.generationAfter - raw.generationBefore !== raw.windowWidth) throw new Error("accelerator generation span must equal windowWidth");
  if (raw.executableTransvections > raw.naiveTransvections) throw new Error("accelerator cannot expand executable transvection count under this certificate schema");
  if (!Array.isArray(raw.executableTimeOrder) || raw.executableTimeOrder.length !== raw.executableTransvections) throw new Error("executableTimeOrder length mismatch");
  for (const op of raw.executableTimeOrder) {
    if (!Array.isArray(op) || op.length !== 2 || !Number.isInteger(op[0]) || op[0] < 0 || op[0] >= 40 || ![1, 2].includes(op[1])) throw new Error("invalid accelerator transvection opcode");
  }
  if (raw.machineType !== "w33.circuit216.steinberg81") throw new Error("unexpected accelerator machine type");
  if (typeof raw.calibrationEpoch !== "string" || !raw.calibrationEpoch.length) throw new TypeError("calibrationEpoch required");
  if (raw.physicalCalibrationEvidenceDigest != null && !isDigest(raw.physicalCalibrationEvidenceDigest)) throw new TypeError("physicalCalibrationEvidenceDigest must be null or sha256 identity");
  if (raw.evidenceClass !== "software-finite-control-equivalence") throw new Error("unsupported accelerator evidence class");
  const body = { ...raw }; delete body.acceleratorCertificateDigest;
  if (sha256(body) !== raw.acceleratorCertificateDigest) throw new Error("accelerator certificate digest mismatch");
  if (expected) {
    if (expected.continuationRoot != null && raw.parentContinuationRoot !== expected.continuationRoot) throw new Error("accelerator parent continuation mismatch");
    if (expected.processId != null && raw.processId !== expected.processId) throw new Error("accelerator process identity mismatch");
    if (expected.generation != null && raw.generationBefore !== expected.generation) throw new Error("accelerator generation mismatch");
    if (expected.machineType != null && raw.machineType !== expected.machineType) throw new Error("accelerator machine type mismatch");
  }
  return Object.freeze({ ...body, acceleratorCertificateDigest: raw.acceleratorCertificateDigest });
}

module.exports = { SCHEMA, stable, sha256, isDigest, verifyAcceleratorCertificate };
