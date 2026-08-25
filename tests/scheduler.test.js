"use strict";

const assert = require("node:assert/strict");
const child = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/substrate.js"));
const W = require(path.join(root, "scheduler/w33-scheduler.js"));
const { containerlabYaml } = require(path.join(root, "scheduler/containerlab-export.js"));
const { runExperiment, sha256 } = require(path.join(root, "experiments/w33_scheduler_ab.js"));

test("spectral reservation bounds make lines and the certified half optimal shapes", () => {
  const line = W.graphStats(S.LINES[0]);
  assert.deepEqual(
    { size: line.size, edges: line.originalInternalEdges, boundary: line.originalBoundary, diameter: line.diameter },
    { size: 4, edges: 6, boundary: 36, diameter: 1 }
  );
  assert.equal(line.spectralBounds.lowerBoundaryReal, 36);
  assert.equal(line.spectralBounds.upperInducedEdgesReal, 6);
  assert.equal(line.meetsLowerBoundaryEquality, true);
  assert.equal(line.meetsUpperInducedEquality, true);

  const half = W.graphStats(S.BISECTION_LEFT);
  assert.deepEqual(
    { size: half.size, edges: half.originalInternalEdges, boundary: half.originalBoundary },
    { size: 20, edges: 70, boundary: 100 }
  );
  assert.equal(half.spectralBounds.lowerBoundaryReal, 100);
  assert.equal(half.spectralBounds.upperInducedEdgesReal, 70);
  assert.equal(half.meetsLowerBoundaryEquality, true);
  assert.equal(half.meetsUpperInducedEquality, true);
});

test("the W33 policy places a four-worker all-reduce on a complete line", () => {
  const plugin = new W.W33SchedulerPlugin();
  const placed = plugin.select({ id: "allreduce-line", width: 4, kind: "allreduce" });
  assert.equal(placed.ok, true);
  assert.equal(placed.shape.connected, true);
  assert.equal(placed.shape.internalEdges, 6);
  assert.equal(placed.shape.minDegree, 3);
  assert.equal(placed.shape.diameter, 1);
  assert.equal(placed.shape.meetsUpperInducedEquality, true);
});

test("Kubernetes-style Reserve prevents overlap and Unreserve is idempotent", () => {
  const plugin = new W.W33SchedulerPlugin();
  assert.equal(plugin.name(), "W33Shape");
  const first = plugin.reserve({ id: "gang-a", width: 4, kind: "allreduce" });
  const repeat = plugin.reserve({ id: "gang-a", width: 4, kind: "allreduce" });
  const second = plugin.reserve({ id: "gang-b", width: 4, kind: "allreduce" });
  assert.equal(first.ok, true);
  assert.equal(repeat, first, "retry returns the same local reservation token");
  assert.equal(second.ok, true);
  assert.equal(first.nodes.some((node) => second.nodes.includes(node)), false);
  assert.deepEqual(plugin.unreserve("gang-a"), { ok: true, released: true });
  assert.deepEqual(plugin.unreserve("gang-a"), { ok: true, released: false });
});

test("the Slurm-style adapter returns one connected induced node set", () => {
  const plugin = new W.W33SchedulerPlugin();
  const selected = plugin.selectTopology({ id: "slurm-gang", width: 8, kind: "shuffle" });
  assert.equal(selected.ok, true);
  assert.equal(selected.adapter, "SLURM_STYLE_REFERENCE_SELECTOR");
  assert.equal(selected.nodeList.length, 8);
  assert.ok(selected.nodeList.every((name) => /^w33-\d{2}$/.test(name)));
  assert.equal(selected.metrics.connected, true);
});

test("Containerlab export has exactly 40 nodes, 240 links and twelve ports per node", () => {
  const yaml = containerlabYaml();
  assert.match(yaml, /CONTAINERLAB_DEPLOYED=false/);
  assert.equal((yaml.match(/^    w33-\d{2}: \{\}$/gm) || []).length, 40);
  assert.equal((yaml.match(/^    - endpoints:/gm) || []).length, 240);
  for (let node = 0; node < 40; node++) {
    const name = `w33-${String(node).padStart(2, "0")}:eth`;
    assert.equal(yaml.split(name).length - 1, 12, `${name} has degree 12`);
  }
});

test("the frozen 288-scenario A/B/C certificate is self-consistent", () => {
  const packet = JSON.parse(fs.readFileSync(path.join(root, "data/w33_scheduler_ab_24.json"), "utf8"));
  assert.equal(packet.evidence, "DETERMINISTIC_DISCRETE_EVENT_SIMULATION");
  assert.equal(packet.design.paired, true);
  assert.equal(packet.design.scenarios, 288);
  assert.equal(packet.rows.length, 288);
  assert.equal(packet.rowsSha256, sha256(packet.rows));
  assert.equal(packet.engine.containerlabRun, false);
  assert.equal(packet.engine.kubernetesPluginDeployed, false);
  assert.equal(packet.engine.slurmPluginDeployed, false);
  assert.equal(packet.summary.policies[W.POLICY.W33].successRate, 1);
  assert.equal(packet.summary.policies[W.POLICY.W33].connectedInducedRate, 1);
  assert.ok(packet.summary.paired[W.POLICY.LOCALITY].meanRelativeMakespanReduction > 0.1);
  assert.ok(packet.summary.paired[W.POLICY.RANDOM].meanRelativeMakespanReduction > 0.1);

  const smokeA = runExperiment({ seeds: 1 });
  const smokeB = runExperiment({ seeds: 1 });
  assert.equal(smokeA.rowsSha256, smokeB.rowsSha256, "seeded experiment is byte-canonical at the row layer");
});

test("GAP independently regenerates the graph, spectrum and connectivity certificate", (t) => {
  let probe = child.spawnSync("gap", ["-q", path.join(root, "analysis/w33_scheduler_math.g")], {
    cwd: root,
    encoding: "utf8",
    timeout: 30_000,
  });
  // The development checkout is commonly driven by Windows Node from WSL.
  // In that mixed environment GAP is a WSL binary, so cross the boundary
  // explicitly while keeping ordinary Linux CI dependency-free.
  if (probe.error && probe.error.code === "ENOENT" && process.platform === "win32") {
    const wslRoot = root.replace(/^([A-Za-z]):\\/, (_, drive) => `/mnt/${drive.toLowerCase()}/`).replaceAll("\\", "/");
    probe = child.spawnSync("wsl.exe", ["gap", "-q", `${wslRoot}/analysis/w33_scheduler_math.g`], {
      cwd: root,
      encoding: "utf8",
      timeout: 30_000,
    });
  }
  if (probe.error && probe.error.code === "ENOENT") return t.skip("GAP is optional in the Node-only CI image");
  assert.equal(probe.status, 0, probe.stderr);
  const live = JSON.parse(probe.stdout);
  const frozen = JSON.parse(fs.readFileSync(path.join(root, "data/w33_scheduler_ab_math_gap.json"), "utf8"));
  assert.equal(live.allChecksPass, true);
  assert.deepEqual(live.graph, frozen.graph);
  assert.deepEqual(live.spectralBounds, frozen.spectralBounds);
  assert.deepEqual(live.equalityShapes, frozen.equalityShapes);
  assert.deepEqual(live.vertexConnectivity, frozen.vertexConnectivity);
});
