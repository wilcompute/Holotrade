"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const W = require("../js/w33-scheduler.js");
const P = require("../scheduler/w33-reversible-checkpoint-ladder.js");

test("checkpoint policy derives boundary-optimal tiers from every spread", () => {
    assert.equal(W.spreads().length, 36);
    for (let spreadIndex = 0; spreadIndex < 36; spreadIndex++) {
        const policy = P.checkpointPolicy({ spreadIndex });
        assert.equal(policy.tiers.length, 10);
        for (const tier of policy.tiers) {
            const i = tier.tier;
            assert.equal(tier.rungVertices, 4 * i);
            assert.equal(tier.releaseBoundary, 4 * i * (10 - i));
            assert.equal(tier.attainsSpectralMinimum, true, `spread ${spreadIndex} tier ${i}`);
            assert.equal(tier.migrationPointsOnResize, 0);
        }
        assert.deepEqual(
            policy.tiers.map((t) => t.releaseBoundary),
            [36, 64, 84, 96, 100, 96, 84, 64, 36, 0],
        );
        assert.equal(policy.economics.totalBoundarySinglePass, 660);
        assert.equal(policy.economics.totalBoundaryFullCycle, 1320);
        assert.equal(policy.economics.peakLiveBoundary, 100);
        assert.equal(policy.economics.peakTier, 5);
        assert.equal(policy.economics.peakIsSpectralMinimumAtHalfRetention, true);
        assert.equal(policy.dispatchable, false);
    }
});

test("custom line order preserves the checkpoint economics", () => {
    const order = [...W.spreads()[3]].reverse();
    const policy = P.checkpointPolicy({ spreadIndex: 3, lineOrder: order });
    assert.deepEqual(policy.lineOrder, order);
    assert.equal(policy.economics.totalBoundaryFullCycle, 1320);
    assert.equal(policy.economics.peakLiveBoundary, 100);
});

test("policy refuses to dispatch without runtime attestation", () => {
    const policy = P.checkpointPolicy();
    assert.equal(policy.dispatchable, false);
    assert.match(policy.dispatchBoundary, /attestation/);
});
