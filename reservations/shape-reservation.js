"use strict";

// Atomic, topology-bearing multi-node reservations on the exact W(3,3)
// point graph.  This is a control-plane prototype: it locks named capacity,
// executes a two-phase prepare/commit protocol, and meters each delivered node
// separately.  It does not start a hypervisor or implement distributed
// consensus.  The companion runtime adapter can sign the resulting receipt.

const crypto = require("node:crypto");
const S = require("../js/substrate.js");
const E = require("../js/evidence.js");

const CONTRACT_SCHEMA = "holotrade.shape-reservation.v1";
const RECEIPT_SCHEMA = "holotrade.shape-delivery-receipt.v1";

const STATE = Object.freeze({
  PROPOSED: "PROPOSED",
  PREPARED: "PREPARED",
  COMMITTED: "COMMITTED",
  RUNNING: "RUNNING",
  SETTLED: "SETTLED",
  FAILED: "FAILED",
  ABORTED: "ABORTED",
});

function canonicalJson(value) {
  return E.canonicalJson(value);
}

function sha256(value) {
  const bytes = Buffer.isBuffer(value)
    ? value
    : Buffer.from(typeof value === "string" ? value : canonicalJson(value), "utf8");
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

function assertText(value, name) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${name} must be a non-empty string`);
  return value.trim();
}

function finite(value, name, { min = -Infinity, integer = false } = {}) {
  const out = Number(value);
  if (!Number.isFinite(out) || out < min || (integer && !Number.isInteger(out))) {
    throw new RangeError(`${name} must be ${integer ? "an integer" : "a number"} >= ${min}`);
  }
  return out;
}

function pointIndex(value) {
  if (Number.isInteger(value) && value >= 0 && value < S.CONST.points) return value;
  if (typeof value === "string") {
    if (S.POINT_INDEX.has(value)) return S.POINT_INDEX.get(value);
    if (/^\d+$/.test(value)) {
      const parsed = Number(value);
      if (parsed >= 0 && parsed < S.CONST.points) return parsed;
    }
  }
  throw new RangeError(`invalid W(3,3) point: ${String(value)}`);
}

function normalizePoints(values) {
  if (!Array.isArray(values) || values.length === 0) throw new TypeError("points must be a non-empty array");
  const points = [...new Set(values.map(pointIndex))].sort((a, b) => a - b);
  if (points.length !== values.length) throw new RangeError("points must be unique");
  return points;
}

function components(points, neighbours) {
  const unseen = new Set(points);
  const out = [];
  while (unseen.size) {
    const start = unseen.values().next().value;
    const queue = [start];
    const part = [];
    unseen.delete(start);
    while (queue.length) {
      const at = queue.shift();
      part.push(at);
      for (const next of neighbours.get(at)) {
        if (unseen.delete(next)) queue.push(next);
      }
    }
    out.push(part.sort((a, b) => a - b));
  }
  return out.sort((a, b) => a[0] - b[0]);
}

function inducedDiameter(points, neighbours) {
  if (points.length <= 1) return 0;
  let diameter = 0;
  for (const source of points) {
    const dist = new Map([[source, 0]]);
    const queue = [source];
    while (queue.length) {
      const at = queue.shift();
      for (const next of neighbours.get(at)) {
        if (!dist.has(next)) {
          dist.set(next, dist.get(at) + 1);
          queue.push(next);
        }
      }
    }
    if (dist.size !== points.length) return null;
    diameter = Math.max(diameter, ...dist.values());
  }
  return diameter;
}

function connectedAfterRemoving(points, removed) {
  const remain = points.filter((p) => !removed.has(p));
  if (remain.length <= 1) return true;
  const allowed = new Set(remain);
  const seen = new Set([remain[0]]);
  const queue = [remain[0]];
  while (queue.length) {
    const at = queue.shift();
    for (const next of S.ADJ[at]) {
      if (allowed.has(next) && !seen.has(next)) {
        seen.add(next);
        queue.push(next);
      }
    }
  }
  return seen.size === remain.length;
}

function combinations(values, choose, visit, start = 0, picked = []) {
  if (picked.length === choose) return visit(picked);
  for (let i = start; i <= values.length - (choose - picked.length); i++) {
    picked.push(values[i]);
    const stop = combinations(values, choose, visit, i + 1, picked);
    picked.pop();
    if (stop === false) return false;
  }
  return true;
}

function survivesFailures(points, count) {
  const f = finite(count, "failure tolerance", { min: 0, integer: true });
  if (f === 0 || points.length <= 1) return true;
  if (f > 3) throw new RangeError("exact failure certification is capped at three simultaneous node failures");
  if (points.length <= f) return false;
  for (let size = 1; size <= f; size++) {
    let ok = true;
    combinations(points, size, (removed) => {
      if (!connectedAfterRemoving(points, new Set(removed))) {
        ok = false;
        return false;
      }
      return true;
    });
    if (!ok) return false;
  }
  return true;
}

function shapeCertificate(values) {
  const points = normalizePoints(values);
  const set = new Set(points);
  const neighbours = new Map(points.map((p) => [p, S.ADJ[p].filter((q) => set.has(q))]));
  const degreeSequence = points.map((p) => neighbours.get(p).length).sort((a, b) => a - b);
  const internalEdges = degreeSequence.reduce((sum, d) => sum + d, 0) / 2;
  const boundaryEdges = points.reduce((sum, p) => sum + S.ADJ[p].filter((q) => !set.has(q)).length, 0);
  const parts = components(points, neighbours);
  const m = points.length;

  // For A(W(3,3)) with spectrum 12, 2, -4, the nonzero Laplacian
  // spectrum is 10 and 16.  For the centered indicator of an m-subset,
  // ||x-m/40||^2 = m(40-m)/40, hence the exact spectral corridor below.
  const lowerNumerator = m * (S.CONST.points - m);
  const upperNumerator = 2 * lowerNumerator;
  const spectralBoundary = {
    theorem: "lambda_2(L)||x_perp||^2 <= boundary <= lambda_max(L)||x_perp||^2",
    laplacianEigenvalues: [0, 10, 16],
    lower: { numerator: lowerNumerator, denominator: 4, rounded: Math.ceil(lowerNumerator / 4) },
    upper: { numerator: upperNumerator, denominator: 5, rounded: Math.floor(upperNumerator / 5) },
    realizedInsideCorridor:
      boundaryEdges * 4 >= lowerNumerator && boundaryEdges * 5 <= upperNumerator,
  };
  const body = {
    schema: "holotrade.w33-induced-shape.v1",
    points,
    pointKeys: points.map((p) => S.POINTS[p].key),
    vertices: m,
    internalEdges,
    boundaryEdges,
    degreeSequence,
    minDegree: degreeSequence[0],
    maxDegree: degreeSequence[degreeSequence.length - 1],
    components: parts,
    connected: parts.length === 1,
    inducedDiameter: inducedDiameter(points, neighbours),
    isIsotropicLine: m === 4 && S.LINES.some((line) => line.every((p) => set.has(p))),
    spectralBoundary,
  };
  return Object.freeze({ ...body, digest: sha256(body) });
}

function topologyDecision(certificate, requirements = {}) {
  const r = {
    connected: requirements.connected !== false,
    isotropicLine: requirements.isotropicLine === true,
    maxDiameter: requirements.maxDiameter == null ? null : finite(requirements.maxDiameter, "maxDiameter", { min: 0, integer: true }),
    minDegree: requirements.minDegree == null ? null : finite(requirements.minDegree, "minDegree", { min: 0, integer: true }),
    minBoundary: requirements.minBoundary == null ? null : finite(requirements.minBoundary, "minBoundary", { min: 0, integer: true }),
    survivesNodeFailures: requirements.survivesNodeFailures == null
      ? 0
      : finite(requirements.survivesNodeFailures, "survivesNodeFailures", { min: 0, integer: true }),
  };
  const blockers = [];
  if (r.connected && !certificate.connected) blockers.push("SHAPE_DISCONNECTED");
  if (r.isotropicLine && !certificate.isIsotropicLine) blockers.push("NOT_ISOTROPIC_LINE");
  if (r.maxDiameter != null && (certificate.inducedDiameter == null || certificate.inducedDiameter > r.maxDiameter)) {
    blockers.push("DIAMETER_EXCEEDED");
  }
  if (r.minDegree != null && certificate.minDegree < r.minDegree) blockers.push("MIN_DEGREE_UNMET");
  if (r.minBoundary != null && certificate.boundaryEdges < r.minBoundary) blockers.push("BOUNDARY_UNMET");
  let failureCertified = null;
  if (r.survivesNodeFailures > 0) {
    failureCertified = survivesFailures(certificate.points, r.survivesNodeFailures);
    if (!failureCertified) blockers.push("FAILURE_TOLERANCE_UNMET");
  }
  const body = {
    schema: "holotrade.w33-shape-admission.v1",
    shapeDigest: certificate.digest,
    requirements: r,
    failureCertified,
    ok: blockers.length === 0,
    blockers,
  };
  return Object.freeze({ ...body, digest: sha256(body) });
}

function createContract(spec = {}) {
  const shape = shapeCertificate(spec.points);
  const topology = topologyDecision(shape, spec.topology || {});
  if (!topology.ok) throw new Error(`topology contract refused: ${topology.blockers.join(",")}`);
  const requestedSeconds = finite(spec.requestedSeconds, "requestedSeconds", { min: 0.001 });
  const perNode = {
    vcpus: finite(spec.resources?.perNode?.vcpus ?? 1, "per-node vcpus", { min: 1, integer: true }),
    memoryMiB: finite(spec.resources?.perNode?.memoryMiB ?? 128, "per-node memoryMiB", { min: 1, integer: true }),
  };
  const validFrom = finite(spec.validFrom ?? 0, "validFrom", { min: 0 });
  const validUntil = finite(spec.validUntil ?? Number.MAX_SAFE_INTEGER, "validUntil", { min: validFrom });
  const mode = spec.failurePolicy?.mode || "all-or-nothing";
  if (!["all-or-nothing", "minimum-survivors"].includes(mode)) throw new RangeError(`unsupported failure mode: ${mode}`);
  const minSurvivors = mode === "all-or-nothing"
    ? shape.vertices
    : finite(spec.failurePolicy?.minSurvivors, "minSurvivors", { min: 1, integer: true });
  if (minSurvivors > shape.vertices) throw new RangeError("minSurvivors exceeds shape size");
  const maxPricePerNodeSecond = spec.maxPricePerNodeSecond == null
    ? null
    : finite(spec.maxPricePerNodeSecond, "maxPricePerNodeSecond", { min: 0 });
  const artifactDigest = assertText(spec.artifactDigest, "artifactDigest");
  if (!/^sha256:[0-9a-f]{64}$/i.test(artifactDigest)) {
    throw new TypeError("artifactDigest must be a full sha256:<64 hex> digest");
  }
  const body = {
    schema: CONTRACT_SCHEMA,
    reservationId: assertText(spec.reservationId, "reservationId"),
    owner: assertText(spec.owner, "owner"),
    nonce: assertText(spec.nonce, "nonce"),
    artifactDigest: artifactDigest.toLowerCase(),
    points: shape.points,
    shapeDigest: shape.digest,
    topologyDigest: topology.digest,
    topologyRequirements: topology.requirements,
    resources: { perNode },
    requestedSeconds,
    requestedNodeSeconds: requestedSeconds * shape.vertices,
    failurePolicy: { mode, minSurvivors },
    maxPricePerNodeSecond,
    evidenceRefs: [...new Set((spec.evidenceRefs || []).map((x) => assertText(x, "evidence ref")))].sort(),
    validFrom,
    validUntil,
  };
  return Object.freeze({ ...body, digest: sha256(body), shape, topology });
}

function verifyContract(contract) {
  if (!contract || contract.schema !== CONTRACT_SCHEMA) return false;
  const body = { ...contract };
  delete body.digest;
  delete body.shape;
  delete body.topology;
  return sha256(body) === contract.digest &&
    contract.shape && contract.shape.digest === contract.shapeDigest &&
    contract.topology && contract.topology.digest === contract.topologyDigest &&
    shapeCertificate(contract.points).digest === contract.shapeDigest;
}

class ShapeReservationLedger {
  constructor(inventory = []) {
    this.inventory = new Map();
    this.locks = new Map();
    this.reservations = new Map();
    for (const item of inventory) this.addInventory(item);
  }

  addInventory(spec) {
    const point = pointIndex(spec.point);
    if (this.inventory.has(point)) throw new Error(`inventory already exists at point ${point}`);
    const row = {
      point,
      nodeId: assertText(spec.nodeId, "nodeId"),
      vcpus: finite(spec.vcpus ?? 1, "vcpus", { min: 1, integer: true }),
      memoryMiB: finite(spec.memoryMiB ?? 128, "memoryMiB", { min: 1, integer: true }),
      pricePerNodeSecond: finite(spec.pricePerNodeSecond ?? 0, "pricePerNodeSecond", { min: 0 }),
      available: spec.available !== false,
      evidenceOk: spec.evidenceOk !== false,
    };
    this.inventory.set(point, row);
    return row;
  }

  setNodeState(point, patch = {}) {
    const row = this.inventory.get(pointIndex(point));
    if (!row) throw new Error(`unknown inventory point ${point}`);
    if (patch.available !== undefined) row.available = patch.available === true;
    if (patch.evidenceOk !== undefined) row.evidenceOk = patch.evidenceOk === true;
    if (patch.pricePerNodeSecond !== undefined) {
      row.pricePerNodeSecond = finite(patch.pricePerNodeSecond, "pricePerNodeSecond", { min: 0 });
    }
    return { ...row };
  }

  prepare(contract, now = 0) {
    if (!verifyContract(contract)) return { ok: false, code: "BAD_CONTRACT" };
    if (this.reservations.has(contract.reservationId)) return { ok: false, code: "DUPLICATE_RESERVATION" };
    if (now < contract.validFrom || now > contract.validUntil) return { ok: false, code: "WINDOW" };
    const blockers = [];
    const selected = [];
    for (const point of contract.points) {
      const node = this.inventory.get(point);
      if (!node) blockers.push({ point, code: "MISSING_NODE" });
      else if (!node.available) blockers.push({ point, code: "NODE_UNAVAILABLE" });
      else if (!node.evidenceOk) blockers.push({ point, code: "EVIDENCE_POLICY" });
      else if (node.vcpus < contract.resources.perNode.vcpus || node.memoryMiB < contract.resources.perNode.memoryMiB) {
        blockers.push({ point, code: "CAPACITY" });
      } else if (contract.maxPricePerNodeSecond != null && node.pricePerNodeSecond > contract.maxPricePerNodeSecond) {
        blockers.push({ point, code: "PRICE_CAP" });
      } else if (this.locks.has(point)) blockers.push({ point, code: "LOCKED", owner: this.locks.get(point) });
      else selected.push(node);
    }
    if (blockers.length) return { ok: false, code: "PREPARE_REFUSED", blockers };

    // State mutation happens only after every participant has voted yes.
    for (const node of selected) this.locks.set(node.point, contract.reservationId);
    const record = {
      contract,
      state: STATE.PREPARED,
      preparedAt: now,
      committedAt: null,
      startedAt: null,
      elapsedSeconds: 0,
      nodes: new Map(selected.map((node) => [node.point, {
        point: node.point,
        nodeId: node.nodeId,
        rate: node.pricePerNodeSecond,
        deliveredSeconds: 0,
        cost: 0,
        failed: false,
      }])),
      failures: [],
      receipt: null,
    };
    this.reservations.set(contract.reservationId, record);
    const body = {
      schema: "holotrade.shape-prepare.v1",
      reservationId: contract.reservationId,
      contractDigest: contract.digest,
      preparedAt: now,
      participants: selected.map((node) => ({ point: node.point, nodeId: node.nodeId })),
      state: record.state,
    };
    return { ok: true, record, certificate: { ...body, digest: sha256(body) } };
  }

  commit(reservationId, now = 0) {
    const record = this.reservations.get(reservationId);
    if (!record) return { ok: false, code: "NOT_FOUND" };
    if (record.state === STATE.COMMITTED || record.state === STATE.RUNNING) return { ok: true, idempotent: true, record };
    if (record.state !== STATE.PREPARED) return { ok: false, code: "BAD_STATE", state: record.state };
    const blockers = [];
    for (const point of record.contract.points) {
      const node = this.inventory.get(point);
      if (this.locks.get(point) !== reservationId) blockers.push({ point, code: "LOCK_LOST" });
      else if (!node || !node.available) blockers.push({ point, code: "NODE_UNAVAILABLE" });
      else if (!node.evidenceOk) blockers.push({ point, code: "EVIDENCE_POLICY" });
      else if (record.contract.maxPricePerNodeSecond != null && node.pricePerNodeSecond > record.contract.maxPricePerNodeSecond) {
        blockers.push({ point, code: "PRICE_CAP" });
      }
    }
    if (blockers.length) {
      this._release(record);
      record.state = STATE.ABORTED;
      return { ok: false, code: "COMMIT_REFUSED", blockers, rolledBack: true };
    }
    record.state = STATE.COMMITTED;
    record.committedAt = now;
    return { ok: true, record };
  }

  start(reservationId, now = 0) {
    const record = this.reservations.get(reservationId);
    if (!record) return { ok: false, code: "NOT_FOUND" };
    if (record.state === STATE.RUNNING) return { ok: true, idempotent: true, record };
    if (record.state !== STATE.COMMITTED) return { ok: false, code: "BAD_STATE", state: record.state };
    record.state = STATE.RUNNING;
    record.startedAt = now;
    return { ok: true, record };
  }

  meter(reservationId, dtSeconds, observations = {}) {
    const record = this.reservations.get(reservationId);
    if (!record) return { ok: false, code: "NOT_FOUND" };
    if (record.state !== STATE.RUNNING) return { ok: false, code: "BAD_STATE", state: record.state };
    const dt = finite(dtSeconds, "dtSeconds", { min: 0.000001 });
    const remainingWall = Math.max(0, record.contract.requestedSeconds - record.elapsedSeconds);
    const slice = Math.min(dt, remainingWall);
    const active = [];
    for (const point of record.contract.points) {
      const node = this.inventory.get(point);
      const explicit = Object.hasOwn(observations, point) ? observations[point] : undefined;
      const healthy = explicit === undefined ? !!(node && node.available && node.evidenceOk) : explicit === true;
      const meter = record.nodes.get(point);
      if (!healthy) {
        if (!meter.failed) record.failures.push({ point, atSecond: record.elapsedSeconds, code: "NODE_FAILED" });
        meter.failed = true;
      } else {
        active.push(meter);
      }
    }

    if (active.length < record.contract.failurePolicy.minSurvivors) {
      record.state = STATE.FAILED;
      this._release(record);
      record.receipt = this._receipt(record, "minimum-survivors-unmet");
      return { ok: false, code: "MINIMUM_SURVIVORS", receipt: record.receipt };
    }

    for (const meter of active) {
      meter.deliveredSeconds += slice;
      const charge = slice * meter.rate;
      meter.cost += charge;
    }
    record.elapsedSeconds += slice;
    if (record.elapsedSeconds >= record.contract.requestedSeconds) {
      record.state = STATE.SETTLED;
      this._release(record);
      record.receipt = this._receipt(record, "requested-wall-time-reached");
    }
    return {
      ok: true,
      state: record.state,
      wallSeconds: record.elapsedSeconds,
      activeNodes: active.length,
      receipt: record.receipt,
    };
  }

  abort(reservationId, reason = "operator-abort") {
    const record = this.reservations.get(reservationId);
    if (!record) return { ok: false, code: "NOT_FOUND" };
    if ([STATE.ABORTED, STATE.FAILED, STATE.SETTLED].includes(record.state)) {
      return { ok: true, idempotent: true, state: record.state, receipt: record.receipt };
    }
    record.state = STATE.ABORTED;
    this._release(record);
    record.receipt = this._receipt(record, reason);
    return { ok: true, state: record.state, receipt: record.receipt };
  }

  _release(record) {
    for (const point of record.contract.points) {
      if (this.locks.get(point) === record.contract.reservationId) this.locks.delete(point);
    }
  }

  _receipt(record, reason) {
    const perNode = [...record.nodes.values()].map((node) => ({ ...node })).sort((a, b) => a.point - b.point);
    const deliveredNodeSeconds = perNode.reduce((sum, node) => sum + node.deliveredSeconds, 0);
    const cost = perNode.reduce((sum, node) => sum + node.cost, 0);
    const body = {
      schema: RECEIPT_SCHEMA,
      reservationId: record.contract.reservationId,
      contractDigest: record.contract.digest,
      shapeDigest: record.contract.shapeDigest,
      state: record.state,
      reason,
      requestedNodeSeconds: record.contract.requestedNodeSeconds,
      deliveredNodeSeconds,
      shortfallNodeSeconds: record.contract.requestedNodeSeconds - deliveredNodeSeconds,
      cost,
      perNode,
      failures: [...record.failures],
      accounting: "sum of per-node delivered seconds; failed or unobserved slices are not billed",
      cryptographicallySigned: false,
    };
    return Object.freeze({ ...body, digest: sha256(body) });
  }
}

module.exports = {
  CONTRACT_SCHEMA,
  RECEIPT_SCHEMA,
  STATE,
  canonicalJson,
  sha256,
  shapeCertificate,
  topologyDecision,
  survivesFailures,
  createContract,
  verifyContract,
  ShapeReservationLedger,
};
