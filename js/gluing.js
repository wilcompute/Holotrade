// ======================================================================
// HOLOTRADE LOCAL -> GLOBAL GLUING KERNEL
//
// W33-Theory's strongest UOR bridge is not an address coincidence: exact
// local sections overlap compatibly and glue to one global section. This
// module turns that pattern into an execution-market primitive.
//
// Independent policy/capability/resource patches may compose iff every
// overlapping path agrees exactly after canonicalization. Conflicts fail
// closed; no "last writer wins" semantics exist here.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!E) throw new Error("gluing requires evidence.js");

  const SCHEMA = "holotrade.gluing.v1";

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) {
      throw new TypeError(`${name} must be a non-empty string`);
    }
    return value.trim();
  }

  function canonical(value) {
    return JSON.parse(E.canonicalJson(value));
  }

  function flatten(value, prefix = "", out = new Map()) {
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      const keys = Object.keys(value).sort();
      if (keys.length === 0 && prefix) out.set(prefix, {});
      for (const key of keys) flatten(value[key], prefix ? `${prefix}.${key}` : key, out);
    } else {
      if (!prefix) throw new TypeError("patch value must be an object");
      out.set(prefix, canonical(value));
    }
    return out;
  }

  function unflatten(entries) {
    const rootValue = {};
    for (const [path, value] of [...entries].sort(([a], [b]) => a.localeCompare(b))) {
      const parts = path.split(".");
      let cursor = rootValue;
      for (let i = 0; i < parts.length - 1; i++) {
        const part = parts[i];
        if (!cursor[part] || typeof cursor[part] !== "object" || Array.isArray(cursor[part])) cursor[part] = {};
        cursor = cursor[part];
      }
      cursor[parts[parts.length - 1]] = canonical(value);
    }
    return rootValue;
  }

  class LocalSection {
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("section spec must be an object");
      this.id = text(spec.id, "section id");
      this.kind = text(spec.kind || "generic", "section kind");
      this.values = Object.freeze(canonical(spec.values || {}));
      this.evidenceRefs = Object.freeze([...(spec.evidenceRefs || [])].map((x) => text(x, "evidence ref")).sort());
      this.paths = Object.freeze([...flatten(this.values).keys()].sort());
      this.digest = E.demoDigest({ id: this.id, kind: this.kind, values: this.values, evidenceRefs: this.evidenceRefs });
      Object.freeze(this);
    }
  }

  function section(value) {
    return value instanceof LocalSection ? value : new LocalSection(value);
  }

  function glue(values, { requiredPaths = [] } = {}) {
    if (!Array.isArray(values) || values.length === 0) throw new TypeError("at least one local section is required");
    const sections = values.map(section).sort((a, b) => a.id.localeCompare(b.id));
    const merged = new Map();
    const owners = new Map();
    const overlaps = [];
    const conflicts = [];

    for (const local of sections) {
      for (const [path, value] of flatten(local.values)) {
        const encoded = E.canonicalJson(value);
        if (!merged.has(path)) {
          merged.set(path, value);
          owners.set(path, [{ id: local.id, digest: local.digest }]);
          continue;
        }
        const prior = merged.get(path);
        const priorEncoded = E.canonicalJson(prior);
        const compatible = priorEncoded === encoded;
        overlaps.push({
          path,
          section: local.id,
          priorSections: owners.get(path).map((x) => x.id),
          compatible,
        });
        if (!compatible) {
          conflicts.push({ path, expected: prior, received: value, section: local.id, priorSections: owners.get(path).map((x) => x.id) });
        } else {
          owners.get(path).push({ id: local.id, digest: local.digest });
        }
      }
    }

    const required = [...new Set(requiredPaths.map((x) => text(x, "required path")))].sort();
    const missing = required.filter((path) => !merged.has(path));
    const ok = conflicts.length === 0 && missing.length === 0;
    const globalSection = ok ? canonical(unflatten(merged)) : null;
    const body = {
      schema: SCHEMA,
      ok,
      unique: ok,
      sectionDigests: sections.map((x) => x.digest),
      paths: [...merged.keys()].sort(),
      requiredPaths: required,
      missing,
      overlaps,
      conflicts,
      globalSection,
      evidenceRefs: [...new Set(sections.flatMap((x) => x.evidenceRefs))].sort(),
    };
    return Object.freeze({ ...body, digest: E.demoDigest(body) });
  }

  function glueResourceMetadata(resources, options = {}) {
    if (!Array.isArray(resources)) throw new TypeError("resources must be an array");
    return glue(resources.map((resource, index) => ({
      id: resource.id || `resource-${index}`,
      kind: resource.kind || "resource",
      values: resource.metadata || {},
      evidenceRefs: resource.metadata?.evidenceRefs || [],
    })), options);
  }

  const API = { SCHEMA, LocalSection, flatten, glue, glueResourceMetadata };
  root.HolotradeGluing = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
