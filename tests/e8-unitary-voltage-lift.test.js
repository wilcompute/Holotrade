"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");
const Freezer = require("../analysis/e8_unitary_voltage_lift.js");
const Lift = require("../scheduler/e8_unitary_voltage_lift.js");
const frozen = require("../data/e8_unitary_voltage_lift.json");
const oldGraph = require("../data/e8_unitary_hole_coset_rtl.json");

const ROOT = path.resolve(__dirname, "..");
const normalizedText = (value) => value.replace(/\r\n/g, "\n");

function yosys(script, timeout = 120_000) {
  return spawnSync(process.execPath, ["scripts/run-yosys.js", script], {
    cwd: ROOT,
    encoding: "utf8",
    maxBuffer: 128 * 1024 * 1024,
    timeout,
  });
}

test("GAP exactly regenerates the frozen affine lift and generated RTL", { timeout: 180_000 }, () => {
  const { sha256, ...body } = frozen;
  assert.equal(Freezer.digest(body), sha256);
  const generated = Freezer.generate();
  assert.deepEqual(generated.certificate, frozen);
  assert.equal(normalizedText(generated.verilog),
    normalizedText(fs.readFileSync(path.join(ROOT, "rtl/e8_unitary_voltage_lift.v"), "utf8")));
  assert.equal(Lift.verifyFrozen(), true);
});

test("the 15 by 8 chart transports every edge of the certified coset graph", () => {
  const transported = new Set();
  for (let logical = 0; logical < 120; logical += 1) {
    const address = Lift.addressFromLogicalId(logical);
    assert.equal(Lift.addressFromCosetVertex(address.transportedCosetVertex).logicalId, logical);
    const actual = Lift.neighbours(address);
    assert.equal(actual.length, 20);
    const actualVertices = actual.map((target) => target.transportedCosetVertex).sort((a, b) => a - b);
    assert.deepEqual(actualVertices,
      [...oldGraph.neighbours[address.transportedCosetVertex]].sort((a, b) => a - b));
    for (const target of actual) {
      assert.equal(Lift.adjacent(address, target), true);
      transported.add([logical, target.logicalId].sort((a, b) => a - b).join(":"));
    }
  }
  assert.equal(transported.size, 1200);
});

test("all sixty cross connectors are four C4s and two parallel affine channels", () => {
  assert.equal(frozen.crossRelations.length, 60);
  assert.equal(frozen.relationTypes.length, 13);
  for (const relation of frozen.crossRelations) {
    assert.equal(relation.affinePermutationGraphsInRelation, 8);
    assert.equal(relation.twoMapDecompositions, 4);
    assert.deepEqual(relation.selectedAffineMaps[0].matrix, relation.selectedAffineMaps[1].matrix);
    const blocks = [relation.leftBlock, relation.rightBlock];
    const vertices = blocks.flatMap((block) => Array.from({ length: 8 }, (_, slot) => 8 * block + slot));
    const restricted = new Map(vertices.map((vertex) => [vertex,
      frozen.logicalNeighbours[vertex].filter((target) => Math.floor(target / 8) !== Math.floor(vertex / 8) &&
        blocks.includes(Math.floor(target / 8)))]));
    assert.equal([...restricted.values()].every((row) => row.length === 2), true);
    const unseen = new Set(vertices);
    const componentSizes = [];
    while (unseen.size) {
      const queue = [unseen.values().next().value];
      let componentSize = 0;
      while (queue.length) {
        const vertex = queue.pop();
        if (!unseen.delete(vertex)) continue;
        componentSize += 1;
        queue.push(...restricted.get(vertex));
      }
      componentSizes.push(componentSize);
    }
    assert.deepEqual(componentSizes.sort((a, b) => a - b), [4, 4, 4, 4]);
  }
});

test("logical fanout plans are immutable, tamper-evident, and never dispatchable", () => {
  const plan = Lift.compileFanout(Lift.address(7, 5));
  assert.equal(plan.fanout, 20);
  assert.equal(plan.dispatchable, false);
  assert.deepEqual(plan.liveBindings, []);
  assert.equal(Object.isFrozen(plan), true);
  assert.equal(Lift.verifyFanout(plan), true);
  assert.equal(Lift.verifyFanout({ ...plan, fanout: 19 }), false);
  assert.throws(() => Lift.address(15, 0), /blockId/);
});

test("Yosys SAT proves the affine predicate equals the full 120-row ROM", { timeout: 120_000 }, () => {
  const run = yosys("rtl/verify_e8_unitary_voltage_lift.ys");
  assert.equal(run.status, 0, run.stderr || run.stdout);
  assert.match(`${run.stdout}\n${run.stderr}`, /SAT proof finished - no model found: SUCCESS!/);
});

test("the affine address circuit uses 171 LUT4s versus 720 in the same exact flow", { timeout: 120_000 }, () => {
  const run = yosys("rtl/synth_e8_unitary_voltage_lift.ys");
  assert.equal(run.status, 0, run.stderr || run.stdout);
  const output = `${run.stdout}\n${run.stderr}`;
  const affine = output.split("AFFINE_VOLTAGE_LIFT_SYNTHESIS")[1]
    ?.split("GENERAL_GF9_PREDICATE_SAME_FLOW_SYNTHESIS")[0];
  const general = output.split("GENERAL_GF9_PREDICATE_SAME_FLOW_SYNTHESIS")[1];
  const affineLuts = Number(affine?.match(/(\d+)\s+SB_LUT4/)?.[1]);
  const generalLuts = Number(general?.match(/(\d+)\s+SB_LUT4/)?.[1]);
  assert.equal(affineLuts, 171);
  assert.equal(generalLuts, 720);
  assert.equal(frozen.implementation.synthesis.affinePredicateIce40Lut4, affineLuts);
  assert.equal(frozen.implementation.synthesis.priorGeneralPredicateSameFlowIce40Lut4, generalLuts);
  assert.ok(affineLuts < 544);
});
