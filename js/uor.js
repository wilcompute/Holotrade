// ======================================================================
// HOLOTRADE UOR LAYER -- addresses and asset mobility policy
//
// A UOR is an unsigned 64-bit integer. Its layout is an invertible
// mixed-radix codec:
//
//   cell    = point * 1,296 + coset       (0 <= cell < 51,840)
//   raw     = payload * 51,840 + cell     (0 <= raw < 2^64)
//
// The quotient/remainder construction is exact. It does not pretend
// that 51,840 divides 2^64: there are 355,839,970,557,668 complete
// payload bands and a final band containing 42,496 cells. The average
// payload information budget is 64 - log2(51,840) = 48.338... bits,
// not a fixed-width 48-bit field.
//
// W(3,3) supplies the 40 x 1,296 cell labels and rank-3 routing
// relation. It does not, by itself, determine counterparties, market
// value, legal delivery scope, or whether a history entry is authentic.
// Those operational properties are represented below by an explicitly
// named venue policy mobility score. The score is a policy model, not
// an orbit-stabilizer theorem or a measured liquidity statistic.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  const UINT64_SPACE = 1n << 64n;
  const UINT64_MAX = UINT64_SPACE - 1n;

  // ---- the exact address codec ---------------------------------------
  const UOR = {
    codec: "uint64-mixed-radix-v1",
    bits: 64,
    sylowChoices: 40,             // n_3(Sp(4,F_3)) = v
    normaliserOrder: 1296,        // |N_G(P_3)| = mu^2 * q^(q+1) = 16 * 81
    autOrder: 51840,              // 40 * 1296
    kolmogorovKernel: 21,         // K(W(3,3)) <= 21 bits
    get canonicalCells() { return this.sylowChoices * this.normaliserOrder; },
    get addressSpaceSize() { return UINT64_SPACE; },
    get maxValue() { return UINT64_MAX; },
    get completePayloadBands() { return UINT64_SPACE / BigInt(this.canonicalCells); },
    get finalPayloadBandCells() { return Number(UINT64_SPACE % BigInt(this.canonicalCells)); },
    // Average information budget after selecting one of 51,840 cells.
    // The mixed-radix payload is a BigInt quotient, not a fixed bitfield.
    get payloadBits() { return this.bits - Math.log2(this.canonicalCells); },
    get contingentBits() { return this.payloadBits - this.kolmogorovKernel; },
  };

  function integerInRange(value, name, min, max) {
    if (typeof value !== "number" || !Number.isInteger(value) || value < min || value > max) {
      throw new RangeError(`${name} must be an integer in [${min}, ${max}]`);
    }
    return value;
  }

  function unsignedBigInt(value, name, max = UINT64_MAX) {
    let parsed;
    if (typeof value === "bigint") {
      parsed = value;
    } else if (typeof value === "number" && Number.isSafeInteger(value)) {
      parsed = BigInt(value);
    } else if (typeof value === "string" && /^(0|[1-9][0-9]*)$/.test(value)) {
      parsed = BigInt(value);
    } else {
      throw new TypeError(`${name} must be a non-negative BigInt, safe integer, or decimal string`);
    }
    if (parsed < 0n || parsed > max) {
      throw new RangeError(`${name} must be in [0, ${max}]`);
    }
    return parsed;
  }

  // The Bose-Mesner rank-3 split of the 40-point shell as seen from any
  // one point: itself, its 12 neighbours, the 27 it cannot reach in one
  // hop. 1 + 12 + 27 = 40. This is the natural three-tier depth
  // classification for a book quoted from a given anchor.
  const SHELL = { self: 1, adjacent: 12, distant: 27 };

  class UORAddress {
    /**
     * @param point    which of the 40 substrate points (the Sylow choice)
     * @param coset    coset representative in [0, 1296)
     * @param payload  mixed-radix quotient as BigInt, safe integer, or decimal string
     */
    constructor(point, coset, payload = 0n) {
      this.point = integerInRange(point, "point", 0, UOR.sylowChoices - 1);
      this.coset = integerInRange(coset, "coset", 0, UOR.normaliserOrder - 1);
      this.payload = unsignedBigInt(payload, "payload");
      if (this.toBigInt() > UINT64_MAX) {
        throw new RangeError("point, coset, and payload do not fit in an unsigned 64-bit UOR");
      }
      Object.freeze(this);
    }

    /** Derive a stable 64-bit demo address from a non-empty identifier. */
    static from(id) {
      if (id === null || id === undefined || String(id).length === 0) {
        throw new TypeError("id must be a non-empty identifier");
      }
      const text = String(id);
      const hi = BigInt(S.hash32(`uor:v1:hi:${text}`));
      const lo = BigInt(S.hash32(`uor:v1:lo:${text}`));
      return UORAddress.fromBigInt((hi << 32n) | lo);
    }

    /** Decode an unsigned 64-bit value without losing precision. */
    static fromBigInt(value) {
      const raw = unsignedBigInt(value, "UOR value");
      const radix = BigInt(UOR.canonicalCells);
      const cell = Number(raw % radix);
      const payload = raw / radix;
      return new UORAddress(
        Math.floor(cell / UOR.normaliserOrder),
        cell % UOR.normaliserOrder,
        payload
      );
    }

    /** Parse the canonical wire representation: exactly `uor:` + 16 hex digits. */
    static fromHex(encoded) {
      if (typeof encoded !== "string" || !/^uor:[0-9a-fA-F]{16}$/.test(encoded)) {
        throw new TypeError("UOR text must match uor:[0-9a-fA-F]{16}");
      }
      return UORAddress.fromBigInt(BigInt(`0x${encoded.slice(4)}`));
    }

    /** The substrate cell index: one of the 51,840 canonical routing cells. */
    get cell() {
      return this.point * UOR.normaliserOrder + this.coset;
    }

    /** Encode as an unsigned 64-bit BigInt. */
    toBigInt() {
      return this.payload * BigInt(UOR.canonicalCells) + BigInt(this.cell);
    }

    /** Render the canonical 64-bit wire form. */
    toHex() {
      return `uor:${this.toBigInt().toString(16).padStart(16, "0")}`;
    }

    /** JSON uses the canonical string so BigInt never reaches JSON.stringify. */
    toJSON() {
      return this.toHex();
    }

    /** The F_3^4 vector this address resolves to -- address IS route. */
    get vector() {
      return S.POINTS[this.point].vec;
    }

    /**
     * The rank-3 relation between two addresses. Identity, intersecting
     * (collinear -- one hop), or disjoint (two hops via one of mu = 4
     * relays). Nothing else exists; that is what rank 3 means.
     */
    relationTo(other) {
      if (!(other instanceof UORAddress)) throw new TypeError("other must be a UORAddress");
      if (this.point === other.point) return "identity";
      return S.isAdjacent(this.point, other.point) ? "intersecting" : "disjoint";
    }
  }

  // --------------------------------------------------------------------
  // Smart asset
  // --------------------------------------------------------------------

  // Venue policy defaults for the fraction of the 40 reference delivery
  // regions in which an asset is expected to remain eligible. These are
  // deliberately named scores: they are configurable policy assumptions,
  // not subgroup orders, prices, or observed order-book liquidity.
  const POLICY_MOBILITY_SCORE = Object.freeze({
    "data-residency": 1 / 3,
    "bare-metal": 1 / 2,
    "single-tenant": 1 / 2,
    "air-gapped": 1 / UOR.sylowChoices,
    "gpu-affinity": 2 / 3,
    "long-lease": 1 / 2,
    "magic-capable": 1,
  });

  function scoreInUnitInterval(value, name) {
    if (typeof value !== "number" || !Number.isFinite(value) || value < 0 || value > 1) {
      throw new RangeError(`${name} must be a finite number in [0, 1]`);
    }
    return value;
  }

  function policyList(value) {
    if (!Array.isArray(value)) throw new TypeError("policies must be an array");
    const unique = [];
    for (const policy of value) {
      if (typeof policy !== "string" || !Object.hasOwn(POLICY_MOBILITY_SCORE, policy)) {
        throw new RangeError(`unknown mobility policy: ${String(policy)}`);
      }
      if (!unique.includes(policy)) unique.push(policy);
    }
    return unique;
  }

  function policyScore(policies) {
    // Eligibility is an intersection. Without a measured overlap matrix,
    // multiplying policy fractions would invent statistical independence;
    // the tightest configured policy is the conservative stated estimate.
    return policies.reduce(
      (score, policy) => Math.min(score, POLICY_MOBILITY_SCORE[policy]),
      1
    );
  }

  function marketBreadthBand(score) {
    scoreInUnitInterval(score, "marketBreadthScore");
    if (score >= 0.8) return "broad";
    if (score >= 0.45) return "multi-region";
    if (score >= 0.18) return "restricted";
    return "site-bound";
  }

  class SmartAsset {
    /**
     * A tradeable object with a UOR identity and explicit delivery-policy
     * metadata. `marketBreadthScore` may be supplied from measured venue
     * eligibility; otherwise the documented policy defaults above apply.
     */
    constructor(spec) {
      if (!spec || typeof spec !== "object") throw new TypeError("asset spec must be an object");
      if (spec.id === null || spec.id === undefined || String(spec.id).length === 0) {
        throw new TypeError("asset id must be a non-empty identifier");
      }
      this.id = spec.id;
      this.kind = spec.kind;              // node | composite | plan | lease | capacity
      this.underlying = spec.underlying;
      this.address = spec.address || UORAddress.from(spec.id);
      if (!(this.address instanceof UORAddress)) throw new TypeError("asset address must be a UORAddress");
      this.createdAt = spec.createdAt ?? Date.now();
      if (typeof this.createdAt !== "number" || !Number.isFinite(this.createdAt) || this.createdAt < 0) {
        throw new RangeError("createdAt must be a non-negative finite timestamp");
      }

      this.policies = Object.freeze(policyList(spec.policies ?? spec.constraints ?? []));
      this.constraints = this.policies; // compatibility alias
      this.marketBreadthOverride = spec.marketBreadthScore === undefined
        ? null
        : scoreInUnitInterval(spec.marketBreadthScore, "marketBreadthScore");

      const suppliedHistory = spec.mobilityHistory ?? spec.orbitHistory;
      if (suppliedHistory !== undefined && !Array.isArray(suppliedHistory)) {
        throw new TypeError("mobilityHistory must be a non-empty array");
      }
      this.mobilityHistory = suppliedHistory
        ? suppliedHistory.map((entry) => ({ ...entry }))
        : [{ cell: this.address.cell, ts: this.createdAt, event: "minted" }];
      if (this.mobilityHistory.length === 0) {
        throw new TypeError("mobilityHistory must be a non-empty array");
      }
      this.orbitHistory = this.mobilityHistory; // compatibility alias
    }

    /** Policy-estimated mobility in [0,1], or the caller's measured override. */
    policyMobilityScore() {
      return this.marketBreadthOverride ?? policyScore(this.policies);
    }

    /** Fraction of the venue's reference delivery regions that are eligible. */
    marketBreadthScore() {
      return this.policyMobilityScore();
    }

    /** Estimated eligible regions out of the 40-region reference universe. */
    marketBreadth() {
      return Math.round(UOR.sylowChoices * this.marketBreadthScore());
    }

    /**
     * Separate the policy estimate from demonstrated movement. Neither
     * number is a price or an order-book liquidity measurement.
     */
    tradeability() {
      const distinct = new Set(
        this.mobilityHistory
          .filter((entry) => Number.isInteger(entry.cell))
          .map((entry) => Math.floor(entry.cell / UOR.normaliserOrder))
      ).size;
      const potential = this.marketBreadth();
      const demonstrated = Math.min(1, distinct / Math.max(1, Math.min(potential, 12)));
      const score = this.marketBreadthScore();
      return {
        policyMobilityScore: this.policyMobilityScore(),
        marketBreadthScore: score,
        demonstratedMobilityScore: demonstrated,
        moves: this.mobilityHistory.length - 1,
        coVolume: score, // compatibility alias; not a mathematical co-volume
        demonstrated,   // compatibility alias
      };
    }

    /**
     * Return recorded movement history and structural anomalies. Geometry
     * cannot authenticate an entry because W(3,3) has diameter two; a
     * signed audit chain is required for authenticity.
     */
    provenance() {
      const chain = this.mobilityHistory;
      const anomalies = [];
      for (let i = 0; i < chain.length; i++) {
        const entry = chain[i];
        if (!entry || !Number.isInteger(entry.cell) || entry.cell < 0 || entry.cell >= UOR.canonicalCells) {
          anomalies.push({ index: i, reason: "cell outside canonical range" });
        }
        if (!entry || typeof entry.ts !== "number" || !Number.isFinite(entry.ts) || entry.ts < 0) {
          anomalies.push({ index: i, reason: "invalid timestamp" });
        } else if (i > 0 && typeof chain[i - 1].ts === "number" && entry.ts < chain[i - 1].ts) {
          anomalies.push({ index: i, reason: "timestamp precedes previous entry" });
        }
        if (!entry || typeof entry.event !== "string" || entry.event.trim().length === 0) {
          anomalies.push({ index: i, reason: "missing event label" });
        }
      }
      return {
        chain: chain.map((entry) => ({ ...entry })),
        anomalies,
        structurallyValid: anomalies.length === 0,
        authenticated: false,
        clean: anomalies.length === 0, // compatibility alias: structural only
        depth: chain.length,
      };
    }

    /** Record a structurally valid movement entry. This does not sign it. */
    move(newAddress, event = "transfer") {
      if (!(newAddress instanceof UORAddress)) throw new TypeError("newAddress must be a UORAddress");
      if (typeof event !== "string" || event.trim().length === 0) {
        throw new TypeError("event must be a non-empty string");
      }
      this.address = newAddress;
      this.mobilityHistory.push({ cell: newAddress.cell, ts: Date.now(), event: event.trim() });
      if (this.mobilityHistory.length > 64) this.mobilityHistory.shift();
      return this;
    }

    // Deprecated compatibility methods. They intentionally do not return
    // a fabricated subgroup order. Consumers should use the named scores.
    stabiliserOrder() { return null; }
    orbitSize() { return this.marketBreadth(); }
    coVolume() { return this.marketBreadthScore(); }

    /** Full asset card for the UI. */
    describe() {
      const t = this.tradeability();
      return {
        id: this.id,
        kind: this.kind,
        uor: this.address.toHex(),
        cell: this.address.cell,
        point: this.address.point,
        vector: this.address.vector.join(""),
        policyMobilityScore: t.policyMobilityScore,
        marketBreadthScore: t.marketBreadthScore,
        marketBreadth: this.marketBreadth(),
        marketBreadthBand: marketBreadthBand(t.marketBreadthScore),
        policies: this.policies,
        provenance: this.provenance(),
        moves: t.moves,
        // Compatibility fields for the existing UI. `stabiliser` is null
        // so it cannot be mistaken for a computed group order.
        stabiliser: null,
        orbit: this.marketBreadth(),
        coVolume: t.marketBreadthScore,
        liquidity: liquidityBand(t.marketBreadthScore),
        constraints: this.policies,
      };
    }
  }

  // Deprecated inverse-score adapter for the current UI table. It exists
  // only until that view consumes POLICY_MOBILITY_SCORE directly.
  const CONSTRAINT_WEIGHT = Object.freeze(Object.fromEntries(
    Object.entries(POLICY_MOBILITY_SCORE).map(([policy, score]) => [policy, 1 / score])
  ));

  /** Deprecated visual-label adapter; this is not measured liquidity. */
  function liquidityBand(marketBreadthScore) {
    if (marketBreadthScore >= 0.8) return "deep";
    if (marketBreadthScore >= 0.45) return "liquid";
    if (marketBreadthScore >= 0.18) return "thin";
    return "bilateral";
  }

  // --------------------------------------------------------------------
  // Registry -- the asset side of the venue
  // --------------------------------------------------------------------

  class AssetRegistry {
    constructor(fleet) {
      this.fleet = fleet;
      this.assets = new Map();
    }

    /** Mint (or fetch) the smart asset that wraps a node or composite. */
    forNode(node) {
      if (this.assets.has(node.id)) return this.assets.get(node.id);
      const policies = [];
      if (node.hardware.kind === "photonic") policies.push("magic-capable");
      if (node.hardware.kind === "fpga") policies.push("bare-metal");
      // datacentres in regulated regions carry residency constraints
      if (["ARN-1", "DUB-3", "SIN-2"].includes(node.dcId)) policies.push("data-residency");
      if (node.isComposite) policies.push("single-tenant");

      const asset = new SmartAsset({
        id: node.id,
        kind: node.isComposite ? "composite" : "node",
        underlying: node,
        address: new UORAddress(node.cellPoint, S.hash32(node.id) % UOR.normaliserOrder, S.hash32(node.address)),
        policies,
      });
      this.assets.set(node.id, asset);
      return asset;
    }

    /** Wrap an execution plan as a tradeable asset -- sellable before it runs. */
    forPlan(plan) {
      if (this.assets.has(plan.id)) return this.assets.get(plan.id);
      const asset = new SmartAsset({
        id: plan.id,
        kind: "plan",
        underlying: plan,
        address: UORAddress.from(plan.digest),
        policies: plan.magicBudget > 0 ? ["magic-capable"] : [],
      });
      this.assets.set(plan.id, asset);
      return asset;
    }

    /** Policy-estimated delivery breadth across the listed fleet. */
    marketBreadthProfile() {
      const bands = { broad: 0, "multi-region": 0, restricted: 0, "site-bound": 0 };
      let totalScore = 0;
      let n = 0;
      for (const node of this.fleet.listedNodes()) {
        const a = this.forNode(node);
        const score = a.marketBreadthScore();
        bands[marketBreadthBand(score)]++;
        totalScore += score;
        n++;
      }
      return { bands, meanMarketBreadthScore: n ? totalScore / n : 0, count: n };
    }

    /** Deprecated shape retained for the existing dashboard. */
    liquidityProfile() {
      const bands = { deep: 0, liquid: 0, thin: 0, bilateral: 0 };
      let totalScore = 0;
      let n = 0;
      for (const node of this.fleet.listedNodes()) {
        const score = this.forNode(node).marketBreadthScore();
        bands[liquidityBand(score)]++;
        totalScore += score;
        n++;
      }
      const meanMarketBreadthScore = n ? totalScore / n : 0;
      return {
        bands,
        meanMarketBreadthScore,
        meanCoVolume: meanMarketBreadthScore,
        count: n,
      };
    }

    /**
     * Rank-3 depth from an anchor: the book as the substrate sees it.
     * 1 self, 12 intersecting, 27 disjoint for the 40 geometric points.
     * Listed-node counts need not have that ratio because a fleet may
     * place zero, one, or many nodes at each point.
     */
    shellFrom(anchorNode) {
      const anchor = this.forNode(anchorNode).address;
      const tiers = { identity: [], intersecting: [], disjoint: [] };
      for (const node of this.fleet.listedNodes()) {
        const a = this.forNode(node);
        tiers[anchor.relationTo(a.address)].push(node);
      }
      const total = tiers.identity.length + tiers.intersecting.length + tiers.disjoint.length;
      const geometryRatios = {
        identity: SHELL.self / UOR.sylowChoices,
        intersecting: SHELL.adjacent / UOR.sylowChoices,
        disjoint: SHELL.distant / UOR.sylowChoices,
      };
      return {
        tiers,
        counts: {
          identity: tiers.identity.length,
          intersecting: tiers.intersecting.length,
          disjoint: tiers.disjoint.length,
        },
        ratios: total
          ? {
              identity: tiers.identity.length / total,
              intersecting: tiers.intersecting.length / total,
              disjoint: tiers.disjoint.length / total,
            }
          : null,
        geometryRatios,
        expectedRatios: geometryRatios, // compatibility alias; not a fleet expectation
        geometryShell: SHELL,
        expected: SHELL, // compatibility alias
        total,
      };
    }
  }

  // --------------------------------------------------------------------
  // Venue capacity -- dimensionally explicit dashboard transforms
  // --------------------------------------------------------------------

  /**
   * Apply the prototype's documented dimensionless factors to a supplied
   * transaction rate T (transactions/second). These are model outputs,
   * not measured ceilings or deployment guarantees. A scan of N cells at
   * T transactions/second takes N/T seconds.
   */
  function venueCapacity(tps) {
    const T = tps === undefined ? 70e6 : tps;
    if (typeof T !== "number" || !Number.isFinite(T) || T <= 0) {
      throw new RangeError("tps must be a positive finite number");
    }
    const fullCellScanSeconds = UOR.canonicalCells / T;
    const illustrativeTransforms = {
      // Dimensionless display factors applied to T. These values are not
      // measured throughput, protocol limits, or service-level objectives.
      conjugacyScale: UOR.autOrder / S.CONST.coxeterE8,
      conjugacyScaledRate: T * (UOR.autOrder / S.CONST.coxeterE8),
      logicalScale: S.CONST.cssRate,
      logicalScaledRate: T * S.CONST.cssRate,
      coherenceScale: 1 / S.CONST.tauO,
      coherenceScaledRate: T / S.CONST.tauO,
    };
    return {
      tps: T,
      illustrativeTransforms,
      fullCellScanSeconds,
      // Compatibility name with corrected units: 51,840 transactions / T tx/s.
      fullOrbitSeconds: fullCellScanSeconds,
    };
  }

  const API = {
    UOR,
    SHELL,
    UORAddress,
    SmartAsset,
    AssetRegistry,
    POLICY_MOBILITY_SCORE,
    marketBreadthBand,
    venueCapacity,
    // Deprecated compatibility exports.
    CONSTRAINT_WEIGHT,
    liquidityBand,
  };
  root.HolotradeUOR = API;
  root.UORAddress = UORAddress;
  root.SmartAsset = SmartAsset;
  root.AssetRegistry = AssetRegistry;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
