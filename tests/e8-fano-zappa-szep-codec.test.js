"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const C = require("../analysis/e8_fano_zappa_szep_codec.js");
const frozen = require("../data/e8_fano_zappa_szep_codec.json");

test("the 168-state codec is canonical and GAP-reproducible", { timeout: 60_000 }, () => {
  assert.equal(C.verifyFrozen(frozen), true);
  assert.deepEqual(C.run(), frozen);
  assert.equal(frozen.exactFactorization.type, "exact Zappa-Szep factorization");
  assert.equal(frozen.exactFactorization.directProduct, false);
  assert.equal(frozen.exhaustiveChecks.uniqueDecompositions, 168);
  assert.equal(frozen.exhaustiveChecks.productsAgainstPermutations, 168 ** 2);
  assert.equal(frozen.exhaustiveChecks.associativityTriples, 168 ** 3);
  assert.equal(frozen.exactFactorization.clockFactorNormal, false);
  assert.equal(frozen.exactFactorization.localFactorNormal, false);
  assert.deepEqual(frozen.matchedAction.localActionOnClock.orbitSizes, [1, 2, 4, 8, 4, 2]);
  assert.deepEqual(frozen.matchedAction.clockActionOnLocal.orbitSizes, [1, 7]);
});

test("all clock/local coordinates encode and decode the GAP permutations bijectively", () => {
  const ids = [];
  for (let translation = 0; translation < 7; translation++) {
    for (let phase = 0; phase < 3; phase++) {
      for (let reflection = 0; reflection < 2; reflection++) {
        for (let rotation = 0; rotation < 4; rotation++) {
          const address = C.makeAddress({ translation, phase, rotation, reflection }, frozen);
          ids.push(address.id);
          const decoded = C.decodePermutation([...address.permutation], frozen);
          assert.equal(decoded.id, address.id);
          assert.deepEqual(decoded.clock, { translation, phase });
          assert.deepEqual(decoded.local, { rotation, reflection });
        }
      }
    }
  }
  assert.deepEqual(ids.sort((a, b) => a - b), [...Array(168).keys()]);
});

test("all 28,224 products use the matched actions and agree with permutation composition", () => {
  let nonCoordinatewise = 0;
  for (let left = 0; left < 168; left++) {
    for (let right = 0; right < 168; right++) {
      const actualId = C.multiplyIds(left, right, frozen);
      const expectedPermutation = C.composePermutations(
        frozen.addresses[left].permutation,
        frozen.addresses[right].permutation,
      );
      assert.deepEqual(frozen.addresses[actualId].permutation, expectedPermutation);
      if (actualId !== C.coordinatewiseProductId(left, right, frozen)) nonCoordinatewise++;
    }
  }
  assert.equal(nonCoordinatewise, 23520);
  assert.equal(168 ** 2 - nonCoordinatewise,
    168 * frozen.exhaustiveChecks.commutingCrossPairs);
  const witness = frozen.nontrivialWitness;
  assert.equal(C.multiplyIds(witness.left, witness.right, frozen), witness.zappaProduct);
  assert.equal(C.coordinatewiseProductId(witness.left, witness.right, frozen),
    witness.coordinatewiseProduct);
  assert.notEqual(witness.zappaProduct, witness.coordinatewiseProduct);
});

test("identity and all 168 inverses close in the compiled address algebra", () => {
  for (let id = 0; id < 168; id++) {
    const inverse = C.inverse(id, frozen);
    assert.equal(C.multiplyIds(id, inverse.id, frozen), 0);
    assert.equal(C.multiplyIds(inverse.id, id, frozen), 0);
    assert.equal(C.inverse(inverse, frozen).id, id);
  }
});

test("abstract bus addresses cannot masquerade as live machines", () => {
  const address = C.addressFromId(107, frozen);
  assert.equal(address.addressSpace, C.ADDRESS_SPACE);
  assert.equal(address.dispatchable, false);
  assert.equal(address.liveMachineBinding, null);
  assert.equal(address.requiredNextEvidence, "SIGNED_LIVE_INVENTORY_BINDING");
  assert.match(frozen.evidenceBoundary, /do not identify, attest, reserve, or dispatch to live machines/);
  assert.throws(() => C.addressFromId(168, frozen), /\[0,167\]/);
  assert.throws(() => C.decodePermutation([1, 2, 3, 4, 5, 6, 6], frozen),
    /not a Fano-plane automorphism/);
});
