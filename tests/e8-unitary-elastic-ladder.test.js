"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const F = require("../analysis/e8_unitary_elastic_ladders.js");
const L = require("../scheduler/e8-unitary-elastic-ladder.js");

test("the frozen GAP certificate is canonical and reproducible", { timeout: 120_000 }, () => {
  const frozen = require("../data/e8_unitary_elastic_ladders.json");
  assert.equal(L.verifyFrozen(), true);
  const rerun = F.run();
  assert.deepEqual(rerun, frozen);
  assert.match(rerun.gapVersion, /^\d+\.\d+\.\d+$/);
});

test("q=2 and q=3 ladders stop at the exhaustive partial-spread ceilings", () => {
  const cases = [
    { q: 2, rungs: 6, size: 30, holes: 15, maxima: 72, full: 9 },
    { q: 3, rungs: 16, size: 160, holes: 120, maxima: 2268, full: 28 },
  ];
  for (const expected of cases) {
    const ladder = L.buildLadder({ q: expected.q });
    assert.equal(ladder.valid, true);
    assert.equal(ladder.maximumRung, expected.rungs);
    assert.equal(ladder.maximumCoveredPoints, expected.size);
    assert.equal(ladder.maximumHolePoints, expected.holes);
    assert.equal(ladder.maximumHolePointIds.length, expected.holes);
    assert.equal(ladder.theorem.maximumPartialSpreadCount, expected.maxima);
    assert.equal(ladder.fullSpreadWouldNeedLines, expected.full);
    assert.equal(ladder.theorem.hasFullSpread, false);
    assert.equal(ladder.rungs.every((row) => row.valid), true);
  }
});

test("every rung obeys the GQ formula and a line-order permutation changes no invariant", () => {
  for (const q of [2, 3]) {
    const canonical = L.buildLadder({ q });
    const reverse = L.buildLadder({ q, lineOrder: [...canonical.lineOrder].reverse() });
    for (let i = 1; i <= canonical.maximumRung; i++) {
      const expected = L.expectedRung(q, i);
      for (const ladder of [canonical, reverse]) {
        const row = ladder.rungs[i - 1];
        assert.equal(row.pointIds.length, expected.vertices);
        assert.equal(row.expected.internalEdges, expected.internalEdges);
        assert.equal(row.expected.boundaryEdges, expected.boundaryEdges);
        assert.equal(row.expected.spectralMinimumBoundary, expected.boundaryEdges);
        assert.equal(row.migratedPointIds.length, 0);
      }
    }
  }
});

test("resize from off, expansion, shrink, and hold migrate no retained work", () => {
  const ladder = L.buildLadder({ q: 3 });
  const start = L.resizePlan(ladder, 0, 4);
  assert.equal(start.valid, true);
  assert.equal(start.addedPointIds.length, 40);
  assert.equal(start.retainedPointIds.length, 0);
  assert.deepEqual(start.changedLineAtomIds, [1, 2, 3, 4]);

  const expand = L.resizePlan(ladder, 4, 13);
  assert.equal(expand.retainedPointIds.length, 40);
  assert.equal(expand.addedPointIds.length, 90);
  assert.equal(expand.migratedPointIds.length, 0);

  const shrink = L.resizePlan(ladder, 13, 2);
  assert.equal(shrink.retainedPointIds.length, 20);
  assert.equal(shrink.removedPointIds.length, 110);
  assert.equal(shrink.migratedPointIds.length, 0);

  const hold = L.resizePlan(ladder, 2, 2);
  assert.equal(hold.direction, "hold");
  assert.equal(hold.changedLineAtomIds.length, 0);
});

test("topology plans are tamper-evident and fail closed before inventory attestation", () => {
  const ladder = L.buildLadder({ q: 2 });
  const plan = L.createTopologyPlan(ladder, 5, {
    reservationId: "RSV-E8-H34-25",
    owner: "unitary-test",
    artifactDigest: `sha256:${"42".repeat(32)}`,
    requestedSeconds: 30,
    resources: { perNode: { vcpus: 2, memoryMiB: 1024 } },
  });
  assert.equal(plan.pointIds.length, 25);
  assert.equal(plan.topologyRequirements.exactInducedDegree, 8);
  assert.equal(plan.topologyRequirements.exactBoundaryEdges, 100);
  assert.equal(plan.dispatchable, false);
  assert.equal(plan.requiredNextEvidence, "RUNTIME_TOPOLOGY_ATTESTATION");
  assert.equal(L.verifyTopologyPlan(plan), true);
  assert.equal(L.verifyTopologyPlan({ ...plan, rung: 4 }), false);
});
