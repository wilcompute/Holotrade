"use strict";

// Exact elastic topology plans on the two unitary E8 residue carriers.
//
// GAP owns the finite geometry in data/e8_unitary_elastic_ladders.json.  This
// module does not rebuild H(3,4) or H(3,9); it verifies the frozen SHA-256,
// turns an explicit maximum partial spread into nested scheduler rungs, and
// emits migration-free resize plans.  These are deliberately separate from
// the 40-point W33 shape contract: the carriers have 45 and 280 points and a
// real inventory binding still needs an attested topology adapter.

const crypto = require("node:crypto");
const path = require("node:path");
const E = require("../js/evidence.js");

const FROZEN_PATH = path.resolve(__dirname, "../data/e8_unitary_elastic_ladders.json");
const FROZEN = require(FROZEN_PATH);
const LADDER_SCHEMA = "holotrade.e8-unitary-elastic-ladder.v1";
const RESIZE_SCHEMA = "holotrade.e8-unitary-elastic-resize-plan.v1";
const CONTRACT_SCHEMA = "holotrade.e8-unitary-topology-plan.v1";

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) =>
      `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

function integer(value, name, min, max) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new RangeError(`${name} must be an integer in [${min}, ${max}]`);
  }
  return value;
}

function text(value, name) {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new TypeError(`${name} must be a non-empty string`);
  }
  return value.trim();
}

function verifyFrozen() {
  if (FROZEN.schema !== "holotrade.e8-unitary-elastic-ladders.v1") return false;
  const { sha256: claimed, ...body } = FROZEN;
  if (!/^[0-9a-f]{64}$/.test(claimed || "") || sha256(body) !== claimed) return false;
  if (FROZEN.profiles.length !== 2 || !FROZEN.theorem.maximumPartialSpreadsExhaustive) return false;
  return FROZEN.profiles.every((profile) => {
    const allPoints = profile.partialSpread.flat();
    return profile.rungs.length === profile.maxPartialSpreadLines &&
      profile.partialSpread.length === profile.maxPartialSpreadLines &&
      new Set(allPoints).size === profile.coveredPoints &&
      allPoints.every((point) => Number.isInteger(point) && point >= 1 && point <= profile.points) &&
      profile.coveredPoints + profile.holePoints === profile.points &&
      profile.maxPartialSpreadLines < profile.fullSpreadWouldNeedLines &&
      profile.hasFullSpread === false;
  });
}

if (!verifyFrozen()) throw new Error("invalid E8 unitary elastic-ladder certificate");

function profileFor(q) {
  integer(q, "q", 2, 3);
  const profile = FROZEN.profiles.find((row) => row.q === q);
  if (!profile) throw new RangeError(`unsupported unitary residue q=${q}`);
  return profile;
}

function normalizeLineOrder(profile, lineOrder) {
  const canonicalOrder = Array.from({ length: profile.maxPartialSpreadLines }, (_, i) => i + 1);
  const order = lineOrder == null ? canonicalOrder : [...lineOrder];
  const sorted = [...order].sort((a, b) => a - b);
  if (order.length !== canonicalOrder.length || new Set(order).size !== order.length ||
      sorted.some((value, i) => value !== canonicalOrder[i])) {
    throw new RangeError(`lineOrder must permute 1..${profile.maxPartialSpreadLines}`);
  }
  return order;
}

function expectedRung(q, rung) {
  const profile = profileFor(q);
  integer(rung, "rung", 1, profile.maxPartialSpreadLines);
  const s = q * q;
  const t = q;
  const vertices = (s + 1) * rung;
  return deepFreeze({
    vertices,
    inducedDegree: s + rung - 1,
    outsideAttachmentDegree: rung,
    internalEdges: ((s + 1) * rung * (s + rung - 1)) / 2,
    boundaryEdges: (s + 1) * rung * (s * t + 1 - rung),
    spectralMinimumBoundary: ((s * t + 1) * vertices * (profile.points - vertices)) / profile.points,
    addedVertices: s + 1,
    addedInternalEdges: ((s + 1) * (s + 2 * rung - 2)) / 2,
    boundaryDelta: (s + 1) * (s * t + 2 - 2 * rung),
  });
}

function buildLadder({ q, lineOrder = null } = {}) {
  const profile = profileFor(q);
  const order = normalizeLineOrder(profile, lineOrder);
  const rungs = [];
  const active = new Set();
  let previous = new Set();

  for (let i = 1; i <= order.length; i++) {
    const lineAtomId = order[i - 1];
    const addedPointIds = [...profile.partialSpread[lineAtomId - 1]].sort((a, b) => a - b);
    for (const point of addedPointIds) active.add(point);
    const pointIds = [...active].sort((a, b) => a - b);
    const expected = expectedRung(q, i);
    const frozenRung = profile.rungs[i - 1];
    const retainedPointIds = pointIds.filter((point) => previous.has(point));
    const checks = {
      wholeLineAtom: addedPointIds.length === profile.lineSize,
      atomDisjointFromPrefix: pointIds.length - previous.size === profile.lineSize,
      nestedWithoutMigration: retainedPointIds.length === (i - 1) * profile.lineSize,
      vertexFormula: pointIds.length === expected.vertices && frozenRung.vertices === expected.vertices,
      regularInside: frozenRung.inducedDegree === expected.inducedDegree,
      uniformOutside: frozenRung.outsideAttachmentDegree === expected.outsideAttachmentDegree,
      internalEdgeFormula: frozenRung.internalEdges === expected.internalEdges,
      boundaryFormula: frozenRung.boundaryEdges === expected.boundaryEdges,
      spectralEquality: frozenRung.boundaryEdges === expected.spectralMinimumBoundary &&
        frozenRung.attainsSpectralMinimum === true,
    };
    const body = {
      rung: i,
      lineAtomIds: order.slice(0, i),
      addedLineAtomId: lineAtomId,
      addedPointIds,
      pointIds,
      retainedPointIds,
      migratedPointIds: [],
      expected,
      checks,
      valid: Object.values(checks).every(Boolean),
    };
    rungs.push(deepFreeze(body));
    previous = new Set(pointIds);
  }

  const maxCovered = new Set(rungs.at(-1).pointIds);
  const maximumHolePointIds = Array.from({ length: profile.points }, (_, i) => i + 1)
    .filter((point) => !maxCovered.has(point));
  const body = {
    schema: LADDER_SCHEMA,
    q,
    fieldOrder: q * q,
    carrier: profile.identification,
    carrierPoints: profile.points,
    carrierDegree: profile.degree,
    lineSize: profile.lineSize,
    lineOrder: order,
    rungs,
    offState: { rung: 0, pointIds: [], vertices: 0 },
    maximumRung: profile.maxPartialSpreadLines,
    maximumCoveredPoints: profile.coveredPoints,
    maximumHolePoints: profile.holePoints,
    maximumHolePointIds,
    fullSpreadWouldNeedLines: profile.fullSpreadWouldNeedLines,
    sourceCertificateSha256: FROZEN.sha256,
    theorem: {
      maximumIsExhaustive: FROZEN.theorem.maximumPartialSpreadsExhaustive,
      maximumPartialSpreadCount: profile.maximumPartialSpreadCount,
      everyRungRegular: rungs.every((row) => row.checks.regularInside),
      everyRungSpectrallyOptimal: rungs.every((row) => row.checks.spectralEquality),
      everyTransitionMigrationFree: rungs.every((row) => row.checks.nestedWithoutMigration),
      hasFullSpread: false,
      holeSectorIsUnavoidableForThisCarrier: true,
    },
    evidenceBoundary:
      "Exact abstract finite-geometry topology plan. Point IDs are GAP coordinates, not host IDs; dispatch requires an inventory map plus independently verified runtime topology attestation. No literal E8-coordinate map is claimed.",
  };
  const valid = rungs.every((row) => row.valid) &&
    maximumHolePointIds.length === profile.holePoints &&
    body.maximumRung < body.fullSpreadWouldNeedLines;
  const certificate = { ...body, valid };
  return deepFreeze({ ...certificate, digest: E.demoDigest(certificate) });
}

function stateAt(ladder, rung) {
  return rung === 0 ? ladder.offState : ladder.rungs[rung - 1];
}

function resizePlan(ladder, fromRung, toRung) {
  if (!ladder || ladder.schema !== LADDER_SCHEMA || !ladder.valid) {
    throw new TypeError("a valid E8 unitary elastic ladder is required");
  }
  integer(fromRung, "fromRung", 0, ladder.maximumRung);
  integer(toRung, "toRung", 0, ladder.maximumRung);
  const from = stateAt(ladder, fromRung);
  const to = stateAt(ladder, toRung);
  const source = new Set(from.pointIds);
  const target = new Set(to.pointIds);
  const retainedPointIds = from.pointIds.filter((point) => target.has(point));
  const addedPointIds = to.pointIds.filter((point) => !source.has(point));
  const removedPointIds = from.pointIds.filter((point) => !target.has(point));
  const lo = Math.min(fromRung, toRung);
  const hi = Math.max(fromRung, toRung);
  const body = {
    schema: RESIZE_SCHEMA,
    ladderDigest: ladder.digest,
    q: ladder.q,
    fromRung,
    toRung,
    fromVertices: from.pointIds.length,
    toVertices: to.pointIds.length,
    direction: fromRung === toRung ? "hold" : (toRung > fromRung ? "expand" : "shrink"),
    retainedPointIds,
    addedPointIds,
    removedPointIds,
    migratedPointIds: [],
    changedLineAtomIds: ladder.lineOrder.slice(lo, hi),
    wholeLineAtoms: addedPointIds.length + removedPointIds.length ===
      ladder.lineSize * Math.abs(toRung - fromRung),
    retainedWorkCanStayInPlace: retainedPointIds.length ===
      ladder.lineSize * Math.min(fromRung, toRung),
    transactionBoundary:
      "This is a topology resize plan, not a distributed commit. Expansion atoms must be acquired before release and every participant must prepare or abort atomically.",
  };
  const valid = body.wholeLineAtoms && body.retainedWorkCanStayInPlace;
  const certificate = { ...body, valid };
  return deepFreeze({ ...certificate, digest: E.demoDigest(certificate) });
}

function createTopologyPlan(ladder, rung, spec = {}) {
  if (!ladder || ladder.schema !== LADDER_SCHEMA || !ladder.valid) {
    throw new TypeError("a valid E8 unitary elastic ladder is required");
  }
  integer(rung, "rung", 1, ladder.maximumRung);
  const row = ladder.rungs[rung - 1];
  const body = {
    schema: CONTRACT_SCHEMA,
    reservationId: text(spec.reservationId, "reservationId"),
    owner: text(spec.owner, "owner"),
    artifactDigest: text(spec.artifactDigest, "artifactDigest"),
    requestedSeconds: integer(spec.requestedSeconds, "requestedSeconds", 1, Number.MAX_SAFE_INTEGER),
    carrier: ladder.carrier,
    q: ladder.q,
    rung,
    pointIds: row.pointIds,
    lineAtomIds: row.lineAtomIds,
    topologyRequirements: {
      vertices: row.expected.vertices,
      exactInducedDegree: row.expected.inducedDegree,
      exactBoundaryEdges: row.expected.boundaryEdges,
      connected: true,
      wholeLineAtoms: true,
      zeroMigrationResize: true,
    },
    resources: spec.resources || {},
    evidenceRefs: [...new Set([FROZEN.sha256, ladder.digest, ...(spec.evidenceRefs || [])])],
    executionState: "ABSTRACT_TOPOLOGY_PLAN",
    dispatchable: false,
    requiredNextEvidence: "RUNTIME_TOPOLOGY_ATTESTATION",
    evidenceBoundary: ladder.evidenceBoundary,
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function verifyTopologyPlan(plan) {
  if (!plan || plan.schema !== CONTRACT_SCHEMA || plan.dispatchable !== false) return false;
  const { digest, ...body } = plan;
  return digest === E.demoDigest(body) && body.pointIds.length === body.topologyRequirements.vertices;
}

module.exports = {
  FROZEN_PATH,
  LADDER_SCHEMA,
  RESIZE_SCHEMA,
  CONTRACT_SCHEMA,
  verifyFrozen,
  expectedRung,
  buildLadder,
  resizePlan,
  createTopologyPlan,
  verifyTopologyPlan,
};
