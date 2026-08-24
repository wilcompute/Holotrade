// ======================================================================
// HOLOTRADE GENETICS
//
// The premise: a node is not a fungible rectangle of FLOPs. It carries
// an AI core that accumulates priors from every job it runs, and after
// a month of divergent work two identical chassis are no longer the
// same product. One of them will reach your target loss in fewer
// node-hours than the other, and that difference is measurable, so it
// should be priced.
//
// This module is the machinery for measuring it:
//
//   LINEAGE    where a core came from. High-fitness cores get
//              checkpointed and redeployed onto fresh silicon, so core
//              identity outlives chassis identity. That is a real
//              practice -- warm starts, model merging, checkpoint
//              averaging -- and it means provenance is a property of
//              the CORE, tracked separately from the hardware.
//
//   FITNESS    what a core has actually achieved. Completion record,
//              genome quality on the class it is strongest at, and
//              experience depth. Never a nameplate figure.
//
//   BREEDING   crossover of two high-fitness cores onto fresh hardware,
//              with the child's expected fitness reported BEFORE the
//              deployment and its realised fitness tracked after, so
//              the claim is falsifiable rather than promotional.
//
//   DRIFT      the honest caveat that goes on every genome lease: a
//              leased core keeps specialising toward whatever YOU feed
//              it. You are buying a starting point, not a frozen asset,
//              and by the end of a long lease you will have changed the
//              thing you rented.
//
// ---------------------------------------------------------------------
// WHY THIS IS THE INTERESTING HALF OF THE EXCHANGE
//
// Spot node-hours are a commodity and commodities converge to their
// marginal cost -- energy plus maintenance reserve, which is exactly
// the floor the pricing engine refuses to clear below. There is no
// durable business in selling undifferentiated node-hours.
//
// Trained cores are not a commodity. They are heterogeneous, their
// quality is observable, and their value compounds with use. That is
// where the spread lives, and it is why the genome lease exists as an
// instrument rather than as a footnote on the spot product.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);
  const FleetAPI = root.HolotradeFleet || (typeof require !== "undefined" ? require("./fleet.js") : null);
  const GENE_NAMES = FleetAPI ? FleetAPI.GENE_NAMES : [
    "throughput", "memoryBandwidth", "thermalStability",
    "convergenceRate", "faultResilience", "adaptability",
  ];

  class GeneticsEngine {
    constructor(fleet, workloads) {
      this.fleet = fleet;
      this.workloads = workloads;
      this.rand = S.rng("holotrade-genetics");
      this.breedLog = [];
      this.maxBreedLog = 80;
      this.generation = 0;
    }

    // ------------------------------------------------------------------
    // Lineage
    // ------------------------------------------------------------------

    /** Walk a core's ancestry back to its founder. */
    ancestry(node, maxDepth = 12) {
      const chain = [node];
      let cur = node;
      let depth = 0;
      while (cur.lineage.forkedFrom && depth++ < maxDepth) {
        const parent = this.fleet.get(cur.lineage.forkedFrom);
        if (!parent) break;
        chain.push(parent);
        cur = parent;
      }
      return chain;
    }

    /** Every core forked from this one, recursively. */
    descendants(node, maxDepth = 6) {
      const out = [];
      const walk = (id, depth) => {
        if (depth > maxDepth) return;
        for (const n of this.fleet.nodes) {
          if (n.lineage.forkedFrom === id) {
            out.push({ node: n, depth });
            walk(n.id, depth + 1);
          }
        }
      };
      walk(node.id, 1);
      return out;
    }

    /**
     * Founder cores: generation-0 ancestors that seeded the most
     * descendants. These are the bloodlines of the fleet, and a lease
     * on a node from a strong bloodline commands a provenance premium
     * that is measurable rather than sentimental.
     */
    founders(limit = 10) {
      const counts = new Map();
      for (const n of this.fleet.nodes) {
        const chain = this.ancestry(n);
        const founder = chain[chain.length - 1];
        if (!founder || founder.id === n.id) continue;
        counts.set(founder.id, (counts.get(founder.id) || 0) + 1);
      }
      return [...counts.entries()]
        .map(([id, descendants]) => {
          const node = this.fleet.get(id);
          return node ? { node, descendants, fitness: this.fleet.fitness(node) } : null;
        })
        .filter(Boolean)
        .sort((a, b) => b.descendants - a.descendants)
        .slice(0, limit);
    }

    /**
     * Bloodline strength: mean realised fitness of everything descended
     * from a founder. A bloodline whose descendants underperform is a
     * bloodline whose founder got lucky, and this number says so.
     */
    bloodlineStrength(founder) {
      const kids = this.descendants(founder);
      if (!kids.length) return { mean: this.fleet.fitness(founder), n: 0 };
      const fits = kids.map((k) => this.fleet.fitness(k.node));
      const mean = fits.reduce((a, b) => a + b, 0) / fits.length;
      const std = Math.sqrt(fits.reduce((a, f) => a + (f - mean) ** 2, 0) / fits.length);
      return { mean, std, n: kids.length, best: Math.max(...fits) };
    }

    // ------------------------------------------------------------------
    // Fitness leaderboard
    // ------------------------------------------------------------------

    leaderboard({ workloadId = null, limit = 25 } = {}) {
      const w = workloadId ? this.workloads.find((x) => x.id === workloadId) : null;
      return this.fleet.nodes
        .map((node) => {
          const fitness = this.fleet.fitness(node);
          const best = this.fleet.bestClass(node);
          const score = w ? this.fleet.specialisationScore(node, w) : fitness;
          return {
            node, fitness, best, score,
            generation: node.lineage.generation,
            jobs: node.jobsCompleted,
            failRate: node.jobsFailed / Math.max(1, node.jobsCompleted + node.jobsFailed),
          };
        })
        .filter((r) => r.score > 0)
        .sort((a, b) => b.score - a.score)
        .slice(0, limit);
    }

    /**
     * How specialised the fleet is overall. A fleet where every node is
     * good at everything is a fleet with no genome premium to sell; a
     * fleet of sharp specialists has a real spread but is fragile to a
     * demand shift. This number is the venue's own risk metric.
     */
    specialisationIndex() {
      let total = 0;
      let n = 0;
      for (const node of this.fleet.nodes) {
        const vals = this.workloads.map((w) => node.specialisation[w.id] ?? 0);
        const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
        const max = Math.max(...vals);
        if (mean > 0) { total += (max - mean) / mean; n++; }
      }
      return n > 0 ? total / n : 0;
    }

    /** Distribution of the fleet's strongest classes -- where the priors sit. */
    classCensus() {
      const counts = new Map();
      for (const node of this.fleet.nodes) {
        const best = this.fleet.bestClass(node);
        if (!best.id) continue;
        const row = counts.get(best.id) || { id: best.id, name: best.name, count: 0, meanScore: 0 };
        row.count++;
        row.meanScore += best.score;
        counts.set(best.id, row);
      }
      const rows = [...counts.values()].map((r) => ({ ...r, meanScore: r.meanScore / r.count }));
      return rows.sort((a, b) => b.count - a.count);
    }

    // ------------------------------------------------------------------
    // Breeding
    // ------------------------------------------------------------------

    /**
     * Crossover two cores onto a target chassis.
     *
     * Gene-level uniform crossover with a small mutation rate, plus
     * specialisation blending. This is the software operation of
     * merging two checkpoints and warm-starting from the result -- not
     * a biological metaphor being taken literally.
     *
     * The child's genes are bounded by what the TARGET HARDWARE can
     * express: you cannot cross two brilliant bandwidth genomes onto a
     * chassis with a narrow bus and get bandwidth. That clamp is the
     * difference between this being a model and being wishful.
     */
    breed(parentA, parentB, targetNode) {
      if (!parentA || !parentB || !targetNode) return { ok: false, reason: "need two parents and a target" };
      if (targetNode.health.inService) return { ok: false, reason: "target node in service" };

      const fitA = this.fleet.fitness(parentA);
      const fitB = this.fleet.fitness(parentB);
      const predicted = this.predictFitness(parentA, parentB, targetNode);

      const child = {};
      for (const g of GENE_NAMES) {
        // fitness-weighted uniform crossover
        const pick = this.rand() < fitA / Math.max(1e-6, fitA + fitB) ? parentA : parentB;
        let v = pick.genome[g];
        if (this.rand() < 0.12) v += (this.rand() - 0.5) * 0.18;  // mutation
        child[g] = clamp01(v);
      }

      // hardware ceiling: the chassis is the constraint the genes live in
      const ceiling = this.hardwareCeiling(targetNode.hardware);
      for (const g of GENE_NAMES) child[g] = Math.min(child[g], ceiling[g]);

      // specialisation: blended priors, attenuated because a merge is
      // lossy -- you do not get the union of two cores' knowledge
      const spec = {};
      for (const w of this.workloads) {
        const a = parentA.specialisation[w.id] ?? 0.2;
        const b = parentB.specialisation[w.id] ?? 0.2;
        spec[w.id] = clamp01((a * fitA + b * fitB) / Math.max(1e-6, fitA + fitB) * 0.82);
      }

      const before = this.fleet.fitness(targetNode);
      targetNode.genome = child;
      targetNode.specialisation = spec;
      targetNode.lineage = {
        parents: [parentA.id, parentB.id],
        forkedFrom: fitA >= fitB ? parentA.id : parentB.id,
        generation: Math.max(parentA.lineage.generation, parentB.lineage.generation) + 1,
        bred: true,
        bredAt: Date.now(),
      };
      // a fresh core has no track record; the exchange must not credit
      // it with its parents' completions
      targetNode.jobsCompleted = Math.floor(targetNode.jobsCompleted * 0.1);
      targetNode.jobsFailed = Math.floor(targetNode.jobsFailed * 0.1);

      const after = this.fleet.fitness(targetNode);
      this.generation++;

      const entry = {
        ts: Date.now(),
        parents: [parentA.id, parentB.id],
        target: targetNode.id,
        parentFitness: [fitA, fitB],
        predicted,
        before,
        after,
        // reported honestly: a bred core starts with strong genes and
        // NO track record, so its realised fitness is below its
        // parents' until it has earned some completions
        delta: after - before,
        generation: targetNode.lineage.generation,
      };
      this.breedLog.unshift(entry);
      if (this.breedLog.length > this.maxBreedLog) this.breedLog.pop();
      return { ok: true, ...entry, node: targetNode };
    }

    /**
     * What a chassis can physically express. Crossing genomes onto
     * hardware that cannot support them is where a genetics story
     * stops being honest, so this is a hard clamp rather than a hint.
     */
    hardwareCeiling(hw) {
      const base = {
        gpu: { throughput: 0.98, memoryBandwidth: 0.97, thermalStability: 0.72, convergenceRate: 0.9, faultResilience: 0.85, adaptability: 0.82 },
        cpu: { throughput: 0.7, memoryBandwidth: 0.62, thermalStability: 0.96, convergenceRate: 0.78, faultResilience: 0.97, adaptability: 0.98 },
        fpga: { throughput: 0.82, memoryBandwidth: 0.78, thermalStability: 0.97, convergenceRate: 0.74, faultResilience: 0.93, adaptability: 0.6 },
        neuro: { throughput: 0.62, memoryBandwidth: 0.55, thermalStability: 0.98, convergenceRate: 0.93, faultResilience: 0.9, adaptability: 0.52 },
        photonic: { throughput: 0.8, memoryBandwidth: 0.5, thermalStability: 0.99, convergenceRate: 0.96, faultResilience: 0.98, adaptability: 0.7 },
        composite: { throughput: 0.95, memoryBandwidth: 0.95, thermalStability: 0.9, convergenceRate: 0.9, faultResilience: 0.9, adaptability: 0.9 },
      }[hw.kind] || {};
      const out = {};
      for (const g of GENE_NAMES) out[g] = base[g] ?? 0.9;
      return out;
    }

    /**
     * Predicted child fitness, stated BEFORE the cross so it can be
     * checked afterwards. Deliberately conservative: it applies the
     * merge attenuation and the loss of track record, which is why
     * predictions here come in below the better parent.
     */
    predictFitness(parentA, parentB, targetNode) {
      const fitA = this.fleet.fitness(parentA);
      const fitB = this.fleet.fitness(parentB);
      const ceiling = this.hardwareCeiling(targetNode.hardware);
      const ceilingMean = GENE_NAMES.reduce((a, g) => a + ceiling[g], 0) / GENE_NAMES.length;
      const parentMean = (fitA + fitB) / 2;
      const heterosis = 1 + Math.abs(fitA - fitB) * 0.14;   // hybrid vigour, modest
      const trackRecordLoss = 0.82;                          // no completions yet
      return clamp01(parentMean * heterosis * trackRecordLoss * Math.min(1, ceilingMean / 0.85));
    }

    /**
     * Suggest crosses worth making: pairs whose predicted child beats
     * the target's current fitness by a real margin, ranked by gain.
     * Requires genuine genetic distance between the parents -- crossing
     * two near-identical cores produces nothing and the filter says so.
     */
    suggestCrosses({ limit = 6, workloadId = null } = {}) {
      const pool = this.leaderboard({ workloadId, limit: 30 }).map((r) => r.node);
      // Targets are the fleet's weakest quartile by realised fitness --
      // a RELATIVE threshold, because an absolute one stops finding
      // anything the moment the fleet as a whole improves, which is
      // exactly when you still want to be breeding the laggards up.
      const ranked = this.fleet.nodes
        .filter((n) => !n.health.inService)
        .sort((a, b) => this.fleet.fitness(a) - this.fleet.fitness(b));
      const targets = ranked.slice(0, Math.max(8, Math.floor(ranked.length * 0.25)));

      const out = [];
      for (let i = 0; i < pool.length && out.length < limit * 4; i++) {
        for (let j = i + 1; j < pool.length; j++) {
          const a = pool[i];
          const b = pool[j];
          const distance = this.geneticDistance(a, b);
          if (distance < 0.18) continue;         // too similar to be worth crossing
          const target = targets.find((t) => t.hardware.kind === a.hardware.kind) || targets[0];
          if (!target) continue;
          const predicted = this.predictFitness(a, b, target);
          const current = this.fleet.fitness(target);
          if (predicted <= current + 0.04) continue;
          out.push({
            parents: [a, b], target, predicted, current,
            gain: predicted - current, distance,
          });
          break;
        }
      }
      return out.sort((x, y) => y.gain - x.gain).slice(0, limit);
    }

    /** Euclidean distance in gene space -- how different two cores are. */
    geneticDistance(a, b) {
      let sum = 0;
      for (const g of GENE_NAMES) sum += (a.genome[g] - b.genome[g]) ** 2;
      return Math.sqrt(sum / GENE_NAMES.length);
    }

    /**
     * Genetic diversity of the fleet. This is a risk metric, not a
     * vanity one: a fleet that has converged on one genome has no
     * crosses left worth making and no resilience to a workload shift.
     * Breeding aggressively for short-term fitness destroys it, which
     * is the classic failure mode and worth surfacing to an operator.
     */
    diversity() {
      const nodes = this.fleet.nodes;
      if (nodes.length < 2) return 0;
      const sample = nodes.length > 80 ? nodes.filter((_, i) => i % Math.ceil(nodes.length / 80) === 0) : nodes;
      let total = 0;
      let pairs = 0;
      for (let i = 0; i < sample.length; i++) {
        for (let j = i + 1; j < sample.length; j++) {
          total += this.geneticDistance(sample[i], sample[j]);
          pairs++;
        }
      }
      return pairs > 0 ? total / pairs : 0;
    }

    /**
     * Drift forecast for a genome lease: where this core's priors will
     * be after N days of running the lessee's workload. Goes on the
     * lease quote, because a lessee who does not know this is going to
     * be surprised when the core they rented for genomics comes back
     * good at inference.
     */
    driftForecast(node, workloadId, days) {
      const w = this.workloads.find((x) => x.id === workloadId);
      if (!w) return null;
      const ratePerDay = 0.0016 * 60 * 24 * Math.max(0.3, node.utilisation);
      const before = { ...node.specialisation };
      const after = {};
      for (const other of this.workloads) {
        if (other.id === workloadId) {
          after[other.id] = clamp01(before[other.id] + ratePerDay * days);
        } else {
          after[other.id] = clamp01(before[other.id] - ratePerDay * days * 0.06);
        }
      }
      const bestBefore = this.fleet.bestClass(node);
      return {
        ratePerDay,
        days,
        before,
        after,
        willReSpecialise: after[workloadId] > (before[bestBefore.id] ?? 0) && bestBefore.id !== workloadId,
        note: "a leased core keeps learning from your work; you are buying a starting point, not a frozen asset",
      };
    }

    summary() {
      return {
        generation: this.generation,
        diversity: this.diversity(),
        specialisationIndex: this.specialisationIndex(),
        founders: this.founders(5).length,
        crossesMade: this.breedLog.length,
        meanFitness:
          this.fleet.nodes.reduce((a, n) => a + this.fleet.fitness(n), 0) / Math.max(1, this.fleet.nodes.length),
        maxGeneration: Math.max(...this.fleet.nodes.map((n) => n.lineage.generation)),
      };
    }
  }

  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  const API = { GeneticsEngine, GENE_NAMES };
  root.GeneticsEngine = GeneticsEngine;
  root.HolotradeGenetics = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
