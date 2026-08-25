"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const S = require("../js/substrate.js");
const R = require("../reservations/shape-reservation.js");

const DIGEST = `sha256:${"ab".repeat(32)}`;

function line() {
  return [...S.LINES[0]];
}

function contract(overrides = {}) {
  return R.createContract({
    reservationId: "RSV-LINE-001",
    owner: "demo-buyer",
    nonce: "nonce-001",
    artifactDigest: DIGEST,
    points: line(),
    requestedSeconds: 10,
    resources: { perNode: { vcpus: 2, memoryMiB: 256 } },
    topology: { connected: true, isotropicLine: true, maxDiameter: 1, minDegree: 3, survivesNodeFailures: 2 },
    failurePolicy: { mode: "all-or-nothing" },
    maxPricePerNodeSecond: 0.02,
    validFrom: 0,
    validUntil: 100,
    ...overrides,
  });
}

function inventory(points = line()) {
  return points.map((point) => ({
    point,
    nodeId: `NODE-${point}`,
    vcpus: 4,
    memoryMiB: 1024,
    pricePerNodeSecond: 0.01 + point / 100000,
    available: true,
    evidenceOk: true,
  }));
}

test("an isotropic line is a canonical K4 reservation shape", () => {
  const a = R.shapeCertificate(line());
  const b = R.shapeCertificate([...line()].reverse());
  assert.equal(a.digest, b.digest, "point order does not change the shape identity");
  assert.equal(a.vertices, 4);
  assert.equal(a.internalEdges, 6);
  assert.equal(a.boundaryEdges, 36);
  assert.deepEqual(a.degreeSequence, [3, 3, 3, 3]);
  assert.equal(a.connected, true);
  assert.equal(a.inducedDiameter, 1);
  assert.equal(a.isIsotropicLine, true);
  assert.equal(a.spectralBoundary.realizedInsideCorridor, true);
  assert.equal(R.survivesFailures(a.points, 2), true, "K4 stays connected after any two node failures");
});

test("the Laplacian corridor holds for every subset and closes the exact bisection", () => {
  const full = R.shapeCertificate(S.POINTS.map((p) => p.index));
  assert.equal(full.boundaryEdges, 0);
  assert.equal(full.spectralBoundary.lower.rounded, 0);
  assert.equal(full.spectralBoundary.upper.rounded, 0);

  const cut = R.shapeCertificate(S.BISECTION_LEFT);
  assert.equal(cut.vertices, 20);
  assert.equal(cut.boundaryEdges, 100);
  assert.equal(cut.spectralBoundary.lower.rounded, 100);
  assert.equal(cut.spectralBoundary.realizedInsideCorridor, true);

  const rng = S.rng("shape-corridor-regression");
  for (let trial = 0; trial < 200; trial++) {
    const size = 1 + Math.floor(rng() * 40);
    const points = S.POINTS.map((p) => p.index)
      .sort(() => rng() - 0.5)
      .slice(0, size);
    assert.equal(R.shapeCertificate(points).spectralBoundary.realizedInsideCorridor, true);
  }
});

test("topology admission refuses disconnected or under-connected shapes", () => {
  const a = 0;
  const b = S.POINTS.find((p) => p.index !== a && !S.isAdjacent(a, p.index)).index;
  const shape = R.shapeCertificate([a, b]);
  assert.equal(shape.connected, false);
  const decision = R.topologyDecision(shape, { connected: true, minDegree: 1 });
  assert.equal(decision.ok, false);
  assert.ok(decision.blockers.includes("SHAPE_DISCONNECTED"));
  assert.ok(decision.blockers.includes("MIN_DEGREE_UNMET"));
  assert.throws(() => R.createContract({
    reservationId: "bad", owner: "buyer", nonce: "n", artifactDigest: DIGEST,
    points: [a, b], requestedSeconds: 1, topology: { connected: true },
  }), /topology contract refused/);
});

test("prepare is atomic: one negative vote produces no partial locks", () => {
  const rows = inventory();
  rows[2].available = false;
  const ledger = new R.ShapeReservationLedger(rows);
  const result = ledger.prepare(contract(), 1);
  assert.equal(result.ok, false);
  assert.equal(result.code, "PREPARE_REFUSED");
  assert.equal(ledger.locks.size, 0);
  assert.equal(ledger.reservations.size, 0);
});

test("prepare/commit holds every named node and conflicting shapes fail closed", () => {
  const ledger = new R.ShapeReservationLedger(inventory());
  const c = contract();
  const prepared = ledger.prepare(c, 1);
  assert.equal(prepared.ok, true);
  assert.equal(ledger.locks.size, 4);
  assert.match(prepared.certificate.digest, /^sha256:[0-9a-f]{64}$/);

  const conflict = contract({ reservationId: "RSV-CONFLICT", nonce: "nonce-002" });
  assert.equal(ledger.prepare(conflict, 1).code, "PREPARE_REFUSED");
  assert.equal(ledger.commit(c.reservationId, 2).ok, true);
  assert.equal(ledger.commit(c.reservationId, 2).idempotent, true);
  assert.equal(ledger.start(c.reservationId, 3).ok, true);
});

test("commit revalidates every participant and rolls every lock back on drift", () => {
  const ledger = new R.ShapeReservationLedger(inventory());
  const c = contract();
  assert.equal(ledger.prepare(c, 1).ok, true);
  ledger.setNodeState(c.points[1], { evidenceOk: false });
  const result = ledger.commit(c.reservationId, 2);
  assert.equal(result.ok, false);
  assert.equal(result.rolledBack, true);
  assert.equal(ledger.locks.size, 0);
  assert.equal(ledger.reservations.get(c.reservationId).state, R.STATE.ABORTED);
});

test("all-or-nothing metering never bills a failed slice or multiplies one node", () => {
  const ledger = new R.ShapeReservationLedger(inventory());
  const c = contract();
  assert.equal(ledger.prepare(c, 1).ok, true);
  assert.equal(ledger.commit(c.reservationId, 2).ok, true);
  assert.equal(ledger.start(c.reservationId, 3).ok, true);
  assert.equal(ledger.meter(c.reservationId, 3).activeNodes, 4);
  const failure = ledger.meter(c.reservationId, 2, { [c.points[0]]: false });
  assert.equal(failure.ok, false);
  assert.equal(failure.code, "MINIMUM_SURVIVORS");
  assert.equal(failure.receipt.deliveredNodeSeconds, 12);
  assert.equal(failure.receipt.shortfallNodeSeconds, 28);
  assert.equal(failure.receipt.perNode.filter((n) => n.deliveredSeconds === 3).length, 4);
  assert.equal(failure.receipt.cryptographicallySigned, false);
  assert.equal(ledger.locks.size, 0);
});

test("minimum-survivors policy continues and reconciles node-seconds per participant", () => {
  const c = contract({
    reservationId: "RSV-DEGRADED",
    nonce: "nonce-degraded",
    failurePolicy: { mode: "minimum-survivors", minSurvivors: 3 },
  });
  const ledger = new R.ShapeReservationLedger(inventory());
  ledger.prepare(c, 1);
  ledger.commit(c.reservationId, 2);
  ledger.start(c.reservationId, 3);
  const failedPoint = c.points[0];
  const first = ledger.meter(c.reservationId, 4, { [failedPoint]: false });
  assert.equal(first.ok, true);
  assert.equal(first.activeNodes, 3);
  const done = ledger.meter(c.reservationId, 6, { [failedPoint]: false });
  assert.equal(done.state, R.STATE.SETTLED);
  assert.equal(done.receipt.deliveredNodeSeconds, 30);
  assert.equal(done.receipt.shortfallNodeSeconds, 10);
  assert.equal(done.receipt.perNode.find((n) => n.point === failedPoint).deliveredSeconds, 0);
  assert.equal(done.receipt.perNode.filter((n) => n.deliveredSeconds === 10).length, 3);
  assert.match(done.receipt.digest, /^sha256:[0-9a-f]{64}$/);
});

test("contract and terminal abort operations are tamper-evident and idempotent", () => {
  const c = contract();
  assert.equal(R.verifyContract(c), true);
  const tampered = { ...c, requestedSeconds: 1000 };
  assert.equal(R.verifyContract(tampered), false);

  const ledger = new R.ShapeReservationLedger(inventory());
  ledger.prepare(c, 1);
  const first = ledger.abort(c.reservationId, "buyer-cancelled");
  const second = ledger.abort(c.reservationId, "ignored-second-reason");
  assert.equal(first.ok, true);
  assert.equal(second.idempotent, true);
  assert.equal(second.receipt.digest, first.receipt.digest);
  assert.equal(ledger.locks.size, 0);
});
