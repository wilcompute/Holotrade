"use strict";

// Independent branch-and-bound set-cover oracle retained to cross-check the
// closed-form minimal-blocker atlas implementation.

const R = require("./w33-topology-resilience.js");
const SCHEMA = "holotrade.w33-failure-distance-search.v1";

function popcountBigInt(x) {
  let n = 0;
  while (x) { x &= x - 1n; n += 1; }
  return n;
}

function exactFailureDistanceSearch(rawFailed) {
  const base = R.assessFailures(rawFailed);
  if (base.allLinesHit) return Object.freeze({ schema: SCHEMA, distance: 0, witnessAdditionalFailures: Object.freeze([]), exact: true, intactLineCount: 0 });
  const failed = new Set(base.failurePoints);
  const intact = base.intactLineIndices;
  const linePosition = new Map(intact.map((lineIndex, i) => [lineIndex, i]));
  const full = (1n << BigInt(intact.length)) - 1n;
  const rawCandidates = [];
  for (let p = 0; p < 40; p++) {
    if (failed.has(p)) continue;
    let mask = 0n;
    for (const li of intact) if (R.GEOMETRY.lines[li].includes(p)) mask |= 1n << BigInt(linePosition.get(li));
    if (mask) rawCandidates.push({ point: p, mask });
  }
  const candidates = rawCandidates.filter((a, i, all) => !all.some((b, j) => {
    if (i === j) return false;
    const subset = (a.mask | b.mask) === b.mask;
    return subset && (a.mask !== b.mask || b.point < a.point);
  })).sort((a, b) => a.point - b.point);
  const byBit = Array.from({ length: intact.length }, () => []);
  for (const c of candidates) for (let bit = 0; bit < intact.length; bit++) if (c.mask & (1n << BigInt(bit))) byBit[bit].push(c);
  if (byBit.some((xs) => xs.length === 0)) throw new Error("intact W33 line has no available failure point");
  function greedyUpper() {
    let rem = full; const witness = [];
    while (rem) {
      let best = null; let cover = -1;
      for (const c of candidates) {
        const k = popcountBigInt(c.mask & rem);
        if (k > cover) { best = c; cover = k; }
      }
      if (!best || cover <= 0) throw new Error("greedy cover stalled");
      witness.push(best.point); rem &= ~best.mask;
    }
    return witness;
  }
  function lowerBound(rem) {
    const uncovered = popcountBigInt(rem);
    let maxCover = 1;
    for (const c of candidates) maxCover = Math.max(maxCover, popcountBigInt(c.mask & rem));
    let bound = Math.ceil(uncovered / maxCover);
    const used = new Set(); let packing = 0;
    for (let bit = 0; bit < intact.length; bit++) {
      if (!(rem & (1n << BigInt(bit)))) continue;
      const line = R.GEOMETRY.lines[intact[bit]];
      if (line.every((p) => !used.has(p))) { packing += 1; for (const p of line) used.add(p); }
    }
    return Math.max(bound, packing);
  }
  function chooseBit(rem) {
    let bestBit = -1; let bestChoices = Infinity;
    for (let bit = 0; bit < intact.length; bit++) {
      if (!(rem & (1n << BigInt(bit)))) continue;
      let n = 0;
      for (const c of byBit[bit]) if (c.mask & rem) n += 1;
      if (n < bestChoices) { bestChoices = n; bestBit = bit; }
    }
    return bestBit;
  }
  const greedy = greedyUpper();
  const memo = new Map();
  function search(rem, depth) {
    if (rem === 0n) return [];
    if (depth <= 0 || lowerBound(rem) > depth) return null;
    const key = rem.toString();
    const failedDepth = memo.get(key);
    if (failedDepth != null && failedDepth >= depth) return null;
    const bit = chooseBit(rem);
    const choices = byBit[bit].filter((c) => c.mask & rem).sort((a, b) => popcountBigInt(b.mask & rem) - popcountBigInt(a.mask & rem) || a.point - b.point);
    for (const c of choices) {
      const tail = search(rem & ~c.mask, depth - 1);
      if (tail) return [c.point, ...tail];
    }
    memo.set(key, Math.max(depth, failedDepth ?? -1));
    return null;
  }
  let witness = null; const lo = lowerBound(full);
  for (let d = lo; d <= greedy.length; d++) { memo.clear(); witness = search(full, d); if (witness) break; }
  if (!witness) throw new Error("exact W33 failure-distance search found no cover");
  if (!R.assessFailures([...base.failurePoints, ...witness]).allLinesHit) throw new Error("distance witness does not hit all W33 lines");
  return Object.freeze({ schema: SCHEMA, distance: witness.length, witnessAdditionalFailures: Object.freeze([...witness].sort((a, b) => a - b)), exact: true, intactLineCount: intact.length, searchLowerBound: lo, greedyUpperBound: greedy.length });
}

module.exports = { SCHEMA, popcountBigInt, exactFailureDistanceSearch };
