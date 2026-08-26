"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const S = require("../js/substrate.js");
const W = require("../js/w33-scheduler.js");
const L = require("../scheduler/w33-elastic-ladder.js");
const R = require("../reservations/shape-reservation.js");

const ARTIFACT = `sha256:${"37".repeat(32)}`;

test("all 36 ordered spreads give ten nested, regular, boundary-optimal rungs", () => {
  assert.equal(W.spreads().length, 36);
  for (let spreadIndex = 0; spreadIndex < 36; spreadIndex++) {
    const ladder = L.buildLadder({ spreadIndex });
    assert.equal(ladder.valid, true);
    assert.deepEqual(ladder.theorem.sizes, [4, 8, 12, 16, 20, 24, 28, 32, 36, 40]);
    assert.equal(ladder.rungs.length, 10);
    for (const row of ladder.rungs) {
      const i = row.rung;
      assert.equal(row.valid, true, `spread ${spreadIndex}, rung ${i}`);
      assert.equal(row.shape.vertices, 4 * i);
      assert.equal(row.shape.internalEdges, 2 * i * (i + 2));
      assert.equal(row.shape.boundaryEdges, 4 * i * (10 - i));
      assert.deepEqual(row.profile.inside, [i + 2]);
      assert.deepEqual(row.profile.outside, i === 10 ? [] : [i]);
      assert.equal(row.shape.boundaryEdges, row.shape.spectralBoundary.lower.numerator / 4);
      assert.equal(row.migratedPoints.length, 0);
    }
  }
});

test("every subset of every spread is a tight set with the same closed-form metrics", () => {
  for (const spread of W.spreads()) {
    for (let mask = 1; mask < (1 << 10); mask++) {
      const chosen = spread.filter((_, bit) => mask & (1 << bit));
      const i = chosen.length;
      const points = [...new Set(chosen.flatMap((lineId) => S.LINES[lineId]))].sort((a, b) => a - b);
      const shape = R.shapeCertificate(points);
      assert.equal(shape.vertices, 4 * i);
      assert.equal(shape.internalEdges, 2 * i * (i + 2));
      assert.equal(shape.boundaryEdges, 4 * i * (10 - i));
      assert.equal(shape.connected, true);
      assert.equal(shape.boundaryEdges * 4, shape.spectralBoundary.lower.numerator);
    }
  }
});

test("arbitrary line order preserves the theorem and resize moves no retained point", () => {
  const spread = [...W.spreads()[7]].reverse();
  const ladder = L.buildLadder({ spreadIndex: 7, lineOrder: spread });
  assert.deepEqual(ladder.lineOrder, spread);

  const expand = L.resizePlan(ladder, 2, 8);
  assert.equal(expand.valid, true);
  assert.equal(expand.direction, "expand");
  assert.equal(expand.retainedPoints.length, 8);
  assert.equal(expand.addedPoints.length, 24);
  assert.equal(expand.removedPoints.length, 0);
  assert.equal(expand.migratedPoints.length, 0);
  assert.equal(expand.changedLineIds.length, 6);

  const shrink = L.resizePlan(ladder, 8, 3);
  assert.equal(shrink.valid, true);
  assert.equal(shrink.direction, "shrink");
  assert.equal(shrink.retainedPoints.length, 12);
  assert.equal(shrink.removedPoints.length, 20);
  assert.equal(shrink.addedPoints.length, 0);
  assert.equal(shrink.migratedPoints.length, 0);
  assert.equal(shrink.changedLineIds.length, 5);
});

test("availability planner selects a fully free optimal prefix or fails with the exact ceiling", () => {
  const none = L.bestAvailableLadder({ unavailable: [], targetRung: 10 });
  assert.equal(none.ok, true);
  assert.equal(none.rung.shape.vertices, 40);

  const spread = W.spreads()[0];
  const blocked = spread.slice(0, 4).map((lineId) => S.LINES[lineId][0]);
  const plan = L.bestAvailableLadder({ unavailable: blocked, targetRung: 5 });
  if (plan.ok) {
    assert.equal(plan.rung.points.every((point) => !blocked.includes(point)), true);
    assert.equal(plan.rung.checks.spectralEquality, true);
  } else {
    assert.ok(plan.maxRung < 5);
    assert.equal(plan.maxVertices, 4 * plan.maxRung);
  }

  const impossible = L.bestAvailableLadder({ unavailable: S.POINTS.map((p) => p.index), targetRung: 1 });
  assert.equal(impossible.ok, false);
  assert.equal(impossible.maxRung, 0);
  assert.equal(impossible.maxVertices, 0);
});

test("a ladder rung becomes an ordinary tamper-evident atomic shape contract", () => {
  const ladder = L.buildLadder({ spreadIndex: 3 });
  const contract = L.createRungContract(ladder, 5, {
    reservationId: "RSV-ELASTIC-20",
    owner: "elastic-test",
    nonce: "elastic-test-1",
    artifactDigest: ARTIFACT,
    requestedSeconds: 12,
    resources: { perNode: { vcpus: 2, memoryMiB: 512 } },
    failurePolicy: { mode: "all-or-nothing" },
  });
  assert.equal(contract.points.length, 20);
  assert.equal(contract.shape.internalEdges, 70);
  assert.equal(contract.shape.boundaryEdges, 100);
  assert.equal(contract.topologyRequirements.minDegree, 7);
  assert.ok(contract.evidenceRefs.includes(ladder.digest));
  assert.equal(R.verifyContract(contract), true);
});

