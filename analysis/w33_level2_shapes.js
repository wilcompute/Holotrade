#!/usr/bin/env node
// ======================================================================
// DO OPTIMAL RESERVATION SHAPES SURVIVE ONE LEVEL UP?
//
//   node analysis/w33_level2_shapes.js [--write]
//
// ----------------------------------------------------------------------
// THE QUESTION
//
// The shape catalogue is entirely level-1: densest reservations inside
// one 40-point cell. A server fleet is not one cell. So the question a
// backend actually has to answer is whether any of it survives:
//
//     is there a densest shape at level 2, and if so, does the level-1
//     catalogue produce it, or does the whole search have to be redone
//     on 1,600 vertices?
//
// It survives, and the proof is short enough to state here.
//
// ----------------------------------------------------------------------
// THE BOUND AT LEVEL 2
//
// The Cartesian fabric W [] W is 24-regular on 1,600 leaves with spectrum
// {24, 14, 8, 4, -2, -8} (verified numerically in w33_level2_check.py).
// The same argument as level 1 -- write f for the component of the
// indicator orthogonal to all-ones, bound f^T A f by the extreme
// eigenvalues off the all-ones direction -- gives
//
//     e(T)  <=  7m + m^2/320          (equality iff f lies in E_14)
//     e(T)  >=  -4m + m^2/100         (equality iff f lies in E_-8)
//
// ----------------------------------------------------------------------
// THE LIFT THEOREM
//
// Let T1 be a densest shape at level 1, so f1 = 1_{T1} - (m1/40)1 lies in
// the 2-eigenspace of A1. Lift it by REPLICATING IT IN EVERY CELL:
//
//     T = { (c,p) : p in T1, any cell c },     m = 40*m1
//
// Its indicator is 1 (x) 1_{T1}, so f = 1 (x) f1, and
//
//     (A1 (x) I + I (x) A1)(1 (x) f1)
//         = (A1 1) (x) f1  +  1 (x) (A1 f1)
//         = 12 (1 (x) f1)  +  2 (1 (x) f1)
//         = 14 (1 (x) f1).
//
// So f lands exactly in E_14 -- the eigenspace equality requires -- and T
// is a densest shape at level 2. The level-1 catalogue lifts.
//
// The dual lift works identically. Take a densest set of CELLS and use
// every point inside them:
//
//     T = { (c,p) : c in C1, any point p },    f = f1 (x) 1,
//
// which gives 2 + 12 = 14 the same way. Both directions land in the same
// eigenspace, from opposite factors.
//
// ----------------------------------------------------------------------
// WHY A BACKEND CARES
//
// It means a multi-cell reservation does not need a new search over
// 1,600 vertices, and it does not need a heuristic. "The same optimal
// 4-shape in every cell" is a provably densest 160-node reservation, and
// it is assembled from a catalogue that already exists.
//
// Everything below verifies the theorem rather than assuming it: both
// lifts are constructed explicitly and their induced edge counts are
// compared with the bound.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const L2 = require(path.resolve(__dirname, "./w33_level2.js"));
const shapes = require(path.resolve(__dirname, "../scheduler/w33-shapes.js"));

const N1 = S.CONST.points;
const N2 = N1 * N1;

/** e(T) <= 7m + m^2/320 for the 24-regular Cartesian fabric. */
function level2UpperBound(m) {
  return 7 * m + (m * m) / 320;
}
function level2LowerBound(m) {
  return Math.max(0, -4 * m + (m * m) / 100);
}

function inducedEdges(adj, T) {
  const set = new Set(T);
  let e = 0;
  for (const v of T) for (const w of adj[v]) if (set.has(w) && w > v) e++;
  return e;
}
function edgeBoundary(adj, T) {
  const set = new Set(T);
  let b = 0;
  for (const v of T) for (const w of adj[v]) if (!set.has(w)) b++;
  return b;
}

/**
 * Neighbourhood profile at level 2. A densest shape must show exactly two
 * values: one inside, one outside. Any spread means it is not an
 * intriguing set and the equality has not been attained.
 */
function profile(adj, T) {
  const set = new Set(T);
  const inside = new Set(), outside = new Set();
  for (let v = 0; v < N2; v++) {
    let c = 0;
    for (const w of adj[v]) if (set.has(w)) c++;
    (set.has(v) ? inside : outside).add(c);
  }
  return {
    inside: [...inside].sort((a, b) => a - b),
    outside: [...outside].sort((a, b) => a - b),
    isIntriguing: inside.size === 1 && outside.size === 1,
  };
}

/** Same points in every cell. */
function liftByPoints(T1) {
  const T = [];
  for (let c = 0; c < N1; c++) for (const p of T1) T.push(L2.idx(c, p));
  return T.sort((a, b) => a - b);
}

/** Every point in the selected cells. */
function liftByCells(C1) {
  const T = [];
  for (const c of C1) for (let p = 0; p < N1; p++) T.push(L2.idx(c, p));
  return T.sort((a, b) => a - b);
}

function run() {
  const adj = L2.buildCartesian();
  const rows = [];

  for (let m1 = 4; m1 <= 36; m1 += 4) {
    const shape = shapes.optimalShape(m1);
    if (!shape.ok) continue;
    const T1 = shape.witness;
    const e1 = shapes.inducedEdges(T1);

    for (const [kind, T] of [["by-points", liftByPoints(T1)], ["by-cells", liftByCells(T1)]]) {
      const m = T.length;
      const e = inducedEdges(adj, T);
      const b = edgeBoundary(adj, T);
      const bound = level2UpperBound(m);
      const prof = profile(adj, T);

      // the arithmetic prediction: replicating a shape in every cell
      // gives 40 copies of its internal edges, plus a copy of the whole
      // cell graph at each held position
      const predicted = kind === "by-points"
        ? N1 * e1 + T1.length * (N1 * S.CONST.degree / 2)
        : T1.length * (N1 * S.CONST.degree / 2) + N1 * e1;

      rows.push({
        level1Size: m1, lift: kind, level2Size: m,
        level1InducedEdges: e1,
        inducedEdges: e,
        predictedInducedEdges: predicted,
        predictionHolds: e === predicted,
        boundary: b,
        upperBound: bound,
        attainsBound: Math.abs(e - bound) < 1e-9,
        profile: prof,
        degreeIdentity: 2 * e + b === 24 * m,
      });
    }
  }

  // Is every level-2 densest shape a lift? Not decidable by the search
  // used at level 1 -- 2^1600 is not a space to walk -- but the
  // neighbourhood condition is checkable, so a non-lifted candidate can
  // at least be looked for among natural constructions.
  const nonLiftProbes = [];
  {
    // a "diagonal" set: point p in cell p, for p in a level-1 shape
    const T1 = shapes.optimalShape(8).witness;
    const diag = T1.map((p) => L2.idx(p, p)).sort((a, b) => a - b);
    nonLiftProbes.push({
      name: "diagonal of the m=8 shape",
      size: diag.length,
      inducedEdges: inducedEdges(adj, diag),
      upperBound: level2UpperBound(diag.length),
      profile: profile(adj, diag),
    });
    // a product set: shape x shape
    const A = shapes.optimalShape(4).witness;
    const prod = [];
    for (const c of A) for (const p of A) prod.push(L2.idx(c, p));
    prod.sort((a, b) => a - b);
    nonLiftProbes.push({
      name: "product of two m=4 shapes",
      size: prod.length,
      inducedEdges: inducedEdges(adj, prod),
      upperBound: level2UpperBound(prod.length),
      profile: profile(adj, prod),
    });
  }

  const result = {
    schema: "holotrade.w33-level2-shapes.v1",
    fabric: "Cartesian W [] W: 1600 leaves, 24-regular, spectrum {24,14,8,4,-2,-8}",
    bounds: {
      upper: "e(T) <= 7m + m^2/320, equality iff f lies in the 14-eigenspace",
      lower: "e(T) >= -4m + m^2/100, equality iff f lies in the -8-eigenspace",
    },
    liftTheorem:
      "if f1 is in the 2-eigenspace of A1 then 1 (x) f1 and f1 (x) 1 are both in "
      + "the 14-eigenspace of A1 (x) I + I (x) A1, because 12 + 2 = 2 + 12 = 14",
    lifts: rows,
    nonLiftProbes,
  };
  result.allLiftsAttainBound = rows.every((r) => r.attainsBound);
  result.allLiftsIntriguing = rows.every((r) => r.profile.isIntriguing);
  result.allPredictionsHold = rows.every((r) => r.predictionHolds);
  result.digest = crypto.createHash("sha256").update(JSON.stringify(rows)).digest("hex");
  return result;
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  L("DO OPTIMAL RESERVATION SHAPES SURVIVE ONE LEVEL UP?");
  L("=".repeat(80));
  L(`  fabric: ${res.fabric}`);
  L(`  bound:  ${res.bounds.upper}`);
  L("");
  L("  level-1   lift        level-2 m   e(T)    bound    attains   two-valued   2e+b=km");
  for (const r of res.lifts) {
    L(`  ${String(r.level1Size).padStart(7)}   ${r.lift.padEnd(10)}  ${String(r.level2Size).padStart(9)}   `
      + `${String(r.inducedEdges).padStart(5)}   ${String(r.upperBound).padStart(6)}   `
      + `${String(r.attainsBound).padStart(7)}   ${String(r.profile.isIntriguing).padStart(10)}   ${r.degreeIdentity}`);
  }
  L("");
  L(`  every lift attains the level-2 bound:  ${res.allLiftsAttainBound}`);
  L(`  every lift is a two-valued (intriguing) set:  ${res.allLiftsIntriguing}`);
  L(`  every induced-edge count matches the arithmetic prediction:  ${res.allPredictionsHold}`);
  L("");
  L("  NON-LIFTED PROBES  (natural constructions that are not replications)");
  for (const p of res.nonLiftProbes) {
    L(`    ${p.name.padEnd(30)} m=${String(p.size).padStart(4)}  e=${String(p.inducedEdges).padStart(4)}  `
      + `bound=${String(p.upperBound).padStart(7)}  two-valued=${p.profile.isIntriguing}`);
  }

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/w33_level2_shapes.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, liftByPoints, liftByCells, level2UpperBound, level2LowerBound, inducedEdges, edgeBoundary, profile };
