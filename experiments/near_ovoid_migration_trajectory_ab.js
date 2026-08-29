#!/usr/bin/env node
"use strict";

// Six-step, size-preserving recovery trajectories from every one of the 2,880
// certified W33 near-ovoid adversarial states.
//
// Both arms use the SAME movement price floor: first minimise level-1 migration
// rays, then hop count.  Since every state considered below has a cheapest
// adjacent move, both arms pay 3 rays / 1 hop per step.
//
// LEGACY: break equal-cost ties lexicographically by (source,destination).
// AWARE:  on a certified near-ovoid, restrict the source to its four exact
//         high-release points; otherwise all busy sources are eligible.  Among
//         equal-cost moves, maximise FINAL free-line headroom after the source
//         is removed AND the destination is occupied, then maximise release-only
//         headroom, then use the same lexicographic tie-break.
//
// Every step is therefore a full migration, not a source-only release.  The
// experiment is exhaustive on a finite adversarial corpus but is still an
// ENGINEERING POLICY EXPERIMENT: its multi-step headroom numbers are not a new
// blocking-number theorem, throughput benchmark, latency claim, or market datum.

const path = require("node:path");
const fs = require("node:fs");
const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/substrate.js"));
const M = require(path.join(root, "scheduler/w33-near-ovoid-migration.js"));
const corpus = JSON.parse(fs.readFileSync(
  path.join(root, "data/w33_near_ovoid_adversarial_corpus.json"), "utf8"
));

const ALL = Array.from({ length: 40 }, (_, i) => i);

function sortedUnique(xs) {
  return [...new Set(xs)].sort((a, b) => a - b);
}

function stateKey(busy) {
  return sortedUnique(busy).join(",");
}

function moveState(busy, from, to) {
  const B = new Set(busy);
  if (!B.has(from)) throw new RangeError("migration source is not busy");
  if (B.has(to)) throw new RangeError("migration destination is already busy");
  B.delete(from);
  B.add(to);
  return [...B].sort((a, b) => a - b);
}

function migrationCost(from, to) {
  return {
    rays: S.migrationRays(from, to),
    hops: S.route(from, to).distance,
  };
}

function cheapestCandidates(busy, sourceSubset = busy) {
  const B = new Set(busy);
  const idle = ALL.filter((x) => !B.has(x));
  const sources = sortedUnique(sourceSubset).filter((x) => B.has(x));
  if (!sources.length || !idle.length) throw new Error("empty migration candidate set");

  let bestRays = Infinity;
  let bestHops = Infinity;
  const raw = [];
  for (const from of sources) {
    for (const to of idle) {
      const { rays, hops } = migrationCost(from, to);
      if (rays < bestRays || (rays === bestRays && hops < bestHops)) {
        bestRays = rays;
        bestHops = hops;
        raw.length = 0;
      }
      if (rays === bestRays && hops === bestHops) raw.push({ from, to, rays, hops });
    }
  }
  return raw.filter((x) => x.rays === bestRays && x.hops === bestHops);
}

function legacyMove(busy) {
  const candidates = cheapestCandidates(busy);
  candidates.sort((a, b) => (a.from - b.from) || (a.to - b.to));
  const z = candidates[0];
  const nextBusy = moveState(busy, z.from, z.to);
  return {
    ...z,
    nextBusy,
    freeLinesAfterRelease: M.freeLineIds(busy.filter((x) => x !== z.from)).length,
    freeLinesAfterMove: M.freeLineIds(nextBusy).length,
  };
}

function awareMove(busy) {
  const info = M.analyzeNearOvoid(busy);
  // Exact four-source rule on the certified near-ovoid stratum; after the
  // trajectory leaves that stratum, retain the same topology-aware principle
  // but score all busy sources instead of pretending an m-label still exists.
  const sources = info ? info.highRelease : busy;
  const candidates = cheapestCandidates(busy, sources).map((z) => {
    const nextBusy = moveState(busy, z.from, z.to);
    return {
      ...z,
      nextBusy,
      freeLinesAfterRelease: M.freeLineIds(busy.filter((x) => x !== z.from)).length,
      freeLinesAfterMove: M.freeLineIds(nextBusy).length,
    };
  });
  candidates.sort((a, b) =>
    (b.freeLinesAfterMove - a.freeLinesAfterMove) ||
    (b.freeLinesAfterRelease - a.freeLinesAfterRelease) ||
    (a.from - b.from) ||
    (a.to - b.to)
  );
  return candidates[0];
}

function runArm(startBusy, arm, steps = 6) {
  let busy = sortedUnique(startBusy);
  if (busy.length !== 10) throw new RangeError("trajectory requires ten busy W33 points");
  const visited = new Set([stateKey(busy)]);
  const trace = [];
  for (let step = 1; step <= steps; step++) {
    const move = arm === "aware" ? awareMove(busy) : legacyMove(busy);
    busy = move.nextBusy;
    visited.add(stateKey(busy));
    trace.push({
      step,
      from: move.from,
      to: move.to,
      rays: move.rays,
      hops: move.hops,
      freeLinesAfterRelease: move.freeLinesAfterRelease,
      freeLinesAfterMove: move.freeLinesAfterMove,
    });
  }
  const heads = trace.map((x) => x.freeLinesAfterMove);
  return {
    trace,
    finalBusy: busy,
    cumulativeHeadroom: heads.reduce((a, b) => a + b, 0),
    minimumHeadroom: Math.min(...heads),
    finalHeadroom: heads[heads.length - 1],
    totalRays: trace.reduce((a, x) => a + x.rays, 0),
    totalHops: trace.reduce((a, x) => a + x.hops, 0),
    uniqueStatesVisited: visited.size,
  };
}

function increment(hist, key) {
  const k = String(key);
  hist[k] = (hist[k] || 0) + 1;
}

function mean(total, n) {
  return total / n;
}

function runExperiment({ steps = 6, includeRows = false } = {}) {
  const stepLegacyTotals = Array(steps).fill(0);
  const stepAwareTotals = Array(steps).fill(0);
  const stepStrict = Array(steps).fill(0);
  const stepLegacyHist = Array.from({ length: steps }, () => ({}));
  const stepAwareHist = Array.from({ length: steps }, () => ({}));
  const legacyUnique = {}, awareUnique = {}, legacyMinimum = {}, awareMinimum = {};
  let states = 0;
  let legacyCumulative = 0, awareCumulative = 0;
  let legacyRays = 0, awareRays = 0;
  const rows = [];

  for (const rec of corpus.records) {
    for (const a of rec.removals) {
      const start = rec.blocker.filter((x) => x !== a).sort((x, y) => x - y);
      if (!M.analyzeNearOvoid(start)) throw new Error("corpus state is not a certified near-ovoid");
      const A = runArm(start, "legacy", steps);
      const B = runArm(start, "aware", steps);
      states++;
      legacyCumulative += A.cumulativeHeadroom;
      awareCumulative += B.cumulativeHeadroom;
      legacyRays += A.totalRays;
      awareRays += B.totalRays;
      increment(legacyUnique, A.uniqueStatesVisited);
      increment(awareUnique, B.uniqueStatesVisited);
      increment(legacyMinimum, A.minimumHeadroom);
      increment(awareMinimum, B.minimumHeadroom);

      for (let i = 0; i < steps; i++) {
        const ah = A.trace[i].freeLinesAfterMove;
        const bh = B.trace[i].freeLinesAfterMove;
        stepLegacyTotals[i] += ah;
        stepAwareTotals[i] += bh;
        increment(stepLegacyHist[i], ah);
        increment(stepAwareHist[i], bh);
        if (bh > ah) stepStrict[i]++;
      }
      if (includeRows) rows.push({ start, legacy: A, aware: B });
    }
  }

  if (states !== 2880) throw new Error(`expected 2880 trajectories, got ${states}`);
  if (legacyRays !== awareRays) throw new Error("paired ray totals diverged");
  if (legacyRays !== states * steps * 3) throw new Error("trajectory left the 3-ray movement floor");
  if (!Object.keys(awareMinimum).every((k) => Number(k) >= 6)) {
    throw new Error("aware trajectory fell below six free lines");
  }

  const result = {
    schema: "holotrade.near-ovoid-migration-trajectory-ab.v1",
    evidence: "EXHAUSTIVE FINITE CORPUS / POLICY TRAJECTORY",
    design: {
      startStates: states,
      steps,
      busyCardinality: 10,
      migrationIsSizePreserving: true,
      movementObjectiveSharedByBothArms: "minimise rays, then hops",
      legacyTieBreak: "lexicographic (source,destination)",
      awareTieBreak: "on near-ovoids use the exact four high-release sources; then maximise post-move line headroom, maximise release-only headroom, lexicographic tie-break",
      revisitRule: "none; repeated states are allowed and measured rather than suppressed",
    },
    summary: {
      movement: {
        raysPerStep: 3,
        hopsPerStep: 1,
        totalRaysPerTrajectory: steps * 3,
        pairedExtraRayCost: 0,
      },
      strictlyBetterStatesByStep: stepStrict,
      legacy: {
        meanFreeLinesByStep: stepLegacyTotals.map((x) => mean(x, states)),
        freeLineHistogramByStep: stepLegacyHist,
        cumulativeHeadroomTotal: legacyCumulative,
        cumulativeHeadroomMean: mean(legacyCumulative, states),
        minimumHeadroomHistogram: legacyMinimum,
        uniqueStatesVisitedHistogram: legacyUnique,
      },
      aware: {
        meanFreeLinesByStep: stepAwareTotals.map((x) => mean(x, states)),
        freeLineHistogramByStep: stepAwareHist,
        cumulativeHeadroomTotal: awareCumulative,
        cumulativeHeadroomMean: mean(awareCumulative, states),
        minimumHeadroomHistogram: awareMinimum,
        uniqueStatesVisitedHistogram: awareUnique,
      },
      cumulativeHeadroomGainTotal: awareCumulative - legacyCumulative,
      cumulativeHeadroomGainMean: mean(awareCumulative - legacyCumulative, states),
      relativeCumulativeHeadroomGain: (awareCumulative - legacyCumulative) / legacyCumulative,
    },
    boundary: "This is exact for the declared deterministic policies on the complete 2,880-state level-1 adversarial corpus. Multi-step headroom is an engineering-policy metric, not a new tau blocking guarantee, production throughput/latency measurement, or physical-fabric result.",
  };
  if (includeRows) result.rows = rows;
  return result;
}

if (require.main === module) {
  const arg = process.argv.find((x) => x.startsWith("--steps="));
  const steps = arg ? Number(arg.slice("--steps=".length)) : 6;
  if (!Number.isSafeInteger(steps) || steps <= 0) throw new RangeError("steps must be a positive integer");
  process.stdout.write(JSON.stringify(runExperiment({ steps, includeRows: false }), null, 2) + "\n");
}

module.exports = {
  moveState,
  cheapestCandidates,
  legacyMove,
  awareMove,
  runArm,
  runExperiment,
};
