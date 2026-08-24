// ======================================================================
// HOLOTRADE ENERGY ENGINE
//
// Compute is bought in dollars but paid for in joules. This module is
// the joule side: a per-second wholesale grid price for every
// datacentre, the carbon intensity that rides along with it, and the
// modeled thermodynamic reference shown separately from node telemetry.
//
// Exporting 58 modeled syndrome qutrits has a Landauer lower bound of
// 2.6e-19 J per syndrome cycle at 300 K. Catalog hardware reports J/op,
// a different functional unit, so HoloTrade does not divide one by the
// other without a workload-specific mapping.
//
// The IEA projects ~945 TWh of datacentre demand by 2030 on the
// assumption of incremental CMOS. That number is a technology choice,
// not a physical law -- and an exchange that prices energy per second
// is the mechanism that makes the choice visible to a buyer.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  const HOUR = 3600;
  const MWH_PER_KWH = 0.001;

  class EnergyEngine {
    constructor(datacenters, seed = "holotrade-energy") {
      this.datacenters = datacenters;
      this.rand = S.rng(seed);
      this.t = 0;                 // seconds since session start
      this.history = new Map();   // dcId -> rolling $/MWh
      this.maxHistory = 720;
      this.state = new Map();
      for (const dc of datacenters) {
        this.state.set(dc.id, {
          price: dc.baseEnergy,
          carbon: dc.carbon,
          shock: 0,               // decaying scarcity event
          phase: S.hash32(dc.id) % 3600,
        });
        this.history.set(dc.id, []);
      }
      this.tick(0);
    }

    /**
     * Wholesale $/MWh for one datacentre.
     *
     * Three additive structures, because that is what real nodal prices
     * actually look like:
     *   - a diurnal curve keyed to LOCAL time (solar trough midday,
     *     evening ramp when the sun goes and the AC does not)
     *   - mean-reverting noise scaled by the market's own volatility
     *   - Poisson scarcity shocks with exponential decay, which is the
     *     only way to get ERCOT's fat right tail without faking it
     */
    tick(dtSeconds = 1) {
      this.t += dtSeconds;
      for (const dc of this.datacenters) {
        const st = this.state.get(dc.id);
        const localHour = ((this.t / HOUR + 12 + dc.tz) % 24 + 24) % 24;

        // diurnal shape: solar suppression 10:00-16:00, evening ramp 17:00-21:00
        const solar = -0.28 * Math.exp(-Math.pow((localHour - 13) / 2.6, 2));
        const evening = 0.42 * Math.exp(-Math.pow((localHour - 19) / 2.1, 2));
        const overnight = -0.18 * Math.exp(-Math.pow((localHour - 3.5) / 3.0, 2));
        const shape = 1 + (solar + evening + overnight) * (0.4 + dc.energyVol);

        // Ornstein-Uhlenbeck style mean reversion on the residual
        const target = dc.baseEnergy * shape;
        const kappa = 0.06;
        const shockNow = st.shock;
        const noise = (this.rand() - 0.5) * 2 * dc.baseEnergy * dc.energyVol * 0.09;
        st.price = st.price + kappa * (target - st.price) + noise + shockNow;

        // scarcity events: rare, violent, decay over ~20 min of sim time
        st.shock *= 0.94;
        const shockProb = 0.00035 * (1 + dc.energyVol * 4);
        if (this.rand() < shockProb * Math.max(1, dtSeconds)) {
          const magnitude = dc.baseEnergy * (0.6 + this.rand() * 5.5) * dc.energyVol;
          st.shock += magnitude * 0.08;
        }
        // negative pricing is real; floor it where curtailment starts
        st.price = Math.max(-12, st.price);

        // carbon tracks the residual: expensive hour == dirtier marginal unit
        const ratio = st.price / Math.max(1, dc.baseEnergy);
        st.carbon = Math.max(8, dc.carbon * (0.72 + 0.42 * Math.min(2.6, ratio)));

        const h = this.history.get(dc.id);
        h.push(st.price);
        if (h.length > this.maxHistory) h.shift();
      }
      return this;
    }

    priceFor(dcId) {
      const st = this.state.get(dcId);
      return st ? st.price : 0;
    }

    carbonFor(dcId) {
      const st = this.state.get(dcId);
      return st ? st.carbon : 0;
    }

    historyFor(dcId) {
      return this.history.get(dcId) || [];
    }

    /**
     * The energy multiplier the pricing engine consumes.
     *
     * Deliberately NOT linear in the grid price. A node's rate should
     * move with energy but not become worthless when ERCOT goes
     * negative at 3am, and not become unsellable when it spikes to
     * $3000. A power-law with exponent 0.55 on the ratio to baseline,
     * clamped to [0.62, 2.40], reproduces how operators actually
     * behave: they pass through most of a move, and none of a tail.
     */
    multiplier(dcId) {
      const dc = this.datacenters.find((d) => d.id === dcId);
      if (!dc) return 1;
      const st = this.state.get(dcId);
      const ratio = Math.max(0.05, st.price / dc.baseEnergy);
      const raw = Math.pow(ratio, 0.55);
      return Math.min(2.4, Math.max(0.62, raw));
    }

    /** Actual electricity cost of running one node for one hour, in dollars. */
    hourlyEnergyCost(node, dc) {
      const kw = (node.hardware.tdp / 1000) * dc.pue * (0.32 + 0.68 * node.utilisation);
      return kw * this.priceFor(dc.id) * MWH_PER_KWH;
    }

    /** kg CO2e for one node-hour at the current marginal intensity. */
    hourlyCarbon(node, dc) {
      const kwh = (node.hardware.tdp / 1000) * dc.pue * (0.32 + 0.68 * node.utilisation);
      return (kwh * this.carbonFor(dc.id)) / 1000;
    }

    /** Cross-unit comparison intentionally unavailable. */
    decadesAboveFloor(node, dc) {
      void node;
      void dc;
      return null;
    }

    /** Fleet-wide roll-up for the energy view. */
    summary(nodes) {
      let totalKW = 0;
      let totalCostPerHour = 0;
      let totalCarbonPerHour = 0;
      const byDc = new Map();
      for (const node of nodes) {
        const dc = this.datacenters.find((d) => d.id === node.dcId);
        if (!dc) continue;
        const kw = (node.hardware.tdp / 1000) * dc.pue * (0.32 + 0.68 * node.utilisation);
        const cost = this.hourlyEnergyCost(node, dc);
        const carbon = this.hourlyCarbon(node, dc);
        totalKW += kw;
        totalCostPerHour += cost;
        totalCarbonPerHour += carbon;
        const agg = byDc.get(dc.id) || { kw: 0, cost: 0, carbon: 0, nodes: 0 };
        agg.kw += kw;
        agg.cost += cost;
        agg.carbon += carbon;
        agg.nodes += 1;
        byDc.set(dc.id, agg);
      }
      return {
        totalKW,
        totalCostPerHour,
        totalCarbonPerHour,
        annualTWh: (totalKW * 8760) / 1e9,
        byDc,
      };
    }
  }

  root.EnergyEngine = EnergyEngine;
  if (typeof module !== "undefined" && module.exports) module.exports = EnergyEngine;
})(typeof window !== "undefined" ? window : globalThis);
