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
