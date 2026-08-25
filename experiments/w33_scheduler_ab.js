#!/usr/bin/env node
// Deterministic paired A/B/C experiment for the W(3,3) shape scheduler.
// The engine is a native discrete-event model.  It does not claim that the
// exported Containerlab topology, Kubernetes adapter or Slurm adapter ran.

"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const S = require("../js/substrate.js");
const {
  POLICY,
  EDGES,
  edgeKey,
  normalizeState,
  W33SchedulerPlugin,
} = require("../scheduler/w33-scheduler.js");

const CONDITIONS = Object.freeze([
  Object.freeze({ id: "steady", intensity: 0.20, failedNodes: 0, failedEdges: 0, hotspot: false }),
  Object.freeze({ id: "congested", intensity: 0.78, failedNodes: 0, failedEdges: 0, hotspot: true }),
  Object.freeze({ id: "link-failures", intensity: 0.55, failedNodes: 0, failedEdges: 20, hotspot: true }),
  Object.freeze({ id: "node-link-failures", intensity: 0.55, failedNodes: 5, failedEdges: 12, hotspot: true }),
]);

const WORKLOADS = Object.freeze([
  Object.freeze({ id: "allreduce-4", kind: "allreduce", width: 4 }),
  Object.freeze({ id: "shuffle-8", kind: "shuffle", width: 8 }),
  Object.freeze({ id: "parameter-server-12", kind: "parameter-server", width: 12 }),
]);

const POLICIES = Object.freeze([POLICY.W33, POLICY.LOCALITY, POLICY.RANDOM]);

function canonicalJson(value) {
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
}

function sha256(value) {
  return crypto.createHash("sha256").update(typeof value === "string" ? value : canonicalJson(value)).digest("hex");
}

function shuffled(values, rand) {
  const out = [...values];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

function scenario(seed, condition) {
  const rand = S.rng(`${seed}:${condition.id}:state`);
  const failedNodes = shuffled([...Array(S.CONST.points).keys()], rand).slice(0, condition.failedNodes).sort((a, b) => a - b);
  const failedNodeSet = new Set(failedNodes);
  const viableEdges = EDGES.filter(([a, b]) => !failedNodeSet.has(a) && !failedNodeSet.has(b));
  const failedEdges = shuffled(viableEdges, rand).slice(0, condition.failedEdges)
    .map(([a, b]) => edgeKey(a, b)).sort();
  const hotCenter = Math.floor(rand() * S.CONST.points);
  const hotRegion = new Set([hotCenter, ...S.ADJ[hotCenter].slice(0, 4)]);
  const edgeLoad = {};
  for (const [a, b] of EDGES) {
    const noise = 0.08 + 0.58 * rand();
    const hot = condition.hotspot && (hotRegion.has(a) || hotRegion.has(b)) ? 0.22 : 0;
    edgeLoad[edgeKey(a, b)] = Math.min(0.94, condition.intensity * noise + hot);
  }
  const nodeLoad = Array.from({ length: S.CONST.points }, () => 0.08 + 0.78 * rand());
  return normalizeState({
    generation: seed,
    failedNodes,
    failedEdges,
    nodeLoad,
    edgeLoad,
  });
}

function rounded(value, digits = 9) {
  return value === null || value === undefined || !Number.isFinite(value)
    ? null
    : Number(value.toFixed(digits));
}

function compactPlacement(result) {
  if (!result.ok) return { ok: false, code: result.code };
  return {
    ok: true,
    nodes: result.nodes,
    connectedInduced: result.shape.connected,
    internalEdges: result.shape.internalEdges,
    originalBoundary: result.shape.originalBoundary,
    liveBoundary: result.shape.liveBoundary,
    minDegree: result.shape.minDegree,
    diameter: result.shape.diameter,
    makespan: rounded(result.network.makespan),
    goodput: rounded(result.network.goodput),
    meanHops: rounded(result.network.meanHops),
    peakUtilization: rounded(result.network.peakUtilization),
    usedLinks: result.network.usedLinks,
  };
}

function mean(values) {
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
}

function summarize(rows) {
  const policies = {};
  for (const policy of POLICIES) {
    const results = rows.map((row) => row.placements[policy]);
    const successful = results.filter((result) => result.ok);
    policies[policy] = {
      attempts: results.length,
      successes: successful.length,
      successRate: successful.length / results.length,
      connectedInducedRate: successful.length
        ? successful.filter((result) => result.connectedInduced).length / successful.length
        : 0,
      meanMakespan: mean(successful.map((result) => result.makespan)),
      meanGoodput: mean(successful.map((result) => result.goodput)),
      meanPeakUtilization: mean(successful.map((result) => result.peakUtilization)),
      meanInternalEdges: mean(successful.map((result) => result.internalEdges)),
      meanLiveBoundary: mean(successful.map((result) => result.liveBoundary)),
    };
  }

  const paired = {};
  for (const baseline of [POLICY.LOCALITY, POLICY.RANDOM]) {
    const pairs = rows
      .map((row) => [row.placements[POLICY.W33], row.placements[baseline]])
      .filter(([aware, base]) => aware.ok && base.ok && base.makespan > 0);
    const reductions = pairs.map(([aware, base]) => (base.makespan - aware.makespan) / base.makespan);
    paired[baseline] = {
      comparableScenarios: pairs.length,
      w33Wins: pairs.filter(([aware, base]) => aware.makespan < base.makespan - 1e-9).length,
      ties: pairs.filter(([aware, base]) => Math.abs(aware.makespan - base.makespan) <= 1e-9).length,
      w33Losses: pairs.filter(([aware, base]) => aware.makespan > base.makespan + 1e-9).length,
      meanRelativeMakespanReduction: mean(reductions),
      minRelativeMakespanReduction: reductions.length ? Math.min(...reductions) : null,
      maxRelativeMakespanReduction: reductions.length ? Math.max(...reductions) : null,
    };
  }
  return { policies, paired };
}

function runExperiment({ seeds = 24 } = {}) {
  if (!Number.isInteger(seeds) || seeds < 1) throw new RangeError("seeds must be a positive integer");
  const rows = [];
  for (let seed = 0; seed < seeds; seed++) {
    for (const condition of CONDITIONS) {
      const state = scenario(seed, condition);
      for (const template of WORKLOADS) {
        const workload = { ...template, seed: `${seed}:${condition.id}:${template.id}` };
        const placements = {};
        for (const policy of POLICIES) {
          const plugin = new W33SchedulerPlugin({ policy });
          placements[policy] = compactPlacement(plugin.select(workload, state, policy));
        }
        rows.push({
          seed,
          condition: condition.id,
          workload: template.id,
          failedNodes: [...state.failedNodes].sort((a, b) => a - b),
          failedEdges: [...state.failedEdges].sort(),
          placements,
        });
      }
    }
  }

  const rowsSha256 = sha256(rows);
  const summary = summarize(rows);
  return {
    schema: "holotrade.w33-scheduler-ab.v1",
    evidence: "DETERMINISTIC_DISCRETE_EVENT_SIMULATION",
    engine: {
      name: "HoloTrade native W(3,3) flow simulator",
      linkCapacity: "1 unit per modeled edge",
      routing: "deterministic congestion-priced shortest path",
      physicalPacketsSent: 0,
      containerlabRun: false,
      kubernetesPluginDeployed: false,
      slurmPluginDeployed: false,
    },
    design: {
      paired: true,
      seeds,
      conditions: CONDITIONS,
      workloads: WORKLOADS,
      policies: POLICIES,
      scenarios: rows.length,
      topology: {
        graph: "W(3,3) point graph",
        parameters: [40, 12, 2, 4],
        edges: EDGES.length,
        spectrum: { "12": 1, "2": 24, "-4": 15 },
      },
    },
    summary,
    rowsSha256,
    rows,
    limitations: [
      "The run is a unitless discrete-event model, not a packet, Kubernetes, Slurm, or Containerlab measurement.",
      "Link load, failures, and collective volumes are seeded synthetic inputs, not field telemetry.",
      "The W33-aware policy evaluates generated candidates; it does not prove a global optimum for arbitrary widths.",
      "Reserve/Unreserve protects only the in-process reference scheduler; distributed atomicity belongs to the reservation transaction layer.",
    ],
  };
}

function parseArgs(argv) {
  const opts = { seeds: 24, write: null, summary: false };
  for (const arg of argv) {
    if (arg.startsWith("--seeds=")) opts.seeds = Number(arg.slice(8));
    else if (arg.startsWith("--write=")) opts.write = arg.slice(8);
    else if (arg === "--summary") opts.summary = true;
    else throw new Error(`unknown argument: ${arg}`);
  }
  return opts;
}

if (require.main === module) {
  const opts = parseArgs(process.argv.slice(2));
  const packet = runExperiment({ seeds: opts.seeds });
  if (opts.write) {
    const target = path.resolve(process.cwd(), opts.write);
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, `${JSON.stringify(packet, null, 2)}\n`);
  }
  if (opts.summary) console.log(JSON.stringify({ design: packet.design, summary: packet.summary, rowsSha256: packet.rowsSha256 }, null, 2));
  else if (!opts.write) console.log(JSON.stringify(packet, null, 2));
}

module.exports = { CONDITIONS, WORKLOADS, POLICIES, canonicalJson, sha256, scenario, summarize, runExperiment };
