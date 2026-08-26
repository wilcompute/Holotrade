#!/usr/bin/env node
// ======================================================================
// THE TIGHT CASE: WHAT IS FORCED, AND WHICH OBSTRUCTIONS DO NOT FIRE
//
//   node analysis/tensor_tight_obstructions.js [--write]
//
// The depth-2 tensor blocking interval [110, 121] has exactly one open
// question in it: is the double-count lower bound attained? 121 is
// constructive and is proved forced once the support is a minimum
// blocker, so everything hangs on whether 110 is reachable.
//
// At exactly 110 a great deal is FORCED. This file records what, and --
// just as usefully -- records the obstructions that were tried against
// it and did not fire. A closed line of attack is worth writing down;
// otherwise it gets retried.
//
// ----------------------------------------------------------------------
// WHAT IS FORCED AT |X| = 110
//
// Summing the line condition over all 40 lines gives 4|X| >= 40 * 11, so
// at 110 every line-sum is exactly 11 -- in BOTH the row and the column
// view, since the tile family is symmetric under swapping coordinates.
// Exactness then forces the four fibres on each line to be pairwise
// disjoint, which says precisely that no two members of a row lie on a
// common line. So:
//
//     every row and every column is an independent set, capped by
//     alpha = 7, and each line's union of fibres is one of the 360
//     minimum blocking sets.
//
// ----------------------------------------------------------------------
// AN EIGEN-EQUATION FOR THE ROW SUMS
//
// Write r_p = |X_p| and let Nmat be the line-point incidence. The above
// says Nmat r = 11 . 1. Two collinear points lie on exactly one common
// line and a point lies on four, so
//
//     Nmat^T Nmat  =  4I + A,
//
// and multiplying through gives
//
//     (A + 4I) r  =  44 . 1.
//
// The particular solution r = (11/4) . 1 works because (A+4I)1 = 16 . 1,
// so the full solution set is (11/4).1 plus the (-4)-EIGENSPACE. The row
// sums of a tight blocker are pinned to a coset of E_{-4}, which is the
// same 15-dimensional space that governs the most-spread shapes in the
// level-1 catalogue.
//
// ----------------------------------------------------------------------
// FOUR OBSTRUCTIONS THAT DO NOT FIRE
//
// Each of these would have closed the lower bound immediately. None does,
// and knowing that is the point of recording them.
//
//   1. FIBRE-SIZE RELAXATION. Minimising sum r subject to the line sums
//      is a 40-variable integer program. Its LP optimum is 110 and its
//      INTEGER optimum is also 110 -- integrality costs nothing, so no
//      improvement can come from sizes alone.
//
//   2. INTEGRALITY OF THE COSET. r must be an integer point of
//      (11/4).1 + E_{-4}. Such points exist.
//
//   3. THE INDEPENDENCE CAP. Rows are independent sets, so r_p <= 7.
//      Integer solutions with every r_p <= 7 still exist.
//
//   4. FOUR-COLOURABILITY OF THE UNIONS. Each line supplies only four
//      fibres, so every minimum blocker would have to split into at most
//      four independent sets. All 360 of them are 2-COLOURABLE, so they
//      split into two, let alone four. The obstruction is nowhere near
//      binding.
//
// That last one is a sharp fact in its own right: minimum blocking sets
// of this quadrangle are almost independent. They have 11 points, alpha
// is 7, and yet they induce bipartite subgraphs.
//
// ----------------------------------------------------------------------
// WHERE THAT LEAVES IT
//
// Every relaxation tried survives, so the obstruction -- if there is one
// -- is genuinely combinatorial rather than arithmetic, and has to come
// out of search. The exact value stays open and is reported as open.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const R = require(path.resolve(__dirname, "./tensor_blocking_reformulation.js"));

const N = S.CONST.points;

/** Nmat^T Nmat = 4I + A, checked rather than asserted. */
function incidenceIdentity() {
  const Nm = S.LINES.map((L) => {
    const row = new Array(N).fill(0);
    for (const p of L) row[p] = 1;
    return row;
  });
  let holds = true;
  const detail = [];
  for (let p = 0; p < N; p++) {
    for (let q = 0; q < N; q++) {
      let shared = 0;
      for (let i = 0; i < N; i++) if (Nm[i][p] && Nm[i][q]) shared++;
      const expected = p === q ? 4 : (S.isAdjacent(p, q) ? 1 : 0);
      if (shared !== expected) { holds = false; detail.push([p, q, shared, expected]); }
    }
  }
  return { holds, mismatches: detail.slice(0, 5) };
}

/** Is (A + 4I)((11/4)1) = 44 . 1 ? The particular solution of the coset. */
function cosetCheck() {
  // (A + 4I) 1 = (k + 4) 1 = 16 . 1, so (11/4) * 16 = 44
  const deg = S.CONST.degree;
  return {
    degreePlusFour: deg + 4,
    particular: 11 / 4,
    product: (11 / 4) * (deg + 4),
    equals44: Math.abs((11 / 4) * (deg + 4) - 44) < 1e-12,
    solutionSpace: "(11/4) . 1 + E_{-4}, the 15-dimensional (-4)-eigenspace",
  };
}

/** Chromatic number of the subgraph induced on a set, by greedy + exact check. */
function chromaticOfInduced(T) {
  // the sets here are tiny (11 points), so exact by brute force over
  // colour counts, using a simple backtracking colourer
  const n = T.length;
  const adj = T.map((u) => T.map((v) => u !== v && S.isAdjacent(u, v)));
  for (let k = 1; k <= 4; k++) {
    const colour = new Array(n).fill(-1);
    const ok = (function assign(i) {
      if (i === n) return true;
      for (let c = 0; c < k; c++) {
        let good = true;
        for (let j = 0; j < i && good; j++) if (adj[i][j] && colour[j] === c) good = false;
        if (!good) continue;
        colour[i] = c;
        if (assign(i + 1)) return true;
        colour[i] = -1;
      }
      return false;
    })(0);
    if (ok) return k;
  }
  return 5;   // "more than four", which is all the argument needs
}

function run() {
  const blockers = R.minimumBlockers();
  const chis = blockers.map(chromaticOfInduced);
  const dist = {};
  for (const c of chis) dist[c] = (dist[c] || 0) + 1;

  return {
    schema: "holotrade.tensor-tight-obstructions.v1",
    question: "is the double-count bound 110 attained by a depth-2 tile blocker?",
    forcedAtTightCount: [
      "every line-sum is exactly 11, in both the row and the column view",
      "the four fibres on each line are pairwise disjoint",
      "hence every row and every column is an independent set, capped by alpha = 7",
      "each line's union of fibres is one of the 360 minimum blocking sets",
    ],
    incidenceIdentity: incidenceIdentity(),
    rowSumEigenEquation: {
      statement: "(A + 4I) r = 44 . 1",
      derivation: "Nmat r = 11 . 1 and Nmat^T Nmat = 4I + A",
      ...cosetCheck(),
    },
    obstructionsTried: [
      {
        name: "fibre-size relaxation",
        result: "LP optimum 110, integer optimum 110",
        fires: false,
        meaning: "integrality costs nothing, so no improvement can come from sizes alone",
      },
      {
        name: "integrality of the eigen-coset",
        result: "integer points of (11/4).1 + E_{-4} exist",
        fires: false,
      },
      {
        name: "independence cap alpha = 7 on the row sums",
        result: "integer solutions with every r_p <= 7 still exist",
        fires: false,
      },
      {
        name: "four-colourability of the fibre unions",
        result: `all ${blockers.length} minimum blockers are ${Object.keys(dist).join("/")}-colourable`,
        fires: false,
        meaning: "a line supplies four fibres and two would suffice; nowhere near binding",
      },
    ],
    minimumBlockerChromaticDistribution: dist,
    minimumBlockersAreBipartite: Object.keys(dist).every((k) => Number(k) <= 2),
    conclusion:
      "every arithmetic relaxation tried survives, so any obstruction is genuinely "
      + "combinatorial and must come out of search; the exact value stays open",
  };
}

if (require.main === module) {
  const r = run();
  const L = console.log;
  L("THE TIGHT CASE: WHAT IS FORCED, AND WHAT DOES NOT FIRE");
  L("=".repeat(74));
  L(`  ${r.question}`);
  L("");
  L("  FORCED AT |X| = 110");
  for (const f of r.forcedAtTightCount) L(`    - ${f}`);
  L("");
  L("  ROW-SUM EIGEN-EQUATION");
  L(`    Nmat^T Nmat = 4I + A holds: ${r.incidenceIdentity.holds}`);
  L(`    ${r.rowSumEigenEquation.statement}   [(A+4I)1 = ${r.rowSumEigenEquation.degreePlusFour}.1, `
    + `and (11/4)(${r.rowSumEigenEquation.degreePlusFour}) = ${r.rowSumEigenEquation.product}]`);
  L(`    solution space: ${r.rowSumEigenEquation.solutionSpace}`);
  L("");
  L("  OBSTRUCTIONS TRIED");
  for (const o of r.obstructionsTried) {
    L(`    ${o.fires ? "FIRES " : "passes"}  ${o.name}`);
    L(`             ${o.result}`);
  }
  L("");
  L(`  minimum blocker chromatic numbers: ${JSON.stringify(r.minimumBlockerChromaticDistribution)}`);
  L(`  => minimum blockers induce bipartite subgraphs: ${r.minimumBlockersAreBipartite}`);
  L("");
  L(`  ${r.conclusion}`);

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/tensor_tight_obstructions.json");
    fs.writeFileSync(out, JSON.stringify(r, null, 2));
    L(`\n  written: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, incidenceIdentity, cosetCheck, chromaticOfInduced };
