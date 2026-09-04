"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const cert = require("../data/the_45_slot_rom_bijection.json");
const {
  SlowPathROMDecoder,
  bootCheck,
  matrixKey,
  projectiveCanonical,
} = require("../js/w33-slowpath-rom-decoder.js");

function clone(x) {
  return JSON.parse(JSON.stringify(x));
}

function neg(M) {
  return M.map((row) => row.map((x) => (3 - x) % 3));
}

test("45-target certificate passes the production boot incidence checks", () => {
  const boot = bootCheck(cert);
  assert.equal(boot.ok, true, JSON.stringify(boot.errors));
  assert.deepEqual(boot.counts, {
    targets: 45,
    slots: 45,
    banks: 27,
    incidences: 135,
    collinearityEdges: 270,
  });
  assert.match(boot.digest, /^sha256:[0-9a-f]{64}$/);
});

test("every concrete anomaly and its negative decode to the same slow ROM slot", () => {
  const decoder = new SlowPathROMDecoder(cert);
  const slots = new Set();
  for (let i = 0; i < cert.table.length; i += 1) {
    const row = cert.table[i];
    const a = decoder.decode(row.spMatrix);
    const b = decoder.decode(neg(row.spMatrix));
    assert.equal(a.slow, true);
    assert.equal(a.extraTransvections, 1);
    assert.equal(a.anomalyIndex, i);
    assert.equal(a.slot, row.slot);
    assert.deepEqual(a.h34Point, row.h34Point);
    assert.equal(a.banks.length, 3);
    assert.deepEqual(a, b, "g and -g must be one projective slow target");
    slots.add(a.slot);
  }
  assert.equal(slots.size, 45);
});

test("identity is not accidentally classified as one of the 45 expensive targets", () => {
  const decoder = new SlowPathROMDecoder(cert);
  const I = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]];
  const row = decoder.decode(I);
  assert.equal(row.slow, false);
  assert.equal(row.extraTransvections, 0);
});

test("projective canonicalization is deterministic under sign", () => {
  for (const row of cert.table) {
    assert.equal(
      matrixKey(projectiveCanonical(row.spMatrix)),
      matrixKey(projectiveCanonical(neg(row.spMatrix)))
    );
  }
});

test("boot refuses a corrupted GQ bank before decoder construction", () => {
  const bad = clone(cert);
  bad.linesB[0][4] = bad.linesB[0][3];
  const boot = bootCheck(bad);
  assert.equal(boot.ok, false);
  assert.ok(boot.errors.some((e) => /BAD_BANK|INCIDENCE|PAIR|GQ|SRG|LINE_SET/.test(e)));
  assert.throws(() => new SlowPathROMDecoder(bad), /boot refused/);
});

test("boot refuses a duplicated concrete projective target", () => {
  const bad = clone(cert);
  bad.table[1].spMatrix = clone(bad.table[0].spMatrix);
  const boot = bootCheck(bad);
  assert.equal(boot.ok, false);
  assert.ok(boot.errors.includes("PROJECTIVE_TARGETS_NOT_UNIQUE"));
});
