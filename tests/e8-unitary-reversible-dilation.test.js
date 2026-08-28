"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");
const Freezer = require("../analysis/e8_unitary_reversible_dilation.js");
const Runtime = require("../scheduler/e8-unitary-reversible-dilation.js");
const frozen = require("../data/e8_unitary_reversible_dilation.json");

const ROOT = path.resolve(__dirname, "..");

test("GAP regenerates the exact reversible symplectic dilation and RTL", { timeout: 180_000 }, () => {
  const { sha256, ...body } = frozen;
  assert.equal(Freezer.digest(body), sha256);
  const generated = Freezer.generate();
  assert.deepEqual(generated.certificate, frozen);
  assert.equal(generated.verilog,
    fs.readFileSync(path.join(ROOT, "rtl/e8_unitary_reversible_dilation.v"), "utf8"));
  assert.equal(Runtime.verifyFrozen(), true);
});

test("twenty perfect matchings cover every directed adjacency gate exactly once", () => {
  assert.equal(frozen.cnotNetwork.schedule.length, 20);
  const edges = new Set();
  for (const layer of frozen.cnotNetwork.schedule) {
    assert.equal(layer.controlYByTargetX.length, 120);
    assert.equal(new Set(layer.controlYByTargetX).size, 120, "each y control occurs once per layer");
    layer.controlYByTargetX.forEach((controlY, targetX) => {
      const key = `${targetX},${controlY}`;
      assert.equal(edges.has(key), false, `reused CNOT ${key}`);
      edges.add(key);
    });
  }
  assert.equal(edges.size, 2400);
  assert.equal(frozen.cnotNetwork.layers, 20);
  assert.equal(frozen.cnotNetwork.optimal, true);
});

test("the scheduled 240-bit transform is an involution preserving the symplectic basis form", () => {
  const zero = () => Array(120).fill(0);
  const basis = [];
  for (let i = 0; i < 240; i += 1) {
    const x = zero(); const y = zero();
    if (i < 120) x[i] = 1; else y[i - 120] = 1;
    basis.push({ x, y });
    const once = Runtime.applyDilation(x, y);
    assert.deepEqual(Runtime.applyDilation(once.x, once.y), { x, y });
  }
  const form = (left, right) => {
    let value = 0;
    for (let i = 0; i < 120; i += 1) {
      value ^= (left.x[i] & right.y[i]) ^ (left.y[i] & right.x[i]);
    }
    return value;
  };
  const images = basis.map((v) => Runtime.applyDilation(v.x, v.y));
  for (let i = 0; i < 240; i += 1) {
    for (let j = 0; j < 240; j += 1) {
      assert.equal(form(images[i], images[j]), form(basis[i], basis[j]), `${i},${j}`);
    }
  }
});

test("the immutable plan is simulation-only and tampering is detected", () => {
  const plan = Runtime.planReversibleDilation();
  assert.equal(plan.depth, 20);
  assert.equal(plan.involution, true);
  assert.equal(plan.symplectic, true);
  assert.equal(plan.dispatchable, false);
  assert.equal(Object.isFrozen(plan), true);
  assert.equal(Runtime.verifyPlan(plan), true);
  assert.equal(Runtime.verifyPlan({ ...plan, depth: 19 }), false);
});

test("Yosys SAT proves that applying the RTL twice is the identity", { timeout: 120_000 }, () => {
  const run = spawnSync(process.execPath,
    ["scripts/run-yosys.js", "rtl/verify_e8_unitary_reversible_dilation.ys"], {
      cwd: ROOT,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
    });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  assert.match(`${run.stdout}\n${run.stderr}`, /SAT proof finished - no model found: SUCCESS!/);
});
