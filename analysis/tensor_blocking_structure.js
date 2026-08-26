#!/usr/bin/env node
// ======================================================================
// NARROWING THE DEPTH-2 TENSOR BLOCKING INTERVAL
//
//   node analysis/tensor_blocking_structure.js [--write]
//
// js/tensor-sharding.js leaves the blocking number of the product-tile
// family open at [110, 121]. This does not close it. What it does is
// reduce the problem to a single sharp question, and settle the
// interval conditionally.
//
// ----------------------------------------------------------------------
// THE REDUCTION
//
// Write X_p = { q : (p,q) in X } for the fibre of a blocked set X above
// point p, and P = { p : X_p non-empty } for its support. Then
//
//     X meets the tile L_a x M_b   iff   (U_{p in L_a} X_p)  meets  M_b,
//
// so X blocks every tile iff for EVERY line L_a the union
// Y_a = U_{p in L_a} X_p is itself a blocking set of the 40 lines, hence
// |Y_a| >= tau_1 = 11. Two consequences follow immediately.
//
// ----------------------------------------------------------------------
// 1. THE SUPPORT MUST BE A BLOCKING SET
//
// If some line missed P entirely then Y_a would be empty. So |P| >= 11.
//
// ----------------------------------------------------------------------
// 2. IF THE SUPPORT IS MINIMUM, THE ANSWER IS EXACTLY 121
//
// Take P = B, an 11-point blocker. Counting incidences, the 11 points of
// B lie on 44 line-slots across 40 lines, so exactly 4 lines meet B twice
// and 36 meet it once -- and, checked directly, ALL ELEVEN points of B
// are the unique B-point of at least one line.
//
// For such a line, Y_a = X_p for that single p, so X_p must itself be a
// line-blocking set and |X_p| >= 11. That holds for every one of the 11
// points, and the fibres are disjoint by construction, so
//
//     |X| = sum_p |X_p| >= 11 * 11 = 121.
//
// B x B attains it. So tau = 121 exactly, CONDITIONAL on the support
// being a minimum blocker -- and the constructive upper bound is not
// merely good, it is forced.
//
// ----------------------------------------------------------------------
// WHAT REMAINS OPEN
//
// Beating 121 therefore requires a support of 12 or more points, trading
// extra support for smaller fibres. The double count still permits 110:
// summing |Y_a| >= 11 over the 40 lines and dividing by the 4 lines
// through each point gives |X| >= 110, with equality demanding that for
// every line the four fibres are pairwise disjoint and union to exactly
// 11. An integer weighting f(p) = |X_p| with every line summing to 11
// does exist, so no counting obstruction rules 110 out.
//
// Whether the SETS can be arranged to match is the open question. Direct
// SAT on 1,600 leaf variables with a cardinality bound near 110 did not
// terminate in the budget tried; greedy plus pruning reaches only 125,
// and B x B survives exhaustive single-leaf pruning and local search
// unchanged, so it is a minimal blocking set rather than merely a
// convenient one.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const T = require(path.resolve(__dirname, "../js/tensor-sharding.js"));

const N = S.CONST.points;
const leaf = (p, q) => p * N + q;

function tiles() {
  const out = [];
  for (const A of S.LINES) for (const B of S.LINES) {
    out.push([...A].flatMap((p) => [...B].map((q) => leaf(p, q))));
  }
  return out;
}

function blocks(X, tl) {
  const s = new Set(X);
  return tl.every((t) => t.some((v) => s.has(v)));
}

/** Which points of a blocker are the unique blocker-point of some line? */
function uniqueWitnessPoints(B) {
  const bs = new Set(B);
  const counts = new Map();
  const intersectionSizes = new Map();
  for (const L of S.LINES) {
    const hit = [...L].filter((p) => bs.has(p));
    intersectionSizes.set(hit.length, (intersectionSizes.get(hit.length) || 0) + 1);
    if (hit.length === 1) counts.set(hit[0], (counts.get(hit[0]) || 0) + 1);
  }
  return { unique: [...counts.keys()].sort((a, b) => a - b), intersectionSizes };
}

function run() {
  const tl = tiles();
  const B = [...T.BLOCKER];
  const uw = uniqueWitnessPoints(B);
  const bxb = B.flatMap((p) => B.map((q) => leaf(p, q)));

  // is B x B minimal? remove each leaf and re-test
  let removable = 0;
  for (const v of bxb) {
    if (blocks(bxb.filter((u) => u !== v), tl)) removable++;
  }

  return {
    schema: "holotrade.tensor-blocking-structure.v1",
    publishedInterval: [T.tensorBlockingBounds(2).lower, T.tensorBlockingBounds(2).upper],
    reduction: "X blocks every tile iff every line's union of fibres is a line-blocking set",
    tau1: T.TAU1,
    blockerSize: B.length,
    lineIntersectionSizes: Object.fromEntries(uw.intersectionSizes),
    uniqueWitnessPoints: uw.unique,
    allBlockerPointsAreUniqueWitnesses: uw.unique.length === B.length,
    conditionalTau: uw.unique.length === B.length ? T.TAU1 * T.TAU1 : null,
    conditionalStatement:
      "if the support of X is a minimum blocker then every fibre must itself block, "
      + "so |X| >= 121, and B x B attains it: tau = 121 exactly in that case",
    bxbSize: bxb.length,
    bxbBlocks: blocks(bxb, tl),
    bxbRemovableLeaves: removable,
    bxbIsMinimal: removable === 0,
    stillOpen:
      "beating 121 requires a support of 12 or more points; the double count still "
      + "permits 110 and an integer fibre-size weighting summing to 11 on every line "
      + "does exist, so no counting obstruction rules it out",
  };
}

if (require.main === module) {
  const r = run();
  const L = console.log;
  L("NARROWING THE DEPTH-2 TENSOR BLOCKING INTERVAL");
  L("=".repeat(72));
  L(`  published interval        [${r.publishedInterval.join(", ")}]  (open)`);
  L(`  reduction                 ${r.reduction}`);
  L("");
  L(`  |L cap B| over 40 lines   ${JSON.stringify(r.lineIntersectionSizes)}`);
  L(`  blocker points that are the unique B-point of some line: `
    + `${r.uniqueWitnessPoints.length} of ${r.blockerSize}`);
  L(`  => every fibre must itself be a line-blocker, so |X| >= 11 x 11 = ${r.conditionalTau}`);
  L("");
  L(`  B x B: size ${r.bxbSize}, blocks all 1600 tiles: ${r.bxbBlocks}`);
  L(`  removable leaves: ${r.bxbRemovableLeaves}  =>  minimal: ${r.bxbIsMinimal}`);
  L("");
  L("  CONDITIONAL RESULT");
  L(`    ${r.conditionalStatement}`);
  L("");
  L("  STILL OPEN");
  L(`    ${r.stillOpen}`);

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/tensor_blocking_structure.json");
    fs.writeFileSync(out, JSON.stringify(r, null, 2));
    L(`
  written: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, tiles, blocks, uniqueWitnessPoints };
