"use strict";

// Microstate-aware migration advice for the 2,880 optimal W33 near-ovoids.
//
// The current four-node line scheduler sees only the oriented defect pair
// (a,c): all six m-microstates have the same three free lines.  They are not
// operationally identical under a release/migration, however.  This module
// extracts the exact one-release signature from the actual busy 10-set.

const S = require("../js/substrate.js");

const lineSets = S.LINES.map((L) => new Set(L));

function lineOccupancies(busy) {
  const B = new Set(busy);
  return S.LINES.map((L) => L.reduce((n, p) => n + (B.has(p) ? 1 : 0), 0));
}

function commonPoint(lineIds) {
  if (!lineIds.length) return null;
  let C = new Set(S.LINES[lineIds[0]]);
  for (const li of lineIds.slice(1)) C = new Set([...C].filter((p) => lineSets[li].has(p)));
  return C.size === 1 ? [...C][0] : null;
}

function freeLineIds(busy) {
  const B = new Set(busy);
  const out = [];
  for (let li = 0; li < S.LINES.length; li++) {
    if (!S.LINES[li].some((p) => B.has(p))) out.push(li);
  }
  return out;
}

/**
 * Analyze an optimal ten-point near-ovoid busy state.
 *
 * Returns null for a set that is not of the certified 0^3 1^34 2^3 form.
 * `highRelease` are the four busy points whose release opens seven lines;
 * releasing any of the other six opens exactly six.
 */
function analyzeNearOvoid(busy) {
  const B = [...new Set(busy)].sort((a, b) => a - b);
  if (B.length !== 10) return null;
  const occ = lineOccupancies(B);
  const free = [], doubled = [];
  for (let li = 0; li < occ.length; li++) {
    if (occ[li] === 0) free.push(li);
    else if (occ[li] === 2) doubled.push(li);
    else if (occ[li] !== 1) return null;
  }
  if (free.length !== 3 || doubled.length !== 3) return null;

  const a = commonPoint(free);
  const c = commonPoint(doubled);
  if (a === null || c === null || a === c || !S.isAdjacent(a, c)) return null;
  const hinge = S.LINES.findIndex((L) => L.includes(a) && L.includes(c));
  if (hinge < 0 || occ[hinge] !== 1) return null;

  const highRelease = [], ordinaryRelease = [];
  const projected = {};
  for (const y of B) {
    const after = B.filter((x) => x !== y);
    const nfree = freeLineIds(after).length;
    projected[y] = nfree;
    if (nfree === 7) highRelease.push(y);
    else if (nfree === 6) ordinaryRelease.push(y);
    else return null;
  }
  if (highRelease.length !== 4 || ordinaryRelease.length !== 6) return null;

  return {
    defectCenter: a,
    blockerCenter: c,
    hingeLine: hinge,
    freeLines: free,
    doubledLines: doubled,
    highRelease,
    ordinaryRelease,
    projectedFreeLinesAfterRelease: projected,
    microstateSignature: highRelease.join(","),
    recommendation: highRelease.slice(),
    guaranteeAfterRecommendedRelease: 7,
    guaranteeAfterOrdinaryRelease: 6,
  };
}

module.exports = {
  freeLineIds,
  lineOccupancies,
  analyzeNearOvoid,
};
