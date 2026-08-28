"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const Freezer = require("../analysis/e8_fractal_microvm_fabric.js");
const Fabric = require("../scheduler/e8-fractal-microvm-fabric.js");
const Codec = require("../analysis/e8_fano_zappa_szep_codec.js");
const frozen = require("../data/e8_fractal_microvm_fabric.json");

test("GAP exactly regenerates the Goursat independence certificate", { timeout: 60_000 }, () => {
  assert.equal(Fabric.verifyFrozen(), true);
  assert.deepEqual(Freezer.run(), frozen);
  assert.equal(frozen.independence.commonNontrivialQuotient, false);
  assert.equal(frozen.independence.productGroupOrder, 3870720);
});

test("all 20,160 abstract fabric addresses round-trip bijectively", () => {
  const seen = new Set();
  for (let control = 0; control < 168; control++) {
    for (let execution = 0; execution < 120; execution++) {
      const address = Fabric.makeAddress(control, execution);
      assert.equal(address.id, control * 120 + execution);
      assert.equal(Fabric.addressFromId(address.id).controlId, control);
      assert.equal(Fabric.addressFromId(address.id).executionVertex, execution);
      assert.equal(address.dispatchable, false);
      seen.add(address.id);
    }
  }
  assert.equal(seen.size, 20160);
  assert.throws(() => Fabric.addressFromId(20160), /\[0, 20159\]/);
});

test("compiled transitions use matched control multiplication and exact 20-way fanout", () => {
  for (let control = 0; control < 168; control += 17) {
    for (let execution = 0; execution < 120; execution += 13) {
      const source = Fabric.makeAddress(control, execution);
      const instruction = (control * 11 + execution) % 168;
      const transition = Fabric.compileTransition(source, instruction);
      assert.equal(transition.matchedActionControlResult,
        Codec.multiplyIds(control, instruction));
      assert.equal(transition.destinationCount, 20);
      assert.equal(new Set(transition.destinationFabricIds).size, 20);
      assert.equal(transition.dispatchable, false);
      assert.equal(Object.isFrozen(transition), true);
      assert.equal(Fabric.verifyTransition(transition), true);
      assert.equal(Fabric.verifyTransition({ ...transition, destinationCount: 19 }), false);
    }
  }
});

test("the numerical A8 coincidence is explicitly quarantined", () => {
  assert.equal(frozen.fabric.states, 20160);
  assert.equal(frozen.fabric.stateCountEqualsOrderA8, true);
  assert.equal(frozen.fabric.a8IdentificationClaimed, false);
  assert.match(frozen.evidenceBoundary, /not A8 elements/);
});
