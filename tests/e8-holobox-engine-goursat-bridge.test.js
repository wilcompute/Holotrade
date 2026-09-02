"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const bridge = require("../analysis/e8_holobox_engine_goursat_bridge.js");

const ROOT = path.resolve(__dirname, "..");
const frozen = require("../data/e8_holobox_engine_goursat_bridge.json");

test("GAP regenerates the HoloBox/engine Goursat bridge byte-for-object", {
  timeout: 60_000,
}, () => {
  assert.deepEqual(bridge.run(), frozen);
  assert.equal(frozen.evidenceClass,
    "EXACT_GAP_NORMAL_QUOTIENT_AND_SUBDIRECT_CLASSIFICATION");
});

test("connected and full routing scopes remain distinct", () => {
  assert.deepEqual(frozen.router.fullNormalSubgroupOrders, [1, 25920, 51840]);
  assert.equal(frozen.router.connectedGroup, "PSp(4,3)");
  assert.equal(frozen.router.connectedSimple, true);
  assert.equal(frozen.router.fullGroup, "PGSp(4,3)");
  assert.equal(frozen.router.fullAbelianization, "C2");
  assert.deepEqual(frozen.router.connectedAndFullPointStabilizers, [648, 1296]);
  assert.equal(frozen.router.outerParityVisibleInFullPointStabilizer, true);
});

test("Goursat leaves one connected coupling and exactly three full parity pullbacks", () => {
  assert.equal(frozen.goursat.connectedRouter.subdirectClasses, 1);
  assert.equal(frozen.goursat.connectedRouter.classification,
    "forced direct product");
  assert.equal(frozen.goursat.fullRouter.subdirectClasses, 4);
  assert.equal(frozen.goursat.fullRouter.classification,
    "one direct product plus three C2 fibre products");
  assert.deepEqual(frozen.goursat.fullRouter.executionOnlyEnumerationOrders,
    [597196800, 597196800, 597196800, 1194393600]);
  assert.deepEqual(frozen.goursat.fullRouter.parityCharacters.map((row) => [
    row.label,
    row.translationCoreIntersection,
    row.permutationComplementIntersection,
  ]), [
    ["permutation_sign", 32, 360],
    ["translation_parity", 16, 720],
    ["translation_xor_sign", 16, 360],
  ]);
  assert.ok(frozen.goursat.fullRouter.parityCharacters.every((row) =>
    row.quotient === "C2" && row.canonical === false && row.dispatchable === false));
});

test("the bridge freezes a logical local carrier, never a deployment claim", () => {
  assert.deepEqual(frozen.engine.logicalChartShape, [21, 8, 15, 8]);
  assert.deepEqual(frozen.localCarrier.addressShape, [40, 20160]);
  assert.equal(frozen.localCarrier.logicalStates, 806400);
  assert.equal(frozen.goursat.connectedRouter.groupOrder, 100329062400);
  assert.equal(frozen.goursat.fullRouter.parityFibreProductOrder, 100329062400);
  assert.equal(frozen.goursat.fullRouter.directProductOrder, 200658124800);
  assert.equal(frozen.dispatchable, false);
  assert.equal(frozen.recursiveParityPolicyBuilt, false);
  assert.equal(frozen.liveBindingBuilt, false);
  assert.match(frozen.evidenceBoundary, /No parity is inferred/);
});

test("the GAP witness names the recursive and dispatch boundaries explicitly", () => {
  const source = fs.readFileSync(path.join(ROOT, "analysis",
    "e8_holobox_engine_goursat_bridge.g"), "utf8");
  assert.match(source, /couplingsCanonical=0/);
  assert.match(source, /recursiveParityPolicyBuilt=0/);
  assert.match(source, /dispatchable=0/);
  assert.match(source, /SubdirectProducts/);
});
