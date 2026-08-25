#!/usr/bin/env node
// ======================================================================
// W(3,3) OPTIMAL RESERVATION SHAPE CATALOGUE
//
//   node analysis/w33_shape_catalogue.js [--write]
//
// ----------------------------------------------------------------------
// WHAT THIS ADDS TO THE EXISTING SPECTRAL BOUND
//
// research/w33_scheduler_math.md already derives, for any vertex set T
// of size m in the W(3,3) point graph SRG(40,12,2,4) with spectrum
// {12^1, 2^24, (-4)^15}:
//
//     m(40-m)/4  <=  b(T)  <=  2m(40-m)/5
//     m(m-10)/5  <=  e(T)  <=  m(m+8)/8
//
// Those are bounds. A scheduler cannot reserve a bound -- it reserves a
// SET. So the operational question is not "how dense could a shape be"
// but "which sizes admit a shape that actually attains the bound, and
// what is it".
//
// This file answers that exactly, by turning each bound into a finite
// combinatorial condition and searching the whole space.
//
// ----------------------------------------------------------------------
// THE EQUALITY CONDITIONS
//
// Write 1_T for the indicator vector and f = 1_T - (m/40)1, so f is the
// component orthogonal to the all-ones vector. Then
//
//     b(T) = 12m(1 - m/40) - f^T A f,     ||f||^2 = m(1 - m/40).
//
// The bounds come from -4||f||^2 <= f^T A f <= 2||f||^2, so equality on
// either side happens exactly when f lies ENTIRELY in one eigenspace.
// Projecting with the SRG identity A^2 = 8I - 2A + 4J turns that into a
// pure counting condition on neighbourhoods:
//
//   UPPER (densest, f in the 2-eigenspace)   -- "tight set"
//       v in T      =>  |N(v) cap T| = 2 + m/4
//       v not in T  =>  |N(v) cap T| = m/4
//       forces 4 | m
//
//   LOWER (most spread, f in the -4-eigenspace) -- "m-ovoid"
//       v in T      =>  |N(v) cap T| = 2m/5 - 4
//       v not in T  =>  |N(v) cap T| = 2m/5
//       forces 5 | m
//
// Both are the classical "intriguing set" dichotomy for strongly regular
// graphs, of positive and negative type respectively. Neither divisibility
// condition is sufficient -- existence has to be decided, and that is what
// the search below does.
//
// ----------------------------------------------------------------------
// WHY A SCHEDULER CARES
//
//   tight set   the densest possible reservation of its size: maximum
//               internal link count per node, minimum exposed boundary.
//               This is the shape you want for one tightly-coupled job.
//
//   m-ovoid     the most evenly spread set of its size: every node
//               outside it sees exactly the same number of its members.
//               This is the shape you want for anti-affinity -- replicas
//               placed so that no single link failure correlates them.
//
//   independence number  the largest set with NO internal link at all.
//               The true ceiling on a fully failure-independent spread.
//
// The Hoffman ratio bound gives alpha <= 40 * 4/(12+4) = 10, and a set
// of size 10 attaining it would be exactly an ovoid of the generalized
// quadrangle. Thas proved W(q) has no ovoid for odd q, so the bound must
// NOT be attained here. The search below settles the true value
// independently, without appealing to that theorem -- which is the point:
// it is a check ON the literature rather than a citation of it.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));

const N = S.CONST.points;      // 40
const K = S.CONST.degree;      // 12
const ADJ = S.ADJ;
const NBR_MASK = ADJ.map((row) => row.reduce((m, j) => m | (1n << BigInt(j)), 0n));

// ---------------------------------------------------------------------
// sanity: the graph really is the one the bounds were derived for
// ---------------------------------------------------------------------
function verifyGraph() {
  const lam = new Set(), mu = new Set();
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      const c = S.commonNeighbours(i, j).length;
      (S.isAdjacent(i, j) ? lam : mu).add(c);
    }
  }
  return {
    vertices: N,
    degree: K,
    edges: ADJ.reduce((a, r) => a + r.length, 0) / 2,
    lambda: [...lam],
    mu: [...mu],
    regular: ADJ.every((r) => r.length === K),
    srg: [...lam].length === 1 && [...mu].length === 1 && [...lam][0] === 2 && [...mu][0] === 4,
  };
}

// ---------------------------------------------------------------------
// Intriguing-set search.
//
// Backtracking over the 40 vertices with full arc-consistency on the
// neighbourhood-count constraints. Each vertex carries a target that
// depends on whether it is IN or OUT, so an unassigned vertex whose
// partial neighbour count is compatible with only one of the two targets
// is forced immediately. That propagation is what makes an exhaustive
// search over 2^40 tractable: the constraints are so rigid that the
// live tree is tiny.
//
// Returns { exists, count, witness } where `count` is exact when the
// search completes (it always does here, and `complete` records it).
// ---------------------------------------------------------------------
function searchIntriguing(m, targetIn, targetOut, { collect = 1, nodeCap = 40e6 } = {}) {
  if (!Number.isInteger(targetIn) || !Number.isInteger(targetOut)) {
    return { exists: false, reason: "non-integral neighbourhood target", count: 0, complete: true };
  }
  if (targetIn < 0 || targetOut < 0 || targetIn > K || targetOut > K) {
    return { exists: false, reason: "neighbourhood target outside [0,k]", count: 0, complete: true };
  }

  const state = new Int8Array(N).fill(-1);   // -1 unset, 0 out, 1 in
  const inCount = new Int8Array(N);          // assigned-in neighbours
  const unknown = new Int8Array(N).fill(0);
  for (let v = 0; v < N; v++) unknown[v] = ADJ[v].length;

  let chosen = 0, rejected = 0, solutions = 0, nodes = 0, exhausted = true;
  const witnesses = [];

  // feasibility of a vertex given its own (possibly unknown) membership
  function feasible(v) {
    const s = inCount[v], u = unknown[v];
    if (state[v] === 1) return s <= targetIn && targetIn <= s + u;
    if (state[v] === 0) return s <= targetOut && targetOut <= s + u;
    const okIn = s <= targetIn && targetIn <= s + u;
    const okOut = s <= targetOut && targetOut <= s + u;
    return okIn || okOut;
  }

  // assign v, recording every derived change so it can be undone
  function assign(v, val, trail) {
    state[v] = val;
    trail.push([v, "state"]);
    if (val === 1) chosen++; else rejected++;
    for (const u of ADJ[v]) {
      unknown[u]--;
      if (val === 1) inCount[u]++;
    }
    trail.push([v, "prop"]);
    return true;
  }

  function undo(v, val) {
    for (const u of ADJ[v]) {
      unknown[u]++;
      if (val === 1) inCount[u]--;
    }
    state[v] = -1;
    if (val === 1) chosen--; else rejected--;
  }

  // full propagation to a fixed point; returns the list of forced
  // assignments so they can be rolled back, or null on contradiction
  function propagate() {
    const forced = [];
    let changed = true;
    while (changed) {
      changed = false;
      if (chosen > m || rejected > N - m) { rollback(forced); return null; }
      for (let v = 0; v < N; v++) {
        if (!feasible(v)) { rollback(forced); return null; }
        const s = inCount[v], u = unknown[v];

        // a decided vertex whose count is already met/forced propagates
        // to its unassigned neighbours
        if (state[v] !== -1) {
          const t = state[v] === 1 ? targetIn : targetOut;
          if (s === t && u > 0) {
            for (const w of ADJ[v]) if (state[w] === -1) { assign(w, 0, []); forced.push([w, 0]); changed = true; }
          } else if (s + u === t && u > 0) {
            for (const w of ADJ[v]) if (state[w] === -1) { assign(w, 1, []); forced.push([w, 1]); changed = true; }
          }
        } else {
          // an undecided vertex compatible with only one target is forced
          const okIn = s <= targetIn && targetIn <= s + u;
          const okOut = s <= targetOut && targetOut <= s + u;
          if (okIn && !okOut) { assign(v, 1, []); forced.push([v, 1]); changed = true; }
          else if (!okIn && okOut) { assign(v, 0, []); forced.push([v, 0]); changed = true; }
        }
      }
      // global cardinality closure
      const unset = [];
      for (let v = 0; v < N; v++) if (state[v] === -1) unset.push(v);
      if (unset.length) {
        if (chosen === m) { for (const v of unset) { assign(v, 0, []); forced.push([v, 0]); } changed = true; }
        else if (chosen + unset.length === m) { for (const v of unset) { assign(v, 1, []); forced.push([v, 1]); } changed = true; }
      }
    }
    return forced;
  }

  function rollback(forced) {
    for (let i = forced.length - 1; i >= 0; i--) undo(forced[i][0], forced[i][1]);
    forced.length = 0;
  }

  function recurse() {
    if (++nodes > nodeCap) { exhausted = false; return true; }
    const forced = propagate();
    if (forced === null) return false;

    let v = -1;
    for (let i = 0; i < N; i++) if (state[i] === -1) { v = i; break; }
    if (v === -1) {
      // complete assignment: verify every constraint exactly
      let ok = chosen === m;
      if (ok) {
        for (let u = 0; u < N && ok; u++) {
          const t = state[u] === 1 ? targetIn : targetOut;
          if (inCount[u] !== t) ok = false;
        }
      }
      if (ok) {
        solutions++;
        if (witnesses.length < collect) {
          witnesses.push([...state.keys()].filter((i) => state[i] === 1));
        }
      }
      rollback(forced);
      return false;
    }

    // symmetry break: vertex 0 is in the set for the first branch only
    for (const val of [1, 0]) {
      assign(v, val, []);
      const stop = recurse();
      undo(v, val);
      if (stop) { rollback(forced); return true; }
    }
    rollback(forced);
    return false;
  }

  recurse();
  return {
    exists: solutions > 0,
    count: solutions,
    complete: exhausted,
    searchNodes: nodes,
    witness: witnesses[0] || null,
  };
}

// ---------------------------------------------------------------------
// Independence and clique numbers, exactly.
// ---------------------------------------------------------------------
function maxIndependentSet() {
  // branch and bound with a greedy-colouring style bound; the graph is
  // small and dense enough that this closes immediately
  let best = 0, bestSet = null, nodes = 0;
  const order = [...Array(N).keys()].sort((a, b) => ADJ[b].length - ADJ[a].length);

  function bb(candIdx, current, forbidden) {
    nodes++;
    if (current.length > best) { best = current.length; bestSet = [...current]; }
    if (candIdx >= order.length) return;
    // bound: nothing left can beat the incumbent
    let remaining = 0;
    for (let i = candIdx; i < order.length; i++) if (!forbidden.has(order[i])) remaining++;
    if (current.length + remaining <= best) return;

    for (let i = candIdx; i < order.length; i++) {
      const v = order[i];
      if (forbidden.has(v)) continue;
      if (current.length + (order.length - i) <= best) return;
      const added = [];
      for (const u of ADJ[v]) if (!forbidden.has(u)) { forbidden.add(u); added.push(u); }
      const selfAdded = !forbidden.has(v);
      if (selfAdded) forbidden.add(v);
      current.push(v);
      bb(i + 1, current, forbidden);
      current.pop();
      if (selfAdded) forbidden.delete(v);
      for (const u of added) forbidden.delete(u);
    }
  }
  bb(0, [], new Set());
  return { alpha: best, witness: bestSet, searchNodes: nodes };
}

function maxClique() {
  let best = 0, bestSet = null;
  function bb(cands, current) {
    if (current.length > best) { best = current.length; bestSet = [...current]; }
    if (!cands.length) return;
    if (current.length + cands.length <= best) return;
    for (let i = 0; i < cands.length; i++) {
      const v = cands[i];
      if (current.length + (cands.length - i) <= best) return;
      const next = cands.slice(i + 1).filter((u) => S.isAdjacent(v, u));
      current.push(v);
      bb(next, current);
      current.pop();
    }
  }
  bb([...Array(N).keys()], []);
  return { omega: best, witness: bestSet };
}

// ---------------------------------------------------------------------
// Verification helpers -- never trust the search, check the witness
// ---------------------------------------------------------------------
function inducedEdges(T) {
  const set = new Set(T);
  let e = 0;
  for (const v of T) for (const u of ADJ[v]) if (set.has(u) && u > v) e++;
  return e;
}
function edgeBoundary(T) {
  const set = new Set(T);
  let b = 0;
  for (const v of T) for (const u of ADJ[v]) if (!set.has(u)) b++;
  return b;
}
function neighbourProfile(T) {
  const set = new Set(T);
  const inside = new Set(), outside = new Set();
  for (let v = 0; v < N; v++) {
    const c = ADJ[v].filter((u) => set.has(u)).length;
    (set.has(v) ? inside : outside).add(c);
  }
  return { inside: [...inside].sort((a, b) => a - b), outside: [...outside].sort((a, b) => a - b) };
}

// ---------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------
function run() {
  const graph = verifyGraph();
  if (!graph.srg) throw new Error("substrate graph is not SRG(40,12,2,4); bounds do not apply");

  const tight = [];
  const ovoids = [];

  for (let m = 1; m < N; m++) {
    // ---- upper bound / tight sets (densest shapes) -------------------
    if (m % 4 === 0) {
      const tIn = 2 + m / 4, tOut = m / 4;
      const r = searchIntriguing(m, tIn, tOut, { collect: 1 });
      const bound = (m * (m + 8)) / 8;
      const row = {
        m, targetIn: tIn, targetOut: tOut,
        boundInducedEdges: bound,
        exists: r.exists, complete: r.complete, searchNodes: r.searchNodes,
      };
      if (r.witness) {
        row.witness = r.witness;
        row.inducedEdges = inducedEdges(r.witness);
        row.boundary = edgeBoundary(r.witness);
        row.profile = neighbourProfile(r.witness);
        row.attainsBound = row.inducedEdges === bound;
      }
      tight.push(row);
    }

    // ---- lower bound / m-ovoids (most spread shapes) -----------------
    if ((2 * m) % 5 === 0) {
      const tIn = (2 * m) / 5 - 4, tOut = (2 * m) / 5;
      const r = searchIntriguing(m, tIn, tOut, { collect: 1 });
      const bound = (m * (m - 10)) / 5;
      const row = {
        m, targetIn: tIn, targetOut: tOut,
        boundInducedEdges: bound,
        exists: r.exists, complete: r.complete, searchNodes: r.searchNodes,
      };
      if (r.witness) {
        row.witness = r.witness;
        row.inducedEdges = inducedEdges(r.witness);
        row.boundary = edgeBoundary(r.witness);
        row.profile = neighbourProfile(r.witness);
        row.attainsBound = row.inducedEdges === bound;
      }
      ovoids.push(row);
    }
  }

  const ind = maxIndependentSet();
  const cli = maxClique();

  // Hoffman / ratio bounds, for comparison against the exact answers
  const hoffmanAlpha = (N * -(-4)) / (K - -4);          // n(-s)/(k-s) = 40*4/16
  const hoffmanOmega = 1 - K / -4;                       // 1 - k/s = 1 + 3

  const result = {
    schema: "holotrade.w33-shape-catalogue.v1",
    generated: "deterministic — no randomness in this computation",
    graph,
    spectrum: { 12: 1, 2: 24, "-4": 15 },
    bounds: {
      edgeBoundary: "m(40-m)/4 <= b(T) <= 2m(40-m)/5",
      inducedEdges: "m(m-10)/5 <= e(T) <= m(m+8)/8",
      equalityUpper: "f lies in the 2-eigenspace: |N(v) cap T| = 2 + m/4 inside, m/4 outside",
      equalityLower: "f lies in the -4-eigenspace: |N(v) cap T| = 2m/5 - 4 inside, 2m/5 outside",
    },
    extremes: {
      cliqueNumber: cli.omega,
      cliqueWitness: cli.witness,
      cliqueHoffmanBound: hoffmanOmega,
      cliqueBoundAttained: cli.omega === hoffmanOmega,
      independenceNumber: ind.alpha,
      independenceWitness: ind.witness,
      independenceHoffmanBound: hoffmanAlpha,
      independenceBoundAttained: ind.alpha === hoffmanAlpha,
      independenceSearchNodes: ind.searchNodes,
    },
    tightSets: tight,
    mOvoids: ovoids,
  };

  // ---- self-verification of every reported witness ------------------
  const problems = [];
  for (const row of [...tight, ...ovoids]) {
    if (!row.witness) continue;
    if (row.witness.length !== row.m) problems.push(`m=${row.m}: witness wrong size`);
    if (!row.attainsBound) problems.push(`m=${row.m}: witness does not attain the bound`);
    if (row.profile.inside.length > 1 || row.profile.outside.length > 1) {
      problems.push(`m=${row.m}: witness is not an intriguing set (profile not constant)`);
    }
    if (row.inducedEdges * 2 + row.boundary !== 12 * row.m) {
      problems.push(`m=${row.m}: 2e(T)+b(T) != 12m`);
    }
  }
  const indSet = new Set(ind.witness);
  for (const v of ind.witness) {
    if (ADJ[v].some((u) => indSet.has(u))) problems.push("independence witness has an internal edge");
  }
  for (const v of cli.witness) {
    for (const u of cli.witness) if (u !== v && !S.isAdjacent(u, v)) problems.push("clique witness is not complete");
  }
  result.selfCheck = { problems, allChecksPass: problems.length === 0 };

  result.digest = crypto.createHash("sha256")
    .update(JSON.stringify({ tight, ovoids, extremes: result.extremes }))
    .digest("hex");

  return result;
}

// ---------------------------------------------------------------------
if (require.main === module) {
  const res = run();
  const write = process.argv.includes("--write");

  const line = (s) => console.log(s);
  line("W(3,3) OPTIMAL RESERVATION SHAPE CATALOGUE");
  line("=".repeat(66));
  line(`graph: SRG(${res.graph.vertices},${res.graph.degree},${res.graph.lambda[0]},${res.graph.mu[0]})  edges=${res.graph.edges}  srg=${res.graph.srg}`);
  line("");
  line("EXTREMES");
  line(`  clique number       omega = ${res.extremes.cliqueNumber}   (Hoffman bound ${res.extremes.cliqueHoffmanBound}, attained=${res.extremes.cliqueBoundAttained})`);
  line(`    witness           ${JSON.stringify(res.extremes.cliqueWitness)}`);
  line(`  independence number alpha = ${res.extremes.independenceNumber}   (Hoffman bound ${res.extremes.independenceHoffmanBound}, attained=${res.extremes.independenceBoundAttained})`);
  line(`    witness           ${JSON.stringify(res.extremes.independenceWitness)}`);
  line("");
  line("TIGHT SETS  (densest shape of each size; equality in e(T) <= m(m+8)/8)");
  line("   m  target in/out   bound e(T)   exists  actual e(T)  boundary  complete");
  for (const r of res.tightSets) {
    line(`  ${String(r.m).padStart(2)}  ${String(r.targetIn).padStart(6)}/${String(r.targetOut).padEnd(4)}  ${String(r.boundInducedEdges).padStart(9)}   ${r.exists ? "  yes " : "  NO  "}  ${String(r.inducedEdges ?? "-").padStart(10)}  ${String(r.boundary ?? "-").padStart(8)}  ${r.complete}`);
  }
  line("");
  line("m-OVOIDS  (most-spread shape of each size; equality in e(T) >= m(m-10)/5)");
  line("   m  target in/out   bound e(T)   exists  actual e(T)  boundary  complete");
  for (const r of res.mOvoids) {
    line(`  ${String(r.m).padStart(2)}  ${String(r.targetIn).padStart(6)}/${String(r.targetOut).padEnd(4)}  ${String(r.boundInducedEdges).padStart(9)}   ${r.exists ? "  yes " : "  NO  "}  ${String(r.inducedEdges ?? "-").padStart(10)}  ${String(r.boundary ?? "-").padStart(8)}  ${r.complete}`);
  }
  line("");
  line(`self-check: ${res.selfCheck.allChecksPass ? "ALL WITNESSES VERIFIED" : "PROBLEMS: " + res.selfCheck.problems.join("; ")}`);
  line(`digest: ${res.digest.slice(0, 32)}`);

  if (write) {
    const out = path.resolve(__dirname, "../data/w33_shape_catalogue.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    line(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = { run, searchIntriguing, maxIndependentSet, maxClique, inducedEdges, edgeBoundary, neighbourProfile };
