"use strict";

// A migration-free elastic reservation ladder on W(3,3).
//
// Fix one of the 36 spreads and order its ten pairwise-disjoint isotropic
// lines.  Rung i is the union of the first i lines.  The generalized-
// quadrangle axiom says that any two spread lines are joined by a perfect
// matching, so every rung is an i-tight set with exact, closed-form metrics:
//
//   vertices       4i
//   induced degree i + 2
//   induced edges  2i(i + 2)
//   edge boundary  4i(10 - i) = m(40 - m)/4.
//
// Thus every rung attains the one-sided spectral minimum boundary, and a
// resize adds or removes a whole K4 line atom without moving retained work.
// Tight-set union is classical finite geometry; treating an ordered spread as
// an executable elastic reservation object is the scheduler synthesis here.

const S = require("../js/substrate.js");
const W = require("../js/w33-scheduler.js");
const E = require("../js/evidence.js");
const R = require("../reservations/shape-reservation.js");

const SCHEMA = "holotrade.w33-elastic-spread-ladder.v1";

function integer(value, name, min, max) {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new RangeError(`${name} must be an integer in [${min}, ${max}]`);
  }
  return value;
}

function sorted(values) {
  return [...values].sort((a, b) => a - b);
}

function sameSet(a, b) {
  const aa = sorted(a);
  const bb = sorted(b);
  return aa.length === bb.length && aa.every((x, i) => x === bb[i]);
}

function normalizeLineOrder(spreadIndex, lineOrder) {
  const catalog = W.spreads();
  integer(spreadIndex, "spreadIndex", 0, catalog.length - 1);
  const spread = catalog[spreadIndex];
  const order = lineOrder == null ? [...spread] : [...lineOrder];
  if (order.length !== 10 || new Set(order).size !== 10 || !sameSet(order, spread)) {
    throw new RangeError("lineOrder must be a permutation of the selected spread's ten lines");
  }
  return order;
}

function neighbourhoodProfile(points) {
  const set = new Set(points);
  const inside = new Set();
  const outside = new Set();
  for (let v = 0; v < S.CONST.points; v++) {
    const count = S.ADJ[v].filter((u) => set.has(u)).length;
    (set.has(v) ? inside : outside).add(count);
  }
  return Object.freeze({
    inside: Object.freeze(sorted(inside)),
    outside: Object.freeze(sorted(outside)),
  });
}

function expectedRung(i) {
  integer(i, "rung", 1, 10);
  const vertices = 4 * i;
  return Object.freeze({
    vertices,
    inducedDegree: i + 2,
    outsideAttachmentDegree: i === 10 ? null : i,
    internalEdges: 2 * i * (i + 2),
    boundaryEdges: 4 * i * (10 - i),
    spectralMinimumBoundary: (vertices * (40 - vertices)) / 4,
    addedVertices: 4,
    addedInternalEdges: 4 * i + 2,
    boundaryDelta: 44 - 8 * i,
  });
}

function buildLadder({ spreadIndex = 0, lineOrder = null } = {}) {
  const order = normalizeLineOrder(spreadIndex, lineOrder);
  const rungs = [];
  const active = new Set();
  let previous = new Set();

  for (let i = 1; i <= 10; i++) {
    const addedLineId = order[i - 1];
    const addedPoints = sorted(S.LINES[addedLineId]);
    for (const point of addedPoints) active.add(point);
    const points = sorted(active);
    const shape = R.shapeCertificate(points);
    const profile = neighbourhoodProfile(points);
    const expected = expectedRung(i);
    const retainedPoints = points.filter((point) => previous.has(point));
    const newPoints = points.filter((point) => !previous.has(point));
    const checks = Object.freeze({
      fourPointAtom: addedPoints.length === 4,
      atomDisjointFromPrefix: newPoints.length === 4,
      nestedWithoutMigration: retainedPoints.length === 4 * (i - 1),
      vertexFormula: shape.vertices === expected.vertices,
      regularInside: profile.inside.length === 1 && profile.inside[0] === expected.inducedDegree,
      uniformOutside: i === 10
        ? profile.outside.length === 0
        : profile.outside.length === 1 && profile.outside[0] === expected.outsideAttachmentDegree,
      internalEdgeFormula: shape.internalEdges === expected.internalEdges,
      boundaryFormula: shape.boundaryEdges === expected.boundaryEdges,
      spectralEquality:
        shape.boundaryEdges === expected.spectralMinimumBoundary &&
        shape.boundaryEdges * 4 === shape.spectralBoundary.lower.numerator,
      connected: shape.connected,
    });
    const body = {
      rung: i,
      lineIds: Object.freeze(order.slice(0, i)),
      addedLineId,
      addedPoints: Object.freeze(addedPoints),
      points: Object.freeze(points),
      retainedPoints: Object.freeze(retainedPoints),
      migratedPoints: Object.freeze([]),
      profile,
      shape,
      expected,
      checks,
      valid: Object.values(checks).every(Boolean),
    };
    rungs.push(Object.freeze(body));
    previous = new Set(points);
  }

  const body = {
    schema: SCHEMA,
    carrier: "W(3,3) point graph SRG(40,12,2,4)",
    spreadIndex,
    lineOrder: Object.freeze([...order]),
    rungs: Object.freeze(rungs),
    theorem: Object.freeze({
      spreadCount: W.spreads().length,
      rungCount: rungs.length,
      sizes: Object.freeze(rungs.map((row) => row.shape.vertices)),
      everyRungConnected: rungs.every((row) => row.shape.connected),
      everyRungRegular: rungs.every((row) => row.profile.inside.length === 1),
      everyRungSpectrallyOptimal: rungs.every((row) => row.checks.spectralEquality),
      everyTransitionMigrationFree: rungs.every((row) => row.checks.nestedWithoutMigration),
      wholeSpreadClosesCarrier: rungs[9].shape.vertices === 40 && rungs[9].shape.boundaryEdges === 0,
    }),
    evidenceBoundary:
      "Exact finite-graph reservation geometry. A production resize still requires a distributed atomic prepare/commit/abort transaction and does not inherit a hardware SLA from this certificate.",
    priorArt:
      "The tight-set union theorem is classical (Bamberg-Law-Penttila, Combinatorica 29 (2009), DOI 10.1007/s00493-009-2179-x); the ordered-spread elastic scheduler object is the applied synthesis.",
  };
  const valid = Object.values(body.theorem).every((value) => value === true || Number.isInteger(value) || Array.isArray(value));
  const certificate = { ...body, valid };
  return Object.freeze({ ...certificate, digest: E.demoDigest(certificate) });
}

function resizePlan(ladder, fromRung, toRung) {
  if (!ladder || ladder.schema !== SCHEMA || !ladder.valid) throw new TypeError("a valid elastic ladder is required");
  integer(fromRung, "fromRung", 1, 10);
  integer(toRung, "toRung", 1, 10);
  const from = ladder.rungs[fromRung - 1];
  const to = ladder.rungs[toRung - 1];
  const a = new Set(from.points);
  const b = new Set(to.points);
  const retainedPoints = from.points.filter((point) => b.has(point));
  const addedPoints = to.points.filter((point) => !a.has(point));
  const removedPoints = from.points.filter((point) => !b.has(point));
  const lo = Math.min(fromRung, toRung);
  const hi = Math.max(fromRung, toRung);
  const changedLineIds = ladder.lineOrder.slice(lo, hi);
  const body = {
    schema: "holotrade.w33-elastic-resize-plan.v1",
    ladderDigest: ladder.digest,
    spreadIndex: ladder.spreadIndex,
    fromRung,
    toRung,
    fromVertices: from.shape.vertices,
    toVertices: to.shape.vertices,
    direction: toRung === fromRung ? "hold" : (toRung > fromRung ? "expand" : "shrink"),
    retainedPoints: Object.freeze(retainedPoints),
    addedPoints: Object.freeze(addedPoints),
    removedPoints: Object.freeze(removedPoints),
    migratedPoints: Object.freeze([]),
    changedLineIds: Object.freeze([...changedLineIds]),
    wholeLineAtoms: (addedPoints.length + removedPoints.length) === 4 * Math.abs(toRung - fromRung),
    retainedWorkCanStayInPlace: retainedPoints.length === 4 * Math.min(fromRung, toRung),
    sourceSpectrallyOptimal: from.checks.spectralEquality,
    targetSpectrallyOptimal: to.checks.spectralEquality,
    transactionBoundary:
      "This is an exact resize plan, not the transaction itself; acquire expansion atoms before release and commit all participants atomically.",
  };
  const valid = body.wholeLineAtoms && body.retainedWorkCanStayInPlace &&
    body.sourceSpectrallyOptimal && body.targetSpectrallyOptimal;
  const certificate = { ...body, valid };
  return Object.freeze({ ...certificate, digest: E.demoDigest(certificate) });
}

function bestAvailableLadder({ unavailable = [], targetRung = 10 } = {}) {
  integer(targetRung, "targetRung", 1, 10);
  const blocked = unavailable instanceof Set ? unavailable : new Set(unavailable);
  for (const point of blocked) integer(point, "unavailable point", 0, 39);

  let best = null;
  const catalog = W.spreads();
  for (let spreadIndex = 0; spreadIndex < catalog.length; spreadIndex++) {
    const freeLines = [];
    const blockedLines = [];
    for (const lineId of catalog[spreadIndex]) {
      const bucket = S.LINES[lineId].every((point) => !blocked.has(point)) ? freeLines : blockedLines;
      bucket.push(lineId);
    }
    freeLines.sort((a, b) => a - b);
    blockedLines.sort((a, b) => a - b);
    const candidate = { spreadIndex, freeLines, blockedLines };
    if (!best || candidate.freeLines.length > best.freeLines.length ||
      (candidate.freeLines.length === best.freeLines.length && spreadIndex < best.spreadIndex)) best = candidate;
  }

  const maxRung = best.freeLines.length;
  const order = [...best.freeLines, ...best.blockedLines];
  const ladder = buildLadder({ spreadIndex: best.spreadIndex, lineOrder: order });
  if (maxRung < targetRung) {
    return Object.freeze({
      ok: false,
      requestedRung: targetRung,
      requestedVertices: 4 * targetRung,
      maxRung,
      maxVertices: 4 * maxRung,
      spreadIndex: best.spreadIndex,
      ladder,
      reason: `no spread contains ${targetRung} fully available line atoms; best has ${maxRung}`,
    });
  }
  return Object.freeze({
    ok: true,
    requestedRung: targetRung,
    requestedVertices: 4 * targetRung,
    maxRung,
    maxVertices: 4 * maxRung,
    spreadIndex: best.spreadIndex,
    ladder,
    rung: ladder.rungs[targetRung - 1],
  });
}

function createRungContract(ladder, rung, spec = {}) {
  if (!ladder || ladder.schema !== SCHEMA || !ladder.valid) throw new TypeError("a valid elastic ladder is required");
  integer(rung, "rung", 1, 10);
  const row = ladder.rungs[rung - 1];
  return R.createContract({
    ...spec,
    points: row.points,
    evidenceRefs: [...(spec.evidenceRefs || []), ladder.digest, row.shape.digest],
    topology: {
      connected: true,
      minDegree: row.expected.inducedDegree,
      ...(spec.topology || {}),
    },
  });
}

module.exports = {
  SCHEMA,
  expectedRung,
  buildLadder,
  resizePlan,
  bestAvailableLadder,
  createRungContract,
};
