"use strict";

// Reversible checkpoint placement on the W33 elastic spread ladder.
//
// The W33-Theory certificate data/w33_spread_ladder_reversible_gc.json
// (schema w33.spread-ladder-reversible-gc.v1) proves that the ladder rungs
// are the boundary-optimal reversible checkpoint tiers: every rung attains
// the spectral minimum boundary m(40-m)/4, so releasing a tier costs exactly
// 4i(10-i) boundary crossings, the peak live boundary is 100 (the certified
// 20|20 cut), and a full compute/uncompute cycle crosses 2*660 = 1320 edges.
//
// This module is the control-plane binding: it turns a ladder into a
// checkpoint policy object with pin/release accounting.  It is an ABSTRACT
// plan over the certified geometry.  It is dispatchable=false until runtime
// topology attestation, matching the existing fail-closed ladder contract.

const L = require("./w33-elastic-ladder.js");

const SCHEMA = "holotrade.w33-reversible-checkpoint-ladder.v1";
const W33_CERTIFICATE_SCHEMA = "w33.spread-ladder-reversible-gc.v1";

function checkpointPolicy({ spreadIndex = 0, lineOrder = null } = {}) {
    const ladder = L.buildLadder({ spreadIndex, lineOrder });
    if (!ladder.valid) {
        throw new Error("base ladder is invalid; refusing to derive a checkpoint policy");
    }

    let cumulative = 0;
    const tiers = ladder.rungs.map((row) => {
        const i = row.rung;
        const releaseBoundary = row.shape.boundaryEdges;
        cumulative += releaseBoundary;
        return Object.freeze({
            tier: i,
            rungVertices: row.shape.vertices,
            releaseBoundary,
            spectralMinimumBoundary: (row.shape.vertices * (40 - row.shape.vertices)) / 4,
            attainsSpectralMinimum: releaseBoundary === (row.shape.vertices * (40 - row.shape.vertices)) / 4,
            cumulativeBoundary: cumulative,
            migrationPointsOnResize: row.migratedPoints.length,
        });
    });

    const totalSinglePass = cumulative;
    const peak = Math.max(...tiers.map((t) => t.releaseBoundary));
    const peakTier = tiers.find((t) => t.releaseBoundary === peak).tier;

    return Object.freeze({
        schema: SCHEMA,
        sourceCertificateSchema: W33_CERTIFICATE_SCHEMA,
        spreadIndex,
        lineOrder: ladder.lineOrder,
        tiers: Object.freeze(tiers),
        economics: Object.freeze({
            totalBoundarySinglePass: totalSinglePass,
            totalBoundaryFullCycle: 2 * totalSinglePass,
            peakLiveBoundary: peak,
            peakTier,
            peakIsSpectralMinimumAtHalfRetention: peak === 100 && peakTier === 5,
            inheritedTimeBound: "T = 2B3^L (Bennett bridge; W33 reversible-storage economics)",
        }),
        policy: Object.freeze({
            pin: "retain rung i state while guest segment i is live",
            release: "releasing tier i costs exactly releaseBoundary hop-crossings",
            resize: "expand/shrink along the ladder moves zero retained points",
        }),
        dispatchable: false,
        dispatchBoundary:
            "Abstract checkpoint plan over certified geometry. Requires runtime " +
            "topology attestation before dispatch; software boundary counts only, " +
            "no energy or device claim.",
    });
}

module.exports = Object.freeze({
    SCHEMA,
    W33_CERTIFICATE_SCHEMA,
    checkpointPolicy,
});
