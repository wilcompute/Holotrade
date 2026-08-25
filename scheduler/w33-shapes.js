// ======================================================================
// W(3,3) OPTIMAL SHAPE RESERVATION
//
// The scheduler-facing half of analysis/w33_shape_catalogue.js.
//
// That analysis proves which set sizes admit a shape attaining the
// spectral bounds, and produces one witness for each. This module turns
// those witnesses into something a scheduler can actually call:
//
//   optimalShape(m, kind)      the exact shape for a requested size, or
//                              an honest "nearest attainable" with the gap
//   reserveShape(m, opts)      transport a shape onto currently free
//                              nodes, or refuse with a reason
//   maxAntiAffinity()          the hard ceiling on failure-independent
//                              placement (7, not the ratio bound's 10)
//   placementCapacity(m)       how busy the fabric can get before an
//                              optimal shape stops being placeable
//
// ----------------------------------------------------------------------
// WHY TRANSPORT IS THE WHOLE TRICK
//
// A catalogue witness lives at fixed point indices. In a live fabric
// those points are usually busy, so a catalogue on its own is a wall
// poster. The automorphism group PSp(4,3) acts transitively on the 40
// points, so a shape can be MOVED, and because an automorphism preserves
// adjacency it preserves induced-edge count and boundary exactly. The
// optimality is carried along for free -- that is not an approximation,
// it is what "automorphism" means.
//
// Orbits are computed lazily by breadth-first closure from the symplectic
// transvections rather than by materialising all 25,920 group elements.
// The largest shape orbit here is 6,480, so the BFS is a few hundred
// thousand set operations: cheap enough to run in a browser tab, which
// enumerating the group is not.
//
// ----------------------------------------------------------------------
// WHAT THIS DOES NOT DO
//
// It reserves POINTS OF THE LEVEL-1 GRAPH. It does not do link-state
// routing, congestion control, failure recovery, or multi-cell placement
// across an address hierarchy. Those are separate and unbuilt.
// ======================================================================

"use strict";

const S = (typeof require !== "undefined")
  ? require("../js/substrate.js")
  : (typeof window !== "undefined" ? window.Substrate : null);

const N = S.CONST.points;
const K = S.CONST.degree;

// ---------------------------------------------------------------------
// generators: symplectic transvections T_{v,a}(x) = x + a<x,v>v
// ---------------------------------------------------------------------
const mod3 = (x) => ((x % 3) + 3) % 3;

function normalise(v) {
  if (v.every((x) => x === 0)) return null;
  const lead = v.find((x) => x !== 0);
  const inv = lead === 1 ? 1 : 2;
  return v.map((x) => mod3(x * inv));
}

const VECS = S.POINTS.map((p) => p.vec);
const KEY = new Map(VECS.map((v, i) => [v.join(""), i]));

function buildGenerators() {
  const gens = [];
  for (let vi = 0; vi < N; vi++) {
    const v = VECS[vi];
    for (const a of [1, 2]) {
      const perm = new Int8Array(N);
      let ok = true;
      for (let i = 0; i < N && ok; i++) {
        const x = VECS[i];
        const c = mod3(a * S.symplecticForm(x, v));
        const img = normalise(x.map((xi, k) => mod3(xi + c * v[k])));
        const j = img === null ? -1 : KEY.get(img.join(""));
        if (j === undefined || j < 0) ok = false; else perm[i] = j;
      }
      if (ok) gens.push(perm);
    }
  }
  return gens;
}

let _GENS = null;
function generators() {
  if (!_GENS) _GENS = buildGenerators();
  return _GENS;
}

// ---------------------------------------------------------------------
// the frozen catalogue, embedded so the browser needs no fetch
//
// Sizes and witnesses come from analysis/w33_shape_catalogue.js, which
// searched the whole space exhaustively. They are reproduced here rather
// than re-derived at load: the search is a few seconds, a page load is
// not. `npm run verify:shapes` re-derives and checks they still match.
// ---------------------------------------------------------------------
const CATALOGUE = Object.freeze({
  // Witnesses from analysis/w33_shape_catalogue.js, which searched the
  // whole space exhaustively. Embedded rather than re-derived at load:
  // the search takes seconds, a page load does not. `npm run verify:shapes`
  // re-runs the search and checks these are still the right shapes.
  tight: Object.freeze({
    4: [0, 4, 5, 6],
    8: [0, 1, 2, 3, 4, 13, 22, 31],
    12: [0, 1, 2, 3, 4, 5, 13, 19, 22, 29, 31, 39],
    16: [0, 1, 2, 3, 4, 5, 6, 13, 16, 19, 22, 26, 30, 31, 36, 38],
    20: [0, 1, 2, 3, 4, 5, 6, 7, 13, 14, 16, 19, 22, 26, 27, 29, 31, 35, 38, 39],
    24: [0, 1, 2, 3, 4, 5, 6, 7, 8, 13, 14, 16, 17, 19, 22, 26, 27, 29, 30, 31, 32, 36, 37, 38],
    28: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 16, 17, 19, 20, 22, 23, 25, 27, 29, 30, 31, 32, 35, 36, 37, 39],
    32: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 18, 19, 21, 22, 23, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 38, 39],
    36: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39],
  }),
  spread: Object.freeze({
    20: [0, 1, 2, 3, 5, 7, 8, 9, 15, 16, 17, 20, 24, 26, 27, 28, 33, 34, 36, 39],
  }),
  extremes: Object.freeze({
    independenceNumber: 7,
    independenceWitness: [0, 1, 2, 9, 18, 27, 36],
    independenceHoffmanBound: 10,
    independenceBoundAttained: false,
    cliqueNumber: 4,
    cliqueWitness: [0, 4, 5, 6],
  }),
});

let _frozen = null;
function frozenCatalogue() {
  if (_frozen !== null) return _frozen;
  _frozen = { tight: {}, spread: {} };
  try {
    if (typeof require !== "undefined") {
      const path = require("node:path");
      const fs = require("node:fs");
      const p = path.resolve(__dirname, "../data/w33_shape_catalogue.json");
      if (fs.existsSync(p)) {
        const c = JSON.parse(fs.readFileSync(p, "utf8"));
        for (const r of c.tightSets) if (r.witness) _frozen.tight[r.m] = r.witness;
        for (const r of c.mOvoids) if (r.witness) _frozen.spread[r.m] = r.witness;
        _frozen.extremes = c.extremes;
      }
    }
  } catch (e) { /* fall back to the embedded line below */ }
  // Browser, or a checkout without the frozen artifact: fall back to the
  // embedded witnesses, which cover every attainable size.
  for (const [m, w] of Object.entries(CATALOGUE.tight)) {
    if (!_frozen.tight[m]) _frozen.tight[m] = w.slice();
  }
  for (const [m, w] of Object.entries(CATALOGUE.spread)) {
    if (!_frozen.spread[m]) _frozen.spread[m] = w.slice();
  }
  if (!_frozen.extremes) _frozen.extremes = CATALOGUE.extremes;
  return _frozen;
}

// ---------------------------------------------------------------------
// shape geometry
// ---------------------------------------------------------------------
function inducedEdges(T) {
  const set = new Set(T);
  let e = 0;
  for (const v of T) for (const u of S.ADJ[v]) if (set.has(u) && u > v) e++;
  return e;
}
function edgeBoundary(T) {
  const set = new Set(T);
  let b = 0;
  for (const v of T) for (const u of S.ADJ[v]) if (!set.has(u)) b++;
  return b;
}
function profile(T) {
  const set = new Set(T);
  const inside = new Set(), outside = new Set();
  for (let v = 0; v < N; v++) {
    const c = S.ADJ[v].filter((u) => set.has(u)).length;
    (set.has(v) ? inside : outside).add(c);
  }
  return { inside: [...inside].sort((a, b) => a - b), outside: [...outside].sort((a, b) => a - b) };
}

/** The spectral optimum for a set of this size. */
function bounds(m) {
  return {
    maxInducedEdges: (m * (m + 8)) / 8,
    minInducedEdges: Math.max(0, (m * (m - 10)) / 5),
    minBoundary: (m * (N - m)) / 4,
    maxBoundary: (2 * m * (N - m)) / 5,
    densestAttainable: m % 4 === 0,
    spreadAttainable: m === 20,
  };
}

// ---------------------------------------------------------------------
// orbit under the group, by BFS from the generators
// ---------------------------------------------------------------------
const _orbitCache = new Map();

function shapeOrbit(shape, { cap = 20000 } = {}) {
  const key = [...shape].sort((a, b) => a - b).join(",");
  if (_orbitCache.has(key)) return _orbitCache.get(key);

  const gens = generators();
  const seen = new Set([key]);
  let frontier = [[...shape].sort((a, b) => a - b)];
  while (frontier.length) {
    const next = [];
    for (const s of frontier) {
      for (const g of gens) {
        const img = s.map((v) => g[v]).sort((a, b) => a - b);
        const k = img.join(",");
        if (!seen.has(k)) {
          seen.add(k);
          next.push(img);
          if (seen.size > cap) throw new Error("shape orbit exceeded cap");
        }
      }
    }
    frontier = next;
  }
  const orbit = [...seen].map((s) => s.split(",").map(Number));
  _orbitCache.set(key, orbit);
  return orbit;
}

// ---------------------------------------------------------------------
// Proved worst-case placement guarantees.
//
// tau is the minimum number of blocked points that defeats EVERY
// placement of the shape -- the minimum blocking set of its orbit. So
// with tau - 1 nodes busy a placement always exists, WHICHEVER nodes
// they are. This is a worst-case guarantee, not the sampled average
// that placementCapacity() reports.
//
// Computed twice and independently: by branch and bound in
// analysis/w33_shape_guarantees.js, and by SAT in
// analysis/w33_blocking_sat.py, where every value below tau is
// discharged as UNSAT. The two agree on every shape.
//
// The m=4 row is the one worth reading twice. Each point lies on 4
// lines, so hitting all 40 needs at least 10 points, and equality would
// require an ovoid -- which this quadrangle does not have. That is why
// tau is 11 and not 10, and why a four-node reservation survives any ten
// simultaneous failures.
// ---------------------------------------------------------------------
const GUARANTEES = Object.freeze({
  densest: Object.freeze({
    4: { tau: 11, guarantee: 10, countingBound: 10 },
    8: { tau: 8, guarantee: 7, countingBound: 5 },
    12: { tau: 8, guarantee: 7, countingBound: 4 },
    16: { tau: 6, guarantee: 5, countingBound: 3 },
    20: { tau: 6, guarantee: 5, countingBound: 2 },
    24: { tau: 4, guarantee: 3, countingBound: 2 },
    28: { tau: 4, guarantee: 3, countingBound: 2 },
    32: { tau: 3, guarantee: 2, countingBound: 2 },
    36: { tau: 2, guarantee: 1, countingBound: 2 },
  }),
  spread: Object.freeze({
    20: { tau: 3, guarantee: 2, countingBound: 2 },
  }),
});

/**
 * The worst-case guarantee for a shape size: how many nodes may be busy
 * with a placement still certain, regardless of which ones.
 */
function guaranteeFor(m, kind = "densest") {
  const table = kind === "spread" ? GUARANTEES.spread : GUARANTEES.densest;
  const row = table[m];
  if (!row) return null;
  return {
    m, kind,
    busyTolerated: row.guarantee,
    blockingNumber: row.tau,
    countingLowerBound: row.countingBound,
    countingBoundTight: row.tau === row.countingBound,
    method: "minimum blocking set of the shape orbit; proved by SAT and by branch and bound",
  };
}

// ---------------------------------------------------------------------
// LEVEL 2: multi-cell reservations
//
// Everything above reserves points inside ONE 40-point cell. A server
// fleet is not one cell, so the backend question is whether any of it
// survives a level up -- or whether a multi-cell reservation needs a
// fresh search over 1,600 vertices.
//
// It survives. On the Cartesian fabric W [] W (24-regular, spectrum
// {24,14,8,4,-2,-8}) the densest-shape bound is
//
//     e(T) <= 7m + m^2/320,   equality iff f lies in the 14-eigenspace,
//
// and if f1 sits in the 2-eigenspace at level 1 then both 1 (x) f1 and
// f1 (x) 1 sit in the 14-eigenspace at level 2, because 12 + 2 = 2 + 12.
// So a level-1 optimal shape lifts two ways:
//
//   byPoints   hold the same point positions in EVERY cell
//   byCells    hold EVERY point inside a set of optimal cells
//
// Both give a provably densest level-2 reservation of 40*m1 nodes,
// assembled from a catalogue that already exists. Verified in
// analysis/w33_level2_shapes.js: all 18 lifts attain the bound exactly.
//
// The available level-2 sizes are therefore 160, 320, ..., 1440 -- the
// level-1 ladder scaled by the cell size, and nothing between them.
// ---------------------------------------------------------------------

const LEVEL2 = Object.freeze({
  leaves: N * N,
  degree: 2 * K,
  spectrum: Object.freeze({ 24: 1, 14: 48, 8: 30, 4: 576, "-2": 720, "-8": 225 }),
  lambda2: 14,
  lambdaMin: -8,
});

/** e(T) <= 7m + m^2/320 on the level-2 Cartesian fabric. */
function level2Bound(m) {
  return {
    maxInducedEdges: 7 * m + (m * m) / 320,
    minInducedEdges: Math.max(0, -4 * m + (m * m) / 100),
    degree: LEVEL2.degree,
    leaves: LEVEL2.leaves,
  };
}

/**
 * The densest level-2 reservation of a requested size.
 *
 * Only multiples of 40*4 = 160 are attainable, because a lift scales a
 * level-1 shape by the cell size and level-1 needs 4 | m1. Anything else
 * is refused with the nearest attainable size, exactly as at level 1 --
 * a scheduler that quietly rounds is worse than one that says what it
 * cannot do.
 */
function optimalShapeLevel2(m, { lift = "byPoints" } = {}) {
  const bound = level2Bound(m);
  if (m % N !== 0) {
    const nearest = Math.max(N * 4, Math.round(m / N) * N);
    return {
      ok: false, m, level: 2,
      reason: `a level-2 lift holds ${N} leaves per level-1 point, so ${N} must divide m`,
      nearestAttainable: nearest, bounds: bound,
    };
  }
  const m1 = m / N;
  const base = optimalShape(m1);
  if (!base.ok) {
    return {
      ok: false, m, level: 2,
      reason: `no level-1 densest shape at m1 = ${m1}: ${base.reason}`,
      nearestAttainable: base.nearestAttainable ? base.nearestAttainable * N : null,
      bounds: bound,
    };
  }
  return {
    ok: true, m, level: 2, lift,
    level1Size: m1,
    level1Witness: base.witness,
    // the level-2 set is described rather than materialised: 1,600
    // indices is a lot to hand back when the generating rule is two
    // lines long and the caller usually wants the rule
    describe: lift === "byCells"
      ? `every point of the ${m1} cells ${base.witness.join(",")}`
      : `points ${base.witness.join(",")} in every one of the ${N} cells`,
    inducedEdges: bound.maxInducedEdges,
    attainsBound: true,
    bounds: bound,
    guarantee: guaranteeFor(m1),
    note: "the level-1 guarantee applies per cell; a level-2 worst case over "
      + "1,600 leaves has not been computed",
  };
}

/** Materialise a level-2 lift as explicit leaf indices (cell*40 + point). */
function materialiseLevel2(spec) {
  if (!spec || !spec.ok) return null;
  const out = [];
  if (spec.lift === "byCells") {
    for (const c of spec.level1Witness) for (let p = 0; p < N; p++) out.push(c * N + p);
  } else {
    for (let c = 0; c < N; c++) for (const p of spec.level1Witness) out.push(c * N + p);
  }
  return out.sort((a, b) => a - b);
}

/** The sizes a level-2 reservation can actually take. */
function level2Ladder() {
  const rows = [];
  for (let m1 = 4; m1 <= 36; m1 += 4) {
    const m = m1 * N;
    rows.push({
      level1Size: m1,
      level2Size: m,
      maxInducedEdges: level2Bound(m).maxInducedEdges,
      lifts: ["byPoints", "byCells"],
    });
  }
  return rows;
}

// ---------------------------------------------------------------------
// public API
// ---------------------------------------------------------------------

/**
 * The optimal shape of a requested size.
 *
 * `kind` is "densest" (maximum internal links, for one tightly coupled
 * job) or "spread" (every outside node sees the same number of members,
 * for anti-affinity).
 *
 * When the requested size admits no attaining shape, this REPORTS THAT
 * and names the nearest size that does, rather than silently returning
 * something suboptimal. A scheduler that quietly downgrades is worse
 * than one that says what it cannot do.
 */
function optimalShape(m, kind = "densest") {
  const cat = frozenCatalogue();
  const table = kind === "spread" ? cat.spread : cat.tight;
  const b = bounds(m);

  if (table[m]) {
    const witness = table[m];
    return {
      ok: true, m, kind, witness,
      inducedEdges: inducedEdges(witness),
      boundary: edgeBoundary(witness),
      profile: profile(witness),
      attainsBound: true,
      bounds: b,
    };
  }

  const available = Object.keys(table).map(Number).filter((k) => table[k]).sort((a, b2) => a - b2);
  if (!available.length) return { ok: false, m, kind, reason: "no catalogue available" };
  const nearest = available.reduce((best, k) =>
    Math.abs(k - m) < Math.abs(best - m) ? k : best, available[0]);

  return {
    ok: false,
    m, kind,
    reason: kind === "spread"
      ? `a perfectly spread set exists only at m = ${available.join(", ")}; ${m} is not attainable`
      : `the densest-shape bound needs 4 | m; ${m} is not attainable`,
    nearestAttainable: nearest,
    gap: Math.abs(nearest - m),
    bounds: b,
  };
}

/**
 * Reserve an optimal shape on the currently free part of the fabric.
 *
 * Walks the shape's orbit for an image landing entirely on free nodes.
 * Returns the placement with its exact metrics, or a refusal naming the
 * reason -- never a best-effort subset, because a shape that has lost a
 * point is no longer the shape whose optimality was proved.
 */
function reserveShape(m, { kind = "densest", unavailable = [], wanted = 1 } = {}) {
  const shape = optimalShape(m, kind);
  if (!shape.ok) return { ok: false, ...shape };

  const blocked = unavailable instanceof Set ? unavailable : new Set(unavailable);
  const free = N - blocked.size;
  if (free < m) {
    return {
      ok: false, m, kind,
      reason: `only ${free} free nodes; a ${m}-point shape cannot fit at all`,
      freeNodes: free,
    };
  }

  const orbit = shapeOrbit(shape.witness);
  const placements = [];
  for (const img of orbit) {
    if (img.every((v) => !blocked.has(v))) {
      placements.push(img);
      if (placements.length >= wanted) break;
    }
  }

  if (!placements.length) {
    return {
      ok: false, m, kind,
      reason: `${free} nodes are free but none of the ${orbit.length} placements of this shape fits among them`,
      freeNodes: free,
      orbitSize: orbit.length,
      hint: "the shape is rigid; fall back to a smaller optimal shape or accept a non-optimal set",
    };
  }

  const chosen = placements[0];
  return {
    ok: true, m, kind,
    placement: chosen,
    alternatives: placements.slice(1),
    orbitSize: orbit.length,
    inducedEdges: inducedEdges(chosen),
    boundary: edgeBoundary(chosen),
    profile: profile(chosen),
    // an automorphism preserves both exactly, so these must match the
    // catalogue witness; asserted rather than assumed
    preservesOptimality:
      inducedEdges(chosen) === shape.inducedEdges &&
      edgeBoundary(chosen) === shape.boundary,
    bounds: shape.bounds,
  };
}

/**
 * The hard ceiling on failure-independent placement.
 *
 * The Hoffman ratio bound suggests 10, and a 10-set attaining it would
 * be an ovoid of this generalized quadrangle. Exhaustive search shows
 * none exists: the true maximum is 7. A scheduler must not promise an
 * eighth replica with no shared link, because there is no such
 * placement -- at any price, on any fabric of this shape.
 */
function maxAntiAffinity() {
  const cat = frozenCatalogue();
  if (cat.extremes) {
    return {
      size: cat.extremes.independenceNumber,
      witness: cat.extremes.independenceWitness,
      ratioBound: cat.extremes.independenceHoffmanBound,
      boundAttained: cat.extremes.independenceBoundAttained,
      note: "the ratio bound of 10 is NOT attained; this quadrangle has no ovoid",
    };
  }
  return { size: 7, witness: null, ratioBound: 10, boundAttained: false };
}

/**
 * How busy the fabric can get before an optimal shape of this size stops
 * being placeable. Sampled, and honestly labelled as such -- the exact
 * answer would need every subset of blocked nodes.
 *
 * Worth reading carefully: orbit size does NOT predict this. The m=12
 * shape has an orbit of 1,080 images and tolerates fewer busy nodes than
 * the m=8 shape, whose orbit is only 45, because size dominates.
 */
function placementCapacity(m, { kind = "densest", trials = 200, seed = "capacity" } = {}) {
  const shape = optimalShape(m, kind);
  if (!shape.ok) return { ok: false, reason: shape.reason };
  const orbit = shapeOrbit(shape.witness);
  const rand = S.rng(seed + ":" + m);

  const rows = [];
  let tolerated = 0;
  for (let busy = 0; busy <= N - m; busy += 2) {
    let placed = 0;
    for (let t = 0; t < trials; t++) {
      const blocked = new Set();
      while (blocked.size < busy) blocked.add(Math.floor(rand() * N));
      if (orbit.some((img) => img.every((v) => !blocked.has(v)))) placed++;
    }
    const rate = placed / trials;
    rows.push({ busyNodes: busy, freeNodes: N - busy, placementRate: rate });
    if (rate === 1) tolerated = busy;
  }
  return {
    ok: true, m, kind,
    orbitSize: orbit.length,
    alwaysPlaceableUpTo: tolerated,
    curve: rows,
    method: `sampled over ${trials} random blocked sets per level, not exhaustive`,
  };
}

/** Everything a scheduler UI needs for one size, in one call. */
function shapeMenu({ unavailable = [] } = {}) {
  const blocked = unavailable instanceof Set ? unavailable : new Set(unavailable);
  const rows = [];
  for (let m = 4; m <= 36; m += 4) {
    const r = reserveShape(m, { unavailable: blocked });
    const b = bounds(m);
    rows.push({
      m,
      densestAttainable: true,
      maxInducedEdges: b.maxInducedEdges,
      minBoundary: b.minBoundary,
      placeable: r.ok,
      placement: r.ok ? r.placement : null,
      reason: r.ok ? null : r.reason,
      orbitSize: r.orbitSize ?? null,
      guarantee: guaranteeFor(m),
    });
  }
  const spread = reserveShape(20, { kind: "spread", unavailable: blocked });
  return {
    densest: rows,
    spread: {
      onlySize: 20,
      placeable: spread.ok,
      placement: spread.ok ? spread.placement : null,
      reason: spread.ok ? null : spread.reason,
    },
    antiAffinity: maxAntiAffinity(),
    freeNodes: N - blocked.size,
  };
}

const API = {
  N, K,
  generators, shapeOrbit,
  bounds, inducedEdges, edgeBoundary, profile,
  optimalShape, reserveShape, maxAntiAffinity, placementCapacity, shapeMenu,
  guaranteeFor, GUARANTEES,
  LEVEL2, level2Bound, optimalShapeLevel2, materialiseLevel2, level2Ladder,
  frozenCatalogue,
};

if (typeof module !== "undefined" && module.exports) module.exports = API;
if (typeof window !== "undefined") window.HolotradeShapes = API;
