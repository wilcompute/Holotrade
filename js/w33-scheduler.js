// ======================================================================
// HOLOTRADE EXACT W(3,3) SPREAD SCHEDULER
//
// Promotes topology from a scalar coherence/locality term into a concrete
// execution-frame witness. A spread is ten pairwise-disjoint W(3,3) lines
// covering all forty sites. Each frame can therefore carry line operations
// with no site collision.
//
// The congestion "shadow price" below is a scheduling heuristic over exact
// line usage. It is not a measured network tariff or physical throughput law.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate ||
    (typeof require !== "undefined" ? require("./substrate.js") : null);
  const U = root.HolotradeUOR ||
    (typeof require !== "undefined" ? require("./uor.js") : null);
  const E = root.HolotradeEvidence ||
    (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!S || !U || !E) throw new Error("w33-scheduler requires substrate, uor, and evidence");

  const SCHEMA = "holotrade.w33-spread-scheduler.v1";

  const LINE_MASKS = S.LINES.map((line) => line.reduce((mask, point) => mask | (1n << BigInt(point)), 0n));
  const FULL_MASK = (1n << BigInt(S.POINTS.length)) - 1n;

  function enumerateSpreads(limit = 256) {
    if (!Number.isInteger(limit) || limit < 1) throw new RangeError("limit must be positive integer");
    const spreads = [];
    function backtrack(start, used, chosen) {
      if (spreads.length >= limit) return;
      if (used === FULL_MASK) {
        if (chosen.length === 10) spreads.push(Object.freeze([...chosen]));
        return;
      }
      if (chosen.length >= 10) return;
      let first = 0;
      while ((used & (1n << BigInt(first))) !== 0n) first++;
      for (let i = start; i < S.LINES.length; i++) {
        const mask = LINE_MASKS[i];
        if ((mask & (1n << BigInt(first))) === 0n || (used & mask) !== 0n) continue;
        chosen.push(i);
        backtrack(i + 1, used | mask, chosen);
        chosen.pop();
        if (spreads.length >= limit) return;
      }
    }
    backtrack(0, 0n, []);
    return Object.freeze(spreads);
  }

  let SPREAD_CACHE = null;
  function spreads() {
    if (!SPREAD_CACHE) SPREAD_CACHE = enumerateSpreads(256);
    return SPREAD_CACHE;
  }

  function lineForEdge(a, b) {
    if (!S.isAdjacent(a, b)) throw new Error(`points ${a},${b} do not form a W(3,3) edge`);
    const matches = [];
    for (let i = 0; i < S.LINES.length; i++) {
      if (S.LINES[i].includes(a) && S.LINES[i].includes(b)) matches.push(i);
    }
    if (matches.length !== 1) throw new Error(`edge ${a},${b} belongs to ${matches.length} lines, expected 1`);
    return matches[0];
  }

  function routeLineIds(fromPoint, toPoint) {
    const route = S.route(fromPoint, toPoint);
    const ids = [];
    for (let i = 0; i < route.hops.length - 1; i++) ids.push(lineForEdge(route.hops[i], route.hops[i + 1]));
    return Object.freeze(ids);
  }

  function resourcePoint(resource) {
    const addr = resource.address instanceof U.UORAddress ? resource.address : U.UORAddress.fromHex(resource.address);
    return addr.point;
  }

  function inputLineDemands(projection, executionPoint) {
    const rows = [];
    for (const input of projection.inputs || []) {
      const fromPoint = resourcePoint(input);
      for (const lineId of routeLineIds(fromPoint, executionPoint)) {
        rows.push(Object.freeze({
          demandId: `${input.id}->${executionPoint}:L${lineId}`,
          resourceId: input.id,
          fromPoint,
          executionPoint,
          lineId,
          sites: [...S.LINES[lineId]],
        }));
      }
    }
    return Object.freeze(rows);
  }

  function scheduleDemands(demands) {
    const remaining = [...demands];
    const frames = [];
    const catalog = spreads();
    if (catalog.length === 0) throw new Error("no W(3,3) spreads were enumerated");
    while (remaining.length) {
      let best = null;
      for (let spreadIndex = 0; spreadIndex < catalog.length; spreadIndex++) {
        const spread = catalog[spreadIndex];
        const lineSet = new Set(spread);
        const covered = remaining.filter((row) => lineSet.has(row.lineId));
        // duplicate operations on one line cannot execute simultaneously.
        const unique = [];
        const seenLines = new Set();
        for (const row of covered) {
          if (seenLines.has(row.lineId)) continue;
          seenLines.add(row.lineId);
          unique.push(row);
        }
        if (!best || unique.length > best.demands.length ||
            (unique.length === best.demands.length && spreadIndex < best.spreadIndex)) {
          best = { spreadIndex, spread, demands: unique };
        }
      }
      if (!best || best.demands.length === 0) throw new Error("failed to schedule W(3,3) line demand");
      const ids = new Set(best.demands.map((row) => row.demandId));
      frames.push(Object.freeze({
        frame: frames.length,
        spreadIndex: best.spreadIndex,
        lineIds: best.demands.map((row) => row.lineId).sort((a, b) => a - b),
        demandIds: best.demands.map((row) => row.demandId).sort(),
        spreadLines: [...best.spread],
        conflictFree: true,
      }));
      for (let i = remaining.length - 1; i >= 0; i--) if (ids.has(remaining[i].demandId)) remaining.splice(i, 1);
    }
    const body = {
      schema: SCHEMA,
      demandCount: demands.length,
      frameCount: frames.length,
      frames,
      exactCarrier: "W(3,3)",
      spreadCountEnumerated: catalog.length,
      conflictFree: frames.every((frame) => {
        const sites = new Set();
        for (const lineId of frame.lineIds) {
          for (const site of S.LINES[lineId]) {
            if (sites.has(site)) return false;
            sites.add(site);
          }
        }
        return true;
      }),
    };
    return Object.freeze({ ...body, digest: E.demoDigest(body) });
  }

  class LineCongestionLedger {
    constructor() {
      this.loads = Array(S.LINES.length).fill(0);
      this.total = 0;
    }

    charge(demands, amount = 1) {
      if (!(amount >= 0)) throw new RangeError("amount must be non-negative");
      for (const row of demands) {
        this.loads[row.lineId] += amount;
        this.total += amount;
      }
    }

    marginalCost(demands, unit = 1e-6) {
      let cost = 0;
      for (const row of demands) {
        const load = this.loads[row.lineId];
        cost += ((load + 1) ** 2 - load ** 2) * unit;
      }
      return cost;
    }

    snapshot() {
      return Object.freeze({ loads: [...this.loads], total: this.total, max: Math.max(...this.loads), min: Math.min(...this.loads) });
    }
  }

  function rankPlacement(executionEngine, plan, projection, ledger = new LineCongestionLedger(), options = {}) {
    const base = executionEngine.place(plan, { limit: options.baseLimit || 32 });
    const unit = options.shadowUnit ?? 1e-6;
    const rows = base.map((candidate) => {
      const demands = inputLineDemands(projection, candidate.node.cellPoint);
      const schedule = scheduleDemands(demands);
      const shadowCost = ledger.marginalCost(demands, unit);
      return {
        ...candidate,
        w33: { demands, schedule, shadowCost },
        scoreWithW33: candidate.score + shadowCost,
      };
    });
    rows.sort((a, b) => a.scoreWithW33 - b.scoreWithW33 || a.node.id.localeCompare(b.node.id));
    return rows.slice(0, options.limit || 8);
  }

  const API = {
    SCHEMA,
    enumerateSpreads,
    spreads,
    lineForEdge,
    routeLineIds,
    inputLineDemands,
    scheduleDemands,
    LineCongestionLedger,
    rankPlacement,
  };
  root.HolotradeW33Scheduler = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
