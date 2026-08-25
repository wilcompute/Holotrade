#!/usr/bin/env node
// ======================================================================
// W(3,3) PERFECT RESERVATION PACKINGS
//
//   node analysis/w33_shape_packing.js [--write]
//
// ----------------------------------------------------------------------
// THE QUESTION
//
// The catalogue says which sizes admit a densest shape, and the blocking
// analysis says how many nodes may be busy before one stops being
// placeable. Neither answers the question a scheduler asks when it is
// filling an empty cell:
//
//     can the fabric be TILED by optimal shapes, leaving nothing over?
//
// A tiling is the fragmentation-free schedule. Every node is used, every
// reservation is provably densest, and no node is stranded between two
// jobs. If such a tiling exists at size m, then scheduling in units of m
// is not merely efficient on average -- it is exactly lossless.
//
// ----------------------------------------------------------------------
// WHICH SIZES COULD POSSIBLY TILE
//
// Two constraints, both arithmetic:
//
//   * a densest shape needs 4 | m   (from the catalogue)
//   * a tiling needs m | 40         (the pieces must exhaust the points)
//
// So m in {4, 8, 20, 40}. Everything else is ruled out before any search
// runs, and 40 is the trivial whole-cell case. That leaves three
// questions, and they have three different answers:
//
//   m = 20  FORCED. The complement of a densest shape is a densest shape
//           -- proved in the catalogue -- so any 20-shape and its
//           complement tile the cell automatically. No search needed.
//
//   m = 4   These are exactly the 40 lines, so a tiling is a set of 10
//           pairwise disjoint lines covering every point once. That is a
//           SPREAD of the generalized quadrangle, a classical object.
//           The substrate corpus reports 36 of them; counted here
//           independently rather than cited.
//
//   m = 8   Genuinely open going in. Searched below.
//
// ----------------------------------------------------------------------
// WHY THIS IS THE USEFUL FORM OF THE RESULT
//
// "Reserve in multiples of four and the cell tiles perfectly, 36
// different ways" is an admission policy. "The spectral bound is
// m(m+8)/8" is not.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const shapes = require(path.resolve(__dirname, "../scheduler/w33-shapes.js"));
const cat = require(path.resolve(__dirname, "./w33_shape_catalogue.js"));

const N = S.CONST.points;

// ---------------------------------------------------------------------
// The candidate pool must be EVERY densest shape of the size, not one
// orbit of them.
//
// An earlier version of this file searched inside the orbit of a single
// catalogue witness, and it produced a wrong answer loudly enough to be
// caught: it reported no tiling at m = 20, which directly contradicts
// the catalogue's proved complementation theorem (the complement of a
// densest shape is a densest shape, so any 20-shape tiles the cell with
// its own complement). The orbit of that witness has 3,240 members while
// there are 33,264 densest 20-sets in total, so the complement simply
// was not in the pool being searched.
//
// The lesson generalises: orbit != isomorphism class here. Only m = 4
// has a single orbit, which is why that case looked right.
// ---------------------------------------------------------------------
const _poolCache = new Map();
function allDensestShapes(m) {
  if (_poolCache.has(m)) return _poolCache.get(m);
  const r = cat.searchIntriguing(m, 2 + m / 4, m / 4, { collect: 100000 });
  const pool = (r.allWitnesses || []).map((w) => [...w].sort((a, b) => a - b));
  _poolCache.set(m, pool);
  return pool;
}

// ---------------------------------------------------------------------
// exact-cover search: tile the 40 points with disjoint copies from a
// pool of candidate shapes
// ---------------------------------------------------------------------
function findTilings(pool, { wanted = Infinity, countAll = true } = {}) {
  const need = N;
  const size = pool.length ? pool[0].length : 0;
  if (!size || need % size !== 0) return { tilings: [], count: 0, feasible: false };
  const pieces = need / size;

  // index candidates by their lowest-numbered point, so the search
  // always covers the smallest uncovered point next: that fixes the
  // ordering and makes each tiling be found exactly once
  const byLowest = Array.from({ length: N }, () => []);
  for (const c of pool) byLowest[Math.min(...c)].push(c);

  const covered = new Uint8Array(N);
  const chosen = [];
  const found = [];
  let count = 0;

  function firstUncovered() {
    for (let v = 0; v < N; v++) if (!covered[v]) return v;
    return -1;
  }

  function recurse() {
    const v = firstUncovered();
    if (v === -1) {
      count++;
      if (found.length < wanted) found.push(chosen.map((c) => [...c]));
      return found.length >= wanted && !countAll;
    }
    for (const c of byLowest[v]) {
      if (c.some((x) => covered[x])) continue;
      for (const x of c) covered[x] = 1;
      chosen.push(c);
      const stop = recurse();
      chosen.pop();
      for (const x of c) covered[x] = 0;
      if (stop) return true;
    }
    return false;
  }

  recurse();
  return { tilings: found, count, feasible: count > 0, pieces };
}

/** Largest set of pairwise disjoint shapes, when a full tiling is impossible. */
function maxDisjointPacking(pool) {
  let best = 0, bestSet = null;
  const covered = new Uint8Array(N);
  const chosen = [];

  function recurse(startIdx) {
    if (chosen.length > best) { best = chosen.length; bestSet = chosen.map((c) => [...c]); }
    for (let i = startIdx; i < pool.length; i++) {
      const c = pool[i];
      if (c.some((x) => covered[x])) continue;
      // bound: even taking every remaining point cannot beat the incumbent
      let free = 0;
      for (let v = 0; v < N; v++) if (!covered[v]) free++;
      if (chosen.length + Math.floor(free / c.length) <= best) return;
      for (const x of c) covered[x] = 1;
      chosen.push(c);
      recurse(i + 1);
      chosen.pop();
      for (const x of c) covered[x] = 0;
    }
  }
  recurse(0);
  return { size: best, packing: bestSet };
}

// ---------------------------------------------------------------------
function analyse(m) {
  const shape = shapes.optimalShape(m);
  if (!shape.ok) return { m, attainable: false, reason: shape.reason };

  const orbit = shapes.shapeOrbit(shape.witness);
  const pool = allDensestShapes(m);
  const divides = N % m === 0;
  const row = {
    m,
    attainable: true,
    orbitSize: orbit.length,
    totalShapes: pool.length,
    orbitsInPool: pool.length / orbit.length,
    dividesFabric: divides,
    piecesNeeded: divides ? N / m : null,
  };

  if (!divides) {
    // no tiling possible; report the best partial packing instead
    const pack = maxDisjointPacking(pool);
    row.tilingPossible = false;
    row.reason = `${m} does not divide ${N}; a tiling cannot exist`;
    row.maxDisjoint = pack.size;
    row.pointsCovered = pack.size * m;
    row.pointsStranded = N - pack.size * m;
    row.packingWitness = pack.packing;
    return row;
  }

  const t = findTilings(pool, { wanted: 3 });
  row.tilingPossible = t.feasible;
  row.tilingCount = t.count;
  row.exampleTilings = t.tilings;
  if (t.feasible) {
    row.pointsCovered = N;
    row.pointsStranded = 0;
  } else {
    const pack = maxDisjointPacking(pool);
    row.maxDisjoint = pack.size;
    row.pointsCovered = pack.size * m;
    row.pointsStranded = N - pack.size * m;
    row.packingWitness = pack.packing;
  }
  return row;
}

function verifyTiling(tiling, m) {
  const seen = new Set();
  for (const piece of tiling) {
    if (piece.length !== m) return { ok: false, why: "wrong piece size" };
    if (shapes.inducedEdges(piece) !== (m * (m + 8)) / 8) {
      return { ok: false, why: "a piece is not a densest shape" };
    }
    for (const v of piece) {
      if (seen.has(v)) return { ok: false, why: "pieces overlap" };
      seen.add(v);
    }
  }
  if (seen.size !== N) return { ok: false, why: `covers ${seen.size} of ${N} points` };
  return { ok: true };
}

function run() {
  const rows = [];
  for (let m = 4; m <= 36; m += 4) rows.push(analyse(m));

  // spreads deserve their own verification: a tiling by lines
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const spreadSearch = findTilings(lines, { wanted: 2 });
  const spreads = {
    definition: "10 pairwise disjoint lines covering every point exactly once",
    count: spreadSearch.count,
    example: spreadSearch.tilings[0] || null,
    everyPointOnce: spreadSearch.tilings[0]
      ? new Set(spreadSearch.tilings[0].flat()).size === N : null,
    // each spread meets every point-star exactly once, which is the
    // property the substrate corpus uses for its scheduler clock
    oneLinePerPointStar: null,
  };
  if (spreadSearch.tilings[0]) {
    let ok = true;
    for (let v = 0; v < N && ok; v++) {
      const through = spreadSearch.tilings[0].filter((l) => l.includes(v)).length;
      if (through !== 1) ok = false;
    }
    spreads.oneLinePerPointStar = ok;
  }

  const verifications = rows
    .filter((r) => r.exampleTilings && r.exampleTilings.length)
    .map((r) => ({ m: r.m, ...verifyTiling(r.exampleTilings[0], r.m) }));

  const result = {
    schema: "holotrade.w33-shape-packing.v1",
    question: "can the fabric be tiled by optimal shapes, leaving nothing stranded?",
    arithmeticFilter: "a tiling needs 4 | m (densest shape exists) and m | 40 (pieces exhaust the cell)",
    candidateSizes: [4, 8, 20, 40],
    shapes: rows,
    spreads,
    verifications,
  };
  result.digest = crypto.createHash("sha256")
    .update(JSON.stringify({ rows, spreads })).digest("hex");
  return result;
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  L("W(3,3) PERFECT RESERVATION PACKINGS");
  L("=".repeat(76));
  L("  a tiling needs 4 | m (a densest shape exists) and m | 40 (the pieces exhaust");
  L("  the cell), so only m = 4, 8, 20, 40 are even candidates");
  L("");
  L("   m   orbit    total   divides 40   tilings   stranded   note");
  for (const r of res.shapes) {
    const tl = r.tilingPossible === true ? String(r.tilingCount)
      : r.tilingPossible === false ? "none" : "-";
    const note = r.tilingPossible ? "PERFECT TILING"
      : `max ${r.maxDisjoint} disjoint`;
    L(`  ${String(r.m).padStart(2)}  ${String(r.orbitSize).padStart(6)}  ${String(r.totalShapes).padStart(7)}   ${String(r.dividesFabric).padStart(10)}   `
      + `${tl.padStart(7)}   ${String(r.pointsStranded).padStart(8)}   ${note}`);
  }
  L("");
  L("SPREADS  (the m=4 tilings, i.e. 10 disjoint lines)");
  L(`  count                       ${res.spreads.count}`);
  L(`  covers every point once     ${res.spreads.everyPointOnce}`);
  L(`  one line per point-star     ${res.spreads.oneLinePerPointStar}`);
  if (res.spreads.example) {
    L(`  example                     ${res.spreads.example.map((l) => l.join("")).join(" ")}`);
  }
  L("");
  L("TILING VERIFICATION  (every piece a densest shape, disjoint, covering all 40)");
  for (const v of res.verifications) {
    L(`  m=${String(v.m).padStart(2)}: ${v.ok ? "verified" : "FAILED — " + v.why}`);
  }

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/w33_shape_packing.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, findTilings, maxDisjointPacking, verifyTiling };
