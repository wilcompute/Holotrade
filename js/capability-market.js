// ======================================================================
// HOLOTRADE CAPABILITY-TRANSITION MARKET
//
// Capabilities are immutable resources. Applying one or more offers to a node
// profile is itself a Projection -> Execution -> Emission transition, so a
// capability upgrade is auditable state rather than a mutable registry flag.
//
// v2 adds exact bundle selection over the listed offers: for a required set of
// capabilities, choose the compatible bundle with minimum modeled price, then
// fewest offers, then lexical offer ids. This is a market optimizer over model
// prices, not a deployed procurement or licensing system.
// ======================================================================

(function (root) {
  "use strict";

  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  const P = root.HolotradeProjection ||
    (typeof require !== "undefined" ? require("./projection.js") : null);
  if (!E || !P) throw new Error("capability-market requires evidence.js and projection.js");

  const PROFILE_SCHEMA = "holotrade.node-capability-profile.v2";
  const OFFER_SCHEMA = "holotrade.capability-offer.v2";

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

    /** Exact minimum-price set cover across compatible offers. */
    bestBundle(profile, requiredCapabilities = []) {
      const required = stringSet(requiredCapabilities, "requiredCapabilities");
      const have = new Set(profile.metadata?.capabilities || []);
      const missing = required.filter((cap) => !have.has(cap));
      if (missing.length === 0) return Object.freeze({ complete: true, offers: [], adds: [], totalPrice: 0, required, missing: [] });
      if (missing.length > 24) throw new RangeError("exact bundle optimizer supports at most 24 missing capabilities");
      const index = new Map(missing.map((cap, i) => [cap, i]));
      const fullMask = (1 << missing.length) - 1;
      const compatible = this.offers.filter((offer) => offer.compatible(profile)).map((offer) => {
        let mask = 0;
        for (const cap of offer.capabilities) if (index.has(cap)) mask |= 1 << index.get(cap);
        return { offer, mask };
      }).filter((row) => row.mask !== 0);

      const best = new Map([[0, { price: 0, ids: [], offers: [] }]]);
      for (const row of compatible) {
        const snapshot = [...best.entries()];
        for (const [mask, state] of snapshot) {
          const nextMask = mask | row.mask;
          const candidate = {
            price: state.price + row.offer.price,
            ids: [...state.ids, row.offer.id].sort(),
            offers: [...state.offers, row.offer],
          };
          const prior = best.get(nextMask);
          const candidateKey = `${candidate.price.toFixed(12)}|${String(candidate.ids.length).padStart(4, "0")}|${candidate.ids.join("|")}`;
          const priorKey = prior ? `${prior.price.toFixed(12)}|${String(prior.ids.length).padStart(4, "0")}|${prior.ids.join("|")}` : null;
          if (!prior || candidateKey < priorKey) best.set(nextMask, candidate);
        }
      }
      const winner = best.get(fullMask);
      if (!winner) return Object.freeze({ complete: false, offers: [], adds: [], totalPrice: null, required, missing });
      const ordered = [...winner.offers].sort((a, b) => a.id.localeCompare(b.id));
      const adds = [...new Set(ordered.flatMap((offer) => offer.capabilities).filter((cap) => !have.has(cap)))].sort();
      return Object.freeze({
        complete: true,
        offers: Object.freeze(ordered),
        offerIds: Object.freeze(ordered.map((x) => x.id)),
        adds: Object.freeze(adds),
        totalPrice: winner.price,
        required: Object.freeze(required),
        missing: Object.freeze(missing),
        digest: E.demoDigest({ profile: profile.digest, required, offerDigests: ordered.map((x) => x.digest), totalPrice: winner.price }),
      });
    }
  }

  class CapabilityTransitionEngine {
    constructor(projectionEngine) {
      if (!projectionEngine || typeof projectionEngine.createPlan !== "function") throw new TypeError("CapabilityTransitionEngine requires ProjectionEngine");
      this.projectionEngine = projectionEngine;
    }

    bundleProjection(profile, offers, { workloadId = "finetune", evidencePolicy = E.POLICY.VERIFIED } = {}) {
      const caps = offers.map((x) => x instanceof CapabilityOffer ? x : new CapabilityOffer(x)).sort((a, b) => a.id.localeCompare(b.id));
      if (caps.length === 0) throw new Error("at least one capability offer is required");
      for (const cap of caps) if (!cap.compatible(profile)) throw new Error(`capability offer ${cap.id} is incompatible with node hardware kind`);
      const current = new Set(profile.metadata?.capabilities || []);
      const adds = [...new Set(caps.flatMap((cap) => cap.capabilities).filter((x) => !current.has(x)))].sort();
      if (adds.length === 0) throw new Error("capability transition is a no-op");
      const refs = [...new Set([...(profile.metadata?.evidenceRefs || []), ...caps.flatMap((cap) => cap.evidenceRefs)])].sort();
      const totalPrice = caps.reduce((sum, cap) => sum + cap.price, 0);
      return new P.Projection({
        id: `projection:capability:${profile.id}:${E.demoDigest(caps.map((x) => x.digest)).slice(5, 17)}`,
        name: `apply ${caps.map((x) => x.id).join("+")} to ${profile.metadata.nodeId}`,
        service: "capability-transition",
        workloadId,
        inputs: [profile, ...caps.map((cap) => cap.asResource())],
        grants: { network: [], services: [], secrets: [] },
        evidenceRefs: refs,
        evidencePolicy,
        outputKind: "node-profile",
        metadata: {
          nodeId: profile.metadata.nodeId,
          currentCapabilities: [...current].sort(),
          addedCapabilities: adds,
          vendors: [...new Set(caps.map((x) => x.vendor))].sort(),
          offerIds: caps.map((x) => x.id),
          offerDigests: caps.map((x) => x.digest),
          transitionPrice: totalPrice,
        },
      });
    }

    projection(profile, offer, options = {}) {
      return this.bundleProjection(profile, [offer], options);
    }

    emitBundleProfile(projection, plan, receipt, profile, offers) {
      const caps = offers.map((x) => x instanceof CapabilityOffer ? x : new CapabilityOffer(x)).sort((a, b) => a.id.localeCompare(b.id));
      const capabilities = [...new Set([...(profile.metadata?.capabilities || []), ...caps.flatMap((cap) => cap.capabilities)])].sort();
      const evidenceRefs = [...new Set([...(profile.metadata?.evidenceRefs || []), ...caps.flatMap((cap) => cap.evidenceRefs)])].sort();
      const generation = (profile.metadata?.generation || 0) + 1;
      return this.projectionEngine.emit(projection, plan, receipt, {
        kind: "node-profile",
        metadata: {
          schema: PROFILE_SCHEMA,
          nodeId: profile.metadata.nodeId,
          hardwareKind: profile.metadata.hardwareKind,
          capabilities,
          evidenceRefs,
          generation,
          vendors: [...new Set(caps.map((x) => x.vendor))].sort(),
          offerIds: caps.map((x) => x.id),
          offerDigests: caps.map((x) => x.digest),
          transitionPrice: caps.reduce((sum, cap) => sum + cap.price, 0),
        },
      });
    }

    emitProfile(projection, plan, receipt, profile, offer) {
      return this.emitBundleProfile(projection, plan, receipt, profile, [offer]);
    }
  }

  const API = { PROFILE_SCHEMA, OFFER_SCHEMA, profileResource, CapabilityOffer, CapabilityExchange, CapabilityTransitionEngine };
  root.HolotradeCapabilityMarket = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
