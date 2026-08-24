// ======================================================================
// HOLOTRADE SUBSTRATE
//
// The geometry the exchange is built on: W(3,3), the symplectic
// generalized quadrangle over F_3^4. Forty points, forty lines,
// automorphism group of order 51,840.
//
// Why a compute exchange cares:
//
//   1. ADDRESS IS ROUTE. Two nodes are adjacent iff the symplectic
//      inner product of their addresses vanishes mod 3. Forwarding is
//      one modular inner product -- no routing table, no BGP, no churn.
//      That makes *locality* a closed-form number, so the exchange can
//      price it per order instead of guessing at "same-AZ" heuristics.
//
//   2. DIAMETER 2. Any two of the 40 nodes in a cell are one hop apart
//      or share exactly mu = 4 common neighbours. Four-way multipath,
//      zero configuration. A buyer never pays for more than two hops
//      inside a cell.
//
//   3. FRACTAL CAPACITY. Replace each point with a whole copy and you
//      get H_n: 40^n leaves at routing diameter 8n. The whole planet
//      fits at n = 7 with a 56-hop worst case. Capacity and bisection
//      bandwidth are the same provisioned quantity, so the exchange
//      quotes ONE price rather than compute + network + egress.
//
//   4. THE MIGRATION PRICE LAW. Moving a workload to a neighbouring
//      node costs strictly LESS than reconfiguring it in place
//      (3 rays vs 6). That is not a heuristic -- it falls out of the
//      lit-set overlap spectrum of the 360 ground states. It is why
//      Holotrade's balancer prefers migration to re-vectoring.
//
// Scope note: the geometry, the group order, the bisection, the
// diameter law and the overlap spectrum are exact finite facts.
// The photonic hardware that would realise them at the quantum layer
// does not exist yet; Holotrade runs the classical (Clifford) layer,
// which is polynomial-time on any computer, and prices the quantum
// advantage separately as the 9^t magic dial.
// ======================================================================

(function (root) {
  "use strict";

  // ---- exact substrate integers -------------------------------------
  const CONST = {
    q: 3,                    // radix; the master equation q! = 2q forces it
    points: 40,              // |W(3,3)| points
    lines: 40,               // totally isotropic 2-spaces
    edges: 240,              // collinearity graph edges
    degree: 12,              // k
    lambda: 2,               // adjacent pairs share 2 common neighbours
    mu: 4,                   // non-adjacent pairs share 4 -> 4-way multipath
    autOrder: 51840,         // |Sp(4,3)| = |W(E6)|
    projOrder: 25920,        // |PSp(4,3)|
    bisection: 100,          // exact: (n/4)(k - lambda2) = (40/4)(12-2)
    lambda2: 2,              // second eigenvalue (Ramanujan bound 6.63)
    cssRate: 27 / 80,        // [[240,81,4,3]]_3 logical-qutrit rate cap
    contextualFraction: 0.1, // (40-36)/40 -- the Kochen-Specker budget
    coxeterE8: 30,           // h(E8); also #conj classes of Sp(4,3)
    tauO: 384,               // coherence-block denominator
    syndromeQutrits: 58,     // n-k for [[66,8,3]]_3: the irreversible step
    magicRobustness: 3,      // R = 3, so classical emulation costs 9^t
    hopsPerDigit: 8,         // reversible moves per recursive address digit
  };

  const K_BOLTZMANN = 1.380649e-23;
  const LN3 = Math.log(3);

  // ---- F_3 arithmetic ------------------------------------------------
  const mod3 = (x) => ((x % 3) + 3) % 3;

  /**
   * The canonical alternating form on F_3^4.
   *   <u,v> = u0*v1 - u1*v0 + u2*v3 - u3*v2  (mod 3)
   * Two points are collinear (adjacent) iff this vanishes.
   */
  function symplecticForm(u, v) {
    return mod3(u[0] * v[1] - u[1] * v[0] + u[2] * v[3] - u[3] * v[2]);
  }

  /**
   * Build the 40 projective points of PG(3,F_3). Every projective point
   * is isotropic for a symplectic form, which is why v = 40 and not fewer.
   * Normalised so the first nonzero coordinate is 1.
   */
  function buildPoints() {
    const seen = new Map();
    const points = [];
    for (let a = 0; a < 3; a++)
      for (let b = 0; b < 3; b++)
        for (let c = 0; c < 3; c++)
          for (let d = 0; d < 3; d++) {
            const v = [a, b, c, d];
            if (v.every((x) => x === 0)) continue;
            const lead = v.find((x) => x !== 0);
            const inv = lead === 1 ? 1 : 2; // 2*2 = 1 mod 3
            const norm = v.map((x) => mod3(x * inv));
            const key = norm.join("");
            if (seen.has(key)) continue;
            seen.set(key, points.length);
            points.push({ index: points.length, vec: norm, key });
          }
    return { points, index: seen };
  }

  const { points: POINTS, index: POINT_INDEX } = buildPoints();

  // ---- adjacency -----------------------------------------------------
  const ADJ = POINTS.map((p) =>
    POINTS.filter((r) => r.index !== p.index && symplecticForm(p.vec, r.vec) === 0).map(
      (r) => r.index
    )
  );

  const ADJ_SET = ADJ.map((row) => new Set(row));

  function isAdjacent(a, b) {
    return a !== b && ADJ_SET[a].has(b);
  }

  /** The mu = 4 internally disjoint two-hop relays between non-adjacent points. */
  function commonNeighbours(a, b) {
    return ADJ[a].filter((x) => ADJ_SET[b].has(x));
  }

  /**
   * Route inside one cell. Address is route: no table is consulted.
   * Returns the hop list and every equal-cost alternative.
   */
  function route(a, b) {
    if (a === b) return { hops: [a], distance: 0, alternates: [] };
    if (isAdjacent(a, b)) return { hops: [a, b], distance: 1, alternates: [] };
    const relays = commonNeighbours(a, b);
    return {
      hops: [a, relays[0], b],
      distance: 2,
      alternates: relays.slice(1).map((r) => [a, r, b]),
    };
  }

  // ---- the 40 totally isotropic lines (measurement contexts) ---------
  function buildLines() {
    const lines = new Set();
    for (let i = 0; i < 40; i++) {
      for (const j of ADJ[i]) {
        // the line through i and j is the set of points collinear with both,
        // plus i and j themselves; on W(3,3) it has exactly 4 points.
        const tail = ADJ[i].filter((x) => x !== j && ADJ_SET[j].has(x) && isLineClosed(i, j, x));
        if (tail.length !== 2) continue;
        const pts = [i, j, ...tail].sort((m, n) => m - n);
        lines.add(pts.join(","));
      }
    }
    return [...lines].map((s) => s.split(",").map(Number));
  }

  function isLineClosed(i, j, x) {
    // x is on the line ij iff x is collinear with both and the triple is
    // pairwise collinear inside a totally isotropic 2-space.
    return ADJ_SET[i].has(x) && ADJ_SET[j].has(x);
  }

  const LINES = buildLines();

  // ---- fractal addressing: H_n --------------------------------------
  //
  // A level-n address is n digits in base 40. Level 1 is one rack of 40.
  // Level 4 is a city-scale pilot (2.56M cores). Level 7 seats every
  // person and every device on Earth at 56 hops worst case.

  function levelFor(nodeCount) {
    if (nodeCount <= 1) return 1;
    return Math.max(1, Math.ceil(Math.log(nodeCount) / Math.log(40)));
  }

  function capacityAtLevel(n) {
    return Math.pow(40, n);
  }

  function diameterAtLevel(n) {
    return CONST.hopsPerDigit * n;
  }

  function parseAddress(str) {
    return String(str)
      .split(".")
      .map((d) => parseInt(d, 10))
      .filter((d) => Number.isFinite(d) && d >= 0 && d < 40);
  }

  function formatAddress(digits) {
    return digits.map((d) => String(d).padStart(2, "0")).join(".");
  }

  /**
   * Hop distance between two fractal addresses. Digits agree down to the
   * first divergence; below that you pay the in-cell route plus 8 hops
   * per remaining digit on each side.
   */
  function fabricDistance(addrA, addrB) {
    const a = Array.isArray(addrA) ? addrA : parseAddress(addrA);
    const b = Array.isArray(addrB) ? addrB : parseAddress(addrB);
    let i = 0;
    while (i < a.length && i < b.length && a[i] === b[i]) i++;
    if (i === a.length && i === b.length) return { hops: 0, sharedPrefix: i, inCell: 0 };
    const da = a[i];
    const db = b[i];
    const inCell = da === undefined || db === undefined ? 1 : route(da, db).distance;
    const depthBelow = Math.max(a.length - i - 1, 0) + Math.max(b.length - i - 1, 0);
    return {
      hops: inCell + depthBelow * CONST.hopsPerDigit,
      sharedPrefix: i,
      inCell,
    };
  }

  // ---- the migration price law ---------------------------------------
  //
  // Overlap of the lit sets of the 360 ground states, classified by the
  // relation between their defect centres:
  //
  //   same centre        overlap always 5   ->  re-vector in place = 6 rays
  //   collinear centres  overlaps {0,2,3,8} ->  cheapest migration  = 3 rays
  //   non-collinear      overlaps {1,2,4,6} ->  cheapest migration  = 5 rays
  //
  // Every ground state has exactly 8 cheap channels, two at each of the
  // four collinear centres written into its own vector. So a workload's
  // escape routes are part of its address, and moving to a NEIGHBOUR is
  // strictly cheaper than reconfiguring where it already sits.

  const RAY_COST = { inPlace: 6, adjacent: 3, nonAdjacent: 5 };

  function migrationRays(fromPoint, toPoint) {
    if (fromPoint === toPoint) return RAY_COST.inPlace;
    if (isAdjacent(fromPoint, toPoint)) return RAY_COST.adjacent;
    return RAY_COST.nonAdjacent;
  }

  /**
   * Full migration cost between two fabric addresses, in rays.
   * The page side is relocation-isotropic (the memory bill is always
   * exactly 9 points), so the ray side alone decides -- edges win.
   */
  function migrationCost(addrA, addrB) {
    const a = Array.isArray(addrA) ? addrA : parseAddress(addrA);
    const b = Array.isArray(addrB) ? addrB : parseAddress(addrB);
    const d = fabricDistance(a, b);
    let i = 0;
    while (i < a.length && i < b.length && a[i] === b[i]) i++;
    const base =
      i >= a.length || i >= b.length ? RAY_COST.inPlace : migrationRays(a[i], b[i]);
    const depthPenalty = Math.max(0, d.sharedPrefix === 0 ? a.length - 1 : 0) * 2;
    // The channel label describes the WHOLE move, not just its first
    // digit. A move whose leading digits are adjacent but which then
    // descends through several address levels is not a cheap channel,
    // however cheap its first hop looked.
    const rays = base + depthPenalty;
    let channel;
    if (i >= a.length || i >= b.length) channel = "in-place";
    else if (rays === RAY_COST.adjacent && d.hops <= 1) channel = "cheap";
    else if (d.hops <= 2) channel = "in-cell";
    else channel = "far";
    return {
      rays,
      hops: d.hops,
      channel,
      pageBill: 9, // constant 18/27 safe-zone overlap either way
    };
  }

  // ---- the magic dial -------------------------------------------------
  //
  // The Clifford layer is the stabilizer formalism: polynomial time on
  // any classical machine (Gottesman-Knill). That is routing, memory,
  // fault tolerance -- everything structural, and it is FREE.
  // Quantum advantage is the priced dial: each non-Clifford (cubic E6)
  // gate multiplies the classical emulation cost by R^2 = 9.

  function magicMultiplier(t) {
    return Math.pow(CONST.magicRobustness * CONST.magicRobustness, Math.max(0, t || 0));
  }

  /** Below this t, a classical node can emulate the job; above it, only real hardware. */
  function classicalFeasibleT(budgetOps) {
    return Math.floor(Math.log(Math.max(1, budgetOps)) / Math.log(9));
  }

  // ---- thermodynamics -------------------------------------------------
  //
  // The Clifford datapath is unitary, hence reversible and Landauer-free.
  // The one irreversible step is syndrome extraction: 58 qutrits per
  // cycle at kT ln 3 each. At 300 K that is 2.6e-19 J/cycle.
  // Real devices dissipate orders more -- this is the floor a node's
  // efficiency is scored AGAINST, not a claim about any node's draw.

  function landauerFloorPerCycle(kelvin) {
    return CONST.syndromeQutrits * K_BOLTZMANN * (kelvin || 300) * LN3;
  }

  function landauerFloorWatts(kelvin, hz) {
    return landauerFloorPerCycle(kelvin) * (hz || 1e9);
  }

  /**
   * How many orders of magnitude above the thermodynamic floor a node
   * actually runs. Today's accelerators sit 6-7 orders up. This is the
   * single most honest efficiency number a datacentre can publish,
   * because the denominator is a law rather than a vendor benchmark.
   */
  function thermodynamicDecades(joulesPerOp, kelvin) {
    const floor = landauerFloorPerCycle(kelvin || 300);
    if (!(joulesPerOp > 0)) return 0;
    return Math.log10(joulesPerOp / floor);
  }

  // ---- receipts / attestation ----------------------------------------
  //
  // Contextuality is tamper-evidence: a KS budget of 36/40 means any
  // intervention that classicalises the statistics MOVES AN INTEGER.
  // A receipt carries the measured contextual fraction; 0.10 is clean,
  // 0 means the channel was classicalised somewhere.

  function attestationVerdict(measuredFraction) {
    const target = CONST.contextualFraction;
    const delta = Math.abs(measuredFraction - target);
    if (delta <= 0.012) return { ok: true, label: "ATTESTED", detail: "contextual fraction on target" };
    if (measuredFraction < 0.05)
      return { ok: false, label: "CLASSICALISED", detail: "channel lost its KS witness" };
    return { ok: false, label: "DRIFT", detail: "contextual fraction off target" };
  }

  // ---- deterministic hashing (stable ids, stable demo data) ----------
  function hash32(str) {
    let h = 2166136261 >>> 0;
    const s = String(str);
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619) >>> 0;
    }
    return h >>> 0;
  }

  /** Seeded PRNG (mulberry32) so every run of the demo is reproducible. */
  function rng(seed) {
    let a = typeof seed === "string" ? hash32(seed) : seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const Substrate = {
    CONST,
    POINTS,
    POINT_INDEX,
    LINES,
    ADJ,
    mod3,
    symplecticForm,
    isAdjacent,
    commonNeighbours,
    route,
    levelFor,
    capacityAtLevel,
    diameterAtLevel,
    parseAddress,
    formatAddress,
    fabricDistance,
    RAY_COST,
    migrationRays,
    migrationCost,
    magicMultiplier,
    classicalFeasibleT,
    landauerFloorPerCycle,
    landauerFloorWatts,
    thermodynamicDecades,
    attestationVerdict,
    hash32,
    rng,
  };

  root.Substrate = Substrate;
  if (typeof module !== "undefined" && module.exports) module.exports = Substrate;
})(typeof window !== "undefined" ? window : globalThis);
