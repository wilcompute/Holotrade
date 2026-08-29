#!/usr/bin/env node
"use strict";

// Exact paired A/B over the complete 2,880-state near-ovoid corpus.
//
// A = existing level-1 migration-price law: choose the cheapest ray-cost
//     busy->idle move, breaking equal-cost ties lexicographically.
// B = microstate-aware: first restrict the source to the four certified
//     high-release points, then choose the cheapest ray-cost destination.
//
// This is an exhaustive finite-policy benchmark, not production telemetry.

const path = require("node:path");
const fs = require("node:fs");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/substrate.js"));
const M = require(path.join(root, "scheduler/w33-near-ovoid-migration.js"));
const corpus = JSON.parse(fs.readFileSync(path.join(root, "data/w33_near_ovoid_adversarial_corpus.json"), "utf8"));

function bestMove(busy, allowedSources = busy) {
  const B = new Set(busy);
  const idle = Array.from({ length: 40 }, (_, i) => i).filter((x) => !B.has(x));
  let best = null;
  for (const from of [...allowedSources].sort((a,b)=>a-b)) {
    for (const to of idle) {
      const rays = S.migrationRays(from, to);
      const hops = S.route(from, to).distance;
      const key = [rays, hops, from, to];
      if (!best || key.join(",").localeCompare(best.key.join(","), undefined, {numeric:true}) < 0) {
        best = { key, from, to, rays, hops };
      }
    }
  }
  return best;
}

function freeAfterRelease(busy, from) {
  return M.freeLineIds(busy.filter((x) => x !== from)).length;
}

function runExperiment() {
  const rows = [];
  for (const rec of corpus.records) {
    for (const a of rec.removals) {
      const busy = rec.blocker.filter((x) => x !== a).sort((x,y)=>x-y);
      const info = M.analyzeNearOvoid(busy);
      if (!info) throw new Error("corpus state failed near-ovoid analysis");
      const A = bestMove(busy);
      const B = bestMove(busy, info.highRelease);
      const aFree = freeAfterRelease(busy, A.from);
      const bFree = freeAfterRelease(busy, B.from);
      rows.push({
        defectCenter: info.defectCenter,
        blockerCenter: info.blockerCenter,
        busy: busy.join(","),
        rayOnly: { from:A.from, to:A.to, rays:A.rays, freeLines:aFree },
        microstateAware: { from:B.from, to:B.to, rays:B.rays, freeLines:bFree },
        improvement: bFree-aFree,
      });
    }
  }
  if (rows.length !== 2880) throw new Error(`expected 2880 states, got ${rows.length}`);
  const improved = rows.filter((r) => r.improvement > 0).length;
  const equal = rows.length-improved;
  const rayOnlyMean = rows.reduce((s,r)=>s+r.rayOnly.freeLines,0)/rows.length;
  const awareMean = rows.reduce((s,r)=>s+r.microstateAware.freeLines,0)/rows.length;
  if (!rows.every((r)=>r.rayOnly.rays===3 && r.microstateAware.rays===3)) throw new Error("ray-cost parity failed");
  if (!rows.every((r)=>r.microstateAware.freeLines===7 && (r.rayOnly.freeLines===6 || r.rayOnly.freeLines===7))) throw new Error("release score invariant failed");
  const canon = JSON.stringify(rows);
  return {
    schema:"holotrade.near-ovoid-migration-ab.v1",
    evidence:"EXHAUSTIVE FINITE CORPUS",
    design:{states:2880,paired:true,
      armA:"existing cheapest level-1 migration-ray law with deterministic lexicographic tie-break",
      armB:"restrict source to certified high-release set, then minimize the same migration-ray law",
      outcome:"number of free W33 line placements after source release"},
    summary:{
      improvedStates:improved,
      equalStates:equal,
      improvedFraction:improved/rows.length,
      rayOnlyMeanFreeLines:rayOnlyMean,
      microstateAwareMeanFreeLines:awareMean,
      meanGainFreeLines:awareMean-rayOnlyMean,
      relativeMeanGain:(awareMean-rayOnlyMean)/rayOnlyMean,
      bothArmsMigrationRays:3,
      extraRayCostForAwarePolicy:0,
      rayOnlyHistogram:{"6":rows.filter((r)=>r.rayOnly.freeLines===6).length,"7":rows.filter((r)=>r.rayOnly.freeLines===7).length},
      awareHistogram:{"7":rows.length}
    },
    rowsSha256:crypto.createHash("sha256").update(canon).digest("hex"),
    boundary:"This is exact on the certified one-step-below-cliff W33 corpus. It measures line-placement headroom after one level-1 migration; it is not a production fleet throughput or latency benchmark."
  };
}

if (require.main === module) process.stdout.write(JSON.stringify(runExperiment(), null, 2)+"\n");
module.exports={runExperiment,bestMove,freeAfterRelease};
