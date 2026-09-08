"use strict";

// Exact distance from an observed W33 point-failure set to the all-lines-hit
// safety boundary, evaluated from the complete inclusion-minimal blocker atlas.
// This replaces repeated branch-and-bound set-cover solving in production while
// preserving the same exact integer semantics.  The independent search oracle
// remains in w33-failure-distance-search.js for regression cross-checks.

const R = require("./w33-topology-resilience.js");
const A = require("./w33-minimal-blocker-atlas.js");
const SCHEMA = "holotrade.w33-failure-distance.v2";

function exactFailureDistance(rawFailed) {
  const base = R.assessFailures(rawFailed);
  const row = A.distanceViaAtlas(base.failurePoints);
  return Object.freeze({
    schema: SCHEMA,
    distance: row.distance,
    witnessAdditionalFailures: row.witnessAdditionalFailures,
    exact: true,
    intactLineCount: base.intactLineCount,
    nearestMinimalBlockerIndex: row.nearestMinimalBlockerIndex,
    nearestMinimalBlockerSize: row.nearestMinimalBlockerSize,
    nearestMinimalBlockerType: row.nearestMinimalBlockerType,
    nearestNeighborhoodCenter: row.nearestNeighborhoodCenter,
    atlasBlockerCount: A.MINIMAL_BLOCKERS.length,
    method: "complete-minimal-blocker-atlas",
  });
}

module.exports = { SCHEMA, exactFailureDistance };
