// ======================================================================
// HOLOTRADE FIRST-CLASS SEMANTIC RESULT CONTRACT
//
// A deterministic result is not execution provenance.  This module makes the
// distinction explicit: a ResultContract is an immutable ResourceRef pinned as
// a projection input, while a SemanticResult commitment is a SHA-256 digest of
// canonical result bytes emitted alongside (not inside) provenance metadata.
// ======================================================================
(function (root) {
  "use strict";
  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  const P = root.HolotradeProjection || (typeof require !== "undefined" ? require("./projection.js") : null);
  let crypto = null;
  if (typeof require !== "undefined") { try { crypto = require("node:crypto"); } catch (_) { crypto = null; } }
  if (!E || !P || !crypto) throw new Error("result-contract requires evidence, projection, and node:crypto");

  const CONTRACT_SCHEMA = "holotrade.semantic-result-contract.v1";
  const RESULT_SCHEMA = "holotrade.semantic-result.v1";

  function text(v, name) {
    if (typeof v !== "string" || !v.trim()) throw new TypeError(`${name} must be a non-empty string`);
    return v.trim();
  }
  function sha256(value) {
    const b = Buffer.isBuffer(value) ? value : Buffer.from(typeof value === "string" ? value : E.canonicalJson(value), "utf8");
    return `sha256:${crypto.createHash("sha256").update(b).digest("hex")}`;
  }

  class ResultContract {
    constructor(spec = {}) {
      this.schema = CONTRACT_SCHEMA;
      this.id = text(spec.id || "semantic-result", "contract id");
      this.mediaType = text(spec.mediaType || "application/json", "mediaType");
      this.encoding = text(spec.encoding || "canonical-json/utf8/sorted-object-keys", "encoding");
      if (this.encoding !== "canonical-json/utf8/sorted-object-keys") throw new RangeError("only canonical-json encoding is supported");
      this.digestAlgorithm = "sha256";
      this.deterministic = spec.deterministic !== false;
      this.schemaId = spec.schemaId == null ? null : text(spec.schemaId, "schemaId");
      this.description = spec.description == null ? null : String(spec.description);
      this.digest = sha256(this.body());
      Object.freeze(this);
    }
    body() {
      return {
        schema: this.schema, id: this.id, mediaType: this.mediaType,
        encoding: this.encoding, digestAlgorithm: this.digestAlgorithm,
        deterministic: this.deterministic, schemaId: this.schemaId,
        description: this.description,
      };
    }
    asResource() {
      return new P.ResourceRef({
        id: `result-contract:${this.id}`,
        kind: "result-contract",
        role: "result-contract",
        digest: this.digest,
        metadata: this.body(),
      });
    }
  }

  function contract(v) { return v instanceof ResultContract ? v : new ResultContract(v); }

  function bindProjection(spec, value) {
    const c = contract(value);
    const base = spec instanceof P.Projection ? spec.body() : { ...(spec || {}) };
    const inputs = [...(base.inputs || [])];
    if (inputs.some((x) => (x.role || x.metadata?.role) === "result-contract")) {
      throw new Error("projection already declares a result-contract input");
    }
    inputs.push(c.asResource());
    return new P.Projection({ ...base, inputs });
  }

  function projectionBinds(projection, value) {
    const c = contract(value);
    return !!projection && (projection.inputs || []).some((x) =>
      x.role === "result-contract" && x.digest === c.digest
    );
  }

  function commit(value, contractValue) {
    const c = contract(contractValue);
    const canonical = E.canonicalJson(value);
    const bytes = Buffer.from(canonical, "utf8");
    const body = {
      schema: RESULT_SCHEMA,
      contractDigest: c.digest,
      contractId: c.id,
      mediaType: c.mediaType,
      encoding: c.encoding,
      digestAlgorithm: "sha256",
      digest: sha256(bytes),
      length: bytes.length,
      deterministic: c.deterministic,
    };
    return Object.freeze(body);
  }

  function verifyCommitment(commitment, contractValue, value = undefined) {
    const c = contract(contractValue);
    if (!commitment || commitment.schema !== RESULT_SCHEMA || commitment.contractDigest !== c.digest ||
        commitment.digestAlgorithm !== "sha256" || !/^sha256:[0-9a-f]{64}$/.test(commitment.digest || "")) {
      return { ok: false, code: "SHAPE_OR_CONTRACT" };
    }
    if (value !== undefined) {
      const expected = commit(value, c);
      if (expected.digest !== commitment.digest || expected.length !== commitment.length) return { ok: false, code: "RESULT_MISMATCH" };
    }
    return { ok: true, code: "OK" };
  }

  function emit(projectionEngine, projection, plan, receipt, { contract: contractValue, value, id, kind, address, metadata = {} } = {}) {
    const c = contract(contractValue);
    if (!projectionBinds(projection, c)) throw new Error("projection does not bind the supplied first-class result contract");
    if (c.deterministic && value === undefined) throw new Error("deterministic result contract requires a semantic result value");
    const semantic = commit(value, c);
    const base = projectionEngine.emit(projection, plan, receipt, {
      id, kind, address,
      // resultDigest is a backwards-compatibility alias only.  The authoritative
      // commitment is output.result below and is contract-bound.
      metadata: { ...metadata, resultContractDigest: c.digest, resultDigest: semantic.digest },
    });
    const body = {
      ...base,
      baseEmissionDigest: base.digest,
      output: { ...base.output, result: semantic },
      semanticResult: semantic,
      resultContract: c.body(),
    };
    delete body.digest;
    const record = Object.freeze({ ...body, digest: E.demoDigest(body) });
    return record;
  }

  function resultDigestOf(emission) {
    const d = emission?.output?.result?.digest || emission?.semanticResult?.digest || emission?.output?.metadata?.resultDigest || null;
    if (typeof d !== "string" || !/^sha256:[0-9a-f]{64}$/.test(d)) throw new Error("emission has no valid first-class semantic SHA-256 result commitment");
    return d;
  }

  const API = { CONTRACT_SCHEMA, RESULT_SCHEMA, ResultContract, contract, bindProjection, projectionBinds, commit, verifyCommitment, emit, resultDigestOf, sha256 };
  root.HolotradeResultContract = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
