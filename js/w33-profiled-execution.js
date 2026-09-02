// Fail-closed W33 machine-profile admission for HoloTrade.
//
// This closes the boundary left explicit by w33-execution-profile.js: the
// construction-time 216-carrier fork now participates in scheduler placement,
// launch admission, VM identity, and GoMicroVM contract compilation.
//
// The generic ExecutionPlan is intentionally not mutated. Its existing digest
// remains the application/authority commitment; the W33 profile commits to
// that digest and the pair {plan, profile} is the deployment identity. This
// avoids invalidating the core plan integrity model while still making the
// machine type fail closed at execution.

"use strict";

const crypto = require("node:crypto");
const P = require("./w33-execution-profile.js");
const G = require("./gomicrovm-adapter.js");

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

class W33HostRegistry {
  constructor() { this.hosts = new Map(); }

  register(nodeId, machineType, options = {}) {
    if (!nodeId) throw new TypeError("node id required");
    const logicalDimension = P.LOGICAL_DIMENSION[machineType];
    if (!logicalDimension) throw new TypeError(`unknown W33 machine type: ${machineType}`);
    const row = Object.freeze({
      nodeId,
      machineType,
      logicalDimension,
      symmetryNamespaces: Object.freeze({
        cliffordLift: options.cliffordLift || P.SYMMETRY_NAMESPACE.CLIFFORD_LIFT,
        projectiveWeyl: options.projectiveWeyl || P.SYMMETRY_NAMESPACE.PROJECTIVE_WEYL,
      }),
    });
    this.hosts.set(nodeId, row);
    return row;
  }

  get(nodeOrId) {
    const id = typeof nodeOrId === "string" ? nodeOrId : nodeOrId?.id;
    return this.hosts.get(id) || null;
  }
}

function verifyHost(profile, plan, node, registry) {
  if (!P.verify(profile, plan)) {
    return { ok: false, code: "W33_PROFILE_INVALID", reason: "profile does not verify against plan" };
  }
  const host = registry.get(node);
  if (!host) {
    return { ok: false, code: "W33_HOST_UNTYPED", reason: "node has no registered W33 machine type" };
  }
  if (host.machineType !== profile.machineType || host.logicalDimension !== profile.logicalDimension) {
    return {
      ok: false,
      code: "W33_MACHINE_TYPE_MISMATCH",
      reason: `deployment requires ${profile.machineType}/${profile.logicalDimension}; host provides ${host.machineType}/${host.logicalDimension}`,
    };
  }
  const ns = host.symmetryNamespaces;
  if (ns.cliffordLift === ns.projectiveWeyl) {
    return { ok: false, code: "W33_NAMESPACE_ALIAS", reason: "Clifford-lift and projective/Weyl namespaces alias" };
  }
  if (ns.cliffordLift !== P.SYMMETRY_NAMESPACE.CLIFFORD_LIFT ||
      ns.projectiveWeyl !== P.SYMMETRY_NAMESPACE.PROJECTIVE_WEYL) {
    return { ok: false, code: "W33_NAMESPACE_UNKNOWN", reason: "host symmetry namespace identity is not canonical" };
  }
  return { ok: true, host };
}

class ProfiledExecutionEngine {
  constructor(baseEngine, registry = new W33HostRegistry()) {
    if (!baseEngine || typeof baseEngine.place !== "function" || typeof baseEngine.launch !== "function") {
      throw new TypeError("base HoloTrade ExecutionEngine required");
    }
    this.base = baseEngine;
    this.registry = registry;
  }

  bind(plan, machineType) {
    return Object.freeze({ plan, profile: P.bind(plan, machineType) });
  }

  place(plan, profile, options = {}) {
    if (!P.verify(profile, plan)) return [];
    return this.base.place(plan, options).filter((candidate) =>
      verifyHost(profile, plan, candidate.node, this.registry).ok
    );
  }

  launch(plan, profile, node) {
    const gate = verifyHost(profile, plan, node, this.registry);
    if (!gate.ok) return gate;
    const result = this.base.launch(plan, node);
    if (!result.ok) return result;
    result.vm.w33ProfileDigest = profile.digest;
    result.vm.w33MachineType = profile.machineType;
    result.vm.w33LogicalDimension = profile.logicalDimension;
    result.vm.w33SymmetryNamespaces = Object.freeze({ ...gate.host.symmetryNamespaces });
    return result;
  }

  compileGoMicroVM(plan, profile, options = {}) {
    if (!P.verify(profile, plan)) throw new Error("refusing to compile invalid W33 execution profile");
    const contract = G.compile(plan, options);
    const w33 = Object.freeze({
      profileDigest: profile.digest,
      machineType: profile.machineType,
      logicalDimension: profile.logicalDimension,
      runtimeRetype: "FORBIDDEN",
      symmetryNamespaces: Object.freeze({ ...profile.symmetryNamespaces }),
    });
    const deploymentDigest = sha256({ contractDigest: contract.digest, w33 });
    return Object.freeze({ ...contract, w33, deploymentDigest });
  }
}

module.exports = {
  W33HostRegistry,
  ProfiledExecutionEngine,
  verifyHost,
};
