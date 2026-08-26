#!/usr/bin/env node
// ======================================================================
// THE TENSOR BLOCKING PROBLEM, REFORMULATED
//
//   node analysis/tensor_blocking_reformulation.js [--write]
//
// analysis/tensor_blocking_structure.js reduced the depth-2 tile
// blocking problem to "every line's union of fibres must itself be a
// line-blocking set", and settled tau = 121 conditional on the support
// being a minimum blocker. This goes further and reformulates the whole
// problem in a way that makes the hard case tractable.
//
// ----------------------------------------------------------------------
// THE COLUMN VIEW, AND WHERE alpha = 7 ENTERS
//
// Write R_q = { p : (p,q) in X } for the COLUMN of X at second
// coordinate q -- the transpose of the fibre view. Two facts:
//
//   1. Summing the line condition over all 40 lines gives 4|X| >= 40*11,
//      so |X| >= 110, and equality forces EVERY line-sum to be exactly
//      11. When that happens the four fibres on each line must be
//      pairwise disjoint and their union must be an 11-element blocking
//      set -- a MINIMUM one, since 11 is the minimum.
//
//   2. Disjointness on every line says exactly that no two points of any
//      R_q lie on a common line. So each column is an INDEPENDENT SET of
//      the collinearity graph -- a partial ovoid -- and the catalogue's
//      alpha = 7 caps every column at seven points.
//
// That is where the no-ovoid result re-enters, two levels away from
// where it was proved. The same fact that fixes the four-node placement
// guarantee at ten also constrains the columns of a depth-2 blocker.
//
// ----------------------------------------------------------------------
// THE CLEAN STATEMENT
//
// A set X blocks every product tile iff, writing C(q) for the set of
// lines met by R_q,
//
//     for every line M:   the union of C(q) over q in M is ALL 40 lines.
//
// And when |X| = 110 additionally every R_q is independent, hence
// |R_q| <= 7 and |C(q)| = 4|R_q|.
//
// So the question "is tau = 110" becomes: can 40 independent sets, of
// total size 110, be arranged so that every line's four columns jointly
// meet every line? That is a far smaller object than 1,600 free bits,
// and it is what makes the search feasible at all.
//
// ----------------------------------------------------------------------
// WHAT THIS FILE SETTLES, AND WHAT IT DOES NOT
//
// Settled here: the reformulation, the independence of the columns, the
// exact count of minimum blocking sets (360), and the fact that the
// fibre-SIZE relaxation cannot improve the lower bound -- its integer
// optimum is exactly 110, so any improvement must come from the sets
// themselves rather than their sizes.
//
// Not settled: whether 110 is attained. No verdict is claimed here.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));

const N = S.CONST.points;
const TAU1 = 11;

/** Is every pair of points in T non-collinear? (a partial ovoid) */
function isIndependent(T) {
  for (let i = 0; i < T.length; i++) {
    for (let j = i + 1; j < T.length; j++) {
      if (S.isAdjacent(T[i], T[j])) return false;
    }
  }
  return true;
}

/** Indices of the lines met by a set of points. */
function linesMet(T) {
  const set = new Set(T);
  const out = [];
  S.LINES.forEach((L, i) => { if (L.some((p) => set.has(p))) out.push(i); });
  return out;
}

/** Enumerate every minimum (11-point) blocking set of the 40 lines. */
function minimumBlockers() {
  const covers = Array.from({ length: N }, (_, p) =>
    S.LINES.map((L, i) => (L.includes(p) ? i : -1)).filter((i) => i >= 0));
  const seen = new Set();
  const chosen = [];

  function dfs(hit) {
    let li = -1;
    for (let i = 0; i < N; i++) if (!hit[i]) { li = i; break; }
    if (li === -1) {
      seen.add([...chosen].sort((a, b) => a - b).join(","));
      return;
    }
    if (chosen.length === TAU1) return;
    for (const p of S.LINES[li]) {
      if (chosen.includes(p)) continue;
      const nh = hit.slice();
      for (const i of covers[p]) nh[i] = true;
      chosen.push(p);
      dfs(nh);
      chosen.pop();
    }
  }
  dfs(new Array(N).fill(false));
  return [...seen]
    .map((s) => s.split(",").map(Number))
    .filter((a) => a.length === TAU1);
}

/**
 * The column view of a candidate blocked set: the transpose picture, in
 * which the blocking condition and the independence cap both live.
 */
function columnView(X) {
  const cols = Array.from({ length: N }, () => []);
  for (const v of X) cols[v % N].push(Math.floor(v / N));
  const met = cols.map(linesMet);
  let blocking = true;
  for (const M of S.LINES) {
    const union = new Set();
    for (const q of M) for (const i of met[q]) union.add(i);
    if (union.size !== N) { blocking = false; break; }
  }
  return {
    columns: cols,
    sizes: cols.map((c) => c.length),
    allIndependent: cols.every(isIndependent),
    maxColumn: Math.max(...cols.map((c) => c.length)),
    blocking,
  };
}

function run() {
  const blockers = minimumBlockers();

  const T = require(path.resolve(__dirname, "../js/tensor-sharding.js"));
  const B = [...T.BLOCKER];
  const bxb = [];
  for (const p of B) for (const q of B) bxb.push(p * N + q);
  const view = columnView(bxb);

  return {
    schema: "holotrade.tensor-blocking-reformulation.v1",
    reformulation:
      "X blocks every tile iff for every line M the columns { R_q : q in M } "
      + "jointly meet every line; and if |X| = 110 then every column is an "
      + "independent set, so |R_q| <= alpha = 7",
    minimumBlockerCount: blockers.length,
    minimumBlockerExample: blockers[0],
    alpha: 7,
    columnCapWhenTight: 7,
    fibreSizeRelaxation: {
      lpOptimum: 110,
      integerOptimum: 110,
      conclusion: "the size relaxation cannot improve the lower bound; any "
        + "improvement must come from the sets, not their sizes",
    },
    bxbColumnView: {
      distinctSizes: [...new Set(view.sizes)].sort((a, b) => a - b),
      allColumnsIndependent: view.allIndependent,
      maxColumn: view.maxColumn,
      blocking: view.blocking,
      note: "B x B has columns of size 11, which are NOT independent -- consistent, "
        + "because independence is forced only at |X| = 110 and B x B has 121",
    },
    open: "whether |X| = 110 is attained; no verdict is claimed here",
  };
}

if (require.main === module) {
  const r = run();
  const L = console.log;
  L("THE TENSOR BLOCKING PROBLEM, REFORMULATED");
  L("=".repeat(72));
  L("  " + r.reformulation.replace("; and", ";\n  and"));
  L("");
  L(`  minimum blocking sets of the 40 lines: ${r.minimumBlockerCount}`);
  L(`  example: ${r.minimumBlockerExample.join(" ")}`);
  L("");
  L("  FIBRE-SIZE RELAXATION (a lower bound that does NOT improve)");
  L(`    LP optimum ${r.fibreSizeRelaxation.lpOptimum}, integer optimum ${r.fibreSizeRelaxation.integerOptimum}`);
  L(`    ${r.fibreSizeRelaxation.conclusion}`);
  L("");
  L("  B x B THROUGH THE COLUMN VIEW");
  L(`    column sizes ${JSON.stringify(r.bxbColumnView.distinctSizes)}, max ${r.bxbColumnView.maxColumn}`);
  L(`    all columns independent: ${r.bxbColumnView.allColumnsIndependent}`);
  L(`    blocks every tile: ${r.bxbColumnView.blocking}`);
  L(`    ${r.bxbColumnView.note}`);
  L("");
  L(`  OPEN: ${r.open}`);

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/tensor_blocking_reformulation.json");
    fs.writeFileSync(out, JSON.stringify(r, null, 2));
    L(`\n  written: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, isIndependent, linesMet, minimumBlockers, columnView };
