// ======================================================================
// HOLOTRADE EXACT W(3,3) SPREAD SCHEDULER
//
// A spread is ten pairwise-disjoint W(3,3) isotropic lines covering all 40
// sites. v2 closes the full finite census used in W33-Theory: exactly 36
// spreads, every line in exactly 9 spreads, and for any anchor point the 36
// spreads split into four anchor-line sectors of size 9.
//
// Congestion shadow pricing remains a scheduling heuristic over this exact
// carrier. It is not measured network throughput or a physical tariff.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);
  const U = root.HolotradeUOR || (typeof require !== "undefined" ? require("./uor.js") : null);
  const E = root.HolotradeEvidence || (typeof require !== "undefined" ? require("./evidence.js") : null);
  if (!S || !U || !E) throw new Error("w33-scheduler requires substrate, uor, and evidence");

  const SCHEMA = "holotrade.w33-spread-scheduler.v2";
  const LINE_MASKS = S.LINES.map((line) => line.reduce((mask, point) => mask | (1n << BigInt(point)), 0n));
  const FULL_MASK = (1n << BigInt(S.POINTS.length)) - 1n;
  const POINT_TO_LINES = Array.from({ length: S.POINTS.length }, () => []);
  for (let lineId = 0; lineId < S.LINES.length; lineId++) {
    for (const point of S.LINES[lineId]) POINT_TO_LINES[point].push(lineId);
  }

  function enumerateAllSpreads() {
    const found = [];
    function backtrack(used, chosen) {
      if (used === FULL_MASK) {
        if (chosen.length === 10) found.push([...chosen].sort((a, b) => a - b));
        return;
      }
      if (chosen.length >= 10) return;
      let first = 0;
      while ((used & (1n << BigInt(first))) !== 0n) first++;
      for (const lineId of POINT_TO_LINES[first]) {
        const mask = LINE_MASKS[lineId];
        if ((used & mask) !== 0n) continue;
        chosen.push(lineId);
        backtrack(used | mask, chosen);
        chosen.pop();
      }
    }
    backtrack(0n, []);
    const unique = new Map(found.map((spread) => [spread.join(","), spread]));
    return [...unique.values()].sort((a, b) => a.join(",").localeCompare(b.join(","))).map(Object.freeze);
  }

  let SPREAD_CACHE = null;
  function spreads() {
    if (!SPREAD_CACHE) SPREAD_CACHE = Object.freeze(enumerateAllSpreads());
    return SPREAD_CACHE;
  }

  function enumerateSpreads(limit = 256) {
    if (!Number.isInteger(limit) || limit < 1) throw new RangeError("limit must be positive integer");
    return Object.freeze(spreads().slice(0, limit));
  }

  function spreadCertificate(anchorPoint = 0) {
    if (!Number.isInteger(anchorPoint) || anchorPoint < 0 || anchorPoint >= S.POINTS.length) throw new RangeError("invalid anchorPoint");
    const catalog = spreads();
    const lineCounts = Array(S.LINES.length).fill(0);
    for (const spread of catalog) for (const lineId of spread) lineCounts[lineId]++;
    const anchorLines = POINT_TO_LINES[anchorPoint].slice().sort((a, b) => a - b);
    const sectorCounts = Object.fromEntries(anchorLines.map((lineId) => [lineId, 0]));
    let partitions = true;
    let oneAnchorLine = true;
    for (const spread of catalog) {
      const covered = new Set(spread.flatMap((lineId) => S.LINES[lineId]));
      if (spread.length !== 10 || covered.size !== 40) partitions = false;
      const chosen = spread.filter((lineId) => S.LINES[lineId].includes(anchorPoint));
      if (chosen.length !== 1) oneAnchorLine = false;
      else sectorCounts[chosen[0]]++;
    }
    const theorem = {
      spreadCount36: catalog.length === 36,
      eachSpreadPartitions40Points: partitions,
      everyLineOccurs9Times: lineCounts.length === 40 && lineCounts.every((count) => count === 9),
      anchorHas4Lines: anchorLines.length === 4,
      eachSpreadHasOneAnchorLine: oneAnchorLine,
      anchorSectorsAre9: Object.values(sectorCounts).every((count) => count === 9),
    };
    const body = {
      schema: "holotrade.w33-spread-certificate.v1",
      exactCarrier: "W(3,3)",
      anchorPoint,
      anchorPointKey: S.POINTS[anchorPoint].key,
      spreadCount: catalog.length,
      lineOccurrenceDistribution: [...lineCounts].sort((a, b) => a - b),
      anchorLines,
      sectorCounts,
      theorem,
      valid: Object.values(theorem).every(Boolean),
      evidenceBoundary: "Exact finite-geometric certificate over the repository W(3,3) carrier; not a physical network SLA or MUB hardware measurement.",
    };
    return Object.freeze({ ...body, digest: E.demoDigest(body) });
  }

  function lineForEdge(a, b) {
    if (!S.isAdjacent(a, b)) throw new Error(`points ${a},${b} do not form a W(3,3) edge`);
    const matches = [];
    for (let i = 0; i < S.LINES.length; i++) if (S.LINES[i].includes(a) && S.LINES[i].includes(b)) matches.push(i);
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
    if (catalog.length !== 36) throw new Error(`W(3,3) spread census mismatch: ${catalog.length}`);
    while (remaining.length) {
      let best = null;
      for (let spreadIndex = 0; spreadIndex < catalog.length; spreadIndex++) {
        const spread = catalog[spreadIndex];
        const lineSet = new Set(spread);
        const covered = remaining.filter((row) => lineSet.has(row.lineId));
        const unique = [];
        const seenLines = new Set();
        for (const row of covered) {
          if (seenLines.has(row.lineId)) continue;
          seenLines.add(row.lineId);
          unique.push(row);
        }
        if (!best || unique.length > best.demands.length || (unique.length === best.demands.length && spreadIndex < best.spreadIndex)) {
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
      spreadCertificateDigest: spreadCertificate(0).digest,
      conflictFree: frames.every((frame) => {
        const sites = new Set();
        for (const lineId of frame.lineIds) for (const site of S.LINES[lineId]) {
          if (sites.has(site)) return false;
          sites.add(site);
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
      for (const row of demands) { this.loads[row.lineId] += amount; this.total += amount; }
    }
    marginalCost(demands, unit = 1e-6) {
      let cost = 0;
      for (const row of demands) { const load = this.loads[row.lineId]; cost += ((load + 1) ** 2 - load ** 2) * unit; }
      return cost;
    }
    snapshot() { return Object.freeze({ loads: [...this.loads], total: this.total, max: Math.max(...this.loads), min: Math.min(...this.loads) }); }
  }

  function rankPlacement(executionEngine, plan, projection, ledger = new LineCongestionLedger(), options = {}) {
    const base = executionEngine.place(plan, { limit: options.baseLimit || 32 });
    const unit = options.shadowUnit ?? 1e-6;
    const rows = base.map((candidate) => {
      const demands = inputLineDemands(projection, candidate.node.cellPoint);
      const schedule = scheduleDemands(demands);
      const shadowCost = ledger.marginalCost(demands, unit);
      return { ...candidate, w33: { demands, schedule, shadowCost }, scoreWithW33: candidate.score + shadowCost };
    });
    rows.sort((a, b) => a.scoreWithW33 - b.scoreWithW33 || a.node.id.localeCompare(b.node.id));
    return rows.slice(0, options.limit || 8);
  }

  const API = {
    SCHEMA,
    enumerateAllSpreads,
    enumerateSpreads,
    spreads,
    spreadCertificate,
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
