"use strict";

// Complete inclusion-minimal transversal atlas of the 40 W(3,3) lines.
//
// Incremental hypergraph transversal construction is exact: after processing
// each line, `family` is minimized under set inclusion.  At completion every
// member is an inclusion-minimal point set intersecting all 40 lines and every
// inclusion-minimal blocker occurs.  This gives a closed-form failure distance
// for any observed failure set F:
//
//   d(F) = min_{B in MINIMAL_BLOCKERS} |B \ F|.
//
// Proof: adding B\F reaches the blocker B. Conversely any completion A for
// which F∪A blocks all lines contains an inclusion-minimal blocker B, hence
// B\F ⊆ A and |B\F| <= |A|.

const R = require("./w33-topology-resilience.js");
const SCHEMA = "holotrade.w33-minimal-blocker-atlas.v1";

function key(xs) { return xs.join(","); }
function subset(a, bSet) { return a.every((x) => bSet.has(x)); }
function intersects(a, bSet) { return a.some((x) => bSet.has(x)); }

function minimizeFamily(raw) {
  const dedup = new Map();
  for (const row of raw) {
    const s = [...new Set(row)].sort((a, b) => a - b);
    dedup.set(key(s), s);
  }
  const ordered = [...dedup.values()].sort((a, b) => a.length - b.length || key(a).localeCompare(key(b)));
  const kept = [];
  for (const s of ordered) {
    const sSet = new Set(s);
    if (kept.some((k) => subset(k, sSet))) continue;
    kept.push(s);
  }
  return kept;
}

function enumerateMinimalBlockers() {
  let family = [[]];
  for (const line of R.GEOMETRY.lines) {
    const lineSet = new Set(line);
    const next = [];
    for (const T of family) {
      if (intersects(T, lineSet)) next.push(T);
      else for (const p of line) next.push([...T, p]);
    }
    family = minimizeFamily(next);
    if (family.length > 250000) throw new Error("minimal-transversal family exceeded deterministic safety bound");
  }
  return Object.freeze(family.map((x) => Object.freeze(x)));
}

const MINIMAL_BLOCKERS = enumerateMinimalBlockers();

function hitsAllLines(points) {
  const s = new Set(points);
  return R.GEOMETRY.lines.every((line) => line.some((p) => s.has(p)));
}
function inclusionMinimal(points) {
  if (!hitsAllLines(points)) return false;
  return points.every((p) => !hitsAllLines(points.filter((q) => q !== p)));
}
function neighborhoodCenter(points) {
  const k = key(points);
  for (let c = 0; c < 40; c++) {
    const n = [...R.GEOMETRY.adjacency[c]].sort((a, b) => a - b);
    if (key(n) === k) return c;
  }
  return null;
}

const CLASSIFIED = Object.freeze(MINIMAL_BLOCKERS.map((points, index) => {
  const center = points.length === 12 ? neighborhoodCenter(points) : null;
  const type = points.length === 11 ? "minimum-11" : center != null ? "neighborhood-12" : "other";
  return Object.freeze({ index, points, size: points.length, type, neighborhoodCenter: center });
}));

function distanceViaAtlas(rawFailed) {
  const failed = R.normalizePointSet(rawFailed, "failurePoints");
  const F = new Set(failed);
  let best = null;
  for (const row of CLASSIFIED) {
    const add = row.points.filter((p) => !F.has(p));
    if (!best || add.length < best.distance || (add.length === best.distance && key(add) < key(best.witnessAdditionalFailures))) {
      best = {
        schema: "holotrade.w33-failure-distance-atlas.v1",
        distance: add.length,
        witnessAdditionalFailures: Object.freeze(add),
        nearestMinimalBlockerIndex: row.index,
        nearestMinimalBlockerSize: row.size,
        nearestMinimalBlockerType: row.type,
        nearestNeighborhoodCenter: row.neighborhoodCenter,
        exact: true,
      };
    }
  }
  if (!best) throw new Error("empty minimal blocker atlas");
  const completed = [...failed, ...best.witnessAdditionalFailures];
  if (!R.assessFailures(completed).allLinesHit) throw new Error("atlas distance witness does not block all lines");
  return Object.freeze(best);
}

function verifyAtlas() {
  const sizes = new Map();
  for (const row of CLASSIFIED) sizes.set(row.size, (sizes.get(row.size) || 0) + 1);
  const neighborhoodRows = CLASSIFIED.filter((x) => x.type === "neighborhood-12");
  const checks = {
    exactly_400_inclusion_minimal_blockers: CLASSIFIED.length === 400,
    exact_size_histogram_360_plus_40: sizes.get(11) === 360 && sizes.get(12) === 40 && sizes.size === 2,
    every_template_hits_all_40_lines: CLASSIFIED.every((x) => hitsAllLines(x.points)),
    every_template_is_inclusion_minimal: CLASSIFIED.every((x) => inclusionMinimal(x.points)),
    all_size12_templates_are_the_40_neighborhoods: neighborhoodRows.length === 40 && new Set(neighborhoodRows.map((x) => x.neighborhoodCenter)).size === 40,
    no_unclassified_template_remains: CLASSIFIED.every((x) => x.type !== "other"),
    empty_failure_distance_is_11: distanceViaAtlas([]).distance === 11,
  };
  return Object.freeze({
    schema: SCHEMA,
    status: Object.values(checks).every(Boolean) ? "PASS" : "FAIL",
    checks: Object.freeze(checks),
    blockerCount: CLASSIFIED.length,
    sizeHistogram: Object.freeze(Object.fromEntries([...sizes.entries()].sort((a, b) => a[0] - b[0]))),
    theorem: "The complete inclusion-minimal transversal family of the 40 W33 lines consists of exactly 360 size-11 blockers and the 40 size-12 point neighborhoods. Therefore failure distance for every subset F of the 40 points is min_B |B\\F| over these 400 templates.",
    boundary: "Exact finite W(3,3) combinatorics. Distance counts additional point failures to the line-blocking veto; it is not a stochastic failure probability, hardware reliability measurement, or physical correlation model.",
  });
}

module.exports = { SCHEMA, MINIMAL_BLOCKERS, CLASSIFIED, enumerateMinimalBlockers, distanceViaAtlas, verifyAtlas };
