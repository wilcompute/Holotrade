// ======================================================================
// HOLOTRADE EVIDENCE LAYER
//
// Immutable evidence records, correction/supersession semantics, policy
// evaluation, and a three-digest execution envelope.
//
// This module is deliberately fail-closed about evidence status while being
// fail-honest about cryptography. `demoDigest` is a deterministic integrity
// checksum built from the prototype's hash32 primitive; it is NOT SHA-256,
// a signature, remote attestation, or a transparency-log inclusion proof.
// Production adapters should replace it with canonical bytes + standard
// cryptographic digests/signatures while preserving the record semantics.
// ======================================================================

(function (root) {
  "use strict";

  let S = root.Substrate || null;
  if (!S && typeof require !== "undefined") {
    try { S = require("./substrate.js"); } catch (_) { S = null; }
  }

  const SCHEMA = "holotrade.evidence.v1";
  const ENVELOPE_SCHEMA = "holotrade.execution-evidence.v1";
  const INTEGRITY_MODE = "DEMO_EVIDENCE_DIGEST";

  const STATUS = Object.freeze({
    VERIFIED: "VERIFIED",
    DERIVED: "DERIVED",
    HYPOTHESIS: "HYPOTHESIS",
    UNVERIFIED: "UNVERIFIED",
    SUPERSEDED: "SUPERSEDED",
    INVALIDATED: "INVALIDATED",
  });

  const EVIDENCE_CLASS = Object.freeze({
    REPO_CERTIFICATE: "REPO_CERTIFICATE",
    FORMAL_WITNESS: "FORMAL_WITNESS",
    MODEL_RESULT: "MODEL_RESULT",
    SOURCE_DOCUMENT: "SOURCE_DOCUMENT",
    EXTERNAL_VERIFIED: "EXTERNAL_VERIFIED",
    RUNTIME_ATTESTATION: "RUNTIME_ATTESTATION",
    OPERATOR_ASSERTION: "OPERATOR_ASSERTION",
  });

  const SCOPE = Object.freeze({
    EXACT: "EXACT",
    FORMAL: "FORMAL",
    SYNTHESIZED: "SYNTHESIZED",
    REGRESSION: "REGRESSION",
    SIMULATION: "SIMULATION",
    PROTOTYPE: "PROTOTYPE",
    DESIGN_SKETCH: "DESIGN_SKETCH",
    PUBLISHED: "PUBLISHED",
    RUNTIME: "RUNTIME",
  });

  const POLICY = Object.freeze({
    DEMO: "demo",
    RESEARCH: "research",
    VERIFIED: "verified",
    RUNTIME_ATTESTED: "runtime-attested",
  });

  const STATUS_VALUES = new Set(Object.values(STATUS));
  const CLASS_VALUES = new Set(Object.values(EVIDENCE_CLASS));
  const SCOPE_VALUES = new Set(Object.values(SCOPE));
  const POLICY_VALUES = new Set(Object.values(POLICY));

  function fallbackHash32(text) {
    // FNV-1a fallback used only if substrate.js is unavailable. Same honesty
    // boundary as hash32: deterministic demo checksum, not cryptography.
    let h = 0x811c9dc5;
    const s = String(text);
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }

  function hash32(text) {
    return S && typeof S.hash32 === "function" ? S.hash32(String(text)) >>> 0 : fallbackHash32(text);
  }

  function canonicalize(value) {
    if (value === null || typeof value === "boolean" || typeof value === "string") return value;
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new TypeError("canonical JSON rejects non-finite numbers");
      return value;
    }
    if (typeof value === "bigint") return value.toString(10);
    if (Array.isArray(value)) return value.map(canonicalize);
    if (typeof value === "object") {
      const out = {};
      for (const key of Object.keys(value).sort()) {
        if (value[key] !== undefined) out[key] = canonicalize(value[key]);
      }
      return out;
    }
    throw new TypeError(`canonical JSON cannot encode ${typeof value}`);
  }

  function canonicalJson(value) {
    return JSON.stringify(canonicalize(value));
  }

  function demoDigest(value) {
    const text = typeof value === "string" ? value : canonicalJson(value);
    const lanes = ["a", "b", "c", "d"].map((lane) =>
      hash32(`${SCHEMA}|${lane}|${text}`).toString(16).padStart(8, "0")
    );
    return `demo:${lanes.join("")}`;
  }

  function assertEnum(value, values, name) {
    if (!values.has(value)) throw new RangeError(`${name} has unsupported value: ${String(value)}`);
    return value;
  }

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) {
      throw new TypeError(`${name} must be a non-empty string`);
    }
    return value.trim();
  }

  function stringList(value, name) {
    if (value === undefined) return [];
    if (!Array.isArray(value)) throw new TypeError(`${name} must be an array`);
    const out = [];
    for (const entry of value) {
      const normalized = text(entry, `${name} entry`);
      if (!out.includes(normalized)) out.push(normalized);
    }
    return out.sort();
  }

  class EvidenceRecord {
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("evidence spec must be an object");
      this.schema = SCHEMA;
      this.id = text(spec.id, "evidence id");
      this.subject = text(spec.subject || this.id, "evidence subject");
      this.status = assertEnum(spec.status || STATUS.UNVERIFIED, STATUS_VALUES, "status");
      this.evidenceClass = assertEnum(spec.evidenceClass || EVIDENCE_CLASS.OPERATOR_ASSERTION, CLASS_VALUES, "evidenceClass");
      this.scope = assertEnum(spec.scope || SCOPE.PROTOTYPE, SCOPE_VALUES, "scope");
      this.claim = text(spec.claim || this.subject, "claim");
      this.source = Object.freeze(canonicalize(spec.source || {}));
      this.supersedes = Object.freeze(stringList(spec.supersedes, "supersedes"));
      this.invalidates = Object.freeze(stringList(spec.invalidates, "invalidates"));
      this.attested = spec.attested === true;
      this.createdAt = Number.isFinite(spec.createdAt) ? spec.createdAt : 0;
      if (this.createdAt < 0) throw new RangeError("createdAt must be non-negative");
      this.metadata = Object.freeze(canonicalize(spec.metadata || {}));
      this.digest = demoDigest(this.body());
      Object.freeze(this);
    }

    body() {
      return {
        schema: this.schema,
        id: this.id,
        subject: this.subject,
        status: this.status,
        evidenceClass: this.evidenceClass,
        scope: this.scope,
        claim: this.claim,
        source: this.source,
        supersedes: this.supersedes,
        invalidates: this.invalidates,
        attested: this.attested,
        createdAt: this.createdAt,
        metadata: this.metadata,
      };
    }

    verify() {
      return this.digest === demoDigest(this.body());
    }
  }

  class EvidenceLedger {
    constructor(records = []) {
      this.records = new Map();
      this.order = [];
      for (const record of records) this.add(record);
    }

    add(spec) {
      const record = spec instanceof EvidenceRecord ? spec : new EvidenceRecord(spec);
      const existing = this.records.get(record.id);
      if (existing) {
        if (existing.digest !== record.digest) {
          throw new Error(`evidence id ${record.id} is immutable and already has a different digest`);
        }
        return existing;
      }
      this.records.set(record.id, record);
      this.order.push(record.id);
      return record;
    }

    get(id) {
      return this.records.get(id) || null;
    }

    resolve(id) {
      const record = this.get(id);
      if (!record) return { id, record: null, effectiveStatus: "MISSING", supersededBy: [], invalidatedBy: [] };
      const supersededBy = [];
      const invalidatedBy = [];
      for (const otherId of this.order) {
        if (otherId === id) continue;
        const other = this.records.get(otherId);
        if (other.supersedes.includes(id)) supersededBy.push(other.id);
        if (other.invalidates.includes(id)) invalidatedBy.push(other.id);
      }
      let effectiveStatus = record.status;
      if (supersededBy.length) effectiveStatus = STATUS.SUPERSEDED;
      if (invalidatedBy.length) effectiveStatus = STATUS.INVALIDATED;
      return { id, record, effectiveStatus, supersededBy, invalidatedBy };
    }

    evaluate(ids = [], { policy = POLICY.DEMO } = {}) {
      assertEnum(policy, POLICY_VALUES, "policy");
      const refs = stringList(ids, "evidence refs");
      const resolved = refs.map((id) => this.resolve(id));
      const blockers = [];
      const warnings = [];

      for (const item of resolved) {
        if (!item.record) {
          blockers.push({ id: item.id, code: "MISSING_EVIDENCE" });
          continue;
        }
        if (!item.record.verify()) blockers.push({ id: item.id, code: "EVIDENCE_DIGEST_MISMATCH" });
        if (item.effectiveStatus === STATUS.INVALIDATED) blockers.push({ id: item.id, code: "INVALIDATED_EVIDENCE" });
        if (item.effectiveStatus === STATUS.SUPERSEDED) blockers.push({ id: item.id, code: "SUPERSEDED_EVIDENCE" });
        if ([STATUS.HYPOTHESIS, STATUS.UNVERIFIED].includes(item.effectiveStatus)) {
          warnings.push({ id: item.id, code: item.effectiveStatus });
        }
        if ([POLICY.VERIFIED, POLICY.RUNTIME_ATTESTED].includes(policy) &&
            ![STATUS.VERIFIED, STATUS.DERIVED].includes(item.effectiveStatus)) {
          blockers.push({ id: item.id, code: "STATUS_NOT_VERIFIED" });
        }
      }

      if (policy === POLICY.RUNTIME_ATTESTED) {
        const runtime = resolved.some((item) => item.record &&
          item.record.evidenceClass === EVIDENCE_CLASS.RUNTIME_ATTESTATION &&
          item.record.attested === true &&
          [STATUS.VERIFIED, STATUS.DERIVED].includes(item.effectiveStatus));
        if (!runtime) blockers.push({ id: null, code: "RUNTIME_ATTESTATION_REQUIRED" });
      }

      // DEMO may carry no evidence. Other policies with an explicitly empty
      // ref list still evaluate successfully except runtime-attested. This lets
      // an operator use RESEARCH as a status filter without inventing evidence.
      const decision = {
        schema: `${SCHEMA}.decision`,
        policy,
        refs,
        ok: blockers.length === 0,
        blockers,
        warnings,
        resolved: resolved.map((item) => ({
          id: item.id,
          digest: item.record ? item.record.digest : null,
          originalStatus: item.record ? item.record.status : null,
          effectiveStatus: item.effectiveStatus,
          evidenceClass: item.record ? item.record.evidenceClass : null,
          scope: item.record ? item.record.scope : null,
          supersededBy: item.supersededBy,
          invalidatedBy: item.invalidatedBy,
        })),
      };
      decision.digest = demoDigest(decision);
      return decision;
    }

    checkpoint(label, payload, parentDigest = null) {
      const body = {
        schema: "holotrade.state-commitment.v1",
        label: text(label, "checkpoint label"),
        parentDigest,
        payload: canonicalize(payload),
      };
      return { ...body, digest: demoDigest(body), integrityMode: INTEGRITY_MODE };
    }

    executionEnvelope({ plan, vm, node, outcome = "settled", auditHash = null } = {}) {
      if (!plan || !vm || !node) throw new TypeError("plan, vm and node are required");
      const decision = this.evaluate(plan.evidenceRefs || [], { policy: plan.evidencePolicy || POLICY.DEMO });
      const identity = {
        nodeId: node.id,
        nodeAddress: node.address ?? node.addr ?? null,
        hardware: node.hardware ? {
          id: node.hardware.id || node.hardware.name || null,
          kind: node.hardware.kind || null,
        } : null,
      };
      const state = {
        planId: plan.id,
        planDigest: plan.digest,
        vmId: vm.id,
        state: vm.state,
        secondsRun: vm.secondsRun,
        stateBlobs: vm.stateBlobs,
        outcome,
      };
      const runtime = {
        bootMs: vm.bootMs,
        nodeSeconds: vm.secondsRun * (plan.nodeCount || 1),
        modeledCost: vm.cost,
        modeledJoules: vm.energyJoules,
        auditHash,
        attested: false,
        evidenceClass: EVIDENCE_CLASS.MODEL_RESULT,
      };
      const bom = {
        identityDigest: demoDigest(identity),
        stateDigest: demoDigest(state),
        runtimeDigest: demoDigest(runtime),
      };
      const predicate = {
        schema: ENVELOPE_SCHEMA,
        integrityMode: INTEGRITY_MODE,
        cryptographicallyAttested: false,
        evidenceDecision: decision,
        threeDigestBOM: bom,
        identity,
        state,
        runtime,
      };
      const statement = {
        _type: "https://in-toto.io/Statement/v1",
        subject: [{ name: plan.id, digest: { holotrade_demo: String(plan.digest) } }],
        predicateType: "urn:holotrade:execution-evidence:v1",
        predicate,
      };
      const envelope = {
        schema: ENVELOPE_SCHEMA,
        integrityMode: INTEGRITY_MODE,
        statement,
        digest: demoDigest(statement),
      };
      return envelope;
    }
  }

  const API = {
    SCHEMA,
    ENVELOPE_SCHEMA,
    INTEGRITY_MODE,
    STATUS,
    EVIDENCE_CLASS,
    SCOPE,
    POLICY,
    canonicalJson,
    demoDigest,
    EvidenceRecord,
    EvidenceLedger,
  };

  root.HolotradeEvidence = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
