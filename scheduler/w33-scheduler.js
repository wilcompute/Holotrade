// =====================================================================
// W(3,3) SHAPE SCHEDULER
//
// A dependency-free reference kernel for topology-aware gang placement on
// HoloTrade's exact 40-node W(3,3) cell.  The API deliberately resembles the
// useful parts of both scheduler ecosystems:
//
//   Kubernetes: Filter -> Score -> NormalizeScore -> Reserve/Unreserve
//   Slurm:      select one topology-aware node set for a gang request
//
// This is executable JavaScript, not a compiled kube-scheduler or Slurm
// plugin.  It is also the native engine behind the deterministic A/B packet.
// =====================================================================

"use strict";

const S = require("../js/substrate.js");

const POLICY = Object.freeze({
  W33: "w33-aware",
  LOCALITY: "locality-first",
  RANDOM: "seeded-random",
});

function edgeKey(a, b) {
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

const EDGES = Object.freeze((() => {
  const out = [];
  for (let a = 0; a < S.CONST.points; a++) {
    for (const b of S.ADJ[a]) if (a < b) out.push(Object.freeze([a, b]));
  }
  return out;
})());

function finiteUnit(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.max(0, Math.min(1, n)) : fallback;
}

function normalizeState(spec = {}) {
  const failedNodes = new Set(spec.failedNodes || []);
  const failedEdges = new Set([...(spec.failedEdges || [])].map((edge) =>
    Array.isArray(edge) ? edgeKey(Number(edge[0]), Number(edge[1])) : String(edge)
  ));
  const reservedNodes = new Set(spec.reservedNodes || []);
  const nodeLoad = Array.from({ length: S.CONST.points }, (_, i) =>
    finiteUnit(spec.nodeLoad && spec.nodeLoad[i], 0)
  );
  const edgeLoad = new Map();
  for (const [a, b] of EDGES) {
    const key = edgeKey(a, b);
    const source = spec.edgeLoad instanceof Map ? spec.edgeLoad.get(key) : spec.edgeLoad && spec.edgeLoad[key];
    edgeLoad.set(key, finiteUnit(source, 0));
  }
  return {
    generation: Number.isInteger(spec.generation) ? spec.generation : 0,
    failedNodes,
    failedEdges,
    reservedNodes,
    nodeLoad,
    edgeLoad,
  };
}

function liveEdge(a, b, state) {
  return S.isAdjacent(a, b) &&
    !state.failedNodes.has(a) && !state.failedNodes.has(b) &&
    !state.failedEdges.has(edgeKey(a, b));
}

function liveNeighbours(node, state) {
  if (state.failedNodes.has(node)) return [];
  return S.ADJ[node].filter((other) => liveEdge(node, other, state));
}

function availableNodes(state) {
  const out = [];
  for (let i = 0; i < S.CONST.points; i++) {
    if (!state.failedNodes.has(i) && !state.reservedNodes.has(i) && state.nodeLoad[i] < 0.98) out.push(i);
  }
  return out;
}

function spectralReservationBounds(m) {
  const size = Number(m);
  if (!Number.isInteger(size) || size < 0 || size > S.CONST.points) {
    throw new RangeError("reservation size must be an integer in [0,40]");
  }
  // For f = 1_T - (m/40)1, b(T) = 12m(1-m/40)-f'Af.
  // The nontrivial spectrum is {2,-4}, hence the two one-sided bounds.
  const lowerBoundaryReal = size * (S.CONST.points - size) / 4;
  const upperBoundaryReal = 2 * size * (S.CONST.points - size) / 5;
  const upperInducedEdgesReal = size * (size + 8) / 8;
  const lowerInducedEdgesReal = size * (size - 10) / 5;
  return Object.freeze({
    size,
    lowerBoundaryReal,
    lowerBoundaryInteger: Math.ceil(lowerBoundaryReal - 1e-12),
    upperBoundaryReal,
    upperBoundaryInteger: Math.floor(upperBoundaryReal + 1e-12),
    lowerInducedEdgesReal,
    lowerInducedEdgesInteger: Math.max(0, Math.ceil(lowerInducedEdgesReal - 1e-12)),
    upperInducedEdgesReal,
    upperInducedEdgesInteger: Math.floor(upperInducedEdgesReal + 1e-12),
  });
}

function graphStats(nodes, state = normalizeState()) {
  const unique = [...new Set(nodes)].sort((a, b) => a - b);
  const selected = new Set(unique);
  const adj = new Map(unique.map((p) => [p, []]));
  let internalEdges = 0;
  let originalInternalEdges = 0;
  let originalBoundary = 0;
  let liveBoundary = 0;

  for (const [a, b] of EDGES) {
    const inA = selected.has(a);
    const inB = selected.has(b);
    if (inA && inB) {
      originalInternalEdges++;
      if (liveEdge(a, b, state)) {
        internalEdges++;
        adj.get(a).push(b);
        adj.get(b).push(a);
      }
    } else if (inA !== inB) {
      originalBoundary++;
      if (liveEdge(a, b, state)) liveBoundary++;
    }
  }

  let components = 0;
  let diameter = unique.length ? 0 : null;
  const seen = new Set();
  for (const start of unique) {
    if (seen.has(start)) continue;
    components++;
    const queue = [start];
    seen.add(start);
    while (queue.length) {
      const u = queue.shift();
      for (const v of adj.get(u)) if (!seen.has(v)) { seen.add(v); queue.push(v); }
    }
  }
  if (components > 1) diameter = null;
  if (components === 1) {
    for (const start of unique) {
      const distance = new Map([[start, 0]]);
      const queue = [start];
      while (queue.length) {
        const u = queue.shift();
        for (const v of adj.get(u)) if (!distance.has(v)) {
          distance.set(v, distance.get(u) + 1);
          queue.push(v);
        }
      }
      diameter = Math.max(diameter, ...distance.values());
    }
  }

  const degrees = unique.map((node) => adj.get(node).length);
  const bounds = spectralReservationBounds(unique.length);
  return Object.freeze({
    nodes: unique,
    size: unique.length,
    internalEdges,
    originalInternalEdges,
    originalBoundary,
    liveBoundary,
    components,
    connected: unique.length > 0 && components === 1,
    diameter,
    minDegree: degrees.length ? Math.min(...degrees) : 0,
    meanDegree: degrees.length ? degrees.reduce((a, b) => a + b, 0) / degrees.length : 0,
    spectralBounds: bounds,
    meetsLowerBoundaryEquality: Math.abs(originalBoundary - bounds.lowerBoundaryReal) < 1e-9,
    meetsUpperInducedEquality: Math.abs(originalInternalEdges - bounds.upperInducedEdgesReal) < 1e-9,
  });
}

function shortestPath(source, target, state, assigned = new Map()) {
  if (source === target) return [source];
  const dist = Array(S.CONST.points).fill(Infinity);
  const prev = Array(S.CONST.points).fill(-1);
  const used = Array(S.CONST.points).fill(false);
  dist[source] = 0;

  for (let step = 0; step < S.CONST.points; step++) {
    let u = -1;
    for (let i = 0; i < S.CONST.points; i++) {
      if (!used[i] && (u < 0 || dist[i] < dist[u] - 1e-12 ||
        (Math.abs(dist[i] - dist[u]) < 1e-12 && i < u))) u = i;
    }
    if (u < 0 || !Number.isFinite(dist[u])) break;
    if (u === target) break;
    used[u] = true;
    for (const v of liveNeighbours(u, state)) {
      const key = edgeKey(u, v);
      const base = state.edgeLoad.get(key) || 0;
      const extra = assigned.get(key) || 0;
      const residual = Math.max(0.025, 1 - base);
      // Convex marginal price: route around both pre-existing load and flows
      // already assigned by this collective.
      const weight = 1 / residual + 2 * extra / (residual * residual) + 0.01;
      const candidate = dist[u] + weight;
      if (candidate < dist[v] - 1e-12 ||
          (Math.abs(candidate - dist[v]) < 1e-12 && u < prev[v])) {
        dist[v] = candidate;
        prev[v] = u;
      }
    }
  }
  if (prev[target] < 0) return null;
  const path = [target];
  while (path[path.length - 1] !== source) path.push(prev[path[path.length - 1]]);
  return path.reverse();
}

function demandsFor(nodes, workload = {}) {
  const points = [...nodes].sort((a, b) => a - b);
  const kind = workload.kind || "allreduce";
  const out = [];
  if (points.length < 2) return out;
  if (kind === "allreduce") {
    const volume = 2 / (points.length - 1);
    for (let i = 0; i < points.length; i++) {
      for (let j = i + 1; j < points.length; j++) out.push({ from: points[i], to: points[j], volume });
    }
  } else if (kind === "parameter-server") {
    // The topology medoid is chosen at simulation time; use the first point as
    // a stable placeholder and permit simulateCollective to replace it.
    for (let i = 1; i < points.length; i++) out.push({ from: points[0], to: points[i], volume: 1 });
  } else if (kind === "shuffle") {
    const rand = S.rng(`${workload.seed || "w33"}:shuffle`);
    const shuffled = [...points];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(rand() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    for (let i = 0; i < shuffled.length; i++) {
      const to = shuffled[(i + Math.max(1, Math.floor(shuffled.length / 2))) % shuffled.length];
      if (shuffled[i] !== to) out.push({ from: shuffled[i], to, volume: 1 });
    }
  } else {
    throw new RangeError(`unsupported collective kind: ${kind}`);
  }
  return out;
}

function topologyMedoid(nodes, state) {
  let best = null;
  for (const source of nodes) {
    let sum = 0;
    let valid = true;
    for (const target of nodes) {
      if (source === target) continue;
      const path = shortestPath(source, target, state);
      if (!path) { valid = false; break; }
      sum += path.length - 1;
    }
    if (valid && (!best || sum < best.sum || (sum === best.sum && source < best.node))) best = { node: source, sum };
  }
  return best && best.node;
}

function simulateCollective(nodes, workload, stateSpec) {
  const state = stateSpec && stateSpec.edgeLoad instanceof Map ? stateSpec : normalizeState(stateSpec);
  const points = [...new Set(nodes)].sort((a, b) => a - b);
  let demands = demandsFor(points, workload);
  if ((workload.kind || "allreduce") === "parameter-server") {
    const center = topologyMedoid(points, state);
    if (center === null || center === undefined) {
      return { success: false, makespan: null, goodput: 0, reason: "placement is not routable" };
    }
    demands = points.filter((p) => p !== center).map((p) => ({ from: center, to: p, volume: 1 }));
  }

  const assigned = new Map();
  let hopVolume = 0;
  let totalDemand = 0;
  for (const demand of demands) {
    const path = shortestPath(demand.from, demand.to, state, assigned);
    if (!path) return { success: false, makespan: null, goodput: 0, reason: `no path ${demand.from}->${demand.to}` };
    totalDemand += demand.volume;
    hopVolume += demand.volume * (path.length - 1);
    for (let i = 0; i + 1 < path.length; i++) {
      const key = edgeKey(path[i], path[i + 1]);
      assigned.set(key, (assigned.get(key) || 0) + demand.volume);
    }
  }

  let bottleneckTime = 0;
  let peakUtilization = 0;
  for (const [key, extra] of assigned) {
    const base = state.edgeLoad.get(key) || 0;
    const residual = Math.max(0.025, 1 - base);
    bottleneckTime = Math.max(bottleneckTime, extra / residual);
    peakUtilization = Math.max(peakUtilization, base + extra);
  }
  const meanHops = totalDemand ? hopVolume / totalDemand : 0;
  const synchronization = points.length > 1 ? Math.log2(points.length) * 0.025 : 0;
  const makespan = Math.max(1e-9, bottleneckTime + meanHops * 0.02 + synchronization);
  return Object.freeze({
    success: true,
    makespan,
    goodput: totalDemand / makespan,
    totalDemand,
    meanHops,
    peakUtilization,
    usedLinks: assigned.size,
  });
}

function lexicographic(a, b) {
  const aa = a.join(",");
  const bb = b.join(",");
  return aa < bb ? -1 : aa > bb ? 1 : 0;
}

function greedyCandidate(seed, width, state, availableSet) {
  const selected = [seed];
  const chosen = new Set(selected);
  while (selected.length < width) {
    const frontier = [...availableSet].filter((p) => !chosen.has(p) && selected.some((q) => liveEdge(p, q, state)));
    if (!frontier.length) return null;
    frontier.sort((a, b) => {
      const score = (p) => {
        const joins = selected.filter((q) => liveEdge(p, q, state)).length;
        const incident = liveNeighbours(p, state);
        const congestion = incident.length
          ? incident.reduce((sum, q) => sum + (state.edgeLoad.get(edgeKey(p, q)) || 0), 0) / incident.length
          : 1;
        return joins * 6 - congestion * 4 - state.nodeLoad[p] * 2;
      };
      return score(b) - score(a) || a - b;
    });
    selected.push(frontier[0]);
    chosen.add(frontier[0]);
  }
  return selected.sort((a, b) => a - b);
}

function w33Candidates(width, state, available) {
  const allowed = new Set(available);
  const byKey = new Map();
  const add = (candidate) => {
    if (!candidate || candidate.length !== width || candidate.some((p) => !allowed.has(p))) return;
    const sorted = [...candidate].sort((a, b) => a - b);
    const stats = graphStats(sorted, state);
    if (stats.connected) byKey.set(sorted.join(","), sorted);
  };

  // Equality templates supplied by the exact spectrum: every line is an
  // optimal four-node shape, and the certified 20|20 split gives two optimal
  // twenty-node shapes when healthy.
  if (width === 4) for (const line of S.LINES) add(line);
  if (width === 20) {
    add(S.BISECTION_LEFT);
    const left = new Set(S.BISECTION_LEFT);
    add(S.POINTS.map((p) => p.index).filter((p) => !left.has(p)));
  }
  for (const seed of available) add(greedyCandidate(seed, width, state, allowed));
  return [...byKey.values()];
}

function selectW33(workload, state, available) {
  const candidates = w33Candidates(workload.width, state, available);
  let best = null;
  for (const nodes of candidates) {
    const network = simulateCollective(nodes, workload, state);
    if (!network.success) continue;
    const shape = graphStats(nodes, state);
    const nodePenalty = nodes.reduce((sum, p) => sum + state.nodeLoad[p], 0) / nodes.length;
    // Makespan is primary.  Shape density and node load make deterministic,
    // operationally sensible tie-breakers without changing the measured KPI.
    const objective = network.makespan + nodePenalty * 0.06 - shape.internalEdges * 1e-4;
    const record = { nodes, shape, network, objective };
    if (!best || objective < best.objective - 1e-12 ||
      (Math.abs(objective - best.objective) < 1e-12 && lexicographic(nodes, best.nodes) < 0)) best = record;
  }
  return best;
}

function selectLocality(workload, state, available) {
  if (!available.length) return null;
  const allowed = new Set(available);
  const seeds = [...available].sort((a, b) => state.nodeLoad[a] - state.nodeLoad[b] || a - b);
  for (const seed of seeds) {
    const selected = [];
    const seen = new Set([seed]);
    const queue = [seed];
    while (queue.length && selected.length < workload.width) {
      const u = queue.shift();
      selected.push(u);
      const next = liveNeighbours(u, state)
        .filter((v) => allowed.has(v) && !seen.has(v))
        .sort((a, b) => state.nodeLoad[a] - state.nodeLoad[b] || a - b);
      for (const v of next) { seen.add(v); queue.push(v); }
    }
    if (selected.length === workload.width) {
      const nodes = selected.sort((a, b) => a - b);
      return { nodes, shape: graphStats(nodes, state), network: simulateCollective(nodes, workload, state) };
    }
  }
  return null;
}

function selectRandom(workload, state, available) {
  if (available.length < workload.width) return null;
  const rand = S.rng(`${workload.seed || "w33"}:placement`);
  const shuffled = [...available];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  const nodes = shuffled.slice(0, workload.width).sort((a, b) => a - b);
  return { nodes, shape: graphStats(nodes, state), network: simulateCollective(nodes, workload, state) };
}

class W33SchedulerPlugin {
  constructor({ policy = POLICY.W33 } = {}) {
    if (!Object.values(POLICY).includes(policy)) throw new RangeError(`unknown scheduler policy: ${policy}`);
    this.policy = policy;
    this.reservations = new Map();
    this.epoch = 0;
  }

  name() { return "W33Shape"; }

  stateWithReservations(stateSpec = {}) {
    const state = normalizeState(stateSpec);
    for (const record of this.reservations.values()) for (const node of record.nodes) state.reservedNodes.add(node);
    return state;
  }

  preFilter(workload, stateSpec = {}) {
    if (!workload || typeof workload !== "object") return { ok: false, code: "INVALID_WORKLOAD" };
    if (!Number.isInteger(workload.width) || workload.width < 1 || workload.width > S.CONST.points) {
      return { ok: false, code: "INVALID_WIDTH" };
    }
    const state = this.stateWithReservations(stateSpec);
    const available = availableNodes(state);
    if (available.length < workload.width) return { ok: false, code: "INSUFFICIENT_CAPACITY", available: available.length };
    return { ok: true, state, available };
  }

  filter(workload, node, stateSpec = {}) {
    const check = this.preFilter(workload, stateSpec);
    if (!check.ok) return check;
    if (!Number.isInteger(node) || node < 0 || node >= S.CONST.points) return { ok: false, code: "INVALID_NODE" };
    if (!check.available.includes(node)) return { ok: false, code: "NODE_UNAVAILABLE" };
    return { ok: true };
  }

  score(workload, node, partial = [], stateSpec = {}) {
    const check = this.filter(workload, node, stateSpec);
    if (!check.ok) return { ...check, score: 0 };
    const state = this.stateWithReservations(stateSpec);
    const joins = partial.filter((p) => liveEdge(node, p, state)).length;
    const neighbours = liveNeighbours(node, state);
    const congestion = neighbours.length
      ? neighbours.reduce((sum, p) => sum + (state.edgeLoad.get(edgeKey(node, p)) || 0), 0) / neighbours.length
      : 1;
    const raw = joins * 24 + (1 - congestion) * 36 + (1 - state.nodeLoad[node]) * 20;
    return { ok: true, score: Math.max(0, Math.min(100, Math.round(raw))), raw };
  }

  normalizeScore(records) {
    if (!records.length) return [];
    const values = records.map((r) => r.raw === undefined ? r.score : r.raw);
    const low = Math.min(...values);
    const high = Math.max(...values);
    return records.map((record, i) => ({
      ...record,
      score: high === low ? 100 : Math.round(100 * (values[i] - low) / (high - low)),
    }));
  }

  select(workload, stateSpec = {}, policy = this.policy) {
    const check = this.preFilter(workload, stateSpec);
    if (!check.ok) return { ok: false, code: check.code, available: check.available };
    const job = { ...workload, kind: workload.kind || "allreduce", seed: workload.seed || workload.id || "w33" };
    let selected;
    if (policy === POLICY.W33) selected = selectW33(job, check.state, check.available);
    else if (policy === POLICY.LOCALITY) selected = selectLocality(job, check.state, check.available);
    else if (policy === POLICY.RANDOM) selected = selectRandom(job, check.state, check.available);
    else throw new RangeError(`unknown scheduler policy: ${policy}`);
    if (!selected || !selected.network || !selected.network.success) {
      return { ok: false, code: "NO_ROUTABLE_SHAPE", policy };
    }
    return Object.freeze({ ok: true, policy, ...selected });
  }

  // Kubernetes-style informational Reserve/Unreserve phases.  This protects
  // a scheduling cycle from local races; the separate multi-node transaction
  // layer remains responsible for distributed two-phase commit.
  reserve(workload, stateSpec = {}) {
    const id = String(workload && (workload.id || workload.uid) || "").trim();
    if (!id) return { ok: false, code: "MISSING_JOB_ID" };
    if (this.reservations.has(id)) return this.reservations.get(id);
    const placement = this.select(workload, stateSpec, POLICY.W33);
    if (!placement.ok) return placement;
    const token = Object.freeze({
      ok: true,
      schema: "holotrade.w33-reserve.v1",
      id,
      epoch: ++this.epoch,
      generation: Number.isInteger(stateSpec.generation) ? stateSpec.generation : 0,
      nodes: Object.freeze([...placement.nodes]),
      shape: placement.shape,
      policy: placement.policy,
    });
    this.reservations.set(id, token);
    return token;
  }

  unreserve(jobOrId) {
    const id = typeof jobOrId === "object" && jobOrId ? jobOrId.id || jobOrId.uid : jobOrId;
    const existed = this.reservations.delete(String(id || ""));
    return { ok: true, released: existed }; // idempotent and cannot fail
  }

  // Slurm-style topology selector surface.  This is a reference adapter, not
  // a compiled select/topology plugin or a topology.conf representation.
  selectTopology(workload, stateSpec = {}) {
    const placement = this.select(workload, stateSpec, POLICY.W33);
    if (!placement.ok) return placement;
    return Object.freeze({
      ok: true,
      adapter: "SLURM_STYLE_REFERENCE_SELECTOR",
      nodeList: placement.nodes.map((p) => `w33-${String(p).padStart(2, "0")}`),
      segmentSize: placement.nodes.length,
      topologyClass: placement.shape.meetsLowerBoundaryEquality ? "spectral-equality-shape" : "connected-induced-shape",
      metrics: placement.shape,
    });
  }
}

module.exports = {
  POLICY,
  EDGES,
  edgeKey,
  normalizeState,
  liveEdge,
  liveNeighbours,
  availableNodes,
  spectralReservationBounds,
  graphStats,
  demandsFor,
  simulateCollective,
  W33SchedulerPlugin,
};
