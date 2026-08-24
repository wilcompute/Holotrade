// ======================================================================
// HOLOTRADE FLEET
//
// A node is not a rectangle of FLOPs. On this exchange a node is four
// things at once, and all four are priced:
//
//   1. HARDWARE   -- what it is. Class, memory, bandwidth, TDP.
//   2. ADDRESS    -- where it is, in the W(3,3) fabric. Address is
//                    route, so locality is a closed-form number.
//   3. GENOME     -- what it has LEARNED. Every node carries an AI core
//                    that accumulates priors from the jobs it has run.
//                    Two identical chassis diverge after a month of
//                    work, and the exchange can measure the divergence.
//   4. HEALTH     -- what it has SPENT. Duty cycle, thermal cycling,
//                    power cycles, correctable-error drift. A node that
//                    everybody wants is a node that is wearing out
//                    faster than its neighbours.
//
// (3) and (4) are the two halves of the same idea, and together they
// are why the price of two physically identical machines should differ.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  const GENE_NAMES = [
    "throughput",        // sustained useful work vs nameplate
    "memoryBandwidth",   // effective, not spec-sheet
    "thermalStability",  // how flat it holds under a long duty cycle
    "convergenceRate",   // how fast its core reaches a target loss
    "faultResilience",   // checkpoint survival, ECC behaviour, restart cost
    "adaptability",      // how well it generalises off its trained class
  ];

  class Node {
    constructor(spec) {
      Object.assign(this, spec);
    }

    /** Fabric address as a dotted string, e.g. "11.07.32". */
    get address() {
      return S.formatAddress(this.addr);
    }

    /** The point of W(3,3) this node occupies inside its own cell. */
    get cellPoint() {
      return this.addr[this.addr.length - 1];
    }

    /** Nameplate-normalised effective throughput, after genome and health. */
    get effectiveTflops() {
      return this.hardware.tflops * this.genome.throughput * this.health.derate;
    }
  }

  class Fleet {
    constructor({ datacenters, hardware, workloads, operators, size = 240, seed = "holotrade-fleet" }) {
      this.datacenters = datacenters;
      this.hardware = hardware;
      this.workloads = workloads;
      this.operators = operators;
      this.rand = S.rng(seed);
      this.nodes = [];
      this.byId = new Map();
      this.epoch = 0;
      this.build(size);
    }

    build(size) {
      const perDc = Math.ceil(size / this.datacenters.length);
      let n = 0;
      for (const dc of this.datacenters) {
        // Each datacentre is a subtree of the fabric. Its nodes get
        // addresses under the DC's prefix, filling W(3,3) cells in order.
        const cells = Math.ceil(perDc / 40);
        for (let c = 0; c < cells && n < size; c++) {
          for (let p = 0; p < 40 && n < size; p++) {
            if (this.rand() < 0.42) continue; // real fabrics are sparse
            this.nodes.push(this.makeNode(dc, [...dc.prefix, c * 7 + 3, p]));
            n++;
          }
        }
      }
      // Backfill so the count is exact regardless of the sparsity draw.
      let guard = 0;
      while (this.nodes.length < size && guard++ < size * 8) {
        const dc = this.datacenters[Math.floor(this.rand() * this.datacenters.length)];
        const c = Math.floor(this.rand() * 6);
        const p = Math.floor(this.rand() * 40);
        const addr = [...dc.prefix, c * 7 + 3, p];
        if (this.nodes.some((x) => x.address === S.formatAddress(addr))) continue;
        this.nodes.push(this.makeNode(dc, addr));
      }
      this.nodes.forEach((node, i) => {
        node.seq = i;
        this.byId.set(node.id, node);
      });
      this.assignLineage();
    }

    makeNode(dc, addr) {
      const r = this.rand;
      // Photonic leaves are rare and clustered; everything else follows
      // a realistic accelerator-heavy mix.
      const roll = r();
      let hw;
      if (roll < 0.045) hw = this.hardware.find((h) => h.class === "W33-L1");
      else if (roll < 0.30) hw = this.hardware.find((h) => h.class === "GX-H");
      else if (roll < 0.44) hw = this.hardware.find((h) => h.class === "GX-B");
      else if (roll < 0.56) hw = this.hardware.find((h) => h.class === "GX-M");
      else if (roll < 0.72) hw = this.hardware.find((h) => h.class === "CX-E");
      else if (roll < 0.84) hw = this.hardware.find((h) => h.class === "CX-A");
      else if (roll < 0.93) hw = this.hardware.find((h) => h.class === "FX-1");
      else hw = this.hardware.find((h) => h.class === "NX-1");

      const id = `${dc.id}-${hw.class}-${S.formatAddress(addr).replace(/\./g, "")}`;
      const ageHours = Math.floor(r() * hw.lifeHours * 0.55);

      return new Node({
        id,
        dcId: dc.id,
        hardware: hw,
        addr,
        operator: this.operators[Math.floor(r() * this.operators.length)],
        commissioned: Date.now() - ageHours * 3600_000,
        ageHours,
        utilisation: 0.2 + r() * 0.5,
        utilisationEMA: 0.45,
        genome: this.seedGenome(hw, r),
        health: this.seedHealth(hw, ageHours, r),
        lineage: { parents: [], generation: 0, forkedFrom: null },
        jobsCompleted: Math.floor(r() * 1400),
        jobsFailed: Math.floor(r() * 40),
        specialisation: this.seedSpecialisation(r),
        priceHistory: [],
        utilHistory: [],
        listed: r() > 0.06,      // a few nodes are held back by their operator
        reservedUntil: 0,
      });
    }

    /**
     * A genome is six observed traits in [0,1], not six knobs to tune.
     * They start near the hardware class's natural centre and then
     * DRIFT with the work the node actually does -- that drift is the
     * whole point, and it is what a genome lease is buying.
     */
    seedGenome(hw, r) {
      const centre = {
        gpu: { throughput: 0.72, memoryBandwidth: 0.78, thermalStability: 0.55, convergenceRate: 0.62, faultResilience: 0.6, adaptability: 0.58 },
        cpu: { throughput: 0.5, memoryBandwidth: 0.48, thermalStability: 0.8, convergenceRate: 0.5, faultResilience: 0.82, adaptability: 0.86 },
        fpga: { throughput: 0.6, memoryBandwidth: 0.6, thermalStability: 0.86, convergenceRate: 0.55, faultResilience: 0.78, adaptability: 0.42 },
        neuro: { throughput: 0.45, memoryBandwidth: 0.4, thermalStability: 0.9, convergenceRate: 0.72, faultResilience: 0.7, adaptability: 0.35 },
        photonic: { throughput: 0.58, memoryBandwidth: 0.35, thermalStability: 0.94, convergenceRate: 0.8, faultResilience: 0.88, adaptability: 0.5 },
      }[hw.kind];

      const g = {};
      for (const k of GENE_NAMES) {
        const jitter = (r() - 0.5) * 0.34;
        g[k] = clamp01(centre[k] + jitter);
      }
      return g;
    }

    /**
     * Specialisation: how much prior a node's core carries for each
     * workload class. Nodes start diffuse and sharpen with use.
     * This is the "genetics" a buyer is actually paying a premium for.
     */
    seedSpecialisation(r) {
      const spec = {};
      for (const w of this.workloads) spec[w.id] = 0.18 + r() * 0.24;
      // give most nodes one or two nascent strengths
      const picks = this.workloads.slice().sort(() => r() - 0.5).slice(0, 2);
      for (const p of picks) spec[p.id] = clamp01(spec[p.id] + 0.22 + r() * 0.3);
      return spec;
    }

    /**
     * Health. `wear` is cumulative and monotone; `derate` is the
     * performance you actually get today; `hazard` is an instantaneous
     * Weibull failure rate that drives the maintenance reserve.
     */
    seedHealth(hw, ageHours, r) {
      const dutyLife = ageHours / hw.lifeHours;
      const wear = clamp01(dutyLife * (0.75 + r() * 0.5));
      const thermalCycles = Math.floor(ageHours / (18 + r() * 40));
      const powerCycles = Math.floor(thermalCycles * (0.08 + r() * 0.1));
      return {
        wear,
        thermalCycles,
        powerCycles,
        correctableErrors: Math.floor(wear * (400 + r() * 2600)),
        uncorrectableErrors: Math.floor(wear * r() * 6),
        derate: 1 - wear * 0.22 * hw.thermalSensitivity,
        hazard: weibullHazard(dutyLife, hw),
        lastServiceHours: Math.floor(r() * 4000),
        inService: false,
        serviceDue: false,
      };
    }

    /**
     * Lineage. High-fitness cores get checkpointed and redeployed onto
     * fresh silicon -- that is a real practice (model merging, warm
     * starts), and it means node identity is not the same as chassis
     * identity. The exchange tracks the CORE's ancestry, because that
     * is what carries value across a hardware refresh.
     */
    assignLineage() {
      const sorted = [...this.nodes].sort((a, b) => b.ageHours - a.ageHours);
      const founders = sorted.slice(0, Math.ceil(sorted.length * 0.14));
      founders.forEach((f) => { f.lineage.generation = 0; });
      const rest = sorted.slice(founders.length);
      for (const node of rest) {
        const pool = founders.concat(rest.filter((x) => x.ageHours > node.ageHours + 500));
        if (!pool.length) continue;
        const parent = pool[Math.floor(this.rand() * pool.length)];
        node.lineage.forkedFrom = parent.id;
        node.lineage.parents = [parent.id];
        node.lineage.generation = parent.lineage.generation + 1;
        // inherited priors, attenuated by the fork
        for (const w of this.workloads) {
          node.specialisation[w.id] = clamp01(
            node.specialisation[w.id] * 0.55 + parent.specialisation[w.id] * 0.45
          );
        }
      }
    }

    // ------------------------------------------------------------------
    // Fitness: what a node has actually achieved, not what it claims.
    // ------------------------------------------------------------------

    /**
     * Composite fitness in [0,1]. Weighted from completion record,
     * genome quality on its own strongest class, and the inverse of
     * its failure rate. This is the number that drives a genome
     * lease's premium and the breeding selection in genetics.js.
     */
    fitness(node) {
      const attempts = node.jobsCompleted + node.jobsFailed;
      const completion = attempts > 0 ? node.jobsCompleted / attempts : 0.5;
      const best = this.bestClass(node);
      const geneQuality =
        (node.genome.throughput + node.genome.convergenceRate + node.genome.faultResilience) / 3;
      const experience = Math.min(1, Math.log10(1 + node.jobsCompleted) / 3.2);
      const raw =
        0.34 * completion +
        0.26 * best.score +
        0.22 * geneQuality +
        0.18 * experience;
      return clamp01(raw * node.health.derate);
    }

    /** The workload class this node's core is strongest on. */
    bestClass(node) {
      let bestId = null;
      let best = -1;
      for (const w of this.workloads) {
        const s = this.specialisationScore(node, w);
        if (s > best) { best = s; bestId = w.id; }
      }
      const w = this.workloads.find((x) => x.id === bestId);
      return { id: bestId, name: w ? w.name : "-", score: best };
    }

    /**
     * How well this node serves a given workload class. Combines the
     * learned prior with the genes that class actually emphasises --
     * so a node with brilliant bandwidth genes does not get credit for
     * it on a workload that is compute-bound.
     */
    specialisationScore(node, workload) {
      const prior = node.specialisation[workload.id] ?? 0.2;
      const emphasised = workload.geneEmphasis || [];
      const geneAvg =
        emphasised.length > 0
          ? emphasised.reduce((a, g) => a + (node.genome[g] ?? 0.5), 0) / emphasised.length
          : 0.5;
      // A magic-budget class cannot be served at all by classical silicon.
      if (workload.magicBudget > 0 && !node.hardware.magicCapable) return 0;
      return clamp01(0.55 * prior + 0.45 * geneAvg);
    }

    // ------------------------------------------------------------------
    // Live evolution: the fleet changes because it is being used.
    // ------------------------------------------------------------------

    /**
     * One simulation step. Utilisation follows demand (set by the
     * pricing engine's feedback), wear accumulates in proportion to
     * duty cycle AND thermal excursion, and the genome drifts toward
     * whatever the node keeps being asked to do.
     */
    tick(dtHours = 1 / 60) {
      this.epoch++;
      for (const node of this.nodes) {
        if (node.health.inService) {
          this.serviceStep(node, dtHours);
          continue;
        }

        node.ageHours += dtHours;
        node.utilisationEMA = node.utilisationEMA * 0.94 + node.utilisation * 0.06;

        // Wear. Duty cycle is linear; thermal cycling is the killer, so
        // a node that swings between idle and pinned wears faster than
        // one held flat at the same average load.
        const swing = Math.abs(node.utilisation - node.utilisationEMA);
        const dutyWear = (dtHours / node.hardware.lifeHours) * (0.45 + 1.1 * node.utilisation);
        const cycleWear = (dtHours / node.hardware.lifeHours) * swing * 3.2 * node.hardware.thermalSensitivity;
        node.health.wear = clamp01(node.health.wear + dutyWear + cycleWear);
        node.health.lastServiceHours += dtHours;
        if (swing > 0.25) node.health.thermalCycles += 1;

        node.health.derate = 1 - node.health.wear * 0.22 * node.hardware.thermalSensitivity;
        node.health.hazard = weibullHazard(node.health.wear, node.hardware);
        node.health.correctableErrors += node.health.wear > 0.4 && this.rand() < node.health.wear * 0.1 ? 1 : 0;
        node.health.serviceDue = node.health.wear > 0.72 || node.health.hazard > 0.14;

        // Genome drift: the core gets better at what it is fed and
        // slowly forgets what it is not. This is why a node's price
        // should not equal its neighbour's after a month of divergence.
        if (node.currentWorkload) {
          const w = this.workloads.find((x) => x.id === node.currentWorkload);
          if (w) {
            const rate = 0.0016 * dtHours * 60 * node.utilisation;
            node.specialisation[w.id] = clamp01(node.specialisation[w.id] + rate);
            for (const g of w.geneEmphasis || []) {
              node.genome[g] = clamp01(node.genome[g] + rate * 0.35);
            }
            for (const other of this.workloads) {
              if (other.id === w.id) continue;
              node.specialisation[other.id] = clamp01(node.specialisation[other.id] - rate * 0.06);
            }
          }
        }

        // job outcomes
        if (this.rand() < node.utilisation * 0.06) {
          const failProb = node.health.hazard * 0.9 + (1 - node.genome.faultResilience) * 0.02;
          if (this.rand() < failProb) node.jobsFailed++;
          else node.jobsCompleted++;
        }

        node.utilHistory.push(node.utilisation);
        if (node.utilHistory.length > 240) node.utilHistory.shift();
      }
      return this;
    }

    /**
     * Maintenance. Taking a node out of service is not free -- it costs
     * its owner the revenue it would have earned -- which is exactly
     * why the balancer's discount window matters: it creates the trough
     * you schedule service into.
     */
    startService(node) {
      if (node.health.inService) return false;
      node.health.inService = true;
      node.health.serviceProgress = 0;
      node.health.serviceHoursNeeded = 2 + node.health.wear * 10;
      node.utilisation = 0;
      node.listed = false;
      return true;
    }

    serviceStep(node, dtHours) {
      node.health.serviceProgress = (node.health.serviceProgress || 0) + dtHours;
      if (node.health.serviceProgress >= node.health.serviceHoursNeeded) {
        // Service restores most but not all of the derate. Wear is
        // partly permanent -- silicon does not go back to new.
        node.health.wear = Math.max(0, node.health.wear - 0.42);
        node.health.derate = 1 - node.health.wear * 0.22 * node.hardware.thermalSensitivity;
        node.health.hazard = weibullHazard(node.health.wear, node.hardware);
        node.health.correctableErrors = Math.floor(node.health.correctableErrors * 0.2);
        node.health.lastServiceHours = 0;
        node.health.inService = false;
        node.health.serviceDue = false;
        node.listed = true;
      }
    }

    /** Remaining useful life in hours, from the current hazard rate. */
    remainingLife(node) {
      const remainingFraction = Math.max(0, 1 - node.health.wear);
      return remainingFraction * node.hardware.lifeHours;
    }

    /**
     * Maintenance reserve: the dollars per node-hour that must be
     * withheld from the clearing price to fund this node's eventual
     * service. Rises steeply with hazard -- so a node everyone wants
     * is a node that is putting more aside, which is the honest way
     * to charge the premium the user described.
     */
    maintenanceReserve(node) {
      const serviceCost = node.hardware.baseRate * 6 + 180;
      const expectedHoursToService = Math.max(60, (0.72 - node.health.wear) * node.hardware.lifeHours * 0.4);
      return (serviceCost / expectedHoursToService) * (1 + node.health.hazard * 8);
    }

    /**
     * Capital recovery per node-hour: what the chassis cost, spread over
     * the hours it will actually deliver.
     *
     * This belongs in the floor and energy alone does not. Electricity
     * for a CPU node is a few cents an hour, so a floor of energy plus
     * maintenance would let the balancer discount a node to a price
     * that never repays the machine. The operator would be running at
     * a loss and calling it utilisation.
     *
     * Derated by health, because a worn node delivers fewer useful
     * hours over the same calendar and has to recover its capex faster.
     */
    capitalRecovery(node) {
      const capex = node.hardware.baseRate * CAPEX_MULTIPLE[node.hardware.kind] || node.hardware.baseRate * 900;
      const deliverableHours = Math.max(1000, node.hardware.lifeHours * 0.72 * node.health.derate);
      return capex / deliverableHours;
    }

    listedNodes() {
      return this.nodes.filter((n) => n.listed && !n.health.inService);
    }

    get(id) {
      return this.byId.get(id);
    }

    /** Neighbours in the fabric -- the cheap migration channels. */
    neighboursOf(node) {
      const prefix = node.addr.slice(0, -1).join(".");
      const point = node.cellPoint;
      return this.nodes.filter(
        (n) =>
          n.id !== node.id &&
          n.addr.slice(0, -1).join(".") === prefix &&
          S.isAdjacent(point, n.cellPoint)
      );
    }
  }

  // ---- helpers ---------------------------------------------------------

  // Capex as a multiple of the hourly base rate. An accelerator costs
  // roughly a thousand hours of its own rental to buy; a photonic leaf
  // is a research instrument and costs far more relative to its rate.
  const CAPEX_MULTIPLE = {
    gpu: 1100, cpu: 950, fpga: 1400, neuro: 1600, photonic: 2600, composite: 1100,
  };

  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  /**
   * Weibull hazard with shape k = 2.4 (wear-out dominated, which is
   * what accelerators actually show after the infant-mortality window).
   * Photonics get a lower shape because optics do not thermal-cycle
   * the same way.
   */
  function weibullHazard(wearFraction, hw) {
    const k = hw.kind === "photonic" ? 1.4 : hw.kind === "fpga" || hw.kind === "neuro" ? 1.9 : 2.4;
    const x = Math.max(0.001, Math.min(0.999, wearFraction));
    return Math.min(0.6, (k / 1) * Math.pow(x, k - 1) * 0.05 * (hw.thermalSensitivity || 1));
  }

  const FleetAPI = { Fleet, Node, GENE_NAMES, weibullHazard, clamp01 };
  root.Fleet = Fleet;
  root.HolotradeFleet = FleetAPI;
  if (typeof module !== "undefined" && module.exports) module.exports = FleetAPI;
})(typeof window !== "undefined" ? window : globalThis);
