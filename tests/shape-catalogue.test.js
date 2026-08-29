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
