"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const {
  buildW33,
  circulant40,
  rewiredRegular,
  run,
} = require("../experiments/w33_quantum_routing_benchmark.js");

function degreeHistogram(adj) {
  const out = {};
  for (const row of adj) out[row.size] = (out[row.size] || 0) + 1;
  return out;
}

test("quantum routing benchmark freezes the exact W33 structural advantage", () => {
  const packet = run();
  assert.equal(packet.status, "PASS");
  assert.equal(packet.evidence, "DETERMINISTIC_NETWORK_MODEL");
  assert.deepEqual(packet.structural.w33.degreeHistogram, { 12: 40 });
  assert.equal(packet.structural.w33.vertices, 40);
  assert.equal(packet.structural.w33.edges, 240);
  assert.equal(packet.structural.w33.distances.diameter, 2);
  assert.equal(packet.structural.w33.distances.disconnectedPairs, 0);
  assert.deepEqual(packet.structural.w33.nonadjacentCommonNeighborHistogram, { 4: 540 });
  assert.equal(packet.checks.w33_nonadjacent_pairs_all_have_four_relays, true);
});

test("both controls are genuinely size/degree matched", () => {
  const w33 = buildW33();
  const circulant = circulant40();
  const rewired = rewiredRegular(w33);
  assert.deepEqual(degreeHistogram(w33), { 12: 40 });
  assert.deepEqual(degreeHistogram(circulant), { 12: 40 });
  assert.deepEqual(degreeHistogram(rewired.adj), { 12: 40 });
  assert.ok(rewired.acceptedSwitches > 100);
});

test("declared stressed repeater model preserves the measured benchmark ordering", () => {
  const packet = run();
  const w = packet.modelResults.w33.stressed.meanProbabilityAtLeastOneQualifiedEntanglement;
  const r = packet.modelResults.degree_preserving_rewire.stressed.meanProbabilityAtLeastOneQualifiedEntanglement;
  const c = packet.modelResults.circulant_degree12.stressed.meanProbabilityAtLeastOneQualifiedEntanglement;
  assert.ok(w > r, `expected W33 ${w} > rewired ${r}`);
  assert.ok(r > c, `expected rewired ${r} > circulant ${c}`);
  assert.ok(Math.abs(w - 0.346469) < 1e-5);
  assert.ok(Math.abs(r - 0.317495) < 1e-5);
  assert.ok(Math.abs(c - 0.224782) < 1e-5);
});

test("Witting-frame opportunity is explicitly a 13/40 model multiplier, not a key rate", () => {
  const packet = run();
  for (const topology of Object.values(packet.modelResults)) {
    for (const row of Object.values(topology)) {
      assert.ok(Math.abs(
        row.meanAcceptedWittingFrameOpportunity -
        row.meanProbabilityAtLeastOneQualifiedEntanglement * (13 / 40)
      ) < 2e-9);
    }
  }
  assert.match(packet.metricBoundary.acceptedWittingFrameOpportunity, /NOT a secret-key rate/);
  assert.ok(packet.limitations.some((x) => /No quantum hardware/.test(x)));
});
