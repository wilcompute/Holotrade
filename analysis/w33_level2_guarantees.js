#!/usr/bin/env node
// ======================================================================
// LEVEL-2 PLACEMENT GUARANTEES — and the robustness collapse
//
//   node analysis/w33_level2_guarantees.js [--write]
//
// ----------------------------------------------------------------------
// THE GAP THIS CLOSES
//
// The lift theorem gives provably densest reservations at level 2, and
// scheduler/w33-shapes.js exposes them. But its `note` field admits the
// guarantee was never computed there: "the level-1 guarantee applies per
// cell; a level-2 worst case over 1,600 leaves has not been computed".
//
// It can be computed, exactly, and the answer is worth knowing before
// anyone ships a 160-node reservation.
//
// ----------------------------------------------------------------------
// THE PRODUCT THEOREM
//
// By Sabidussi-Vizing the automorphism group of a square of a connected
// prime graph is Aut(W) wr S_2: elements act as (c,p) -> (g(c), h(p)),
// plus the swap (c,p) -> (p,c). Applying those to a by-points lift
//
//     L_P(T1) = { (c,p) : every cell c, p in T1 }
//
// gives (g,h) . L_P(T1) = L_P(h(T1)), and the swap gives L_C(h(T1)), the
// by-cells lift. So the orbit is exactly
//
//     { L_P(T1') : T1' in orbit_1 }  union  { L_C(T1') : T1' in orbit_1 }.
//
// Now let X be a set of blocked leaves, and write
//
//     P(X) = { p : (c,p) in X for some c }      the point shadow
//     C(X) = { c : (c,p) in X for some p }      the cell shadow.
//
// X meets L_P(T1') exactly when P(X) meets T1', and X meets L_C(T1')
// exactly when C(X) meets T1'. So X blocks every placement iff BOTH
// shadows are level-1 blocking sets, giving
//
//     |X| >= |P(X)| >= tau_1.
//
// And that is attained: take a level-1 blocking set B and put X on the
// diagonal, X = { (b,b) : b in B }. Both shadows equal B. Hence
//
//     tau_2 = tau_1  EXACTLY.
//
// ----------------------------------------------------------------------
// WHY THAT IS BAD NEWS, STATED PLAINLY
//
// The reservation grew by a factor of 40 -- 4 leaves to 160 -- and the
// fabric grew by 40 as well, from 40 leaves to 1,600. The number of
// simultaneous failures it survives did not grow at all. It is still 10.
//
// So the FRACTION of the fabric that can be lost collapses:
//
//     level 1:  10 of    40  =  25%
//     level 2:  10 of 1,600  =  0.625%
//
// A lifted shape spans every cell, so it presents a target in every cell,
// and eleven well-chosen leaves out of sixteen hundred defeat it. The
// lift buys optimality and pays for it in fault tolerance, and nothing in
// the spectral argument warns you about that -- it is invisible unless
// you ask the blocking question separately.
//
// This is the kind of result that only shows up if you refuse to
// extrapolate: the level-1 guarantee of 10 is numerically correct at
// level 2 and operationally means something completely different.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const L2 = require(path.resolve(__dirname, "./w33_level2.js"));
const L2S = require(path.resolve(__dirname, "./w33_level2_shapes.js"));
const shapes = require(path.resolve(__dirname, "../scheduler/w33-shapes.js"));
const guarantees = require(path.resolve(__dirname, "./w33_shape_guarantees.js"));

const N1 = S.CONST.points;
const N2 = N1 * N1;

/**
 * The level-2 orbit of a lift, as a pair of families rather than an
 * explicit list: materialising 1,600-element sets 80 times over is
 * wasteful when the generating rule is what the argument uses.
 */
function liftOrbitFamilies(T1) {
  const orbit1 = shapes.shapeOrbit(T1);
  return { orbit1, byPoints: orbit1, byCells: orbit1, size: 2 * orbit1.length };
}

/** Does X, as a set of leaves, meet every placement of the lift? */
function blocksAllLifts(X, orbit1) {
  const P = new Set(), C = new Set();
  for (const v of X) { P.add(L2.pointOf(v)); C.add(L2.cellOf(v)); }
  const hits = (shadow) => orbit1.every((T) => T.some((p) => shadow.has(p)));
  return hits(P) && hits(C);
}

/** Verify the product theorem constructively at a given level-1 size. */
function verifyAt(m1) {
  const T1 = shapes.optimalShape(m1).witness;
  const orbit1 = shapes.shapeOrbit(T1);

  // level-1 blocking number, recomputed here rather than looked up
  const hs = guarantees.minimumHittingSet(orbit1, N1, { msBudget: 30000 });
  const tau1 = hs.exhausted ? hs.tau : null;

  const out = {
    level1Size: m1,
    level2Size: m1 * N1,
    orbit1Size: orbit1.length,
    level2OrbitSize: 2 * orbit1.length,
    tau1,
    tau1Exhaustive: hs.exhausted,
  };
  if (tau1 === null) {
    out.note = "level-1 blocking search did not close in budget";
    return out;
  }

  // upper bound: the diagonal construction
  const B = hs.witness;
  const diagonal = B.map((b) => L2.idx(b, b));
  out.diagonalBlocks = blocksAllLifts(diagonal, orbit1);
  out.diagonalSize = diagonal.length;

  // lower bound: any blocking set's point shadow must itself block
  // level 1, so nothing smaller than tau1 can work. Checked by sampling
  // sets of size tau1 - 1 and confirming none blocks.
  const rand = S.rng("l2-lower-" + m1);
  let counterexample = null;
  for (let t = 0; t < 3000 && !counterexample; t++) {
    const X = new Set();
    while (X.size < tau1 - 1) X.add(Math.floor(rand() * N2));
    if (blocksAllLifts([...X], orbit1)) counterexample = [...X];
  }
  out.noSmallerBlockerFound = counterexample === null;
  out.tau2 = out.diagonalBlocks && out.noSmallerBlockerFound ? tau1 : null;
  out.guarantee2 = out.tau2 !== null ? out.tau2 - 1 : null;

  // the collapse, stated as fractions
  if (out.guarantee2 !== null) {
    out.fractionLevel1 = (tau1 - 1) / N1;
    out.fractionLevel2 = (out.guarantee2) / N2;
    out.fractionRatio = out.fractionLevel1 / out.fractionLevel2;
  }
  return out;
}

/**
 * The alternative the collapse implies: confine a reservation to a few
 * cells instead of spreading it over all of them.
 *
 * A shape held inside k cells presents no target in the other 40 - k, so
 * an adversary must spend blocked leaves inside the cells actually used.
 * This measures the trade directly: how many busy leaves defeat a
 * reservation of the same total size, as a function of how many cells it
 * is spread across.
 */
function confinementTradeoff(totalLeaves = 160) {
  const adj = L2.buildCartesian();
  const rows = [];
  for (const cells of [1, 2, 4, 5, 8, 10, 20, 40]) {
    if (totalLeaves % cells !== 0) continue;
    const perCell = totalLeaves / cells;
    if (perCell > N1) continue;
    // use an optimal level-1 shape inside each cell where one exists
    const usable = perCell % 4 === 0 && perCell <= 36;
    const T1 = usable ? shapes.optimalShape(perCell).witness : null;

    // WHICH cells matters as much as how many. An earlier version took
    // the first k cell indices, which are mutually non-adjacent, so the
    // inter-cell links contributed nothing and confinement looked
    // strictly worse than lifting. Choosing an OPTIMAL set of cells --
    // a densest level-1 shape, where one exists at that count -- adds
    // back every inter-cell link the geometry allows.
    const cellShape = (cells % 4 === 0 && cells <= 36)
      ? shapes.optimalShape(cells).witness : null;
    const chosenCells = cellShape ? cellShape.slice() : [];
    for (let c = 0; c < N1 && chosenCells.length < cells; c++) {
      if (!chosenCells.includes(c)) chosenCells.push(c);
    }

    const T = [];
    for (const c of chosenCells) {
      const pts = T1 || [...Array(perCell).keys()];
      for (const p of pts) T.push(L2.idx(c, p));
    }
    const e = L2S.inducedEdges(adj, T);
    const bound = L2S.level2UpperBound(T.length);
    rows.push({
      cellsUsed: cells,
      leavesPerCell: perCell,
      totalLeaves: T.length,
      optimalPerCell: usable,
      inducedEdges: e,
      level2Bound: bound,
      efficiency: e / bound,
      // an adversary must block inside the cells in use
      cellsAreOptimalShape: cellShape !== null,
      cellsFreeForOtherTenants: N1 - cells,
      note: cells === N1 ? "by-points lift: a target in every cell"
        : (cellShape && (perCell === N1)) ? "by-cells lift: optimal AND confined"
        : usable ? "optimal per cell" : "no optimal shape at this per-cell size",
    });
  }
  return rows;
}

function run() {
  const perSize = [];
  for (const m1 of [4, 8, 16]) perSize.push(verifyAt(m1));

  const result = {
    schema: "holotrade.w33-level2-guarantees.v1",
    theorem: "tau_2 = tau_1 exactly: a blocking set's point and cell shadows must each "
      + "block at level 1, and the diagonal construction attains it",
    consequence: "a lifted reservation survives the same absolute number of failures as its "
      + "level-1 seed, so the surviveable FRACTION of the fabric collapses by the cell size",
    perSize,
    confinementTradeoff: confinementTradeoff(160),
  };
  result.theoremHolds = perSize.every((r) => r.tau2 === r.tau1);
  result.digest = crypto.createHash("sha256").update(JSON.stringify(perSize)).digest("hex");
  return result;
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  L("LEVEL-2 PLACEMENT GUARANTEES");
  L("=".repeat(78));
  L("  theorem: tau_2 = tau_1, because a blocking set's point shadow and cell shadow");
  L("           must each be a level-1 blocking set, and the diagonal attains it");
  L("");
  L("  m1   m2    orbit_1   tau_1   diagonal blocks   none smaller   tau_2   guarantee");
  for (const r of res.perSize) {
    L(`  ${String(r.level1Size).padStart(2)}  ${String(r.level2Size).padStart(4)}   `
      + `${String(r.orbit1Size).padStart(7)}   ${String(r.tau1).padStart(5)}   `
      + `${String(r.diagonalBlocks).padStart(15)}   ${String(r.noSmallerBlockerFound).padStart(12)}   `
      + `${String(r.tau2).padStart(5)}   ${String(r.guarantee2).padStart(9)}`);
  }
  L("");
  L("  THE COLLAPSE");
  L("   m1    survivable fraction, level 1   ->   level 2      ratio");
  for (const r of res.perSize) {
    if (r.fractionLevel1 == null) continue;
    L(`  ${String(r.level1Size).padStart(3)}    ${(r.fractionLevel1 * 100).toFixed(2).padStart(24)}%   ->   `
      + `${(r.fractionLevel2 * 100).toFixed(3)}%      ${r.fractionRatio.toFixed(0)}x worse`);
  }
  L("");
  L("  THE TRADE: confine the reservation instead of lifting it (160 leaves)");
  L("   cells   per cell   e(T)     bound   efficiency   cells free   note");
  for (const t of res.confinementTradeoff) {
    L(`  ${String(t.cellsUsed).padStart(6)}   ${String(t.leavesPerCell).padStart(8)}   `
      + `${String(t.inducedEdges).padStart(4)}   ${String(t.level2Bound).padStart(7)}   `
      + `${(t.efficiency * 100).toFixed(1).padStart(9)}%   ${String(t.cellsFreeForOtherTenants).padStart(10)}   ${t.note}`);
  }

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/w33_level2_guarantees.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, verifyAt, blocksAllLifts, liftOrbitFamilies, confinementTradeoff };
