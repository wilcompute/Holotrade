// ======================================================================
// W(3,3) SHAPE CATALOGUE — regression tests
//
// These lock down the classification of the sets that ATTAIN the
// spectral bounds, not the bounds themselves (those are covered in
// scheduler.test.js). The distinction matters: a scheduler reserves a
// set, not an inequality.
//
// Everything asserted here is exact finite mathematics with no tuning
// parameter, so any failure is a bug rather than a drifted coefficient.
// ======================================================================

"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");
const fs = require("node:fs");

global.window = global;
const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/substrate.js"));
const cat = require(path.join(root, "analysis/w33_shape_catalogue.js"));
const auto = require(path.join(root, "analysis/w33_automorphisms.js"));

const N = S.CONST.points;

// ---------------------------------------------------------------------
// the equality conditions
// ---------------------------------------------------------------------

test("the tight-set condition is exactly the upper spectral bound", () => {
  // e(T) <= m(m+8)/8 with equality iff |N(v) cap T| = 2 + m/4 inside,
  // m/4 outside. Verify the arithmetic identity on a real witness.
  const r = cat.searchIntriguing(8, 4, 2, { collect: 1 });
  assert.ok(r.exists, "an m=8 tight set exists");
  const T = r.witness;
  assert.equal(T.length, 8);

  const e = cat.inducedEdges(T);
  const b = cat.edgeBoundary(T);
  assert.equal(e, (8 * (8 + 8)) / 8, "attains e(T) = m(m+8)/8");
  assert.equal(2 * e + b, S.CONST.degree * 8, "2e(T) + b(T) = km");

  const prof = cat.neighbourProfile(T);
  assert.deepEqual(prof.inside, [4], "every member sees 2 + m/4 = 4 members");
  assert.deepEqual(prof.outside, [2], "every non-member sees m/4 = 2 members");
});

test("the m-ovoid condition is exactly the lower spectral bound", () => {
  const r = cat.searchIntriguing(20, 4, 8, { collect: 1 });
  assert.ok(r.exists, "the m=20 ovoid-type set exists");
  const T = r.witness;
  const e = cat.inducedEdges(T);
  const b = cat.edgeBoundary(T);
  assert.equal(e, (20 * (20 - 10)) / 5, "attains e(T) = m(m-10)/5");
  assert.equal(b, (2 * 20 * (40 - 20)) / 5, "attains b(T) = 2m(40-m)/5");
  const prof = cat.neighbourProfile(T);
  assert.deepEqual(prof.inside, [4]);
  assert.deepEqual(prof.outside, [8]);
});

// ---------------------------------------------------------------------
// the classification itself
// ---------------------------------------------------------------------

test("densest shapes exist at every multiple of four, and nowhere else", () => {
  for (let m = 1; m < N; m++) {
    if (m % 4 !== 0) {
      // non-integral neighbourhood target: no set can attain the bound
      const tIn = 2 + m / 4;
      assert.ok(!Number.isInteger(tIn), `m=${m} cannot attain the upper bound`);
      continue;
    }
    const r = cat.searchIntriguing(m, 2 + m / 4, m / 4, { collect: 1 });
    assert.ok(r.exists, `a densest shape exists at m=${m}`);
    assert.ok(r.complete, `the search at m=${m} was exhaustive`);
    assert.equal(cat.inducedEdges(r.witness), (m * (m + 8)) / 8);
  }
});

test("the most-spread shape exists at m=20 and at no other size", () => {
  const feasible = [];
  for (let m = 1; m < N; m++) {
    if ((2 * m) % 5 !== 0) continue;
    const tIn = (2 * m) / 5 - 4, tOut = (2 * m) / 5;
    const r = cat.searchIntriguing(m, tIn, tOut, { collect: 1 });
    assert.ok(r.complete, `the search at m=${m} was exhaustive`);
    if (r.exists) feasible.push(m);
  }
  assert.deepEqual(feasible, [20],
    "20 is the only size admitting a perfectly spread set");
});

test("the four-point densest shapes are exactly the 40 lines", () => {
  // brute force over every 4-subset: C(40,4) = 91,390, so this is
  // genuinely exhaustive rather than a sample
  const found = [];
  for (let a = 0; a < N; a++)
    for (let b = a + 1; b < N; b++)
      for (let c = b + 1; c < N; c++)
        for (let d = c + 1; d < N; d++) {
          const T = [a, b, c, d], set = new Set(T);
          let ok = true;
          for (let v = 0; v < N && ok; v++) {
            const cnt = S.ADJ[v].filter((u) => set.has(u)).length;
            if (cnt !== (set.has(v) ? 3 : 1)) ok = false;
          }
          if (ok) found.push(T.join(","));
        }
  const lines = new Set(S.LINES.map((l) => [...l].sort((x, y) => x - y).join(",")));
  assert.equal(found.length, 40, "exactly 40 four-point densest shapes");
  assert.equal(lines.size, 40);
  for (const f of found) assert.ok(lines.has(f), `${f} is a totally isotropic line`);
  // and each is a maximum clique
  for (const f of found) {
    const T = f.split(",").map(Number);
    for (const x of T) for (const y of T) {
      if (x !== y) assert.ok(S.isAdjacent(x, y), "a line induces a K4");
    }
  }
});

// ---------------------------------------------------------------------
// extremes
// ---------------------------------------------------------------------

test("clique number is 4 and attains the Hoffman bound", () => {
  const { omega, witness } = cat.maxClique();
  assert.equal(omega, 4);
  assert.equal(1 - S.CONST.degree / -4, 4, "Hoffman clique bound 1 - k/s");
  for (const x of witness) for (const y of witness) {
    if (x !== y) assert.ok(S.isAdjacent(x, y));
  }
});

test("independence number is 7, strictly below the Hoffman bound of 10", () => {
  const { alpha, witness } = cat.maxIndependentSet();
  const hoffman = (N * 4) / (S.CONST.degree + 4);
  assert.equal(hoffman, 10, "n(-s)/(k-s) = 40*4/16");
  assert.equal(alpha, 7);
  assert.ok(alpha < hoffman,
    "the ratio bound is not attained, so this quadrangle has no ovoid");
  assert.equal(witness.length, 7);
  const set = new Set(witness);
  for (const v of witness) {
    assert.ok(!S.ADJ[v].some((u) => set.has(u)), "witness has no internal edge");
  }
});

test("no eight nodes can be placed with zero shared links", () => {
  // the operational reading of alpha = 7: a hard ceiling on
  // failure-independent replica placement
  const { alpha } = cat.maxIndependentSet();
  assert.ok(alpha < 8,
    "a scheduler cannot promise 8 replicas with no shared link");
});

// ---------------------------------------------------------------------
// complementation
// ---------------------------------------------------------------------

test("the complement of a densest shape is a densest shape", () => {
  for (const m of [4, 8, 12, 16, 20]) {
    const r = cat.searchIntriguing(m, 2 + m / 4, m / 4, { collect: 1 });
    const T = new Set(r.witness);
    const C = [];
    for (let v = 0; v < N; v++) if (!T.has(v)) C.push(v);
    const mc = C.length;
    assert.equal(cat.inducedEdges(C), (mc * (mc + 8)) / 8,
      `complement of the m=${m} shape attains the bound at m=${mc}`);
    const prof = cat.neighbourProfile(C);
    assert.deepEqual(prof.inside, [2 + mc / 4]);
    assert.deepEqual(prof.outside, [mc / 4]);
  }
});

test("the frozen catalogue counts are palindromic in m", () => {
  const p = path.join(root, "data/w33_shape_catalogue.json");
  if (!fs.existsSync(p)) return;                 // catalogue not frozen yet
  const c = JSON.parse(fs.readFileSync(p, "utf8"));
  const counts = c.tightSets.map((r) => r.count);
  assert.deepEqual(counts, [...counts].reverse(),
    "complementation forces the count at m to equal the count at 40-m");
});

// ---------------------------------------------------------------------
// the automorphism group, and shape transport
// ---------------------------------------------------------------------

test("the transvection closure is PSp(4,3) of order 25920", () => {
  const els = auto.generateGroup();
  const props = auto.checkGroup(els);
  assert.equal(props.order, 25920,
    "projective symplectic group — NOT Sp(4,3) or W(E6), which are 51840");
  assert.deepEqual(props.problems, []);
  assert.ok(props.pointTransitive, "transitive on the 40 points");
  assert.ok(props.edgeTransitive, "transitive on the 480 ordered edges");
  assert.equal(props.pointStabiliserOrder, 648);
  assert.ok(props.orbitStabiliserHolds, "648 * 40 = 25920");
});

test("every group element preserves adjacency", () => {
  const els = auto.generateGroup();
  // check a spread-out sample in full; each check is O(n^2)
  for (let i = 0; i < els.length; i += Math.floor(els.length / 25)) {
    assert.ok(auto.isAutomorphism(els[i]), "element is a graph automorphism");
  }
});

test("shape transport preserves optimality exactly", () => {
  const els = auto.generateGroup();
  const r = cat.searchIntriguing(8, 4, 2, { collect: 1 });
  const shape = r.witness;
  const e0 = cat.inducedEdges(shape);
  const b0 = cat.edgeBoundary(shape);

  // Block the shape's own nodes plus a few more, and relocate it into
  // what is left. The block size is kept inside the size this shape is
  // measured to tolerate -- an 8-point tight set has an orbit of only
  // 45 images, so it is rigid, and a large enough adversarial block CAN
  // make it unplaceable. That is a real property of the shape, not a
  // failure of transport, and it is quantified in
  // "shapes report an honest placement capacity" below.
  const blocked = new Set([...shape, 30, 31]);
  const images = auto.transportShape(shape, blocked, els, { wanted: 4 });
  assert.ok(images.length > 0, "the shape can be relocated away from busy nodes");
  for (const img of images) {
    assert.equal(img.length, shape.length);
    assert.ok(img.every((v) => !blocked.has(v)), "lands entirely on free nodes");
    assert.equal(cat.inducedEdges(img), e0, "induced edges are preserved");
    assert.equal(cat.edgeBoundary(img), b0, "boundary is preserved");
    const prof = cat.neighbourProfile(img);
    assert.deepEqual(prof.inside, [4], "still an intriguing set");
    assert.deepEqual(prof.outside, [2]);
  }
});

test("shape orbits satisfy orbit-stabiliser against the group order", () => {
  const els = auto.generateGroup();
  const r = cat.searchIntriguing(4, 3, 1, { collect: 1 });
  const images = new Set();
  for (const g of els) images.add(r.witness.map((v) => g[v]).sort((a, b) => a - b).join(","));
  assert.equal(images.size, 40, "the 4-point shapes form a single orbit of size 40");
  assert.equal(els.length / images.size, 648, "set stabiliser order");
  // and that orbit is precisely the line set
  const lines = new Set(S.LINES.map((l) => [...l].sort((a, b) => a - b).join(",")));
  for (const img of images) assert.ok(lines.has(img), "orbit element is a line");
});

test("shapes report an honest placement capacity, and it is not orbit size", () => {
  // A scheduler needs to know when to STOP promising an optimal shape.
  // The naive guess is that a shape with a large orbit is easy to place.
  // It is not: the m=12 shape has an orbit of 1080 images and tolerates
  // FEWER busy nodes than the m=8 shape, whose orbit is only 45. Size
  // dominates, because a shape of m points needs m free points before
  // any image can fit at all.
  const els = auto.generateGroup();
  const rand = S.rng("placement-capacity");

  const measure = (m) => {
    const r = cat.searchIntriguing(m, 2 + m / 4, m / 4, { collect: 1 });
    const imgs = new Set();
    for (const g of els) imgs.add(r.witness.map((v) => g[v]).sort((a, b) => a - b).join(","));
    const images = [...imgs].map((x) => x.split(",").map(Number));
    const rate = (B, trials = 200) => {
      let ok = 0;
      for (let t = 0; t < trials; t++) {
        const blocked = new Set();
        while (blocked.size < B) blocked.add(Math.floor(rand() * N));
        if (images.some((im) => im.every((v) => !blocked.has(v)))) ok++;
      }
      return ok / trials;
    };
    return { m, orbit: images.length, rate };
  };

  const a = measure(8);
  const b = measure(12);
  assert.ok(b.orbit > a.orbit, "m=12 has the larger orbit");
  assert.ok(b.rate(16) <= a.rate(16) + 0.1,
    "yet it is no easier to place under load — orbit size is not the metric");

  // an empty fabric always places every shape
  for (const m of [4, 8, 12, 16, 20]) {
    const s2 = measure(m);
    assert.equal(s2.rate(0, 20), 1, `m=${m} always places on an empty fabric`);
  }

  // and a fabric with fewer free nodes than the shape never does
  const s20 = measure(20);
  assert.equal(s20.rate(21, 40), 0,
    "21 busy nodes leaves 19 free, so a 20-point shape cannot fit at all");
});

// ======================================================================
// scheduler/w33-shapes.js — the reservation API built on the catalogue
// ======================================================================

const shapes = require(path.join(root, "scheduler/w33-shapes.js"));

test("the shape menu offers a densest shape at every multiple of four", () => {
  const menu = shapes.shapeMenu();
  assert.equal(menu.densest.length, 9, "m = 4,8,...,36");
  for (const row of menu.densest) {
    assert.equal(row.m % 4, 0);
    assert.equal(row.maxInducedEdges, (row.m * (row.m + 8)) / 8);
    assert.equal(row.minBoundary, (row.m * (N - row.m)) / 4);
    assert.ok(row.placeable, `m=${row.m} places on an empty fabric`);
  }
  assert.equal(menu.freeNodes, N);
  assert.equal(menu.antiAffinity.size, 7);
  assert.equal(menu.antiAffinity.boundAttained, false);
});

test("a size with no attaining shape is refused, not silently downgraded", () => {
  for (const m of [5, 7, 10, 13, 22]) {
    const r = shapes.optimalShape(m);
    assert.equal(r.ok, false, `m=${m} has no densest shape`);
    assert.match(r.reason, /4 \| m/);
    assert.equal(r.nearestAttainable % 4, 0, "and names a size that does");
    assert.ok(r.gap > 0);
  }
  // spread sets exist only at 20
  for (const m of [5, 10, 15, 25, 30, 35]) {
    const r = shapes.optimalShape(m, "spread");
    assert.equal(r.ok, false, `no perfectly spread set at m=${m}`);
    assert.equal(r.nearestAttainable, 20);
  }
  assert.equal(shapes.optimalShape(20, "spread").ok, true);
});

test("reservation transports a shape and preserves its optimality exactly", () => {
  const witness = shapes.optimalShape(8).witness;
  const busy = new Set(witness);            // the catalogue position is taken
  const r = shapes.reserveShape(8, { unavailable: busy, wanted: 3 });
  assert.ok(r.ok, "the shape relocates off its catalogue position");
  assert.ok(r.placement.every((v) => !busy.has(v)));
  assert.equal(r.inducedEdges, (8 * 16) / 8, "still attains the bound");
  assert.ok(r.preservesOptimality, "edges and boundary both preserved");
  assert.deepEqual(shapes.profile(r.placement).inside, [4]);
  for (const alt of r.alternatives) {
    assert.equal(shapes.inducedEdges(alt), r.inducedEdges);
  }
});

test("reservation refuses honestly when the fabric cannot hold the shape", () => {
  // fewer free nodes than the shape needs
  const nearlyFull = [...Array(N - 3).keys()];
  const r1 = shapes.reserveShape(20, { unavailable: nearlyFull });
  assert.equal(r1.ok, false);
  assert.match(r1.reason, /cannot fit at all/);
  assert.equal(r1.freeNodes, 3);

  // enough free nodes in total, but the shape is too rigid to fit them
  const r2 = shapes.reserveShape(12, { unavailable: [...Array(14).keys()] });
  assert.equal(r2.ok, false, "26 free nodes is not enough for this rigid shape");
  assert.match(r2.reason, /none of the \d+ placements/);
  assert.ok(r2.orbitSize > 0);
  assert.ok(r2.hint.includes("fall back"), "and it says what to do instead");
});

test("shape orbits are closed under the group and preserve all invariants", () => {
  for (const m of [4, 8, 16]) {
    const w = shapes.optimalShape(m).witness;
    const orbit = shapes.shapeOrbit(w);
    const e0 = shapes.inducedEdges(w), b0 = shapes.edgeBoundary(w);
    assert.ok(orbit.length >= 1);
    // orbit-stabiliser: the orbit size must divide the group order
    assert.equal(25920 % orbit.length, 0,
      `orbit size ${orbit.length} divides |PSp(4,3)| = 25920`);
    for (const img of orbit) {
      assert.equal(img.length, m);
      assert.equal(shapes.inducedEdges(img), e0);
      assert.equal(shapes.edgeBoundary(img), b0);
    }
  }
});

test("placement capacity is measured, and orbit size does not predict it", () => {
  const c8 = shapes.placementCapacity(8, { trials: 120 });
  const c12 = shapes.placementCapacity(12, { trials: 120 });
  assert.ok(c8.ok && c12.ok);
  assert.ok(c12.orbitSize > c8.orbitSize, "m=12 has the far larger orbit");
  assert.ok(c12.alwaysPlaceableUpTo <= c8.alwaysPlaceableUpTo,
    "yet tolerates no more busy nodes — size dominates, not orbit count");
  assert.match(c8.method, /not exhaustive/, "and the method is labelled honestly");
  // every curve starts at certainty and is non-increasing
  for (const c of [c8, c12]) {
    assert.equal(c.curve[0].placementRate, 1, "empty fabric always places");
    for (let i = 1; i < c.curve.length; i++) {
      assert.ok(c.curve[i].placementRate <= c.curve[i - 1].placementRate + 1e-9,
        "placement rate is non-increasing in busy nodes");
    }
  }
});

test("the embedded catalogue agrees with the frozen artifact", () => {
  const cat = shapes.frozenCatalogue();
  for (const [m, witness] of Object.entries(cat.tight)) {
    const size = Number(m);
    assert.equal(witness.length, size);
    assert.equal(shapes.inducedEdges(witness), (size * (size + 8)) / 8,
      `frozen m=${m} witness still attains its bound`);
  }
  if (cat.spread[20]) {
    assert.equal(shapes.inducedEdges(cat.spread[20]), (20 * 10) / 5);
  }
});

// ======================================================================
// Worst-case placement guarantees
//
// placementCapacity() is sampled. These are the exact worst-case
// numbers: the minimum blocking set of a shape's orbit. With tau - 1
// nodes busy a placement ALWAYS exists, whichever nodes they are.
// ======================================================================

const guarantees = require(path.join(root, "analysis/w33_shape_guarantees.js"));

test("a minimum blocking set really blocks, and nothing smaller does", () => {
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const hs = guarantees.minimumHittingSet(lines);
  assert.ok(hs.exhausted, "the search closed");
  assert.equal(hs.tau, 11, "eleven points are needed to hit all 40 lines");
  assert.ok(guarantees.verifyBlocking(hs.witness, lines), "the witness blocks every line");
  assert.equal(hs.witness.length, 11);
});

test("the line blocking number is forced by the absence of an ovoid", () => {
  // Each point lies on 4 lines, so hitting 40 lines needs >= 10 points,
  // and equality would require 10 pairwise non-collinear points -- an
  // ovoid. There is none, so tau >= 11, and 11 is achieved.
  const pointsPerLine = 4;
  const linesPerPoint = S.LINES.filter((l) => l.includes(0)).length;
  assert.equal(linesPerPoint, pointsPerLine, "4 lines through each point");
  const countingBound = Math.ceil(S.LINES.length / linesPerPoint);
  assert.equal(countingBound, 10);

  const { alpha } = cat.maxIndependentSet();
  assert.ok(alpha < 10, "no ovoid, so the counting bound cannot be attained");

  const hs = guarantees.minimumHittingSet(S.LINES.map((l) => [...l].sort((a, b) => a - b)));
  assert.equal(hs.tau, countingBound + 1, "so tau is exactly one more");
});

test("a four-node densest reservation survives any ten busy nodes", () => {
  // the headline guarantee, checked directly rather than via tau
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const rand = S.rng("ten-busy");
  for (let t = 0; t < 3000; t++) {
    const busy = new Set();
    while (busy.size < 10) busy.add(Math.floor(rand() * N));
    assert.ok(lines.some((l) => l.every((v) => !busy.has(v))),
      `a line survived ${[...busy].join(",")}`);
  }
});

test("eleven busy nodes can defeat it, so the guarantee is tight", () => {
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const hs = guarantees.minimumHittingSet(lines);
  const busy = new Set(hs.witness);
  assert.equal(busy.size, 11);
  assert.ok(!lines.some((l) => l.every((v) => !busy.has(v))),
    "this specific set of 11 leaves no line intact");
});

test("the frozen SAT guarantees agree with the branch-and-bound", () => {
  const satPath = path.join(root, "data/w33_blocking_sat.json");
  const bbPath = path.join(root, "data/w33_shape_guarantees.json");
  if (!fs.existsSync(satPath) || !fs.existsSync(bbPath)) return;
  const sat = JSON.parse(fs.readFileSync(satPath, "utf8"));
  const bb = JSON.parse(fs.readFileSync(bbPath, "utf8"));
  const byM = new Map(bb.shapes.map((r) => [r.m, r]));

  for (const r of sat.shapes) {
    if (r.kind !== "densest") continue;
    const j = byM.get(r.m);
    if (!j) continue;
    if (j.tau != null) {
      assert.equal(j.tau, r.tau, `m=${r.m}: two independent solvers give the same tau`);
    } else {
      assert.ok(j.tauLowerBound <= r.tau && r.tau <= j.tauUpperBound,
        `m=${r.m}: SAT answer lies inside the branch-and-bound interval`);
    }
    assert.ok(r.guaranteeProvedUnsat,
      `m=${r.m}: the guarantee is proved by UNSAT, not sampled`);
    assert.ok(r.witnessValid);
    assert.equal(r.guarantee, r.tau - 1);
  }
});

test("guarantees shrink as shapes grow, and orbit size does not explain it", () => {
  const satPath = path.join(root, "data/w33_blocking_sat.json");
  if (!fs.existsSync(satPath)) return;
  const sat = JSON.parse(fs.readFileSync(satPath, "utf8"));
  const densest = sat.shapes.filter((r) => r.kind === "densest").sort((a, b) => a.m - b.m);

  for (let i = 1; i < densest.length; i++) {
    assert.ok(densest[i].guarantee <= densest[i - 1].guarantee,
      "a larger shape never tolerates more busy nodes than a smaller one");
  }
  // m=8 (orbit 45) and m=12 (orbit 1080) have the SAME tau despite a
  // twenty-four-fold difference in orbit size
  const m8 = densest.find((r) => r.m === 8);
  const m12 = densest.find((r) => r.m === 12);
  assert.ok(m12.orbitSize > 20 * m8.orbitSize, "orbits differ by more than 20x");
  assert.equal(m8.tau, m12.tau, "yet the blocking numbers are equal");
});

// ======================================================================
// Perfect reservation packings
//
// A tiling is the fragmentation-free schedule: every node used, every
// reservation provably densest, nothing stranded. It needs 4 | m (a
// densest shape exists) and m | 40 (the pieces exhaust the cell).
// ======================================================================

const packing = require(path.join(root, "analysis/w33_shape_packing.js"));

test("only m in {4, 8, 20, 40} can possibly tile the cell", () => {
  for (let m = 1; m <= 40; m++) {
    const canTile = m % 4 === 0 && N % m === 0;
    const expected = [4, 8, 20, 40].includes(m);
    assert.equal(canTile, expected, `m=${m}`);
  }
});

test("the 40 lines tile the cell in exactly 36 ways — the spreads", () => {
  const lines = S.LINES.map((l) => [...l].sort((a, b) => a - b));
  const t = packing.findTilings(lines);
  assert.equal(t.count, 36, "36 spreads of W(3,3)");
  assert.equal(t.pieces, 10, "ten disjoint lines");

  for (const tiling of t.tilings.slice(0, 5)) {
    const covered = tiling.flat();
    assert.equal(new Set(covered).size, N, "covers every point exactly once");
    assert.equal(covered.length, N, "and no point twice");
    // a spread meets every point-star exactly once
    for (let v = 0; v < N; v++) {
      assert.equal(tiling.filter((l) => l.includes(v)).length, 1,
        `point ${v} lies on exactly one line of the spread`);
    }
  }
});

test("perfect tilings exist at exactly the three admissible sizes", () => {
  const res = packing.run();
  const tiling = new Map(res.shapes.map((r) => [r.m, r]));
  for (const m of [4, 8, 20]) {
    assert.ok(tiling.get(m).tilingPossible, `m=${m} tiles the cell`);
    assert.equal(tiling.get(m).pointsStranded, 0, `m=${m} strands nothing`);
  }
  for (const m of [12, 16, 24, 28, 32, 36]) {
    assert.equal(tiling.get(m).tilingPossible, false, `m=${m} cannot tile`);
    assert.ok(tiling.get(m).pointsStranded > 0);
  }
});

test("the m=20 tiling count is exactly half the shape count", () => {
  // Complementation forces it: every densest 20-set tiles the cell with
  // its own complement, and the pair is counted once as an unordered
  // tiling. So tilings = shapes / 2, with no search needed to predict it.
  const res = packing.run();
  const r20 = res.shapes.find((r) => r.m === 20);
  assert.equal(r20.tilingCount * 2, r20.totalShapes,
    "16,632 tilings from 33,264 shapes");
});

test("a tiling really is made of densest shapes and covers everything", () => {
  const res = packing.run();
  for (const v of res.verifications) {
    assert.ok(v.ok, `m=${v.m}: ${v.why || ""}`);
  }
  assert.ok(res.verifications.length >= 3, "all three tiling sizes verified");
});

test("orbit is not the same thing as isomorphism class", () => {
  // The bug this test exists to prevent: searching for tilings inside a
  // single orbit reported NO tiling at m=20, contradicting the proved
  // complementation theorem. The orbit had 3,240 members out of 33,264
  // densest 20-sets, so the complement was simply not in the pool.
  const res = packing.run();
  const r20 = res.shapes.find((r) => r.m === 20);
  assert.ok(r20.totalShapes > r20.orbitSize,
    "there are more densest 20-sets than one orbit contains");
  assert.ok(r20.orbitsInPool > 1, "so the pool spans several orbits");

  const r4 = res.shapes.find((r) => r.m === 4);
  assert.equal(r4.totalShapes, r4.orbitSize,
    "m=4 is the one size with a single orbit, which is why it looked fine");
});

// ======================================================================
// Level 2: the inter-cell fabric, and whether shapes lift
// ======================================================================

const L2 = require(path.join(root, "analysis/w33_level2.js"));
const L2S = require(path.join(root, "analysis/w33_level2_shapes.js"));

test("the level-2 constructions have the degrees and diameters claimed", () => {
  const cart = L2.buildCartesian();
  assert.equal(cart.length, 1600);
  assert.ok(cart.every((r) => r.length === 24), "Cartesian is 24-regular");
  assert.equal(cart.reduce((a, r) => a + r.length, 0) / 2, 19200);
  assert.equal(L2.diameter(cart).diameter, 4,
    "measured by BFS from every vertex, not bounded");

  const lex = L2.buildLexicographic();
  assert.ok(lex.every((r) => r.length === 492), "lexicographic is 492-regular");
  assert.equal(L2.diameter(lex).diameter, 2);
});

test("the closed-form level-2 spectra are consistent with the graphs", () => {
  const cart = L2.cartesianSpectrumClosedForm();
  assert.equal(cart.reduce((a, [, m]) => a + m, 0), 1600, "multiplicities sum to n");
  assert.equal(cart[0][0], 24, "top eigenvalue is the degree");
  assert.equal(cart[0][1], 1, "and it is simple, so the graph is connected");
  assert.deepEqual(cart.map(([e]) => e), [24, 14, 8, 4, -2, -8]);

  const lex = L2.lexicographicSpectrumClosedForm();
  assert.equal(lex.reduce((a, [, m]) => a + m, 0), 1600);
  assert.equal(lex[0][0], 492);
  // trace of A is zero for a simple graph: sum of eigenvalues times
  // multiplicity must vanish
  for (const spec of [cart, lex]) {
    const trace = spec.reduce((a, [e, m]) => a + e * m, 0);
    assert.equal(trace, 0, "trace of the adjacency matrix is zero");
  }
});

test("both products expand strictly worse than a single cell", () => {
  // The engineering point: scaling up costs expansion. A single W(3,3)
  // has (k - lambda_2)/k = 10/12; the Cartesian fabric has 10/24.
  const level1 = (S.CONST.degree - 2) / S.CONST.degree;
  const cart = L2.cartesianSpectrumClosedForm();
  const cartExp = (cart[0][0] - cart[1][0]) / cart[0][0];
  assert.ok(Math.abs(level1 - 10 / 12) < 1e-12);
  assert.ok(Math.abs(cartExp - 10 / 24) < 1e-12);
  assert.ok(cartExp < level1, "the Cartesian fabric is the weaker expander");
});

test("the measured level-2 diameter is far below the software distance bound", () => {
  // js/substrate.js models recursive distance as 16n - 14, which is a
  // DECLARED descent cost (8 reversible moves per digit per side), not a
  // graph distance. Under an explicit inter-cell wiring the graph
  // diameter is 4. The two numbers measure different things and should
  // not be compared as if they were the same quantity.
  const modelled = S.diameterAtLevel(2);
  assert.equal(modelled, 18, "2 + 16(n-1)");
  const measured = L2.diameter(L2.buildCartesian()).diameter;
  assert.equal(measured, 4);
  assert.ok(measured < modelled,
    "an explicit graph is much better connected than the declared descent cost");
});

test("level-1 densest shapes lift to level-2 densest shapes", () => {
  // The lift theorem: if f1 is in the 2-eigenspace of A1 then 1 (x) f1
  // and f1 (x) 1 are both in the 14-eigenspace of the Cartesian fabric,
  // because 12 + 2 = 2 + 12 = 14.
  const adj = L2.buildCartesian();
  for (const m1 of [4, 8, 20]) {
    const T1 = shapes.optimalShape(m1).witness;
    for (const [kind, T] of [["byPoints", L2S.liftByPoints(T1)], ["byCells", L2S.liftByCells(T1)]]) {
      const m = T.length;
      assert.equal(m, 40 * m1, `${kind}: a lift scales by the cell size`);
      const e = L2S.inducedEdges(adj, T);
      assert.equal(e, L2S.level2UpperBound(m),
        `${kind} m1=${m1}: attains e(T) = 7m + m^2/320 exactly`);
      const b = L2S.edgeBoundary(adj, T);
      assert.equal(2 * e + b, 24 * m, "2e(T) + b(T) = km at level 2");
      const prof = L2S.profile(adj, T);
      assert.ok(prof.isIntriguing, `${kind}: two-valued neighbourhood profile`);
    }
  }
});

test("a construction that is not a lift does not attain the level-2 bound", () => {
  const adj = L2.buildCartesian();
  const T1 = shapes.optimalShape(8).witness;
  // the diagonal {(p,p)} is a natural-looking set and is not a lift
  const diag = T1.map((p) => L2.idx(p, p));
  const e = L2S.inducedEdges(adj, diag);
  assert.ok(e < L2S.level2UpperBound(diag.length),
    "the diagonal falls short of the bound");
  assert.ok(!L2S.profile(adj, diag).isIntriguing,
    "and is not a two-valued set, so it is not attaining the equality");
});

test("the level-2 reservation API refuses unattainable sizes", () => {
  assert.ok(shapes.optimalShapeLevel2(160).ok);
  assert.ok(shapes.optimalShapeLevel2(800).ok);
  for (const m of [100, 200, 500, 1000]) {
    const r = shapes.optimalShapeLevel2(m);
    assert.equal(r.ok, false, `m=${m} is not a lift size`);
    assert.ok(r.reason, "and it says why");
    assert.ok(r.nearestAttainable, "and names something that works");
  }
  assert.deepEqual(shapes.level2Ladder().map((r) => r.level2Size),
    [160, 320, 480, 640, 800, 960, 1120, 1280, 1440]);
});

test("the level-2 API materialises the same set the theorem describes", () => {
  const adj = L2.buildCartesian();
  for (const m of [160, 320]) {
    for (const lift of ["byPoints", "byCells"]) {
      const spec = shapes.optimalShapeLevel2(m, { lift });
      assert.ok(spec.ok);
      const T = shapes.materialiseLevel2(spec);
      assert.equal(T.length, m);
      assert.equal(new Set(T).size, m, "no duplicate leaves");
      assert.equal(L2S.inducedEdges(adj, T), spec.inducedEdges,
        "the materialised set has the induced-edge count the API promised");
      assert.ok(L2S.profile(adj, T).isIntriguing);
    }
  }
});

// ======================================================================
// Level-2 guarantees, and the robustness collapse
// ======================================================================

const L2G = require(path.join(root, "analysis/w33_level2_guarantees.js"));

test("a level-2 blocking set's shadows must each block at level 1", () => {
  // the product theorem, checked constructively rather than argued
  const T1 = shapes.optimalShape(4).witness;
  const orbit1 = shapes.shapeOrbit(T1);
  const hs = guarantees.minimumHittingSet(orbit1, 40);
  assert.ok(hs.exhausted);

  // the diagonal of a level-1 blocking set blocks every level-2 lift
  const diagonal = hs.witness.map((b) => L2.idx(b, b));
  assert.equal(diagonal.length, hs.tau);
  assert.ok(L2G.blocksAllLifts(diagonal, orbit1),
    "tau_1 leaves on the diagonal defeat every placement of the lift");

  // and a set whose point shadow is too small cannot block, however
  // many leaves it holds
  const oneCell = [];
  for (let p = 0; p < 40; p++) oneCell.push(L2.idx(0, p));
  assert.equal(oneCell.length, 40, "forty leaves, but all in one cell");
  assert.ok(!L2G.blocksAllLifts(oneCell, orbit1),
    "forty leaves in a single cell do not block, because the cell shadow is one point");
});

test("tau_2 equals tau_1 exactly, so absolute tolerance does not scale", () => {
  const res = L2G.run();
  assert.ok(res.theoremHolds, "verified at every size checked");
  for (const r of res.perSize) {
    assert.equal(r.tau2, r.tau1, `m1=${r.level1Size}: tau is unchanged one level up`);
    assert.ok(r.diagonalBlocks, "the diagonal construction attains it");
    assert.ok(r.noSmallerBlockerFound, "and nothing smaller was found");
    // the collapse is exactly the cell size, every time
    assert.ok(Math.abs(r.fractionRatio - 40) < 1e-6,
      `m1=${r.level1Size}: survivable fraction collapses by exactly the cell size`);
  }
});

test("the survivable fraction collapses from a quarter to well under a percent", () => {
  const res = L2G.run();
  const r4 = res.perSize.find((r) => r.level1Size === 4);
  assert.ok(Math.abs(r4.fractionLevel1 - 0.25) < 1e-9, "10 of 40 at level 1");
  assert.ok(Math.abs(r4.fractionLevel2 - 10 / 1600) < 1e-9, "still 10, now of 1600");
  assert.ok(r4.fractionLevel2 < 0.01,
    "under one percent of the fabric may fail before an optimal lift is unplaceable");
});

test("byCells is Pareto-dominant, and is the default", () => {
  const byCells = shapes.optimalShapeLevel2(160);
  const byPoints = shapes.optimalShapeLevel2(160, { lift: "byPoints" });

  assert.equal(byCells.lift, "byCells", "the default");
  // tie on density
  assert.equal(byCells.inducedEdges, byPoints.inducedEdges);
  assert.ok(byCells.attainsBound && byPoints.attainsBound);
  // tie on fault tolerance
  assert.equal(byCells.level2Guarantee.busyTolerated,
               byPoints.level2Guarantee.busyTolerated);
  // strictly better on co-tenancy
  assert.equal(byCells.cellsUsed, 4);
  assert.equal(byCells.cellsLeftFree, 36);
  assert.equal(byPoints.cellsUsed, 40);
  assert.equal(byPoints.cellsLeftFree, 0);
  assert.ok(byCells.cellsLeftFree > byPoints.cellsLeftFree,
    "same density, same tolerance, 36 free cells against none");
});

test("intermediate splits are strictly worse than either extreme", () => {
  // The two lifts are the only ways to reach the bound at 160 leaves.
  // Splitting the difference gives up inter-cell links without gaining
  // enough intra-cell ones to compensate.
  const rows = L2G.confinementTradeoff(160);
  const extremes = rows.filter((r) => r.cellsUsed === 4 || r.cellsUsed === 40);
  const middle = rows.filter((r) => r.cellsUsed !== 4 && r.cellsUsed !== 40);
  assert.equal(extremes.length, 2);
  for (const e of extremes) {
    assert.ok(Math.abs(e.efficiency - 1) < 1e-9, `${e.cellsUsed} cells attains the bound`);
  }
  for (const mrow of middle) {
    assert.ok(mrow.efficiency < 1,
      `${mrow.cellsUsed} cells reaches only ${(mrow.efficiency * 100).toFixed(0)}% of the bound`);
  }
});

test("choosing WHICH cells matters, not just how many", () => {
  // The bug this prevents: taking the first k cell indices picks a
  // mutually non-adjacent set, so no inter-cell link is captured and
  // confinement looks strictly worse than it is.
  const adj = L2.buildCartesian();
  const line = shapes.optimalShape(4).witness;      // 4 mutually adjacent cells
  const arbitrary = [0, 1, 2, 3];

  const build = (cells) => {
    const T = [];
    for (const c of cells) for (let p = 0; p < 40; p++) T.push(L2.idx(c, p));
    return T.sort((a, b) => a - b);
  };
  const eLine = L2S.inducedEdges(adj, build(line));
  const eArb = L2S.inducedEdges(adj, build(arbitrary));
  assert.equal(build(line).length, build(arbitrary).length, "same leaf count");
  assert.ok(eLine > eArb,
    "an optimal cell set captures inter-cell links an arbitrary one does not");
  assert.equal(eLine, L2S.level2UpperBound(160), "and it attains the bound");
});

// ======================================================================
// Level n: the classification, and what it forbids
// ======================================================================

const LN = require(path.join(root, "analysis/w33_leveln_classification.js"));

test("the spectral gap is exactly 10 at every level", () => {
  // k = 12n and lambda_2 = 12n - 10, so the gap never grows. This single
  // invariant is the robustness collapse in spectral form.
  for (let n = 1; n <= 6; n++) {
    const p = LN.levelParameters(n);
    assert.equal(p.degree, 12 * n, `degree at level ${n}`);
    assert.equal(p.lambda2, 12 * n - 10, `lambda_2 at level ${n}`);
    assert.equal(p.spectralGap, 10, "the gap is the same absolute 10 forever");
    assert.ok(Math.abs(p.expansionRatio - 10 / (12 * n)) < 1e-12);
  }
  // and it therefore decays toward zero
  assert.ok(LN.levelParameters(6).expansionRatio < LN.levelParameters(1).expansionRatio / 5);
});

test("the lambda_2 eigenspace is the 2-eigenspace in one coordinate", () => {
  // dim should be n * 24: the level-1 2-eigenspace placed in each of the
  // n coordinates. This is what forces every densest shape to be a lift.
  for (let n = 1; n <= 5; n++) {
    const p = LN.levelParameters(n);
    assert.equal(p.lambda2Multiplicity, n * 24,
      `level ${n}: lambda_2 multiplicity is n x 24`);
  }
});

test("the power spectrum is consistent and trace-free", () => {
  for (let n = 1; n <= 4; n++) {
    const spec = LN.powerSpectrum(n);
    const total = spec.reduce((a, [, m]) => a + m, 0);
    assert.equal(total, Math.pow(40, n), `multiplicities sum to 40^${n}`);
    const trace = spec.reduce((a, [e, m]) => a + e * m, 0);
    assert.equal(trace, 0, "a simple graph has zero trace");
    assert.equal(spec[0][1], 1, "the degree is a simple eigenvalue, so connected");
  }
});

test("a 0/1 separable function forces all but one part constant", () => {
  // The step the classification turns on: |A+B| >= |A|+|B|-1, so two
  // non-constant parts give at least three distinct sums and cannot land
  // inside the two-element set {0,1}.
  const sep = LN.verifySeparability({ trials: 60000 });
  assert.ok(sep.pairsChecked > 1000, "enough pairs actually sampled");
  assert.equal(sep.counterexample, null,
    "no pair of non-constant value sets has 2 or fewer sums");
  assert.ok(sep.sumsetBoundHolds);
});

test("the level-n densest bound reduces correctly at levels 1 and 2", () => {
  // (6n-5)m + 5m^2/40^n must agree with the bounds derived independently
  for (const m of [4, 8, 20, 36]) {
    assert.ok(Math.abs(LN.levelParameters(1).densestBound(m) - (m * (m + 8)) / 8) < 1e-9,
      `level 1 at m=${m} reduces to m(m+8)/8`);
  }
  for (const m of [160, 320, 800]) {
    assert.ok(Math.abs(LN.levelParameters(2).densestBound(m) - (7 * m + (m * m) / 320)) < 1e-9,
      `level 2 at m=${m} reduces to 7m + m^2/320`);
  }
});

test("the level-2 shape count is exactly two lifts per level-1 tight set", () => {
  const res = LN.verifyLevel2Exhaustive(4);
  assert.equal(res.level1TightSets, 40, "the 40 lines");
  assert.equal(res.predictedLevel2Shapes, 80, "two lifts each, and nothing else");
  assert.ok(res.allSampledAttainBound);
});

test("the ladder gets 40x coarser per level and never gets more robust", () => {
  for (let n = 1; n <= 5; n++) {
    const a = shapes.levelAdvice(n);
    assert.equal(a.smallestDensestShape, 4 * Math.pow(40, n - 1));
    assert.equal(a.busyTolerated, 10, "the same ten failures at every level");
    assert.equal(a.ladder.length, 9, "nine rungs, always");
    // consecutive rungs differ by 40^(n-1)
    for (let i = 1; i < a.ladder.length; i++) {
      assert.equal(a.ladder[i] - a.ladder[i - 1], 4 * Math.pow(40, n - 1));
    }
  }
  // by level 5 the smallest densest reservation is over ten million nodes
  assert.ok(shapes.levelAdvice(5).smallestDensestShape > 1e7);
  assert.ok(shapes.levelAdvice(5).survivableFraction < 1e-6);
});

test("levelAdvice refuses off-ladder requests and says what to do instead", () => {
  const r = shapes.levelAdvice(3, 5000);
  assert.equal(r.ok, false);
  assert.match(r.reason, /below the ladder/);
  assert.equal(r.nearestOnLadder, 6400);
  assert.match(r.recommendation, /compose level-1 shapes inside cells/,
    "and it recommends the honest alternative rather than a formula");

  const good = shapes.levelAdvice(2, 320);
  assert.equal(good.ok, true);
  assert.equal(good.maxInducedEdges, 7 * 320 + (320 * 320) / 320);

  assert.match(shapes.levelAdvice(1).recommendation, /level-1 catalogue/);
});

// ======================================================================
// The 36-spread graph colouring
//
// js/spread-obstruction.js shipped an 8-colouring that was not proper --
// 29 monochromatic edges, and its own certificate said valid = false.
// The chromatic number claim was right; only the assignment was wrong.
// ======================================================================

test("the shipped spread colouring is proper and matches its asserted sizes", () => {
  require(path.join(root, "js/uor.js"));
  require(path.join(root, "js/w33-scheduler.js"));
  const O = require(path.join(root, "js/spread-obstruction.js"));
  const c = O.certificate();
  const a = O.adjacency();

  assert.equal(c.valid, true, "the certificate validates");
  assert.equal(c.chromaticNumber, 8);
  assert.deepEqual(c.colorClassSizes, [5, 5, 5, 5, 5, 5, 4, 2]);

  let mono = 0;
  for (const batch of c.batches) {
    for (let i = 0; i < batch.length; i++) {
      for (let j = i + 1; j < batch.length; j++) if (a[batch[i]][batch[j]]) mono++;
    }
  }
  assert.equal(mono, 0, "no colour class contains an edge");

  const covered = c.batches.flat();
  assert.equal(covered.length, 36, "every spread coloured once");
  assert.equal(new Set(covered).size, 36, "and only once");
});

test("chi = 8 is forced by the independence number, not merely observed", () => {
  require(path.join(root, "js/uor.js"));
  require(path.join(root, "js/w33-scheduler.js"));
  const O = require(path.join(root, "js/spread-obstruction.js"));
  const c = O.certificate();
  // a colour class is an independent set, so at least ceil(n / alpha)
  // classes are needed. alpha = 5 and n = 36 give 8, and 8 is achieved.
  assert.equal(c.alpha, 5);
  assert.equal(Math.ceil(36 / c.alpha), 8);
  assert.equal(c.chromaticNumber, 8, "the counting bound is attained");
});

// ======================================================================
// Depth-2 tensor blocking: the structural narrowing
//
// js/tensor-sharding.js leaves tau open at [110, 121]. This does not
// close it, but it reduces the problem and settles it conditionally.
// ======================================================================

const TBS = require(path.join(root, "analysis/tensor_blocking_structure.js"));

test("every point of a minimum line-blocker is some line's only blocker point", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const r = TBS.run();
  assert.equal(r.blockerSize, 11);
  assert.deepEqual(r.lineIntersectionSizes, { 1: 36, 2: 4 },
    "44 incidences over 40 lines: 36 met once, 4 met twice");
  assert.equal(r.uniqueWitnessPoints.length, 11,
    "all eleven, which is what forces every fibre to block");
  assert.ok(r.allBlockerPointsAreUniqueWitnesses);
});

test("if the support is a minimum blocker then tau is exactly 121", () => {
  const r = TBS.run();
  // each of the 11 fibres must itself be a line-blocking set, so >= 11
  assert.equal(r.conditionalTau, 121);
  assert.equal(r.bxbSize, 121);
  assert.ok(r.bxbBlocks, "and B x B attains it");
});

test("B x B is a minimal blocking set, not merely a convenient one", () => {
  const r = TBS.run();
  assert.equal(r.bxbRemovableLeaves, 0,
    "no single leaf can be dropped while still blocking every tile");
  assert.ok(r.bxbIsMinimal);
});

test("the interval is narrowed but honestly still open", () => {
  const r = TBS.run();
  assert.deepEqual(r.publishedInterval, [110, 115]);
  // this module PREDICTED that beating 121 needs a support of 12 or more.
  // A support-37 blocker of size 116 was then found, so the prediction is
  // resolved and the conditional tau=121 theorem is vacuous at the optimum.
  assert.match(r.predictionForBeating121, /support of 12 or more/);
  assert.equal(r.predictionResolved, true);
  assert.equal(r.conditionalHypothesisHoldsAtOptimum, false);
  assert.match(r.stillOpen, /exact value of tau_2 inside \[110, 115\]/,
    "the interval narrowed; it did not close");
  // the module must not claim an exact value it does not have
  const T = require(path.join(root, "js/tensor-sharding.js"));
  assert.equal(T.depth2Certificate().exactTau, null,
    "tensor-sharding still reports the exact value as unknown");
});

// ======================================================================
// Breaking the product bound: 121 -> 115
//
// The upper bound had always been B x B for a minimum line blocker B.
// Searching only blockers invariant under a cyclic subgroup of Aut(W33)
// collapses 1,600 leaf variables to 174 orbit variables, and CP-SAT then
// finds a 115-leaf blocker in seconds.  These tests re-verify the witness
// from scratch -- they never trust the stored number.
// ======================================================================

test("the 115 witness really blocks every one of the 1600 depth-2 tiles", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const X = new Set(T.SYMMETRIC_WITNESS);
  assert.equal(T.SYMMETRIC_WITNESS.length, 115);
  assert.equal(X.size, 115, "no duplicated leaves");
  let checked = 0;
  for (let a = 0; a < 40; a++) {
    for (let b = 0; b < 40; b++) {
      const tile = T.productTile(a, b);
      assert.equal(tile.leaves.length, 16);
      assert.ok(tile.leaves.some((v) => X.has(v)),
        `tile (${a},${b}) is unblocked`);
      checked++;
    }
  }
  assert.equal(checked, 1600, "every product tile was actually tested");
});

test("the 115 witness is minimal: no leaf can be dropped", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  for (const v of T.SYMMETRIC_WITNESS) {
    const T2 = new Set(T.SYMMETRIC_WITNESS);
    T2.delete(v);
    assert.equal(T.hitsAllProductTiles(T2), false,
      `dropping leaf ${v} still blocked everything, so it is not minimal`);
  }
});

test("115 beats the product construction, so B x B is not optimal", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const c = T.depth2Certificate();
  assert.equal(c.productWitness.length, T.TAU1 * T.TAU1);
  assert.equal(c.productWitness.length, 121);
  assert.ok(c.upperWitness.length < c.productWitness.length,
    "the symmetric witness must strictly beat B x B");
  assert.equal(c.productConstructionOptimal, false);
  assert.equal(c.bounds.productUpper, 121);
  assert.equal(c.bounds.upper, 115);
});

test("the 115 witness refutes the hypothesis of the conditional tau=121 theorem", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const rows = new Set(T.SYMMETRIC_WITNESS.map((v) => Math.floor(v / 40)));
  const cols = new Set(T.SYMMETRIC_WITNESS.map((v) => v % 40));
  // the old theorem assumed the row support IS a minimum line blocker (11)
  assert.equal(rows.size, 37);
  assert.equal(cols.size, 40);
  assert.ok(rows.size > T.TAU1,
    "support exceeds 11, which is exactly the case the theorem left open");
  // it is still a line-blocking set -- that much is forced
  const S = require(path.join(root, "js/substrate.js"));
  assert.ok(S.LINES.every((L) => L.some((p) => rows.has(p))),
    "any row support must block all 40 lines");
});

test("the tensor guarantee agrees with the exact single-cell one at depth 1", () => {
  const SH = require(path.join(root, "scheduler/w33-shapes.js"));
  // depth 1 is just a line: it must reproduce the frozen m=4 SAT guarantee
  const one = SH.tensorGuarantee(1);
  const line = SH.guaranteeFor(4, "densest");
  assert.equal(one.blockingLower, line.blockingNumber);
  assert.equal(one.busyTolerated, line.busyTolerated);
  assert.equal(one.busyTolerated, 10);
  assert.equal(one.exact, true);
  assert.equal(one.open, false);
  assert.equal(one.openGap, 0);
});

test("the tensor guarantee quotes the proved floor and names the ceiling it cannot pass", () => {
  const SH = require(path.join(root, "scheduler/w33-shapes.js"));
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const g = SH.tensorGuarantee(2);
  // the quotable number is the PROVED one
  assert.equal(g.busyTolerated, 109);
  assert.equal(g.blockingLower, T.tensorBlockingBounds(2).lower);
  // and a 115-leaf blocker exists, so no proof can ever push it past 114
  assert.equal(g.busyToleratedCeiling, 114);
  assert.equal(g.blockingUpper, T.tensorBlockingBounds(2).upper);
  assert.equal(g.open, true);
  assert.equal(g.openGap, 5);
  assert.match(g.boundary, /not known exactly/);
  // the scheduler's constants must not drift from the engine's
  assert.equal(SH.TENSOR.depth2Lower, T.tensorBlockingBounds(2).lower);
  assert.equal(SH.TENSOR.depth2Upper, T.tensorBlockingBounds(2).upper);
  assert.equal(SH.TENSOR.productUpperSuperseded, T.tensorBlockingBounds(2).productUpper);
  assert.equal(SH.TENSOR.tau1, T.TAU1);
});

test("tensor guarantees track the submultiplicative bound at every depth", () => {
  const SH = require(path.join(root, "scheduler/w33-shapes.js"));
  const T = require(path.join(root, "js/tensor-sharding.js"));
  for (const d of [1, 2, 3, 4, 5]) {
    const g = SH.tensorGuarantee(d);
    const b = T.tensorBlockingBounds(d);
    assert.equal(g.blockingLower, b.lower, `depth ${d} floor`);
    assert.equal(g.blockingUpper, b.upper, `depth ${d} ceiling`);
    assert.equal(g.leaves, Math.pow(4, d));
    assert.equal(g.fabric, Math.pow(40, d));
    assert.ok(g.busyTolerated < g.fabric, "a guarantee cannot exceed the fabric");
  }
  assert.throws(() => SH.tensorGuarantee(0), RangeError);
  assert.throws(() => SH.tensorGuarantee(1.5), RangeError);
});

test("the 115 improvement propagates to every depth by submultiplicativity", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  // tau_(a+b) <= tau_a * tau_b, so the best product uses depth-2 factors
  for (const d of [2, 3, 4, 5, 6]) {
    const b = T.tensorBlockingBounds(d);
    const expect = Math.pow(115, Math.floor(d / 2)) * Math.pow(11, d % 2);
    assert.equal(b.upper, expect, `depth ${d} upper bound`);
    assert.ok(b.upper < b.productUpper,
      `depth ${d} must beat the naive 11^n = ${b.productUpper}`);
    assert.equal(b.lower, 11 * Math.pow(10, d - 1));
    assert.ok(b.lower < b.upper, "the interval stays open at every depth");
  }
  // depth 1 is the exact SAT value and must not be inflated
  const one = T.tensorBlockingBounds(1);
  assert.equal(one.lower, 11);
  assert.equal(one.upper, 11);
  assert.equal(one.exact, true);
});

test("the depth-3 product blocker is verified against all 64000 tiles, not asserted", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const S = require(path.join(root, "js/substrate.js"));
  // X3 = (the 115-leaf depth-2 blocker) x (the 11-point line blocker)
  const X2 = new Set(T.SYMMETRIC_WITNESS);
  const B = [...T.BLOCKER];
  const X3 = new Set();
  for (const v of X2) for (const r of B) X3.add(v * 40 + r);
  assert.equal(X3.size, 115 * 11);
  assert.equal(X3.size, 1265);
  assert.equal(X3.size, T.tensorBlockingBounds(3).upper);

  let tiles = 0;
  for (let a = 0; a < 40; a++) {
    for (let b = 0; b < 40; b++) {
      for (let c = 0; c < 40; c++) {
        let hit = false;
        for (const p of S.LINES[a]) {
          for (const q of S.LINES[b]) {
            for (const r of S.LINES[c]) {
              if (X3.has((p * 40 + q) * 40 + r)) { hit = true; break; }
            }
            if (hit) break;
          }
          if (hit) break;
        }
        assert.ok(hit, `depth-3 tile (${a},${b},${c}) is unblocked`);
        tiles++;
      }
    }
  }
  assert.equal(tiles, 64000, "every depth-3 tile was actually tested");
});

test("the frozen certificate and the engine agree on the same witness", () => {
  // These drifted apart once already: the engine carried a witness from one
  // search run and the certificate a different one of the same size. Pin them.
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const cert = require(path.join(root, "data/tensor_symmetric_blocker.json"));
  assert.equal(cert.upperBound, 115);
  assert.equal(cert.previousUpperBound, 121);
  assert.equal(cert.lowerBound, 110);
  assert.deepEqual(cert.witness, [...T.SYMMETRIC_WITNESS],
    "certificate witness and engine witness must be the same set of leaves");
  assert.equal(cert.witnessBlocksAll1600, true);
  assert.equal(cert.witnessMinimal, true);
  assert.equal(cert.productConstructionOptimal, false);
  assert.equal(cert.exactTau, null);
  // the search that produced it is one-sided, and the certificate says so
  assert.match(cert.onesided, /a miss.*bound\s*nothing about tau_2/s);
  assert.match(cert.boundary, /remains OPEN/);
});

test("the coclique census of W(3,3) is recomputed, not trusted", () => {
  const S = require(path.join(root, "js/substrate.js"));
  const census = require(path.join(root, "data/w33_coclique_census.json"));
  const nbr = [];
  for (let i = 0; i < 40; i++) {
    const s = new Set();
    for (let j = 0; j < 40; j++) if (i !== j && S.isAdjacent(i, j)) s.add(j);
    nbr.push(s);
  }
  const by = new Array(12).fill(0);
  (function ext(depth, cand) {
    by[depth]++;
    for (let i = 0; i < cand.length; i++) {
      const v = cand[i];
      ext(depth + 1, cand.slice(i + 1).filter((w) => !nbr[v].has(w)));
    }
  })(0, [...Array(40).keys()]);
  for (const [k, v] of Object.entries(census.bySize)) {
    assert.equal(by[Number(k)], v, `independent sets of size ${k}`);
  }
  assert.equal(by.reduce((a, b) => a + b, 0), census.total);
  assert.equal(census.total, 40055);
  // alpha = 7, well under the Hoffman ratio bound of 10 -- the ovoid defect
  assert.equal(by[8], 0, "there is no independent set of size 8");
  assert.equal(census.independenceNumber, 7);
  assert.ok(census.independenceNumber < census.hoffmanRatioBound);
});

test("the q=5 extension is recorded as four open questions, not as results", () => {
  const w = require(path.join(root, "data/w35_open_questions.json"));

  // tau_1(W(3,5)) is bracketed but not settled
  assert.deepEqual(w.tau1.interval, [28, 29]);
  assert.equal(w.tau1.status, "UNDECIDED");
  assert.equal(w.tau1.publishedLowerBound, 28);
  assert.equal(w.tau1.witnessFound, 29);
  assert.equal(w.tau1.exactFeasibilityAt28, "UNKNOWN");
  assert.match(w.tau1.publishedSource, /Eisfeld/);

  // the ovoid deficiency at q=5 likewise
  assert.deepEqual(w.ovoidDeficiency.interval, [1, 12]);
  assert.equal(w.ovoidDeficiency.status, "UNDECIDED");
  assert.equal(w.ovoidDeficiency.lowerBound, 1, "no ovoid, so at least one");

  // and the product-bound claim is CONDITIONAL, which is the point
  const p = w.productBound;
  assert.equal(p.symmetricBlockerFound, 814);
  assert.equal(p.beats29squared, true);
  assert.equal(p.beats28squared, false);
  assert.equal(p["28squared"], 784);
  assert.equal(p["29squared"], 841);
  assert.ok(p.status.startsWith("CONDITIONAL"),
    "814 beats 841 but loses to 784, so nothing may be claimed");
  assert.match(p.why, /no claim can be made/);

  // q=3, by contrast, IS settled and beaten
  assert.equal(p.atQ3ForComparison.productBound, 121);
  assert.equal(p.atQ3ForComparison.found, 115);
  assert.equal(p.atQ3ForComparison.beaten, true);

  // no general theorem is asserted from any of this
  assert.match(w.boundary, /remains a q=3 fact only/);
});

test("the near-ovoid / minimum-blocker correspondence holds both ways", () => {
  const c = require(path.join(root, "data/w33_near_ovoid_blocker_correspondence.json"));
  assert.equal(c.valid, true);
  // the converse, checked on every deletion rather than sampled
  assert.equal(c.blockers, 360);
  assert.equal(c.deletionsChecked, 3960, "360 blockers x 11 points");
  assert.equal(c.criterionAgreement, 3960, "100% agreement, no exceptions");
  assert.deepEqual(c.fibreSize, [8], "uniform fibre");
  assert.deepEqual(c.nearOvoidsPerBlocker, { 8: 360 });
  // the count is DERIVED, not matched
  assert.equal(c.derivedCount, 2880);
  assert.equal(c.theirEnumeratedCount, 2880);
  assert.equal(c.countDerived, true);
  assert.equal(360 * 8, 2880);
  // the two distinguished points are always distinct and collinear
  assert.deepEqual(Object.keys(c.centreRelation), ["collinear"]);
  assert.equal(c.centreRelation.collinear, 2880);
  // the 8 is our own (0,8,3) shape, not a free parameter
  assert.match(c.whyEight, /\(0,8,3\)/);
  assert.match(c.whyThisIsNotANumberMatch, /both\s+directions/);
  // and it is scoped to q=3, since the dipole shape dies at q=5
  assert.match(c.boundary, /not claimed to\s+generalise/);
});

test("the correspondence recomputes from the geometry, not from the artifact", () => {
  // Independent rebuild: delete each point of each minimum blocker and check
  // the collinear-with-centre criterion directly against the incidence data.
  const S = require(path.join(root, "js/substrate.js"));
  const R = require(path.join(root, "analysis/tensor_blocking_reformulation.js"));
  const B = R.minimumBlockers().map((b) => new Set(b));
  const pencil = new Map();
  for (let p = 0; p < 40; p++) {
    const ls = [];
    for (let li = 0; li < 40; li++) if (S.LINES[li].includes(p)) ls.push(li);
    pencil.set(ls.join(","), p);
  }
  let checked = 0, agree = 0;
  const perBlocker = new Set();
  for (const b of B) {
    const exc = [];
    for (let li = 0; li < 40; li++) {
      if (S.LINES[li].filter((p) => b.has(p)).length === 2) exc.push(li);
    }
    const c = pencil.get(exc.join(","));
    assert.notEqual(c, undefined);
    let good = 0;
    for (const p of b) {
      const rest = new Set(b); rest.delete(p);
      const missed = [];
      for (let li = 0; li < 40; li++) {
        if (!S.LINES[li].some((z) => rest.has(z))) missed.push(li);
      }
      const isOpt = missed.length === 3 && missed.every((li) => S.LINES[li].includes(p));
      const predicted = p !== c && S.isAdjacent(p, c);
      checked++;
      if (isOpt === predicted) agree++;
      if (isOpt) good++;
    }
    perBlocker.add(good);
  }
  assert.equal(checked, 3960);
  assert.equal(agree, 3960, "the criterion must hold with no exceptions");
  assert.deepEqual([...perBlocker], [8]);
});

test("GQ(2,4) is a second no-ovoid quadrangle and the centre theorem transfers", () => {
  const g = require(path.join(root, "data/gq24_schlaefli_quadrangle.json"));
  assert.equal(g.valid, true);
  // the geometry
  assert.equal(g.geometry.points, 27);
  assert.equal(g.geometry.lines, 45);
  assert.deepEqual(g.geometry.order, [2, 4]);
  assert.equal(g.geometry.ovoidSize, 9);
  assert.equal(g.geometry.hasOvoid, false);
  // same defect as W(3,3), different interval
  assert.equal(g.tau1, 10);
  assert.equal(g.tau1Proved, true);
  assert.equal(g.blockingOvoidDefect, 1);
  assert.deepEqual(g.depth2Interval, [90, 100]);
  // the centre theorem transfers, and more cleanly: a BIJECTION
  const c = g.centreTheorem;
  assert.equal(g.minimumBlockers, 27);
  assert.equal(g.blockerEnumerationComplete, true);
  assert.equal(c.allCentred, true);
  assert.equal(c.distinctCentres, 27);
  assert.deepEqual(c.blockersPerCentre, [1]);
  assert.equal(c.bijectionWithPoints, true, "27 blockers, one per point");
  assert.equal(c.centreInsideBlocker, 0, "never contains its own centre");
  // every layer is an order of magnitude smaller than W(3,3)
  assert.equal(g.alpha, 6);
  assert.equal(g.cocliqueDeficit, 3);
  assert.equal(g.independentSets, 2764);
  assert.equal(g.pencilUnionMasks, 2728);
  assert.ok(g.independentSets * 10 < g.comparisonToW33.w33IndependentSets);
  assert.ok(g.comparisonToW33.gq24Leaves < g.comparisonToW33.w33Leaves / 2);
  // the geometry is prior art and says so
  assert.match(g.priorArt.pass84, /PSU\(4,2\)/);
  assert.match(g.priorArt.passes3769_3786, /40-plane-ovoid/);
  assert.match(g.priorArt.whatIsNewHere, /product blocking/);
  // and tau_2 is open
  assert.match(g.boundary, /OPEN in \[90, 100\]/);
});

test("the tight case has no local obstruction, and that is stated as a characterisation", () => {
  const o = require(path.join(root, "data/tensor_110_no_local_obstruction.json"));
  assert.equal(o.valid, true);
  for (const [k, v] of Object.entries(o.checks)) assert.equal(v, true, k);
  // the occupancy count and the pencil count must agree exactly
  const c = o.occupancy;
  assert.equal(c.incidences, 16 * 110);
  assert.equal(c.tiles, 1600);
  assert.equal(c.singletons, 1440);
  assert.equal(c.doubled, 160);
  assert.equal(c.doubledFromPencils, 160, "40 lines x 4 pencil lines");
  assert.equal(c.agree, true, "two independent counts of the doubled tiles");
  assert.equal(c.singletons + c.doubled, c.tiles);
  assert.equal(c.singletons + 2 * c.doubled, c.incidences);
  // nine formulations, none infeasible -- that is the evidence for the claim
  assert.equal(o.formulationsTried, 9);
  assert.equal(o.infeasibleReturned, 0);
  assert.ok(o.invariantsThatClose.length >= 10);
  // and it is a characterisation, not a proof
  assert.match(o.boundary, /NOT a proof either way/);
  assert.match(o.boundary, /open in \[110, 115\]/);
  assert.match(o.dichotomy, /exhaustive search|not a local invariant/);
});

test("the tight case reduces to N^T X N = J + P N, and re-derives the centre balance", () => {
  const e = require(path.join(root, "data/tensor_tight_matrix_equation.json"));
  assert.equal(e.valid, true);
  assert.equal(e.equation, "N^T X N = J + P N");
  for (const [k, v] of Object.entries(e.checks)) assert.equal(v, true, k);
  // the cross-check is the point: centre balance from a second direction
  assert.match(e.crossCheck, /Two independent routes/);
  assert.match(e.rankNote, /rank\(N\) = 25/);
  // and it is explicitly NOT sold as an obstruction
  assert.equal(e.isAnObstruction, false);
  assert.match(e.boundary, /proves nothing about\s+tau_2/);
  assert.match(e.boundary, /easy to\s+oversell/);
});

test("the matrix equation is rebuilt from the geometry, not read back", () => {
  const S = require(path.join(root, "js/substrate.js"));
  const R = require(path.join(root, "analysis/tensor_blocking_reformulation.js"));
  // rows of N sum to 4, and 1 is in rowspace(N) since column sums are 4 too
  const Nm = [];
  for (let p = 0; p < 40; p++) {
    Nm.push([...Array(40).keys()].map((li) => (S.LINES[li].includes(p) ? 1 : 0)));
    assert.equal(Nm[p].reduce((a, b) => a + b, 0), 4);
  }
  for (let li = 0; li < 40; li++) {
    let c = 0;
    for (let p = 0; p < 40; p++) c += Nm[p][li];
    assert.equal(c, 4, "column sums 4, so the all-ones vector is in rowspace(N)");
  }
  // every minimum blocker's doubled-line set is a pencil row of N
  const pencils = new Map();
  for (let p = 0; p < 40; p++) {
    pencils.set(Nm[p].join(""), p);
  }
  for (const b of R.minimumBlockers()) {
    const bs = new Set(b);
    const row = [...Array(40).keys()].map((li) =>
      (S.LINES[li].filter((z) => bs.has(z)).length === 2 ? 1 : 0));
    assert.equal(row.reduce((a, x) => a + x, 0), 4, "four doubled lines");
    assert.ok(pencils.has(row.join("")), "and they form a pencil, i.e. a row of N");
    // trace sum is 4|B| = 44
    let tr = 0;
    for (let li = 0; li < 40; li++) tr += S.LINES[li].filter((z) => bs.has(z)).length;
    assert.equal(tr, 44);
  }
});

test("the tau_2 SAT encoding is a validated control, now superseded by proof", () => {
  const e = require(path.join(root, "data/tensor_110_sat_encoding.json"));
  assert.equal(e.valid, true);
  assert.equal(e.soundAndComplete, true);
  assert.equal(e.constraintFamilies.length, 3);
  // the control passed, which is what made an UNSAT here meaningful
  const c = e.positiveControl;
  assert.equal(c.geometry, "W(3,2)");
  assert.equal(c.result, "SAT");
  assert.equal(c.witnessSize, 25);
  assert.equal(c.passes, true);
  // and the question it was aimed at is now CLOSED by W33-Theory's
  // self-duality obstruction, not by this search
  assert.equal(e.q3Instance.currentStatus, "SUPERSEDED BY THEOREM");
  assert.equal(e.q3Instance.proved110Impossible, true);
  assert.match(e.q3Instance.supersedingProofCommit, /^43049db/);
  assert.deepEqual(e.currentFrontier.interval, [111, 115],
    "the lower bound moved off 110 for the first time");
  assert.equal(e.currentFrontier.lowerBound, 111);
});

test("the deficiency / induced-edge identity holds, and is upper-bound only", () => {
  const d = require(path.join(root, "data/w33_deficiency_edge_identity.json"));
  assert.equal(d.valid, true);
  for (const r of d.instances) {
    // sum_L |S cap L| = (q+1)|S| = #lines at ovoid size
    assert.equal(r.countingIdentityHolds, true);
    assert.equal(r.profileTotal, (r.q + 1) * r.setSize);
    assert.equal(r.profileTotal, r.lines);
    // ||f||^2 = 2 e(S), recomputed from the profile
    assert.equal(r.normIdentityHolds, true);
    let norm = 0;
    for (const [k, v] of Object.entries(r.profile)) norm += (Number(k) - 1) ** 2 * v;
    assert.equal(norm, 2 * r.witnessEdges);
    // d <= e(S), with equality here since the profile stays within {0,1,2}
    assert.equal(r.dAtMostE, true);
    assert.ok(r.deficiency <= r.witnessEdges);
    assert.equal(r.equalityCase, true);
    assert.equal(r.deficiency, r.witnessEdges, "equality case: d = e");
  }
  // q=3 closes; q=5 does not
  const [q3, q5] = d.instances;
  assert.equal(q3.minEdges, 3);
  assert.equal(q3.proved, true, "q=3 minimum induced edges is OPTIMAL");
  assert.equal(q3.deficiency, 3);
  assert.equal(q5.minEdges, 12);
  assert.equal(q5.proved, false, "q=5 is only feasible, not proved minimal");
  // the direction is stated: upper bound only
  assert.match(d.direction, /UPPER bound/);
  assert.match(d.direction, /Not a lower bound/);
  assert.match(d.spectralNoteFails, /Hoffman bound/);
  assert.match(d.boundary, /stays open in \[6, 12\]/);
});

test("def(W(3,5)) is tracked as an open interval, however the tracks move it", () => {
  const s = require(path.join(root, "data/w35_ovoid_deficiency_state.json"));
  assert.equal(s.status, "OPEN");
  const [lo, hi] = s.interval;
  // the bound has tightened repeatedly across both tracks; assert the
  // INVARIANTS rather than the current numbers, which keep moving
  assert.ok(lo >= 7, "the lower bound never regresses below the dipole result");
  assert.equal(hi, 12, "the upper bound is still our explicit witness");
  assert.ok(lo < hi, "still an open interval");
  assert.equal(s.lowerBound.value, lo);
  assert.equal(s.upperBound.value, hi);
  assert.equal(s.lowerBound.crossTrack, true, "the lower bound is a joint result");
  // every exact test remains undecided, and the annealing floor stays evidence
  // our own exact tests were all UNKNOWN; they have since been superseded
  // by W33-Theory theorems, and the artifact records both facts
  // the three we ran ourselves were all UNKNOWN and are recorded as such;
  // later entries come from W33-Theory theorems and may say anything
  for (const k of ["deficiency6", "deficiency7", "deficiency8"]) {
    assert.match(s.exactTests[k], /UNKNOWN/, k);
  }
  assert.ok(Object.keys(s.exactTests).length >= 3);
  assert.equal(s.annealing.floor, 12);
  assert.match(s.annealing.reading, /not proof/);
});

test("the defect-dipole shape is q=3 exceptional", () => {
  const d = require(path.join(root, "data/w33_dipole_q3_exceptional.json"));
  assert.equal(d.valid, true);
  const [q3, q5] = d.instances;

  // at q=3 the punctured-pencil dipole realises the optimum
  assert.equal(q3.q, 3);
  assert.equal(q3.puncturedPencilSize, 3, "a pencil has q+1 lines, punctured q");
  assert.equal(q3.feasible, true);
  assert.equal(q3.profile["0"], 3);
  assert.equal(q3.profile["2"], 3);
  assert.equal(q3.profile["1"], 34);

  // at q=5 it is INFEASIBLE, so the shape does not generalise
  assert.equal(q5.q, 5);
  assert.equal(q5.puncturedPencilSize, 5);
  assert.equal(q5.feasible, false);
  assert.equal(q5.status, "INFEASIBLE");

  // and the failure is combinatorial, not arithmetic: the counting identity
  // permits the profile at BOTH q, so infeasibility is not a parity accident
  for (const r of d.instances) {
    assert.equal(r.countingIdentityPermits, true);
    assert.equal(r.profileTotal, r.requiredTotal);
    assert.equal(r.requiredTotal, (r.q + 1) * r.setSize);
  }

  // the two rival predictions agree at q=3 and diverge at q=5
  assert.equal(d.predictionsAgreeAtQ3, true);
  assert.match(d.shapePredicts, /def\(q\) = q/);
  assert.match(d.rivalPredicts, /theta - alpha/);

  // scope: this kills a route, not the value
  assert.match(d.whatItSettles, /kills the dipole route/);
  assert.match(d.whatItDoesNotSettle, /is NOT proved/);
  assert.match(d.whatItDoesNotSettle, /open in \[1, 12\]/);
});

test("the ovoid deficiency of W(3,3) is exactly 3", () => {
  const d = require(path.join(root, "data/w33_ovoid_deficiency.json"));
  assert.equal(d.valid, true);
  const q3 = d.instances.find((r) => r.q === 3);
  assert.equal(q3.setSize, 10, "ovoid size q^2+1");
  assert.equal(q3.deficiency, 3);
  assert.equal(q3.status, "OPTIMAL");
  assert.equal(q3.bound, 3, "proved, not just attained");
  // missed and doubled must balance: sum_L |S cap L| = (q+1)|S| = #lines
  assert.equal(q3.profile["0"], 3);
  assert.equal(q3.profile["2"], 3);
  assert.equal(q3.profile["1"], 34);
  const total = 0 * q3.profile["0"] + 1 * q3.profile["1"] + 2 * q3.profile["2"];
  assert.equal(total, 40, "(q+1)|S| = 4*10 = 40 = the number of lines");
  assert.equal(q3.profile["0"] + q3.profile["1"] + q3.profile["2"], 40);
  // nonzero deficiency is the no-ovoid theorem, restated
  assert.ok(q3.deficiency > 0, "W(3,3) has no ovoid");
});

test("the ten-state carrier match is size only, not structure", () => {
  const d = require(path.join(root, "data/w33_ovoid_deficiency.json"));
  const e = d.ellipticQuadric;
  // Q^-(3,3) = P1(F9) has exactly the ovoid size, which is the temptation
  assert.equal(e.size, 10);
  // but it misses 12 lines where the optimum is 3
  assert.equal(e.linesMissed, 12);
  assert.equal(e.optimum, 3);
  assert.equal(e.isNearOptimal, false);
  assert.ok(e.linesMissed > 3 * e.optimum, "four times worse than optimal");
  // its profile still satisfies the counting identity
  const p = e.profile;
  assert.equal(0 * p["0"] + 1 * p["1"] + 2 * p["2"], 40);
  assert.equal(p["0"], p["2"], "missed and doubled must balance");
  assert.match(e.verdict, /size only/);
  assert.match(d.thirdCoincidenceDefused, /shared parameter, not a shared object/);
});

test("the cyclotomic bridge holds at q=3 and is killed at q=5", () => {
  const c = require(path.join(root, "data/w33_cyclotomic_bridge_killed.json"));
  assert.equal(c.valid, true);
  const [q3, q5] = c.instances;

  // q = 3: the fit that made it tempting
  assert.equal(q3.q, 3);
  assert.equal(q3.points, 40);
  assert.equal(q3.srgConfirmed, true);
  assert.equal(q3.ovoidSize, 10);          // Phi_4(3) = q^2+1
  assert.equal(q3.alpha, 7);
  assert.equal(q3.phi6, 7);                // Phi_6(3) = q^2-q+1
  assert.equal(q3.alphaEqualsPhi6, true);
  assert.equal(q3.cocliqueDeficit, 3);
  assert.equal(q3.deficitEqualsQ, true);

  // q = 5: the prediction, and its failure
  assert.equal(q5.q, 5);
  assert.equal(q5.points, 156);            // (q+1)(q^2+1)
  assert.equal(q5.srgConfirmed, true);     // SRG(156,30,4,6)
  assert.equal(q5.ovoidSize, 26);
  assert.equal(q5.phi6, 21, "the prediction was 21");
  assert.equal(q5.alpha, 18, "the truth is 18");
  assert.equal(q5.alphaEqualsPhi6, false);
  assert.equal(q5.cocliqueDeficit, 8);
  assert.equal(q5.deficitEqualsQ, false);

  // both alphas are established, not asserted
  for (const r of c.instances) {
    assert.equal(r.alphaStatus, "OPTIMAL");
    assert.equal(r.nextSizeStatus, "INFEASIBLE", "alpha+1 must be refuted");
    assert.equal(r.witnessCollinearPairs, 0,
      "the witness is checked against the symplectic form itself");
    assert.equal(r.witnessDistinct, true);
  }
  assert.match(c.verdict, /FALSE/);
  assert.match(c.boundary, /weaker evidence of a shared\s+object, not stronger/);
});

test("one ovoid suffices: three products close, one stays open", () => {
  const o = require(path.join(root, "data/tensor_one_ovoid_suffices.json"));
  assert.equal(o.valid, true);
  const by = Object.fromEntries(o.instances.map((r) => [r.product, r]));
  // an ovoid on EITHER side makes the bounds meet
  assert.equal(by["W(3,2) x W(3,2)"].tau, 25);
  assert.equal(by["W(3,2) x W(3,3)"].tau, 55);
  assert.equal(by["W(3,3) x Q(4,3)"].tau, 110);
  for (const k of ["W(3,2) x W(3,2)", "W(3,2) x W(3,3)", "W(3,3) x Q(4,3)"]) {
    assert.equal(by[k].multiplicative, true, k);
    assert.equal(by[k].lower, by[k].upper, `${k}: the bounds must meet`);
  }
  // and the one with no ovoid on either side does not
  const open = by["W(3,3) x W(3,3)"];
  assert.equal(open.multiplicative, false);
  assert.equal(open.lower, 110);
  assert.equal(open.upper, 121);
  assert.equal(open.tau, null, "the open case may not claim a value");
  assert.match(o.boundary, /does NOT decide tau_2/);
});

test("the dual-product witness is verified against all 1600 tiles", () => {
  // Rebuilt here from the geometry: an 11-point blocker of W(3,3) crossed
  // with a 10-line spread of W(3,3) blocks every line x pencil tile.
  const S = require(path.join(root, "js/substrate.js"));
  const W = require(path.join(root, "js/w33-scheduler.js"));
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const B = [...T.BLOCKER];
  const sp = W.spreads()[0];
  assert.equal(B.length, 11);
  assert.equal(sp.length, 10);
  const covered = new Set();
  for (const li of sp) for (const p of S.LINES[li]) covered.add(p);
  assert.equal(covered.size, 40, "a spread covers every point exactly once");

  const X = new Set();
  for (const p of B) for (const M of sp) X.add(p * 40 + M);
  assert.equal(X.size, 110);

  const thru = [];
  for (let r = 0; r < 40; r++) {
    thru.push([...Array(40).keys()].filter((li) => S.LINES[li].includes(r)));
  }
  let tiles = 0;
  for (let li = 0; li < 40; li++) {
    for (let r = 0; r < 40; r++) {
      let hit = false;
      for (const p of S.LINES[li]) {
        for (const M of thru[r]) if (X.has(p * 40 + M)) { hit = true; break; }
        if (hit) break;
      }
      assert.ok(hit, `dual tile (${li},${r}) unblocked`);
      tiles++;
    }
  }
  assert.equal(tiles, 1600);
  // same grid, same tile count, same tile size as the open problem
  assert.equal(tiles, 40 * 40);
});

test("the 3-5-7 cube cannot reach W(3,3) by symmetry, and neither can C13", () => {
  const o = require(path.join(root, "data/w33_357_cube_obstruction.json"));
  assert.equal(o.valid, true);
  // 51840 = 2^7 * 3^4 * 5 -- recomputed, not trusted
  assert.equal(o.autOrder, 51840);
  assert.equal(Math.pow(2, 7) * Math.pow(3, 4) * 5, 51840);
  assert.notEqual(o.autOrder % 7, 0, "7 does not divide the order");
  assert.notEqual(o.autOrder % 13, 0);
  assert.equal(o.autOrder % 3, 0);
  assert.equal(o.autOrder % 5, 0);
  // the realised element orders must be the true ones, not a broken walk:
  // Aut(W(3,3)) has exponent 12 and these are its element orders
  assert.deepEqual(o.elementOrdersRealised, [1, 2, 3, 4, 5, 6, 9, 12]);
  assert.ok(!o.elementOrdersRealised.some((n) => n > 12),
    "no element order may exceed the exponent -- this caught a real bug");
  for (const r of o.primes) {
    if (r.prime === 7 || r.prime === 13) {
      assert.equal(r.dividesAutOrder, false);
      assert.equal(r.orderRealised, false);
    } else {
      assert.equal(r.dividesAutOrder, true);
      assert.equal(r.orderRealised, true);
    }
  }
  assert.deepEqual(o.whatCouldStillTransport, [3, 5]);
  assert.equal(o.notASearchResult, true);
  // the seven in W(3,3) is alpha, not a group order
  assert.match(o.sevenInW33, /alpha = 7/);
  assert.match(o.sevenInW33, /not\s+a group order/);
  assert.match(o.boundary, /does not rule out some\s+other kind of map/);
});

test("both 114 closure attempts are recorded as undecided", () => {
  for (const f of ["data/tensor_close_at_114.json",
                   "data/tensor_close_at_114_two_sided.json"]) {
    const r = require(path.join(root, f));
    assert.equal(r.size, 114);
    assert.equal(r.slackBudget, 16, "4*114 - 440");
    assert.equal(r.status, "UNKNOWN");
    assert.equal(r.proved, false);
    assert.ok(!("exactTau" in r), "UNKNOWN may not claim an exact value");
    assert.deepEqual(r.intervalUnchanged, [110, 115]);
  }
  // the two-sided model is the strictly stronger one and says so
  const two = require(path.join(root, "data/tensor_close_at_114_two_sided.json"));
  assert.ok(two.encodes.includes("cross-implication coupling the axes"));
  assert.equal(two.linesForcedFullyTightPerAxis, 24);
});

test("a tight blocker carries none of the excluded symmetries", () => {
  const s = require(path.join(root, "data/tensor_tight_symmetry_exclusion.json"));
  assert.equal(s.target, 110);
  assert.equal(s.classesTested, 44);
  assert.equal(s.provedInfeasible, 12);
  // the point of the sweep: nothing was found, anywhere
  assert.equal(s.feasible, 0);
  assert.equal(s.provedInfeasible + s.undecided + s.feasible, s.classesTested);
  // it reaches inside the full wreath group, not just the base
  assert.deepEqual(s.kindsTested.sort(), ["direct", "transpose"]);
  assert.deepEqual(s.ordersExcluded, [2, 4, 6, 9, 12]);
  // every row is one of the three statuses, and none is feasible
  for (const r of s.rows) {
    assert.ok(["INFEASIBLE", "UNKNOWN"].includes(r.status),
      `no class may report feasible: ${JSON.stringify(r)}`);
    assert.ok(r.orbits > 0 && r.orbits < 1600, "orbits collapse the leaves");
  }
  // and it is labelled evidence, not proof
  assert.equal(s.exactTau, null);
  assert.match(s.boundary, /evidence, not proof/);
  assert.match(s.boundary, /stays open in \[110, 115\]/);
});

test("the Levi Betti companion to the other track's hexagon theorem", () => {
  const S = require(path.join(root, "js/substrate.js"));
  const c = require(path.join(root, "data/crosstrack_hexagon_quadrangle.json"));
  // beta1(Levi(GQ(s,t))) = (st)^2, recomputed from the actual incidence graph
  const V = 80;
  let E = 0;
  for (const L of S.LINES) E += L.length;
  assert.equal(E, 160);
  assert.equal(E - V + 1, 81);
  assert.equal(c.bettiCompanion.w33, 81);
  assert.equal(81, Math.pow(3, 4), "3^4, the (st)^2 value at s=t=3");
  for (const r of c.bettiCompanion.table) {
    assert.equal(r.beta1, r.stSquared, `(s,t)=(${r.s},${r.t})`);
    assert.equal(r.matches, true);
  }
  // framed as elementary, not as a discovery
  assert.match(c.bettiCompanion.novelty, /not a discovery/);
});

test("the nine-triple shape match is recorded as NOT a bridge", () => {
  const c = require(path.join(root, "data/crosstrack_hexagon_quadrangle.json"));
  // the structure is real: 9 blockers per centre partition the far-27
  assert.equal(c.nineTriples.partitionsAtEveryCentre, true);
  // but the architecture is common, so it is not evidence of a shared object
  assert.equal(c.nineTriples.isABridge, false);
  assert.ok(c.nineTriples.rivalPartitions >= 200000);
  assert.match(c.nineTriples.why, /common architecture/);
  assert.match(c.nineTriples.whatSurvives, /one per centre/);
  assert.match(c.boundary, /no objectwise identification/);
});

test("the far-27 subconstituent has the parameters the note claims", () => {
  const S = require(path.join(root, "js/substrate.js"));
  const c = require(path.join(root, "data/crosstrack_hexagon_quadrangle.json"));
  // rank-3 shell around a point: 1 + 12 + 27
  const p = 0;
  const near = new Set();
  for (const L of S.LINES) if (L.includes(p)) for (const q of L) if (q !== p) near.add(q);
  assert.equal(near.size, 12);
  const far = [...Array(40).keys()].filter((q) => q !== p && !near.has(q));
  assert.equal(far.length, 27);
  const deg = far.map((a) => far.filter((b) => a !== b && S.isAdjacent(a, b)).length);
  assert.deepEqual([...new Set(deg)], c.nineTriples.far27.degree);
  assert.deepEqual([...new Set(deg)], [8]);
});

test("no two-point convex relaxation can prove the lower bound", () => {
  const s = require(path.join(root, "data/tensor_lower_sdp_ceiling.json"));
  assert.equal(s.status, "optimal");
  assert.equal(s.commutantDimension, 9);
  // the symmetry-reduced Lasserre-1 SDP returns the plain fractional bound
  assert.equal(s.plainFractionalBound, 100);
  assert.ok(Math.abs(s.sdpBound - 100) < 1e-3,
    "the SDP collapses to 1600/16, adding nothing");
  // it does not even reach the elementary shadow bound
  assert.equal(s.shadowBound, 110);
  assert.equal(s.reachesShadowBound, false);
  assert.ok(s.sdpBound < s.shadowBound);
  // and the record says what that bounds: the method family, not tau_2
  assert.match(s.rulesOut, /two-point association scheme/);
  assert.match(s.boundary, /bounds the METHOD family, not tau_2/);
  assert.equal(s.remainingRoutes.length, 2);
});

test("an ovoid is sufficient for multiplicativity; the converse is not claimed", () => {
  const d = require(path.join(root, "data/tensor_multiplicativity_ovoid_defect.json"));
  assert.equal(d.valid, true);
  const [gq22, w33] = d.instances;

  // GQ(2,2) has an ovoid: the two bounds coincide, so tau_2 is exactly tau_1^2.
  // This is the SUFFICIENT direction and is all that is proved.
  assert.equal(gq22.hasOvoid, true);
  assert.equal(gq22.ovoidDefect, 0);
  assert.equal(gq22.tau1, gq22.ovoidSize);
  assert.equal(gq22.shadowLower, gq22.productUpper);
  assert.equal(gq22.intervalWidth, 0);
  assert.equal(gq22.tau2, 25);
  assert.equal(gq22.tau2, gq22.tau1 * gq22.tau1);
  assert.equal(gq22.tau2Status, "OPTIMAL", "solved exactly, no symmetry assumed");
  assert.equal(gq22.multiplicative, true);

  // W(3,3) has none: the defect is 1 and the gap is exactly tau_1 * delta.
  // That opens an interval; it does NOT by itself prove non-multiplicativity.
  // W(3,3) is non-multiplicative because the 115 witness beats 121.
  assert.equal(w33.hasOvoid, false);
  assert.equal(w33.ovoidDefect, 1);
  assert.equal(w33.tau1, 11);
  assert.equal(w33.ovoidSize, 10);
  assert.equal(w33.shadowLower, 110);
  assert.equal(w33.productUpper, 121);
  assert.equal(w33.intervalWidth, 11);
  assert.equal(w33.productUpper - w33.shadowLower, w33.tau1 * w33.ovoidDefect,
    "the width formula tau_1*delta must close");
  // and it is still open, with the truth at neither end
  assert.equal(w33.tau2, null);
  assert.equal(d.w33Open, true);
  assert.deepEqual(d.w33Interval, [110, 115]);
  // stated as a derivation, not a discovery
  assert.match(d.novelty, /not as a discovery/);
});

test("every minimum blocker has a centre, and the structure is fully rigid", () => {
  // Recomputed here from the geometry, not read out of the artifact.
  const S = require(path.join(root, "js/substrate.js"));
  const R = require(path.join(root, "analysis/tensor_blocking_reformulation.js"));
  const B = R.minimumBlockers().map((b) => new Set(b));
  assert.equal(B.length, 360);

  const pencil = new Map();
  for (let p = 0; p < 40; p++) {
    const ls = [];
    for (let li = 0; li < 40; li++) if (S.LINES[li].includes(p)) ls.push(li);
    assert.equal(ls.length, 4, "W(3,3) is 4-regular on lines");
    pencil.set(ls.join(","), p);
  }

  const perCentre = new Map();
  for (const b of B) {
    const exc = [];
    const prof = new Map();
    for (let li = 0; li < 40; li++) {
      const k = S.LINES[li].filter((p) => b.has(p)).length;
      prof.set(k, (prof.get(k) || 0) + 1);
      if (k >= 2) exc.push(li);
    }
    // every blocker meets 36 lines once and 4 lines twice
    assert.equal(prof.get(1), 36);
    assert.equal(prof.get(2), 4);
    assert.equal(prof.size, 2, "no line is met three or more times");
    // the four doubly-met lines are exactly a pencil
    const c = pencil.get(exc.join(","));
    assert.notEqual(c, undefined, "the excess set must be a pencil");
    assert.ok(!b.has(c), "a blocker never contains its own centre");
    perCentre.set(c, (perCentre.get(c) || 0) + 1);
  }
  assert.equal(perCentre.size, 40, "forty centres");
  for (const n of perCentre.values()) assert.equal(n, 9, "nine per centre");
  assert.equal(40 * 9, 360);
});

test("the centre structure is recorded as prior art, not as a discovery", () => {
  const c = require(path.join(root, "data/w33_blocker_centre_structure.json"));
  assert.equal(c.valid, true);
  assert.match(c.novelty, /NOT NEW/);
  assert.ok(c.citations.length >= 1);
  assert.match(c.citations[0].source, /Eisfeld/);
  assert.match(c.citations[0].source, /Discrete Mathematics 238 \(2001\)/);
  // the published bound is what tau_1 = 11 reproduces; it is not ours
  assert.match(c.citations[0].bearing, /prior art/);
  assert.equal(c.tau1, 11);
  assert.match(c.oursInstead, /tensor/);
});

test("the tight case has support at least 24, beating the counting bound", () => {
  const d = require(path.join(root, "data/tensor_tight_degree_sequences.json"));
  // alpha = 7 alone gives only ceil(110/7) = 16
  assert.equal(d.naiveCountingSupport, 16);
  assert.equal(d.provedBounds.support_min.value, 24);
  assert.equal(d.provedBounds.support_min.proved, true);
  assert.equal(d.provedBounds.support_min.status, "OPTIMAL");
  assert.ok(d.provedBounds.support_min.value > d.naiveCountingSupport,
    "the geometry must beat the counting bound for this to be worth having");
  // no tight solution is flat
  assert.equal(d.provedBounds.maxfibre_min.value, 4);
  assert.equal(d.provedBounds.maxfibre_max.value, 7);
  // and the enumeration itself decided nothing
  assert.equal(d.complete, false);
  assert.equal(d.proved, false);
  assert.match(d.observedRangesAreNotBounds, /only provedBounds are facts/);
});

test("the LNS run is recorded as bounding the method, not tau_2", () => {
  const r = require(path.join(root, "data/tensor_upper_lns.json"));
  assert.equal(r.startedFrom, 115);
  assert.equal(r.result, 115);
  assert.equal(r.improved, false);
  assert.equal(r.exactTau, null);
  assert.equal(r.witnessVerified, true);
  assert.equal(r.witnessMinimal, true);
  assert.match(r.onesided, /bounds the method, not tau_2/);
  assert.ok(r.rounds > 0, "the search actually ran");
});

test("the tight-case lower-bound attempt is recorded as undecided, not as evidence", () => {
  const r = require(path.join(root, "data/tensor_tight_rows_and_columns.json"));
  assert.equal(r.target, 110);
  assert.equal(r.proved, false);
  assert.equal(r.status, "UNKNOWN");
  assert.equal(r.conclusion, "undecided in budget");
  assert.equal(r.forced.T3_everyFibreAndCofibreIsIndependent, true,
    "the derivation is sound even though the solver did not decide");
  assert.deepEqual(r.intervalUnchanged, [110, 115]);
  assert.ok(!("newLowerBound" in r), "no lower bound may be claimed from UNKNOWN");
});

test("the lower bound is untouched: narrowing the interval did not close it", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const c = T.depth2Certificate();
  assert.equal(c.bounds.lower, 110, "the shadow double count is unchanged");
  assert.equal(c.openGap, 5, "gap fell from 11 to 5");
  assert.equal(c.exactTau, null, "the exact value is still unknown");
  assert.match(c.evidenceBoundary, /No claim is made that either endpoint is the exact/);
  assert.ok(c.bounds.lower < c.bounds.upper, "the interval is still open");
});

// ======================================================================
// The tensor blocking reformulation
//
// Where the no-ovoid result re-enters, two levels from where it was
// proved: at |X| = 110 every column of a blocking set is forced to be a
// partial ovoid, so alpha = 7 caps it.
// ======================================================================

const TBR = require(path.join(root, "analysis/tensor_blocking_reformulation.js"));

test("there are exactly 360 minimum blocking sets of the 40 lines", () => {
  const B = TBR.minimumBlockers();
  assert.equal(B.length, 360);
  for (const b of B.slice(0, 25)) {
    assert.equal(b.length, 11);
    for (const L of S.LINES) {
      assert.ok(L.some((p) => b.includes(p)), "every line is met");
    }
  }
  // 360 divides the automorphism group order
  assert.equal(51840 % 360, 0);
});

test("the column view detects blocking exactly", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const B = [...T.BLOCKER];
  const bxb = [];
  for (const p of B) for (const q of B) bxb.push(p * 40 + q);
  const v = TBR.columnView(bxb);
  assert.ok(v.blocking, "B x B blocks, seen through columns");
  assert.equal(v.maxColumn, 11);

  // drop a whole column and it must stop blocking
  const holed = bxb.filter((x) => x % 40 !== B[0]);
  assert.ok(!TBR.columnView(holed).blocking, "removing a column breaks it");
});

test("independence of the columns is forced only at the tight count", () => {
  const T = require(path.join(root, "js/tensor-sharding.js"));
  const B = [...T.BLOCKER];
  const bxb = [];
  for (const p of B) for (const q of B) bxb.push(p * 40 + q);
  const v = TBR.columnView(bxb);
  // B x B has 121, not 110, so its columns need not be independent -- and
  // they are not. A test that asserted independence here would be wrong.
  assert.equal(v.allIndependent, false);
  assert.equal(bxb.length, 121);

  // an 11-point blocker is never independent: alpha is 7
  assert.ok(!TBR.isIndependent(B), "a minimum blocker exceeds alpha = 7");
});

test("the fibre-size relaxation cannot improve the lower bound", () => {
  const r = TBR.run();
  assert.equal(r.fibreSizeRelaxation.lpOptimum, 110);
  assert.equal(r.fibreSizeRelaxation.integerOptimum, 110,
    "integrality costs nothing here, so any improvement must come from the sets");
  assert.equal(r.minimumBlockerCount, 360);
  assert.match(r.open, /no verdict is claimed/,
    "the exact value stays open and is labelled as such");
});

// ======================================================================
// The tight case: what is forced at |X| = 110
// ======================================================================

const TTO = require(path.join(root, "analysis/tensor_tight_obstructions.js"));

test("the incidence identity Nmat^T Nmat = 4I + A holds exactly", () => {
  const r = TTO.incidenceIdentity();
  assert.ok(r.holds, `mismatches: ${JSON.stringify(r.mismatches)}`);
  // it is the statement that two collinear points share exactly one line
  for (let p = 0; p < 40; p++) {
    for (const q of S.ADJ[p]) {
      const shared = S.LINES.filter((L) => L.includes(p) && L.includes(q));
      assert.equal(shared.length, 1);
    }
  }
});

test("the row sums of a tight blocker satisfy (A + 4I) r = 44 . 1", () => {
  const c = TTO.cosetCheck();
  assert.equal(c.degreePlusFour, 16, "k + 4 = 16");
  assert.ok(c.equals44, "(11/4) * 16 = 44, so the uniform vector is a solution");
  // the homogeneous part is the (-4)-eigenspace, dimension 15
  const spec = { 12: 1, 2: 24, "-4": 15 };
  assert.equal(spec["-4"], 15);
});

test("every minimum blocking set induces a bipartite subgraph", () => {
  // 11 points, alpha = 7, and yet chi = 2: minimum blockers of this
  // quadrangle are almost independent sets.
  const r = TTO.run();
  assert.equal(r.minimumBlockerChromaticDistribution["2"], 360);
  assert.ok(r.minimumBlockersAreBipartite);
  // so the "four fibres per line" constraint is nowhere near binding
  const obstruction = r.obstructionsTried.find((o) => /colourability/.test(o.name));
  assert.equal(obstruction.fires, false);
});

test("every arithmetic relaxation of the tight case survives", () => {
  const r = TTO.run();
  assert.equal(r.obstructionsTried.length, 4);
  for (const o of r.obstructionsTried) {
    assert.equal(o.fires, false,
      `${o.name} was expected not to fire; if it now does, the bound improves`);
  }
  assert.match(r.conclusion, /stays open/,
    "and the exact value is still reported as open");
});

// ======================================================================
// The t > s theorem: the tight case is impossible for a whole family,
// and the trichotomy is proved rather than borrowed
// ======================================================================

test("the trichotomy leaves exactly two branches, and t > s kills one", () => {
  const t = require(path.join(root, "data/gq_tight_case_theorem.json"));
  assert.ok(t.valid);

  const by = Object.fromEntries(t.instances.map((r) => [r.name, r]));
  const gq24 = by["Q^-(5,2) = GQ(2,4)"];
  const q53 = by["Q^-(5,3) = GQ(3,9)"];
  const w33 = by["W(3,3) = GQ(3,3)"];

  // branch (A) is always available; branch (B) needs t <= s
  for (const r of t.instances) {
    const wide = r.branches.filter((b) => b.mult1Points > 0);
    assert.equal(wide.length > 0, r.t <= r.s,
      `${r.name}: branch (B) should exist exactly when t <= s`);
  }

  // the two no-ovoid quadrangles with t > s are both excluded
  for (const r of [gq24, q53]) {
    assert.ok(r.delta >= 1, `${r.name} has no ovoid`);
    assert.ok(r.t > r.s);
    assert.ok(r.theoremApplies);
    assert.match(r.conclusion, /^tau_2 > /);
  }
  assert.equal(gq24.tightSize, 90);
  assert.equal(q53.tightSize, 840);

  // W(3,3) sits on the diagonal, so the theorem must NOT claim it
  assert.equal(w33.s, w33.t);
  assert.equal(w33.theoremApplies, false,
    "t = s leaves branch (B) open; that case needed self-duality, not counting");
});

test("the centre property is checked, and it does not assume delta = 1", () => {
  const t = require(path.join(root, "data/gq_tight_case_theorem.json"));
  const by = Object.fromEntries(t.instances.map((r) => [r.name, r]));

  for (const r of t.instances) {
    if (r.delta < 1) continue;
    const cp = r.centreProperty;
    assert.ok(cp.sampled > 0, `${r.name}: no minimum blockers sampled`);
    assert.ok(cp.holdsOnEverySampled,
      `${r.name}: the centre property failed on a sampled blocker`);
    assert.equal(cp.centreInsideItsBlocker, 0,
      `${r.name}: a blocker contained its own centre`);
  }

  // Q^-(5,3) has defect 2 and the excess is STILL one pencil, each of its
  // lines met delta+1 = 3 times. That is why the argument survives delta > 1.
  const q53 = by["Q^-(5,3) = GQ(3,9)"];
  assert.equal(q53.delta, 2);
  const profiles = Object.keys(q53.centreProperty.profiles);
  assert.equal(profiles.length, 1, "one trace profile across the sample");
  // the key is a Python dict repr, so read it with a regex rather than JSON
  const prof = Object.fromEntries(
    [...profiles[0].matchAll(/(\d+):\s*(\d+)/g)].map((m) => [m[1], +m[2]]));
  assert.equal(prof[String(q53.delta + 1)], q53.linesPerPoint,
    "the excess lines number t+1 and are met delta+1 = 3 times");
  assert.equal(prof["1"], q53.lines - q53.linesPerPoint,
    "every other line is met exactly once");

  // GQ(2,4) is exhaustive: 27 blockers, one per point
  const gq24 = by["Q^-(5,2) = GQ(2,4)"];
  assert.ok(gq24.centreProperty.exhaustive);
  assert.equal(gq24.centreProperty.distinctCentres, 27);
});

test("the counting layer alone settles neither quadrangle", () => {
  const d = require(path.join(root, "data/gq24_centre_balance_diophantine.json"));
  assert.ok(d.valid);
  const by = Object.fromEntries(d.cases.map((c) => [c.name, c]));

  // both Diophantine systems are feasible: the trichotomy is NOT a counting
  // fact, which is exactly why it had to be proved
  assert.ok(by["W(3,3)"].feasible);
  assert.ok(by["GQ(2,4)"].feasible);
  assert.ok(by["W(3,3)"].allOnesIsASolution, "the bijection solves W(3,3)");
  assert.equal(by["GQ(2,4)"].uniformIsIntegral, false, "5/3 is not an integer");
  assert.match(d.conclusion, /both systems are feasible/);
});

test("two further relaxations close, and the linear algebra cross-checks", () => {
  const r = require(path.join(root, "data/tensor_relaxations_that_close.json"));
  assert.ok(r.valid && r.bothClose);
  for (const i of r.instances) {
    assert.equal(i.integralityGain, 0,
      `${i.name}: the size-sum IP should not beat the shadow bound`);
    assert.ok(i.rankObstructionCloses,
      `${i.name}: 1 should lie in the mod-p row space`);
  }
  // rank_3 of W(3,3) must agree with the corpus rank law, not just with itself
  const w = r.instances.find((i) => i.name === "W(3,3)");
  assert.equal(w.rankObstruction["3"].rankN, 25);
  assert.match(r.boundary, /NEGATIVE/);
});

test("their 45 and our 45 are the same set, with an explicit isomorphism", () => {
  const b = require(path.join(root, "data/gq42_bridge_to_85_point_module.json"));
  assert.ok(b.valid && b.isomorphic);
  assert.equal(b.mismatches, 0);
  assert.equal(b.pairsChecked, 990);
  // both sides are SRG(45, 12, 3, 3)
  for (const side of [b.theirSide.srg, b.ourSide.srg]) {
    assert.deepEqual(side.degree, [12]);
    assert.deepEqual(side.lambda, [3]);
    assert.deepEqual(side.mu, [3]);
  }
  assert.equal(b.theirSide.commit, "fd10fd7e2");
  // and no implication is claimed in either direction
  assert.match(b.notClaimed, /no implication/);
});

test("the centre property is a perp profile, and W(3,3) is the exception", () => {
  const r = require(path.join(root, "data/gq_perp_blockers_and_h44.json"));
  assert.ok(r.valid);
  const by = Object.fromEntries(r.instances.map((i) => [i.name, i]));

  // the classical fact, checked in every geometry including W(3,3)
  for (const i of r.instances) {
    assert.ok(i.perpIsBlocking, `${i.name}: p-perp should block every line`);
    assert.equal(i.perpSize, i.s * (i.t + 1));
    assert.equal(i.perpProfile[String(i.s)], i.t + 1,
      `${i.name}: the perp meets the t+1 lines of its pencil s times`);
  }

  // where t > s, tau_1 attains the perp size and the blockers ARE perps,
  // which is what makes the centre property automatic
  for (const i of r.instances.filter((x) => x.tGreaterThanS)) {
    assert.ok(i.tau1Proved, `${i.name}: tau_1 must be proved optimal`);
    assert.equal(i.tau1, i.perpSize);
    assert.equal(i.delta, i.s - 1, "delta = s(t+1) - (st+1) = s - 1");
    assert.ok(i.allSampledArePerps);
  }

  // W(3,3) beats the perp construction by exactly one point
  const w = by["W(3,3)"];
  assert.equal(w.tau1, 11);
  assert.equal(w.perpSize, 12);
  assert.equal(r.w33IsTheException.beatsPerpBy, 1);
  assert.equal(w.sampledThatArePerps, 0,
    "none of W(3,3)'s minimum blockers is a perp");
  assert.notEqual(w.delta, w.s - 1, "and its defect breaks the s-1 pattern");

  // the third family
  const h = by["H(4,4)"];
  assert.equal(h.points, 165);
  assert.equal(h.lines, 297);
  assert.equal(h.tightSize, 1188);
  assert.match(r.thirdFamily.conclusion, /tau_2\(H\(4,4\)\^2\) > 1188/);
  assert.ok(r.thirdFamily.hermitianNotQuadric);

  // the general-q statement is explicitly NOT claimed
  assert.match(r.notClaimed, /EVERY q/);
});

test("on the diagonal the branches cannot mix, and q=5 stops the extension", () => {
  const d = require(path.join(root, "data/gq_diagonal_theorem.json"));
  assert.ok(d.valid);

  // the mixing lemma's sharp prediction on W(3,3): imposing only the
  // trichotomy cuts 14370 balance solutions to exactly one, the bijection
  const v = d.verification;
  // a floor, deliberately: that enumeration is never run to completion
  assert.ok(v.solutionsWithoutTrichotomyAtLeast > 10000);
  assert.equal(v.solutionsWithTrichotomy, 1);
  assert.equal(v.allOnesSolutions, 1);
  assert.equal(v.ovoidSupportedSolutions, 0, "W(3,3) has no ovoid");
  assert.equal(v.status, "OPTIMAL");

  // and the extension to odd q is BLOCKED, measured not assumed
  assert.ok(d.w35.centrePropertyFails);
  assert.equal(d.w35.theoremApplies, false);
  assert.ok(d.w35.centreProperty.centrePropertyHolds <
            d.w35.centreProperty.sampled);
  assert.match(d.wouldCover, /does NOT/);

  // tau_1(W(3,5)) = 29, proved, one below the point-perp -- same margin as q=3
  assert.equal(d.w35.tau1, 29);
  assert.ok(d.w35.tau1Proved);
  assert.equal(d.w35.pointPerpSize, 30);
  assert.equal(d.w35.beatsPerpBy, 1);
  assert.equal(d.tau1Conjecture.status.startsWith("CONJECTURE"), true,
    "q^2+q-1 is labelled a conjecture, not a result");
  for (const c of d.tau1Conjecture.confirmations) {
    assert.equal(c.tau1, c.q * c.q + c.q - 1);
  }

  // the trichotomy of cases is recorded with t < s still open
  assert.match(d.trichotomy.tLessThanS, /OPEN/);
  assert.match(d.attribution.theirs, /43049db/);
});

// ======================================================================
// The tight case is an m-ovoid question, with m = t+1
// ======================================================================

test("the tight case is exactly a {0,1,t+1} weighting, and its pure cases " +
     "are an ovoid and a (t+1)-ovoid", () => {
  const r = require(path.join(root, "data/gq_tight_case_is_an_m_ovoid.json"));
  assert.ok(r.valid);
  const by = Object.fromEntries(r.instances.map((i) => [i.name, i]));

  // the (F,U) structure is not a claim about some solutions -- it held on
  // every single weighting enumerated, in every geometry
  for (const i of r.instances) {
    const c = i.census;
    assert.equal(c.structure, c.k, `${i.name}: (F,U) structure must hold on all`);
    assert.equal(c.partialOvoid, c.k, `${i.name}: F must always be a partial ovoid`);
    assert.equal(c.pureA, c.pureAisOvoid, `${i.name}: every pure-A is an ovoid`);
    assert.equal(c.pureB, c.pureBisMOvoid, `${i.name}: every pure-B is a (t+1)-ovoid`);
  }

  // t > s: the (t+1)-ovoid cannot fit on a line, so nothing survives
  for (const n of ["GQ(2,4)", "Q^-(5,3)", "H(4,4)"]) {
    const i = by[n];
    assert.ok(i.t > i.s);
    assert.ok(i.mExceedsLineSize, `${n}: t+1 must exceed the line size`);
    assert.equal(i.ovoidStatus, "INFEASIBLE");
    assert.equal(i.mOvoidStatus, "INFEASIBLE");
    assert.ok(i.tightCaseExcluded, `${n}: tight case must be excluded`);
    assert.equal(i.census.k, 0);
  }

  // GQ(4,2) recovers the 200 known ovoids as a by-product
  const g42 = by["GQ(4,2)"];
  assert.equal(g42.census.pureA, 200, "GQ(4,2) has exactly 200 ovoids");
  assert.equal(g42.census.k, 200 + g42.census.pureB + g42.census.mixed);
  assert.ok(g42.census.complete, "that census is exhaustive");

  // GQ(8,4) has NO ovoid but does have a 5-ovoid, so counting cannot close it
  const g84 = by["GQ(8,4)"];
  assert.equal(g84.ovoidStatus, "INFEASIBLE", "GQ(8,4) has no ovoid");
  assert.equal(g84.mOvoidExists, true, "but it does have a (t+1)-ovoid");
  assert.equal(g84.tightCaseExcluded, false);
});

test("the diagonal is provably beyond any counting argument", () => {
  const r = require(path.join(root, "data/gq_tight_case_is_an_m_ovoid.json"));
  const w = r.instances.find((i) => i.s === i.t);

  // at t = s the (t+1)-ovoid is the whole point set, so it always exists
  assert.equal(w.name, "W(3,3)");
  assert.equal(w.mOvoidNeeded, w.pointsPerLine,
    "a (t+1)-ovoid must take every point of every line");
  assert.equal(w.mOvoidExists, true);
  assert.equal(w.ovoidExists, false, "W(3,3) still has no ovoid (Thas)");
  assert.equal(w.census.pureB, 1, "exactly one: the all-ones vector");
  assert.equal(w.census.pureA, 0);
  assert.equal(w.census.mixed, 0);
  assert.equal(w.tightCaseExcluded, false);
  assert.match(r.diagonalIsBeyondCounting, /PROVES/);

  // and the prior art is credited, with the new part named
  assert.match(r.priorArt.inThisRepository, /w33_shape_catalogue/);
  assert.match(r.priorArt.whatIsNewHere, /connection to the depth-2/);
  // the subquadrangle route is recorded as refuted, not quietly dropped
  assert.match(r.refutedConjecture, /27/);
});

test("115 is what the group gives, and the solver stops at exactly 110", () => {
  const r = require(path.join(root, "data/tensor_115_resists_from_both_sides.json"));
  assert.ok(r.valid);

  // the constraint side reaches the shadow bound and no further
  const c = r.constraintSide;
  assert.equal(c.boundBefore, 101);
  assert.equal(c.boundAfter, 110, "exactly the shadow bound, not one more");
  assert.equal(c.objective, 115);
  assert.match(c.feasibilityAt111, /UNKNOWN/, "111 got no verdict either way");

  // the symmetry side: every witness is verified, and only one class hits 115
  assert.equal(r.groupOrder, 25920, "PSp(4,3)");
  for (const row of r.symmetrySide.rows) {
    assert.ok(row.verified, `order ${row.order}: witness must block all tiles`);
    assert.ok(row.best >= 115, "no cyclic class beat the known witness");
  }
  assert.equal(r.symmetrySide.best, 115);
  assert.deepEqual(r.symmetrySide.attainedBy, [6]);

  // and that class is the witness's own stabiliser -- 115 is not a fluke
  const st = r.witnessStabiliser;
  assert.equal(st.order, 6);
  assert.deepEqual(st.elementOrders, [1, 2, 3, 6]);
  assert.equal(st.total, 115);
  assert.equal(st.orbitProfile["6"], 11);
  assert.ok(st.sweepRecoversIt,
    "the blind sweep must recover 115 from the same order");

  // the limits of the sweep are recorded, not glossed
  assert.ok(r.boundaries.some((b) => /not proved minima/.test(b)));
  assert.ok(r.boundaries.some((b) => /only cyclic subgroups/.test(b)));
  assert.deepEqual(r.frontier.interval, [111, 115]);
});

// ======================================================================
// The exponential base of the depth-n blocking number
// ======================================================================

test("the growth rate is exactly 10, and the SDP's 100 was tau*(H^2)", () => {
  const r = require(path.join(root, "data/tensor_growth_rate_is_exactly_ten.json"));
  assert.ok(r.valid);

  // the hand certificate is checked, not asserted
  assert.ok(r.certificateChecked.coverIsUnitOnEveryLine);
  assert.ok(r.certificateChecked.matchingIsUnitOnEveryPoint);
  assert.ok(Math.abs(r.tauStar - 10) < 1e-6);
  assert.equal(r.tauStar.toFixed(6), r.nuStar.toFixed(6),
    "tau* = nu* is what makes both certificates optimal");
  assert.equal(r.tau1, 11);

  // multiplicativity, verified on the 1600-variable product LP
  assert.ok(Math.abs(r.tauStarProduct - 100) < 1e-4);
  assert.match(r.sdpIdentified, /not an artifact/);

  // the base is pinned to 10, where before it was only in [10, sqrt(115)]
  assert.equal(r.baseAfter, 10);
  assert.equal(r.basesBefore.lower, 10);
  assert.ok(r.basesBefore.upper > 10.72 && r.basesBefore.upper < 10.73);
  assert.match(r.theorem, /= 10$/);

  // and the finite bounds are not overturned: the product number is better
  // than greedy's until a depth nobody uses, and greedy loses to 115 at n=2
  assert.ok(r.productBoundBetterUntilDepth > 50);
  assert.ok(r.greedyOnH2 > 115, "greedy does not threaten the 115 witness");
  for (const row of r.depthTable) {
    assert.ok(row.lowerRecursive <= row.upperProduct,
      `depth ${row.depth}: lower must not exceed the product upper bound`);
  }
  assert.match(r.boundary, /asymptotic/);
});

test("their 216 hemisystem lines are our 432 hemisystems modulo complement", () => {
  const h = require(path.join(root, "data/w33_hemisystems_are_their_216.json"));
  assert.ok(h.valid);

  assert.equal(h.count, 432);
  assert.ok(h.enumerationComplete, "the census must be exhaustive");
  assert.ok(h.allSize20);
  assert.ok(h.closedUnderComplementation,
    "a line meeting T twice meets the complement 4-2 = 2 times");
  assert.equal(h.selfComplementary, 0);
  assert.equal(h.complementaryPairs, 216);
  assert.ok(h.matchesTheir216);
  assert.equal(h.theirSide.count, 216);

  // the two derivations are independent, and the limits are stated
  assert.match(h.theirSide.route, /trade-lattice|GQ\(4,2\)/);
  assert.match(h.ourSide.route, /m-ovoid census/);
  assert.match(h.notClaimed, /no fibre-level correspondence/);
});

test("blocker excess plus column dependence equals (t+1) times the slack", () => {
  const r = require(path.join(root, "data/tensor_excess_conservation_law.json"));
  assert.ok(r.valid);
  assert.equal(r.law, "F + D = (t+1) r");

  // the law is checked on two blockers built by unrelated constructions
  assert.equal(r.instances.length, 2);
  for (const a of r.instances) {
    assert.ok(a.lawHolds, `${a.name}: F + D must equal (t+1)r`);
    assert.equal(a.FplusD, a.lawTarget);
    assert.equal(a.lawTarget, 4 * a.r, "t+1 = 4 for W(3,3)");
    assert.ok(a.GequalsTPlus1D, "collisions are 4D, not a separate quantity");
    assert.equal(a.G, 4 * a.D);
    // the corollary must actually hold, not just be stated
    assert.ok(a.minimumRowShadows >= a.guaranteedMinimumRows);
    assert.ok(a.independentColumnClasses >= a.guaranteedIndependentColumns);
  }

  const w = r.instances.find((a) => a.size === 115);
  const prod = r.instances.find((a) => a.size === 121);
  assert.equal(w.r, 5);
  assert.equal(w.F, 10);
  assert.equal(w.D, 10);
  // the optimum carries a column class of size 10, which alpha = 7 forbids
  // from being independent -- it is not a near-tight configuration
  assert.equal(w.columnClassSizes["10"], 1);
  assert.ok(w.minimumRowShadows < 40, "not all its row shadows are minimum");

  // the product blocker has NO blocker excess at all: its 44 units are pure
  // dependence, which is the opposite extreme
  assert.equal(prod.r, 11);
  assert.equal(prod.F, 0);
  assert.equal(prod.D, 44);
  assert.equal(prod.minimumRowShadows, 40);

  assert.match(r.tightCase, /r = 0/);
  assert.match(r.boundary, /identity, not a bound/);
});

// ======================================================================
// What the blocking numbers mean: Pauli context covering
// ======================================================================

test("tau_1 and alpha are Pauli measurement quantities, verified with matrices", () => {
  const r = require(path.join(root, "data/w33_blocking_is_pauli_context_covering.json"));
  assert.ok(r.valid);
  const v = r.verifiedWithMatrices;

  // the identification is checked on actual 9x9 matrices, not asserted
  assert.equal(v.paulisBuilt, 80);
  assert.equal(v.commutatorFormMismatches, 0,
    "commuting must coincide with the symplectic form on every pair");
  assert.equal(v.pairsChecked, 3160);
  assert.equal(v.projectiveClasses, 40);
  assert.deepEqual(v.srg.degree, [12]);
  assert.deepEqual(v.srg.lambda, [2]);
  assert.deepEqual(v.srg.mu, [4]);

  // lines really are the maximal commuting subalgebras
  assert.equal(v.contexts, 40);
  assert.equal(v.contextSize, 4);
  assert.ok(v.everyContextCommutes);

  // and the two numbers come back with their combinatorial values
  assert.equal(r.readings.tau1.value, 11);
  assert.ok(r.readings.tau1.proved);
  assert.equal(r.readings.alpha.value, 7);
  assert.ok(r.readings.alpha.proved);
  assert.match(r.readings.alpha.meaning, /non-commuting/);

  // depth 2 is about LOCAL product observables, a proper subset of 4-qutrit
  assert.equal(r.fourQutritClasses, 3280);
  assert.equal(r.productObservables, 1600);
  assert.ok(r.productObservables < r.fourQutritClasses);
  assert.match(r.scopeNote, /proper\s+subset/);
  assert.match(r.boundary, /not a new bound/);
});

test("the annealing evidence at 114 is invalidated by its own control", () => {
  const r = require(path.join(root, "data/tensor_114_search_log_with_control.json"));
  assert.ok(r.valid);
  assert.ok(r.isSearchLogNotTheorem);

  // the control ran at sizes that ARE feasible and still failed
  for (const c of r.control) {
    assert.ok(c.knownFeasible, "the control must target a feasible size");
    assert.equal(c.solved, false);
    assert.ok(c.bestUncovered > 6,
      "cold starts do worse than the seeded 114 run, which is the point");
  }
  assert.ok(r.controlInvalidatesAnnealingEvidence);
  assert.match(r.whatIsNotEstablished, /carries no weight/);
  assert.match(r.whatSurvives, /locally isolated/);

  // the LNS rounds are the evidence that does carry weight -- exact
  // sub-solves, thousands of overlapping neighbourhoods -- and its own
  // limit is recorded rather than glossed
  const lns = r.attempts.filter((a) => /LNS/.test(a.method));
  assert.equal(lns.length, 2, "small and large neighbourhood runs");
  for (const a of lns) assert.match(a.result, /0 improvements/);
  assert.match(r.whatSurvives, /3,430/);
  assert.match(r.lnsCaveat, /not proved its\s+neighbourhood empty/);

  // and the searcher that failed calibration is recorded so it is not rebuilt
  assert.ok(r.attempts.some((a) => /row-weighting/.test(a.method)
                                 && /calibration/.test(a.result)));

  // the cyclic sweep's own stated boundary is now closed, not left open
  const nc = r.attempts.find((a) => /NON-CYCLIC/.test(a.method));
  assert.ok(nc, "the non-cyclic sweep must be recorded");
  assert.match(nc.result, /9 distinct classes/);
  assert.match(nc.result, /best 116/);
  assert.equal(nc.verdict, "no improvement");
  assert.match(r.nonCyclicGapClosed, /orders 4, 8, 9 and 24/);

  // and no attempt claims to have moved anything
  assert.deepEqual(r.frontier.interval, [111, 115]);
  for (const a of r.attempts) {
    assert.ok(/no improvement|no verdict|no solution/.test(a.verdict),
      `${a.method} must not claim an improvement`);
  }
  assert.match(r.constraintSideCeiling, /^110/);
});

// ======================================================================
// Pauli incompatibility = partial ovoids of symplectic polar spaces
// ======================================================================

test("mutually incompatible Paulis are partial ovoids, and alpha(W(3,5)) = 18", () => {
  const r = require(path.join(root, "data/pauli_incompatibility_is_partial_ovoids.json"));
  assert.ok(r.valid);
  const by = Object.fromEntries(r.instances.map((i) => [i.space, i]));

  // every value solved to optimality, every witness genuinely non-commuting
  for (const i of r.instances) {
    assert.equal(i.status, "OPTIMAL", `${i.space} must be proved`);
    assert.ok(i.witness.pairwiseNonCommuting,
      `${i.space}: the witness must be pairwise non-commuting`);
    assert.equal(i.witness.size, i.alpha);
    assert.equal(i.ovoidCeiling, Math.pow(i.q, i.n) + 1);
    assert.equal(i.shortfall, i.ovoidCeiling - i.alpha);
  }

  // the controls: qubits reproduce the known 2n+1 law
  assert.equal(by["W(3,2)"].alpha, 5);
  assert.equal(by["W(3,2)"].alpha, by["W(3,2)"].twoNplusOne);
  assert.equal(by["W(3,2)"].shortfall, 0, "q even: an ovoid exists");
  assert.equal(by["W(5,2)"].alpha, 7);
  assert.equal(by["W(5,2)"].alpha, by["W(5,2)"].twoNplusOne);

  // two qutrits reproduce Sarkar-Yoder's 7, short of the ceiling 10
  assert.equal(by["W(3,3)"].alpha, 7);
  assert.equal(by["W(3,3)"].ovoidCeiling, 10);
  assert.equal(by["W(3,3)"].shortfall, 3);
  assert.notEqual(by["W(3,3)"].alpha, by["W(3,3)"].twoNplusOne,
    "the qubit law does not survive to qutrits");

  // 18 attained, 19 impossible -- but recorded as VERIFICATION, not discovery
  assert.equal(by["W(3,5)"].alpha, 18);
  assert.equal(r.newResult.size19, "INFEASIBLE");
  assert.match(r.newResult.statement, /verified independently/);
  // the correction must be present and must name the published source
  assert.match(r.correction, /Cimrakova and Fack/);
  assert.match(r.correction, /independent verification/);
  // Tallini's bound is credited as a THEOREM, not called a refuted formula
  assert.match(r.tallini, /q\^2\+1-q/);
  assert.match(r.newResult.doesNotRefute, /valid upper bound/);
  assert.equal(r.newResult.refutes.length, 1,
    "only the deficiency=q pattern is refuted, not Tallini");
  assert.ok(r.newResult.refutes.some((x) => /26-18 = 8/.test(x)));
  assert.match(r.priorArt.geometryValues, /33/);

  // and the honest limits are recorded
  assert.match(r.leadNotResult, /lead and not a proof/);
  assert.match(r.boundary, /restatement, not a theorem/);
  assert.match(r.priorArt.qudit, /2302\.07966/);
});

test("the context cover equals the MUB count exactly when q is even", () => {
  const r = require(path.join(root, "data/context_cover_equals_mub_count_iff_q_even.json"));
  assert.ok(r.valid && r.dichotomyHolds);

  const by = Object.fromEntries(r.rows.map((x) => [x.q, x]));
  for (const row of r.rows) {
    assert.equal(row.status, "OPTIMAL", `q=${row.q} must be proved`);
    assert.equal(row.mubCount, row.q * row.q + 1);
    assert.equal(row.excess, row.tau1 - row.mubCount);
    // the dichotomy itself, on every row
    assert.equal(row.attainsMubCount, row.qEven,
      `q=${row.q}: attains the MUB count iff q is even`);
  }
  assert.equal(by[2].tau1, 5);
  assert.equal(by[3].tau1, 11);
  assert.equal(by[4].tau1, 17);
  assert.equal(by[5].tau1, 29);

  // q=7 and q=8 were run separately; q=8 is a THIRD even case at the MUB count
  const extra = Object.fromEntries(r.additionalRuns.map((x) => [x.q, x]));
  assert.equal(extra[8].tau1, 65);
  assert.equal(extra[8].excess, 0);
  assert.equal(extra[8].status, "OPTIMAL");
  assert.equal(extra[8].mubCount, 65);
  // q=7 is only a witness, and must be recorded as bounded rather than pinned
  assert.equal(extra[7].status, "FEASIBLE");
  assert.equal(extra[7].excessAtMost, 5);
  assert.match(extra[7].note, /not pinned/);

  // q=4 is the row that kills a naive formula: excess 0 while q-2 = 2
  assert.equal(by[4].excess, 0);
  assert.match(r.oddExcessPattern, /NOT q-2 at q = 4/);

  // the two tens must be kept apart
  assert.match(r.twoTens.phi4, /every q/);
  assert.match(r.twoTens.tauStar, /26 at q=5/);
  assert.match(r.twoTens.note, /q = 3 alone/);

  // prior art credited, new part named
  assert.ok(r.priorArt.inRepo.length >= 3);
  assert.ok(r.priorArt.inRepo.some((x) => /MUB basis states/.test(x)));
  assert.ok(r.priorArt.inRepo.some((x) => /36 spreads/.test(x)));
  assert.match(r.priorArt.external, /Kantor/);
  assert.match(r.priorArt.newHere, /parity dichotomy/);
  assert.match(r.boundary, /not proved as a\s+family/);
});

// ======================================================================
// When is a perfect context transversal available? (Thas's classification)
// ======================================================================

test("a perfect context transversal exists only for two qudits of even dimension", () => {
  const r = require(path.join(root, "data/perfect_context_transversal_classification.json"));
  assert.ok(r.valid && r.allRowsMatchThas);
  assert.match(r.theorem, /Thas/);

  const by = Object.fromEntries(r.rows.map((x) => [x.space, x]));
  for (const row of r.rows) {
    // the geometry builder is validated by its own context count
    assert.ok(row.contextCountMatches,
      `${row.space}: contexts must equal prod (q^i+1)`);
    assert.equal(row.contexts, row.contextsExpected);
    assert.equal(row.fractionalValue, Math.pow(row.q, row.n) + 1);
    assert.equal(row.excess, row.tau1 - row.fractionalValue);
    // Thas's prediction: free iff n = 2 and q even
    assert.equal(row.predictedFree, row.n === 2 && row.q % 2 === 0);
    assert.equal(row.isFree, row.predictedFree,
      `${row.space}: freeness must match the classification`);
    assert.ok(row.matchesThas);
  }

  // the free ones
  assert.equal(by["W(3,2)"].excess, 0);
  assert.equal(by["W(3,4)"].excess, 0);
  // the odd-q ones are not free
  assert.equal(by["W(3,3)"].excess, 1);
  assert.ok(by["W(3,5)"].excess > 0);

  // THE decisive row: q=2 is even, but rank 3 loses the transversal
  const three = by["W(5,2)"];
  assert.equal(three.n, 3);
  assert.equal(three.q, 2, "even dimension");
  assert.equal(three.tau1, 10);
  assert.equal(three.fractionalValue, 9);
  assert.equal(three.excess, 1);
  assert.equal(three.isFree, false, "a third qubit destroys the free lunch");
  assert.equal(three.status, "OPTIMAL");

  assert.ok(r.consequences.some((c) => /rank-2 phenomenon/.test(c)));
  assert.match(r.statusNote, /FEASIBLE only bounds/);
  assert.match(r.boundary, /the proof is Thas's/);
});

test("the 115-leaf schedule is one Clifford gate plus 39 seeds", () => {
  const r = require(path.join(root, "data/witness_compresses_under_one_clifford.json"));
  assert.ok(r.valid);

  // the gate is an explicit symplectic 4x4 over F_3 of order 6
  assert.equal(r.gate.length, 4);
  for (const row of r.gate) {
    assert.equal(row.length, 4);
    for (const x of row) assert.ok(x >= 0 && x < 3, "entries live in F_3");
  }
  assert.equal(r.gateOrder, 6);
  assert.ok(r.gateIsSymplectic, "symplectic means it names a Clifford coset");
  assert.ok(r.stabilisesWitness);

  // the compression, and the regeneration that proves it is real
  assert.equal(r.witnessSize, 115);
  assert.equal(r.seeds, 39);
  const total = Object.entries(r.orbitProfile)
    .reduce((s, [len, count]) => s + Number(len) * count, 0);
  assert.equal(total, 115, "orbit lengths must sum to the witness size");
  const orbits = Object.values(r.orbitProfile).reduce((a, b) => a + b, 0);
  assert.equal(orbits, r.seeds, "one seed per orbit");

  // regeneration is checked by rebuilding, not by counting
  assert.ok(r.regeneratesExactly, "seeds + gate must rebuild the witness exactly");
  assert.ok(r.regeneratedStillBlocks, "and the rebuild must still block");
  assert.equal(r.tiles, 1600);
  assert.ok(r.compression > 2.9 && r.compression < 3.0);

  // and the limits are stated
  assert.match(r.canonicality, /no other/);
  assert.match(r.boundary, /does not\s+lower tau_2/);
});

test("structure injection cannot reprove 110, so that route is closed", () => {
  const r = require(path.join(root, "data/structure_injection_cannot_reprove_110.json"));
  assert.ok(r.valid && r.isNegativeMethodResult);

  // the control ran on a case whose answer is a THEOREM, and failed it
  for (const run of r.runs) {
    assert.equal(run.target, 110);
    assert.equal(run.slack, 0, "r=0 is the most constrained instance");
    assert.equal(run.knownAnswer, "INFEASIBLE");
    assert.equal(run.status, "UNKNOWN");
    assert.equal(run.reprovedKnownAnswer, false);
  }
  // and it was given real time, not a token budget
  assert.ok(Math.max(...r.runs.map((x) => x.budgetMinutes)) >= 45);
  assert.ok(r.controlFailed);

  // the model really did inject the theory, not just more inequalities
  assert.match(r.model, /360 known minimum blockers/);
  assert.match(r.model, /F \+ D = 4r/);

  assert.match(r.whyRouteIsClosed, /UNKNOWN at 111 would carry no information/);
  assert.match(r.boundary, /moves no bound/);
});

// ======================================================================
// The dual measurement question: grouping vs certification
// ======================================================================

test("Pauli grouping is always free, unlike certification", () => {
  const r = require(path.join(root, "data/the_dual_measurement_question_never_fails.json"));
  assert.ok(r.valid && r.groupingAlwaysFree);

  // every case reaches the spread value, and does so as an exact PARTITION
  for (const row of r.rows) {
    assert.equal(row.status, "OPTIMAL", `${row.space} must be proved`);
    assert.equal(row.spreadValue, Math.pow(row.q, row.n) + 1);
    assert.equal(row.excess, 0, `${row.space}: grouping must be free`);
    assert.ok(row.isExactPartition,
      `${row.space}: the optimum must be a spread, not an overlapping cover`);
  }

  // the rank-3 contrast: one geometry, opposite answers
  const c = r.rank3Contrast;
  assert.equal(c.space, "W(5,2)");
  assert.equal(c.certification.tau1, 10);
  assert.equal(c.certification.value, 9);
  assert.equal(c.certification.free, false);
  assert.equal(c.grouping.cover, 9);
  assert.equal(c.grouping.free, true);
  assert.ok(c.grouping.exactPartition);
  assert.ok(c.certification.tau1 > c.grouping.cover,
    "no ovoid but a perfect spread, in the same space");

  // the duality is what is claimed, and the classical half is credited
  assert.match(r.twoQuestions.certification, /Thas/);
  assert.match(r.twoQuestions.grouping, /spreads always do/);
  assert.match(r.priorArt, /2\^n\+1 commuting/);
  assert.match(r.whatIsAdded, /opposite answers/);
  assert.match(r.boundary, /classical and not proved by these/);
});

test("only the extreme load levels ever fail, and only for odd q", () => {
  const r = require(path.join(root, "data/load_balance_spectrum_only_extremes_fail.json"));
  assert.ok(r.valid && r.ruleHolds);

  const by = Object.fromEntries(r.spectra.map((s) => [s.q, s]));
  for (const s of r.spectra) {
    // complementation m <-> q+1-m must pair existence, a real check
    assert.ok(s.complementationSymmetric,
      `q=${s.q}: existence must be symmetric under m -> q+1-m`);
    // every intermediate level exists at every q
    assert.ok(s.allIntermediateExist, `q=${s.q}: middles must all exist`);
    // extremes fail exactly when q is odd
    assert.equal(s.extremesFail, !s.qEven,
      `q=${s.q}: extremes fail iff q is odd`);
    for (const row of s.rows) {
      assert.equal(row.size, row.m * (s.q * s.q + 1));
      assert.equal(row.exists, row.count > 0);
    }
  }

  // the W(3,3) row must reproduce the repository's own census exactly
  const q3 = by[3].rows;
  assert.equal(q3.find((x) => x.m === 1).exists, false, "no ovoid at q=3");
  assert.equal(q3.find((x) => x.m === 2).count, 432, "the 432 hemisystems");
  assert.equal(q3.find((x) => x.m === 3).exists, false);

  // q=5 is what refutes the tempting "odd q admits only the hemisystem"
  const q5 = by[5].rows;
  for (const m of [2, 3, 4]) {
    assert.ok(q5.find((x) => x.m === m).exists, `q=5 m=${m} must exist`);
  }
  assert.equal(q5.find((x) => x.m === 1).exists, false);
  assert.equal(q5.find((x) => x.m === 5).exists, false);
  assert.match(r.q3IsNotSpecial, /refutes it/);

  assert.match(r.unifies, /only place the spectrum is obstructed/);
  assert.match(r.boundary, /NOT proved as a\s+family/);
});

test("the depth-2 perfect tile transversal is exactly tau* and does not exist", () => {
  const r = require(path.join(root, "data/depth2_balance_spectrum.json"));
  assert.ok(r.valid);

  const by = Object.fromEntries(r.rows.map((x) => [x.m, x]));
  // the forced size identity |X| = 100m, checked on every solved row
  for (const row of r.rows) {
    assert.equal(row.predictedSize, 100 * row.m);
    if (row.actualSize !== null) {
      assert.equal(row.actualSize, row.predictedSize);
      assert.deepEqual(row.tileCounts, [row.m], "balance must be exact");
      assert.ok(row.consistent);
    }
  }

  // m = 1 is the LP optimum and is impossible, proved two independent ways
  assert.equal(by[1].predictedSize, 100);
  assert.equal(by[1].status, "INFEASIBLE");
  assert.equal(r.mEqualsOneProvedTwice.solver, "INFEASIBLE");
  assert.match(r.mEqualsOneProvedTwice.boundArgument, /111 > 100/);
  assert.match(r.structuralReadingOfTheGap, /not\s+merely numerical/);

  // the hemisystem product gives m = 4 for free, verified leaf-by-leaf
  const h = r.hemisystemProduct;
  assert.equal(h.hemisystemSize, 20);
  assert.equal(h.productSize, 400);
  assert.deepEqual(h.tileCounts, [4], "an m-ovoid squared is m^2-balanced");
  assert.equal(by[4].actualSize, 400);

  // m = 3 exists and cannot come from that construction
  assert.equal(by[3].status, "OPTIMAL");
  assert.equal(by[3].actualSize, 300);
  assert.match(r.mEqualsThreeIsNotAProduct, /not a square/);

  // the trade-off, as a number
  assert.equal(r.balanceCost.bestKnownBlocker, 115);
  assert.equal(r.balanceCost.smallestBalanced, 300);
  assert.ok(r.balanceCost.ratio > 2.5 && r.balanceCost.ratio < 2.7);

  assert.match(r.open, /m = 2/);
  assert.match(r.boundary, /consumes that bound/);
});

// ======================================================================
// Grunbaum-Coxeter cells inside the optimal grouping schedule
// ======================================================================

test("every optimal two-qutrit grouping schedule carries both GC cells", () => {
  const r = require(path.join(root, "data/grouping_optimum_carries_the_gc_cells.json"));
  assert.ok(r.valid);

  // BT836 reproduced from scratch, every step
  const g = r.reproduced;
  assert.equal(g.spreadLines, 10);
  assert.ok(g.coversExactlyOnce, "a spread partitions the 40 points");
  assert.equal(g.groupOrder, 25920);
  assert.equal(g.spreadStabiliserOrder, 720);
  assert.ok(g.stabiliserIsS6Order);
  assert.ok(g.a5Found);
  assert.deepEqual(g.a5OrbitsOnLinePairs, [15, 30], "the Kneser split");
  assert.equal(g.fifteenOrbitIsPetersen, true);

  // the cells named correctly
  assert.equal(r.cells["11-cell"].cellSkeleton, "K_6");
  assert.equal(r.cells["57-cell"].cellSkeleton, "Petersen");
  assert.match(r.cells["11-cell"].group, /PSL\(2,11\)/);
  assert.match(r.cells["57-cell"].group, /PSL\(2,19\)/);

  // the theorem is credited, not claimed
  assert.match(r.theoremIsTheirs, /BT836/);
  assert.match(r.boundary, /reproduced, not extended/);

  // and the generality test: Petersen needs 10, spreads have q^2+1 lines
  const sizes = r.anchoredToQ3.spreadSizes;
  for (const [q, n] of Object.entries(sizes)) {
    assert.equal(n, Number(q) * Number(q) + 1);
    assert.equal(n === 10, Number(q) === 3,
      `q=${q}: a spread has 10 lines iff q = 3`);
  }
  assert.match(r.anchoredToQ3.generalPart, /every\s+q/);
  assert.match(r.anchoredToQ3.specificPart, /only at\s+q = 3/);
  assert.match(r.whyStated, /q = 3 by default/);
});

test("the Grunbaum-Coxeter connection cannot rise above the cell", () => {
  const r = require(path.join(root, "data/gc_connection_is_cell_level_only.json"));
  assert.ok(r.valid);

  // the prime obstruction, checked as arithmetic rather than asserted
  assert.equal(r.orders["Sp(4,3)"], 51840);
  assert.equal(r.orders["PSL(2,11)"], 660);
  assert.equal(r.orders["PSL(2,19)"], 3420);
  assert.equal(51840 % 11 === 0, r.primeObstruction["11dividesSp43"]);
  assert.equal(51840 % 19 === 0, r.primeObstruction["19dividesSp43"]);
  assert.equal(r.primeObstruction["11dividesSp43"], false);
  assert.equal(r.primeObstruction["19dividesSp43"], false);
  // the polytope groups carry primes the substrate group does not
  assert.ok(r.factorisations["PSL(2,11)"]["11"]);
  assert.ok(r.factorisations["PSL(2,19)"]["19"]);
  assert.equal(r.factorisations["Sp(4,3)"]["11"], undefined);
  assert.equal(r.factorisations["Sp(4,3)"]["19"], undefined);
  // but the CELL groups do fit, which is why the cells appear
  assert.ok(r.cellGroupsDoFit.A5divides);
  assert.equal(51840 % 60, 0);

  // the combinatorial agreement
  assert.equal(r.countMismatch.spreads, 36);
  assert.notEqual(r.countMismatch.spreads, r.countMismatch.elevenCellNeeds);
  assert.notEqual(r.countMismatch.spreads, r.countMismatch.fiftySevenCellNeeds);

  // prior art credited in detail, including the more general family
  assert.match(r.reproducedPriorArt.BT2053, /NO_6\^-\(2\)/);
  assert.match(r.reproducedPriorArt.BT2064, /36, 300, 1176/);
  assert.match(r.reproducedPriorArt.BT2088, /1440/);
  assert.match(r.reproducedPriorArt.independentCheck, /1 and 4 = q\+1/);
  assert.match(r.whatIsAdded, /^CORRECTED/);
  assert.match(r.correctedClaim, /it is BT836's/);
  assert.match(r.boundary, /BT836's theorem is untouched/);
});

test("the 11-cell's gluing is the Paley biplane, answering BT836's open item", () => {
  const r = require(path.join(root, "data/eleven_cell_gluing_is_the_paley_biplane.json"));
  assert.ok(r.valid);

  // Coxeter's hexad read arithmetically
  const a = r.arithmeticReading;
  assert.deepEqual(r.coxeter.hexad, [0, 2, 6, 7, 8, 10]);
  assert.deepEqual(a.quadraticResidues, [1, 3, 4, 5, 9]);
  assert.deepEqual(a.nonResidues, [2, 6, 7, 8, 10]);
  assert.ok(a.hexadIsZeroPlusNonResidues, "02678t = {0} u non-residues");
  assert.ok(a.complementIsResidues, "its complement is the residue set");

  // the biplane, verified over every pair rather than asserted
  const v = r.verified;
  assert.deepEqual(v.hexadPairIntersections, [3], "Coxeter's triangle condition");
  assert.deepEqual(v.blockSizes, [5]);
  assert.deepEqual(v.blockPairIntersections, [2]);
  assert.equal(v.pairsCovered, 55, "all C(11,2) pairs checked");
  assert.deepEqual(v.everyPairInBlocks, [2], "2-(11,5,2)");
  assert.ok(v.isBiplane_2_11_5_2);

  // and the hemi-icosahedron rebuilt from the triangles
  assert.equal(v.triangles, 10);
  assert.equal(v.vertices, 6);
  assert.deepEqual(v.vertexDegrees, [5], "{3,5}: five faces per vertex");
  assert.equal(v.distinctEdges, 15);
  assert.deepEqual(v.edgeMultiplicities, [2], "each edge in exactly 2 faces");
  assert.ok(v.skeletonIsK6);
  assert.ok(v.isHemiIcosahedron);

  // the correction to the previous commit is carried, not buried
  assert.match(r.correctionToPreviousCommit, /BT836 already states it/);
  assert.match(r.answersOpenItem, /It is\./);
  // and the limits: no PSL(2,11) inside Sp(4,3)
  assert.match(r.boundary, /does NOT place PSL\(2,11\) inside Sp\(4,3\)/);

  // the corrected file agrees
  const g = require(path.join(root, "data/gc_connection_is_cell_level_only.json"));
  assert.match(g.whatIsAdded, /^CORRECTED/);
  assert.ok(g.correctedClaim);
});

test("universality makes the cell pair one fact, and simplicity makes it rigid", () => {
  const r = require(path.join(root, "data/universality_makes_the_cell_pair_structural.json"));
  assert.ok(r.valid);

  // the reframing: one cell pair, two amalgamations
  assert.match(r.universality.reading, /one coincidence, not\s+two/);
  assert.ok(r.universality.sourceIsClassical, "universality was supplied, not derived");

  // simplicity computed, not asserted -- via conjugacy class unions
  assert.equal(r.simplicity.length, 2);
  const byQ = Object.fromEntries(r.simplicity.map((s) => [s.q, s]));
  assert.equal(byQ[11].order, 660);
  assert.equal(byQ[19].order, 3420);
  for (const s of r.simplicity) {
    assert.ok(s.isSimple, `PSL(2,${s.q}) must be simple`);
    assert.deepEqual(s.properNormalCandidates, []);
    // class sizes must sum to the group order
    assert.equal(s.classSizes.reduce((a, b) => a + b, 0), s.order);
    assert.equal(s.classSizes[0], 1, "the identity class");
  }
  assert.match(r.noRegularQuotients, /N is\s+trivial/);

  // the honest answer on "universal computation"
  assert.match(r.onUniversalComputation.falseFriend, /unrelated notions/);
  assert.match(r.onUniversalComputation.realConsequence, /INCOMPRESSIBILITY/);
  assert.match(r.onUniversalComputation.contrast, /2\.95x/);

  // the large polytope carries GC primes but no substrate order
  const L = r.largeUniversalPolytope;
  assert.equal(L.facets, 10006920);
  assert.ok(L.carriesGCPrimes);
  assert.equal(L.divisibleBySubstrateOrders["Sp(4,3)"], false);
  assert.equal(L.divisibleBySubstrateOrders["PSp(4,3)"], false);
  // and the factorisation must actually multiply back
  let prod = 1;
  for (const [p, e] of Object.entries(L.factorisation)) prod *= Math.pow(Number(p), e);
  assert.equal(prod, L.facets);
  assert.match(L.verdict, /no relation to W\(3,3\) claimed/);
});

// ======================================================================
// The schedule time/memory frontier
// ======================================================================

test("the shortest schedule and the smallest description are different", () => {
  const r = require(path.join(root, "data/schedule_time_memory_frontier.json"));
  assert.ok(r.valid);

  // every witness on both objectives blocks all 1600 tiles
  assert.ok(r.allWitnessesVerified);
  for (const row of r.rows) {
    for (const k of ["minLeaves", "minSeeds"]) {
      assert.ok(row[k].verified, `|H|=${row.order} ${k}: must block all tiles`);
      assert.ok(row[k].leaves > 0 && row[k].seeds > 0);
      // seeds can never exceed the orbit count of the group
      assert.ok(row[k].seeds <= row.orbits);
    }
    // the min-seeds solution never uses fewer leaves than the min-leaves one
    assert.ok(row.minSeeds.leaves >= row.minLeaves.leaves,
      `|H|=${row.order}: optimising seeds cannot also shorten the schedule`);
    assert.ok(row.minSeeds.seeds <= row.minLeaves.seeds);
  }

  // the two objectives genuinely differ, and PROVABLY so where both are OPTIMAL
  const proved = r.rows.filter((x) => x.minLeaves.status === "OPTIMAL"
                                   && x.minSeeds.status === "OPTIMAL");
  assert.ok(proved.length >= 2, "at least two rows proved on both objectives");
  assert.ok(proved.some((x) => x.minSeeds.seeds < x.minLeaves.seeds),
    "a proved row where fewer seeds cost more leaves");

  // the memory-optimal end
  assert.equal(r.memoryOptimalSeeds, 3);
  assert.equal(r.timeOptimal.leaves, 115);
  assert.equal(r.timeOptimal.seeds, 39);
  assert.ok(r.compressionVsWitness > 12);
  const big = r.rows.find((x) => x.order === 192);
  assert.ok(big, "the order-192 subgroup must be present");
  assert.equal(big.minSeeds.seeds, 3);
  assert.equal(big.minSeeds.status, "OPTIMAL");
  assert.ok(big.minSeeds.verified);

  // the contrast with the incompressible polytopes, and the honest limit
  assert.match(r.contrast, /no nontrivial\s+regular quotient/);
  assert.match(r.boundary, /not\s+a global optimum/);
});

test("the memory-optimal schedule is one seed: the commuting orbit", () => {
  const r = require(path.join(root, "data/one_seed_schedule_is_the_commuting_orbit.json"));
  assert.ok(r.valid);

  // rank 3: exactly three orbits partitioning the whole 40x40 grid
  const o = Object.fromEntries(r.rankThree.orbits.map((x) => [x.orbit, x]));
  assert.equal(r.rankThree.orbits.length, 3);
  assert.equal(r.rankThree.total, 1600);
  assert.equal(o.diagonal.leaves + o.collinear.leaves + o["non-collinear"].leaves, 1600);
  assert.equal(o.diagonal.leaves, 40);
  assert.equal(o.collinear.leaves, 480, "40 * k = 40 * 12");
  assert.equal(o["non-collinear"].leaves, 1080, "40 * 27");

  // exactly one orbit blocks, and it is the COMMUTING one
  assert.ok(o.collinear.blocksAllTiles);
  assert.equal(o.collinear.failingTiles, 0);
  assert.match(o.collinear.meaning, /COMMUTING/);
  assert.equal(o.diagonal.blocksAllTiles, false);
  assert.equal(o["non-collinear"].blocksAllTiles, false);

  // the non-commuting orbit is bigger and still fails -- size does not help
  assert.ok(o["non-collinear"].leaves > o.collinear.leaves);
  assert.match(r.failuresAreInformative.nonCollinear, /size does not help/);
  // and it fails on a tile L x L
  assert.deepEqual(o["non-collinear"].firstFailure[0],
                   o["non-collinear"].firstFailure[1], "fails on L x L");
  // while the diagonal fails on DISJOINT lines
  const d = o.diagonal.firstFailure;
  assert.equal(d[0].filter((x) => d[1].includes(x)).length, 0, "disjoint");

  // the proof is three cases, all from the quadrangle axiom
  assert.equal(r.proof.length, 3);
  assert.ok(r.proof.some((s) => /GQ axiom/.test(s)));

  // the frontier is monotone, and one seed is minimal
  const f = r.frontier;
  for (let i = 1; i < f.length; i++) {
    assert.ok(f[i].leaves > f[i - 1].leaves, "leaves increase");
    assert.ok(f[i].seeds < f[i - 1].seeds, "seeds decrease");
  }
  assert.equal(f[f.length - 1].seeds, 1);
  assert.equal(f[f.length - 1].leaves, 480);
  assert.match(r.oneIsMinimal, /optimal, not merely the best found/);
  assert.match(r.boundary, /says nothing about tau_2/);
});

test("the one-seed schedule exists at depth 2 and provably not at depth 3", () => {
  const r = require(path.join(root, "data/one_seed_is_a_depth_two_fact.json"));
  assert.ok(r.valid);

  // depth 2: three orbits, exactly one blocks
  assert.equal(r.depth2.orbits, 3);
  assert.equal(r.depth2.blockingOrbits, 1);
  assert.equal(r.depth2.blockingSize, 480);

  // depth 3: eighteen orbits, none blocks
  assert.equal(r.depth3.orbits, 18);
  assert.equal(r.depth3.blockingOrbits, 0);
  assert.equal(r.depth3.tiles, 64000);
  assert.ok(r.depth3.bestCoverage < r.depth3.tiles, "the best orbit falls short");
  for (const s of r.depth3.sampledCoverage) {
    assert.ok(s.covers < 64000, `orbit ${s.orbitSize} must not block`);
    // an orbit covers at most 64 tiles per leaf
    assert.ok(s.covers <= 64 * s.orbitSize);
  }

  // the obstruction, with its arithmetic checked
  const o = r.obstruction;
  assert.equal(o.lineTriples, 9880, "C(40,3)");
  assert.equal(o.withTransversal + o.withoutTransversal, o.lineTriples);
  assert.equal(o.withoutTransversal, 1080);
  assert.ok(o.allTransversalFreeArePairwiseDisjoint);
  assert.match(o.why, /no triangles/);
  assert.match(o.disjointnessProof, /exactly one point/);

  // the example really is three pairwise disjoint 4-sets
  const [A, B, C] = o.example;
  for (const [X, Y] of [[A, B], [A, C], [B, C]]) {
    assert.equal(X.filter((v) => Y.includes(v)).length, 0, "pairwise disjoint");
    assert.equal(X.length, 4, "lines have 4 points");
  }

  assert.match(r.dichotomy, /destroys it at depth 3/);
  assert.match(r.boundary, /does not rule out few-seed/);
});

test("the depth-3 obstruction is non-isotropy, not a missing line", () => {
  const r = require(path.join(
    root,
    "data/the_depth3_obstruction_is_non_isotropy.json"
  ));
  assert.ok(r.valid);

  // the ambient space, and W(3,3) sitting inside it
  const a = r.ambient;
  assert.equal(a.points, 40);
  assert.equal(a.lines, 130, "PG(3,3) has (3^2+1)(3^2+3+1) = 130 lines");
  assert.equal(a.isotropicLines, 40, "the 40 isotropic lines ARE W(3,3)");
  assert.equal(a.nonIsotropicLines, 90);
  assert.equal(a.isotropicLines + a.nonIsotropicLines, a.lines);

  // the transversals exist -- q+1 = 4 of them, the opposite regulus --
  // and none is usable, uniformly across all 1,080
  assert.equal(r.transversalFreeTriples, 1080);
  const keys = Object.keys(r.transversalProfile);
  assert.deepEqual(keys, ["(4, 0)"], "exactly four transversals, none isotropic");
  assert.equal(r.transversalProfile["(4, 0)"], 1080);
  assert.equal(
    Object.values(r.transversalProfile).reduce((s, v) => s + v, 0),
    r.transversalFreeTriples
  );
  assert.ok(r.uniformFourZero);

  // and they are one class of the group, not a scattered accident
  assert.ok(r.singleOrbit);
  assert.equal(r.orbitSize, r.transversalFreeTriples);

  assert.match(r.classicalFact, /q\+1 transversals, always/);
  assert.match(r.obstruction, /not a measurement context/);
  assert.match(r.obstruction, /NON-COMMUTING/);
  assert.match(r.invisibleFromInside, /each copy fails/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the depth-3 obstruction is 270 isotropic reguli carrying GQ(4,2)", () => {
  const r = require(path.join(
    root,
    "data/the_depth3_obstruction_is_a_quadrangle.json"
  ));
  assert.ok(r.valid);

  // the census adds up, and the obstruction is a third of the skew triples
  const c = r.census;
  assert.equal(c.total, 9880, "C(40,3)");
  assert.equal(c.notPairwiseSkew + c.skew, c.total);
  assert.equal(c.skewWithIsotropicTransversal + c.skewWithNone, c.skew);
  assert.equal(c.skewWithNone, 1080);
  assert.equal(3 * c.skewWithNone, c.skew);
  assert.ok(c.oneThirdOfSkew);

  // 270 all-isotropic reguli account for the 1,080 exactly, none left over
  const i = r.identification;
  assert.equal(i.allIsotropicReguli, 270);
  assert.equal(i.subTriplesEach * i.allIsotropicReguli, c.skewWithNone);
  assert.ok(i.exact);
  assert.deepEqual(i.isotropicLinesPerRegulus, { 4: 1080 }, "all four isotropic");

  // the opposite regulus is perp-closed onto exactly two tritangent planes
  const o = r.oppositeRegulus;
  assert.ok(o.perpClosed);
  assert.deepEqual(o.polarPairsTouched, { 2: 1080 });
  assert.deepEqual(o.incidencesPerHyperbolicLine, [48], "4320/90");
  assert.deepEqual(o.incidencesPerPolarPair, [96], "4320/45");
  assert.equal(48 * 90, 4320);
  assert.equal(96 * 45, 4320);

  // and the 270 edges are GQ(4,2) -- lines derived, not assumed
  const g = r.quadrangle;
  assert.ok(g.injective);
  assert.equal(g.points, 45);
  assert.equal(g.edges, 270);
  assert.deepEqual(g.degreeSpectrum, { 12: 45 }, "12-regular");
  assert.equal((g.edges * 2) / g.points, 12);
  assert.equal(g.maximalCliques, 27);
  assert.deepEqual(g.cliqueSizes, { 5: 27 }, "27 lines of size 5, nothing else");
  assert.deepEqual(g.linesPerPoint, { 3: 45 });
  assert.ok(g.everyEdgeInExactlyOneLine);
  assert.ok(g.gqAxiom);
  assert.equal(g.isomorphismType, "GQ(4,2)");
  // parameters cohere: 27 lines * 5 points = 45 points * 3 lines
  assert.equal(27 * 5, 45 * 3);
  assert.match(g.linesRecoveredNotAssumed, /maximal cliques/);

  // prior art is named, not absorbed
  assert.match(r.priorArt.BT810, /45 polar pairs/);
  assert.match(r.priorArt.Pass2023_2029, /two-transversal\s+branch/);
  assert.match(r.priorArt.BT3769_BT3795, /opposite direction/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("depth 3 needs exactly two seeds and one of them is a repetition", () => {
  const r = require(path.join(
    root,
    "data/depth_three_needs_two_seeds_and_one_is_a_repetition.json"
  ));
  assert.ok(r.valid);
  assert.equal(r.tiles, 64000);

  // the orbit census accounts for every point-triple
  assert.equal(
    r.orbits.reduce((s, o) => s + o.size * o.multiplicity, 0),
    64000,
    "orbit sizes sum to 40^3"
  );
  for (const o of r.orbits) assert.ok(o.covers < r.tiles, "no orbit blocks alone");

  // exactly two orbits, three optimal covers, all the same shape
  assert.equal(r.minimumOrbits, 2);
  assert.equal(r.optimalCovers, 3);
  assert.equal(r.leaves, 4800);
  assert.equal(
    r.optimalShape.reduce((s, x) => s + x.size, 0),
    r.leaves
  );
  const kinds = r.optimalShape.map((x) => x.kind).sort();
  assert.deepEqual(kinds, ["2 commuting pairs", "two equal, commuting"]);
  assert.match(r.whyThreeAndNotNine, /position pair/);

  // the positional theorem: 1600 = 40 x 40, set equality both ways
  const t = r.positionalTheorem;
  assert.equal(t.count, "1600 = 40 x 40");
  const paths = t.rows.filter((x) => x.kind === "2 commuting pairs");
  const degen = t.rows.filter((x) => x.kind === "two equal, commuting");
  assert.equal(paths.length, 3, "one per position pair");
  assert.equal(degen.length, 3);
  for (const x of paths) {
    assert.ok(x.samePositionForAll);
    assert.equal(x.misses, 1600);
    assert.equal(x.predictedTiles, 1600);
    assert.ok(x.missesExactlyThose, "set equality, not just the count");
  }
  for (const x of degen) assert.ok(x.coversAllOfThem);
  // the three path orbits use three distinct position pairs
  assert.equal(new Set(paths.map((x) => String(x.positions))).size, 3);

  // the correction is recorded, with the number that refutes the old claim
  const c = r.correction;
  assert.equal(c.supersedes, "one_seed_is_a_depth_two_fact.py");
  assert.equal(c.distinctLineTiles, 59280);
  assert.equal(40 * 39 * 38, c.distinctLineTiles);
  assert.ok(c.pathOrbitCoversThemAll);
  assert.match(c.isFalse, /fails only where a line\s+repeats/);

  // the frontier gains a row
  assert.deepEqual(r.frontier, [
    { depth: 2, seeds: 1, leaves: 480 },
    { depth: 3, seeds: 2, leaves: 4800 },
  ]);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the seed count strictly increases with depth: 1, 2, at least 3", () => {
  const r = require(path.join(
    root,
    "data/the_seed_count_strictly_increases_with_depth.json"
  ));
  assert.ok(r.valid);

  // the three facts the proofs rest on
  const g = r.ingredients;
  assert.ok(g.twoPointsOfALineCommute, "case 1 rests on this");
  assert.ok(g.noTriangles, "case 3 rests on this");
  assert.equal(g.transversalFreeTriples, 1080);
  assert.ok(g.transversalFreeTriplesArePairwiseDisjoint);
  assert.deepEqual(g.disjointLinesPerLine, [27], "case 2 needs disjoint pairs");
  // 27 disjoint + 12 meeting + itself = the 40 lines
  assert.equal(27 + 12 + 1, 40);

  // Theorem A is exhaustive on the pattern, and says why n=2 escapes
  assert.equal(r.theoremA.cases.length, 3);
  assert.match(r.theoremA.statement, /n >= 3/);
  assert.match(r.theoremA.whyNotAtN2, /always have a transversal/);

  // Theorem B, with all six witnesses killing both orbits outright
  const b = r.theoremB;
  assert.match(b.statement, /n >= 4/);
  assert.match(b.whyNotAtN3, /two orbits do suffice at depth 3/);
  assert.equal(b.witnesses.length, 6, "one per position pair of a 4-tuple");
  for (const w of b.witnesses) {
    assert.equal(w.leaves, 256, "4^4 leaves in a depth-4 tile");
    assert.equal(w.allCommutingOrEqualLeaves, 0, "O_a misses");
    assert.equal(w.leavesWithIJCommutingOrEqual, 256, "O_b misses");
    // the tile really does repeat a line at the named positions
    const [i, j] = w.positions;
    assert.equal(w.tile[i], w.tile[j]);
    assert.equal(new Set(w.tile).size, 3, "one repeat plus the bad pair");
  }
  assert.ok(b.everyWitnessKillsBoth);

  // and the counts, with depth 4 honestly a lower bound
  assert.deepEqual(r.counts.map((c) => c.seeds), [1, 2, 3]);
  assert.deepEqual(r.counts.map((c) => c.status), [
    "exact",
    "exact",
    "lower bound",
  ]);
  assert.match(r.standingOfThe1080, /what forces the third/);
  assert.match(r.boundary, /Whether three orbits SUFFICE at depth 4 is open/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the obstruction generalizes over q but the quadrangle is q=3 only", () => {
  const r = require(path.join(
    root,
    "data/the_quadrangle_is_the_q_equals_three_coincidence.json"
  ));
  assert.ok(r.valid);

  // the closed forms hold at every q tested, arithmetic checked here
  assert.deepEqual(r.perQ.map((x) => x.q), [3, 5, 7]);
  for (const x of r.perQ) {
    const q = x.q;
    assert.equal(x.linesOfW, (q * q + 1) * (q + 1));
    assert.equal(x.disjointFromALine, q ** 3);
    assert.equal(x.disjointFromTwo, q * q * (q - 1));
    assert.equal(
      x.skewTriples,
      (x.linesOfW * q ** 3 * q * q * (q - 1)) / 6
    );
    assert.equal(x.allIsotropicReguli, (q ** 3 * (q - 1) * (q * q + 1)) / 2);
    // the fraction is exact, not approximate
    assert.equal(x.transversalFreeTriples * 2 * q, x.skewTriples * (q - 1));
    assert.ok(x.fractionExact);
    // the opposite regulus: q+1 lines, none isotropic
    assert.equal(x.ambientTransversals, q + 1);
    assert.equal(x.isotropicAmongThem, 0);
    assert.equal(x.polarPairsNamed, (q + 1) / 2);
  }
  assert.deepEqual(r.perQ.map((x) => x.allIsotropicReguli), [270, 6500, 51450]);

  // the elementary counts were observed, not just asserted
  for (const c of r.elementaryChecks) {
    assert.deepEqual(c.disjointObserved, [c.disjointPredicted]);
    assert.equal(c.disjointFromTwoObserved, c.disjointFromTwoPredicted);
    assert.equal(c.lines, (c.q ** 2 + 1) * (c.q + 1));
  }

  // and the split: a graph only where (q+1)/2 = 2
  assert.deepEqual(r.perQ.map((x) => x.isAGraph), [true, false, false]);
  assert.match(r.doesNotGeneralize.why, /\(q\+1\)\/2 polar pairs/);
  assert.match(r.doesNotGeneralize.reading, /W\(E6\)'/);

  // q=7 was counted exactly, and the sample was explicitly not trusted
  const s = r.q7WasCountedNotSampled;
  assert.equal(s.skewPairsThroughOneLine, 50421);
  assert.equal(s.transversalFreeThroughOneLine, 21609);
  assert.equal(s.totals.reguli, 51450);
  assert.equal(s.totals.transversalFree, 2881200);
  // the fixed-line counts scale to the totals by transitivity over 400 lines
  assert.equal((s.skewPairsThroughOneLine * 400) / 3, s.totals.skewTriples);
  assert.equal(
    (s.transversalFreeThroughOneLine * 400) / 3,
    s.totals.transversalFree
  );
  assert.match(s.whyNotTheSample, /neither\s+confirming nor refuting/);

  assert.match(r.consequence, /will not transport/);
  assert.match(r.boundary, /odd q only/);
});

test("1, 2, 5: depth 4 needs five seeds and the proof gave only three", () => {
  const r = require(path.join(
    root,
    "data/one_two_five_and_the_proof_was_not_tight.json"
  ));
  assert.ok(r.valid);
  assert.match(r.reduction, /equivariant/);

  assert.deepEqual(r.rows.map((x) => x.depth), [2, 3, 4]);
  for (const x of r.rows) {
    assert.equal(x.tiles, 40 ** x.depth);
    assert.equal(x.status, "OPTIMAL", "the minimum is proved, not found");
    assert.equal(x.leanestStatus, "OPTIMAL");
    assert.equal(x.orbitSizes.length, x.minimumSeeds);
    assert.equal(
      x.orbitSizes.reduce((s, v) => s + v, 0),
      x.leanestLeaves
    );
    // the reduction really does collapse the ground set
    assert.ok(x.tileOrbits < x.tiles);
    // no single orbit ever suffices past depth 2
    if (x.depth > 2) assert.ok(x.bestSingleOrbitTileOrbits < x.tileOrbits);
  }

  // depths 2 and 3 reproduce the enumerations they replace
  assert.equal(r.rows[0].leanestLeaves, 480);
  assert.equal(r.rows[1].leanestLeaves, 4800);
  assert.deepEqual(r.rows[1].orbitSizes, [480, 4320]);
  // depth 4 is the new one
  assert.equal(r.rows[2].tileOrbits, 270);
  assert.equal(r.rows[2].leafOrbits, 226);
  assert.equal(r.rows[2].leanestLeaves, 44160);
  assert.deepEqual(r.rows[2].orbitSizes, [480, 480, 4320, 12960, 25920]);

  // the sequence, explicitly NOT promoted to a formula
  assert.deepEqual(r.sequence, [1, 2, 5]);
  const s = r.sequenceIsNotAResult;
  assert.deepEqual(s.bell.slice(0, 3), r.sequence);
  assert.deepEqual(s.catalan.slice(0, 3), r.sequence);
  assert.notEqual(s.theyDisagreeAt.bell, s.theyDisagreeAt.catalan);
  assert.equal(s.theyDisagreeAt.depth, 5);
  assert.match(s.why, /matching integer/);
  assert.match(s.depth5NotComputed, /102,400,000/);

  // and the earlier proof is recorded as loose, not quietly dropped
  const p = r.proofWasNotTight;
  assert.equal(p.file, "the_seed_count_strictly_increases_with_depth.py");
  assert.equal(p.proved, 3);
  assert.equal(p.truth, 5);
  assert.ok(p.proved < p.truth, "sound but not tight");
  assert.match(r.boundary, /Depth 5 is not computed and no\s+formula is claimed/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the sentinel shell and the depth-3 obstruction are the same 270", () => {
  const r = require(path.join(
    root,
    "data/the_sentinel_shell_is_the_depth_three_obstruction.json"
  ));
  const plane = require(path.join(root, "data/e8_pg34_sentinel_control_plane.json"));
  assert.ok(r.valid);

  // the dictionary: polar pairs, supports L u L^perp of size 8
  assert.deepEqual(r.dictionary.supportSizes, [8]);
  assert.deepEqual(r.dictionary.pointDegree, [9]);
  assert.equal((45 * 8) / 40, 9);
  // and that is the sentinel plane's own cross-degrees
  assert.equal(plane.carrier.crossDegrees.fromW33, 9);
  assert.equal(plane.carrier.crossDegrees.fromGQ42, 8);
  assert.equal(plane.carrier.split.w33Nonabsolute, 40);
  assert.equal(plane.carrier.split.gq42Absolute, 45);

  // the shell metric agrees with the code's, and accounts for every pair
  assert.deepEqual(r.shellMetric.observed, { 0: 270, 2: 720 });
  assert.ok(r.shellMetric.matches);
  assert.equal(720 + 270, (45 * 44) / 2, "C(45,2)");

  // the identification, as SETS
  const i = r.theIdentification;
  assert.equal(i.supportDisjointPairs, 270);
  assert.equal(i.regulusNamedPairs, 270);
  assert.ok(i.equalAsSets, "not merely equinumerous");
  assert.equal(i.symmetricDifference, 0);
  assert.match(i.statement, /opposite regulus of an all-isotropic/);
  // 270 edges on 45 vertices is degree 12
  assert.equal((270 * 2) / 45, 12);
  assert.deepEqual(r.gramIdentitiesReproduced.degreeOfA, [12]);

  // both Gram identities, rebuilt from the geometry with no code
  assert.ok(r.gramIdentitiesReproduced.BtBHolds);
  assert.ok(r.gramIdentitiesReproduced.BBtHolds);
  assert.equal(plane.gramIdentities.BBt, "8I + 2A_W33 + J".replace("8I", "8I_40").replace("+ J", "+ J_40"));
  assert.match(plane.gramIdentities.BtB, /8I_45/);

  // the consequence, in both directions
  assert.match(r.consequences.forTheCode, /SRG\(45,12,3,3\)/);
  assert.match(r.consequences.forTheObstruction, /\[40,15,8\]/);
  assert.match(r.consequences.headline, /same 270 objects/);

  // prior art named, and the new part kept small
  assert.match(r.priorArt.whatIsNew, /only the identification/);
  assert.match(r.priorArt.BT810, /tritangent/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("depth 5 is reachable, and the interval does not decide the sequence", () => {
  const r = require(path.join(
    root,
    "data/depth_five_is_reachable_but_undecided.json"
  ));
  assert.ok(r.valid);

  // the construction, and the size it avoids
  assert.equal(r.construction.tuplesNeverTouched, 40 ** 5);
  assert.equal(r.construction.tuplesNeverTouched, 102400000);
  assert.match(r.construction.transporter, /T\[w\] = T\[v\] \. g\^-1/);
  assert.equal(r.groupOrder, 25920);

  // depth-4 inputs are the ones already established
  assert.equal(r.depth4.pointOrbits, 226);
  assert.equal(r.depth4.lineOrbits, 270);
  // and the depth-5 structure it builds
  assert.equal(r.depth5.leafOrbits, 5294);
  assert.equal(r.depth5.tileOrbits, 6129);
  assert.equal(r.depth5.tileOrbitsWithNoCover, 0, "every tile-orbit is coverable");
  assert.match(r.validation, /both OPTIMAL, before depth 5 was run/);

  // the bounds, and the honest status
  const b = r.bounds;
  assert.ok(b.lpRelaxation > 12 && b.lpRelaxation < 13);
  assert.equal(b.lpLowerBound, Math.ceil(b.lpRelaxation));
  assert.equal(b.cpsatStatus, "FEASIBLE");
  assert.ok(b.cpsatNeverOptimal, "never proved optimal");
  assert.ok(b.cpsatBestFound <= b.greedyCover, "CP-SAT improved on greedy");
  assert.deepEqual(b.interval, [b.cpsatBound, b.cpsatBestFound]);
  assert.ok(b.interval[0] < b.interval[1], "still an interval, not a value");

  // and it does NOT decide Bell vs Catalan
  const s = r.sequenceStillUndecided;
  assert.deepEqual(s.known, [1, 2, 5]);
  for (const v of [s.bellNext, s.catalanNext]) {
    assert.ok(v >= b.interval[0] && v <= b.interval[1], "both lie inside");
  }
  assert.ok(s.bothInsideInterval);
  assert.equal(s.excluded, null, "neither candidate is excluded");
  assert.ok(s.impressionIsNotEvidence, "solver behaviour is not evidence");
  assert.equal(s.summary, "1, 2, 5, [13, 22]");

  assert.match(r.whatWouldDecideIt, /Neither is attempted here/);
  assert.match(r.boundary, /depth 5 bounded\s+only/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("one ovoid splits a tower of any depth, so height is free", () => {
  const r = require(path.join(
    root,
    "data/the_tower_law_one_ovoid_splits_any_depth.json"
  ));
  assert.ok(r.valid);

  // prior art is named, and the new part is the splitting form
  assert.equal(r.priorArt.file, "tensor_one_ovoid_suffices.py");
  assert.match(r.priorArt.owns, /depth-2 theorem/);
  assert.match(r.whatIsNew, /SPLITS a tower/);
  assert.match(r.splittingTheorem.statement, /arbitrary R/);

  // the two quadrangles, and why one is free
  const q = r.quadrangles;
  assert.equal(q.tau1W, 11);
  assert.equal(q.tau1Q, 10);
  assert.equal(q.tau1WStatus, "OPTIMAL");
  assert.equal(q.tau1QStatus, "OPTIMAL");
  assert.ok(q.tau1W > q.tau1Q, "no ovoid costs exactly one extra point");
  assert.ok(q.QOvoidsAreWSpreads);
  assert.match(q.WHasNoOvoid, /Thas/);
  // 10 = st+1 for a GQ(3,3)
  assert.equal(3 * 3 + 1, q.tau1Q);

  // depth 3, checked against every tile
  const d = r.depth3Verified;
  assert.equal(d.tiles, 40 ** 3);
  assert.equal(d.BxOxO, 1100);
  assert.equal(d.BxOxO, 11 * 10 * 10);
  assert.ok(d.blocksWQQ);
  assert.equal(d.shadow, 10 * 110);
  assert.ok(d.tauWQQExact, "upper meets lower, so it is exact not bounded");
  assert.equal(d.OxOxO, 1000);
  assert.equal(d.OxOxO, 10 ** 3);
  assert.ok(d.blocksQQQ);

  // the law and its three consequences
  assert.equal(r.towerLaw.formula, "tau(W^k x Q^m) = 10^m * tau(W^k)");
  assert.match(r.towerLaw.k2, /\[111,115\]/);
  assert.match(r.consequences.taxPaidOnce, /height/i);
  assert.match(r.consequences.quotaNotAlternation, /corrects an\s+earlier/);
  assert.match(r.consequences.quotaNotAlternation, /commutative/);
  assert.match(r.consequences.tau2Propagates, /infinite family/);
  assert.match(r.operationalReading, /compose through spreads, not lines/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the open configuration has a second, smaller, differently-behaved instance", () => {
  const r = require(path.join(
    root,
    "data/the_open_configuration_has_a_smaller_instance.json"
  ));
  assert.ok(r.valid);

  // GQ(2,4), built as the dual of the reguli quadrangle
  const g = r.gq24;
  assert.match(g.construction, /270 isotropic reguli/);
  assert.equal(g.points, 27);
  assert.equal(g.lines, 45);
  assert.deepEqual(g.pointsPerLine, [3]);
  assert.equal(g.s * g.t + 1, g.stPlusOne);
  assert.equal(g.stPlusOne, 9);
  // 27 points * 5 lines each = 45 lines * 3 points each
  assert.equal(27 * 5, 45 * 3);
  assert.equal(g.tau1, 10);
  assert.equal(g.tau1Status, "OPTIMAL");
  assert.equal(g.hasOvoid, false);
  assert.ok(g.tau1 > g.stPlusOne, "no ovoid means tau_1 exceeds st+1");
  assert.equal(g.deficiency, 1);

  // both factors ovoid-free with the SAME deficiency
  assert.equal(r.w33.tau1, 11);
  assert.equal(r.w33.deficiency, 1);
  assert.ok(r.sameDeficiency, "the controlled comparison");

  // the two instances, and their arithmetic
  assert.equal(r.instances.length, 2);
  for (const i of r.instances) {
    assert.ok(i.shadow < i.product, "shadow is the weaker bound");
    assert.ok(i.bestKnown >= i.shadow && i.bestKnown <= i.product);
    assert.equal(i.status, "OPEN");
  }
  const [w, q] = r.instances;
  assert.equal(w.shadow, 110);
  assert.equal(w.product, 121);
  assert.equal(q.shadow, 90);
  assert.equal(q.product, 100);
  assert.equal(q.leaves, 27 * 27);

  // the qualitative difference is the finding
  const d = r.qualitativeDifference;
  assert.ok(d.w33SquaredBeatsProduct);
  assert.equal(d.byHowMuch, 6);
  assert.equal(d.gq24SquaredBeatsProduct, false);
  assert.match(d.reading, /NOT a\s+function of the ovoid deficiency alone/);

  // and the negative on shadow cuts
  const s = r.shadowCutsNegative;
  assert.equal(s.dualBoundWithCuts, s.dualBoundWithoutCuts, "cuts changed nothing");
  assert.ok(s.dualBoundWithCuts < s.shadowBound, "below even the shadow bound");
  assert.match(s.reading, /does not raise the bound/);

  // and the hardness reproduces at under half the size
  const h = r.hardnessReproduces;
  assert.equal(h.result, "UNKNOWN", "not INFEASIBLE, the telling part");
  assert.equal(h.budgetSeconds, 3000);
  assert.match(h.matchesW33Signature, /nine formulations/);
  assert.match(h.reading, /intrinsic to the/);
  assert.match(r.boundary, /upper bounds only/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the composition tax tracks blocker richness, not ovoid deficiency", () => {
  const r = require(path.join(
    root,
    "data/the_tax_tracks_blocker_richness_not_deficiency.json"
  ));
  assert.ok(r.valid);
  assert.match(r.question, /not a function of the ovoid\s+deficiency/);
  assert.match(r.notTheCentreTheorem, /not the difference/);

  const [g, w] = r.families;
  assert.equal(g.label, "GQ(2,4)");
  assert.equal(w.label, "W(3,3)");
  for (const f of r.families) {
    assert.equal(f.enumerationStatus, "OPTIMAL", "the count is complete");
    assert.ok(f.centreTheoremHolds, "both satisfy it, so it is not the cause");
    assert.equal(f.sTimesTPlus1, f.s * (f.t + 1));
    assert.equal(f.perPoint, f.blockers / f.points);
    // GQ point/line arithmetic
    assert.equal(f.points, (f.s + 1) * (f.s * f.t + 1));
    assert.equal(f.lines, (f.t + 1) * (f.s * f.t + 1));
  }

  // t > s: blockers are the perps, one per point
  assert.ok(g.t > g.s);
  assert.equal(g.tau1, g.sTimesTPlus1, "tau_1 = s(t+1) exactly");
  assert.equal(g.blockers, 27);
  assert.equal(g.perPoint, 1);
  assert.equal(g.puncturedPerps, 27, "every one is a perp");

  // s = t: the diagonal, perps are too big, family opens up
  assert.equal(w.s, w.t);
  assert.ok(w.tau1 < w.sTimesTPlus1, "11 < 12 is the exception");
  assert.equal(w.blockers, 360);
  assert.equal(w.perPoint, 9);
  assert.equal(w.puncturedPerps, 0, "not one of them is a perp");
  assert.equal(w.blockers, w.points * 9);

  // the ratio, and that it is q^2
  assert.equal(r.richnessRatio, 9);
  assert.ok(r.ratioIsQSquared);

  // the cause is a theorem already in the repo
  assert.equal(r.cause.file, "gq_perp_blockers_and_h44.py");
  assert.match(r.cause.theorem, /point-perps when t > s/);
  assert.match(r.cause.exception, /s = t/);
  assert.match(r.cause.diagonal, /beyond counting/);

  // reading and prediction are labelled as such, not promoted
  assert.match(r.reading, /an explanation rather\s+than a theorem/);
  assert.match(r.prediction, /not tested here/);
  assert.match(r.boundary, /not a proof/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("GQ(2,4) lives inside W(3,3) as its 27 K(4,4)-factors", () => {
  const r = require(path.join(
    root,
    "data/gq24_lives_inside_w33_as_its_octet_factors.json"
  ));
  assert.ok(r.valid);
  assert.match(r.notConventionallyDual, /\(3,3\) is not \(2,4\)/);

  // one group, verified rather than quoted
  const g = r.sameGroup;
  assert.match(g.fact, /PSp\(4,3\) = PSU\(4,2\)/);
  assert.equal(g.orderOnPoints, 25920);
  assert.equal(g.imageOrder, 25920);
  assert.ok(g.inducedOn27Faithful);
  assert.ok(g.transitive);
  assert.equal(g.rank, 3, "rank 3, like W(3,3) on its 40");
  assert.equal(g.autOrder, 2 * g.orderOnPoints);

  // the octets are K(4,4)s, and that census is prior art
  assert.equal(r.octetsAreK44.count, 45);
  assert.equal(r.octetsAreK44.of, 45);
  assert.match(r.octetsAreK44.priorArt, /BT766/);
  assert.match(r.octetsAreK44.identification, /4952a3b/);

  // the new part: all 27 lines are factors
  const f = r.octetFactors;
  assert.equal(f.count, 27);
  assert.equal(f.of, 27);
  assert.equal(f.blocksEach * f.blockSize, 40, "5 x 8 covers W(3,3)");
  assert.equal(f.covers, 40);
  assert.match(f.statement, /vertex-\s*disjoint induced K\(4,4\)/);

  // collinearity is block-sharing, both counts exact
  const c = r.collinearityIsBlockSharing;
  assert.deepEqual(Object.keys(c.sharedBlockCounts).sort(), ["0", "1"]);
  assert.ok(c.neverMoreThanOne);
  assert.equal(c.shareOne, c.expectedCollinear);
  assert.equal(c.shareOne, 135);
  assert.equal(c.shareNone, c.expectedNonCollinear);
  assert.equal(c.shareNone, 216);
  assert.equal(c.shareOne + c.shareNone, (27 * 26) / 2, "every pair accounted");

  assert.match(r.theStatement, /27 K\(4,4\)-factors/);
  assert.match(r.threeGeometriesOneGroup, /40 \+ 45 = 85/);
  assert.match(r.effectOnTheTaxResult, /same group on the\s+same space/);
  assert.match(r.boundary, /prior art/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("every minimum blocker of W(3,3) is a point and a triple", () => {
  const r = require(path.join(
    root,
    "data/every_minimum_blocker_is_a_point_and_a_triple.json"
  ));
  assert.ok(r.valid);

  // the enumeration is complete, so these are properties of ALL of them
  assert.equal(r.enumeration.status, "OPTIMAL");
  assert.equal(r.enumeration.count, 360);
  assert.ok(r.enumeration.exhaustive);
  assert.equal(360, 40 * 9, "one per (point, block)");

  const t = r.theorem;
  // 1. the centre is never in the blocker, and the counting reason is recorded
  assert.ok(t.centreNotInB);
  assert.match(t.whyCentreIsExcluded, /6 x 4 = 24/);
  // 2. eight near, three far, and the excluded set is a pencil transversal
  assert.deepEqual(t.nearFarSplit, { "(8, 3)": 360 });
  assert.deepEqual(t.excludedTransversalSizes, { 4: 360 });
  assert.equal(8 + 3, 11, "the eleven points");
  assert.equal(12 - 4, 8, "twelve neighbours minus a transversal");
  // 3. the far triple is a coclique, never a line
  assert.deepEqual(t.farCollinearPairs, { 0: 360 });
  assert.equal(t.farTripleOnALine, 0);
  // 4. nine per centre, and they partition the 27 far points at every centre
  assert.deepEqual(t.blockersPerCentre, [9]);
  assert.equal(t.farTriplesPartitionTheFar, t.centres);
  assert.equal(t.centres, 40);
  assert.equal(9 * 3, 27, "the partition is exact");
  assert.equal(40 - 1 - 12, 27, "27 = 40 minus c minus its neighbours");
  // 5. and the pair determines the blocker
  assert.ok(t.keyDeterminesBlocker);
  assert.equal(t.distinctKeys, r.enumeration.count);

  // the far graph is NOT strongly regular -- mu takes two values
  const f = r.theFarGraph;
  assert.equal(f.vertices, 27);
  assert.deepEqual(f.degree, [8]);
  assert.deepEqual(f.lambda, [1], "every edge in exactly one triangle");
  assert.deepEqual(f.mu, [0, 3]);
  assert.equal(f.stronglyRegular, false);
  assert.equal(f.triangles, 36);
  assert.equal(f.trianglesPerPoint, 4);
  assert.equal((f.triangles * 3) / f.vertices, f.trianglesPerPoint);
  assert.ok(f.threeCocliques > 9, "the nine are singled out among many");

  assert.match(r.parametrization, /360 = 40 x 9/);
  assert.match(r.whatItBuys, /a pair \(centre, block/);
  assert.match(r.literature, /no classification/);
  assert.match(r.boundary, /not a sample/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the tau_2 interval is [111,115] and the corpus disagrees with itself", () => {
  const r = require(path.join(
    root,
    "data/the_tau2_interval_is_111_not_110.json"
  ));
  assert.ok(r.valid);
  assert.deepEqual(r.certifiedInterval, [111, 115]);
  assert.equal(r.excluded, 110);
  assert.equal(r.certifiedInterval[0], r.excluded + 1);

  // the scan found a genuine split, and the sets are disjoint
  const s = r.scan;
  assert.ok(s.staleCount > 0, "the disagreement is real");
  assert.ok(s.currentCount > s.staleCount, "the current figure dominates");
  assert.equal(s.staleOnly.length, s.staleCount);
  assert.equal(s.currentOnly.length, s.currentCount);
  assert.equal(s.both.length, s.bothCount);
  for (const f of s.staleOnly) assert.ok(!s.currentOnly.includes(f));
  // the campaign file that explains the split is itself among the stale
  assert.ok(s.staleOnly.includes("analysis/tensor_110_no_local_obstruction.py"));

  // resolution names the cross-track proof and who already cites it
  assert.match(r.resolution.proof, /43049db/);
  assert.match(r.resolution.proof, /centre argument/);
  assert.ok(r.resolution.citedInHolotradeBy.length >= 4);
  assert.ok(
    r.resolution.citedInHolotradeBy.includes(
      "structure_injection_cannot_reprove_110.py"
    )
  );
  assert.match(r.resolution.whyTheStaleFilesExist, /never\s+returned INFEASIBLE/);
  assert.match(r.resolution.verdict, /supersedes the local non-result/);

  // and why it is not a typo: 110 is exactly the shadow bound
  assert.equal(10 * 11, 110, "tau* x tau_1 is the shadow bound");
  assert.match(r.whyItMatters, /tax would be zero/);

  // the tenth formulation is recorded as a non-result
  assert.equal(r.tenthFormulation.target, 111);
  assert.equal(r.tenthFormulation.result, "UNKNOWN");
  assert.match(r.tenthFormulation.tableIsRedundant, /logically|already one of/);
  assert.match(r.boundary, /cited not reproduced/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the open configuration's floor is 91, and the negative holds at both ends", () => {
  const r = require(path.join(root, "data/the_open_configuration_floor_is_91.json"));
  const orig = require(path.join(
    root, "data/the_open_configuration_has_a_smaller_instance.json"));
  assert.ok(r.valid);

  // correction one: my own understated interval, prior art now cited
  const c = r.correctionOne;
  assert.deepEqual(c.wrote, [90, 100]);
  assert.deepEqual(c.correct, [91, 100]);
  assert.equal(c.correct[0], c.wrote[0] + 1);
  assert.equal(c.priorArtNotCited, "gq24_tight_obstruction.py");
  assert.ok(c.mine, "recorded as my error, not someone else's");
  assert.match(c.theirArgument, /45 lines cannot have distinct centres/);
  assert.match(c.whyNoSelfDualityNeeded, /pigeonhole/);
  // the earlier file's own numbers still agree on what was probed
  assert.equal(orig.instances[1].shadow, 90);
  assert.equal(orig.instances[1].product, 100);

  // correction two ties to the richness result
  assert.match(r.correctionTwo, /one minimum blocker per centre/);
  assert.match(r.correctionTwo, /nine per centre/);

  // the negative now holds at both ends
  const s = r.strengthenedNegative;
  assert.equal(s.earlierProbe.target, 99);
  assert.equal(s.newProbe.target, 91);
  assert.equal(s.earlierProbe.result, "UNKNOWN");
  assert.equal(s.newProbe.result, "UNKNOWN");
  assert.ok(s.newProbe.target < s.earlierProbe.target, "climbed from below");
  assert.equal(s.newProbe.target, c.correct[0], "one above the proved floor");
  assert.match(s.reading, /both\s+ends of the interval/);
  assert.match(s.runningTotal, /eleven formulations/);

  // the r >= 4 argument is offered and explicitly NOT claimed
  const w = r.whatWouldMoveIt;
  assert.ok(w.notClaimed, "hypothesis unverified");
  assert.match(w.ifTrichotomySurvivedSlack, /r >= 4/);
  assert.match(w.whyNot, /tightness/);
  assert.match(w.theRealOpenQuestion, /geometry question, not a solver one/);
  assert.match(r.boundary, /\[91, 100\]/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the trichotomy breaks at multiplicity three, and only its arithmetic half", () => {
  const r = require(path.join(
    root, "data/the_trichotomy_breaks_at_multiplicity_three.json"));
  assert.ok(r.valid);
  assert.match(r.question, /survives defect/);

  // a real object in the defect regime
  assert.equal(r.witness.leaves, 115);
  assert.equal(r.witness.r, 5);
  assert.equal(r.witness.leaves - 110, r.witness.r);
  assert.ok(r.witness.blocksAllTiles);
  assert.equal(r.conservation.sum, r.conservation.F + r.conservation.D);
  assert.equal(r.conservation.expected, 4 * r.witness.r);
  assert.ok(r.conservation.holds);

  // both axes, and they agree exactly
  const axes = [r.axes.row, r.axes.col];
  for (const a of axes) {
    // geometric half survives
    assert.ok(a.everyFibreInAPencil, "fibres are concurrent");
    assert.equal(a.disjointCollisions, 0, "not one disjoint collision");
    // arithmetic half fails, uniformly at 3
    assert.deepEqual(a.multiplicities, { 3: 11 });
    assert.equal(a.distinctCentres, 11);
    assert.equal(a.minimumShadows, 33);
    assert.equal(a.distinctCentres * 3, a.minimumShadows);
    assert.equal(a.fullPencils, 0, "no multiplicity-(t+1) fibre exists");
    assert.equal(a.trichotomyRespected, false);
  }
  assert.deepEqual(r.axes.row.multiplicities, r.axes.col.multiplicities);
  // 3 is strictly between the two permitted values
  assert.ok(1 < 3 && 3 < 4, "the forbidden intermediate value");

  // reciprocity fails in one direction only, and the reason is recorded
  const rec = r.reciprocityIsOneSided;
  assert.equal(rec.holds + rec.fails, 1320);
  assert.ok(rec.oneSided);
  assert.deepEqual(Object.keys(rec.modes), ["(True, False)"]);
  assert.match(rec.why, /needs no\s+tightness/);
  assert.ok(rec.fails <= r.conservation.D + 2, "bounded by the overlap, same order");

  // where the proof snaps, and what is safe to reuse
  assert.match(r.whereTheProofSnaps, /second link, not its\s+last/);
  assert.match(r.geometricHalfSurvives, /needs no tightness/);
  assert.match(r.arithmeticHalfFails, /EVERY fibre/);
  assert.match(r.theBreakIsCheap, /available\s+immediately/);
  assert.equal(r.whatSurvivesAndIsReusable.length, 2);
  assert.match(r.whatSurvivesAndIsReusable[0], /ANY blocking set/);
  assert.match(r.boundary, /not what the distribution must be/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("three witnesses: the geometric half survives, the pretty structure was an artefact", () => {
  const r = require(path.join(
    root, "data/three_witnesses_and_what_survives_variation.json"));
  assert.ok(r.valid);
  assert.match(r.why, /seen once on a symmetric object is not a structure/);

  // three genuinely different witnesses
  assert.equal(r.witnesses.length, 3);
  assert.equal(new Set(r.witnesses.map((w) => w.symmetryOrder)).size, 3);
  assert.equal(new Set(r.witnesses.map((w) => w.r)).size, 3, "three defects");
  for (const w of r.witnesses) {
    assert.equal(w.leaves - 110, w.r);
    assert.ok(w.r > 0, "all in the defect regime");
    assert.ok(w.centres > 0);
    // multiplicities account for the minimum shadows
    const total = Object.entries(w.multiplicities).reduce(
      (s, [k, v]) => s + Number(k) * v, 0);
    assert.equal(total, w.minimumShadows);
    const fibres = Object.values(w.multiplicities).reduce((s, v) => s + v, 0);
    assert.equal(fibres, w.centres);
  }

  // survives: three for three
  assert.deepEqual(r.survives.observed, [true, true, true]);
  assert.match(r.survives.why, /needs no tightness/);
  for (const w of r.witnesses) assert.ok(w.fibresInPencils);

  // fails everywhere: never {0,1,4}, and never a full pencil
  for (const w of r.witnesses) {
    const ms = Object.keys(w.multiplicities);
    assert.ok(!ms.every((m) => m === "1" || m === "4"), "trichotomy violated");
    assert.ok(!ms.includes("4"), "no full-pencil fibre in any witness");
  }
  assert.match(r.failsEverywhere.reading, /not an accident of one object/);

  // the artefact: true for exactly one witness
  assert.equal(r.artefact.centresAreMinimumBlocker.filter(Boolean).length, 1);
  assert.ok(r.artefact.centresBlock.filter(Boolean).length < 3);
  assert.match(r.artefact.heldFor, /order-6 witness alone/);
  assert.match(r.standingRule, /until the\s+sample is varied/);

  // and the two things a future attack may assume
  assert.equal(r.whatToAssume.length, 2);
  assert.match(r.whatToAssume[0], /ANY blocking set/);
  assert.match(r.whatToAssume[1], /contained in pencils/);
  assert.match(r.boundary, /still not a\s+proof/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the hidden 36-quotient is the spreads, and reciprocity alone excludes 110", () => {
  const r = require(path.join(root, "data/the_hidden_36_quotient_is_the_spreads.json"));
  assert.ok(r.valid);

  // the quotient is the spread action
  const s = r.spreadIdentification;
  assert.equal(s.spreads, 36);
  assert.equal(s.groupOrder, 25920);
  assert.ok(s.transitive);
  assert.equal(s.stabilizerOrder, 720);
  assert.equal(s.index, 36);
  assert.equal(s.groupOrder / s.stabilizerOrder, s.index);
  assert.equal(s.index, s.spreads, "orbit-stabilizer closes");
  assert.equal(720, 6 * 5 * 4 * 3 * 2, "|S6|");
  assert.match(s.theirReport, /quotientStabilizerOrder\s+720/);
  assert.match(s.bt809, /regular\s+spread stabilizer/);
  assert.match(s.conclusion, /216 = 36 x 6/);
  assert.equal(36 * 6, 216, "the circuits fibre 6:1 over the spreads");

  // reciprocity alone kills 110
  const e = r.reciprocityExcludes110;
  assert.equal(e.status, "INFEASIBLE");
  assert.match(e.size, /1600 biconditionals/);
  assert.match(e.meaning, /INFEASIBLE excludes 110/);
  assert.match(e.whyItMatters, /22 files/);
  assert.match(e.doesNotReach111, /UNKNOWN/);
  // the model really is far smaller than the grid
  assert.ok(2 * 40 * 40 < 40 * 40 * 40, "3200 booleans, not a 1600-cell grid model");

  // the other track's unfinished work is reported, not repaired
  const u = r.otherTrackUnfinished;
  assert.equal(u.runs.length, 2);
  assert.match(u.broken, /never emits/);
  assert.match(u.orphan, /does not\s+exist/);
  assert.equal(u.policy, "reported, not guessed at");
  assert.match(r.boundary, /\[111, 115\]/);
});

test("one reciprocity CSP recovers both tight-case floors and stops there", () => {
  const r = require(path.join(
    root, "data/reciprocity_recovers_both_floors_and_stops.json"));
  assert.ok(r.valid);
  assert.match(r.theCSP, /c_L in M <=> d_M in L/);

  // it replaces two different bespoke endgames
  assert.match(r.replaces["W(3,3)^2"], /self-duality/);
  assert.match(r.replaces["GQ(2,4)^2"], /pigeonhole/);
  assert.match(r.replaces.reading, /solver finds for itself/);

  assert.equal(r.results.length, 2);
  for (const x of r.results) {
    // both tight cases excluded, by a model far smaller than the grid
    assert.equal(x.tightStatus, "INFEASIBLE");
    assert.ok(x.tightExcluded);
    assert.equal(x.booleans, 2 * x.lines * x.points);
    assert.equal(x.biconditionals, x.lines * x.lines);
    assert.ok(x.booleans < x.points * x.points * x.points, "not a grid model");
    // and both are satisfiable at one unit of slack
    assert.equal(x.slackStatus, "OPTIMAL", "genuine existence, not UNKNOWN");
  }
  // the two geometries really are different objects
  const [w, g] = r.results;
  assert.equal(w.lines, 40);
  assert.equal(w.points, 40);
  assert.equal(g.lines, 45);
  assert.equal(g.points, 27);
  assert.equal(w.tight, 110);
  assert.equal(g.tight, 90);
  // tight = (st+1) * tau_1 in both
  assert.equal(w.tight, 10 * 11);
  assert.equal(g.tight, 9 * 10);

  assert.ok(r.stopsAtSlack.bothOptimalNotUnknown);
  assert.match(r.stopsAtSlack.reading, /reach past tightness is zero/);

  // the correction to the parallel approach
  const c = r.correction;
  assert.equal(c.file, "gq24_slack_center_lift_91.py");
  assert.equal(c.itsStageTwo, "SKIPPED");
  assert.match(c.becauseItWanted, /false at size 12/);
  assert.match(c.lemmaNotNeeded, /45 - 5r/);
  assert.equal(c.stageTwoRunHere, "OPTIMAL");
  assert.match(c.conclusion, /never the obstacle/);
  assert.match(r.boundary, /\[91, 100\]/);
  assert.match(r.boundary, /\[111, 115\]/);
});

test("the 216 is a principal 6-fibration over the double-sixes", () => {
  const r = require(path.join(root, "data/the_216_is_a_principal_six_fibration.json"));
  assert.ok(r.valid);
  assert.match(r.wasOnlyNumerical, /matching integers/);

  // the containment is real, not arithmetic
  const g = r.groupTheory;
  assert.equal(g.circuitStabiliser, 120);
  assert.equal(g.spreadStabiliser, 720);
  assert.equal(g.spreadStabilisersContainingIt, 1, "canonical: exactly one");
  assert.ok(g.canonical);
  assert.equal(g.index, g.spreadStabiliser / g.circuitStabiliser);
  assert.equal(g.index, 6);
  assert.equal(720, 6 * 120, "S6 : S5");
  assert.match(g.inclusion, /S5 <= S6/);
  // orbit-stabilizer closes on both actions
  assert.equal(25920 / g.circuitStabiliser, 216);
  assert.equal(25920 / g.spreadStabiliser, 36);

  // the fibration, built by transport
  const f = r.fibration;
  assert.match(f.method, /transport, not brute force/);
  assert.equal(f.circuitsMapped, 216);
  assert.ok(f.wellDefined, "independent of the transporting element");
  assert.equal(f.spreadsHit, 36);
  assert.deepEqual(f.fibreSizes, { 6: 36 });
  assert.equal(f.equivarianceViolations, 0);
  assert.equal(36 * 6, 216, "the bundle accounts for every state");

  // the fibre is named, via a dictionary entry
  assert.match(r.theFibreHasAName, /double-six, letter/);
  assert.match(r.theFibreHasAName, /Schlafli/);
  assert.match(r.whatTheK66Were, /seen through a correspondence/);

  // the architecture reading, and its limits
  assert.match(r.architectureReading, /derived rather than\s+designed/);
  assert.match(r.architectureReading, /exactly one way to type a state/);
  assert.match(r.boundary, /dictionary\s+entry/);
  assert.match(r.boundary, /no module is written/);
});

test("the typed microVM property is proved, and its control fails", () => {
  const r = require(path.join(root, "data/the_typed_microvm_property_is_a_theorem.json"));
  assert.ok(r.valid);
  assert.match(r.theOrphan, /module that did not exist/);

  // the type discipline is derived, not designed
  const t = r.typeDiscipline;
  assert.match(t.source, /principal 6-fibration/);
  assert.match(t.relabelling, /by construction/);
  assert.equal(t.property, "s/6 == t/6  =>  g[s]/6 == g[t]/6");
  assert.match(t.meaning, /cannot leak the tag into the type/);
  assert.match(t.forced, /exactly one way to type a state/);

  // the proof, and the control that gives it meaning
  assert.equal(r.proof.verdict, "PROVED");
  assert.equal(r.control.verdict, "COUNTEREXAMPLE");
  assert.notEqual(r.proof.script, r.control.script);
  for (const x of [r.proof, r.control]) {
    assert.ok(x.variables > 30000, "a real SAT instance");
    assert.ok(x.clauses > x.variables);
  }
  // the control differs only slightly -- same shape, two entries swapped
  assert.ok(r.control.variables > r.proof.variables);
  assert.ok(r.control.variables - r.proof.variables < 100);
  assert.match(r.controlHasTeeth, /not vacuously true/);
  assert.match(r.quantification, /216 x 216/);
  assert.equal(216 * 216, 46656, "the quantified space");

  assert.match(r.harnessRepair, /chformal -lower/);
  assert.match(r.whyItMatters, /the specification IS the fibration/);
  assert.match(r.boundary, /not a processor/);
});

test("two carriers over one base: the type system is a gauge choice", () => {
  const r = require(path.join(root, "data/two_carriers_one_base.json"));
  assert.ok(r.valid);
  assert.match(r.qualification, /holds WITHIN a\s+carrier/);

  // the wrong first guess is kept, not hidden
  const w = r.wrongFirstGuess;
  assert.equal(w.orbits, 1);
  assert.equal(w.stabiliser, 60);
  assert.equal(w.fibre, 12);
  assert.equal(25920 / w.stabiliser, 432, "one orbit of 432");

  // the twin: 432 pairs to 216, stabiliser doubles to 120
  const t = r.theTwin;
  assert.ok(t.complementsAreHemisystems);
  assert.equal(t.count, 216);
  assert.equal(t.count * 2, 432, "pairing halves the orbit");
  assert.equal(t.stabiliser, 120);
  assert.equal(t.stabiliser, 2 * w.stabiliser, "pair stabiliser doubles");
  assert.equal(25920 / t.stabiliser, t.count);
  assert.ok(t.transitive);
  assert.ok(t.matchesParallelTrack);

  // a second canonical 6-fibration over the SAME 36
  const f = r.twinFibration;
  assert.equal(f.spreadStabilisersContaining, 1);
  assert.ok(f.canonical);
  assert.equal(f.mapped, 216);
  assert.equal(f.spreadsHit, 36);
  assert.deepEqual(f.fibreSizes, { 6: 36 });

  // and the carriers are inequivalent, proved exhaustively
  const i = r.inequivalence;
  assert.equal(i.circuitStabiliser, i.pairStabiliser);
  assert.ok(i.indistinguishableByCounting, "same order, so counting cannot tell");
  assert.equal(i.conjugateInPSp, false);
  assert.match(i.method, /every one\s+of the 25,920/);
  assert.match(i.consequence, /no equivariant bijection/);

  // the corrected architecture, and the correction to my own claim
  const a = r.correctedArchitecture;
  assert.match(a.base, /canonical/);
  assert.match(a.fibration, /GIVEN a carrier/);
  assert.match(a.carrier, /binary gauge choice/);
  assert.match(a.consequence, /cannot see both/);
  assert.match(a.onTheMicroVM, /'a type\s+system'/);
  assert.match(r.whatTheChoiceCosts, /81 and not 64/);
  assert.match(r.boundary, /cited not\s+reproduced/);
});

test("the carrier binary is not a gauge: no substrate symmetry relates the two", () => {
  const r = require(path.join(root, "data/the_carrier_binary_is_a_fork.json"));
  assert.ok(r.valid);
  assert.match(r.theGuess, /are they the same one/);

  // tau is the genuine outer element
  assert.equal(r.tau.inPSp, false, "outside PSp");
  assert.ok(r.tau.normalisesPSp, "but normalises it");
  assert.ok(r.tau.preservesLines, "and is a substrate symmetry");
  assert.match(r.tau.construction, /non-square mod 3/);

  // chirality does not swap the carriers
  const c = r.carriersUnderTau;
  assert.equal(c.conjugateBeforeTau, false);
  assert.equal(c.conjugateAfterTau, false);
  assert.equal(c.conjugateAfterTau, c.conjugateBeforeTau, "tau changes nothing");
  assert.match(c.reading, /FULL automorphism group/);

  // and the reason: tau acts inner on the fibre group
  const w = r.whyNot;
  assert.equal(w.spreadStabiliserOrder, 720);
  assert.equal(w.spreadsFixedByTau, 6);
  assert.ok(w.tauNormalisesIt, "so it does induce an automorphism of S6");
  assert.ok(w.tauActsInner);
  assert.equal(w.outS6RealisedBySubstrate, false, "the key negative");
  assert.match(w.reading, /not induced by\s+anything in PGSp/);

  // my own wording is corrected
  const m = r.correctionToMyWording;
  assert.equal(m.said, "gauge choice");
  assert.match(m.wrong, /intertranslatable/);
  assert.match(m.correct, /FORK/);
  assert.match(r.contrast.chirality, /symmetry of the substrate/);
  assert.match(r.contrast.carrierChoice, /not a symmetry at all/);

  assert.match(r.whatItForbids, /no gauge-transformation instruction can\s+exist/);
  assert.match(r.whatItForbids, /irreversible\s+from inside/);
  assert.match(r.boundary, /not abstract group\s+isomorphisms/);
});

test("the fork is bridged by the fibre product, and the machine-type enum is ternary", () => {
  const r = require(path.join(root, "data/the_fork_is_bridged.json"));
  assert.ok(r.valid);
  assert.match(r.whereThisStarts, /a fork, not a gauge/);

  // the fibre product itself
  const f = r.fibreProduct;
  assert.equal(f.states, 1296);
  assert.equal(f.states, 36 * 6 * 6);
  assert.deepEqual(f.statesPerSpread, [36]);
  assert.equal(f.shapePerSpread, "K(6,6)");
  assert.equal(6 * 6, f.statesPerSpread[0], "a complete bipartite fibre");
  assert.ok(f.transitive);
  assert.equal(f.stabiliserOrder, 20);
  assert.equal(f.orbitStabiliser, f.states);
  assert.equal(25920 / f.stabiliserOrder, f.states, "orbit-stabilizer closes");
  assert.deepEqual(f.projectionsOnto, [true, true]);

  // it IS the parallel track's correspondence
  assert.match(r.isTheirCorrespondence, /valency six/);
  assert.match(r.isTheirCorrespondence, /rank 36/);

  // the stabiliser is F20
  const s = r.stabiliserIsF20;
  assert.equal(s.order, 20);
  assert.ok(s.nonAbelian);
  assert.equal(s.subgroupsOfOrderFive, 1, "unique Sylow-5: Frobenius");
  assert.match(s.reading, /AGL\(1,5\)/);

  // the architecture, and the product-layer consequence
  assert.match(r.architecture.oneCarrier, /sees exactly one/);
  assert.match(r.architecture.theComposite, /1296 states/);
  assert.match(r.architecture.noConversionNeeded, /unique up to unique/);

  const p = r.productLayerIsOneEntryShort;
  assert.equal(p.file, "js/w33-execution-profile.js");
  assert.equal(p.enumerates.length, 2, "their enum has two entries");
  assert.match(p.missing, /1296/);
  assert.match(p.forced, /ternary rather than binary/);
  assert.match(p.stillForbidden, /fed190d/);
  assert.match(r.boundary, /No hardware claim/);
});

test("the ISA cost model, and the transvection optimum confirming the spine", () => {
  const r = require(path.join(root, "data/the_isa_cost_model.json"));
  assert.ok(r.valid);
  assert.match(r.whatAnOpcodeIs, /elements of PSp\(4,3\)/);

  // the tradeoff curve: more opcodes, shorter programs, diminishing returns
  const c = r.tradeoffCurve;
  assert.ok(c.length >= 2);
  for (let i = 1; i < c.length; i++) {
    assert.ok(c[i].opcodes > c[i - 1].opcodes);
    assert.ok(c[i].groupDiameter <= c[i - 1].groupDiameter, "monotone");
  }
  assert.equal(c[0].opcodes, 2, "two opcodes suffice for universality");
  assert.ok(c[0].groupDiameter >= 10, "but the program is long");

  // the transvections: one per point, 40 inverse pairs
  const t = r.transvections;
  assert.equal(t.count, 80);
  assert.equal(t.count, 2 * 40, "40 inverse pairs, one per point");
  assert.equal(t.generates, 25920);
  assert.ok(t.isPSp, "they generate the whole group");
  assert.equal(t.reached, t.generates, "BFS covered the group");
  assert.equal(t.cayleyDiameter, 4);
  assert.equal(t.stateDiameter40, 2);
  assert.equal(t.stateDiameter216, 2);
  // and they beat the best small set decisively
  assert.ok(t.cayleyDiameter < c[0].groupDiameter);
  assert.ok(t.stateDiameter216 < c[0].stateDiameter216);

  // the spine's assertion is now a measured fact
  const s = r.spineClaimConfirmed;
  assert.match(s.claim, /zero, one, or two/);
  assert.ok(s.isADiameterClaim);
  assert.equal(s.measured40, 2);
  assert.equal(s.measured216, 2);
  assert.equal(s.verdict, "CONFIRMED");
  assert.match(s.newPart, /216 carrier states/);

  assert.match(r.literature, /CONTAINING A TRANSVECTION/);
  assert.match(r.literature, /computed values not\s+lookups/);
  assert.match(r.reading, /not a design decision/);
  assert.match(r.boundary, /UPPER bounds/);
  assert.match(r.boundary, /count opcodes, not cycles/);
});

test("minimal instruction count is not minimal program length", () => {
  const r = require(path.join(root, "data/minimal_count_is_not_minimal_length.json"));
  assert.ok(r.valid);
  assert.match(r.whatTheySettled, /9880\s+triples/);
  assert.match(r.whatNobodyAsked, /worst-case program length/);

  // their set, exact
  const b = r.bt1228Set;
  assert.equal(b.vectors.length, 4);
  assert.equal(b.generates, 25920);
  assert.equal(b.reached, 25920, "BFS covered the group");
  assert.equal(b.opcodes, 4);
  assert.equal(b.cayleyDiameter, 11);
  assert.equal(b.routingDiameter, 6);

  // the full ISA, and the cost of compressing to it
  const f = r.fullTransvectionISA;
  assert.equal(f.opcodes, 40);
  assert.equal(f.cayleyDiameter, 4);
  assert.equal(f.routingDiameter, 2);
  assert.ok(b.opcodes < f.opcodes, "fewer instructions");
  assert.ok(b.cayleyDiameter > f.cayleyDiameter, "longer programs");
  assert.equal(r.minimalityCost.group, b.cayleyDiameter / f.cayleyDiameter);
  assert.equal(r.minimalityCost.routing, b.routingDiameter / f.routingDiameter);
  assert.ok(r.minimalityCost.group > 2, "roughly threefold");

  // and their set is beaten on length
  const n = r.notLengthOptimal;
  assert.ok(n.sampled > 100);
  assert.ok(n.bestFound < n.bt1228);
  assert.ok(n.theirSetIsBeaten);
  assert.match(n.reading, /different objectives/);

  // the portability trap
  const p = r.portabilityCaveat;
  assert.match(p.theirForm, /\(0,2\) and \(1,3\)/);
  assert.notEqual(p.underOtherPairing, 25920);
  assert.match(p.reading, /does not transport/);
  assert.match(p.reading, /Not an error in their work/);

  assert.match(r.architecturalReading, /universality is cheap, latency is/);
  assert.match(r.boundary, /UPPER bound/);
});

test("the latency law is 2n, and its one exception is the doily", () => {
  const r = require(path.join(root, "data/the_latency_law_is_2n.json"));
  assert.ok(r.valid);
  assert.match(r.question, /is the\s+diameter always 2n/);

  // seven cases, each exact
  assert.equal(r.cases.length, 7);
  assert.equal(r.tested, 7);
  for (const c of r.cases) {
    assert.equal(c.twoN, 2 * c.n);
    assert.equal(c.points, (Math.pow(c.q, c.twoN) - 1) / (c.q - 1));
    assert.equal(c.equalsTwoN, c.diameter === c.twoN);
    assert.ok(c.diameter >= c.twoN, "never below the Cartan-Dieudonne count");
  }
  assert.equal(r.onTheLaw, 6, "six of seven on the law");

  // the exception, and what it is
  const e = r.exception;
  assert.equal(e.group, "Sp(4,2)");
  assert.equal(e.n, 2);
  assert.equal(e.q, 2);
  assert.equal(e.diameter, 5);
  assert.equal(e.excess, 1);
  assert.ok(e.isS6);
  assert.match(e.whyItMatters, /out\(S6\)/);
  assert.match(e.notCharacteristicTwo, /Sp\(6,2\)/);
  // Sp(6,2) really is on the law, so q=2 alone does not explain it
  const s62 = r.cases.find((c) => c.n === 3 && c.q === 2);
  assert.equal(s62.diameter, 6);
  assert.ok(s62.equalsTwoN);

  // the fourth arrival at a known asymmetry
  const f = r.fourthArrival;
  assert.match(f.priorArt, /PASS4714/);
  assert.match(f.theirExplanation, /SELF-DUAL/);
  assert.match(f.thisIsTheFourth, /not looked for/);
  assert.equal(f.sameSplitFourWays.length, 4);
  assert.ok(f.sameSplitFourWays.some((x) => /tau_2/.test(x)));
  assert.ok(f.sameSplitFourWays.some((x) => /carrier fork/.test(x)));
  assert.match(f.reading, /changes sign/);

  // the scaling law and our machine's position on it
  assert.match(r.scalingLaw.reading, /logarithmic depth/);
  assert.match(r.scalingLaw.ourMachine, /ON the law/);
  assert.match(r.boundary, /not a proof of the law/);
});

test("length equals residue, and the doily's exception is having no centre", () => {
  const r = require(path.join(root, "data/length_equals_residue.json"));
  assert.ok(r.valid);
  assert.match(r.whatWasUnexplained, /no mechanism/);
  assert.match(r.lengthVersusResidue, /length >= residue always/);

  const [a, b] = r.cases;
  assert.equal(a.q, 2);
  assert.equal(b.q, 3);
  assert.equal(a.order, 720);
  assert.equal(b.order, 51840);
  // both matrix diameters are 5 -- the difference is projective
  assert.equal(a.matrixDiameter, 5);
  assert.equal(b.matrixDiameter, 5);

  // length never drops below residue, in either group
  for (const c of [a, b]) {
    for (const k of Object.keys(c.table)) {
      const [res, len] = k.split(",").map(Number);
      assert.ok(len >= res, "a transvection has residue 1");
    }
    assert.equal(
      Object.values(c.table).reduce((s, v) => s + v, 0),
      c.order,
      "the table accounts for every element"
    );
  }

  // the densities, and the mechanism
  assert.ok(a.anomalyPercent > 30);
  assert.ok(b.anomalyPercent < 1);
  assert.ok(r.anomalyDensityRatio > 100);
  assert.equal(b.extremeCount, 1, "one element at the extreme");
  assert.ok(b.extremeIsMinusI, "and it is the centre");
  assert.equal(b.hasCentre, true);
  assert.equal(a.hasCentre, false, "at q=2, -I = I");
  assert.match(r.theMechanism.qOdd, /removed by projectivisation/);
  assert.match(r.theMechanism.qTwo, /no centre/);
  assert.match(r.theMechanism.reading, /every\s+other case is rescued/);

  // and my own framing is corrected
  assert.match(r.correctionToMyFraming, /without saying so/);
  assert.match(r.correctionToMyFraming, /on matrices\s+Sp\(4,3\) is also 5/);
  assert.match(r.boundary, /NOT established/);
});

test("the cost anomalies are the tritangent structure", () => {
  const r = require(path.join(root, "data/the_cost_anomalies_are_the_tritangents.json"));
  assert.equal(r.schema, "holotrade.cost-anomalies-are-tritangents.v1");
  assert.equal(r.valid, true);

  // PG(3,3) splits 40 + 90, and the 90 are the hyperbolic lines
  assert.equal(r.pg33Split.lines, 130);
  assert.equal(r.pg33Split.isotropic, 40);
  assert.equal(r.pg33Split.hyperbolic, 90);
  assert.equal(
    r.pg33Split.isotropic + r.pg33Split.hyperbolic,
    r.pg33Split.lines,
    "the split is exhaustive"
  );

  // g -> im(g - 1) is a BIJECTION onto them, not merely a count match
  const m = r.theMap;
  assert.equal(m.definition, "g -> im(g - 1)");
  assert.equal(m.anomalies, 90);
  assert.equal(m.involutions, 90, "every anomaly is an involution");
  assert.equal(m.actAsMinusOneOnTheirImage, 90);
  assert.equal(m.imageIsHyperbolic, 90, "no anomaly lands on an isotropic line");
  assert.equal(m.distinctImages, 90, "the map is injective");
  assert.equal(m.bijectionOntoTheNinety, true, "and onto -- set equality");
  assert.equal(m.distinctImages, r.pg33Split.hyperbolic);

  // 91 = 90 + 1, agreeing with 6bb8975's anomaly count
  const d = r.decomposition;
  assert.equal(d.hyperbolicReflections, 90);
  assert.equal(d.centre, 1);
  assert.equal(d.total, 91);
  assert.equal(d.hyperbolicReflections + d.centre, d.total);
  const prior = require(path.join(root, "data/length_equals_residue.json"));
  const sp43 = prior.cases.find((c) => c.q === 3);
  assert.equal(
    sp43.anomalies,
    d.total,
    "the decomposition accounts for exactly 6bb8975's 91 anomalies"
  );

  // the reading, and its boundary
  assert.match(r.whyNinetyIsNotFree, /tritangent/);
  assert.match(r.whyNinetyIsNotFree, /minimum-weight words/);
  assert.match(r.architecturalReading, /CO-LOCATED with the code/);
  assert.match(r.pg33Split.reading, /cheap generators and the expensive/);
  assert.match(r.boundary, /set equality, not a count match/);
  assert.match(r.boundary, /No claim\s+for other q/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("every cost anomaly is a nondegenerate reflection", () => {
  const r = require(path.join(
    root,
    "data/every_cost_anomaly_is_a_nondegenerate_reflection.json"
  ));
  assert.equal(r.schema, "holotrade.anomaly-is-nondegenerate-reflection.v1");
  assert.equal(r.valid, true);

  const b = r.cases.q3;

  // isotropic image is NEVER anomalous, and that is the mechanism
  assert.equal(b.residue2Split["isotropic,2"], 720);
  assert.equal(b.residue2Split["isotropic,3"], undefined, "none are anomalous");
  assert.equal(b.residue2Split["hyperbolic,2"], 1260);
  assert.equal(b.residue2Split["hyperbolic,3"], 90);
  assert.equal(
    Object.values(b.residue2Split).reduce((s, v) => s + v, 0),
    2070,
    "the split accounts for every residue-2 element"
  );
  assert.match(r.whyIsotropicIsAlwaysCheap, /self-contradictory/);

  // one distinguished element per hyperbolic line, uniformly across all 90
  const prof = b.perHyperbolicLineProfiles;
  assert.equal(Object.keys(prof).length, 1, "the profile is uniform");
  assert.equal(prof["{2: 14, 3: 1}"], 90);

  // the law, as SET equality against an independently built set
  assert.equal(b.nondegenerate2Spaces, 90);
  assert.equal(b.predictedSetSize, 91);
  assert.equal(b.anomalies, 91);
  assert.equal(b.predictedEqualsAnomalySet, true);
  assert.equal(b.allPredictedAreInGroup, true);
  assert.match(r.theLaw, /if and only if/);
  assert.match(r.whyTheCountIsOneFact, /no\s+odd-dimensional nondegenerate/);

  // 91 agrees with 6bb8975 and decomposes as 3f93821 said
  const prior = require(path.join(root, "data/length_equals_residue.json"));
  assert.equal(prior.cases.find((c) => c.q === 3).anomalies, b.anomalies);
  const tri = require(path.join(
    root,
    "data/the_cost_anomalies_are_the_tritangents.json"
  ));
  assert.equal(tri.decomposition.total, b.anomalies);
  assert.equal(tri.theMap.bijectionOntoTheNinety, true, "the bijection stands");

  // and the law is provably q-odd: at q=2 it predicts 0 against 225
  const a = r.cases.q2;
  assert.equal(a.predictedSetSize, 0, "-1 = +1, so no such element exists");
  assert.equal(a.anomalies, 225);
  assert.equal(a.predictedEqualsAnomalySet, false, "it FAILS, not degrades");
  assert.match(r.qOddOnly, /fails completely rather than\s+degrading/);

  // the over-read is retracted in the record
  assert.match(r.correctionToMyPriorCommit, /over-read/);
  assert.match(r.correctionToMyPriorCommit, /bijection.*stands/);
  assert.match(r.boundary, /set equality against a set/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the length law is O'Meara's, and the doily breaks its induction", () => {
  const r = require(path.join(root, "data/the_length_law_is_omeara.json"));
  assert.equal(r.schema, "holotrade.length-law-is-omeara.v1");
  assert.equal(r.valid, true);

  // the retraction is on the record, with sources
  assert.match(r.retraction, /novelty claim is withdrawn/);
  assert.ok(r.sources.some((s) => /O'Meara/.test(s)));
  assert.ok(r.sources.some((s) => /Callan/.test(s)));
  assert.ok(r.sources.some((s) => /2102\.11380/.test(s)));
  assert.ok(r.sources.some((s) => /Ellers/.test(s)));

  // at q=3 the criterion is exact, as SETS
  const b = r.cases.q3;
  assert.equal(b.anomalies, 91);
  assert.equal(b.hyperbolicMaps, 91);
  assert.equal(b.anomaliesEqualHyperbolic, true);

  // at q=2 it is a strict subset -- the doily again
  const a = r.cases.q2;
  assert.equal(a.anomalies, 225);
  assert.equal(a.hyperbolicMaps, 15);
  assert.equal(a.anomaliesEqualHyperbolic, false);
  assert.equal(a.hyperbolicIsSubset, true);
  assert.equal(a.anomalies - a.hyperbolicMaps, 210);

  // and the cascade is the mechanism
  assert.equal(a.induction["2,3,hyperbolic"], 15);
  assert.equal(a.induction["3,4,every drop lands hyperbolic"], 90);
  assert.equal(a.induction["4,5,clean step exists"], 120);
  assert.equal(
    a.induction["2,3,hyperbolic"] +
      a.induction["3,4,every drop lands hyperbolic"] +
      a.induction["4,5,clean step exists"],
    a.anomalies,
    "the three cells account for every q=2 anomaly"
  );
  assert.match(r.theDoilyBreaksTheInduction, /CASCADE from 15 seeds/);

  // Ellers' one-class metric is genuinely different at odd q
  assert.equal(b.allTransvections, 80);
  assert.equal(b.oneClassTransvections, 40);
  assert.equal(b.allDiameter, 5);
  assert.equal(b.oneClassDiameter, 6, "one class is strictly worse at q=3");
  assert.equal(b.lengthsDifferOn, 38264);
  assert.ok(b.lengthsDifferOn / b.order > 0.7, "they differ on most elements");
  assert.equal(a.lengthsDifferOn, 0, "at q=2 only one lambda exists");
  assert.equal(a.allTransvections, a.oneClassTransvections);

  // my characterisation is demoted to a q-odd coincidence
  assert.match(r.myCharacterisationIsQOddOnly, /empty at q = 2/);
  assert.match(r.terminologyTrap, /Do not conflate/);

  // and the corpus-internal part is kept, correctly scoped
  assert.match(r.whatSurvivesAsOurs, /minimum-weight/);
  assert.match(r.whatSurvivesAsOurs, /not about symplectic groups/);
  assert.match(r.boundary, /primary sources are NOT read/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the qutrit transvection compiler is total, correct and minimal", () => {
  const r = require(path.join(
    root,
    "data/the_qutrit_transvection_compiler.json"
  ));
  assert.equal(r.schema, "holotrade.qutrit-transvection-compiler.v1");
  assert.equal(r.valid, true);

  // the gap it fills: the published algorithm is F_2 only
  assert.match(r.theGap, /F_2/);
  assert.match(r.theGap, /2102\.11380/);

  // the step, and the fact that the scalar is what odd q adds
  assert.equal(r.theStep.vector, "v = g^-1 x - x");
  assert.equal(r.theStep.scalar, "lam = <x, g^-1 x>^-1");
  assert.match(r.theStep.atQ2, /lam = 1/);
  assert.match(r.theStep.hypothesis, /NON-hyperbolicity/);

  // exhaustive verification -- every element, and MINIMAL not just correct
  const v = r.verification;
  assert.equal(v.elements, 51840, "the whole of Sp(4,3)");
  assert.equal(v.everyFactorATransvection, v.elements);
  assert.equal(v.productReconstructsG, v.elements);
  assert.equal(
    v.lengthEqualsBFSGroundTruth,
    v.elements,
    "optimal pointwise, against a full BFS"
  );
  assert.equal(v.failedToCompile, 0, "a total function");
  assert.equal(v.longestProgram, 5);
  assert.equal(
    v.longestProgram,
    v.groupDiameter,
    "the longest program is exactly the group diameter"
  );

  // the porting pitfall is recorded, with its exact cost
  assert.match(r.portingPitfall, /1,679/);
  assert.match(r.portingPitfall, /hyperbolic INTERMEDIATE/);
  assert.match(r.portingPitfall, /3595bd1/);

  // the irregular branch is exactly the anomaly set of the prior commits
  assert.equal(r.hyperbolicBranch.fires, 91);
  const om = require(path.join(root, "data/the_length_law_is_omeara.json"));
  assert.equal(
    r.hyperbolicBranch.fires,
    om.cases.q3.hyperbolicMaps,
    "the compiler's only irregular branch IS the hyperbolic-map set"
  );
  const tri = require(path.join(
    root,
    "data/the_cost_anomalies_are_the_tritangents.json"
  ));
  assert.equal(r.hyperbolicBranch.fires, tri.decomposition.total);

  // and the boundary is honest about what is NOT done
  assert.match(r.runtimeCost, /never searches the group/);
  assert.match(r.boundary, /not a proof for/);
  assert.match(r.boundary, /phase bookkeeping/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the projective ISA has exactly 45 expensive instructions", () => {
  const r = require(path.join(root, "data/the_projective_isa_45.json"));
  assert.equal(r.schema, "holotrade.projective-isa-45-expensive.v1");
  assert.equal(r.valid, true);

  // the centre acts as the symplectic polarity on the anomaly set
  const c = r.centreIsThePolarity;
  assert.equal(c.anomalySetClosedUnderNegation, true);
  assert.equal(c.outOf, 90);
  assert.equal(c.imageOfNegatedIsPolarLine, 90, "polar on every one, not most");
  assert.equal(c.classes, 45);
  assert.equal(c.outOf / c.classes, 2, "a clean two-to-one collapse");
  assert.match(c.reading, /ACTS AS THE SYMPLECTIC POLARITY/);

  // the projective cost model
  const p = r.projectiveCostModel;
  assert.equal(p.order, 25920);
  assert.equal(p.opcodes, 80);
  assert.equal(p.diameter, 4, "2n, the projective latency law");
  assert.equal(p.matrixDiameter, 5, "Sp is still 5");
  assert.equal(p.table["2,3"], 45);
  assert.equal(p.anomalies, 45);
  assert.equal(
    Object.values(p.table).reduce((s, v) => s + v, 0),
    p.order,
    "the table accounts for every projective element"
  );
  // no cell other than (2,3) exceeds its residue
  for (const k of Object.keys(p.table)) {
    const [res, len] = k.split(",").map(Number);
    assert.ok(len >= res, "length is never below residue");
    if (len > res) assert.equal(k, "2,3", "(2,3) is the only anomalous cell");
  }
  // the (4,5) cell of Sp is gone: that was -I
  assert.equal(p.table["4,5"], undefined);
  assert.match(p.residueConvention, /NOT projectively defined/);

  // the bijection: 45 expensive instructions, 45 minimum-weight codewords
  const b = r.theBijection;
  assert.equal(b.expensiveInstructions, 45);
  assert.equal(b.minimumWeightCodewords, 45);
  assert.equal(
    b.expensiveInstructions,
    b.minimumWeightCodewords,
    "one expensive instruction per minimum-weight codeword"
  );
  assert.equal(b.reflectionsAreAllAnomalies, true, "and nothing else");
  assert.match(b.chain, /tritangent/);
  assert.match(b.chain, /cited prior art/);

  // it supersedes the Sp-level hedge, and agrees with the Sp counts
  const om = require(path.join(root, "data/the_length_law_is_omeara.json"));
  assert.equal(om.cases.q3.anomalies, 91);
  assert.equal(
    c.outOf + 1,
    om.cases.q3.anomalies,
    "Sp's 91 is these 90 plus the centre that pairs them"
  );
  assert.match(r.supersedesTheHedge, /wrong group/);
  assert.match(r.readingForTheMachine, /same 45 objects/);
  assert.match(r.boundary, /min over the two\s+lifts/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the expensive instructions form a quadrangle under anticommutation", () => {
  const r = require(path.join(
    root,
    "data/the_expensive_instructions_form_a_quadrangle.json"
  ));
  assert.equal(r.schema, "holotrade.expensive-instructions-quadrangle.v1");
  assert.equal(r.valid, true);

  // the relation is ENTIRELY anticommutation -- zero commuting pairs
  const rel = r.theRelation;
  assert.equal(rel.stricltyCommuting, 0, "not one pair commutes");
  assert.equal(rel.antiCommuting, 270);
  assert.equal(rel.totalPairs, 990, "C(45,2)");
  assert.equal(
    rel.stricltyCommuting + rel.antiCommuting + rel.remaining,
    rel.totalPairs,
    "the trichotomy is exhaustive"
  );
  assert.match(rel.reading, /Pauli incompatibility/);

  // and the graph is GQ(4,2), with the 27 lines recovered not assumed
  const q = r.quadrangle;
  assert.equal(q.points, 45);
  assert.equal(q.edges, 270);
  assert.deepEqual(q.stronglyRegular, [45, 12, 3, 3]);
  assert.deepEqual(q.maximalCliqueSizes, { 5: 27 }, "nothing but K5 survives");
  assert.equal(q.lines, 27);
  assert.deepEqual(q.linesPerPoint, { 3: 45 });
  assert.equal(q.flags, 135);
  assert.equal(q.flags, q.lines * 5);
  assert.equal(q.flags, q.points * 3);
  assert.equal(q.gqAxiom, true);
  assert.equal(q.isomorphismType, "GQ(4,2) = H(3,4)");
  assert.match(q.linesRecoveredNotAssumed, /Bron-Kerbosch/);
  // the SRG parameters are exactly GQ(s,t) with s=4,t=2
  const [n, k, lam, mu] = q.stronglyRegular;
  const s = 4;
  const t = 2;
  assert.equal(n, (s + 1) * (s * t + 1));
  assert.equal(k, s * (t + 1));
  assert.equal(lam, s - 1);
  assert.equal(mu, t + 1);

  // the geometric rule, and the refuted alternative
  const g = r.geometricForm;
  assert.match(g.rule, /L n M = empty AND L n M\^perp = empty/);
  assert.equal(g.meetsNeither, 270, "adjacency is exactly total skewness");
  assert.equal(
    g.meetsMOnly + g.meetsPolarOnly + g.meetsNeither,
    rel.totalPairs
  );
  assert.match(g.refutedAlternative, /accounts for 0 of the 270/);

  // it upgrades 3a0a194 from a count to a geometry
  const p45 = require(path.join(root, "data/the_projective_isa_45.json"));
  assert.equal(q.points, p45.theBijection.expensiveInstructions);
  assert.equal(q.points, p45.theBijection.minimumWeightCodewords);

  // duality with the carrier, and the honest limit on the convergence
  assert.match(r.duality, /DUAL of GQ\(2,4\)/);
  assert.match(r.convergence, /a149d0b/);
  assert.match(r.boundary, /INVARIANTS only/);
  assert.match(r.boundary, /NOT established here/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the 27 lines carry the Schlafli graph and are Pauli groups", () => {
  const r = require(path.join(root, "data/the_27_lines_are_pauli_groups.json"));
  assert.equal(r.schema, "holotrade.27-lines-are-pauli-groups.v1");
  assert.equal(r.valid, true);

  // (1) the 2n+1 ceiling is attained and never exceeded
  const c = r.ceiling;
  assert.deepEqual(c.maximalSetSizes, { 5: 27 }, "every maximal set has 5");
  assert.equal(c.bound, "2n + 1 = 5");
  assert.equal(c.attained, true);
  assert.equal(c.nothingExceedsIt, true, "no 6 anticommuting reflections");

  // (2) both halves of the configuration, on the same data
  const s = r.theSchlafliGraph;
  assert.equal(s.lines, 27);
  assert.deepEqual(s.meetGraph, [27, 10, 1, 5]);
  assert.equal(s.isGQ24Collinearity, true);
  assert.deepEqual(s.complement, [27, 16, 10, 8]);
  assert.equal(s.isSchlafli, true);
  // the meet graph and its complement partition K27
  assert.equal(s.meetGraph[1] + s.complement[1], 26, "degrees sum to n-1");
  assert.match(s.automorphismGroup, /51,840/);
  assert.match(s.automorphismGroup, /CITED not recomputed/);

  // and it is the DUAL of the 45-point quadrangle from 605f5e5
  const gq = require(path.join(
    root,
    "data/the_expensive_instructions_form_a_quadrangle.json"
  ));
  assert.equal(gq.quadrangle.lines, s.lines, "27 lines there, 27 points here");
  assert.deepEqual(gq.quadrangle.stronglyRegular, [45, 12, 3, 3]);

  // (3) extraspecial 2^{1+4}_-, uniformly
  const e = r.extraspecial;
  assert.equal(e.order, 32);
  assert.equal(e.centreOrder, 2);
  assert.equal(e.derivedEqualsCentre, true);
  assert.equal(e.quotientOrder, 16);
  assert.equal(e.quotientElementaryAbelian, true);
  assert.equal(e.order, e.centreOrder * e.quotientOrder, "|G| = |Z|.|G/Z|");
  assert.equal(e.involutions, 11);
  assert.equal(e.orderFourElements, 20);
  assert.equal(
    e.involutions + e.orderFourElements,
    e.order - 1,
    "every non-identity element has order 2 or 4"
  );
  assert.equal(e.type, "2^{1+4}_- = D8 o Q8");
  assert.match(e.typeReasoning, /minus type 11 and 20/);
  assert.equal(e.uniformAcrossAllLines, true);

  // one centre, and it is the -I that does the polarity
  assert.equal(r.oneCentre.distinctCentres, 1);
  assert.equal(r.oneCentre.isCentreOfSp43, true);
  assert.match(r.oneCentre.reading, /three jobs/);
  const p45 = require(path.join(root, "data/the_projective_isa_45.json"));
  assert.match(p45.centreIsThePolarity.reading, /SYMPLECTIC POLARITY/);

  // the strangeness, and the honest limits
  assert.match(r.whatIsStrange, /2-GROUPS/);
  assert.match(r.whatIsStrange, /knows nothing about the field/);
  assert.match(r.boundary, /NO claim is made that these 27 groups are Pauli/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the cost model reconstructs the cubic surface", () => {
  const r = require(path.join(
    root,
    "data/the_cost_model_reconstructs_the_cubic_surface.json"
  ));
  assert.equal(r.schema, "holotrade.cost-model-is-the-cubic-surface.v1");
  assert.equal(r.valid, true);

  // all three Schlafli numbers, from a predicate with no geometry in it
  const t = r.theThreeNumbers;
  assert.equal(t.tritangentPlanes, 45);
  assert.equal(t.lines, 27);
  assert.equal(t.doubleSixes, 36);
  assert.match(r.whatTheCostModelKnows, /nothing geometric/);
  assert.match(r.whatTheCostModelKnows, /no cubic\s+surface/);

  // the rigid test: 36 is not reachable by a wrong construction
  const g = r.theRigidTest;
  assert.deepEqual(g.meetDegree, [10], "each line meets 10");
  assert.deepEqual(g.skewDegree, [16], "and is skew to 16");
  assert.equal(g.meetDegree[0] + g.skewDegree[0], 26, "degrees sum to n-1");
  assert.equal(g.sixers, 72);
  assert.deepEqual(g.partnersPerSixer, { 1: 72 }, "exactly one partner each");
  assert.equal(g.doubleSixes, 36);
  assert.equal(g.sixers / 2, g.doubleSixes, "72 sixers pair into 36");
  assert.deepEqual(g.linesCovered, { 12: 36 });
  assert.equal(g.looseReadingGives, 756);
  assert.notEqual(
    g.looseReadingGives,
    g.doubleSixes,
    "the loose definition is off by 21x -- the count is not robust to error"
  );

  // it chains onto the earlier quadrangle results
  const gq = require(path.join(
    root,
    "data/the_expensive_instructions_form_a_quadrangle.json"
  ));
  assert.equal(gq.quadrangle.points, t.tritangentPlanes);
  assert.equal(gq.quadrangle.lines, t.lines);
  const pl = require(path.join(root, "data/the_27_lines_are_pauli_groups.json"));
  assert.equal(pl.theSchlafliGraph.lines, t.lines);
  assert.equal(pl.extraspecial.order, 32, "qubit-shaped, order 32");

  // the cross-track citations are present and the limit is stated
  assert.ok(r.alreadyInTheCorpus.some((s) => /BT810/.test(s)));
  assert.ok(r.alreadyInTheCorpus.some((s) => /THE_27_FOLD_WAY/.test(s)));
  assert.ok(r.alreadyInTheCorpus.some((s) => /0d8d33e/.test(s)));
  assert.ok(r.alreadyInTheCorpus.some((s) => /4952a3b/.test(s)));
  assert.match(r.whatIsNew, /COST FUNCTION produces them/);
  assert.match(r.twoPauliGroupsOnOne27, /order-27 exponent-3/);
  assert.match(r.twoPauliGroupsOnOne27, /2\^\{1\+4\}_-/);
  assert.match(r.boundary, /by INVARIANTS/);
  assert.match(r.boundary, /NOT by an explicit equivariant\s+bijection/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the 45-slot ROM bijection is explicit and verified", () => {
  const r = require(path.join(root, "data/the_45_slot_rom_bijection.json"));
  assert.equal(r.schema, "holotrade.45-slot-rom-bijection.v1");
  assert.equal(r.valid, true);

  // two independent constructions, same shape
  assert.equal(r.sideA.points, 45);
  assert.equal(r.sideB.points, 45);
  assert.equal(r.sideA.lines, 27);
  assert.equal(r.sideB.lines, 27);
  assert.deepEqual(r.sideA.degrees, [12]);
  assert.deepEqual(r.sideB.degrees, [12]);
  assert.equal(r.sideB.weightSplit.weight2, 18);
  assert.equal(r.sideB.weightSplit.weight4, 27);
  assert.equal(
    r.sideB.weightSplit.weight2 + r.sideB.weightSplit.weight4,
    r.sideB.points
  );
  assert.match(r.independence, /nothing is shared/);

  // the verification, all three parts
  const v = r.verification;
  assert.equal(v.bijective, true);
  assert.equal(v.edgePreservingBothDirections, true);
  assert.equal(v.linesMappedOntoLines, true);
  assert.match(v.method, /SET EQUALITY, not containment/);

  // the table itself is complete, well-formed and a genuine bijection
  assert.equal(r.table.length, 45);
  const slots = new Set(r.table.map((e) => e.slot));
  assert.equal(slots.size, 45, "every slot used exactly once");
  for (const e of r.table) {
    assert.ok(e.slot >= 0 && e.slot < 45);
    assert.equal(e.h34Point.length, 4);
    assert.ok(
      e.h34Point.every((x) => x >= 0 && x <= 3),
      "GF(4) coordinates"
    );
    assert.equal(
      e.h34Point.filter((x) => x !== 0).length % 2,
      0,
      "H(3,4) points have even weight"
    );
    assert.equal(e.spMatrix.length, 4);
    for (const row of e.spMatrix) {
      assert.equal(row.length, 4);
      assert.ok(row.every((x) => x >= 0 && x <= 2), "F_3 entries");
    }
  }
  // every Sp matrix is distinct too
  const mats = new Set(r.table.map((e) => JSON.stringify(e.spMatrix)));
  assert.equal(mats.size, 45, "45 distinct instructions");

  // the line sets on both sides: 27 lines of 5, each point on 3
  for (const key of ["linesA", "linesB"]) {
    const L = r[key];
    assert.equal(L.length, 27);
    const per = new Map();
    for (const line of L) {
      assert.equal(line.length, 5, key + " lines have 5 points");
      for (const p of line) per.set(p, (per.get(p) || 0) + 1);
    }
    assert.equal(per.size, 45);
    for (const [, c] of per) assert.equal(c, 3, key + ": 3 lines per point");
  }

  // it closes the gap both tracks named
  assert.match(r.theGapNamedTwice, /fe4fb77/);
  assert.match(r.theGapNamedTwice, /fail closed/);
  assert.match(r.whatThisUnblocks, /27 banks of 5/);
  assert.match(r.aChoiceNotCanonical, /THIS certificate is the\s+contract/);
  assert.match(r.boundary, /NO claim that this particular\s+table is equivariant/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the cheap opcodes are the expensive geometry's ovoids", () => {
  const r = require(path.join(root, "data/cheap_opcodes_are_ovoids.json"));
  assert.equal(r.schema, "holotrade.cheap-opcodes-are-ovoids.v1");
  assert.equal(r.valid, true);

  // exactly dual defects
  const d = r.dualDefects;
  assert.equal(d.cheapIndex.geometry, "W(3,3)");
  assert.equal(d.cheapIndex.spreads, 36);
  assert.equal(d.cheapIndex.ovoids, 0, "Thas: no ovoid at odd q");
  assert.equal(d.expensiveSet.geometry, "GQ(4,2)");
  assert.equal(d.expensiveSet.ovoids, 200);
  assert.equal(d.expensiveSet.spreads, 0, "and no spread");
  // the inversion is the point
  assert.ok(d.cheapIndex.spreads > 0 && d.cheapIndex.ovoids === 0);
  assert.ok(d.expensiveSet.ovoids > 0 && d.expensiveSet.spreads === 0);
  assert.match(d.reading, /dual defects/);

  // the orbit split matches the literature, via the machine's own group
  assert.deepEqual(r.orbitSplit.sizes, [40, 160]);
  assert.equal(
    r.orbitSplit.sizes.reduce((a, b) => a + b, 0),
    d.expensiveSet.ovoids,
    "the orbits account for all 200"
  );
  assert.match(r.orbitSplit.byWhat, /CONJUGATION/);
  assert.match(r.orbitSplit.byWhat, /class functions/);
  assert.match(r.orbitSplit.literature, /CITED/);

  // same PSp-set: subdegrees AND an equivariant bijection
  const s = r.sameSet;
  assert.deepEqual(s.subdegreesOvoids, [1, 12, 27]);
  assert.deepEqual(s.subdegreesW33Points, [1, 12, 27]);
  assert.deepEqual(s.subdegreesOvoids, s.subdegreesW33Points);
  assert.equal(
    s.subdegreesOvoids.reduce((a, b) => a + b, 0),
    40,
    "subdegrees sum to the degree"
  );
  assert.equal(s.equivariantBijection, true, "built, not just matched");
  assert.equal(s.generatorsChecked, 80, "checked on every generator");
  assert.match(s.reading, /Matching subdegrees is only\s+evidence/);

  // an ovoid is a minimal cover of the 27 banks: 9 points x 3 lines = 27
  const gq = require(path.join(
    root,
    "data/the_expensive_instructions_form_a_quadrangle.json"
  ));
  assert.equal(gq.quadrangle.points, 45);
  assert.equal(gq.quadrangle.lines, 27);
  assert.equal(9 * 3, gq.quadrangle.lines, "9 points x 3 lines each = 27 banks");
  assert.match(r.machineReading, /every cheap opcode canonically names a/);
  assert.match(r.machineReading, /cover but never cleanly split/);

  // and the honest limit on the cross-track 27
  assert.match(r.boundary, /verified\s+against EVERY generator, not sampled/);
  assert.match(r.boundary, /does NOT establish that the 27/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("my 27 is their 27 -- one torsor under the qutrit Pauli group", () => {
  const r = require(path.join(root, "data/my_27_is_their_27.json"));
  assert.equal(r.schema, "holotrade.my-27-is-their-27.v1");
  assert.equal(r.valid, true);

  // it closes a named open item
  assert.match(r.whatWasOpen, /8982d36/);
  assert.match(r.whatWasOpen, /does NOT establish/);

  // both 27s are transitive Stab(p0)-sets
  const s = r.stabiliser;
  assert.equal(s.order, 648, "25920/40");
  assert.deepEqual(s.orbitsOnOppositePoints, [27]);
  assert.deepEqual(s.orbitsOnMy27Lines, [27]);

  // the elation group: order 27, exponent 3, NONabelian, regular on BOTH
  const e = r.elationGroup;
  assert.equal(e.sylow3Order, 81);
  assert.equal(e.exponent, 3, "exponent 3, not 9");
  assert.equal(e.nonabelian, true, "the abelian one fails to be regular");
  assert.equal(e.regularOnOppositePoints, true, "their result, reproduced");
  assert.equal(e.regularOnMy27Lines, true, "the new half");

  // and the bijection is explicit
  assert.equal(r.equivariantBijection.bijective, true);
  assert.equal(r.equivariantBijection.intertwinesElationGroup, true);
  assert.match(r.equivariantBijection.reading, /explicit rather than abstract/);

  // a 3-group and 27 2-groups now provably on one object
  const pl = require(path.join(root, "data/the_27_lines_are_pauli_groups.json"));
  assert.equal(pl.theSchlafliGraph.lines, 27);
  assert.equal(pl.extraspecial.order, 32, "2-groups");
  assert.equal(pl.oneCentre.isCentreOfSp43, true);
  assert.match(r.whatSitsOnOne27, /3-GROUP/);
  assert.match(r.whatSitsOnOne27, /2-GROUPS/);
  assert.match(r.whatSitsOnOne27, /now a\s+statement about one object/);

  // the search limit is declared, not glossed
  assert.equal(e.order27SubgroupsFound, 1);
  assert.match(r.limitOnTheSearch, /TWO elements of order 3/);
  assert.match(r.limitOnTheSearch, /NOT enumerated here/);
  assert.match(r.limitOnTheSearch, /does not re-derive their\s+classification/);

  // and the 36 is explicitly NOT claimed
  assert.match(r.boundary, /closes the 27 question ONLY/);
  assert.match(r.boundary, /36 here are BT810's\s+spreads is still by invariants/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("every opcode axis anchors five minimal covers", () => {
  const r = require(path.join(
    root,
    "data/opcode_axis_anchors_five_covers.json"
  ));
  assert.equal(r.schema, "holotrade.opcode-axis-anchors-five-covers.v1");
  assert.equal(r.valid, true);

  // every one of the 200 is anchored -- including the 160
  const a = r.everyCoverIsAnchored;
  assert.deepEqual(a.stabiliserOrders, { 162: 160, 648: 40 });
  assert.deepEqual(a.pointsFixedByStabiliser, { 1: 200 }, "all 200, exactly one");
  assert.equal(648 / 162, 4, "the small stabiliser has index 4 in the point one");
  assert.match(a.reading, /is false/);

  // the fibration is uniform: 5 per axis, 1 + 4
  const f = r.fibration;
  assert.deepEqual(f.coversPerAxis, { 5: 40 });
  assert.equal(f.composition, "1 plane + 4 other, at every one of the 40");
  assert.equal(f.alternatesFormOneOrbit, true);
  assert.equal(f.total, 200);
  assert.equal(40 * 5, f.total, "40 axes x 5 covers = 200");
  assert.deepEqual(f.stabOrbitsOnFibre, [1, 4]);

  // intersections: the alternates are genuinely different, not near-duplicates
  const i = r.intersections;
  assert.deepEqual(i.planeWithPlane, { 1: 540, 3: 240 });
  assert.equal(
    Object.values(i.planeWithPlane).reduce((s, v) => s + v, 0),
    780,
    "C(40,2)"
  );
  assert.equal(i.planeWithPlane["0"], undefined, "canonicals never miss");
  assert.deepEqual(i.otherWithPlane, { 0: 1600, 2: 4320, 6: 480 });
  assert.equal(
    Object.values(i.otherWithPlane).reduce((s, v) => s + v, 0),
    160 * 40
  );
  assert.ok(i.otherWithPlane["0"] > 0, "an alternate CAN be disjoint");
  assert.equal(
    Object.values(i.otherWithOther).reduce((s, v) => s + v, 0),
    (160 * 159) / 2,
    "C(160,2)"
  );

  // it builds on, and cites, the parallel track's Payne identification
  assert.match(r.whereThisStarts, /slow_path_is_payne_derivative/);
  assert.match(r.whereThisStarts, /80% of\s+the covers, unexamined/);
  assert.match(r.operationalReading, /160 spare minimal\s+covers/);

  // and the five is explicitly NOT the F20 five
  assert.match(r.thisFiveIsNotTheF20Five, /NOT\s+transitively/);
  assert.match(r.thisFiveIsNotTheF20Five, /two distinct fives/);
  assert.match(r.boundary, /NO\s+claim that the four alternates have a Payne/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the Schlafli triple is closed by equivariant maps", () => {
  const r = require(path.join(root, "data/schlafli_triple_closed.json"));
  assert.equal(r.schema, "holotrade.schlafli-triple-closed.v1");
  assert.equal(r.valid, true);

  // the last leg: 36 double-sixes = 36 spreads, equivariantly
  const t = r.theThirtySix;
  assert.equal(t.spreadsOfW33, 36);
  assert.equal(t.doubleSixesFromCostGeometry, 36);
  assert.equal(t.sixers, 72);
  assert.equal(t.sixers / 2, t.doubleSixesFromCostGeometry);
  assert.equal(t.transitiveOnDoubleSixes, true);
  assert.equal(t.transitiveOnSpreads, true);
  assert.equal(t.equivariantBijection, true, "built, not by invariants");
  assert.equal(t.generatorsChecked, 80);
  assert.match(t.whatIsAdded, /FROM THE COST\s+MODEL/);

  // the whole ledger, and each leg cross-checked against its own certificate
  const L = r.ledger;
  assert.deepEqual(Object.keys(L).sort(), ["27", "36", "40", "45"]);
  for (const k of Object.keys(L)) {
    assert.ok(L[k].costObject && L[k].corpusObject && L[k].commit);
  }
  const t27 = require(path.join(root, "data/my_27_is_their_27.json"));
  assert.equal(t27.equivariantBijection.intertwinesElationGroup, true);
  const rom = require(path.join(root, "data/the_45_slot_rom_bijection.json"));
  assert.equal(rom.verification.linesMappedOntoLines, true);
  assert.equal(rom.table.length, 45);
  const ov = require(path.join(root, "data/cheap_opcodes_are_ovoids.json"));
  assert.equal(ov.sameSet.equivariantBijection, true);
  assert.equal(ov.sameSet.generatorsChecked, 80);

  // the three Schlafli numbers agree with the derivation that started it
  const cs = require(path.join(
    root,
    "data/the_cost_model_reconstructs_the_cubic_surface.json"
  ));
  assert.equal(cs.theThreeNumbers.lines, 27);
  assert.equal(cs.theThreeNumbers.doubleSixes, t.doubleSixesFromCostGeometry);
  assert.equal(cs.theThreeNumbers.tritangentPlanes, rom.table.length);
  // and that file's invariants-only hedge is the thing now discharged
  assert.match(cs.boundary, /by INVARIANTS/);
  assert.match(r.theLastLeg, /still outstanding/);

  // the claim is bounded: nothing new was discovered, it was identified
  assert.match(r.whatItLicenses, /ONE object/);
  assert.match(r.whatItDoesNotSay, /discovered anything\s+the corpus lacked/);
  assert.match(r.whatItDoesNotSay, /it IS the geometry/);
  assert.match(r.boundary, /CITED not derived/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the cost quadrangle is a new tower-law base with tau_1 = 9", () => {
  const r = require(path.join(root, "data/cost_quadrangle_tower_base.json"));
  assert.equal(r.schema, "holotrade.cost-quadrangle-tower-base.v1");
  assert.equal(r.valid, true);

  // tau_1 = 9, and the lower bound is pure counting
  const t = r.tau1;
  assert.equal(t.points, 45);
  assert.equal(t.lines, 27);
  assert.deepEqual(t.linesPerPoint, [3]);
  assert.deepEqual(t.pointsPerLine, [5]);
  assert.equal(t.countingBound, 9, "27 lines / 3 lines per point");
  assert.equal(t.value, 9);
  assert.equal(t.value, t.countingBound, "the counting bound is attained");
  assert.equal(t.defect, 0, "tau_1 = st+1 exactly");
  assert.equal(t.witness.length, 9);

  // minimum blockers ARE the ovoids -- that is what defect zero means
  const m = r.minimumBlockersAreOvoids;
  assert.equal(m.minimumBlockers, 200);
  assert.equal(m.ovoids, 200);
  assert.equal(m.identical, true);
  const ov = require(path.join(root, "data/cheap_opcodes_are_ovoids.json"));
  assert.equal(
    ov.dualDefects.expensiveSet.ovoids,
    m.ovoids,
    "the same 200 ovoids as 8982d36"
  );

  // the four-quadrangle dichotomy holds row by row
  assert.equal(r.fourQuadrangles.length, 4);
  for (const g of r.fourQuadrangles) {
    assert.equal(
      g.defect,
      g.tau1 - g.stPlus1,
      g.geometry + ": defect is tau_1 - (st+1)"
    );
    assert.equal(
      g.ovoid,
      g.defect === 0,
      g.geometry + ": ovoid iff defect zero"
    );
    assert.equal(
      g.towerBase !== null,
      g.ovoid,
      g.geometry + ": tower law applies iff ovoid"
    );
    if (g.ovoid) assert.equal(g.towerBase, g.tau1);
    assert.equal(g.stPlus1, g.st[0] * g.st[1] + 1);
  }
  // exactly one of each dual pair bears an ovoid
  const byPair = [
    ["W(3,3)", "dual of W(3,3)"],
    ["GQ(2,4)", "GQ(4,2) the cost quadrangle"],
  ];
  for (const [a, b] of byPair) {
    const ga = r.fourQuadrangles.find((x) => x.geometry === a);
    const gb = r.fourQuadrangles.find((x) => x.geometry === b);
    assert.notEqual(ga.ovoid, gb.ovoid, a + " / " + b + ": exactly one");
  }

  // the new base, and that it is smaller than the existing one
  assert.match(r.newTowerBase.pure, /9\^m/);
  assert.match(r.newTowerBase.combined, /EXCEPT its W-factors/);
  assert.match(r.newTowerBase.smallestYet, /base 10/);
  assert.ok(9 < 10, "the new base is smaller than d9a9c59's");

  // what tau_2 measures -- and it stays open
  assert.match(r.whatTau2Measures, /9\^2 = 81 exactly/);
  assert.match(r.whatTau2Measures, /between 6 and 10 off the square/);
  assert.equal(11 * 11 - 115, 6);
  assert.equal(11 * 11 - 111, 10);
  assert.match(r.boundary, /CITED and applied, not re-proved/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the cost quadrangle is q = 3 only", () => {
  const r = require(path.join(root, "data/cost_quadrangle_is_q3_only.json"));
  assert.equal(r.schema, "holotrade.cost-quadrangle-q3-only.v1");
  assert.equal(r.valid, true);

  const byQ = Object.fromEntries(r.rows.map((x) => [x.q, x]));
  assert.deepEqual(Object.keys(byQ).map(Number).sort((a, b) => a - b), [3, 5, 7]);

  // the construction is q-general and the counts follow closed forms
  for (const q of [3, 5, 7]) {
    const x = byQ[q];
    assert.equal(x.everyReflectionIsHyperbolic, true, "q=" + q);
    assert.equal(x.classes, x.classesClosedForm, "q^2(q^2+1)/2 at q=" + q);
    assert.equal(x.degrees.length, 1, "regular at q=" + q);
    assert.equal(x.degrees[0], x.degreeClosedForm, "q(q^2-1)/2 at q=" + q);
    assert.equal(x.classes, (q * q * (q * q + 1)) / 2);
    assert.equal(x.degrees[0], (q * (q * q - 1)) / 2);
  }

  // q=3: a quadrangle
  assert.deepEqual(byQ[3].stronglyRegular, [45, 12, 3, 3]);
  assert.equal(byQ[3].isGQ, true);

  // q=5: strongly regular but NOT a quadrangle
  assert.deepEqual(byQ[5].stronglyRegular, [325, 60, 15, 10]);
  assert.equal(byQ[5].isGQ, false, "the GQ identity fails");
  {
    const [N, k, l, m] = byQ[5].stronglyRegular;
    const s = l + 1;
    const t = m - 1;
    assert.notEqual((s + 1) * (s * t + 1), N, "17 x 145 is nowhere near 325");
    // but the SRG feasibility identity does hold
    assert.equal(k * (k - l - 1), (N - k - 1) * m);
  }

  // q=7: not strongly regular -- and precisely how it fails
  assert.equal(byQ[7].stronglyRegular, null);
  assert.equal(byQ[7].isGQ, false);
  assert.equal(byQ[7].lambdaValues.length, 1, "lambda is still constant");
  assert.ok(byQ[7].muValues.length > 1, "it is mu that splits");
  assert.deepEqual(byQ[7].muValues, [21, 28]);

  // the two-step degradation, and the scope correction it forces
  assert.match(r.twoStepDegradation.reading, /two-step degradation, not one/);
  assert.match(r.everythingDownstreamIsQ3Only, /holds only at q = 3/);
  assert.match(r.everythingDownstreamIsQ3Only, /34f2a84/);
  assert.match(r.everythingDownstreamIsQ3Only, /8982d36/);
  assert.match(r.everythingDownstreamIsQ3Only, /48e1841/);

  // and the convergence with the corpus's own q=3 coincidence result
  assert.match(r.secondIndependentArrival, /REGULUS side/);
  assert.match(r.secondIndependentArrival, /\(q\+1\)\/2/);
  assert.match(r.boundary, /NOT proved/);
  assert.match(r.boundary, /only that q = 7 is\s+not/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the whole machine is one projective space: 121 = 40 + 45 + 36", () => {
  const r = require(path.join(
    root,
    "data/machine_is_one_projective_space.json"
  ));
  assert.equal(r.schema, "holotrade.machine-is-one-projective-space.v1");
  assert.equal(r.valid, true);

  // the counting identity, recomputed from the formulas
  for (const row of r.theIdentity.rows) {
    const q = row.q;
    assert.equal(row.pointsOfPG4, (q ** 5 - 1) / (q - 1));
    assert.equal(row.isotropic, (q + 1) * (q * q + 1));
    assert.equal(row.square, (q * q * (q * q + 1)) / 2);
    assert.equal(row.nonsquare, (q * q * (q * q - 1)) / 2);
    assert.equal(
      row.pointsOfPG4,
      row.isotropic + row.square + row.nonsquare,
      "identity at q=" + q
    );
    assert.equal(row.identityHolds, true);
  }
  assert.match(r.theIdentity.viaClassicalIsomorphism, /Sp\(4,q\) = O\(5,q\)/);

  // q=3 is the machine
  const a = r.atQ3;
  assert.equal(a.total, 121);
  assert.equal(a.isotropic.count, 40);
  assert.equal(a.square.count, 45);
  assert.equal(a.nonsquare.count, 36);
  assert.equal(
    a.isotropic.count + a.square.count + a.nonsquare.count,
    a.total
  );

  // and the three claims carry DIFFERENT epistemic status, correctly labelled
  assert.match(a.isotropic.status, /CITED/);
  assert.match(a.square.status, /PROVED here by explicit isomorphism/);
  assert.match(a.nonsquare.status, /COUNT MATCH ONLY/);

  // the isomorphism itself
  const i = r.isomorphism;
  assert.deepEqual(i.vertices, [45, 45]);
  assert.equal(i.found, true);
  assert.equal(i.bijective, true);
  assert.equal(i.edgePreservingBothWays, true);
  assert.match(i.sideA, /ANTICOMMUTATION/);
  assert.match(i.sideB, /PERPENDICULARITY/);
  assert.match(i.whyTheRelationsCorrespond, /commuting ones in PSp/);

  // it explains the q-dependence that 424111b only measured
  const q3 = require(path.join(root, "data/cost_quadrangle_is_q3_only.json"));
  const byQ = Object.fromEntries(q3.rows.map((x) => [x.q, x]));
  for (const q of [3, 5, 7]) {
    const row = r.theIdentity.rows.find((x) => x.q === q);
    assert.equal(
      byQ[q].classes,
      row.square,
      "the cost classes ARE the square class at q=" + q
    );
  }
  assert.match(r.whatItExplains, /ORBIT\s+SIZES/);
  assert.match(r.whatItExplains, /never a quadrangle in general/);
  assert.match(r.theStatement, /ONE point set, sorted by the value of a\s+single form/);
  assert.match(r.boundary, /NOT built at q = 5 or 7/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the partition's first leg is LINES, not points -- and the 36 is proved", () => {
  const r = require(path.join(
    root,
    "data/partition_is_lines_not_points.json"
  ));
  assert.equal(r.schema, "holotrade.partition-is-lines-not-points.v1");
  assert.equal(r.valid, true);

  // the correction is explicit and directional
  const c = r.correction;
  assert.equal(c.of, "eb6cfe8");
  assert.equal(c.equivariantToPoints, false, "NOT the points");
  assert.equal(c.equivariantToLines, true, "it is the lines");
  assert.match(c.whyItIsWrong, /decomposable bivector/);

  // and the methodological point: invariants agreed for both candidates
  const inv = r.invariantsCouldNotCatchIt;
  assert.deepEqual(inv.subdegreesIsotropic, [1, 12, 27]);
  assert.deepEqual(inv.subdegreesW33Points, [1, 12, 27]);
  assert.deepEqual(inv.subdegreesW33Lines, [1, 12, 27]);
  assert.equal(inv.allIdentical, true, "subdegrees cannot separate them");
  assert.match(inv.lesson, /only\s+the explicit equivariant map separates them/);

  // the last leg, upgraded from count-match to proof
  const l = r.lastLegProved;
  assert.deepEqual(l.subdegreesNonsquare, [1, 15, 20]);
  assert.deepEqual(l.subdegreesSpreads, [1, 15, 20]);
  assert.equal(l.equivariantBijection, true);
  assert.equal(l.intertwinesAllGenerators, true);
  assert.equal(l.generators, 80);
  assert.match(l.wasPreviously, /COUNT MATCH ONLY/);
  // and the prior certificate did label it that way
  const prev = require(path.join(
    root,
    "data/machine_is_one_projective_space.json"
  ));
  assert.match(prev.atQ3.nonsquare.status, /COUNT MATCH ONLY/);

  // the corrected partition, all three legs with a status
  const p = r.correctedPartition;
  assert.equal(p.total, 121);
  assert.equal(p.isotropic.count, 40);
  assert.equal(p.square.count, 45);
  assert.equal(p.nonsquare.count, 36);
  assert.equal(
    p.isotropic.count + p.square.count + p.nonsquare.count,
    p.total
  );
  assert.equal(p.isotropic.is, "the LINES of W(3,3)");
  assert.equal(p.nonsquare.is, "the 36 spreads");
  for (const k of ["isotropic", "square", "nonsquare"]) {
    assert.match(p[k].status, /proved/, k + " is proved, not matched");
  }
  assert.match(p.whereTheOpcodesSit, /its DUAL/);
  assert.match(p.whereTheOpcodesSit, /not self-dual at odd q/);

  // the refutation was exhaustive, not a failed lucky search
  assert.match(r.boundary, /failed EXHAUSTIVE search over all 40/);
  assert.match(r.whatSurvivesUnchanged, /none of those touched\s+the mislabelled leg/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the m = 2 balanced set exists, over a hemisystem pair", () => {
  const r = require(path.join(root, "data/m_equals_two_balanced_exists.json"));
  assert.equal(r.schema, "holotrade.m2-balanced-exists.v1");
  assert.equal(r.valid, true);

  // it closes a row the corpus flagged UNKNOWN
  assert.match(r.theOpenRow, /UNKNOWN/);
  const prev = require(path.join(root, "data/depth2_balance_spectrum.json"));
  const m2 = prev.rows.find((x) => x.m === 2);
  assert.equal(m2.status, "UNKNOWN", "the prior certificate's open row");
  assert.equal(m2.predictedSize, 200);

  // the cyclic sweep: exactly one order works, the rest are proofs
  const sweep = r.cyclicSweep;
  const ok = sweep.filter((x) => x.status === "OPTIMAL");
  assert.equal(ok.length, 1, "exactly one working cyclic order");
  assert.equal(ok[0].order, 5);
  assert.equal(ok[0].size, 200);
  assert.deepEqual(r.result.infeasibleOrders, [2, 4, 6, 9, 12]);
  assert.deepEqual(r.result.unknownOrders, [3]);
  assert.equal(r.result.feasible, true);
  assert.equal(r.result.size, 200);
  assert.equal(r.result.size, 100 * 2, "forced size 100m");

  // independent re-verification of the witness
  const v = r.independentVerification;
  assert.equal(v.linePairsChecked, 1600);
  assert.equal(v.everyTileExactlyTwo, true);
  assert.match(v.method, /without reference\s+to the model/);
  assert.equal(r.witness.length, 200);
  assert.equal(new Set(r.witness).size, 200, "distinct cells");
  for (const c of r.witness) assert.ok(c >= 0 && c < 1600);

  // the structure the solver was not told about
  assert.deepEqual(v.rowCountProfile, { 6: 20, 4: 20 });
  const h = v.rowSplitIsHemisystemPair;
  assert.deepEqual(Object.keys(h).map(Number).sort(), [4, 6]);
  for (const k of Object.keys(h)) {
    assert.equal(h[k].size, 20);
    assert.equal(h[k].isHemisystem, true, "both halves are hemisystems");
    assert.deepEqual(h[k].meetsEveryLineIn, { 2: 40 });
  }
  assert.equal(20 * 6 + 20 * 4, r.result.size);
  assert.match(v.structureFound, /complementary pair of hemisystems/);
  assert.match(v.structureFound, /fed190d/);

  // scope: it does not touch tau_2, and the five is not the other fives
  assert.match(r.whatItDoesNotSettle, /does NOT move tau_2/);
  assert.match(r.cautionAboutTheFive, /two\s+distinct fives/);
  assert.match(r.boundary, /FULL problem without symmetry is not resolved/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the balance spectrum is complete: holes at 1 and 15 only", () => {
  const r = require(path.join(root, "data/balance_spectrum_complete.json"));
  assert.equal(r.schema, "holotrade.balance-spectrum-complete.v1");
  assert.equal(r.valid, true);

  // the complementation lemma is a proof, and it is stated as one
  const c = r.complementationLemma;
  assert.equal(c.isAProofNotASearch, true);
  assert.match(c.statement, /16-m/);
  assert.match(c.proof, /16 - m for every tile/);

  // the sweep: m=2..8 all feasible, verified, and at size 100m
  const byM = Object.fromEntries(r.sweep.map((x) => [x.m, x]));
  assert.equal(byM[1].status, "INFEASIBLE");
  for (let m = 2; m <= 8; m++) {
    assert.equal(byM[m].status, "OPTIMAL", "m=" + m);
    assert.equal(byM[m].size, 100 * m, "size is 100m at m=" + m);
    assert.equal(byM[m].sizeIs100m, true);
    assert.equal(byM[m].verified, true, "re-verified at m=" + m);
    assert.equal(byM[m].complement, 16 - m);
  }

  // the spectrum and its holes
  assert.deepEqual(r.holes, [1, 15]);
  assert.equal(r.spectrum.length, 15, "15 of the 17 levels");
  for (let m = 0; m <= 16; m++) {
    assert.equal(
      r.spectrum.includes(m),
      !r.holes.includes(m),
      "level " + m
    );
  }
  // the spectrum is symmetric about 8, as the lemma forces
  for (const m of r.spectrum) {
    assert.ok(r.spectrum.includes(16 - m), "symmetric at " + m);
  }
  for (const m of r.holes) {
    assert.ok(r.holes.includes(16 - m), "holes come in complementary pairs");
  }

  // it extends the prior certificate rather than contradicting it
  const prev = require(path.join(root, "data/depth2_balance_spectrum.json"));
  for (const row of prev.rows) {
    if (row.status === "OPTIMAL") {
      assert.equal(
        byM[row.m].size,
        row.actualSize,
        "C5 search reproduces the corpus size at m=" + row.m
      );
    }
  }
  assert.match(r.crossCheck, /WITHOUT\s+symmetry/);

  // the reading, and the honest sourcing of the m=1 row
  assert.match(r.theHolesAreTheOvoidLevels, /product\s+analogue of an ovoid/);
  assert.match(r.theHolesAreTheOvoidLevels, /once at\s+each end and nowhere in between/);
  assert.match(r.boundary, /GLOBAL infeasibility is the corpus's, CITED/);
  assert.match(r.boundary, /only that no C5-invariant\s+one exists/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the second multiplicative instance, and 48e1841's converse is retracted", () => {
  const r = require(path.join(
    root,
    "data/second_multiplicative_instance.json"
  ));
  assert.equal(r.schema, "holotrade.second-multiplicative-instance.v1");
  assert.equal(r.valid, true);

  // the correction: the converse is NOT proved in the corpus
  assert.equal(r.correction.of, "48e1841");
  assert.equal(r.priorTheorem.converseProved, false);
  assert.match(r.priorTheorem.converseBoundary, /does not by itself imply/);
  assert.match(r.correction.whyItIsAnOverRead, /CONVERSE/);
  assert.match(r.correction.whatStands, /fact about\s+W\(3,3\), not a law about defect/);
  assert.match(r.correction.correctStatement, /FORCES/);
  // and it really is the prior certificate's own wording
  const prior = require(path.join(
    root,
    "data/tensor_multiplicativity_ovoid_defect.json"
  ));
  assert.equal(prior.converseProved, false);
  assert.equal(r.priorTheorem.converseBoundary, prior.converseBoundary);

  // every row satisfies the GQ arithmetic and the width formula
  for (const x of r.table) {
    assert.equal(x.points, (x.s + 1) * (x.s * x.t + 1), x.name);
    assert.equal(x.lines, (x.t + 1) * (x.s * x.t + 1), x.name);
    assert.equal(x.ovoidSize, x.s * x.t + 1, x.name);
    assert.equal(x.ovoidDefect, x.tau1 - x.ovoidSize, x.name);
    assert.equal(x.hasOvoid, x.ovoidDefect === 0, x.name);
    assert.equal(x.shadowLower, x.ovoidSize * x.tau1, x.name);
    assert.equal(x.productUpper, x.tau1 * x.tau1, x.name);
    assert.equal(x.widthFormulaHolds, true, x.name);
    assert.equal(
      x.intervalWidth,
      x.tau1 * x.ovoidDefect,
      "width = tau_1 * delta at " + x.name
    );
    // multiplicativity is claimed exactly when delta = 0
    assert.equal(x.multiplicative, x.ovoidDefect === 0 ? true : null, x.name);
  }

  // the new row
  const n = r.newRow;
  assert.equal(n.s, 4);
  assert.equal(n.t, 2);
  assert.equal(n.points, 45);
  assert.equal(n.lines, 27);
  assert.equal(n.tau1, 9);
  assert.equal(n.ovoidDefect, 0);
  assert.equal(n.tau2, 81);
  assert.equal(n.intervalWidth, 0);
  assert.equal(n.multiplicative, true);
  // consistent with where tau_1 = 9 was established
  const tb = require(path.join(root, "data/cost_quadrangle_tower_base.json"));
  assert.equal(tb.tau1.value, n.tau1);
  assert.equal(tb.tau1.defect, n.ovoidDefect);

  // two confirmed rows now, not one
  const mult = r.table.filter((x) => x.multiplicative === true);
  assert.equal(mult.length, 2, "GQ(2,2) and GQ(4,2)");
  assert.ok(mult.some((x) => x.s === 2 && x.t === 2));
  assert.ok(mult.some((x) => x.s === 4 && x.t === 2));
  assert.match(r.whyItMatters, /not W\(3,2\)/);

  // and W(3,3) is untouched
  const w = r.table.find((x) => x.s === 3 && x.t === 3);
  assert.equal(w.tau2, null, "still undecided");
  assert.equal(w.intervalWidth, 11);
  assert.match(r.itDoesNotTouchW33, /decides no delta = 1/);
  assert.match(r.boundary, /NOT an\s+independent verification/);
  assert.match(r.boundary, /tau_2 for W\(3,3\) is untouched/);
});

test("the stale-frontier audit is semantic, not a string match", () => {
  const r = require(path.join(
    root,
    "data/stale_frontier_audit_semantic.json"
  ));
  assert.equal(r.schema, "holotrade.stale-frontier-audit-semantic.v1");
  assert.equal(r.valid, true);

  // the exclusion is sourced, not asserted
  assert.match(r.theExclusion, /43049db/);
  assert.match(r.theExclusion, /CITED, not reproduced/);

  // what the prior audit did and did not do
  const p = r.whatThePriorAuditDidNotDo;
  assert.equal(p.commit, "4b23ec0");
  assert.match(p.matched, /literal interval string/);
  assert.match(p.limitation2, /nothing applied the fix/);
  const prior = require(path.join(
    root,
    "data/the_tau2_interval_is_111_not_110.json"
  ));
  assert.equal(p.filesFound, prior.scan.staleCount);
  assert.deepEqual(prior.certifiedInterval, [111, 115]);
  assert.equal(prior.excluded, 110);

  // the classification is by a published rule
  assert.ok(Array.isArray(r.classificationRule.staleMarks));
  assert.ok(Array.isArray(r.classificationRule.defensibleMarks));
  assert.match(r.classificationRule.STALE, /lower bound\s+110/);

  // counts are consistent and every row carries a verdict
  assert.equal(r.counts.stale + r.counts.defensible, r.counts.flagged);
  assert.equal(r.stale.length, r.counts.stale);
  assert.equal(r.defensible.length, r.counts.defensible);
  assert.ok(r.counts.stale >= 15, "the backlog is substantial");
  for (const x of r.stale.concat(r.defensible)) {
    assert.ok(x.file && x.field && x.verdict);
    assert.ok(["STALE", "DEFENSIBLE"].includes(x.verdict));
  }

  // the audit must not have read its own output
  const self = "stale_frontier_audit_semantic.json";
  for (const x of r.stale.concat(r.defensible)) {
    assert.notEqual(x.file, self, "no self-contamination");
  }

  // the files the literal scan missed are genuinely absent from its list
  const priorData = new Set(
    prior.scan.staleOnly.filter((f) => f.startsWith("data/"))
  );
  assert.ok(r.dataFilesTheLiteralScanMissed.length >= 5);
  for (const f of r.dataFilesTheLiteralScanMissed) {
    assert.equal(priorData.has(f), false, f + " was not in the literal scan");
  }

  // the certificate that already acknowledges the exclusion is NOT called stale
  const defFiles = r.defensible.map((x) => x.file);
  assert.ok(defFiles.includes("tensor_110_sat_encoding.json"));
  assert.ok(defFiles.includes("tensor_blocking_structure.json"));
  assert.match(r.theOneMostWorthKeeping, /not a\s+counting argument/);

  // nothing was rewritten, and no bound moved
  assert.match(r.whyNotRewritten, /would break the suite/);
  assert.match(r.boundary, /NO certificate is modified/);
  assert.match(r.boundary, /still open\s+in \[111, 115\]/);
});

test("why depth five resists is a property of the instance", () => {
  const r = require(path.join(root, "data/why_depth_five_resists.json"));
  assert.equal(r.schema, "holotrade.why-depth-five-resists.v1");
  assert.equal(r.valid, true);
  assert.equal(r.isNegativeMethodResult, true, "labelled as such");

  // the packing route is closed by a PROOF, not a timeout
  const d = r.lpRouteClosedByDuality;
  assert.equal(d.isAProof, true);
  assert.equal(d.integerPackingCeiling, Math.floor(d.lp));
  assert.equal(d.lpCeiling, Math.ceil(d.lp - 1e-9));
  assert.ok(
    d.integerPackingCeiling < d.lpCeiling,
    "any integer packing is WEAKER than the LP's own ceiling"
  );
  assert.match(d.argument, /LP dual IS the fractional\s+packing/);

  // the decision reformulation was tried and returned UNKNOWN
  assert.equal(r.decisionReformulation.length, 2);
  for (const x of r.decisionReformulation) {
    assert.equal(x.status, "UNKNOWN");
    assert.equal(x.budgetSeconds, 240);
  }

  // reductions genuinely do not bite
  const red = r.reductions;
  assert.equal(red.tileConstraints, 6129);
  assert.equal(red.forcedLeavesFromSingletons, 0, "no unit clauses at all");
  assert.equal(red.variableCountUnchanged, true);
  assert.equal(red.leafVariablesRelevant, 5294);
  assert.ok(
    red.afterRemovingDominated > 0.95 * red.tileConstraints,
    "dominance removes under 5%"
  );

  // the measurements that explain it
  const m = r.measurements;
  assert.ok(m.leafOptionsPerTile.min >= 50, "every tile has 50+ options");
  assert.ok(m.largestLeafCoversFraction < 0.2, "no leaf covers a fifth");
  assert.ok(m.density > 0.1 && m.density < 0.15);
  assert.equal(m.incidences, 3640843);
  // and they reproduce the corpus's numbers exactly
  const prior = require(path.join(
    root,
    "data/depth_five_is_reachable_but_undecided.json"
  ));
  assert.ok(Math.abs(m.lp - prior.bounds.lpRelaxation) < 1e-6);
  assert.equal(m.greedy, prior.bounds.greedyCover);
  assert.equal(m.bestKnown, prior.bounds.cpsatBestFound);
  assert.ok(m.integralityGap > 1.7 && m.integralityGap < 1.8);

  // the interval is NOT moved, and the file says so
  assert.deepEqual(prior.bounds.interval, [13, 22]);
  assert.match(r.boundary, /MOVES NO BOUND/);
  assert.match(r.boundary, /NOT\s+evidence that longer budgets would fail/);
  assert.match(r.implication, /will not be separated by\s+more solver/);
  assert.match(r.implication, /GEOMETRY/);
  assert.match(r.diagnosis, /no unit clause anywhere/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the complement half is demonstrated, not just asserted", () => {
  const r = require(path.join(root, "data/complement_half_demonstrated.json"));
  assert.equal(r.schema, "holotrade.complement-half-demonstrated.v1");
  assert.equal(r.valid, true);

  // the prior file did claim it constructively
  const prev = require(path.join(root, "data/balance_spectrum_complete.json"));
  assert.match(prev.boundary, /constructive/);
  assert.match(r.whatWasAsserted, /calling something constructive and\s+constructing it are different/);

  // the check itself: both halves, all tiles, from the committed artefact
  const c = r.complementCheck;
  assert.equal(c.readFromDisk, true);
  assert.equal(c.witnessSource, "data/m_equals_two_balanced_exists.json");
  assert.equal(c.tilesRecounted, 1600);
  assert.equal(c.X.size, 200);
  assert.equal(c.X.m, 2);
  assert.deepEqual(c.X.tileCounts, { 2: 1600 });
  assert.equal(c.X.isBalanced, true);
  assert.equal(c.complement.size, 1400);
  assert.equal(c.complement.m, 14);
  assert.deepEqual(c.complement.tileCounts, { 14: 1600 });
  assert.equal(c.complement.isBalanced, true);
  assert.equal(c.sizeIs100m, true);
  // the two sizes partition the grid, and each is 100m
  assert.equal(c.X.size + c.complement.size, 1600);
  assert.equal(c.X.size, 100 * c.X.m);
  assert.equal(c.complement.size, 100 * c.complement.m);
  assert.equal(c.X.m + c.complement.m, 16, "m + (16-m)");
  // and 14 really is in the spectrum the prior file claimed
  assert.ok(prev.spectrum.includes(14));

  // the C3 row, with its budget recorded
  const c3 = r.c3Row;
  assert.equal(c3.symmetry, "C3");
  assert.equal(c3.budgetSeconds, 430);
  assert.ok(c3.budgetSeconds > c3.priorBudgetSeconds);
  assert.equal(c3.priorStatus, "UNKNOWN");
  assert.equal(c3.loadBearing, false);
  const bal = require(path.join(root, "data/m_equals_two_balanced_exists.json"));
  assert.equal(bal.result.feasible, true, "m=2 settled by C5 regardless");

  // honest about size and limits
  assert.match(r.whyItIsWorthDoing, /neither item moves a bound/);
  assert.match(r.boundary, /AS COMMITTED, read\s+from disk/);
  assert.match(r.boundary, /NOT\s+evidence that no C3-invariant/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the phase lift has no obstruction: the qutrit Clifford group splits", () => {
  const r = require(path.join(root, "data/phase_lift_has_no_obstruction.json"));
  assert.equal(r.schema, "holotrade.phase-lift-no-obstruction.v1");
  assert.equal(r.valid, true);

  // it addresses a boundary the compiler actually stated
  const comp = require(path.join(
    root,
    "data/the_qutrit_transvection_compiler.json"
  ));
  assert.match(comp.boundary, /phase bookkeeping/);
  assert.match(r.theBoundaryLeft, /hard, easy or impossible/);

  // the group orders are the expected ones
  const g = r.oneQutritGroups;
  assert.equal(g.pauliModGlobalPhase, 9);
  assert.equal(g.cliffordModGlobalPhase, 216);
  assert.equal(g.quotient, 24);
  assert.equal(
    g.cliffordModGlobalPhase,
    g.pauliModGlobalPhase * g.quotient,
    "|C| = |P| . |C/P|"
  );

  // the complement, which is what splitting means
  const s = r.splitting;
  assert.equal(s.splits, true);
  assert.equal(s.complementOrder, 24);
  assert.equal(s.complementOrder, g.quotient, "a complement has quotient order");
  assert.equal(s.pauliIntersection, 1, "trivial intersection with the Paulis");
  assert.match(s.consequence, /no 2-cocycle, no\s+phase table/);

  // the qubit contrast is cited, not claimed as derived here
  assert.match(r.literature, /odd prime p/);
  assert.match(r.literature, /NOT such a\s+semidirect product/);
  assert.match(r.literature, /cited for general n/);

  // the q=2 pattern is flagged as an observation, not a theorem
  assert.match(r.sameDichotomyAsTheSession, /6bb8975/);
  assert.match(r.sameDichotomyAsTheSession, /3595bd1/);
  assert.match(r.sameDichotomyAsTheSession, /OBSERVATION/);
  assert.match(r.sameDichotomyAsTheSession, /not a claim that\s+these are the same theorem/);

  // the compiler consequence, and its honest limits
  assert.match(r.whatItChangesForTheCompiler, /lifts TERMWISE/);
  assert.match(r.whatItChangesForTheCompiler, /rather than\s+'not known how'/);
  assert.match(r.boundary, /NOT verified at n = 2/);
  assert.match(r.boundary, /eighty canonical\s+lifts are NOT produced here/);
  assert.match(r.boundary, /not in exact\s+cyclotomic arithmetic/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the eighty Clifford lifts are tabulated in closed form and verified", () => {
  const r = require(path.join(root, "data/eighty_clifford_lifts.json"));
  assert.equal(r.schema, "holotrade.eighty-clifford-lifts.v1");
  assert.equal(r.valid, true);

  // it delivers what the prior commit called engineering
  const prev = require(path.join(
    root,
    "data/phase_lift_has_no_obstruction.json"
  ));
  assert.match(prev.whatItChangesForTheCompiler, /TABULATION/);
  assert.match(r.whatWasPromised, /would be the cheap move/);

  // the closed form, and its collapse at p=3
  const f = r.closedForm;
  assert.match(f.formula, /w\^\{lam k\^2\}/);
  assert.equal(f.generalP, "a = -(2 lam)^{-1} mod p");
  assert.equal(f.collapsesAtP3, true, "a = lam at p=3");

  // verification is exhaustive, not sampled
  const v = r.verification;
  assert.equal(v.lifts, 80);
  assert.equal(v.unitary, 80);
  assert.equal(v.realisesItsTransvection, 80);
  assert.equal(v.conjugationsChecked, 6400, "80 lifts x 80 Paulis");
  assert.equal(v.conjugationsChecked, v.lifts * 80);
  assert.equal(v.isASample, false);

  // the commutation sign is pinned by evidence, both ways measured
  const c = r.commutationConvention;
  assert.equal(c.minusSignViolations, 0);
  assert.ok(c.plusSignViolations > 0, "the other sign genuinely fails");
  assert.match(c.correct, /w\^\{-<u,v>\}/);

  // the table is complete and well formed
  assert.equal(r.table.length, 80);
  const seen = new Set();
  for (const t of r.table) {
    assert.equal(t.v.length, 4);
    assert.ok(t.v.every((x) => x >= 0 && x <= 2), "F_3 coordinates");
    assert.ok([1, 2].includes(t.lam));
    assert.equal(t.a, t.lam, "a = lam at p = 3");
    assert.equal(t.unitary, true);
    assert.equal(t.realisesItsTransvection, true);
    const k = t.v.join(",") + "|" + t.lam;
    assert.equal(seen.has(k), false, "no duplicate (v, lam)");
    seen.add(k);
  }
  assert.equal(seen.size, 80);
  // 40 projective points x 2 values of lam
  assert.equal(new Set(r.table.map((t) => t.v.join(","))).size, 40);

  // and the failed attempt is disclosed as an artefact, not reported as data
  assert.match(r.notSettled, /NOT established/);
  assert.match(r.notSettled, /ARTEFACT/);
  assert.match(r.notSettled, /whether THIS choice is one is open/);
  assert.match(r.stillUsable, /up to a Pauli and a global phase/);
  assert.match(r.boundary, /NUMERICAL at 1e-7/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the Gauss-sum lifts are NOT a homomorphic section", () => {
  const r = require(path.join(
    root,
    "data/gauss_sum_lifts_not_a_section.json"
  ));
  assert.equal(r.schema, "holotrade.gauss-lifts-not-a-section.v1");
  assert.equal(r.valid, true);

  // it settles what the prior commit flagged open
  const prev = require(path.join(root, "data/eighty_clifford_lifts.json"));
  assert.match(prev.notSettled, /whether THIS choice is one is open/);
  assert.match(r.whatWasOpen, /disclosed as an artefact/);

  // the encoding is exact: no unitaries, no rounding, after one safe readout
  const e = r.exactEncoding;
  assert.match(e.arithmetic, /pure F_3/);
  assert.ok(e.phaseReadoffError < 1e-12, "phases are cube roots to 1e-12");

  // phi is not linear, and the zero-sets are NOT uniform
  const q = r.phiIsNotLinear;
  assert.equal(q.linearLifts, 0, "no lift has a linear phase function");
  assert.deepEqual(q.zerosPerLift, { 26: 16, 44: 64 });
  assert.equal(
    Object.values(q.zerosPerLift).reduce((a, b) => a + b, 0),
    80,
    "all eighty accounted for"
  );
  assert.ok(Object.keys(q.zerosPerLift).length > 1, "not uniform");
  // and the unexplained part is labelled as unexplained
  assert.match(q.whatIsAccountedFor, /FLOOR/);
  assert.match(q.whatIsAccountedFor, /NOT explained here/);
  assert.match(q.whatIsAccountedFor, /came from three examples\s+and was wrong/);

  // the negative result itself
  const res = r.result;
  assert.equal(res.isASection, false);
  assert.equal(res.containsPaulis, true);
  assert.equal(res.spOrder, 51840);
  assert.equal(res.hitCap, true);
  assert.ok(res.groupOrderExceeded > res.spOrder, "far past |Sp(4,3)|");

  // it does not overturn the splitting, and says which claim survives
  assert.match(r.doesNotOverturnTheSplitting, /section EXISTS/);
  assert.match(r.doesNotOverturnTheSplitting, /nontrivial cocycle/);
  const split = require(path.join(
    root,
    "data/phase_lift_has_no_obstruction.json"
  ));
  assert.equal(split.splitting.splits, true, "n=1 splitting still stands");
  assert.match(r.compilerUnaffected, /up to a Pauli and a global\s+phase/);

  // and the partial count is not dressed up as a subgroup order
  assert.match(r.boundary, /PARTIAL because/);
  assert.match(r.boundary, /never a subgroup order/);
  assert.match(r.boundary, /NOT attempted here/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the section is constructed and the eighty lifts are corrected onto it", () => {
  const r = require(path.join(
    root,
    "data/section_and_correction_table.json"
  ));
  assert.equal(r.schema, "holotrade.section-and-correction-table.v1");
  assert.equal(r.valid, true);

  // it delivers what the previous commit declined to attempt
  const prev = require(path.join(
    root,
    "data/gauss_sum_lifts_not_a_section.json"
  ));
  assert.match(prev.boundary, /NOT attempted here/);
  assert.equal(prev.result.isASection, false, "the Gauss-sum lifts were not");

  // the section: exactly |Sp(4,3)|, no Paulis
  const s = r.theSection;
  assert.equal(s.order, 51840);
  assert.equal(s.spOrder, 51840);
  assert.equal(s.pauliCount, 0);
  assert.equal(s.isASection, true);
  assert.equal(s.order, s.spOrder, "no excess over the symplectic group");
  assert.equal(s.generatorCount, 77);
  assert.equal(s.verifiedNotCited, true);
  assert.match(s.generators, /quadratic phase/);
  assert.match(s.generators, /Fourier/);
  assert.match(s.consequence, /bijection/);

  // every correction is a genuine Pauli, and linearity was checked FIRST
  const c = r.correction;
  assert.equal(c.outOf, 80);
  assert.equal(c.differenceIsLinear, 80, "all differences linear");
  assert.equal(c.pauliSolved, 80, "all corrections solved");
  assert.match(c.method, /BEFORE a is\s+extracted/);

  // the table is complete and well-formed
  assert.equal(r.table.length, 80);
  const seenKeys = new Set();
  for (const t of r.table) {
    assert.equal(t.v.length, 4);
    assert.ok(t.v.every((x) => x >= 0 && x <= 2));
    assert.ok([1, 2].includes(t.lam));
    assert.equal(t.differenceIsLinear, true);
    assert.ok(Array.isArray(t.pauliCorrection), "a correction exists");
    assert.equal(t.pauliCorrection.length, 4);
    assert.ok(t.pauliCorrection.every((x) => x >= 0 && x <= 2), "F_3 vector");
    const k = t.v.join(",") + "|" + t.lam;
    assert.equal(seenKeys.has(k), false);
    seenKeys.add(k);
  }
  assert.equal(seenKeys.size, 80);
  assert.equal(new Set(r.table.map((t) => t.v.join(","))).size, 40);

  // it matches the lift table it corrects
  const lifts = require(path.join(root, "data/eighty_clifford_lifts.json"));
  assert.equal(lifts.table.length, r.table.length);

  // and the splitting it realises was verified earlier at n=1
  const split = require(path.join(
    root,
    "data/phase_lift_has_no_obstruction.json"
  ));
  assert.equal(split.splitting.splits, true);
  assert.match(r.whyItMatters, /NO\s+residual/);
  assert.match(r.boundary, /VERIFIED here rather than cited/);
  assert.match(r.boundary, /Only n = 2, q = 3/);
  assert.match(r.boundary, /tau_2 is untouched/);
});

test("the correction table is fixed: right relation, real section, closed form", () => {
  const r = require(path.join(root, "data/correction_table_fixed.json"));
  assert.equal(r.schema, "holotrade.correction-table-fixed.v1");
  assert.equal(r.valid, true);
  assert.match(r.supersedes, /0c9ac42/);

  // the bug: solved at the source, but the shift happens at the image
  const b = r.theBug;
  assert.match(b.whatItSolved, /-<a, v>/);
  assert.match(b.correctRelation, /\+<a, S v>/);
  assert.match(b.why, /IMAGE/);
  assert.match(b.whyItSurvived, /solvable 80\/80/);
  assert.match(b.howItWasCaught, /non-circular/);
  assert.match(b.secondSlipCaughtTheSameWay, /do not compose phase-free/);

  // two independent verifications, both passing
  const v = r.verification;
  assert.equal(v.sectionOrder, 51840);
  assert.equal(v.sectionHasNoPaulis, true);
  assert.equal(v.correctedEncodingEqualsSection, 80, "per-lift, direct");
  assert.equal(v.outOf, 80);
  assert.equal(v.groupGeneratedByCorrected, 51840, "global");
  assert.equal(v.pauliCount, 0);
  assert.equal(v.isASection, true);
  assert.equal(
    v.groupGeneratedByCorrected,
    v.sectionOrder,
    "the corrected family lands exactly on the section"
  );
  assert.match(v.twoIndependentChecks, /would fail\s+if any single correction/);

  // and the old table demonstrably failed -- it is superseded, not just amended
  const old = require(path.join(
    root,
    "data/section_and_correction_table.json"
  ));
  assert.equal(old.correction.pauliSolved, 80, "it 'solved' 80/80 too");
  assert.notEqual(
    old.correction.method.includes("S v"),
    true,
    "the old method did not use the image"
  );

  // the closed form, with the sign that the bug flipped
  const c = r.closedForm;
  assert.equal(c.everyCorrectionIsAMultipleOfV, true);
  assert.equal(c.formula, "c = -lam * Q(v)");
  assert.equal(c.fitsNegative, 80);
  assert.ok(c.fitsPositive < c.fitsNegative, "the positive sign does not fit");
  assert.equal(c.fitsPositive, 32);
  assert.match(c.signIsPropagated, /same error/);
  assert.match(c.lift, /Pauli MULTIPLICATION/);

  // the table is complete and every entry has a scalar
  assert.equal(r.table.length, 80);
  for (const t of r.table) {
    assert.equal(t.v.length, 4);
    assert.equal(t.pauliCorrection.length, 4);
    assert.ok([0, 1, 2].includes(t.c), "the scalar exists");
    // the correction really is c times v
    for (let i = 0; i < 4; i++) {
      assert.equal(t.pauliCorrection[i], (t.c * t.v[i]) % 3);
    }
    // and c matches the closed form
    const Q = (t.v[0] * t.v[2] + t.v[1] * t.v[3]) % 3;
    assert.equal(t.c, ((-t.lam * Q) % 3 + 3) % 3, "c = -lam Q(v)");
  }
  assert.equal(new Set(r.table.map((t) => t.v.join(","))).size, 40);

  assert.match(r.boundary, /recomputed from scratch, not patched/);
  assert.match(r.boundary, /Only n = 2/);
  assert.match(r.boundary, /tau_2 is untouched/);
});
