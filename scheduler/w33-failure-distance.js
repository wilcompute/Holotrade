"use strict";

// Production exact distance from an observed W33 point-failure set to the
// all-lines-hit safety boundary.
//
// Runtime scheduling must not enumerate the global minimal-transversal atlas at
// module import.  We therefore use the already-validated independent exact
// branch-and-bound set-cover oracle.  The offline blocker-atlas analysis remains
// a separate proof/classification front and must not sit on the hot path.

const Search = require("./w33-failure-distance-search.js");
const SCHEMA = "holotrade.w33-failure-distance.v3";

function exactFailureDistance(rawFailed) {
  const row = Search.exactFailureDistanceSearch(rawFailed);
  return Object.freeze({
    schema: SCHEMA,
    distance: row.distance,
    witnessAdditionalFailures: row.witnessAdditionalFailures,
    exact: true,
    intactLineCount: row.intactLineCount,
    searchLowerBound: row.searchLowerBound ?? 0,
    greedyUpperBound: row.greedyUpperBound ?? row.distance,
    method: "exact-branch-and-bound-set-cover",
  });
}

module.exports = { SCHEMA, exactFailureDistance };
