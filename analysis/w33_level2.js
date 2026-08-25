#!/usr/bin/env node
// ======================================================================
// W(3,3) AT LEVEL 2 — the inter-cell fabric, as an actual graph
//
//   node analysis/w33_level2.js [--write]
//
// ----------------------------------------------------------------------
// THE GAP THIS CLOSES
//
// Everything the repository proves about topology is level-1: one cell of
// 40 points. The recursive layer is currently a DISTANCE FORMULA --
// js/substrate.js computes hops as "route inside the first divergent
// cell, then eight moves per descent on each side", giving the bound
// 16n - 14 -- and the paper labels it MODELLED, with the note "no
// physical product graph".
//
// That is the honest label, and it is also the gap. A distance formula
// cannot tell you the degree, the spectrum, the bisection, or whether an
// optimal reservation shape exists one level up. Only a graph can.
//
// So: define the level-2 graph explicitly, under each construction the
// architecture could plausibly mean, and compute the exact invariants.
//
// ----------------------------------------------------------------------
// THREE CONSTRUCTIONS, AND WHY THE CHOICE IS A REAL ENGINEERING DECISION
//
// A level-2 leaf is a pair (c, p): cell c, point p inside it. What makes
// two leaves adjacent is exactly the question of how cells are wired, and
// there are three natural answers with wildly different costs.
//
//   CARTESIAN  W [] W
//       (c,p) ~ (d,q)  iff  (c = d and p ~ q)  or  (c ~ d and p = q)
//     Each leaf keeps its 12 intra-cell links and gains one inter-cell
//     link per neighbouring cell, to the SAME point position. Homogeneous,
//     no gateway node, no privileged position -- which is what "the
//     network is the computer" implies. Degree 24.
//
//   LEXICOGRAPHIC  W [ W ]
//       (c,p) ~ (d,q)  iff  (c = d and p ~ q)  or  c ~ d
//     Adjacent cells are FULLY meshed: every leaf of one talks to every
//     leaf of the other. Diameter 2 at any level, and a wiring bill that
//     grows like the square of the cell size. Degree 492.
//
//   HIERARCHICAL (what the software's distance formula implies)
//     Cells meet through a bounded gateway, so leaving a cell costs a
//     climb and entering costs a descent. This is what produces the
//     16n - 14 bound: 2 moves at the divergent cell, 8 per descent, both
//     sides.
//
// These are not three descriptions of one thing. They are three different
// machines, and the numbers below are how much the choice costs.
// ======================================================================

"use strict";

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");

global.window = global;
const S = require(path.resolve(__dirname, "../js/substrate.js"));

const N1 = S.CONST.points;      // 40
const K1 = S.CONST.degree;      // 12
const N2 = N1 * N1;             // 1600

const idx = (c, p) => c * N1 + p;
const cellOf = (v) => Math.floor(v / N1);
const pointOf = (v) => v % N1;

// ---------------------------------------------------------------------
// constructions
// ---------------------------------------------------------------------

function buildCartesian() {
  const adj = Array.from({ length: N2 }, () => []);
  for (let c = 0; c < N1; c++) {
    for (let p = 0; p < N1; p++) {
      const v = idx(c, p);
      for (const q of S.ADJ[p]) adj[v].push(idx(c, q));      // same cell
      for (const d of S.ADJ[c]) adj[v].push(idx(d, p));      // same position
    }
  }
  return adj;
}

function buildLexicographic() {
  const adj = Array.from({ length: N2 }, () => []);
  for (let c = 0; c < N1; c++) {
    for (let p = 0; p < N1; p++) {
      const v = idx(c, p);
      for (const q of S.ADJ[p]) adj[v].push(idx(c, q));
      for (const d of S.ADJ[c]) for (let q = 0; q < N1; q++) adj[v].push(idx(d, q));
    }
  }
  return adj;
}

/**
 * Hierarchical: every cell exposes a gateway set, and inter-cell traffic
 * must pass through it. Modelled with the cell's own optimal 4-point
 * shape as the gateway -- a line, which is the densest 4-set and the
 * natural port group. Cell c's gateway talks to cell d's gateway when
 * c ~ d, matched position for position.
 */
function buildHierarchical(gatewaySize = 4) {
  const gateway = S.LINES[0].slice(0, gatewaySize).sort((a, b) => a - b);
  const gwPos = new Map(gateway.map((p, i) => [p, i]));
  const adj = Array.from({ length: N2 }, () => []);
  for (let c = 0; c < N1; c++) {
    for (let p = 0; p < N1; p++) {
      const v = idx(c, p);
      for (const q of S.ADJ[p]) adj[v].push(idx(c, q));
      if (gwPos.has(p)) {
        for (const d of S.ADJ[c]) adj[v].push(idx(d, p));    // gateway to gateway
      }
    }
  }
  return adj;
}

// ---------------------------------------------------------------------
// exact invariants
// ---------------------------------------------------------------------

function degrees(adj) {
  const d = adj.map((r) => r.length);
  return { min: Math.min(...d), max: Math.max(...d), regular: Math.min(...d) === Math.max(...d) };
}

/** BFS eccentricity from every vertex: exact diameter, not a bound. */
function diameter(adj) {
  const n = adj.length;
  let diam = 0;
  const dist = new Int32Array(n);
  const queue = new Int32Array(n);
  for (let s = 0; s < n; s++) {
    dist.fill(-1);
    let head = 0, tail = 0;
    dist[s] = 0; queue[tail++] = s;
    let ecc = 0;
    while (head < tail) {
      const u = queue[head++];
      for (const w of adj[u]) {
        if (dist[w] === -1) { dist[w] = dist[u] + 1; if (dist[w] > ecc) ecc = dist[w]; queue[tail++] = w; }
      }
    }
    if (tail < n) return { diameter: Infinity, connected: false };
    if (ecc > diam) diam = ecc;
  }
  return { diameter: diam, connected: true };
}

/**
 * Closed-form spectra.
 *
 * For a regular G on n vertices with spectrum {lambda} and H on m with
 * spectrum {mu} and degree k_H:
 *
 *   Cartesian      spec(G [] H) = { lambda + mu }, all pairs
 *   Lexicographic  spec(G[H])   = { m*lambda + k_H }  from the all-ones
 *                                 part of H, plus each mu != k_H with
 *                                 multiplicity n times its own
 *
 * Both are standard; they are stated here so the numeric check below has
 * something to disagree with.
 */
function cartesianSpectrumClosedForm() {
  const spec1 = [[12, 1], [2, 24], [-4, 15]];
  const out = new Map();
  for (const [a, ma] of spec1) {
    for (const [b, mb] of spec1) {
      const e = a + b;
      out.set(e, (out.get(e) || 0) + ma * mb);
    }
  }
  return [...out.entries()].sort((x, y) => y[0] - x[0]);
}

function lexicographicSpectrumClosedForm() {
  const spec1 = [[12, 1], [2, 24], [-4, 15]];
  const out = new Map();
  for (const [lam, m] of spec1) {                     // from y = all-ones
    const e = N1 * lam + K1;
    out.set(e, (out.get(e) || 0) + m);
  }
  for (const [mu, m] of spec1) {                      // from y orthogonal to 1
    if (mu === K1) continue;
    out.set(mu, (out.get(mu) || 0) + N1 * m);
  }
  return [...out.entries()].sort((x, y) => y[0] - x[0]);
}

/**
 * Spectral edge-boundary bounds for a k-regular graph, from the second
 * largest and the least eigenvalue. These are the same bounds the
 * level-1 analysis uses; the point of computing them here is the RATIO
 * (k - lambda_2)/k, which is what actually says how good the fabric is.
 */
function spectralBounds(k, lambda2, lambdaMin, n) {
  return {
    degree: k,
    lambda2,
    lambdaMin,
    // b(T) >= (k - lambda_2) * m(n-m)/n   and   <= (k - lambda_min) * m(n-m)/n
    lowerCoefficient: k - lambda2,
    upperCoefficient: k - lambdaMin,
    // normalised expansion: how much of the degree survives as boundary
    expansionRatio: (k - lambda2) / k,
    balancedBisectionLowerBound: ((k - lambda2) * (n / 2) * (n / 2)) / n,
  };
}

/** Edges crossing an explicit balanced cut, to test the bound. */
function cutSize(adj, leftSet) {
  const L = leftSet instanceof Set ? leftSet : new Set(leftSet);
  let cross = 0;
  for (const v of L) for (const w of adj[v]) if (!L.has(w)) cross++;
  return cross;
}

// ---------------------------------------------------------------------
function analyse(name, adj, closedForm, note) {
  const deg = degrees(adj);
  const edges = adj.reduce((a, r) => a + r.length, 0) / 2;
  const dia = diameter(adj);

  let bounds = null;
  if (closedForm && deg.regular) {
    const sorted = closedForm.slice().sort((a, b) => b[0] - a[0]);
    const k = sorted[0][0];
    const lambda2 = sorted[0][1] > 1 ? sorted[0][0] : sorted[1][0];
    const lambdaMin = sorted[sorted.length - 1][0];
    bounds = spectralBounds(k, lambda2, lambdaMin, N2);
    bounds.degreeMatchesGraph = k === deg.max;
    bounds.multiplicitiesSumToN = closedForm.reduce((a, [, m]) => a + m, 0) === N2;
  }

  // a natural balanced cut: split by cell, using the level-1 certified
  // bisection to choose which cells go left
  const cert = S.bisectionCertificate();
  const leftCells = new Set(cert.left);
  const left = [];
  for (let v = 0; v < N2; v++) if (leftCells.has(cellOf(v))) left.push(v);
  const cut = cutSize(adj, left);

  return {
    name, note,
    vertices: N2,
    edges,
    degree: deg,
    diameter: dia.diameter,
    connected: dia.connected,
    spectrumClosedForm: closedForm,
    spectralBounds: bounds,
    cellSplitCut: {
      leftSize: left.length,
      crossingEdges: cut,
      description: "cells split by the certified level-1 20|20 bisection",
      spectralLowerBound: bounds ? Math.round(bounds.balancedBisectionLowerBound) : null,
      meetsLowerBound: bounds ? cut >= bounds.balancedBisectionLowerBound - 1e-9 : null,
    },
  };
}

function run() {
  const results = [];

  results.push(analyse("cartesian", buildCartesian(), cartesianSpectrumClosedForm(),
    "homogeneous: every leaf keeps 12 intra-cell links and gains one per neighbouring cell"));

  results.push(analyse("lexicographic", buildLexicographic(), lexicographicSpectrumClosedForm(),
    "adjacent cells fully meshed; diameter 2 at any level, quadratic wiring"));

  const hier = buildHierarchical(4);
  results.push(analyse("hierarchical-gateway-4", hier, null,
    "inter-cell traffic funnels through one 4-point line per cell; matches the software's distance model"));

  // what the software's distance formula says, for comparison
  const softwareBound = S.diameterAtLevel(2);

  const result = {
    schema: "holotrade.w33-level2.v1",
    question: "the recursive layer is a distance formula; what is it as an actual graph?",
    leafCount: N2,
    softwareDistanceBound: softwareBound,
    softwareModel: "route in the first divergent cell, then 8 moves per descent on each side: 16n - 14",
    constructions: results,
  };
  result.digest = crypto.createHash("sha256")
    .update(JSON.stringify(results.map((r) => ({ n: r.name, d: r.diameter, e: r.edges })))).digest("hex");
  return result;
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  L("W(3,3) AT LEVEL 2 — THE INTER-CELL FABRIC AS AN ACTUAL GRAPH");
  L("=".repeat(78));
  L(`  ${res.leafCount} leaves.  The software's distance formula bounds the diameter at `
    + `${res.softwareDistanceBound}; it is a bound on a model, not a graph invariant.`);
  L("");
  L("  construction              degree   edges     diameter   expansion   cell-split cut");
  for (const r of res.constructions) {
    const d = r.degree.regular ? String(r.degree.max) : `${r.degree.min}-${r.degree.max}`;
    const exp = r.spectralBounds ? r.spectralBounds.expansionRatio.toFixed(4) : "   —  ";
    L(`  ${r.name.padEnd(24)} ${d.padStart(6)}   ${String(r.edges).padStart(6)}   `
      + `${String(r.diameter).padStart(8)}   ${exp.padStart(9)}   ${String(r.cellSplitCut.crossingEdges).padStart(8)}`);
  }
  L("");
  for (const r of res.constructions) {
    if (!r.spectrumClosedForm) continue;
    L(`  ${r.name} spectrum (closed form): `
      + r.spectrumClosedForm.map(([e, m]) => `${e}^${m}`).join("  "));
  }
  L("");
  L("  EXPANSION IS THE NUMBER THAT MATTERS");
  const l1 = (12 - 2) / 12;
  L(`    level 1 W(3,3):        (k - lambda_2)/k = (12-2)/12 = ${l1.toFixed(4)}`);
  for (const r of res.constructions) {
    if (!r.spectralBounds) continue;
    const b = r.spectralBounds;
    L(`    ${r.name.padEnd(20)} (${b.degree}-${b.lambda2})/${b.degree} = ${b.expansionRatio.toFixed(4)}`
      + (b.expansionRatio < l1 ? "   <-- worse than one cell" : ""));
  }

  if (process.argv.includes("--write")) {
    const out = path.resolve(__dirname, "../data/w33_level2.json");
    fs.writeFileSync(out, JSON.stringify(res, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
}

module.exports = {
  buildCartesian, buildLexicographic, buildHierarchical,
  degrees, diameter, cutSize, cellOf, pointOf, idx,
  cartesianSpectrumClosedForm, lexicographicSpectrumClosedForm, spectralBounds, run,
};
