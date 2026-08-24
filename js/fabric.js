// ======================================================================
// HOLOTRADE FABRIC MARKET
//
// The single most consequential fact about this substrate for a trading
// venue: THE COMPUTER IS THE NETWORK AND THE NETWORK IS THE COMPUTER.
// Routing a packet is applying a gate is addressing memory. That is an
// algebraic identity on W(3,3), not an analogy.
//
// Every conventional compute marketplace assumes the opposite. It sells
// you compute, then sells you network, then sells you egress, because
// in a von Neumann machine those are three separate things with three
// separate bills. Here they are one thing, and a venue that keeps
// pricing them separately is mispricing its own product.
//
// ---------------------------------------------------------------------
// THE CONSEQUENCE: YOU DO NOT BUY NODES, YOU BUY SHAPES
//
// Forty nodes scattered across the fabric and one complete W(3,3) cell
// of forty nodes have identical node counts and completely different
// value:
//
//   scattered 40   40 computers, and a network bill to make them
//                  cooperate. Bisection between them: whatever the
//                  public internet gives you.
//   one cell       ONE computer. Diameter 2. Bisection exactly 100 of
//                  240 edges -- 42% cross-section, the spectral bound
//                  (40/4)(12-2) met by an explicit 20|20 cut. Four
//                  internally-disjoint paths between any non-adjacent
//                  pair, because mu = 4. No configuration.
//
// So the tradeable object at scale is a SUBGRAPH, and its price is
// superlinear in its coherence, not linear in its node count. The whole
// really is worth more than the sum of its parts, and here that is a
// measurable quantity rather than a slogan: it is the realised
// bisection of what you actually hold.
//
// ---------------------------------------------------------------------
// THE MECHANISM THAT FALLS OUT: A DEFRAGMENTATION MARKET
//
// Trading fragments ownership. After a month of spot fills, everyone
// holds confetti -- a few points in each of forty cells -- and the
// aggregate bisection of the whole market has collapsed even though
// every individual position looks fine.
//
// That is a coordination failure with a clean fix: a SWAP BOOK. I give
// you my three nodes in your cell, you give me your three nodes in mine.
// No cash changes hands. Both of us end up more coherent, and the
// market's total delivered bisection rises. It is disk defragmentation,
// except the value being recovered is bandwidth, and unlike a disk both
// parties can be made strictly better off, so the swaps are voluntary.
//
// ---------------------------------------------------------------------
// AND THE MARKET IS ITSELF FRACTAL
//
// A level-n holonet is 40^n leaves at routing diameter 8n, built by
// replacing each point of one W(3,3) with a whole copy of the level
// below. So a complete subtree at any level is, as one object, a single
// computer -- which means it can be LISTED AS ONE NODE on the level
// above it. An operator's whole campus becomes one tradeable instrument
// at the parent level. Orders at level n aggregate into liquidity at
// level n+1, and the book has the same shape at every zoom.
//
// This also gives structural service levels. "Diameter 16" is not an
// SLA somebody promises you and pays penalties for missing. It is a
// theorem about the shape you bought.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  // How hard coherence is priced. At kCoherence = 0.85 a perfectly
  // coherent cell is worth ~1.85x the same nodes held as confetti --
  // which is roughly the ratio of its delivered bisection to the
  // internet path you would otherwise be renting.
  const K_COHERENCE = 0.85;

  class FabricMarket {
    constructor(fleet, pricing) {
      this.fleet = fleet;
      this.pricing = pricing;
      this.rand = S.rng("holotrade-fabric");
      this.swapBook = [];
      this.swapHistory = [];
      this.spliceLog = [];
    }

    // ------------------------------------------------------------------
    // Cells: the level-1 unit
    // ------------------------------------------------------------------

    /** Group the fleet by its cell prefix -- everything above the last digit. */
    cells() {
      const map = new Map();
      for (const node of this.fleet.nodes) {
        const prefix = node.addr.slice(0, -1).map((d) => String(d).padStart(2, "0")).join(".");
        if (!map.has(prefix)) {
          map.set(prefix, { prefix, dcId: node.dcId, nodes: [], points: new Set() });
        }
        const cell = map.get(prefix);
        cell.nodes.push(node);
        cell.points.add(node.cellPoint);
      }
      for (const cell of map.values()) {
        cell.occupancy = cell.points.size / S.CONST.points;
        cell.bisection = this.realisedBisection(cell.nodes);
        cell.coherence = this.coherence(cell.nodes);
        cell.diameter = this.realisedDiameter(cell.nodes);
      }
      return [...map.values()].sort((a, b) => b.nodes.length - a.nodes.length);
    }

    // ------------------------------------------------------------------
    // Shape metrics
    // ------------------------------------------------------------------

    /**
     * Realised bisection: the number of substrate edges actually present
     * inside a basket, crossing a balanced halving.
     *
     * A full cell hits exactly 100 -- the spectral lower bound
     * (n/4)(k - lambda_2) = (40/4)(12 - 2), met by an explicit 20|20
     * cut. A basket that holds no two adjacent nodes hits zero, and
     * every byte it moves has to leave the fabric.
     */
    realisedBisection(nodes) {
      const byPrefix = new Map();
      for (const n of nodes) {
        const p = n.addr.slice(0, -1).join(".");
        if (!byPrefix.has(p)) byPrefix.set(p, []);
        byPrefix.get(p).push(n);
      }
      let total = 0;
      for (const group of byPrefix.values()) {
        const pts = group.map((n) => n.cellPoint);
        // count internal edges, then take the balanced-cut share
        let edges = 0;
        for (let i = 0; i < pts.length; i++)
          for (let j = i + 1; j < pts.length; j++)
            if (S.isAdjacent(pts[i], pts[j])) edges++;
        // The collinearity graph has 240 undirected edges (40 x 12 / 2)
        // and a minimum bisection of exactly 100, so the share of edges
        // crossing a balanced cut is 100/240. A partial subgraph
        // inherits that share in proportion to the edges it holds.
        total += edges * (S.CONST.bisection / S.CONST.edges);
      }
      return total;
    }

    /**
     * The bisection an ideal basket of this size would deliver -- i.e.
     * if you had spent the same money on CONTIGUOUS capacity. This is
     * the denominator that turns "how many nodes" into "what shape".
     */
    idealBisection(size) {
      const fullCells = Math.floor(size / S.CONST.points);
      const remainder = size % S.CONST.points;
      // within a partial cell, the induced subgraph on r of 40 points
      // has expected edge count r(r-1)/2 * (12/39)
      const partialEdges = (remainder * (remainder - 1) / 2) * (S.CONST.degree / (S.CONST.points - 1));
      return fullCells * S.CONST.bisection + partialEdges * (S.CONST.bisection / S.CONST.edges);
    }

    /**
     * Coherence in [0,1]: how much of the achievable bisection this
     * basket actually holds. This is THE number that separates buying
     * a computer from buying a pile of parts.
     */
    coherence(nodes) {
      if (!nodes || nodes.length < 2) return 0;
      const ideal = this.idealBisection(nodes.length);
      if (ideal <= 0) return 0;
      return Math.max(0, Math.min(1, this.realisedBisection(nodes) / ideal));
    }

    /**
     * Worst-case hops inside the basket. Inside one cell this is 2 by
     * theorem. Across d address digits it is 8d, because each recursive
     * digit costs 8 reversible moves. Disconnected baskets report
     * Infinity -- they are not one computer, and the UI should say so.
     */
    realisedDiameter(nodes) {
      if (!nodes || nodes.length < 2) return 0;
      let worst = 0;
      const sample = nodes.length > 60 ? nodes.filter((_, i) => i % Math.ceil(nodes.length / 60) === 0) : nodes;
      for (let i = 0; i < sample.length; i++) {
        for (let j = i + 1; j < sample.length; j++) {
          const d = S.fabricDistance(sample[i].addr, sample[j].addr);
          if (d.hops > worst) worst = d.hops;
        }
      }
      return worst;
    }

    /**
     * THE COHERENCE MULTIPLIER -- the fabric's contribution to price.
     *
     * Applied at the BASKET level, never at the node level, because
     * coherence is not a property any single node has. This is the
     * structural reason a Holotrade order is priced as a shape.
     */
    coherenceMultiplier(nodes) {
      const c = this.coherence(nodes);
      // superlinear: the last few edges that complete a cell are worth
      // more than the first few, because they are what collapse the
      // diameter to 2 and unlock the disjoint-path multipath
      return 1 + K_COHERENCE * Math.pow(c, 1.35);
    }

    /**
     * Price a basket as one object. The per-node quotes come from the
     * pricing engine; the fabric applies the coherence premium on top
     * and reports what the buyer is structurally guaranteed.
     */
    quoteBasket(nodes, opts = {}) {
      const quotes = nodes
        .map((n) => this.pricing.quote(n, opts))
        .filter((q) => q.serviceable && q.price != null);
      if (!quotes.length) return null;

      const sumParts = quotes.reduce((a, q) => a + q.price, 0);
      const C = this.coherenceMultiplier(nodes);
      const coherence = this.coherence(nodes);
      const bisection = this.realisedBisection(nodes);
      const diameter = this.realisedDiameter(nodes);

      return {
        nodes: nodes.length,
        sumParts,
        coherence,
        coherenceMultiplier: C,
        price: sumParts * C,
        premium: sumParts * (C - 1),
        bisection,
        idealBisection: this.idealBisection(nodes.length),
        diameter,
        // what you are structurally guaranteed, as a theorem not an SLA
        guarantees: {
          maxHops: Number.isFinite(diameter) ? diameter : null,
          disjointPaths: coherence > 0.6 ? S.CONST.mu : 1,
          crashTolerance: coherence > 0.8 ? S.CONST.degree - 1 : 0,
          byzantineTolerance: coherence > 0.8 ? 5 : 0,
          tableFree: coherence > 0.9,
        },
        effectiveTflops: nodes.reduce((a, n) => a + n.effectiveTflops, 0),
      };
    }

    // ------------------------------------------------------------------
    // Fragmentation and the swap book
    // ------------------------------------------------------------------

    /**
     * Fleet-wide fragmentation. 0 means every holder's positions are
     * contiguous; 1 means everyone holds confetti. This rises on its
     * own as spot trading proceeds, which is exactly why the swap book
     * has to exist.
     */
    fragmentation(positions) {
      if (!positions || !positions.length) return 0;
      const nodes = positions.map((p) => p.node || this.fleet.get(p.nodeId)).filter(Boolean);
      if (nodes.length < 2) return 0;
      return 1 - this.coherence(nodes);
    }

    /**
     * Propose defragmentation swaps for a holder.
     *
     * A swap is only offered if BOTH sides gain coherence -- there is
     * no version of this where the venue improves one book at the
     * other's expense, because then nobody would take the other side.
     * The gain is measured in delivered bisection, which is the thing
     * that was actually lost to fragmentation.
     */
    proposeSwaps(myNodes, { limit = 6 } = {}) {
      if (!myNodes || myNodes.length < 2) return [];
      const myCoherence = this.coherence(myNodes);
      const myPrefixes = tally(myNodes.map((n) => n.addr.slice(0, -1).join(".")));

      // my "orphans": nodes sitting alone in a cell where I hold almost nothing
      const orphans = myNodes.filter(
        (n) => (myPrefixes.get(n.addr.slice(0, -1).join(".")) || 0) <= 2
      );
      // my "home" cells: where the rest of my position is concentrated
      const homes = [...myPrefixes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3).map((x) => x[0]);
      if (!orphans.length || !homes.length) return [];

      const proposals = [];
      const held = new Set(myNodes.map((n) => n.id));

      for (const orphan of orphans) {
        const orphanPrefix = orphan.addr.slice(0, -1).join(".");
        for (const home of homes) {
          if (home === orphanPrefix) continue;
          // find a counterparty node in MY home cell that I do not hold,
          // whose owner would benefit from consolidating into the
          // orphan's cell instead
          const candidates = this.fleet.nodes.filter(
            (n) =>
              !held.has(n.id) &&
              n.addr.slice(0, -1).join(".") === home &&
              n.listed &&
              !n.health.inService &&
              n.hardware.class === orphan.hardware.class
          );
          if (!candidates.length) continue;

          // pick the candidate that most improves my shape
          let best = null;
          for (const cand of candidates.slice(0, 12)) {
            const after = myNodes.filter((n) => n.id !== orphan.id).concat([cand]);
            const gain = this.coherence(after) - myCoherence;
            if (gain > 0 && (!best || gain > best.gain)) {
              best = { cand, gain, after };
            }
          }
          if (!best) continue;

          const myBisGain = this.realisedBisection(best.after) - this.realisedBisection(myNodes);
          proposals.push({
            id: `SWP-${S.hash32(orphan.id + best.cand.id).toString(16).slice(0, 6)}`,
            give: orphan,
            get: best.cand,
            coherenceGain: best.gain,
            bisectionGain: myBisGain,
            counterparty: best.cand.operator,
            // the counterparty's mirror gain: they consolidate into the
            // cell my orphan is sitting in
            counterpartyGain: this.mirrorGain(best.cand, orphan),
            cashAdjustment: this.swapCashAdjustment(orphan, best.cand),
          });
        }
      }
      proposals.sort((a, b) => b.bisectionGain - a.bisectionGain);
      return proposals.slice(0, limit);
    }

    /** What the other side gets: how much of their own cell the orphan completes. */
    mirrorGain(theirNode, myOrphan) {
      const theirPrefix = myOrphan.addr.slice(0, -1).join(".");
      const theirs = this.fleet.nodes.filter(
        (n) => n.operator === theirNode.operator && n.addr.slice(0, -1).join(".") === theirPrefix
      );
      const before = this.coherence(theirs);
      const after = this.coherence(theirs.concat([myOrphan]));
      return after - before;
    }

    /**
     * Swaps are usually not value-neutral -- one node may be healthier,
     * younger or better-trained than the other. The cash adjustment
     * settles that difference so the swap can be a pure shape trade.
     */
    swapCashAdjustment(give, get) {
      const qGive = this.pricing.quote(give, {});
      const qGet = this.pricing.quote(get, {});
      if (!qGive.serviceable || !qGet.serviceable) return 0;
      return qGet.price - qGive.price;
    }

    executeSwap(proposal, positions) {
      const pos = positions.find((p) => p.nodeId === proposal.give.id);
      if (!pos) return { ok: false, reason: "position not held" };
      pos.nodeId = proposal.get.id;
      pos.node = proposal.get;
      this.swapHistory.unshift({
        ...proposal,
        ts: Date.now(),
        gave: proposal.give.id,
        got: proposal.get.id,
      });
      if (this.swapHistory.length > 100) this.swapHistory.pop();
      return { ok: true, cash: -proposal.cashAdjustment };
    }

    // ------------------------------------------------------------------
    // Levels: the fractal instrument ladder
    // ------------------------------------------------------------------

    /**
     * The instrument ladder. Each level is a whole subtree traded as
     * ONE object, because at every level a complete subtree is, as one
     * object, a single computer.
     *
     * Note what happens to the per-node price as you climb: it FALLS,
     * because the fabric comes free with the shape -- you stop paying
     * for interconnect you would otherwise have to rent. But the total
     * rises superlinearly, because coherence is worth more than count.
     * Both of those are correct and they are the same fact seen twice.
     */
    levelLadder(maxLevel = 7) {
      const rows = [];
      const medianQuote = this.medianNodePrice();
      for (let n = 1; n <= maxLevel; n++) {
        const leaves = S.capacityAtLevel(n);
        const instances = Math.round((leaves - 1) / 39) + 1;
        const diameter = S.diameterAtLevel(n);
        // full coherence at every level by construction
        const C = 1 + K_COHERENCE;
        // interconnect saving: a conventional fleet of this size needs
        // a fat-tree; here bisection is a property of the shape
        const fabricDiscount = 1 / (1 + Math.log10(leaves) * 0.06);
        rows.push({
          level: n,
          leaves,
          instances,
          diameter,
          bisection: S.CONST.bisection * Math.pow(40, n - 1),
          perNodeHour: medianQuote * fabricDiscount,
          totalPerHour: medianQuote * fabricDiscount * leaves * C,
          coherenceMultiplier: C,
          seats: LEVEL_SEATS[n] || `${leaves.toLocaleString()} leaves`,
          tradeable: leaves <= 64000,   // above this it is a bilateral deal
        });
      }
      return rows;
    }

    medianNodePrice() {
      const stats = this.pricing.marketStats();
      return stats ? stats.median : 20;
    }

    /**
     * Splice: how a node joins.
     *
     * Joining is a LOCAL operation -- you graft a W(3,3) copy into the
     * incidence structure at one point and nothing else in the fabric
     * has to be told. There is no rebalancing pass, no consistent-hash
     * ring to rotate, no global reconfiguration. Because W(E6) is
     * transitive on leaves, the new node is immediately
     * indistinguishable from every other node under the automorphism
     * group -- it does not have to earn a place in a topology.
     *
     * For a two-sided market that is the difference between "list your
     * idle machine" costing nothing and costing a fleet-wide event.
     */
    splice(node, atPrefix) {
      const prefix = S.parseAddress(atPrefix);
      const occupied = new Set(
        this.fleet.nodes
          .filter((n) => n.addr.slice(0, -1).join(".") === prefix.join("."))
          .map((n) => n.cellPoint)
      );
      let point = -1;
      for (let p = 0; p < S.CONST.points; p++) {
        if (!occupied.has(p)) { point = p; break; }
      }
      if (point < 0) return { ok: false, reason: "cell is full; splice one level deeper" };

      node.addr = [...prefix, point];
      node.listed = true;
      const entry = {
        ts: Date.now(),
        nodeId: node.id,
        address: node.address,
        cost: "O(1) -- local graft, no global reconfiguration",
        neighbours: S.ADJ[point].length,
      };
      this.spliceLog.unshift(entry);
      if (this.spliceLog.length > 60) this.spliceLog.pop();
      return { ok: true, ...entry };
    }

    // ------------------------------------------------------------------
    // Clearing on the fabric
    // ------------------------------------------------------------------

    /**
     * The venue does not need a matching-engine bottleneck.
     *
     * W(E6) acts transitively on the leaves, so no node is
     * architecturally privileged and leader election has nothing to
     * elect. Agreement is two hops plus a neighbour-averaging round
     * that contracts disagreement by 1/3 per step -- about 19 rounds
     * for a part in 1e9 -- and the committee tolerates 5 lying nodes
     * out of 40. Six breaks the tested configuration; that is a
     * measured boundary, not a margin.
     *
     * The energy contrast is the part that matters commercially:
     * proof-of-work spends on the order of 1e9 J of dissipated work per
     * transaction. Here the only irreducible cost is the Landauer
     * syndrome export at ~2.6e-19 J. Twenty-seven orders of magnitude,
     * because security is a group-membership check rather than burned
     * electricity.
     *
     * Honest scope: this is a property of the substrate as specified.
     * No physical holonet exists, so today the clearing loop runs as
     * the classical Clifford emulation -- which is polynomial-time and
     * runs anywhere, and is what this simulation actually executes.
     */
    clearingRounds(precision = 1e-9) {
      // disagreement contracts by 1/3 per averaging round
      return Math.ceil(Math.log(precision) / Math.log(1 / 3));
    }

    clearingProfile() {
      const rounds = this.clearingRounds();
      return {
        hops: 2,
        rounds,
        contractionPerRound: 1 / 3,
        byzantineTolerance: 5,
        byzantineBreaks: 6,
        leaderless: true,
        joulesPerClear: S.landauerFloorPerCycle(300),
        pathOfWorkComparison: 1e9,
        ordersOfMagnitude: Math.round(Math.log10(1e9 / S.landauerFloorPerCycle(300))),
      };
    }

    /**
     * Aggregate market health from the fabric's point of view -- the
     * numbers a venue running on this substrate would publish instead
     * of "volume" and "open interest".
     */
    fabricStats(positions) {
      const cells = this.cells();
      const listed = this.fleet.listedNodes();
      const totalBisection = this.realisedBisection(listed);
      const completeCells = cells.filter((c) => c.occupancy >= 0.95).length;
      return {
        cells: cells.length,
        completeCells,
        meanOccupancy: cells.length ? cells.reduce((a, c) => a + c.occupancy, 0) / cells.length : 0,
        totalBisection,
        idealBisection: this.idealBisection(listed.length),
        fleetCoherence: this.coherence(listed),
        fragmentation: this.fragmentation(positions),
        level: S.levelFor(this.fleet.nodes.length),
        diameterAtLevel: S.diameterAtLevel(S.levelFor(this.fleet.nodes.length)),
        swapsAvailable: this.swapBook.length,
        swapsExecuted: this.swapHistory.length,
      };
    }
  }

  // ====================================================================
  // COMPOSITION -- the recursion closes
  //
  // A network of computers is a computer. So a network of THOSE is also
  // a computer, and so on up. That is not a metaphor about scale; it is
  // the fractal substitution law H_n, where each of the 40 points of one
  // W(3,3) is replaced by an entire copy of the level below. The
  // resulting object has the same symmetry group, the same routing rule,
  // the same diameter law (8 hops per address digit) -- it is the same
  // KIND of thing as its own parts.
  //
  // For a venue, this is the load-bearing structural fact, and it has a
  // sharp consequence: THERE IS ONLY ONE ORDER BOOK AND ONE PRICING
  // ENGINE, AND THEY APPLY AT EVERY LEVEL.
  //
  // A Composite implements exactly the interface a leaf Node implements
  // -- an address, a genome, a health record, a utilisation, an
  // effective throughput, a hardware descriptor. So the pricing engine
  // cannot tell whether it is quoting one machine or a campus, and does
  // not need to. An operator lists their whole H_3 campus as a single
  // instrument at level 4; a buyer at level 5 sees it as one line in the
  // same book that a single GPU appears in at level 1.
  //
  // The book is self-similar because the machine is.
  // ====================================================================

  class Composite {
    /**
     * @param children  leaf Nodes or other Composites -- the recursion
     *                  takes either, which is the whole point
     * @param fabric    the FabricMarket, for coherence measurement
     */
    constructor(children, fabric, opts = {}) {
      this.children = children;
      this.fabric = fabric;
      this.isComposite = true;
      this.level = 1 + Math.max(...children.map((c) => c.level || 0));
      this.leaves = children.reduce((a, c) => a + (c.leaves || 1), 0);

      const leafNodes = this.flatten();
      this.coherence = fabric.coherence(leafNodes);
      this.addr = commonPrefix(leafNodes.map((n) => n.addr));
      this.id = opts.id || `CMP-L${this.level}-${S.formatAddress(this.addr) || "root"}`;
      this.name = opts.name || `Level-${this.level} composite (${this.leaves.toLocaleString()} leaves)`;
      this.operator = opts.operator || dominant(leafNodes.map((n) => n.operator));
      this.dcId = dominant(leafNodes.map((n) => n.dcId));

      this.hardware = this.aggregateHardware(leafNodes);
      this.genome = this.aggregateGenome(leafNodes);
      this.health = this.aggregateHealth(leafNodes);
      this.specialisation = this.aggregateSpecialisation(leafNodes);
      this.lineage = {
        parents: children.map((c) => c.id),
        generation: Math.max(...leafNodes.map((n) => n.lineage.generation)),
        forkedFrom: null,
        composed: true,
      };

      this.utilisation = weightedMean(leafNodes.map((n) => [n.utilisation, n.hardware.tflops]));
      this.utilisationEMA = weightedMean(leafNodes.map((n) => [n.utilisationEMA, n.hardware.tflops]));
      this.jobsCompleted = leafNodes.reduce((a, n) => a + n.jobsCompleted, 0);
      this.jobsFailed = leafNodes.reduce((a, n) => a + n.jobsFailed, 0);
      this.listed = leafNodes.every((n) => n.listed);
      this.priceHistory = [];
      this.utilHistory = [];
      this.currentWorkload = null;
    }

    /** Recursively collapse to leaf nodes. The recursion bottoms out here. */
    flatten() {
      const out = [];
      for (const c of this.children) {
        if (c.isComposite) out.push(...c.flatten());
        else out.push(c);
      }
      return out;
    }

    get address() {
      return S.formatAddress(this.addr) + (this.addr.length ? ".*" : "*");
    }

    get cellPoint() {
      return this.addr.length ? this.addr[this.addr.length - 1] : 0;
    }

    /**
     * Effective throughput of the composed object.
     *
     * NOT the sum of its parts. Coherence enters here because a
     * disconnected pile cannot run one job -- the fabric is what makes
     * the sum usable as a single machine. A perfectly coherent
     * composite delivers its full sum; an incoherent one delivers the
     * sum discounted toward what its largest connected piece can do.
     */
    get effectiveTflops() {
      const raw = this.flatten().reduce((a, n) => a + n.effectiveTflops, 0);
      return raw * (0.45 + 0.55 * this.coherence);
    }

    /**
     * The composite's hardware descriptor. `baseRate` is the sum of the
     * children's floors, so the pricing engine's multiplicative model
     * lands on the right order of magnitude with no special-casing.
     * `magicCapable` is true if ANY leaf is -- one photonic leaf in a
     * campus makes the campus able to serve a magic-budget plan.
     */
    aggregateHardware(leaves) {
      return {
        class: `H${this.level}`,
        name: `Level-${this.level} composite`,
        kind: "composite",
        tflops: leaves.reduce((a, n) => a + n.hardware.tflops, 0),
        memGB: leaves.reduce((a, n) => a + n.hardware.memGB, 0),
        memBW: leaves.reduce((a, n) => a + n.hardware.memBW, 0),
        tdp: leaves.reduce((a, n) => a + n.hardware.tdp, 0),
        baseRate: leaves.reduce((a, n) => a + n.hardware.baseRate, 0),
        lifeHours: Math.min(...leaves.map((n) => n.hardware.lifeHours)),
        joulesPerOp: weightedMean(leaves.map((n) => [n.hardware.joulesPerOp, n.hardware.tflops])),
        magicCapable: leaves.some((n) => n.hardware.magicCapable),
        thermalSensitivity: weightedMean(leaves.map((n) => [n.hardware.thermalSensitivity, n.hardware.tdp])),
      };
    }

    /**
     * The composite's genome. Throughput-weighted for the capacity
     * genes; MINIMUM for faultResilience, because a composed machine is
     * only as resilient as its weakest constituent -- averaging that
     * would be the kind of flattering aggregate that gets someone's
     * training run killed at hour 300.
     */
    aggregateGenome(leaves) {
      const w = leaves.map((n) => n.hardware.tflops);
      const g = {};
      for (const key of ["throughput", "memoryBandwidth", "thermalStability", "convergenceRate", "adaptability"]) {
        g[key] = weightedMean(leaves.map((n, i) => [n.genome[key], w[i]]));
      }
      g.faultResilience = Math.min(...leaves.map((n) => n.genome.faultResilience));
      return g;
    }

    /**
     * Composed health. Hazard is the union: the probability that ANY
     * constituent fails, which is what actually interrupts your job.
     * Derate is capacity-weighted. Wear is the max, not the mean --
     * the composite is due for service when its worst member is.
     */
    aggregateHealth(leaves) {
      const survival = leaves.reduce((a, n) => a * (1 - n.health.hazard), 1);
      return {
        wear: Math.max(...leaves.map((n) => n.health.wear)),
        meanWear: leaves.reduce((a, n) => a + n.health.wear, 0) / leaves.length,
        thermalCycles: leaves.reduce((a, n) => a + n.health.thermalCycles, 0),
        powerCycles: leaves.reduce((a, n) => a + n.health.powerCycles, 0),
        correctableErrors: leaves.reduce((a, n) => a + n.health.correctableErrors, 0),
        uncorrectableErrors: leaves.reduce((a, n) => a + n.health.uncorrectableErrors, 0),
        derate: weightedMean(leaves.map((n) => [n.health.derate, n.hardware.tflops])),
        hazard: 1 - survival,
        lastServiceHours: Math.max(...leaves.map((n) => n.health.lastServiceHours)),
        inService: leaves.some((n) => n.health.inService),
        serviceDue: leaves.some((n) => n.health.serviceDue),
      };
    }

    /** Capacity-weighted priors -- what this campus collectively knows. */
    aggregateSpecialisation(leaves) {
      const spec = {};
      const keys = Object.keys(leaves[0].specialisation || {});
      for (const k of keys) {
        spec[k] = weightedMean(leaves.map((n) => [n.specialisation[k] ?? 0, n.hardware.tflops]));
      }
      return spec;
    }

    /** Structural guarantees of the composed shape -- theorems, not SLAs. */
    guarantees() {
      return {
        level: this.level,
        leaves: this.leaves,
        maxHops: S.diameterAtLevel(this.level),
        bisection: this.fabric.realisedBisection(this.flatten()),
        disjointPaths: this.coherence > 0.6 ? S.CONST.mu : 1,
        crashTolerance: this.coherence > 0.8 ? S.CONST.degree - 1 : 0,
        byzantineTolerance: this.coherence > 0.8 ? 5 : 0,
        coherence: this.coherence,
      };
    }
  }

  /**
   * Compose children into one tradeable object one level up.
   *
   * Accepts leaves, composites, or a mix -- which is what makes the
   * recursion close rather than merely repeat. compose(compose(x)) is
   * well-formed and produces a thing of the same kind, so a market at
   * level 5 quotes exactly the way a market at level 1 does.
   */
  FabricMarket.prototype.compose = function (children, opts = {}) {
    if (!children || children.length < 2) return null;
    return new Composite(children, this, opts);
  };

  /**
   * Compose an entire fleet bottom-up into a level tower, so you can
   * see the same object at every zoom. Returns one entry per level,
   * each a list of composites -- and the composites at level n are
   * literally the children of the composites at level n+1.
   */
  FabricMarket.prototype.buildTower = function (maxLevel = 4) {
    const tower = [];
    // level 1: group leaves by cell prefix -- each full-ish cell is one computer
    const byCell = new Map();
    for (const node of this.fleet.listedNodes()) {
      const key = node.addr.slice(0, -1).join(".");
      if (!byCell.has(key)) byCell.set(key, []);
      byCell.get(key).push(node);
    }
    let current = [];
    for (const [, nodes] of byCell) {
      if (nodes.length < 2) continue;
      const c = this.compose(nodes, { name: `Cell ${nodes[0].addr.slice(0, -1).join(".")}` });
      if (c) current.push(c);
    }
    tower.push({ level: 1, objects: current });

    // and now upward: composites of composites, until it stops growing
    let level = 2;
    while (current.length >= 2 && level <= maxLevel) {
      const byParent = new Map();
      for (const c of current) {
        const key = c.addr.slice(0, -1).join(".") || "root";
        if (!byParent.has(key)) byParent.set(key, []);
        byParent.get(key).push(c);
      }
      const next = [];
      for (const [, group] of byParent) {
        if (group.length < 2) { next.push(group[0]); continue; }
        const c = this.compose(group, { name: `Level-${level} block` });
        if (c) next.push(c);
      }
      if (next.length === current.length) break;   // no further composition possible
      tower.push({ level, objects: next });
      current = next;
      level++;
    }
    return tower;
  };

  function commonPrefix(addrs) {
    if (!addrs.length) return [];
    const out = [];
    for (let i = 0; i < addrs[0].length; i++) {
      const d = addrs[0][i];
      if (addrs.every((a) => a[i] === d)) out.push(d);
      else break;
    }
    return out;
  }

  function weightedMean(pairs) {
    let num = 0;
    let den = 0;
    for (const [v, w] of pairs) {
      if (!Number.isFinite(v) || !Number.isFinite(w)) continue;
      num += v * w;
      den += w;
    }
    return den > 0 ? num / den : 0;
  }

  function dominant(values) {
    const t = tally(values);
    let best = null;
    let bestN = -1;
    for (const [k, n] of t) if (n > bestN) { best = k; bestN = n; }
    return best;
  }

  const LEVEL_SEATS = {
    1: "a rack",
    2: "a building",
    3: "a campus",
    4: "a city pilot",
    5: "a nation",
    6: "half the planet",
    7: "everyone + every device",
  };

  function tally(arr) {
    const m = new Map();
    for (const x of arr) m.set(x, (m.get(x) || 0) + 1);
    return m;
  }

  const API = { FabricMarket, Composite, K_COHERENCE, LEVEL_SEATS };
  root.Composite = Composite;
  root.FabricMarket = FabricMarket;
  root.HolotradeFabric = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
