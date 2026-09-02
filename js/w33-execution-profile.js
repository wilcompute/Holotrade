// W33 construction-time machine-type binding for HoloTrade execution plans.
//
// This layer exists because current finite-geometry evidence distinguishes two
// inequivalent 216-state carriers over one 36-state base.  They are different
// machines, not gauge choices, so deployment identity must commit to the
// carrier before execution begins.
//
// The core ExecutionPlan remains generic.  A W33ExecutionProfile wraps one
// already-verified plan and adds the immutable W33 machine type to a SHA-256
// deployment commitment.  Rebinding is not mutation: it creates a different
// profile with a different digest.
//
// Honest boundary: the current scheduler does not yet consume this profile at
// admission.  This module closes the identity/serialization layer; fail-closed
// scheduler enforcement is the next systems step.

"use strict";

const crypto = require("node:crypto");

const MACHINE_TYPE = Object.freeze({
  CIRCUIT_ST81: "w33.circuit216.steinberg81",
  PAIR_ST64: "w33.paired-hemisystem216.steinberg64",
});

const LOGICAL_DIMENSION = Object.freeze({
  [MACHINE_TYPE.CIRCUIT_ST81]: 81,
  [MACHINE_TYPE.PAIR_ST64]: 64,
});

const SYMMETRY_NAMESPACE = Object.freeze({
  CLIFFORD_LIFT: "Sp(4,3)-clifford-lift",
  PROJECTIVE_WEYL: "PGSp(4,3)-projective-weyl",
});

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

function validateMachineType(machineType) {
  if (!Object.prototype.hasOwnProperty.call(LOGICAL_DIMENSION, machineType)) {
    throw new TypeError(`unknown W33 machine type: ${machineType}`);
  }
  return LOGICAL_DIMENSION[machineType];
}

function payloadFor(plan, machineType) {
  if (!plan || typeof plan !== "object" || !plan.digest) {
    throw new TypeError("verified ExecutionPlan required");
  }
  if (typeof plan.verify === "function" && !plan.verify()) {
    throw new Error("refusing to bind an ExecutionPlan with an invalid integrity seal");
  }
  const logicalDimension = validateMachineType(machineType);
  return {
    schema: "holotrade.w33-execution-profile.v1",
    planDigest: plan.digest,
    machineType,
    logicalDimension,
    symmetryNamespaces: {
      cliffordLift: SYMMETRY_NAMESPACE.CLIFFORD_LIFT,
      projectiveWeyl: SYMMETRY_NAMESPACE.PROJECTIVE_WEYL,
      sameOrderNotSameNamespace: true,
      order: 51840,
    },
    runtimeRetype: "FORBIDDEN",
  };
}

function bind(plan, machineType) {
  const payload = payloadFor(plan, machineType);
  return Object.freeze({ ...payload, digest: sha256(payload) });
}

function verify(profile, plan) {
  if (!profile || typeof profile !== "object") return false;
  if (!plan || profile.planDigest !== plan.digest) return false;
  if (typeof plan.verify === "function" && !plan.verify()) return false;
  let payload;
  try {
    payload = payloadFor(plan, profile.machineType);
  } catch (_) {
    return false;
  }
  return (
    profile.logicalDimension === payload.logicalDimension &&
    profile.runtimeRetype === "FORBIDDEN" &&
    profile.digest === sha256(payload)
  );
}

module.exports = {
  MACHINE_TYPE,
  LOGICAL_DIMENSION,
  SYMMETRY_NAMESPACE,
  bind,
  verify,
};
