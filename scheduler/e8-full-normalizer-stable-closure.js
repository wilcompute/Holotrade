"use strict";

const crypto = require("node:crypto");
const E = require("../js/evidence.js");
const FROZEN = require("../data/e8_full_normalizer_stable_closure.json");

const PLAN_SCHEMA = "holotrade.e8-full-normalizer-stable-plan.v1";

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) =>
      `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

function verifyFrozen(frozen = FROZEN) {
  if (!frozen || frozen.schema !== "holotrade.e8-full-normalizer-stable-closure.v1") return false;
  const { sha256: claimed, ...body } = frozen;
  return /^[0-9a-f]{64}$/.test(claimed || "") && sha256(body) === claimed &&
    frozen.stableClosure.stableDimensionEachSide === 4160 &&
    frozen.stableClosure.abstractModuleIsomorphismProved === true &&
    frozen.stableClosure.chainLevelIntertwinerBuilt === false &&
    frozen.stableClosure.dispatchable === false;
}

if (!verifyFrozen()) throw new Error("invalid full-normalizer stable-closure certificate");

function planStableClosure() {
  const body = {
    schema: PLAN_SCHEMA,
    branch: "c13c6",
    group: FROZEN.group.name,
    sourceDimensionEachSide: FROZEN.sourceDecomposition.dimensionEach,
    correctionDimensionEachSide: FROZEN.correction.left.dimension,
    stableDimensionEachSide: FROZEN.stableClosure.stableDimensionEachSide,
    leftCorrection: FROZEN.correction.left,
    rightCorrection: FROZEN.correction.right,
    commonStableDecomposition: FROZEN.correction.commonStableDecomposition,
    restrictionCompatibility: {
      c2: FROZEN.correction.c2Restriction,
      c3: FROZEN.correction.c3Restriction,
    },
    abstractModuleIsomorphismProved: true,
    chainLevelIntertwinerBuilt: false,
    dispatchable: false,
    requiredNextEvidence: "EXPLICIT_CHAIN_LEVEL_4160_INTERTWINER",
    sourceCertificateSha256: FROZEN.sha256,
    evidenceBoundary: FROZEN.evidenceBoundary,
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function verifyPlan(plan) {
  if (!plan || plan.schema !== PLAN_SCHEMA || plan.dispatchable !== false) return false;
  const { digest, ...body } = plan;
  return digest === E.demoDigest(body) &&
    plan.sourceCertificateSha256 === FROZEN.sha256 &&
    plan.stableDimensionEachSide === 4160;
}

module.exports = { PLAN_SCHEMA, verifyFrozen, planStableClosure, verifyPlan };
