"use strict";

// Production-facing level-1 W33 migration selector.
//
// IMPORTANT: legacy remains the default.  The topology-aware policy is opt-in
// and changes only equal-cost tie-breaking after the same primary movement
// objective (rays, then hops).  `failed` points are unavailable destinations
// and count against line headroom.  `destinationScore`, when supplied, is a
// final secondary tie-break only after movement and topology scores are equal.

const S = require("../js/substrate.js");
const M = require("./w33-near-ovoid-migration.js");

const POLICY = Object.freeze({
  LEGACY: "legacy",
  TOPOLOGY_AWARE: "topology-aware",
});

function normalizePolicy(policy = POLICY.LEGACY) {
  if (policy == null || policy === "") return POLICY.LEGACY;
  if (policy !== POLICY.LEGACY && policy !== POLICY.TOPOLOGY_AWARE) {
    throw new RangeError(`unknown W33 migration policy: ${policy}`);
  }
  return policy;
}

function sortedUnique(xs) {
  return [...new Set(xs)].sort((a, b) => a - b);
}

function moveState(busy, from, to) {
  const B = new Set(busy);
  if (!B.has(from)) throw new RangeError("migration source is not busy");
  if (B.has(to)) throw new RangeError("migration destination is already busy");
  B.delete(from);
  B.add(to);
  return [...B].sort((a, b) => a - b);
}

function freeLineCount(busy, failed = []) {
  const unavailable = new Set([...busy, ...failed]);
  return S.LINES.filter((L) => !L.some((p) => unavailable.has(p))).length;
}

function chooseMigration(busy, opts = {}) {
  const policy = normalizePolicy(opts.policy);
  const failed = sortedUnique(opts.failed || []);
  const destinationScore = typeof opts.destinationScore === "function"
    ? opts.destinationScore
    : null;

  const B = sortedUnique(busy);
  if (!B.length) throw new RangeError("busy set must be non-empty");
  const busySet = new Set(B);
  const failedSet = new Set(failed);
  if (failed.some((p) => busySet.has(p))) {
    throw new RangeError("failed points must be separate from busy workloads");
  }

  const info = policy === POLICY.TOPOLOGY_AWARE ? M.analyzeNearOvoid(B) : null;
  const sources = info ? info.highRelease : B;
  const idle = Array.from({ length: S.CONST.points }, (_, i) => i)
    .filter((p) => !busySet.has(p) && !failedSet.has(p));
  if (!idle.length) throw new Error("no healthy idle migration destination");

  let bestRays = Infinity;
  let bestHops = Infinity;
  let candidates = [];
  for (const from of sources) {
    for (const to of idle) {
      const rays = S.migrationRays(from, to);
      const hops = S.route(from, to).distance;
      if (rays < bestRays || (rays === bestRays && hops < bestHops)) {
        bestRays = rays;
        bestHops = hops;
        candidates = [];
      }
      if (rays !== bestRays || hops !== bestHops) continue;
      const nextBusy = moveState(B, from, to);
      candidates.push({
        from, to, rays, hops, nextBusy,
        freeLinesAfterRelease: freeLineCount(B.filter((p) => p !== from), failed),
        freeLinesAfterMove: freeLineCount(nextBusy, failed),
        destinationScore: destinationScore ? Number(destinationScore(to)) : 0,
      });
    }
  }

  if (policy === POLICY.LEGACY) {
    candidates.sort((a, b) => (a.from - b.from) || (a.to - b.to));
  } else {
    candidates.sort((a, b) =>
      (b.freeLinesAfterMove - a.freeLinesAfterMove) ||
      (b.freeLinesAfterRelease - a.freeLinesAfterRelease) ||
      ((destinationScore ? a.destinationScore - b.destinationScore : 0)) ||
      (a.from - b.from) ||
      (a.to - b.to)
    );
  }

  const chosen = candidates[0];
  return {
    ...chosen,
    policy,
    usedNearOvoidMicrostate: Boolean(info),
    primaryCost: { rays: bestRays, hops: bestHops },
  };
}

module.exports = {
  POLICY,
  normalizePolicy,
  moveState,
  freeLineCount,
  chooseMigration,
};
