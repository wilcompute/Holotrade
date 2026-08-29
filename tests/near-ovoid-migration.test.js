"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const corpus = require(path.join(root, "data/w33_near_ovoid_adversarial_corpus.json"));
const M = require(path.join(root, "scheduler/w33-near-ovoid-migration.js"));

function intersectionSize(a, b) {
  const B = new Set(b);
  return a.filter((x) => B.has(x)).length;
}

test("all 2880 near-ovoids expose the exact 4-vs-6 release split", () => {
  let states = 0;
  const groups = new Map();
  for (const r of corpus.records) {
    for (const a of r.removals) {
      const busy = r.blocker.filter((x) => x !== a);
      const z = M.analyzeNearOvoid(busy);
      assert.ok(z);
      assert.equal(z.defectCenter, a);
      assert.equal(z.blockerCenter, r.center);
      assert.equal(z.highRelease.length, 4);
      assert.equal(z.ordinaryRelease.length, 6);
      assert.equal(z.guaranteeAfterRecommendedRelease, 7);
      assert.equal(z.guaranteeAfterOrdinaryRelease, 6);
      const key = `${z.defectCenter}:${z.blockerCenter}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(z);
      states++;
    }
  }
  assert.equal(states, 2880);
  assert.equal(groups.size, 480);

  for (const xs of groups.values()) {
    assert.equal(xs.length, 6);
    assert.equal(new Set(xs.map((z) => z.freeLines.join(","))).size, 1,
      "all six m states must have the same current availability");
    assert.equal(new Set(xs.map((z) => z.microstateSignature)).size, 6,
      "release signatures distinguish all six hidden states");
    assert.equal(xs.reduce((S, z) => {
      if (S === null) return new Set(z.highRelease);
      return new Set([...S].filter((p) => z.highRelease.includes(p)));
    }, null).size, 0,
      "there is no universally high-release point after m is forgotten");

    // Intersecting high-release tetrads form two disjoint K3 components.
    const adj = Array.from({ length: 6 }, () => []);
    for (let i = 0; i < 6; i++) for (let j = i + 1; j < 6; j++) {
      const s = intersectionSize(xs[i].highRelease, xs[j].highRelease);
      assert.ok(s === 0 || s === 1);
      if (s === 1) { adj[i].push(j); adj[j].push(i); }
    }
    assert.deepEqual(adj.map((x) => x.length).sort((a,b)=>a-b), [2,2,2,2,2,2]);
    const seen = new Set();
    const comps = [];
    for (let i = 0; i < 6; i++) if (!seen.has(i)) {
      const stack=[i], C=[]; seen.add(i);
      while (stack.length) {
        const u=stack.pop(); C.push(u);
        for (const v of adj[u]) if (!seen.has(v)) { seen.add(v); stack.push(v); }
      }
      comps.push(C);
    }
    assert.deepEqual(comps.map((x)=>x.length).sort(), [3,3]);
    for (const C of comps) {
      const H = C.map((i) => xs[i].highRelease);
      const common = H.reduce((S,h) => new Set([...S].filter((p)=>h.includes(p))), new Set(H[0]));
      const union = new Set(H.flat());
      assert.equal(common.size, 1);
      assert.equal(union.size, 10);
    }
  }
});
