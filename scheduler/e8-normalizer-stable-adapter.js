"use strict";

// Fail-closed plans for the two exact stable normalizer repairs.  These plans
// expose auxiliary module accounting; they are not workload routes or live
// intertwiners. The original v1 certificate remains the source for C13:C3 and
// D26; the later full-normalizer certificate supersedes only its C13:C6
// refusal with an abstract 4160-dimensional stable plan.

const crypto = require("node:crypto");
const E = require("../js/evidence.js");
const FROZEN = require("../data/e8_normalizer_stable_adapter.json");
const FullClosure = require("./e8-full-normalizer-stable-closure.js");

const PLAN_SCHEMA = "holotrade.e8-normalizer-stable-plan.v1";
const REFUSAL_SCHEMA = "holotrade.e8-normalizer-stable-refusal.v1";

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
  if (!frozen || frozen.schema !== "holotrade.e8-normalizer-stable-adapter.v1") return false;
  const { sha256: claimed, ...body } = frozen;
  if (!/^[0-9a-f]{64}$/.test(claimed || "") || sha256(body) !== claimed) return false;
  return frozen.sourceDimension === 4096 &&
    frozen.oddBranch.inducedStableDimension === 4200 &&
    frozen.d26Branch.stableDimension === 4160 &&
    frozen.d26Branch.c13FixedSector.dimension === 316 &&
    frozen.d26Branch.naturalFixedConeIsCorrectionCarrier === false &&
    frozen.fullNormalizer.compatibleStableGlueBuilt === false &&
    frozen.fullNormalizer.dispatchable === false;
}

if (!verifyFrozen()) throw new Error("invalid E8 normalizer stable-adapter certificate");

function refusal(reason) {
  const body = {
    schema: REFUSAL_SCHEMA,
    branch: "c13c6",
    group: FROZEN.fullNormalizer.group,
    accepted: false,
    dispatchable: false,
    sourceCertificateSha256: FROZEN.sha256,
    reason,
    requiredNextEvidence:
      "ONE_COMPATIBLE_C13_C6_CHAIN_LEVEL_INTERTWINER_WITH_VERIFIED_RESTRICTIONS",
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function planStableAdapter(branch) {
  if (branch === "c13c6") {
    return FullClosure.planStableClosure();
  }

  let body;
  if (branch === "c13c3") {
    body = {
      schema: PLAN_SCHEMA,
      branch,
      group: FROZEN.oddBranch.group,
      sourceDimensionEachSide: FROZEN.sourceDimension,
      stableDimensionEachSide: FROZEN.oddBranch.inducedStableDimension,
      correctionDimensionEachSide: FROZEN.oddBranch.inducedCorrectionDimensionEachSide,
      leftCorrection: FROZEN.oddBranch.leftCorrection,
      rightCorrection: FROZEN.oddBranch.rightCorrection,
      identity:
        "F2[V2] plus Ind(4*W2) is stably equivalent to H1 plus Ind(8*1) over C13:C3",
      exact: FROZEN.oddBranch.proved,
    };
  } else if (branch === "d26") {
    body = {
      schema: PLAN_SCHEMA,
      branch,
      group: FROZEN.d26Branch.group,
      sourceDimensionEachSide: FROZEN.sourceDimension,
      stableDimensionEachSide: FROZEN.d26Branch.stableDimension,
      correctionDimensionEachSide: 64,
      leftCorrection: FROZEN.d26Branch.leftCorrection,
      rightCorrection: FROZEN.d26Branch.rightCorrection,
      identity: FROZEN.d26Branch.stableIdentity,
      c13FixedSector: FROZEN.d26Branch.c13FixedSector,
      nontrivialC13Sector: FROZEN.d26Branch.nontrivialC13Sector,
      naturalFixedConeIsCorrectionCarrier:
        FROZEN.d26Branch.naturalFixedConeIsCorrectionCarrier,
      c13EquivariantTranslationExists:
        FROZEN.d26Branch.translationBoundary.c13EquivariantTranslationExists,
      exact: FROZEN.d26Branch.proved,
    };
  } else {
    throw new RangeError("branch must be c13c3, d26, or c13c6");
  }

  const plan = {
    ...body,
    sourceCertificateSha256: FROZEN.sha256,
    direct4096Bridge: false,
    compatibleFullNormalizerGlue: false,
    dispatchable: false,
    evidenceBoundary:
      "This is exact stable module accounting with external auxiliary states. It is not a direct module isomorphism, a live transport map, or dispatch authority.",
  };
  return deepFreeze({ ...plan, digest: E.demoDigest(plan) });
}

function verifyPlan(plan) {
  if (plan?.schema === FullClosure.PLAN_SCHEMA) return FullClosure.verifyPlan(plan);
  if (!plan || ![PLAN_SCHEMA, REFUSAL_SCHEMA].includes(plan.schema)) return false;
  const { digest, ...body } = plan;
  return digest === E.demoDigest(body) && plan.dispatchable === false &&
    plan.sourceCertificateSha256 === FROZEN.sha256;
}

module.exports = {
  PLAN_SCHEMA,
  REFUSAL_SCHEMA,
  verifyFrozen,
  planStableAdapter,
  verifyPlan,
};
