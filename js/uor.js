// ======================================================================
// HOLOTRADE UOR LAYER -- the asset model
//
// Everything above this file trades. This file says WHAT a tradeable
// thing IS, and it takes the definition from the substrate rather than
// inventing one.
//
// ---------------------------------------------------------------------
// THE ADDRESS
//
// The forty vertices of W(3,3) are in canonical bijection with the
// forty Sylow-3 subgroups of Sp(4,F_3) -- n_3 = v = 40, the hidden
// Sylow bijection. So an object reference is naturally a pair (P, x):
// a Sylow subgroup and a coset representative. A flat 64-bit address
// space factors exactly:
//
//     2^64  =  40          x  1,296          x  3.55e14
//              Sylow choice   |N_G(P_3)|        contingent payload
//
// and 40 x 1296 = 51,840 = |Aut(W(3,3))|. Every address picks out
// exactly one substrate element times a contingent payload.
//
// The payload is computed here rather than quoted: 64 - log2(51840) =
// 48.34 bits. The source paper rounds this to ~49.2 and then states a
// residual of 43 bits after the 21-bit Kolmogorov bootstrap kernel,
// but 49.2 - 21 = 28.2, so those two figures do not both hold. We
// carry the computable one and report the kernel separately rather
// than propagate an arithmetic slip into a price.
//
// This is not decoration. It means an asset's identity and its position
// in the fabric are THE SAME 64 BITS -- there is no separate registry
// mapping ids to locations that can go stale, and no lookup to do.
// Resolve the address and you have located the object.
//
// ---------------------------------------------------------------------
// THE ASSET
//
// A smart asset is a self-funding, tradable workload with embedded
// economics. At substrate scale the minimum such object is the temporal
// Bell qutrit
//
//     |Omega> = q^(-1/2) SUM_j |j>_past |j>_future ,   q = 3
//
// whose stabiliser is a totally isotropic 2-space -- one of the forty
// lines. From that identification three market quantities are DEFINED
// rather than assumed:
//
//     tradeability  =  orbit-mobility under Aut(W)
//     provenance    =  orbit history
//     value         =  orbit-stabilizer co-volume
//
// The third is the one that earns its keep. By orbit-stabilizer,
// |orbit| = |G| / |Stab|, so an asset with a LARGE stabiliser has a
// SMALL orbit: few positions it can occupy, few counterparties, thin
// market. An asset with a small stabiliser ranges over a large orbit
// and is correspondingly liquid. Liquidity stops being a statistic
// gathered from the tape and becomes a computable property of the
// asset's own symmetry. The Bell-line orbit has size 40 with stabiliser
// order 1,296, and 40 x 1296 = 51,840 checks out.
//
// ---------------------------------------------------------------------
// THE LIFECYCLE
//
//     Projection  ->  Execution  ->  Emission
//
// Projection assembles data and capabilities into a container; the
// projection definition is a stabiliser descriptor, picking out the
// subgroup that fixes the configuration. Execution evolves it under
// equivariant dynamics. Emission projects the result back into orbit
// space and emits the receipt.
//
// That is exactly the execution-plan lifecycle in execution.js -- sign,
// admit, run, settle -- which is why the two layers compose instead of
// merely coexisting.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  // ---- the address-space factorisation -------------------------------
  const UOR = {
    bits: 64,
    sylowChoices: 40,             // n_3(Sp(4,F_3)) = v
    normaliserOrder: 1296,        // |N_G(P_3)| = mu^2 * q^(q+1) = 16 * 81
    autOrder: 51840,              // 40 * 1296
    kolmogorovKernel: 21,         // K(W(3,3)) <= 21 bits
    get canonicalCells() { return this.sylowChoices * this.normaliserOrder; },
    get payloadBits() { return this.bits - Math.log2(this.canonicalCells); },
    get contingentBits() { return this.payloadBits - this.kolmogorovKernel; },
  };

  // The Bose-Mesner rank-3 split of the 40-point shell as seen from any
  // one point: itself, its 12 neighbours, the 27 it cannot reach in one
  // hop. 1 + 12 + 27 = 40. This is the natural three-tier depth
  // structure for a book quoted from a given anchor -- and it is the
  // same triad as the three container modes (component/service/policy),
  // because both are the q = 3 trichotomy.
  const SHELL = { self: 1, adjacent: 12, distant: 27 };

  class UORAddress {
    /**
     * @param point    which of the 40 substrate points (the Sylow choice)
     * @param coset    coset representative in [0, 1296)
     * @param payload  contingent state, 48.34 bits of address space
     */
    constructor(point, coset, payload = 0) {
      this.point = ((point % 40) + 40) % 40;
      this.coset = ((coset % UOR.normaliserOrder) + UOR.normaliserOrder) % UOR.normaliserOrder;
      this.payload = payload >>> 0;
    }

    /** Derive a canonical address from any string id -- deterministic. */
    static from(id) {
      const h = S.hash32(String(id));
      const h2 = S.hash32(String(id) + "|payload");
      return new UORAddress(h % 40, Math.floor(h / 40) % UOR.normaliserOrder, h2);
    }

    /** The substrate cell index: one of the 51,840 canonical orbit cells. */
    get cell() {
      return this.point * UOR.normaliserOrder + this.coset;
    }

    /** Render as the flat 64-bit hex address a UOR resolver would take. */
    toHex() {
      const hi = (this.cell >>> 0).toString(16).padStart(8, "0");
      const lo = (this.payload >>> 0).toString(16).padStart(8, "0");
      return `uor:${hi}${lo}`;
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
      if (this.point === other.point) return "identity";
      return S.isAdjacent(this.point, other.point) ? "intersecting" : "disjoint";
    }
  }

  // --------------------------------------------------------------------
  // Smart asset
  // --------------------------------------------------------------------

  class SmartAsset {
    /**
     * A tradeable object with embedded economics. Wraps whatever is
     * being sold -- a node, a composite, a lease, an execution plan --
     * and gives it a substrate identity, an orbit, and a valuation
     * derived from its symmetry rather than from its marketing.
     */
    constructor(spec) {
      this.id = spec.id;
      this.kind = spec.kind;              // node | composite | plan | lease | capacity
      this.underlying = spec.underlying;
      this.address = spec.address || UORAddress.from(spec.id);
      this.createdAt = spec.createdAt || Date.now();

      // orbit history: every position this asset has occupied, in order.
      // This IS the provenance -- not a log kept alongside the asset,
      // but the asset's own trajectory through the automorphism group.
      this.orbitHistory = spec.orbitHistory || [{ cell: this.address.cell, ts: this.createdAt, event: "minted" }];

      // the constraints that fix this asset in place. Each one shrinks
      // the orbit and therefore the liquidity.
      this.constraints = spec.constraints || [];
    }

    /**
     * Stabiliser order: how much of Aut(W) fixes this asset where it is.
     *
     * Every real-world constraint is a symmetry the asset does NOT have.
     * A node pinned to one datacentre by data-residency law cannot be
     * moved by the automorphisms that would move it; a bare-metal
     * reservation is fixed harder still. Each constraint multiplies the
     * stabiliser, and by orbit-stabilizer that divides the orbit.
     */
    stabiliserOrder() {
      // The Bell-line stabiliser is the baseline: mu^2 * q^(q+1) = 1296.
      let stab = UOR.normaliserOrder;
      for (const c of this.constraints) {
        stab *= CONSTRAINT_WEIGHT[c] || 2;
      }
      return Math.min(UOR.autOrder, stab);
    }

    /**
     * Orbit size = |G| / |Stab|. The number of distinct positions this
     * asset can legally occupy -- which is the number of places a
     * counterparty could take delivery. This is the asset's addressable
     * market, computed rather than surveyed.
     */
    orbitSize() {
      return Math.max(1, Math.round(UOR.autOrder / this.stabiliserOrder()));
    }

    /**
     * VALUE = ORBIT-STABILIZER CO-VOLUME.
     *
     * Normalised to [0,1] against the maximal orbit. An unconstrained
     * asset scores 1: it can be delivered anywhere in the fabric, so
     * every participant is a potential counterparty. A fully pinned
     * asset scores near 0: it is worth whatever its single possible
     * counterparty will pay.
     *
     * This is a LIQUIDITY multiplier, and it belongs on the quote next
     * to the six pricing multipliers. It is the honest reason a
     * residency-pinned node in one jurisdiction should not trade at the
     * same price as an identical unpinned node.
     */
    coVolume() {
      return this.orbitSize() / (UOR.autOrder / UOR.normaliserOrder);
    }

    /**
     * Tradeability = orbit-mobility. How much of its own orbit this
     * asset has actually traversed. An asset that has moved is an asset
     * with demonstrated mobility; one that has never moved may be
     * mobile in principle and illiquid in fact.
     */
    tradeability() {
      const distinct = new Set(this.orbitHistory.map((h) => h.cell)).size;
      const potential = this.orbitSize();
      const demonstrated = Math.min(1, distinct / Math.max(1, Math.min(potential, 12)));
      return { coVolume: this.coVolume(), demonstrated, moves: this.orbitHistory.length - 1 };
    }

    /**
     * Provenance = orbit history. Returned as a chain, so a buyer can
     * see every position this asset has held and every event that moved
     * it. Hallucinated or forged provenance shows up as an orbit
     * anomaly: a transition between cells that no automorphism connects.
     */
    provenance() {
      const chain = this.orbitHistory;
      const anomalies = [];
      for (let i = 1; i < chain.length; i++) {
        const from = Math.floor(chain[i - 1].cell / UOR.normaliserOrder);
        const to = Math.floor(chain[i].cell / UOR.normaliserOrder);
        // a legal move is identity, one hop, or two hops -- diameter 2.
        // anything else did not happen on this fabric.
        if (from !== to && !S.isAdjacent(from, to)) {
          const relays = S.commonNeighbours(from, to);
          if (relays.length === 0) anomalies.push({ index: i, from, to, reason: "no path in W(3,3)" });
        }
      }
      return { chain, anomalies, clean: anomalies.length === 0, depth: chain.length };
    }

    /** Record a move. The orbit history IS the provenance, so this is the only writer. */
    move(newAddress, event = "transfer") {
      this.address = newAddress;
      this.orbitHistory.push({ cell: newAddress.cell, ts: Date.now(), event });
      if (this.orbitHistory.length > 64) this.orbitHistory.shift();
      return this;
    }

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
        stabiliser: this.stabiliserOrder(),
        orbit: this.orbitSize(),
        coVolume: t.coVolume,
        liquidity: liquidityBand(t.coVolume),
        constraints: this.constraints,
        provenance: this.provenance(),
        moves: t.moves,
      };
    }
  }

  // How much each real-world constraint multiplies the stabiliser --
  // i.e. how much market it costs you.
  const CONSTRAINT_WEIGHT = {
    "data-residency": 3,        // must stay in one jurisdiction
    "bare-metal": 2,            // no migration off this chassis
    "single-tenant": 2,         // cannot be co-scheduled
    "air-gapped": 8,            // cannot leave the enclave at all
    "gpu-affinity": 1.5,        // needs a specific accelerator class
    "long-lease": 2,            // committed to one tenant for a term
    "magic-capable": 1,         // no mobility cost; it is a capability
  };

  function liquidityBand(coVolume) {
    if (coVolume >= 0.8) return "deep";
    if (coVolume >= 0.45) return "liquid";
    if (coVolume >= 0.18) return "thin";
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
      const constraints = [];
      if (node.hardware.kind === "photonic") constraints.push("magic-capable");
      if (node.hardware.kind === "fpga") constraints.push("bare-metal");
      // datacentres in regulated regions carry residency constraints
      if (["ARN-1", "DUB-3", "SIN-2"].includes(node.dcId)) constraints.push("data-residency");
      if (node.isComposite) constraints.push("single-tenant");

      const asset = new SmartAsset({
        id: node.id,
        kind: node.isComposite ? "composite" : "node",
        underlying: node,
        address: new UORAddress(node.cellPoint, S.hash32(node.id) % UOR.normaliserOrder, S.hash32(node.address)),
        constraints,
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
        constraints: plan.magicBudget > 0 ? ["magic-capable"] : [],
      });
      this.assets.set(plan.id, asset);
      return asset;
    }

    /**
     * The liquidity map: how the listed fleet distributes across the
     * four bands. A venue whose inventory is mostly "bilateral" has an
     * inventory problem, not a marketing problem, and this says so.
     */
    liquidityProfile() {
      const bands = { deep: 0, liquid: 0, thin: 0, bilateral: 0 };
      let totalCoVolume = 0;
      let n = 0;
      for (const node of this.fleet.listedNodes()) {
        const a = this.forNode(node);
        const cv = a.coVolume();
        bands[liquidityBand(cv)]++;
        totalCoVolume += cv;
        n++;
      }
      return { bands, meanCoVolume: n ? totalCoVolume / n : 0, count: n };
    }

    /**
     * Rank-3 depth from an anchor: the book as the substrate sees it.
     * 1 self, 12 intersecting, 27 disjoint. Every quote in the venue
     * falls into exactly one of three tiers relative to where your data
     * already is, and the tier is a fact about the geometry rather than
     * a routing heuristic.
     */
    shellFrom(anchorNode) {
      const anchor = this.forNode(anchorNode).address;
      const tiers = { identity: [], intersecting: [], disjoint: [] };
      for (const node of this.fleet.listedNodes()) {
        const a = this.forNode(node);
        tiers[anchor.relationTo(a.address)].push(node);
      }
      const total = tiers.identity.length + tiers.intersecting.length + tiers.disjoint.length;
      // The absolute counts depend on how many nodes are listed; the
      // RATIOS are the substrate fact and should hold at any fleet
      // size. 1 : 12 : 27 out of 40 is 2.5% / 30% / 67.5%.
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
        expectedRatios: {
          identity: SHELL.self / 40,
          intersecting: SHELL.adjacent / 40,
          disjoint: SHELL.distant / 40,
        },
        expected: SHELL,
        total,
      };
    }
  }

  // --------------------------------------------------------------------
  // Venue capacity -- the substrate's throughput identities
  // --------------------------------------------------------------------

  /**
   * What a venue running on this substrate can actually do, at a given
   * transaction rate. These are not projections; they are the substrate
   * identities evaluated at T, and every one of them is a CEILING that
   * a deployment claiming more has broken something to get.
   *
   *   conjugacy cadence   T * |Sp(4,3)|/h(E8)  =  T * 1728
   *                       and 1728 = k^3 = j(i), the modular
   *                       j-invariant at tau = i -- the venue's tempo
   *                       is a CM value
   *   logical rate        T * q^(q+1)/|E|      =  T * 27/80
   *                       the CSS [[240,81,4,3]]_3 rate cap. Claiming
   *                       more means you dropped substrate-coherent
   *                       encoding or measured a non-logical metric.
   *   coherence blocks    T / tau(O)           =  T / 384
   *                       the rate at which self-healing convergence
   *                       can be paid for
   *
   * And two hard floors:
   *   settlement latency  h(E8) ms = 30 ms. A 55-validator committee on
   *                       a planetary fabric should not converge faster;
   *                       anything that claims to has lost an invariant.
   *   logical error       q^(-mu^4) = 3^-256 ~ 1e-122.
   */
  function venueCapacity(tps) {
    const T = tps || 70e6;
    return {
      tps: T,
      conjugacyCadence: T * (UOR.autOrder / S.CONST.coxeterE8),   // T * 1728
      cadencePrefactor: UOR.autOrder / S.CONST.coxeterE8,
      logicalRate: T * S.CONST.cssRate,                            // T * 27/80
      coherenceBlocks: T / S.CONST.tauO,                           // T / 384
      settlementFloorMs: S.CONST.coxeterE8,                        // 30 ms
      logicalErrorRate: Math.pow(3, -256),
      bftCommittee: 55,
      bftThreshold: 1 / 3,
      // full traversal of Aut(W) at this rate, in seconds
      fullOrbitSeconds: UOR.autOrder / (T * 1e9),
    };
  }

  const API = { UOR, SHELL, UORAddress, SmartAsset, AssetRegistry, CONSTRAINT_WEIGHT, liquidityBand, venueCapacity };
  root.HolotradeUOR = API;
  root.UORAddress = UORAddress;
  root.SmartAsset = SmartAsset;
  root.AssetRegistry = AssetRegistry;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
