// Fail-closed scheduler/admission enforcement for the W33 carrier fork.
//
// The construction-time execution profile already distinguishes the two
// inequivalent 216-state machines.  This module makes that distinction
// operational: placement and launch require an immutable node-inventory
// assignment with the same machine type.  Wrong-type and untyped nodes are
// refused before generic pricing/launch logic runs.
//
// Honest boundary: this is a software admission invariant.  It is not remote
// attestation of physical hardware and does not prove that a node actually
// implements the declared finite carrier.

"use strict";

const crypto = require("node:crypto");
const P = require("./w33-execution-profile.js");

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
  if (!Object.prototype.hasOwnProperty.call(P.LOGICAL_DIMENSION, machineType)) {
    throw new TypeError(`unknown W33 machine type: ${machineType}`);
  }
  return machineType;
}

function compileInventory(entries) {
  if (!Array.isArray(entries)) throw new TypeError("W33 inventory entries must be an array");
  const assignments = Object.create(null);
  for (const e of entries) {
    if (!e || typeof e.nodeId !== "string" || !e.nodeId) throw new TypeError("inventory nodeId required");
    if (Object.prototype.hasOwnProperty.call(assignments, e.nodeId)) throw new TypeError(`duplicate W33 inventory node: ${e.nodeId}`);
    assignments[e.nodeId] = validateMachineType(e.machineType);
  }
  const frozenAssignments = Object.freeze({ ...assignments });
  const payload = {
    schema: "holotrade.w33-machine-inventory.v1",
    assignments: frozenAssignments,
    runtimeRetype: "FORBIDDEN",
  };
  return Object.freeze({ ...payload, digest: sha256(payload) });
}

function verifyInventory(inventory) {
  if (!inventory || inventory.schema !== "holotrade.w33-machine-inventory.v1") return false;
  if (inventory.runtimeRetype !== "FORBIDDEN") return false;
  if (!inventory.assignments || typeof inventory.assignments !== "object") return false;
  try {
    for (const machineType of Object.values(inventory.assignments)) validateMachineType(machineType);
  } catch (_) {
    return false;
  }
  const payload = {
    schema: inventory.schema,
    assignments: inventory.assignments,
    runtimeRetype: inventory.runtimeRetype,
  };
  return inventory.digest === sha256(payload);
}

function machineTypeFor(inventory, node) {
  if (!verifyInventory(inventory) || !node || typeof node.id !== "string") return null;
  return Object.prototype.hasOwnProperty.call(inventory.assignments, node.id)
    ? inventory.assignments[node.id]
    : null;
}

function typeGate(profile, plan, node, inventory) {
  if (!P.verify(profile, plan)) {
    return { ok: false, code: "BAD_W33_PROFILE", reason: "W33 execution profile does not verify against plan" };
  }
  if (!verifyInventory(inventory)) {
    return { ok: false, code: "BAD_W33_INVENTORY", reason: "W33 machine inventory integrity check failed" };
  }
  const machineType = machineTypeFor(inventory, node);
  if (!machineType) {
    return { ok: false, code: "W33_UNTYPED_NODE", reason: `node ${node?.id || "<unknown>"} has no immutable W33 machine assignment` };
  }
  if (machineType !== profile.machineType) {
    return {
      ok: false,
      code: "W33_MACHINE_MISMATCH",
      reason: `profile requires ${profile.machineType}; node ${node.id} is ${machineType}`,
      requiredMachineType: profile.machineType,
      nodeMachineType: machineType,
    };
  }
  return { ok: true, machineType, logicalDimension: profile.logicalDimension };
}

function place(engine, profile, plan, inventory, { limit = 8 } = {}) {
  if (!P.verify(profile, plan)) {
    return { ok: false, code: "BAD_W33_PROFILE", reason: "W33 execution profile does not verify against plan", candidates: [] };
  }
  if (!verifyInventory(inventory)) {
    return { ok: false, code: "BAD_W33_INVENTORY", reason: "W33 machine inventory integrity check failed", candidates: [] };
  }
  if (!engine || typeof engine.place !== "function") throw new TypeError("ExecutionEngine-like object with place() required");

  // Ask the generic scheduler for its complete admissible/ranked list first;
  // machine type is a hard gate, not a score penalty or fallback preference.
  const generic = engine.place(plan, { limit: Number.MAX_SAFE_INTEGER });
  const candidates = generic.filter((c) => machineTypeFor(inventory, c.node) === profile.machineType).slice(0, limit);
  if (!candidates.length) {
    return {
      ok: false,
      code: "NO_W33_MACHINE_MATCH",
      reason: `no admissible node is assigned ${profile.machineType}`,
      candidates: [],
    };
  }
  return { ok: true, machineType: profile.machineType, logicalDimension: profile.logicalDimension, candidates };
}

function launch(engine, profile, plan, node, inventory) {
  if (!engine || typeof engine.launch !== "function") throw new TypeError("ExecutionEngine-like object with launch() required");
  const gate = typeGate(profile, plan, node, inventory);
  if (!gate.ok) return gate;
  const result = engine.launch(plan, node);
  if (!result || !result.ok) return result;
  return { ...result, w33MachineType: gate.machineType, w33LogicalDimension: gate.logicalDimension, w33ProfileDigest: profile.digest, w33InventoryDigest: inventory.digest };
}

module.exports = {
  compileInventory,
  verifyInventory,
  machineTypeFor,
  typeGate,
  place,
  launch,
};
