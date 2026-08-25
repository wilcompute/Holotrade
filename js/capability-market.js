// ======================================================================
// HOLOTRADE CAPABILITY-TRANSITION MARKET
//
// A vendor capability is modeled as an immutable resource. Applying it to a
// node profile is itself a Projection -> Execution -> Emission transition,
// so capability upgrades are auditable state changes rather than mutable
// flags in a central registry.
//
// This is a prototype market/state-machine. It does not perform firmware
// installation, hardware reconfiguration, licensing, or remote attestation.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const P = root.HolotradeProjection ||
    (typeof require !== "undefined" ? require("./projection.js") : null);
  if (!E || !P) throw new Error("capability-market requires evidence.js and projection.js");

  const PROFILE_SCHEMA = "holotrade.node-capability-profile.v1";
  const OFFER_SCHEMA = "holotrade.capability-offer.v1";

  function text(value, name) {
    if (typeof value !== "string" || value.trim().length === 0) throw new TypeError(`${name} must be a non-empty string`);
    return value.trim();
  }

  function stringSet(value, name) {
    if (!Array.isArray(value)) throw new TypeError(`${name} must be an array`);
    return [...new Set(value.map((x) => text(x, `${name} entry`)))].sort();
  }

  function profileResource(spec) {
    if (!spec || typeof spec !== "object") throw new TypeError("profile spec required");
    const nodeId = text(spec.nodeId, "nodeId");
    const capabilities = stringSet(spec.capabilities || [], "capabilities");
    const evidenceRefs = stringSet(spec.evidenceRefs || [], "evidenceRefs");
    const payload = {
      schema: PROFILE_SCHEMA,
      nodeId,
      hardwareKind: text(spec.hardwareKind || "unknown", "hardwareKind"),
      capabilities,
      evidenceRefs,
      generation: Number.isInteger(spec.generation) && spec.generation >= 0 ? spec.generation : 0,
    };
    return new P.ResourceRef({
      id: spec.id || `node-profile:${nodeId}:g${payload.generation}`,
      kind: "node-profile",
      role: spec.role || "node-profile",
      digest: E.demoDigest(payload),
      metadata: payload,
    });
  }

  class CapabilityOffer {
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("offer spec required");
      this.schema = OFFER_SCHEMA;
      this.id = text(spec.id, "offer id");
      this.vendor = text(spec.vendor, "vendor");
      this.capabilities = Object.freeze(stringSet(spec.capabilities || [], "capabilities"));
      if (this.capabilities.length === 0) throw new TypeError("offer must add at least one capability");
      this.hardwareKinds = Object.freeze(stringSet(spec.hardwareKinds || ["any"], "hardwareKinds"));
      this.evidenceRefs = Object.freeze(stringSet(spec.evidenceRefs || [], "evidenceRefs"));
      this.price = Number(spec.price);
      if (!Number.isFinite(this.price) || this.price < 0) throw new RangeError("price must be non-negative");
      this.metadata = Object.freeze(JSON.parse(E.canonicalJson(spec.metadata || {})));
      this.digest = E.demoDigest(this.body());
      Object.freeze(this);
    }

    body() {
      return {
        schema: this.schema,
        id: this.id,
        vendor: this.vendor,
        capabilities: this.capabilities,
        hardwareKinds: this.hardwareKinds,
        evidenceRefs: this.evidenceRefs,
        price: this.price,
        metadata: this.metadata,
      };
    }

    asResource() {
      return new P.ResourceRef({
        id: `capability:${this.id}`,
        kind: "capability",
        role: "capability",
        digest: this.digest,
        metadata: this.body(),
      });
    }

    compatible(profile) {
      const kind = profile.metadata?.hardwareKind || "unknown";
      return this.hardwareKinds.includes("any") || this.hardwareKinds.includes(kind);
    }
  }

  class CapabilityExchange {
    constructor(offers = []) {
      this.offers = offers.map((x) => x instanceof CapabilityOffer ? x : new CapabilityOffer(x));
    }

    list(profile, requiredCapabilities = []) {
      const required = stringSet(requiredCapabilities, "requiredCapabilities");
      const have = new Set(profile.metadata?.capabilities || []);
      return this.offers
        .filter((offer) => offer.compatible(profile))
        .map((offer) => {
          const adds = offer.capabilities.filter((cap) => !have.has(cap));
          const covers = required.filter((cap) => have.has(cap) || offer.capabilities.includes(cap));
          return { offer, adds, covers, complete: covers.length === required.length };
        })
        .filter((row) => row.adds.length > 0)
        .sort((a, b) => Number(b.complete) - Number(a.complete) || a.offer.price - b.offer.price || a.offer.id.localeCompare(b.offer.id));
    }
  }

  class CapabilityTransitionEngine {
    constructor(projectionEngine) {
      if (!projectionEngine || typeof projectionEngine.createPlan !== "function") {
        throw new TypeError("CapabilityTransitionEngine requires ProjectionEngine");
      }
      this.projectionEngine = projectionEngine;
    }

    projection(profile, offer, { workloadId = "finetune", evidencePolicy = E.POLICY.VERIFIED } = {}) {
      const cap = offer instanceof CapabilityOffer ? offer : new CapabilityOffer(offer);
      if (!cap.compatible(profile)) throw new Error("capability offer is incompatible with node hardware kind");
      const current = new Set(profile.metadata?.capabilities || []);
      const adds = cap.capabilities.filter((x) => !current.has(x));
      if (adds.length === 0) throw new Error("capability transition is a no-op");
      const refs = [...new Set([...(profile.metadata?.evidenceRefs || []), ...cap.evidenceRefs])].sort();
      return new P.Projection({
        id: `projection:capability:${profile.id}:${cap.id}`,
        name: `apply ${cap.id} to ${profile.metadata.nodeId}`,
        service: "capability-transition",
        workloadId,
        inputs: [profile, cap.asResource()],
        grants: { network: [], services: [], secrets: [] },
        evidenceRefs: refs,
        evidencePolicy,
        outputKind: "node-profile",
        metadata: {
          nodeId: profile.metadata.nodeId,
          currentCapabilities: [...current].sort(),
          addedCapabilities: adds,
          vendor: cap.vendor,
          offerDigest: cap.digest,
          transitionPrice: cap.price,
        },
      });
    }

    emitProfile(projection, plan, receipt, profile, offer) {
      const cap = offer instanceof CapabilityOffer ? offer : new CapabilityOffer(offer);
      const capabilities = [...new Set([...(profile.metadata?.capabilities || []), ...cap.capabilities])].sort();
      const evidenceRefs = [...new Set([...(profile.metadata?.evidenceRefs || []), ...cap.evidenceRefs])].sort();
      const generation = (profile.metadata?.generation || 0) + 1;
      const emission = this.projectionEngine.emit(projection, plan, receipt, {
        kind: "node-profile",
        metadata: {
          schema: PROFILE_SCHEMA,
          nodeId: profile.metadata.nodeId,
          hardwareKind: profile.metadata.hardwareKind,
          capabilities,
          evidenceRefs,
          generation,
          vendor: cap.vendor,
          offerId: cap.id,
          offerDigest: cap.digest,
          transitionPrice: cap.price,
        },
      });
      return emission;
    }
  }

  const API = { PROFILE_SCHEMA, OFFER_SCHEMA, profileResource, CapabilityOffer, CapabilityExchange, CapabilityTransitionEngine };
  root.HolotradeCapabilityMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
