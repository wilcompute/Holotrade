"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");
const generator = require("../analysis/e8_unitary_hole_coset_rtl.js");
const frozen = require("../data/e8_unitary_hole_coset_rtl.json");

const ROOT = path.resolve(__dirname, "..");

function add3(a, b) { return (a + b) % 3; }
function mul3(a, b) { return (a * b) % 3; }

// Independent JS interpretation of GF(9)=GF(3)[alpha]/(alpha^2-alpha-1).
function hermitianTerm(x, y) {
  const [a, b] = x;
  const [c, d] = y;
  const conjugate = [add3(c, d), mul3(2, d)];
  const [e, f] = conjugate;
  return [
    add3(mul3(a, e), mul3(b, f)),
    add3(add3(mul3(a, f), mul3(b, e)), mul3(b, f)),
  ];
}

function compactAdjacent(u, v) {
  if (u < 0 || v < 0 || u >= 120 || v >= 120 || u === v) return false;
  const left = frozen.coordinates[u];
  const right = frozen.coordinates[v];
  let form = [0, 0];
  for (let k = 0; k < 4; k += 1) {
    const term = hermitianTerm(left.slice(2 * k, 2 * k + 2), right.slice(2 * k, 2 * k + 2));
    form = [add3(form[0], term[0]), add3(form[1], term[1])];
  }
  return form[0] === 0 && form[1] === 0;
}

test("GAP exactly regenerates the frozen coset transport and both RTL implementations", { timeout: 180_000 }, () => {
  const { sha256, ...body } = frozen;
  assert.equal(generator.digest(body), sha256);
  const generated = generator.generate();
  assert.deepEqual(generated.certificate, frozen);
  assert.equal(generated.verilog, fs.readFileSync(path.join(ROOT, "rtl/e8_unitary_hole_adj.v"), "utf8"));
});

test("the compact Hermitian predicate exhausts all 2^14 address pairs", () => {
  let directedEdges = 0;
  for (let u = 0; u < 128; u += 1) {
    for (let v = 0; v < 128; v += 1) {
      const fromRom = u < 120 && v < 120 && frozen.neighbours[u].includes(v);
      const fromField = compactAdjacent(u, v);
      assert.equal(fromField, fromRom, `adjacency mismatch at ${u},${v}`);
      if (fromField) directedEdges += 1;
    }
  }
  assert.equal(directedEdges, 2400);
  assert.equal(directedEdges / 2, frozen.carrier.edges);
  assert.equal(frozen.implementation.compactCarrierBits, 1920);
  assert.equal(frozen.implementation.fullRowRomBits, 14400);
  assert.equal(frozen.implementation.tableCompressionRatio, 7.5);
});

test("Yosys SAT proves compact-coordinate RTL equals the complete row ROM", { timeout: 120_000 }, () => {
  const run = spawnSync(process.execPath,
    ["scripts/run-yosys.js", "rtl/verify_e8_unitary_hole_adj.ys"], {
      cwd: ROOT,
      encoding: "utf8",
      maxBuffer: 64 * 1024 * 1024,
    });
  assert.equal(run.status, 0, run.stderr || run.stdout);
  assert.match(`${run.stdout}\n${run.stderr}`, /SAT proof finished - no model found: SUCCESS!/);
});

test("measured iCE40 synthesis retains the compact circuit's advantage", () => {
  const compact = fs.readFileSync(path.join(ROOT, "rtl/build/e8_hole_compact_ice40.txt"), "utf8");
  const rom = fs.readFileSync(path.join(ROOT, "rtl/build/e8_hole_rom_ice40.txt"), "utf8");
  const compactLuts = Number(compact.match(/(\d+)\s+SB_LUT4/)?.[1]);
  const romLuts = Number(rom.match(/(\d+)\s+SB_LUT4/)?.[1]);
  assert.equal(compactLuts, 544);
  assert.equal(romLuts, 1174);
  assert.ok(compactLuts < romLuts);
});
