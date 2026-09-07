"use strict";

// Exact W(3,3) correlated-failure assessment for continuation scheduling.
//
// Safety rule: if the observed failed-point set intersects every one of the 40
// W33 lines, no intact 4-point W33 line remains. Such a worker is rejected when
// line resilience is required. This strictly subsumes checking only the recent
// 10,480 size-12 blocker census and also catches the 360 minimum size-11
// blockers. When exactly 12 failed points block every line, the unique
// two-pencil excess pair is recovered and classified as equal/collinear/
// noncollinear, matching the exact Holotrade census theorem.

const SCHEMA = "holotrade.w33-topology-resilience.v1";
const Q = 3;

function mod3(x) { x %= 3; return x < 0 ? x + 3 : x; }
function key(v) { return v.join(","); }
function norm(v) {
  const i = v.findIndex((x) => mod3(x) !== 0);
  if (i < 0) throw new Error("zero projective vector");
  const scale = mod3(v[i]) === 1 ? 1 : 2;
  return v.map((x) => mod3(scale * x));
}
function form(u, v) {
  return mod3(u[0] * v[2] - u[2] * v[0] + u[1] * v[3] - u[3] * v[1]);
}

function buildGeometry() {
  const seen = new Map();
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) for (let c = 0; c < 3; c++) for (let d = 0; d < 3; d++) {
    if (!(a || b || c || d)) continue;
    const p = norm([a, b, c, d]); seen.set(key(p), p);
  }
  const points = [...seen.values()].sort((x, y) => key(x).localeCompare(key(y)));
  if (points.length !== 40) throw new Error("W33 must have 40 projective points");
  const pidx = new Map(points.map((p, i) => [key(p), i]));
  const lineMap = new Map();
  for (let a = 0; a < 40; a++) for (let b = a + 1; b < 40; b++) {
    if (form(points[a], points[b]) !== 0) continue;
    const span = new Set();
    for (let x = 0; x < 3; x++) for (let y = 0; y < 3; y++) {
      if (!(x || y)) continue;
      const w = norm(points[a].map((_, k) => mod3(x * points[a][k] + y * points[b][k])));
      span.add(pidx.get(key(w)));
    }
    if (span.size === 4) {
      const line = [...span].sort((x, y) => x - y);
      lineMap.set(line.join(","), line);
    }
  }
  const lines = [...lineMap.values()].sort((x, y) => x.join(",").localeCompare(y.join(",")));
  if (lines.length !== 40) throw new Error("W33 must have 40 lines");
  const adjacency = Array.from({ length: 40 }, () => new Set());
  for (const line of lines) for (const p of line) for (const q of line) if (p !== q) adjacency[p].add(q);
  if (!adjacency.every((s) => s.size === 12)) throw new Error("W33 point degree must be 12");
  const incidence = lines.map((line) => Array.from({ length: 40 }, (_, p) => line.includes(p) ? 1 : 0));
  return Object.freeze({ points, lines, adjacency, incidence });
}

const GEOMETRY = buildGeometry();

function normalizePointSet(points, name = "points") {
  if (!Array.isArray(points)) throw new TypeError(`${name} must be an array`);
  const out = [...points];
  for (const p of out) if (!Number.isInteger(p) || p < 0 || p >= 40) throw new RangeError(`${name} contains point outside 0..39`);
  if (new Set(out).size !== out.length) throw new RangeError(`${name} must not contain duplicates`);
  return Object.freeze(out.sort((a, b) => a - b));
}

function classifyTwelvePointBlocker(failed, lineCounts) {
  if (failed.length !== 12 || !lineCounts.every((x) => x >= 1)) return null;
  const excess = lineCounts.map((x) => x - 1);
  if (excess.reduce((a, b) => a + b, 0) !== 8) throw new Error("size-12 blocker must have excess mass 8");
  const matches = [];
  for (let a = 0; a < 40; a++) for (let b = a; b < 40; b++) {
    let ok = true;
    for (let i = 0; i < 40; i++) {
      if (GEOMETRY.incidence[i][a] + GEOMETRY.incidence[i][b] !== excess[i]) { ok = false; break; }
    }
    if (ok) matches.push([a, b]);
  }
  if (matches.length !== 1) throw new Error("12-point blocker did not recover unique two-pencil pair");
  const [a, b] = matches[0];
  const pairType = a === b ? "equal" : GEOMETRY.adjacency[a].has(b) ? "collinear" : "noncollinear";
  const expectedSupports = pairType === "equal" ? 10 : pairType === "collinear" ? 6 : 16;
  return Object.freeze({ pair: Object.freeze([a, b]), pairType, expectedSupportsForFixedPair: expectedSupports });
}

function assessFailures(rawFailed) {
  const failed = normalizePointSet(rawFailed, "failurePoints");
  const failedSet = new Set(failed);
  const lineCounts = GEOMETRY.lines.map((line) => line.reduce((n, p) => n + (failedSet.has(p) ? 1 : 0), 0));
  const intactLineIndices = lineCounts.map((x, i) => x === 0 ? i : -1).filter((i) => i >= 0);
  const allLinesHit = intactLineIndices.length === 0;
  const classification = classifyTwelvePointBlocker(failed, lineCounts);
  return Object.freeze({
    schema: SCHEMA,
    failurePoints: failed,
    failureCount: failed.length,
    lineCounts: Object.freeze(lineCounts),
    intactLineIndices: Object.freeze(intactLineIndices),
    intactLineCount: intactLineIndices.length,
    allLinesHit,
    twelvePointBlocker: classification,
    code: allLinesHit ? "W33_ALL_LINES_HIT" : "W33_INTACT_LINE_REMAINS",
  });
}

module.exports = {
  SCHEMA,
  GEOMETRY,
  normalizePointSet,
  classifyTwelvePointBlocker,
  assessFailures,
};
