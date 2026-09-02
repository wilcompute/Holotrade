// End-to-end receipt binding for the immutable W33 carrier fork.
//
// The generic delivery-receipt payload already signs its metadata field.  This
// module defines the W33 metadata that must be placed there and independently
// verifies it against the plan, immutable profile, launched VM identity, and
// (when present) compiled GoMicroVM deployment digest.  A receipt from one
// carrier therefore cannot be relabelled as the other carrier without changing
// signed payload bytes and failing this binding check.

"use strict";

const crypto = require("node:crypto");
const P = require("./w33-execution-profile.js");

const SCHEMA = "holotrade.w33-receipt-binding.v1";

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

function core(plan, profile, vm, contract = null) {
  if (!P.verify(profile, plan)) throw new Error("invalid W33 profile for receipt binding");
  if (!vm || vm.w33ProfileDigest !== profile.digest || vm.w33MachineType !== profile.machineType ||
      vm.w33LogicalDimension !== profile.logicalDimension) {
    throw new Error("VM W33 identity does not match immutable profile");
  }
  if (contract) {
    if (!contract.w33 || contract.w33.profileDigest !== profile.digest ||
        contract.w33.machineType !== profile.machineType ||
        contract.w33.logicalDimension !== profile.logicalDimension ||
        contract.w33.runtimeRetype !== "FORBIDDEN" || !contract.deploymentDigest) {
      throw new Error("compiled deployment does not match immutable W33 profile");
    }
  }
  return {
    schema: SCHEMA,
    planDigest: plan.digest,
    profileDigest: profile.digest,
    machineType: profile.machineType,
    logicalDimension: profile.logicalDimension,
    vmId: String(vm.id),
    deploymentDigest: contract ? contract.deploymentDigest : null,
    runtimeRetype: "FORBIDDEN",
    symmetryNamespaces: {
      cliffordLift: profile.symmetryNamespaces.cliffordLift,
      projectiveWeyl: profile.symmetryNamespaces.projectiveWeyl,
    },
  };
}

function bindReceiptMetadata(plan, profile, vm, contract = null) {
  const payload = core(plan, profile, vm, contract);
  return Object.freeze({ ...payload, bindingDigest: sha256(payload) });
}

function verifyReceiptMetadata(binding, plan, profile, vm, contract = null) {
  if (!binding || typeof binding !== "object") return false;
  let expected;
  try { expected = bindReceiptMetadata(plan, profile, vm, contract); }
  catch (_) { return false; }
  return stable(binding) === stable(expected);
}

function attachToReceiptMetadata(metadata, plan, profile, vm, contract = null) {
  return Object.freeze({ ...(metadata || {}), w33: bindReceiptMetadata(plan, profile, vm, contract) });
}

module.exports = {
  SCHEMA,
  bindReceiptMetadata,
  verifyReceiptMetadata,
  attachToReceiptMetadata,
};
