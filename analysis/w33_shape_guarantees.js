#!/usr/bin/env node
// ======================================================================
// W(3,3) WORST-CASE PLACEMENT GUARANTEES
//
//   node analysis/w33_shape_guarantees.js [--write]
//
// ----------------------------------------------------------------------
// THE QUESTION
//
// scheduler/w33-shapes.js reports a SAMPLED placement capacity: over
// random sets of busy nodes, how often can an optimal shape still be
// placed. That is honest but weak. A scheduler wants a GUARANTEE:
//
//     "with at most B nodes busy, a densest m-node reservation is
//      always placeable, no matter WHICH nodes are busy."
//
// That is a worst-case quantity, and it has an exact combinatorial
// answer. A set X of blocked points defeats a shape S exactly when every
// image of S under the automorphism group meets X -- that is, when X is
// a BLOCKING SET (a hitting set, a transversal) for the shape's orbit.
//
// So if tau is the minimum size of a blocking set for the orbit of S:
//
//     * with |X| <= tau - 1 busy nodes, a placement ALWAYS exists;
//     * with |X| = tau, an adversary can make placement impossible.
//
// tau - 1 is therefore the exact guarantee, and tau is exactly where the
// cliff is. Both are computed here.
//
// ----------------------------------------------------------------------
// THE PRETTY CASE: m = 4
//
// The densest 4-point shapes are exactly the 40 totally isotropic lines,
// so blocking them means hitting every line. Count incidences: each
// point lies on 4 lines, so k points cover at most 4k line-incidences,
// and covering all 40 lines needs 4k >= 40, i.e. k >= 10.
//
// Equality would require all 40 incidences to be distinct -- no two of
// the 10 points on a common line -- which is precisely an OVOID. The
// catalogue proved this quadrangle has none (independence number 7, not
// the ratio bound's 10). Therefore
//
//     tau(lines) >= 11
//
// and the no-ovoid result stops being a curiosity: it is the reason a
// four-node reservation survives any ten simultaneous failures. The
// exact value is computed below rather than left at the bound.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));
const shapes = require(path.resolve(__dirname, "../scheduler/w33-shapes.js"));

const N = S.CONST.points;

// ---------------------------------------------------------------------
// Minimum hitting set, exactly.
//
// Branch and bound over the sets to be hit. At each step take an
// as-yet-unhit set and branch on which of its points enters the cover:
// any cover must contain at least one of them, so this is complete.
// Bounding by a greedy incumbent plus a disjoint-sets lower bound closes
// it quickly at these sizes.
// ---------------------------------------------------------------------
function minimumHittingSet(sets, universe = N, { cap = 8e7, msBudget = Infinity } = {}) {
  const deadline = msBudget === Infinity ? Infinity : Date.now() + msBudget;
  // which sets contain each point
  const covers = Array.from({ length: universe }, () => []);
  sets.forEach((s, i) => { for (const v of s) covers[v].push(i); });

  // greedy incumbent for an initial upper bound
  const greedy = () => {
    const hit = new Uint8Array(sets.length);
    const chosen = [];
    let left = sets.length;
    while (left > 0) {
      let best = -1, bestGain = -1;
      for (let v = 0; v < universe; v++) {
        let gain = 0;
        for (const i of covers[v]) if (!hit[i]) gain++;
        if (gain > bestGain) { bestGain = gain; best = v; }
      }
      if (bestGain <= 0) break;
      chosen.push(best);
      for (const i of covers[best]) if (!hit[i]) { hit[i] = 1; left--; }
    }
    return chosen;
  };

  let best = greedy();
  let bestSize = best.length;
  let nodes = 0;
  let exhausted = true;

  // COUNTING LOWER BOUND, from transitivity.
  //
  // The orbit of a shape under a point-transitive group is balanced:
  // every point lies in exactly |orbit| * m / N of the images (double
  // count incidences and use that the group moves any point to any
  // other). So one blocked point can hit at most that many images, and
  //
  //     tau  >=  |orbit| / (|orbit| * m / N)  =  N / m,
  //
  // hence tau >= ceil(N/m). This generalises the m=4 incidence argument
  // exactly -- at m=4 it gives 10, which is where the no-ovoid result
  // then pushes it to 11 -- and it is far stronger than the disjoint-set
  // bound on large overlapping orbits, where barely any two images are
  // disjoint at all.
  const shapeSize = sets.length ? sets[0].length : 1;
  const countingBound = sets.every((x) => x.length === shapeSize)
    ? Math.ceil(universe / shapeSize)
    : 1;

  // lower bound: a maximal collection of pairwise disjoint unhit sets
  // must each contribute a distinct point
  const disjointBound = (hit) => {
    const used = new Uint8Array(universe);
    let count = 0;
    for (let i = 0; i < sets.length; i++) {
      if (hit[i]) continue;
      if (sets[i].every((v) => !used[v])) {
        count++;
        for (const v of sets[i]) used[v] = 1;
      }
    }
    return count;
  };

  const hit = new Uint8Array(sets.length);
  const chosen = [];

  function search(remaining) {
    if (++nodes > cap) { exhausted = false; return; }
    if ((nodes & 1023) === 0 && Date.now() > deadline) { exhausted = false; return; }
    if (!exhausted) return;
    if (remaining === 0) {
      if (chosen.length < bestSize) { bestSize = chosen.length; best = [...chosen]; }
      return;
    }
    if (chosen.length + Math.max(disjointBound(hit), 0) >= bestSize) return;

    // branch on the first unhit set
    let target = -1;
    for (let i = 0; i < sets.length; i++) if (!hit[i]) { target = i; break; }

    for (const v of sets[target]) {
      const newlyHit = [];
      for (const i of covers[v]) if (!hit[i]) { hit[i] = 1; newlyHit.push(i); }
      chosen.push(v);
      search(remaining - newlyHit.length);
      chosen.pop();
      for (const i of newlyHit) hit[i] = 0;
    }
  }

  const lowerBound = Math.max(countingBound, disjointBound(new Uint8Array(sets.length)));
  search(sets.length);
  return {
    tau: exhausted ? bestSize : null,
    upperBound: bestSize,
    lowerBound,
    countingBound,
    witness: best.sort((a, b) => a - b),
    searchNodes: nodes,
    exhausted,
  };
}

// ---------------------------------------------------------------------
function verifyBlocking(blocker, orbit) {
  const X = new Set(blocker);
  return orbit.every((img) => img.some((v) => X.has(v)));
}

function verifyGuarantee(orbit, size, { trials = 4000, seed = "guarantee" } = {}) {
  // spot-check that no blocked set of this size defeats the shape
  const rand = S.rng(seed);
  for (let t = 0; t < trials; t++) {
    const X = new Set();
    while (X.size < size) X.add(Math.floor(rand() * N));
    if (!orbit.some((img) => img.every((v) => !X.has(v)))) return false;
  }
  return true;
}

// ---------------------------------------------------------------------
function run() {
  const cat = shapes.frozenCatalogue();
  const rows = [];

  for (const m of Object.keys(cat.tight).map(Number).sort((a, b) => a - b)) {
    const witness = cat.tight[m];
    const orbit = shapes.shapeOrbit(witness);

    // A shape of m points is trivially defeated by blocking 40 - m + 1
    // points, since then fewer than m are free. Only compute the exact
    // transversal where it is smaller than that and the orbit is a
    // manageable size for exact search.
    const trivialCeiling = N - m + 1;
    // Exact where the search closes inside its budget; an interval
    // otherwise. Reporting a greedy answer as if it were the minimum
    // would turn a guarantee into a guess.
    const hs = minimumHittingSet(orbit, N, { msBudget: 20000 });

    const row = {
      m,
      orbitSize: orbit.length,
      trivialCeiling,
      inducedEdges: shapes.inducedEdges(witness),
      boundary: shapes.edgeBoundary(witness),
    };
    row.exhaustive = hs.exhausted;
    row.searchNodes = hs.searchNodes;
    row.blockerWitness = hs.witness;
    row.blockerValid = verifyBlocking(hs.witness, orbit);
    if (hs.exhausted) {
      row.tau = hs.tau;
      row.guarantee = hs.tau - 1;
      row.guaranteeSpotChecked = verifyGuarantee(orbit, hs.tau - 1, { trials: 1200, seed: "g" + m });
      row.tauBelowTrivial = hs.tau < trivialCeiling;
      row.countingBound = hs.countingBound;
      row.countingBoundTight = hs.tau === hs.countingBound;
    } else {
      // the guarantee is still sound at lowerBound - 1: no set that
      // small can block, because the disjoint-orbit-images argument
      // needs at least lowerBound points
      row.tauLowerBound = hs.lowerBound;
      row.countingBound = hs.countingBound;
      row.tauUpperBound = hs.upperBound;
      row.guarantee = hs.lowerBound - 1;
      row.guaranteeSpotChecked = verifyGuarantee(orbit, hs.lowerBound - 1, { trials: 1200, seed: "g" + m });
      row.note = "search did not close in budget; guarantee stated from the certified lower bound";
    }
    rows.push(row);
  }

  // the m=4 case deserves its own derivation, since the incidence count
  // ties it directly to the non-existence of an ovoid
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const lineHS = minimumHittingSet(lines, N, { msBudget: 60000 });
  const ovoidBound = {
    countingLowerBound: Math.ceil((S.LINES.length * 1) / 4),   // 40 lines / 4 per point
    equalityWouldBeAnOvoid: true,
    ovoidExists: cat.extremes.independenceBoundAttained,
    thereforeTauAtLeast: cat.extremes.independenceBoundAttained ? 10 : 11,
    exactTau: lineHS.tau,
    exactSearchClosed: lineHS.exhausted,
    witness: lineHS.witness,
    valid: verifyBlocking(lineHS.witness, lines),
  };

  const result = {
    schema: "holotrade.w33-shape-guarantees.v1",
    question: "with at most B nodes busy, is an optimal shape always placeable regardless of WHICH are busy?",
    answer: "B = tau - 1, where tau is the minimum blocking set of the shape's orbit",
    lineBlockingDerivation: ovoidBound,
    shapes: rows,
  };
  result.digest = crypto.createHash("sha256")
    .update(JSON.stringify({ rows, ovoidBound })).digest("hex");
  return result;
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  L("W(3,3) WORST-CASE PLACEMENT GUARANTEES");
  L("=".repeat(74));
  L("");
  L("THE m=4 CASE (the 40 lines), from first principles");
  const d = res.lineBlockingDerivation;
  L(`  each point lies on 4 lines, so hitting 40 lines needs >= ${d.countingLowerBound} points`);
  L(`  equality would require an ovoid (10 pairwise non-collinear points)`);
  L(`  an ovoid exists here?  ${d.ovoidExists}`);
  L(`  therefore tau >= ${d.thereforeTauAtLeast}`);
  L(`  exact tau = ${d.exactTau}   blocker verified: ${d.valid}`);
  L(`  => a four-node densest reservation survives ANY ${d.exactTau - 1} simultaneous busy/failed nodes`);
  L("");
  L("PER-SHAPE GUARANTEES");
  L("   m   orbit         tau   guarantee   trivial ceiling   status   spot-checked");
  for (const r of res.shapes) {
    const tau = r.tau != null ? String(r.tau) : `[${r.tauLowerBound},${r.tauUpperBound}]`;
    L(`  ${String(r.m).padStart(2)}  ${String(r.orbitSize).padStart(6)}   ${tau.padStart(9)}   ${String(r.guarantee).padStart(9)}   ${String(r.trivialCeiling).padStart(15)}   ${r.exhaustive ? "exact" : "bound"}   ${r.guaranteeSpotChecked}`);
  }
  L("");
  L(`digest: ${res.digest.slice(0, 32)}`);

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/w33_shape_guarantees.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, minimumHittingSet, verifyBlocking, verifyGuarantee };
