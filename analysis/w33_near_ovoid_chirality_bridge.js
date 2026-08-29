"use strict";

/**
 * Exact operational bridge from Holotrade's near-ovoid release signatures to
 * W33-Theory's unique 3+3 microstate block system.
 *
 * For every one of the 2,880 optimal near-ovoids:
 *   - the hinge line has two residual points besides defect centre a and
 *     blocker centre c;
 *   - the four-point high-release set contains exactly one residual point;
 *   - that point is the geometric chirality anchor;
 *   - for each oriented pair (a,c), the six hidden microstates split 3+3 by
 *     chirality anchor;
 *   - the split is exactly the two K3 components of the high-release
 *     intersection graph already used by the migration scheduler.
 *
 * The two three-state blocks are naturally C3 torsors under the W33 local
 * action.  This file intentionally does not assign a canonical F3 phase
 * inside either block: an origin/order is a gauge convention, not scheduler-
 * visible geometry.
 */

const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const corpus = require(path.join(root, "analysis/w33_near_ovoid_corpus.js")).buildCorpus();
const M = require(path.join(root, "scheduler/w33-near-ovoid-migration.js"));

function intersectionSize(a, b) {
  const B = new Set(b);
  return a.reduce((n, x) => n + (B.has(x) ? 1 : 0), 0);
}

function components(xs) {
  const adj = Array.from({ length: xs.length }, () => []);
  for (let i = 0; i < xs.length; i++) for (let j = i + 1; j < xs.length; j++) {
    const s = intersectionSize(xs[i].highRelease, xs[j].highRelease);
    if (s !== 0 && s !== 1) throw new Error(`unexpected intersection ${s}`);
    if (s === 1) { adj[i].push(j); adj[j].push(i); }
  }
  const seen = new Set(), out = [];
  for (let i = 0; i < xs.length; i++) if (!seen.has(i)) {
    const stack = [i], C = [];
    seen.add(i);
    while (stack.length) {
      const u = stack.pop(); C.push(u);
      for (const v of adj[u]) if (!seen.has(v)) { seen.add(v); stack.push(v); }
    }
    out.push(C.sort((a,b)=>a-b));
  }
  return { adj, components: out };
}

function main() {
  const groups = new Map();
  const anchorCounts = Array(40).fill(0);
  const bitCounts = [0, 0];
  let states = 0;

  for (const r of corpus.records) {
    for (const a of r.removals) {
      const busy = r.blocker.filter((x) => x !== a);
      const z = M.analyzeNearOvoid(busy);
      if (!z) throw new Error("certified corpus state rejected by scheduler");
      if (z.defectCenter !== a || z.blockerCenter !== r.center) throw new Error("coordinate mismatch");
      if (z.residualHingePoints.length !== 2) throw new Error("hinge residual count");
      if (!z.residualHingePoints.includes(z.chiralityAnchor)) throw new Error("anchor off hinge");
      if (z.residualHingePoints.filter((p) => z.highRelease.includes(p)).length !== 1) {
        throw new Error("high-release set does not select one residual hinge point");
      }
      anchorCounts[z.chiralityAnchor]++;
      bitCounts[z.chiralityBit]++;
      const key = `${z.defectCenter}:${z.blockerCenter}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(z);
      states++;
    }
  }

  if (states !== 2880 || groups.size !== 480) throw new Error("global state count mismatch");
  if (anchorCounts.some((x) => x !== 72)) throw new Error(`anchor imbalance ${anchorCounts}`);
  if (bitCounts[0] !== 1440 || bitCounts[1] !== 1440) throw new Error(`bit imbalance ${bitCounts}`);

  let halves = 0;
  for (const xs of groups.values()) {
    if (xs.length !== 6) throw new Error("six-state fibre mismatch");
    const residual = new Set(xs.map((z) => z.residualHingePoints.join(",")));
    if (residual.size !== 1) throw new Error("residual hinge pair depends on microstate");
    const byAnchor = new Map();
    for (let i = 0; i < xs.length; i++) {
      const a = xs[i].chiralityAnchor;
      if (!byAnchor.has(a)) byAnchor.set(a, []);
      byAnchor.get(a).push(i);
    }
    const anchorBlocks = [...byAnchor.values()].map((C) => C.sort((a,b)=>a-b));
    if (anchorBlocks.length !== 2 || anchorBlocks.some((C) => C.length !== 3)) {
      throw new Error("chirality partition is not 3+3");
    }

    const { adj, components: comps } = components(xs);
    if (adj.some((N) => N.length !== 2)) throw new Error("intersection graph is not K3 union K3");
    if (comps.length !== 2 || comps.some((C) => C.length !== 3)) throw new Error("component split mismatch");

    const A = new Set(anchorBlocks.map((C) => C.join(",")));
    const C = new Set(comps.map((D) => D.join(",")));
    if (A.size !== C.size || [...A].some((x) => !C.has(x))) {
      throw new Error("K3 components differ from residual-hinge chirality blocks");
    }

    for (const block of comps) {
      const anchors = new Set(block.map((i) => xs[i].chiralityAnchor));
      if (anchors.size !== 1) throw new Error("component has mixed chirality anchor");
      const H = block.map((i) => xs[i].highRelease);
      let common = new Set(H[0]);
      for (const h of H.slice(1)) common = new Set([...common].filter((p) => h.includes(p)));
      if (common.size !== 1 || !common.has(xs[block[0]].chiralityAnchor)) {
        throw new Error("K3 common point is not chirality anchor");
      }
      halves++;
    }
  }
  if (halves !== 960) throw new Error("chirality-half count mismatch");

  const out = {
    schema: "holotrade.w33-near-ovoid-chirality-bridge.v1",
    status: "PASS",
    states: 2880,
    orientedDefectPairs: 480,
    microstatesPerPair: 6,
    chiralityHalves: 960,
    statesPerHalf: 3,
    chiralityAnchor: {
      definition: "the unique residual point of hinge line ac contained in the four-point high-release set",
      residualPointsPerPair: 2,
      statesPerAnchorWithinPair: 3,
      globalStatesPerW33PointAsAnchor: 72,
    },
    deterministicBitEncoding: {
      rule: "sort the two residual hinge point ids and use the anchor index 0/1",
      counts: { "0": bitCounts[0], "1": bitCounts[1] },
      boundary: "the anchor is geometric; the numeric bit is a serialization gauge and is not claimed invariant under relabeling",
    },
    migrationIntersectionGraph: {
      graphPerPair: "K3 disjoint union K3",
      theorem: "its two connected components are exactly the two chirality-anchor blocks",
      commonPointOfEachK3: "its residual hinge chirality anchor",
    },
    w33TheoryBridge: {
      groupImage: "C3 x S3 = (C3 x C3) : C2",
      uniqueBlockSystem: "3+3",
      quotient: "C2 swaps the two residual hinge anchors / chirality halves",
      insideEachHalf: "a three-state C3 torsor; no canonical F3 origin is assigned by Holotrade",
    },
    operationalReading: "The F2 quotient is scheduler-visible during one-release migration even though the current free-line placement depends only on (a,c). The hidden threefold coordinate remains a gauge/torsor unless extra state is supplied.",
    boundary: "Exact finite scheduler/group-action bridge only; 'chirality' names the C2 block quotient and is not a physical particle-chirality claim.",
  };

  const outPath = path.join(root, "data/w33_near_ovoid_chirality_bridge.json");
  if (process.argv.includes("--write")) fs.writeFileSync(outPath, JSON.stringify(out, null, 2) + "\n");
  process.stdout.write(JSON.stringify(out, null, 2) + "\n");
  return out;
}

if (require.main === module) main();
module.exports = { main };
