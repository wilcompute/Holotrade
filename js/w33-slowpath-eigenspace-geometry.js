// Direct matrix decoder for the 45 slow-path geometric labels.
//
// For every certified slow target g in PSp(4,3), ker(g-I) and ker(g+I) are
// complementary nondegenerate 2-spaces. Their projective points are the two
// center-quads, and their 8-point union is the target's C2(W33) minimum word /
// eight compatible Payne staging axes. The frozen 45-row dictionary is used
// only as a boot-time cross-check; decode() derives its answer from the matrix.
"use strict";

const minwords = require("../data/slow_targets_are_w33_minimum_words.json");
const rom = require("../data/the_45_slot_rom_bijection.json");

const Q = 3;
const D = 4;
function mod(x) { const y = x % Q; return y < 0 ? y + Q : y; }
function symplectic(a, b) { return mod(a[0] * b[2] - a[2] * b[0] + a[1] * b[3] - a[3] * b[1]); }
function vectorKey(v) { return v.join(""); }
function canonAxis(v) {
  const i = v.findIndex((x) => mod(x) !== 0);
  if (i < 0) throw new Error("zero vector has no projective axis");
  const z = mod(v[i]) === 1 ? 1 : 2;
  return v.map((x) => mod(z * x));
}
function buildAxes() {
  const m = new Map();
  for (let n = 1; n < 81; n += 1) {
    const v = [n % 3, Math.floor(n / 3) % 3, Math.floor(n / 9) % 3, Math.floor(n / 27) % 3];
    const c = canonAxis(v); m.set(vectorKey(c), c);
  }
  return [...m.values()].sort((a, b) => vectorKey(a).localeCompare(vectorKey(b)));
}
const AXES = buildAxes();
const AXIS_INDEX = new Map(AXES.map((v, i) => [vectorKey(v), i]));

function rrefKernel(A) {
  const M = A.map((r) => r.map(mod));
  const pivots = []; let r = 0;
  for (let c = 0; c < D; c += 1) {
    let p = r; while (p < D && M[p][c] === 0) p += 1;
    if (p === D) continue;
    [M[r], M[p]] = [M[p], M[r]];
    const inv = M[r][c] === 1 ? 1 : 2;
    M[r] = M[r].map((x) => mod(inv * x));
    for (let i = 0; i < D; i += 1) if (i !== r && M[i][c] !== 0) {
      const z = M[i][c]; M[i] = M[i].map((x, j) => mod(x - z * M[r][j]));
    }
    pivots.push(c); r += 1;
  }
  const free = Array.from({ length: D }, (_, i) => i).filter((c) => !pivots.includes(c));
  return free.map((f) => {
    const v = Array(D).fill(0); v[f] = 1;
    pivots.forEach((c, i) => { v[c] = mod(-M[i][f]); });
    return v;
  });
}

function eigenspaceAxes(matrix, eigenvalue) {
  if (!Array.isArray(matrix) || matrix.length !== D || matrix.some((r) => !Array.isArray(r) || r.length !== D)) throw new TypeError("target must be a 4x4 matrix");
  const K = matrix.map((row, i) => row.map((x, j) => mod(x - (i === j ? eigenvalue : 0))));
  const basis = rrefKernel(K);
  if (basis.length !== 2) throw new Error(`slow target eigenspace dimension ${basis.length} != 2`);
  const pts = new Map();
  for (let a = 0; a < Q; a += 1) for (let b = 0; b < Q; b += 1) {
    if (a === 0 && b === 0) continue;
    const v = canonAxis(Array.from({ length: D }, (_, j) => mod(a * basis[0][j] + b * basis[1][j])));
    pts.set(vectorKey(v), v);
  }
  if (pts.size !== 4) throw new Error(`slow target projective eigenspace size ${pts.size} != 4`);
  const axes = [...pts.values()].map((v) => {
    const i = AXIS_INDEX.get(vectorKey(v)); if (i === undefined) throw new Error("eigenspace point absent from W33 axis order"); return i;
  }).sort((a, b) => a - b);
  return { basis, axes };
}

function sortedPair(a, b) {
  const A = [...a].sort((x, y) => x - y); const B = [...b].sort((x, y) => x - y);
  const ka = A.join(","), kb = B.join(","); return ka <= kb ? [A, B] : [B, A];
}
function axisDistance(a, b) {
  if (a === b) return 0;
  return symplectic(AXES[a], AXES[b]) === 0 ? 1 : 2;
}

function geometryFromMatrix(matrix) {
  const plus = eigenspaceAxes(matrix, 1);
  const minus = eigenspaceAxes(matrix, Q - 1);
  const pair = sortedPair(plus.axes, minus.axes);
  const support = [...new Set([...plus.axes, ...minus.axes])].sort((a, b) => a - b);
  if (support.length !== 8) throw new Error("slow target eigenspaces do not give 8 distinct W33 axes");
  if (symplectic(plus.basis[0], plus.basis[1]) === 0 || symplectic(minus.basis[0], minus.basis[1]) === 0) throw new Error("slow target eigenspace is degenerate");
  if (!plus.basis.every((u) => minus.basis.every((v) => symplectic(u, v) === 0))) throw new Error("slow target eigenspaces are not perpendicular");
  return Object.freeze({
    payneCoverAxes: Object.freeze([...support]),
    weight8Support: Object.freeze([...support]),
    centerQuadPair: Object.freeze(pair.map((q) => Object.freeze([...q]))),
    plusAxes: Object.freeze([...plus.axes]),
    minusAxes: Object.freeze([...minus.axes]),
    codeLabel: "C2(W33)[40,16,8]_MINIMUM_WORD",
    derivation: "KER_G_MINUS_I_PLUS_KER_G_PLUS_I",
    priorE8Label: "SELECTED_D4_PERP_D4",
    e8Evidence: "REPO_PRIOR_WORK_NOT_REDERIVED_HERE",
  });
}

function stageFromMatrix(matrix, currentAxis = null) {
  const geometry = geometryFromMatrix(matrix); const choices = geometry.payneCoverAxes;
  if (currentAxis === null || currentAxis === undefined) return Object.freeze({ chosenAxis: choices[0], routeDistance: null, role: "NEW_HYPERBOLIC_LINE", candidateAxes: choices });
  if (!Number.isInteger(currentAxis) || currentAxis < 0 || currentAxis >= 40) throw new RangeError("currentAxis must be 0..39");
  const chosenAxis = [...choices].sort((a, b) => axisDistance(currentAxis, a) - axisDistance(currentAxis, b) || a - b)[0];
  const routeDistance = axisDistance(currentAxis, chosenAxis);
  if (routeDistance > 1) throw new Error("direct eigenspace staging escaped proved one-hop bound");
  return Object.freeze({ currentAxis, chosenAxis, routeDistance, role: "NEW_HYPERBOLIC_LINE", candidateAxes: choices });
}

function bootCheck() {
  const errors = [];
  if (!minwords || minwords.status !== "PASS") errors.push("MINWORD_CERT");
  const rows = Array.isArray(rom.table) ? [...rom.table].sort((a, b) => a.slot - b.slot) : [];
  if (rows.length !== 45) errors.push("ROM_TABLE_NOT_45");
  for (const row of rows) {
    try {
      const g = geometryFromMatrix(row.spMatrix); const want = minwords.dictionary[String(row.slot)];
      if (!want) { errors.push(`NO_MINWORD_${row.slot}`); continue; }
      if (JSON.stringify(g.weight8Support) !== JSON.stringify([...want.weight8Support].sort((a, b) => a - b))) errors.push(`SUPPORT_${row.slot}`);
      const wp = [...want.centerQuadPair].map((q) => [...q].sort((a, b) => a - b)).sort((a, b) => a.join(",").localeCompare(b.join(",")));
      if (JSON.stringify(g.centerQuadPair) !== JSON.stringify(wp)) errors.push(`PAIR_${row.slot}`);
      for (let currentAxis = 0; currentAxis < 40; currentAxis += 1) if (stageFromMatrix(row.spMatrix, currentAxis).routeDistance > 1) errors.push(`RADIUS_${row.slot}_${currentAxis}`);
    } catch (e) { errors.push(`SLOT_${row.slot}_${e.message}`); }
  }
  return Object.freeze({ ok: errors.length === 0, errors: Object.freeze(errors) });
}

module.exports = { AXES, axisDistance, bootCheck, eigenspaceAxes, geometryFromMatrix, stageFromMatrix, symplectic };
