// W33 execution-passport and checkpoint policy for Holotrade deployment.
//
// Version 2 mirrors the W33 runtime control-plane identity as well as the
// machine/profile identity.  A signed receipt can therefore commit the exact
// capability epoch/revocation state, wait-for graph, cancellation decision,
// async wake schedule, and temporal-GC registry used by an execution.
//
// Migration law:
//   FULL_RESTORE          -> same construction-time carrier/profile only
//   NEUTRAL_CONTINUATION  -> may change profile/carrier only at SYSCALL_BOUNDARY
//                            and carries a neutral-state content digest

"use strict";

const crypto = require("node:crypto");
const P = require("./w33-execution-profile.js");
const R = require("./w33-profiled-receipt.js");

const SCHEMA = "holotrade.w33-execution-passport.v2";
const CHECKPOINT = Object.freeze({
  FULL_RESTORE: "FULL_RESTORE",
  NEUTRAL_CONTINUATION: "NEUTRAL_CONTINUATION",
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

function isDigest(value) {
  return typeof value === "string" && /^sha256:[0-9a-f]{64}$/.test(value);
}

function assertContext(plan, profile, vm, contract = null) {
  if (!P.verify(profile, plan)) throw new Error("invalid W33 profile for execution passport");
  if (!vm || vm.w33ProfileDigest !== profile.digest || vm.w33MachineType !== profile.machineType ||
      vm.w33LogicalDimension !== profile.logicalDimension) {
    throw new Error("VM W33 identity does not match passport profile");
  }
  if (contract) {
    if (!contract.w33 || contract.w33.profileDigest !== profile.digest ||
        contract.w33.machineType !== profile.machineType ||
        contract.w33.logicalDimension !== profile.logicalDimension ||
        contract.w33.runtimeRetype !== "FORBIDDEN" || !contract.deploymentDigest) {
      throw new Error("compiled deployment does not match passport profile");
    }
  }
}

function bindPassport({
  plan,
  profile,
  vm,
  contract = null,
  guestImage,
  memoryRoot,
  memoryCapabilityDigest,
  componentLinkDigest,
  packetRefinementDigest,
  historyRoot,
  capabilityEpoch,
  revocationRoot,
  waitForRoot,
  cancellationRoot,
  asyncScheduleRoot,
  gcRegistryRoot,
  erasurePolicy = "EXPLICIT_DISCARD_ONLY",
  magicBudget = 0,
}) {
  assertContext(plan, profile, vm, contract);
  for (const [name, value] of Object.entries({
    guestImage,
    memoryRoot,
    memoryCapabilityDigest,
    componentLinkDigest,
    packetRefinementDigest,
    historyRoot,
    revocationRoot,
    waitForRoot,
    cancellationRoot,
    asyncScheduleRoot,
    gcRegistryRoot,
  })) {
    if (!isDigest(value)) throw new TypeError(`${name} must be sha256 content identity`);
  }
  if (!Number.isSafeInteger(capabilityEpoch) || capabilityEpoch < 0) {
    throw new RangeError("capabilityEpoch must be nonnegative integer");
  }
  if (!Number.isSafeInteger(magicBudget) || magicBudget < 0) throw new RangeError("magicBudget must be nonnegative integer");
  if (Number.isSafeInteger(plan.magicBudget) && magicBudget > plan.magicBudget) {
    throw new RangeError("passport magic budget exceeds signed execution plan budget");
  }
  if (!["EXPLICIT_DISCARD_ONLY", "RETAIN_OR_UNCOMPUTE"].includes(erasurePolicy)) {
    throw new TypeError("unknown erasure policy");
  }
  if (profile.symmetryNamespaces.cliffordLift === profile.symmetryNamespaces.projectiveWeyl) {
    throw new Error("W33 symmetry namespaces alias");
  }
  const core = {
    schema: SCHEMA,
    planDigest: plan.digest,
    profileDigest: profile.digest,
    machineType: profile.machineType,
    logicalDimension: profile.logicalDimension,
    vmId: String(vm.id),
    deploymentDigest: contract ? contract.deploymentDigest : null,
    guestImage,
    memoryRoot,
    memoryCapabilityDigest,
    componentLinkDigest,
    packetRefinementDigest,
    historyRoot,
    capabilityEpoch,
    revocationRoot,
    waitForRoot,
    cancellationRoot,
    asyncScheduleRoot,
    gcRegistryRoot,
    erasurePolicy,
    magicBudget,
    runtimeRetype: "FORBIDDEN",
    symmetryNamespaces: {
      cliffordLift: profile.symmetryNamespaces.cliffordLift,
      projectiveWeyl: profile.symmetryNamespaces.projectiveWeyl,
    },
  };
  return Object.freeze({ ...core, passportId: sha256(core) });
}

function verifyPassport(passport, context) {
  if (!passport || typeof passport !== "object") return false;
  try {
    const expected = bindPassport(context);
    return stable(expected) === stable(passport);
  } catch (_) {
    return false;
  }
}

function validatePassportIdentity(passport, plan, profile, vm, contract = null) {
  if (!passport || passport.schema !== SCHEMA) return false;
  try {
    const expected = bindPassport({
      plan,
      profile,
      vm,
      contract,
      guestImage: passport.guestImage,
      memoryRoot: passport.memoryRoot,
      memoryCapabilityDigest: passport.memoryCapabilityDigest,
      componentLinkDigest: passport.componentLinkDigest,
      packetRefinementDigest: passport.packetRefinementDigest,
      historyRoot: passport.historyRoot,
      capabilityEpoch: passport.capabilityEpoch,
      revocationRoot: passport.revocationRoot,
      waitForRoot: passport.waitForRoot,
      cancellationRoot: passport.cancellationRoot,
      asyncScheduleRoot: passport.asyncScheduleRoot,
      gcRegistryRoot: passport.gcRegistryRoot,
      erasurePolicy: passport.erasurePolicy,
      magicBudget: passport.magicBudget,
    });
    return stable(expected) === stable(passport);
  } catch (_) {
    return false;
  }
}

function checkpointAdmission({ sourcePassport, targetProfile, kind, safePoint = null, neutralStateDigest = null }) {
  if (!sourcePassport || sourcePassport.schema !== SCHEMA || !targetProfile) {
    return { ok: false, code: "CHECKPOINT_CONTEXT_INVALID" };
  }
  const sameCarrierShape = sourcePassport.machineType === targetProfile.machineType &&
    sourcePassport.logicalDimension === targetProfile.logicalDimension;
  const sameConstructionProfile = sameCarrierShape &&
    typeof targetProfile.digest === "string" &&
    sourcePassport.profileDigest === targetProfile.digest;

  if (kind === CHECKPOINT.FULL_RESTORE) {
    if (sameConstructionProfile) return { ok: true, code: "FULL_RESTORE_SAME_PROFILE" };
    return sameCarrierShape
      ? { ok: false, code: "PROFILE_DRIFT_FULL_RESTORE_FORBIDDEN" }
      : { ok: false, code: "CROSS_CARRIER_FULL_RESTORE_FORBIDDEN" };
  }

  if (kind === CHECKPOINT.NEUTRAL_CONTINUATION) {
    if (safePoint !== "SYSCALL_BOUNDARY") return { ok: false, code: "NEUTRAL_SAFEPOINT_REQUIRED" };
    if (!isDigest(neutralStateDigest)) return { ok: false, code: "NEUTRAL_STATE_DIGEST_REQUIRED" };
    return {
      ok: true,
      code: sameConstructionProfile
        ? "NEUTRAL_CONTINUATION_SAME_PROFILE"
        : (sameCarrierShape ? "NEUTRAL_CONTINUATION_PROFILE_DRIFT" : "NEUTRAL_CONTINUATION_CROSS_CARRIER"),
      startsNewMachineIdentity: !sameConstructionProfile,
      runtimeRetype: "FORBIDDEN",
    };
  }
  return { ok: false, code: "UNKNOWN_CHECKPOINT_KIND" };
}

function attachPassportReceiptMetadata(metadata, plan, profile, vm, contract, passport, historyBinding = null) {
  const base = R.attachToReceiptMetadata(metadata, plan, profile, vm, contract);
  if (!validatePassportIdentity(passport, plan, profile, vm, contract)) {
    throw new Error("execution passport identity does not verify against signed W33 receipt context");
  }
  const passportBinding = {
    schema: "holotrade.w33-passport-receipt-binding.v2",
    passportId: passport.passportId,
    memoryRoot: passport.memoryRoot,
    componentLinkDigest: passport.componentLinkDigest,
    packetRefinementDigest: passport.packetRefinementDigest,
    historyRoot: passport.historyRoot,
    capabilityEpoch: passport.capabilityEpoch,
    revocationRoot: passport.revocationRoot,
    waitForRoot: passport.waitForRoot,
    cancellationRoot: passport.cancellationRoot,
    asyncScheduleRoot: passport.asyncScheduleRoot,
    gcRegistryRoot: passport.gcRegistryRoot,
    erasurePolicy: passport.erasurePolicy,
    magicBudget: passport.magicBudget,
    historyBinding: historyBinding || null,
  };
  return Object.freeze({
    ...base,
    w33ExecutionPassport: Object.freeze({ ...passportBinding, bindingDigest: sha256(passportBinding) }),
  });
}

module.exports = {
  SCHEMA,
  CHECKPOINT,
  sha256,
  isDigest,
  bindPassport,
  verifyPassport,
  validatePassportIdentity,
  checkpointAdmission,
  attachPassportReceiptMetadata,
};
