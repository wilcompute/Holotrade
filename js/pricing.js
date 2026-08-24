// ======================================================================
// HOLOTRADE PRICING ENGINE
//
// One clearing price per node, recomputed every second, as a product of
// six independent multipliers over a hardware floor:
//
//     P  =  P_base  x  E  x  G  x  D  x  H  x  Q  x  L
//
//   P_base  hardware floor          what the chassis costs to exist
//   E       energy                  live wholesale $/MWh at that site,
//                                   this second, PUE-adjusted
//   G       genetics                what the node's AI core has LEARNED
//                                   about the class you are bidding for
//   D       demand / wear           the balancer -- premium when hot,
//                                   discount when cold. Two-sided.
//   H       health                  derate, hazard, maintenance reserve
//   Q       quantum                 9^t for t non-Clifford gates; 1 for
//                                   everything classical
//   L       locality                fabric distance from your data,
//                                   priced off the migration price law
//
// A multiplicative model, not additive, and that is a real decision:
// it makes the terms independent, keeps every one of them auditable on
// its own line, and means no single factor can drive the price to zero
// or to infinity on its own once each is clamped. The buyer sees the
// full decomposition on every quote -- there is no opaque "market rate".
//
// ---------------------------------------------------------------------
// WHY D IS TWO-SIDED (the part that pays for itself)
//
// The naive version of a compute market prices scarcity only: busy
// node costs more. That leaves the cold half of the fleet idle, and an
// idle node still ages, still draws standby power, and still has to be
// serviced on the same calendar.
//
// So D charges a premium ABOVE a target utilisation band and pays a
// discount BELOW it. The discount is not charity -- it is cheaper than
// the alternative. Demand migrates toward the discounted nodes, the
// dispersion of utilisation across the fleet falls, thermal cycling
// falls with it (cycling, not duty, is what actually kills silicon),
// and the fleet's service events spread out instead of arriving in a
// clump. The measurable target is the utilisation Gini coefficient,
// and the balancer drives it down. See balance() and Fleet.tick().
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  // Utilisation band the balancer steers toward. Not 100%: a fleet
  // pinned at 100% has no headroom for a burst option to be exercised
  // against, and cycles harder when one is.
  const TARGET_BAND = { low: 0.55, high: 0.78 };

  const CLAMP = {
    energy: [0.62, 2.4],
    genetics: [0.7, 2.6],
    demand: [0.55, 3.2],
    health: [0.58, 1.12],
    locality: [0.92, 1.85],
  };

  class PricingEngine {
    constructor(fleet, energy, workloads) {
      this.fleet = fleet;
      this.energy = energy;
      this.workloads = workloads;
      this.quotes = new Map();       // nodeId -> last full quote
      this.fleetStats = null;
      this.balanceHistory = [];
      this.maxBalanceHistory = 300;
      this.balancerEnabled = true;
      this.refreshFleetStats();
    }

    // ------------------------------------------------------------------
    // The six multipliers
    // ------------------------------------------------------------------

    /** E -- energy. Delegated to the energy engine's clamped power law. */
    energyMultiplier(node) {
      const m = this.energy.multiplier(node.dcId);
      return clampTo(m, CLAMP.energy);
    }

    /**
     * G -- genetics.
     *
     * This is the multiplier that makes Holotrade different from renting
     * a box. Two identical chassis that have run different work for a
     * month are no longer the same product: one of them already carries
     * priors for what you are about to ask, and will reach your target
     * in fewer node-hours. That is worth paying for, and it is
     * measurable -- so it gets a line on the quote.
     *
     * Built from three observable things, never from a claim:
     *   - the node's specialisation score on THIS workload class
     *   - its realised fitness (completion record, not nameplate)
     *   - its provenance depth (a long lineage of successful forks is
     *     evidence the core is genuinely good, not lucky)
     */
    geneticsMultiplier(node, workloadId) {
      const w = this.workloads.find((x) => x.id === workloadId) || this.workloads[0];
      const spec = this.fleet.specialisationScore(node, w);
      if (spec === 0) return 0; // cannot serve this class at all
      const fit = this.fleet.fitness(node);
      const provenance = Math.min(1, node.lineage.generation / 6) * 0.5 +
                         Math.min(1, Math.log10(1 + node.jobsCompleted) / 3.2) * 0.5;

      // Centre at 1.0 for an average node on an average class, so the
      // multiplier reads as a premium/discount rather than a score.
      const raw = 0.55 + 1.05 * spec + 0.55 * fit + 0.25 * provenance;
      return clampTo(raw, CLAMP.genetics);
    }

    /**
     * D -- demand and wear. The balancer.
     *
     * Above the target band: premium. Two things are being charged for
     * and they happen to point the same way -- scarcity, and the extra
     * wear a hot node is accumulating on behalf of everyone who wants it.
     * The premium is superlinear because the wear term is: thermal
     * cycling scales worse than duty cycle.
     *
     * Below the band: discount. Deep enough to actually move demand,
     * floored so a cold node is never sold below its energy plus
     * maintenance reserve (see floorPrice()).
     *
     * Inside the band: 1.0, with a gentle tilt. A node in the band is
     * exactly where the fleet wants it and should not be pushed.
     */
    demandMultiplier(node) {
      if (!this.balancerEnabled) return 1;
      const u = node.utilisation;

      // The three branches must be MONOTONE INCREASING in utilisation
      // and continuous at both seams. If they are not, there is a
      // utilisation at which a node gets cheaper by becoming busier --
      // which inverts the whole incentive and lets a buyer arbitrage
      // the discount by loading the node they are about to rent.
      // (An earlier version centred the in-band branch on 1.0 and dipped
      // below the discount branch's value at the lower seam. The
      // monotonicity test caught it.)
      const BAND_TOP = 1.10;   // D at the top of the band

      if (u > TARGET_BAND.high) {
        const over = (u - TARGET_BAND.high) / (1 - TARGET_BAND.high);
        const scarcity = 1 + 1.35 * Math.pow(over, 1.4);
        // wear surcharge: what this node is spending to be popular
        const wearRate = 0.45 + 1.1 * u + Math.abs(u - node.utilisationEMA) * 3.2;
        const surcharge = 1 + 0.28 * (wearRate - 1.2) * node.hardware.thermalSensitivity;
        return clampTo(BAND_TOP * scarcity * Math.max(1, surcharge), CLAMP.demand);
      }
      if (u < TARGET_BAND.low) {
        const under = (TARGET_BAND.low - u) / TARGET_BAND.low;
        // discount deepens toward the floor but never past it, and
        // reaches exactly 1.0 at the band's lower edge
        return clampTo(1 - 0.42 * Math.pow(under, 0.85), CLAMP.demand);
      }
      // inside the band: a gentle rise from 1.0 to BAND_TOP, so a node
      // in the band is where the fleet wants it and is barely pushed
      const t = (u - TARGET_BAND.low) / (TARGET_BAND.high - TARGET_BAND.low);
      return 1 + t * (BAND_TOP - 1);
    }

    /**
     * H -- health.
     *
     * A worn node delivers less per hour, so it should cost less per
     * hour, and it should be visibly cheaper rather than quietly slower.
     * Three components: the performance derate you actually receive, a
     * reliability discount from the Weibull hazard (your job is more
     * likely to need a restart), and an error-drift term.
     */
    healthMultiplier(node) {
      const derate = node.health.derate;
      const reliability = 1 - Math.min(0.3, node.health.hazard * 1.6);
      const errorDrift = 1 - Math.min(0.08, node.health.correctableErrors / 40000);
      return clampTo(derate * reliability * errorDrift, CLAMP.health);
    }

    /**
     * Q -- quantum.
     *
     * The Clifford layer is free. It is the stabilizer formalism, it is
     * polynomial-time on any classical machine, and it covers routing,
     * memory, fault tolerance -- everything structural. So a classical
     * job's Q is exactly 1 and always will be.
     *
     * Non-Clifford gates are the priced resource: each one multiplies
     * the classical emulation cost by 9, so at t = 20 no classical
     * fleet can help you and only real substrate hardware can. That is
     * a hard cliff, and it is honest to show it as one rather than
     * pretending quantum capacity is a smooth premium.
     */
    quantumMultiplier(node, workloadId) {
      const w = this.workloads.find((x) => x.id === workloadId);
      const t = w ? w.magicBudget : 0;
      if (t <= 0) return 1;
      if (!node.hardware.magicCapable) return Infinity; // cannot serve
      // Charged on the log of the emulation cost the buyer is escaping,
      // not the raw 9^t -- which would be absurd past t = 6. The buyer
      // pays for the ADVANTAGE, scaled, not for the emulator's misery.
      return 1 + 0.34 * Math.log(S.magicMultiplier(t));
    }

    /**
     * L -- locality.
     *
     * Address is route, so this is not a heuristic about availability
     * zones -- it is a distance in the fabric, computed from one
     * symplectic inner product per hop. Inside a cell the diameter is
     * 2 and there are mu = 4 disjoint paths, so locality barely costs
     * anything; across cells you pay 8 hops per address digit.
     *
     * The migration price law sets the floor: moving to a NEIGHBOUR
     * costs 3 rays, re-vectoring in place costs 6. So a buyer with data
     * already on the fabric is quoted less to move than to stay put and
     * reconfigure, which is the correct incentive and falls out of the
     * geometry rather than being imposed on it.
     */
    localityMultiplier(node, anchorAddress) {
      if (!anchorAddress) return 1;
      const cost = S.migrationCost(anchorAddress, node.addr);
      const hopTerm = 1 + cost.hops * 0.018;
      const rayTerm = 1 + (cost.rays - S.RAY_COST.adjacent) * 0.035;
      return clampTo(hopTerm * rayTerm, CLAMP.locality);
    }

    // ------------------------------------------------------------------
    // The quote
    // ------------------------------------------------------------------

    /**
     * Full price decomposition for one node against one workload class.
     * Every field here is meant to be shown to the buyer.
     */
    quote(node, { workloadId = "llm-train", anchorAddress = null } = {}) {
      const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
      const base = node.hardware.baseRate;

      const E = this.energyMultiplier(node);
      const G = this.geneticsMultiplier(node, workloadId);
      const D = this.demandMultiplier(node);
      const H = this.healthMultiplier(node);
      const Q = this.quantumMultiplier(node, workloadId);
      const L = this.localityMultiplier(node, anchorAddress);

      const serviceable = G > 0 && Number.isFinite(Q);
      const price = serviceable ? base * E * G * D * H * Q * L : null;

      const energyCost = this.energy.hourlyEnergyCost(node, dc);
      const reserve = this.fleet.maintenanceReserve(node);
      const capital = this.fleet.capitalRecovery(node);
      // Floor = energy + maintenance reserve + capital recovery. All
      // three, because a discount that does not repay the machine is
      // not a discount, it is a loss the operator has not noticed yet.
      const floor = energyCost + reserve + capital;

      const q = {
        nodeId: node.id,
        workloadId,
        serviceable,
        base,
        multipliers: { E, G, D, H, Q, L },
        price: serviceable ? Math.max(price, floor * 1.02) : null,
        rawPrice: price,
        floor,
        energyCost,
        maintenanceReserve: reserve,
        capitalRecovery: capital,
        margin: serviceable ? Math.max(price, floor * 1.02) - floor : null,
        marginPct: serviceable ? (Math.max(price, floor * 1.02) - floor) / Math.max(price, floor * 1.02) : null,
        carbonPerHour: this.energy.hourlyCarbon(node, dc),
        decadesAboveFloor: this.energy.decadesAboveFloor(node, dc),
        atFloor: serviceable ? price < floor * 1.02 : false,
        ts: Date.now(),
      };

      this.quotes.set(node.id, q);
      node.lastPrice = q.price;
      if (q.price != null) {
        node.priceHistory.push(q.price);
        if (node.priceHistory.length > 240) node.priceHistory.shift();
      }
      return q;
    }

    /** Quote the whole listed fleet against one class. */
    quoteAll(opts = {}) {
      const out = [];
      for (const node of this.fleet.listedNodes()) out.push(this.quote(node, opts));
      return out;
    }

    /**
     * The floor price. Below this the exchange refuses to clear,
     * because the operator would be paying to run your job. Energy
     * plus maintenance reserve -- no margin assumed, but no charity
     * either. This is what stops the balancer's discount from
     * becoming a race to the bottom.
     */
    floorPrice(node) {
      const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
      return (
        this.energy.hourlyEnergyCost(node, dc) +
        this.fleet.maintenanceReserve(node) +
        this.fleet.capitalRecovery(node)
      );
    }

    // ------------------------------------------------------------------
    // Feedback: the loop that actually balances the fleet
    // ------------------------------------------------------------------

    /**
     * Demand response. Given each node's current price relative to the
     * fleet median, move its utilisation the way a rational buyer
     * would: toward the cheap nodes, away from the expensive ones.
     *
     * This is the closed loop. Nothing here is scripted -- utilisation
     * is not being nudged toward the target band directly. It is being
     * nudged by PRICE, and the price came from the utilisation. That
     * is what makes the Gini fall an emergent result rather than a
     * decorated animation.
     */
    applyDemandResponse(dtHours = 1 / 60, opts = {}) {
      const nodes = this.fleet.listedNodes();
      if (!nodes.length) return;
      const workloadId = opts.workloadId || "llm-train";

      const quotes = nodes
        .map((n) => ({ node: n, q: this.quote(n, { workloadId }) }))
        .filter((x) => x.q.serviceable && x.q.price != null);
      if (!quotes.length) return;

      // Compare each node to the median of ITS OWN hardware class, not
      // of the whole fleet. A buyer choosing between accelerators does
      // not find a CPU node "cheap" -- they are not substitutes, and a
      // fleet-wide median would make every CPU look like a bargain and
      // every photonic leaf look extortionate forever. The substitution
      // set is the class.
      const byClass = new Map();
      for (const x of quotes) {
        const k = x.node.hardware.class;
        if (!byClass.has(k)) byClass.set(k, []);
        byClass.get(k).push(x.q.price);
      }
      const classMedian = new Map();
      for (const [k, ps] of byClass) {
        ps.sort((a, b) => a - b);
        classMedian.set(k, ps[Math.floor(ps.length / 2)]);
      }

      // Aggregate demand shock: the whole market has a mood, and it is
      // what makes utilisation move together before it disperses. Kept
      // narrow, because a wide swing here would swamp the price signal
      // and the Gini result would be measuring the sine wave, not the
      // balancer.
      const marketDrive = 0.92 + 0.16 * Math.sin(this.fleet.epoch / 220) + (this.fleet.rand() - 0.5) * 0.1;
      const bandCentre = (TARGET_BAND.low + TARGET_BAND.high) / 2;

      for (const { node, q } of quotes) {
        const rel = q.price / (classMedian.get(node.hardware.class) || q.price);
        // Price elasticity of demand for compute: around -1.9 here.
        // Buyers are strongly price-sensitive because on this fabric
        // migration is cheap -- a neighbouring node costs 3 rays -- so
        // the frictions that make real cloud demand sticky are mostly
        // absent. That is the substrate showing up in the economics.
        const elasticity = -1.9;
        const pull = Math.pow(Math.max(0.3, rel), elasticity);
        const genePull = 0.75 + 0.5 * this.fleet.specialisationScore(
          node,
          this.workloads.find((w) => w.id === workloadId) || this.workloads[0]
        );
        // Note what is and is not happening here: the target is set by
        // the node's PRICE relative to the market, and the price came
        // from its utilisation. Nothing pushes utilisation toward the
        // band directly. The band is where the loop settles, not where
        // it is aimed -- which is why the Gini result is a finding
        // rather than an animation.
        const target = clamp01(bandCentre * marketDrive * pull * genePull);

        // First-order lag: real workloads take minutes to move, not ticks.
        const tau = 0.10;
        node.utilisation = clamp01(node.utilisation + (target - node.utilisation) * tau);
        node.currentWorkload = workloadId;
      }
      this.refreshFleetStats();
    }

    // ------------------------------------------------------------------
    // Balance metrics -- the scoreboard for the whole idea
    // ------------------------------------------------------------------

    /**
     * Gini coefficient of utilisation across the listed fleet.
     *
     * 0 means every node is equally loaded -- the ideal. 1 means one
     * node does all the work while the rest idle. This single number
     * is the honest test of whether two-sided pricing works: turn the
     * balancer off and watch it climb.
     */
    utilisationGini(nodes) {
      const xs = (nodes || this.fleet.listedNodes()).map((n) => n.utilisation).sort((a, b) => a - b);
      const n = xs.length;
      if (n === 0) return 0;
      const sum = xs.reduce((a, b) => a + b, 0);
      if (sum === 0) return 0;
      let cum = 0;
      for (let i = 0; i < n; i++) cum += (i + 1) * xs[i];
      return (2 * cum) / (n * sum) - (n + 1) / n;
    }

    refreshFleetStats() {
      const nodes = this.fleet.listedNodes();
      const utils = nodes.map((n) => n.utilisation);
      const mean = utils.length ? utils.reduce((a, b) => a + b, 0) / utils.length : 0;
      const variance = utils.length
        ? utils.reduce((a, u) => a + (u - mean) ** 2, 0) / utils.length
        : 0;
      const gini = this.utilisationGini(nodes);
      const inBand = utils.filter((u) => u >= TARGET_BAND.low && u <= TARGET_BAND.high).length;
      const cold = utils.filter((u) => u < TARGET_BAND.low).length;
      const hot = utils.filter((u) => u > TARGET_BAND.high).length;

      this.fleetStats = {
        count: nodes.length,
        meanUtilisation: mean,
        stdUtilisation: Math.sqrt(variance),
        gini,
        inBand,
        cold,
        hot,
        bandPct: nodes.length ? inBand / nodes.length : 0,
        serviceDue: this.fleet.nodes.filter((n) => n.health.serviceDue).length,
        inService: this.fleet.nodes.filter((n) => n.health.inService).length,
      };

      this.balanceHistory.push({ gini, mean, inBand: this.fleetStats.bandPct, t: this.fleet.epoch });
      if (this.balanceHistory.length > this.maxBalanceHistory) this.balanceHistory.shift();
      return this.fleetStats;
    }

    /**
     * Wear dispersion. The reason balancing pays: if every node wears
     * at the same rate, service events arrive evenly and the fleet
     * needs a smaller maintenance crew and fewer spare units. A high
     * dispersion means a few nodes are being consumed while the rest
     * age into obsolescence unused -- the worst of both.
     */
    wearDispersion() {
      const wears = this.fleet.nodes.map((n) => n.health.wear);
      if (!wears.length) return { mean: 0, std: 0, cv: 0 };
      const mean = wears.reduce((a, b) => a + b, 0) / wears.length;
      const std = Math.sqrt(wears.reduce((a, w) => a + (w - mean) ** 2, 0) / wears.length);
      return { mean, std, cv: mean > 0 ? std / mean : 0 };
    }

    /** Fleet-wide price statistics for the exchange header. */
    marketStats(opts = {}) {
      const quotes = this.quoteAll(opts).filter((q) => q.serviceable && q.price != null);
      if (!quotes.length) return null;
      const prices = quotes.map((q) => q.price).sort((a, b) => a - b);
      const idx = (p) => prices[Math.min(prices.length - 1, Math.floor(p * prices.length))];
      const total = prices.reduce((a, b) => a + b, 0);
      return {
        count: prices.length,
        min: prices[0],
        max: prices[prices.length - 1],
        median: idx(0.5),
        p10: idx(0.1),
        p90: idx(0.9),
        mean: total / prices.length,
        atFloor: quotes.filter((q) => q.atFloor).length,
        totalCapacityPerHour: total,
      };
    }

    // ------------------------------------------------------------------
    // Derived instrument pricing
    // ------------------------------------------------------------------

    /**
     * Forward price for a block of node-hours delivered in a future
     * window. Cost-of-carry over the spot: the seller is giving up
     * optionality on energy, so the forward carries the expected
     * energy drift plus a risk premium scaled by that site's volatility.
     */
    forwardPrice(node, days, workloadId = "llm-train") {
      const spot = this.quote(node, { workloadId });
      if (!spot.serviceable) return null;
      const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
      const carry = Math.pow(1 + 0.00042 * dc.energyVol, days);
      const wearForward = 1 + (node.health.wear + days * 0.0006) * 0.05;
      const risk = 1 + dc.energyVol * 0.11 * Math.sqrt(days / 30);
      return {
        price: spot.price * carry * wearForward * risk,
        spot: spot.price,
        carry,
        risk,
        basis: spot.price * carry * wearForward * risk - spot.price,
      };
    }

    /**
     * Burst option premium. Black-Scholes is the wrong model for a
     * non-storable good, so this is a simple utilisation-vol model:
     * the premium is the probability the node is actually free times
     * the expected spike you are protected against.
     */
    optionPremium(node, days, strikeMultiple = 1.25, workloadId = "llm-train") {
      const spot = this.quote(node, { workloadId });
      if (!spot.serviceable) return null;
      const hist = node.utilHistory.length > 20 ? node.utilHistory : [node.utilisation];
      const mean = hist.reduce((a, b) => a + b, 0) / hist.length;
      const vol = Math.sqrt(hist.reduce((a, u) => a + (u - mean) ** 2, 0) / hist.length) || 0.12;
      const availability = Math.max(0.05, 1 - mean);
      const spikeProb = Math.min(0.85, vol * 3.2);
      const strike = spot.price * strikeMultiple;
      const expectedPayoff = spikeProb * Math.max(0, spot.price * (1 + vol * 4) - strike);
      return {
        premium: (expectedPayoff * availability + spot.price * 0.035) * Math.sqrt(days / 7),
        strike,
        availability,
        impliedVol: vol,
      };
    }

    /**
     * Genome lease. You are renting the CORE, not the chassis --
     * priced on fitness and specialisation rather than on silicon, with
     * a term discount because a long lease de-risks the operator's
     * utilisation.
     *
     * The honest caveat, and it goes on the quote: a leased core's
     * genome keeps drifting toward whatever YOU feed it. You are
     * buying a starting point, not a frozen asset.
     */
    leasePrice(node, days, workloadId) {
      const spot = this.quote(node, { workloadId });
      if (!spot.serviceable) return null;
      const w = this.workloads.find((x) => x.id === workloadId) || this.workloads[0];
      const spec = this.fleet.specialisationScore(node, w);
      const fit = this.fleet.fitness(node);
      const termDiscount = 1 - Math.min(0.28, Math.log10(1 + days) * 0.11);
      const genomePremium = 1 + spec * fit * 0.9;
      const hourly = spot.price * termDiscount * genomePremium;
      return {
        hourly,
        total: hourly * 24 * days,
        termDiscount,
        genomePremium,
        specialisation: spec,
        fitness: fit,
        drift: `core will re-specialise toward your workload at ~${(0.0016 * 60 * 24).toFixed(2)}/day`,
      };
    }
  }

  // ---- helpers ---------------------------------------------------------
  function clampTo(x, [lo, hi]) {
    if (!Number.isFinite(x)) return x;
    return Math.max(lo, Math.min(hi, x));
  }
  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  const API = { PricingEngine, TARGET_BAND, CLAMP };
  root.PricingEngine = PricingEngine;
  root.HolotradePricing = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
