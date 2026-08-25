// ======================================================================
// HOLOTRADE PROJECTION -> EXECUTION -> EMISSION KERNEL
//
// This module closes three existing prototype surfaces into one state
// transition:
//
//   immutable resource refs -> projection -> evidence-gated ExecutionPlan
//   -> node-second settlement -> immutable emitted resource
//
// The shape is inspired by the HCP/HLIX "projection -> execution -> emission"
// materials supplied to this project, while the execution boundary follows
// HoloTrade's current GoMicroVM-compatible contract vocabulary: pinned
// artifacts, explicit grants, policy references, validity and receipts.
//
// IMPORTANT EVIDENCE BOUNDARY
// ---------------------------
// This is an HCP-shaped prototype lifecycle, NOT an implementation or claim
// of HCP conformance, HLIX interoperability, GoMicroVM deployment, remote
// attestation, content retrieval, or cryptographic signing. UORAddress.from()
// and Evidence.demoDigest() remain deterministic prototype integrity tools.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const U = root.HolotradeUOR ||
    (typeof require !== "undefined" ? require("./uor.js") : null);

  if (!E || !U) throw new Error("projection requires evidence.js and uor.js");

  const RESOURCE_SCHEMA = "holotrade.resource-ref.v1";
  const PROJECTION_SCHEMA = "holotrade.projection.v1";
  const EMISSION_SCHEMA = "holotrade.emission.v1";

  const POLICY_RANK = Object.freeze({
    [E.POLICY.DEMO]: 0,
    [E.POLICY.RESEARCH]: 1,
    [E.POLICY.VERIFIED]: 2,
    [E.POLICY.RUNTIME_ATTESTED]: 3,
  });

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) {
      throw new TypeError(`${name} must be a non-empty string`);
    }
    return value.trim();
  }

  function canonical(value) {
    return JSON.parse(E.canonicalJson(value));
  }

  function strings(value, name) {
    if (value === undefined || value === null) return [];
    if (!Array.isArray(value)) throw new TypeError(`${name} must be an array`);
    const out = [];
    for (const item of value) {
      const normalized = text(item, `${name} entry`);
      if (!out.includes(normalized)) out.push(normalized);
    }
    return out.sort();
  }

  function normalizePolicy(value) {
    const policy = value || E.POLICY.DEMO;
    if (!Object.hasOwn(POLICY_RANK, policy)) {
      throw new RangeError(`unsupported evidence policy: ${String(policy)}`);
    }
    return policy;
  }

  function normalizeGrants(value = {}) {
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new TypeError("grants must be an object");
    }
    return Object.freeze({
      network: Object.freeze(strings(value.network, "network grants")),
      services: Object.freeze(strings(value.services, "service grants")),
      secrets: Object.freeze(strings(value.secrets, "secret grants")),
    });
  }

  function isSubset(candidate, ceiling) {
    const allowed = new Set(ceiling);
    return candidate.every((item) => allowed.has(item));
  }

  function narrowGrants(ceiling, requested) {
    if (requested === undefined || requested === null) return ceiling;
    const normalized = normalizeGrants(requested);
    for (const key of ["network", "services", "secrets"]) {
      if (!isSubset(normalized[key], ceiling[key])) {
        throw new Error(`projection authority widening refused for ${key}`);
      }
    }
    return normalized;
  }

  function address(value, seed) {
    if (value instanceof U.UORAddress) return value;
    if (typeof value === "string") return U.UORAddress.fromHex(value);
    if (value === undefined || value === null) return U.UORAddress.from(seed);
    throw new TypeError("resource address must be a UORAddress or canonical uor: hex string");
  }

  class ResourceRef {
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("resource spec must be an object");
      this.schema = RESOURCE_SCHEMA;
      this.id = text(spec.id, "resource id");
      this.kind = text(spec.kind || "dataset", "resource kind");
      this.role = text(spec.role || "input", "resource role");
      this.digest = text(spec.digest, "resource digest");
      this.address = address(spec.address, `${this.id}|${this.digest}`);
      this.metadata = Object.freeze(canonical(spec.metadata || {}));
      this.referenceDigest = E.demoDigest(this.body());
      Object.freeze(this);
    }

    body() {
      return {
        schema: this.schema,
        id: this.id,
        kind: this.kind,
        role: this.role,
        digest: this.digest,
        address: this.address.toHex(),
        metadata: this.metadata,
      };
    }

    toJSON() {
      return this.body();
    }
  }

  function resource(value) {
    return value instanceof ResourceRef ? value : new ResourceRef(value);
  }

  class Projection {
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("projection spec must be an object");
      this.schema = PROJECTION_SCHEMA;
      this.id = text(spec.id, "projection id");
      this.name = text(spec.name || this.id, "projection name");
      this.service = text(spec.service || "compute", "projection service");
      this.workloadId = text(spec.workloadId || "llm-train", "projection workloadId");
      this.outputKind = text(spec.outputKind || "dataset", "projection outputKind");
      this.inputs = Object.freeze((spec.inputs || []).map(resource).sort((a, b) =>
        a.role.localeCompare(b.role) || a.id.localeCompare(b.id) || a.digest.localeCompare(b.digest)
      ));
      this.grants = normalizeGrants(spec.grants || {});
      this.evidenceRefs = Object.freeze(strings(spec.evidenceRefs, "projection evidenceRefs"));
      this.evidencePolicy = normalizePolicy(spec.evidencePolicy);
      this.metadata = Object.freeze(canonical(spec.metadata || {}));
      this.digest = E.demoDigest(this.body());
      Object.freeze(this);
    }

    body() {
      return {
        schema: this.schema,
        id: this.id,
        name: this.name,
        service: this.service,
        workloadId: this.workloadId,
        outputKind: this.outputKind,
        inputs: this.inputs.map((item) => item.body()),
        grants: this.grants,
        evidenceRefs: this.evidenceRefs,
        evidencePolicy: this.evidencePolicy,
        metadata: this.metadata,
      };
    }

    toJSON() {
      return { ...this.body(), digest: this.digest };
    }
  }

  function projection(value) {
    return value instanceof Projection ? value : new Projection(value);
  }

  function strongerPolicy(floor, requested) {
    const base = normalizePolicy(floor);
    const candidate = normalizePolicy(requested || base);
    if (POLICY_RANK[candidate] < POLICY_RANK[base]) {
      throw new Error(`projection evidence policy weakening refused: ${base} -> ${candidate}`);
    }
    return candidate;
  }

  class ProjectionEngine {
    constructor(executionEngine) {
      if (!executionEngine || typeof executionEngine.createPlan !== "function") {
        throw new TypeError("ProjectionEngine requires an execution engine with createPlan()");
      }
      this.execution = executionEngine;
      this.emissions = new Map();
    }

    /**
     * Compile a projection to the existing ExecutionPlan vocabulary.
     *
     * Authority is monotone: runtime settings may NARROW grants and may
     * STRENGTHEN the evidence policy, but cannot widen authority or weaken the
     * projection's trust contract. Every input digest plus the projection
     * definition digest becomes a pinned plan artifact.
     */
    compile(value, runtime = {}) {
      const p = projection(value);
      if (!runtime || typeof runtime !== "object") throw new TypeError("runtime spec must be an object");
      if (runtime.artifacts !== undefined) {
        throw new Error("runtime artifacts are refused; declare resources as projection inputs");
      }

      const grants = narrowGrants(p.grants, runtime.grants);
      const evidencePolicy = strongerPolicy(p.evidencePolicy, runtime.evidencePolicy);
      const evidenceRefs = strings(
        [...p.evidenceRefs, ...strings(runtime.evidenceRefs, "runtime evidenceRefs")],
        "compiled evidenceRefs"
      );
      const artifacts = [
        { name: `projection:${p.id}`, digest: p.digest },
        ...p.inputs.map((item) => ({
          name: `${item.role}:${item.id}`,
          digest: item.digest,
          resourceAddress: item.address.toHex(),
        })),
      ];

      const planSpec = {
        workloadId: runtime.workloadId || p.workloadId,
        name: runtime.name || p.name,
        owner: runtime.owner || "YOU",
        artifacts,
        grants,
        validFrom: runtime.validFrom,
        validUntil: runtime.validUntil,
        requestedSeconds: runtime.requestedSeconds,
        nodeCount: runtime.nodeCount,
        maxPricePerNodeSecond: runtime.maxPricePerNodeSecond,
        anchorAddress: runtime.anchorAddress,
        evidenceRefs,
        evidencePolicy,
      };

      // Do not pass undefined values into the legacy plan where defaults are
      // selected with `||`; omission preserves those defaults exactly.
      for (const key of Object.keys(planSpec)) {
        if (planSpec[key] === undefined) delete planSpec[key];
      }

      const binding = {
        schema: "holotrade.projection-binding.v1",
        projectionDigest: p.digest,
        inputDigests: p.inputs.map((item) => item.digest).sort(),
        evidenceRefs,
        evidencePolicy,
        grantDigest: E.demoDigest(grants),
      };
      binding.digest = E.demoDigest(binding);
      return Object.freeze({ projection: p, planSpec: Object.freeze(planSpec), binding: Object.freeze(binding) });
    }

    createPlan(value, runtime = {}) {
      const compiled = this.compile(value, runtime);
      const plan = this.execution.createPlan(compiled.planSpec);
      const check = this.verifyBinding(compiled.projection, plan);
      if (!check.ok) throw new Error(`compiled plan lost projection binding: ${check.reason}`);
      return Object.freeze({ ...compiled, plan });
    }

    verifyBinding(value, plan) {
      const p = projection(value);
      if (!plan || typeof plan !== "object") return { ok: false, reason: "missing plan" };
      const artifactDigests = new Set((plan.artifacts || []).map((item) => item && item.digest).filter(Boolean));
      if (!artifactDigests.has(p.digest)) return { ok: false, reason: "projection digest missing from plan artifacts" };
      for (const input of p.inputs) {
        if (!artifactDigests.has(input.digest)) {
          return { ok: false, reason: `input digest missing from plan artifacts: ${input.id}` };
        }
      }
      const planPolicy = normalizePolicy(plan.evidencePolicy || E.POLICY.DEMO);
      if (POLICY_RANK[planPolicy] < POLICY_RANK[p.evidencePolicy]) {
        return { ok: false, reason: "plan evidence policy is weaker than projection policy" };
      }
      const planRefs = new Set(plan.evidenceRefs || []);
      for (const ref of p.evidenceRefs) {
        if (!planRefs.has(ref)) return { ok: false, reason: `projection evidence ref missing from plan: ${ref}` };
      }
      return { ok: true };
    }

    /**
     * Emit one immutable resource from one successful settled execution.
     * Failed/partial work still has an execution receipt; it does not silently
     * become a reusable output resource.
     */
    emit(value, plan, receipt, outputSpec = {}) {
      const p = projection(value);
      const binding = this.verifyBinding(p, plan);
      if (!binding.ok) throw new Error(`emission refused: ${binding.reason}`);
      if (!receipt || typeof receipt !== "object") throw new TypeError("receipt is required");
      if (receipt.outcome !== "settled") throw new Error(`emission refused: receipt outcome is ${String(receipt.outcome)}`);
      if (receipt.planId !== plan.id || receipt.planDigest !== plan.digest) {
        throw new Error("emission refused: receipt does not bind the supplied plan");
      }

      const receiptCommitment = receipt.evidenceDigest || E.demoDigest({
        id: receipt.id,
        planId: receipt.planId,
        planDigest: receipt.planDigest,
        nodeId: receipt.nodeId,
        nodeSeconds: receipt.nodeSeconds,
        outcome: receipt.outcome,
        chainHash: receipt.chainHash || null,
        ts: receipt.ts,
      });
      const requestedId = outputSpec.id === undefined ? null : text(outputSpec.id, "output id");
      const outputKind = text(outputSpec.kind || p.outputKind, "output kind");
      const transition = {
        schema: EMISSION_SCHEMA,
        projection: { id: p.id, digest: p.digest },
        parents: p.inputs.map((item) => ({ id: item.id, role: item.role, digest: item.digest })),
        execution: {
          planId: plan.id,
          planDigest: plan.digest,
          receiptId: receipt.id,
          receiptCommitment,
          nodeId: receipt.nodeId,
          nodeSeconds: receipt.nodeSeconds,
          outcome: receipt.outcome,
        },
        output: {
          requestedId,
          kind: outputKind,
          metadata: canonical(outputSpec.metadata || {}),
        },
      };
      const contentDigest = E.demoDigest(transition);
      const outputId = requestedId || `RES-${contentDigest.slice(5, 17).toUpperCase()}`;
      const output = new ResourceRef({
        id: outputId,
        kind: outputKind,
        role: "output",
        digest: contentDigest,
        address: outputSpec.address || U.UORAddress.from(contentDigest),
        metadata: {
          ...(outputSpec.metadata || {}),
          projectionDigest: p.digest,
          planDigest: plan.digest,
          receiptCommitment,
        },
      });

      const recordBody = {
        ...transition,
        output: output.body(),
        integrityMode: E.INTEGRITY_MODE,
        cryptographicallyAttested: false,
      };
      const record = Object.freeze({ ...recordBody, digest: E.demoDigest(recordBody) });
      const key = `${p.digest}|${plan.digest}|${receipt.id}`;
      const existing = this.emissions.get(key);
      if (existing) {
        if (existing.digest !== record.digest) {
          throw new Error("emission key already exists with different content");
        }
        return existing;
      }
      this.emissions.set(key, record);
      return record;
    }
  }

  const API = {
    RESOURCE_SCHEMA,
    PROJECTION_SCHEMA,
    EMISSION_SCHEMA,
    ResourceRef,
    Projection,
    ProjectionEngine,
  };

  root.HolotradeProjection = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
