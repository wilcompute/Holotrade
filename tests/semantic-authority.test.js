const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
global.window = global;

const R = require(path.join(root, "js/result-contract.js"));
const Challenge = require(path.join(root, "js/challenge-market.js"));

const A = `sha256:${"a".repeat(64)}`;
const B = `sha256:${"b".repeat(64)}`;

function firstClass(digest = A, legacy = digest, semantic = digest) {
  return {
    output: {
      result: { schema: R.RESULT_SCHEMA, digest },
      metadata: legacy == null ? {} : { resultDigest: legacy },
    },
    semanticResult: { schema: R.RESULT_SCHEMA, digest: semantic },
  };
}

test("first-class semantic identity is authoritative and redundant locations must agree", () => {
  const emission = firstClass();
  const identity = R.resultIdentityOf(emission);
  assert.equal(identity.digest, A);
  assert.equal(identity.mode, "first-class");
  assert.equal(identity.authoritative, true);
  assert.equal(identity.manualReviewRequired, false);
  assert.equal(R.resultDigestOf(emission), A);
  assert.equal(Challenge.resultDigestOf(emission), A);

  assert.throws(() => R.resultDigestOf(firstClass(A, A, B)), (err) => err.code === "FIRST_CLASS_RESULT_MISMATCH");
  assert.throws(() => Challenge.resultDigestOf(firstClass(A, B, A)), (err) => err.code === "LEGACY_ALIAS_MISMATCH");
});

test("metadata-only result digests require an explicit legacy/advisory opt-in", () => {
  const legacy = { output: { metadata: { resultDigest: A } } };
  assert.throws(() => R.resultDigestOf(legacy), (err) => err.code === "LEGACY_ONLY_RESULT_DIGEST");
  assert.throws(() => Challenge.resultDigestOf(legacy), (err) => err.code === "LEGACY_ONLY_RESULT_DIGEST");
  const identity = R.resultIdentityOf(legacy, { allowLegacy: true });
  assert.equal(identity.digest, A);
  assert.equal(identity.mode, "legacy-metadata");
  assert.equal(identity.authoritative, false);
  assert.equal(identity.manualReviewRequired, true);
});

test("the ovoid artifact proves a sufficient condition, not an unsupported converse", () => {
  const d = require(path.join(root, "data/tensor_multiplicativity_ovoid_defect.json"));
  assert.equal(d.converseProved, false);
  assert.match(d.converseBoundary, /does not by itself imply/);
  assert.equal(d.instances[0].hasOvoid, true);
  assert.equal(d.instances[0].multiplicative, true);
  assert.equal(d.instances[1].hasOvoid, false);
  assert.equal(d.instances[1].ovoidDefect, 1);
  assert.equal(d.w33Nonmultiplicative, true);
  assert.match(d.w33NonmultiplicativityReason, /115 < 121/);
  assert.equal(d.w33CocliqueOvoidDeficit, 3);
  assert.match(d.defectBoundary, /distinct invariants/);
});
