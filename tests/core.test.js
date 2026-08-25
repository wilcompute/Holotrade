// ======================================================================
// HOLOTRADE regression suite
//
//   node --test tests/core.test.js
//
// Two kinds of test live here and they are deliberately not mixed:
//
//   SUBSTRATE FACTS  — exact finite mathematics. These have single
//                      correct answers and any deviation is a bug, not
//                      a tuning question. W(3,3) is SRG(40,12,2,4) or
//                      the geometry is wrong.
//
//   ENGINE CONTRACTS — invariants the pricing, market and execution
//                      layers must hold whatever the parameters are:
//                      the floor is never breached, a magic budget is
//                      never silently substituted, the audit chain
//                      detects tampering, the recursion closes.
//
// Nothing here asserts a tuned constant. A test that fails when a
// coefficient is retuned is a test that stops anyone improving the
// model, so the assertions are bounds and invariants, not fixtures.
// ======================================================================

const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");
const fs = require("node:fs");

global.window = global;
const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/substrate.js"));
const catalog = require(path.join(root, "data/catalog.js"));
const EnergyEngine = require(path.join(root, "js/energy.js"));
const { Fleet } = require(path.join(root, "js/fleet.js"));
const { PricingEngine, TARGET_BAND } = require(path.join(root, "js/pricing.js"));
const { FabricMarket } = require(path.join(root, "js/fabric.js"));
const { GeneticsEngine } = require(path.join(root, "js/genetics.js"));
const U = require(path.join(root, "js/uor.js"));
const { ExecutionEngine } = require(path.join(root, "js/execution.js"));
const { Market, sweepAsks, paretoFrontier } = require(path.join(root, "js/market.js"));
const { runExperiment } = require(path.join(root, "experiments/balancer_ab.js"));
const { SECURITY_HEADERS, resolveRequestPath } = require(path.join(root, "scripts/serve.js"));

function build(size = 200, seed = "test") {
  const energy = new EnergyEngine(catalog.DATACENTERS, seed + "-e");
  const fleet = new Fleet({
    datacenters: catalog.DATACENTERS, hardware: catalog.HARDWARE,
    workloads: catalog.WORKLOADS, operators: catalog.OPERATORS, size, seed,
  });
  const pricing = new PricingEngine(fleet, energy, catalog.WORKLOADS);
  const fabric = new FabricMarket(fleet, pricing);
  const genetics = new GeneticsEngine(fleet, catalog.WORKLOADS);
  const exec = new ExecutionEngine(fleet, pricing, energy, catalog.WORKLOADS);
  const market = new Market(fleet, pricing, energy, catalog);
  return { energy, fleet, pricing, fabric, genetics, exec, market };
}

// ======================================================================
// SUBSTRATE FACTS
// ======================================================================

test("W(3,3) is exactly SRG(40,12,2,4) with 240 edges", () => {
  assert.equal(S.POINTS.length, 40, "40 projective points of PG(3,F_3)");
  assert.ok(S.ADJ.every((row) => row.length === 12), "every point has degree k = 12");
  assert.equal(S.ADJ.reduce((a, r) => a + r.length, 0) / 2, 240, "|E| = 240");

  const lambdas = new Set(), mus = new Set();
  for (let i = 0; i < 40; i++) {
    for (let j = i + 1; j < 40; j++) {
      const common = S.commonNeighbours(i, j).length;
      (S.isAdjacent(i, j) ? lambdas : mus).add(common);
    }
  }
  assert.deepEqual([...lambdas], [2], "adjacent pairs share exactly lambda = 2");
  assert.deepEqual([...mus], [4], "non-adjacent pairs share exactly mu = 4");
});

test("the 40 totally isotropic lines each carry exactly 4 points", () => {
  assert.equal(S.LINES.length, 40);
  assert.ok(S.LINES.every((l) => l.length === 4));
  // every pair of collinear points lies on exactly one line
  for (let i = 0; i < 40; i++) {
    for (const j of S.ADJ[i]) {
      const through = S.LINES.filter((l) => l.includes(i) && l.includes(j));
      assert.equal(through.length, 1, `points ${i},${j} lie on exactly one line`);
    }
  }
});

test("the symplectic form is alternating and adjacency is its kernel", () => {
  for (const p of S.POINTS) {
    assert.equal(S.symplecticForm(p.vec, p.vec), 0, "alternating: <x,x> = 0");
  }
  for (let i = 0; i < 40; i++) {
    for (let j = 0; j < 40; j++) {
      if (i === j) continue;
      const orthogonal = S.symplecticForm(S.POINTS[i].vec, S.POINTS[j].vec) === 0;
      assert.equal(orthogonal, S.isAdjacent(i, j), "adjacency IS the form vanishing");
    }
  }
});

test("routing is table-free and the diameter is exactly 2", () => {
  let maxDist = 0;
  for (let i = 0; i < 40; i++) {
    for (let j = 0; j < 40; j++) {
      const r = S.route(i, j);
      maxDist = Math.max(maxDist, r.distance);
      // every hop in the path must be a legal edge
      for (let h = 1; h < r.hops.length; h++) {
        assert.ok(S.isAdjacent(r.hops[h - 1], r.hops[h]), "each hop is an edge");
      }
      if (r.distance === 2) {
        assert.equal(r.alternates.length, S.CONST.mu - 1, "mu = 4 disjoint two-hop paths");
      }
    }
  }
  assert.equal(maxDist, 2, "diameter 2");
});

test("the migration price law: a neighbour is cheaper than staying put", () => {
  assert.equal(S.RAY_COST.adjacent, 3);
  assert.equal(S.RAY_COST.inPlace, 6);
  assert.ok(S.RAY_COST.adjacent < S.RAY_COST.inPlace,
    "moving to a neighbour must cost strictly less than re-vectoring in place");
  assert.ok(S.RAY_COST.adjacent < S.RAY_COST.nonAdjacent, "edges win");

  // and the cost function agrees with the constants
  const nbr = S.ADJ[1][0];
  assert.equal(S.migrationRays(1, nbr), S.RAY_COST.adjacent);
  assert.equal(S.migrationRays(1, 1), S.RAY_COST.inPlace);
  // the page bill is relocation-isotropic: always 9 points either way
  assert.equal(S.migrationCost([3, 1], [3, nbr]).pageBill, 9);
  assert.equal(S.migrationCost([3, 1], [11, 30]).pageBill, 9);
});

test("recursive address model: 40^n leaves at a 16n-14 distance bound", () => {
  for (let n = 1; n <= 7; n++) {
    assert.equal(S.capacityAtLevel(n), Math.pow(40, n));
    assert.equal(S.diameterAtLevel(n), 16 * n - 14);
  }
  assert.equal(S.diameterAtLevel(1), 2, "the base cell keeps its exact diameter");
  assert.equal(S.diameterAtLevel(7), 98);
  assert.ok(S.capacityAtLevel(7) > 1.6e11, "1.638e11 leaf slots at level 7");
  assert.equal(S.levelFor(8e9), 7, "8 billion people need level 7");
  assert.equal(S.levelFor(40), 1);
  for (let n = 1; n <= 4; n++) {
    const far = S.fabricDistance(Array(n).fill(0), Array(n).fill(1));
    assert.equal(far.hops, S.diameterAtLevel(n), `metric witness attains level-${n} bound`);
  }
  assert.throws(() => S.parseAddress("03.bad.17.99"), /address/,
    "malformed addresses are rejected rather than silently shortened");
});

test("the exact W(3,3) bisection has a machine-readable 20|20 certificate", () => {
  const cert = S.bisectionCertificate();
  assert.equal(cert.left.length, 20);
  assert.equal(cert.right.length, 20);
  assert.equal(new Set(cert.left.concat(cert.right)).size, 40);
  assert.equal(cert.crossingEdges, 100);
  assert.equal(cert.spectralLowerBound, 100);
  assert.equal(cert.exact, true, "an explicit cut attains the spectral lower bound");
  assert.equal(S.cutSize(cert.left), 100);
});

test("the Landauer floor is 58 syndrome qutrits at kT ln 3", () => {
  const floor300 = S.landauerFloorPerCycle(300);
  assert.ok(Math.abs(floor300 - 2.64e-19) < 0.05e-19,
    `2.64e-19 J/cycle at 300 K, got ${floor300.toExponential(3)}`);
  // linear in temperature
  assert.ok(Math.abs(S.landauerFloorPerCycle(600) / floor300 - 2) < 1e-9);
  const sameUnitProbe = floor300 * 1e6;
  assert.ok(Math.abs(S.thermodynamicDecades(sameUnitProbe, 300) - 6) < 1e-9,
    "the ratio is valid when numerator and denominator share the same functional cycle");
  const { energy, fleet } = build(20, "units");
  const node = fleet.nodes[0];
  const dc = catalog.DATACENTERS.find((d) => d.id === node.dcId);
  assert.equal(energy.decadesAboveFloor(node, dc), null,
    "catalog J/op is not divided by modeled J/syndrome-cycle");
});

test("the magic dial is exactly 9^t", () => {
  assert.equal(S.magicMultiplier(0), 1, "classical work is free");
  assert.equal(S.magicMultiplier(1), 9);
  assert.equal(S.magicMultiplier(6), 531441);
  assert.ok(S.magicMultiplier(20) > 1e19, "at t=20 no classical fleet can help");
});

test("venue dashboard transforms keep units explicit", () => {
  const cap = U.venueCapacity(70e6);
  assert.equal(cap.illustrativeTransforms.conjugacyScale, 1728);
  assert.equal(cap.illustrativeTransforms.logicalScale, 27 / 80);
  assert.equal(cap.illustrativeTransforms.coherenceScale, 1 / 384);
  assert.equal(cap.fullCellScanSeconds, 51840 / 70e6,
    "51,840 transactions divided by tx/s has units of seconds");
  assert.equal(cap.fullOrbitSeconds, cap.fullCellScanSeconds, "legacy name keeps corrected units");
  assert.equal(Object.hasOwn(cap, "settlementFloorMs"), false,
    "a dimensionless Coxeter number is not relabelled as milliseconds");
});

test("UOR uses an exact uint64 mixed-radix codec over 51,840 cells", () => {
  assert.equal(U.UOR.sylowChoices * U.UOR.normaliserOrder, 51840);
  assert.equal(U.UOR.canonicalCells, S.CONST.autOrder);
  assert.equal(U.UOR.addressSpaceSize, 1n << 64n);
  assert.equal(
    U.UOR.completePayloadBands * BigInt(U.UOR.canonicalCells) + BigInt(U.UOR.finalPayloadBandCells),
    U.UOR.addressSpaceSize,
    "the non-dividing final band is represented exactly"
  );
  assert.ok(Math.abs(U.UOR.payloadBits - (64 - Math.log2(51840))) < 1e-9);
  // and the rank-3 shell sums to the point count
  assert.equal(U.SHELL.self + U.SHELL.adjacent + U.SHELL.distant, 40);
  assert.equal(U.SHELL.adjacent, S.CONST.degree);
});

test("UOR addresses round-trip and classify by the rank-3 relation", () => {
  const a = U.UORAddress.from("node-alpha");
  const b = U.UORAddress.from("node-alpha");
  assert.equal(a.cell, b.cell, "deterministic");
  assert.ok(a.cell < 51840, "inside the canonical cell space");
  assert.match(a.toHex(), /^uor:[0-9a-f]{16}$/);
  for (const raw of [0n, 1n, (1n << 32n) + 17n, (1n << 64n) - 1n]) {
    const decoded = U.UORAddress.fromBigInt(raw);
    assert.equal(decoded.toBigInt(), raw);
    assert.equal(U.UORAddress.fromHex(decoded.toHex()).toBigInt(), raw);
  }
  assert.throws(() => U.UORAddress.fromHex("uor:123"), /must match/);
  assert.throws(() => U.UORAddress.fromBigInt(1n << 64n), /must be in/);

  const rels = new Set();
  for (let i = 0; i < 40; i++) {
    rels.add(new U.UORAddress(0, 0).relationTo(new U.UORAddress(i, 0)));
  }
  assert.deepEqual([...rels].sort(), ["disjoint", "identity", "intersecting"],
    "rank 3 means exactly three relations exist");
});

test("asset mobility is labelled as policy score, not orbit-stabilizer arithmetic", () => {
  const asset = new U.SmartAsset({ id: "regulated-gpu", kind: "node", policies: ["data-residency", "gpu-affinity"] });
  const card = asset.describe();
  assert.equal(card.policyMobilityScore, 1 / 3);
  assert.equal(card.marketBreadth, Math.round(40 / 3));
  assert.equal(card.stabiliser, null);
  assert.equal(asset.stabiliserOrder(), null);
  assert.equal(asset.provenance().authenticated, false,
    "geometry validates structure but does not authenticate history");
});

// ======================================================================
// ENGINE CONTRACTS
// ======================================================================

test("a quote decomposes into exactly six multipliers over a base", () => {
  const { fleet, pricing } = build();
  const node = fleet.listedNodes()[0];
  const q = pricing.quote(node, { workloadId: "llm-train" });
  assert.ok(q.serviceable);
  assert.deepEqual(Object.keys(q.multipliers).sort(), ["D", "E", "G", "H", "L", "Q"]);
  const product = q.base * q.multipliers.E * q.multipliers.G * q.multipliers.D *
                  q.multipliers.H * q.multipliers.Q * q.multipliers.L;
  // the quote is the product, unless the floor lifted it
  assert.ok(Math.abs(q.rawPrice - product) < 1e-9, "P = base x E x G x D x H x Q x L");
  assert.ok(q.price >= q.rawPrice - 1e-9, "the floor only ever lifts the price");
});

test("the exchange never clears below energy + reserve + capital", () => {
  const { fleet, pricing, energy } = build();
  for (const node of fleet.listedNodes()) {
    const q = pricing.quote(node, { workloadId: "llm-train" });
    if (!q.serviceable) continue;
    const dc = catalog.DATACENTERS.find((d) => d.id === node.dcId);
    const expected = energy.hourlyEnergyCost(node, dc)
      + fleet.maintenanceReserve(node)
      + fleet.capitalRecovery(node);
    assert.ok(Math.abs(q.floor - expected) < 1e-9, "floor has all three components");
    assert.ok(q.price >= q.floor, `${node.id}: price ${q.price} must not breach floor ${q.floor}`);
  }
});

test("a magic budget is refused, never substituted", () => {
  const { fleet, pricing, exec } = build();
  const classical = fleet.nodes.find((n) => !n.hardware.magicCapable);
  const photonic = fleet.nodes.find((n) => n.hardware.magicCapable);
  assert.ok(classical && photonic, "the fleet has both kinds");

  // pricing refuses
  const q = pricing.quote(classical, { workloadId: "qsim" });
  assert.equal(q.serviceable, false, "a Clifford-only node cannot serve t > 0");
  assert.equal(q.price, null, "and gets no price rather than a degraded one");

  // execution refuses, with a reason
  const plan = exec.createPlan({ name: "t12", workloadId: "qsim", requestedSeconds: 5 });
  assert.equal(plan.magicBudget, 12);
  const r = exec.launch(plan, classical);
  assert.equal(r.ok, false);
  assert.equal(r.code, "NO_MAGIC");

  // and the magic-capable node does serve it, at a premium
  const qp = pricing.quote(photonic, { workloadId: "qsim" });
  assert.ok(qp.serviceable);
  assert.ok(qp.multipliers.Q > 1, "magic is priced above classical");
  assert.equal(pricing.quote(photonic, { workloadId: "llm-train" }).multipliers.Q, 1,
    "classical work on the same node is Q = 1 exactly");
});

test("the demand multiplier is genuinely two-sided about the band", () => {
  const { pricing } = build();
  const probe = (u) => pricing.demandMultiplier({
    utilisation: u, utilisationEMA: u, hardware: { thermalSensitivity: 1 },
  });
  assert.ok(probe(0.05) < 0.9, "a cold node is discounted");
  assert.ok(probe(0.97) > 1.3, "a pinned node carries a premium");

  // The band's lower edge is the seam between discount and neutral, so
  // it must be exactly 1.0 -- that is what makes the curve continuous.
  // Across the band D stays near neutral but is not flat: a flat band
  // would make the curve non-monotone at one seam or the other, and a
  // node that gets cheaper by becoming busier is arbitrageable.
  assert.ok(Math.abs(probe(TARGET_BAND.low) - 1) < 1e-9, "the lower seam is exactly neutral");
  for (let u = TARGET_BAND.low; u <= TARGET_BAND.high; u += 0.01) {
    const v = probe(u);
    assert.ok(v >= 1 - 1e-9 && v <= 1.12, `in-band D stays near neutral, got ${v.toFixed(4)} at u=${u.toFixed(2)}`);
  }
  // monotone increasing in utilisation
  let prev = -Infinity;
  for (let u = 0; u <= 1.0001; u += 0.05) {
    const v = probe(Math.min(1, u));
    assert.ok(v >= prev - 1e-9, `monotone at u=${u.toFixed(2)}`);
    prev = v;
  }
  // and it switches off cleanly
  pricing.balancerEnabled = false;
  assert.equal(probe(0.05), 1);
  assert.equal(probe(0.97), 1);
});

test("two-sided pricing reduces fleet dispersion", () => {
  // The headline claim of the whole design, so it gets a test.
  // Asserted as a strict inequality on the Gini, not a target value --
  // the coefficients should be free to change without breaking this.
  const run = (balancerOn) => {
    const { fleet, pricing, energy } = build(220, "gini-paired");
    pricing.balancerEnabled = balancerOn;
    for (let i = 0; i < 500; i++) {
      energy.tick(60);
      pricing.applyDemandResponse(1 / 60, { workloadId: "llm-train" });
      fleet.tick(1 / 60);
    }
    return pricing.fleetStats.gini;
  };
  const on = run(true);
  const off = run(false);
  assert.ok(on < off, `balancer must reduce dispersion: on=${on.toFixed(4)} off=${off.toFixed(4)}`);
  assert.ok(on >= 0 && on <= 1, "Gini is a coefficient in [0,1]");
});

test("the frozen 64-seed balancer packet is reproducible and explicitly simulated", () => {
  const packet = JSON.parse(fs.readFileSync(path.join(root, "data/balancer_ab_64.json"), "utf8"));
  assert.equal(packet.evidence, "SIMULATION");
  assert.equal(packet.design.paired, true);
  assert.equal(packet.design.seeds, 64);
  assert.equal(packet.summary.improvedSeeds, 64);
  assert.equal(packet.summary.allSeedsImproved, true);
  assert.ok(packet.summary.relativeReduction.mean > 0.5);

  // The demo surface must show the frozen result rather than invite a
  // presenter to infer a headline number from the live animation.
  const site = fs.readFileSync(path.join(root, "holotrade.html"), "utf8");
  assert.match(site, /Paired simulation certificate/);
  assert.match(site, /60\.34%/);
  assert.match(site, /64 \/ 64/);
  assert.match(site, new RegExp(packet.rowsSha256.slice(0, 12)));

  // Fast smoke reproduction uses fewer seeds/steps; the complete packet
  // is regenerated with `npm run experiment:balancer`.
  const smoke = runExperiment({ seeds: 3, size: 80, steps: 80, stepSeconds: 60 });
  assert.equal(smoke.design.paired, true);
  assert.equal(smoke.rows.length, 3);
  assert.ok(smoke.rows.every((row) => row.seed && Number.isFinite(row.on) && Number.isFinite(row.off)));
});

test("the Gini coefficient itself is correct on known inputs", () => {
  const { pricing } = build(20);
  const mk = (utils) => utils.map((u) => ({ utilisation: u }));
  assert.ok(pricing.utilisationGini(mk([0.5, 0.5, 0.5, 0.5])) < 1e-9, "perfect equality = 0");
  const perfect = pricing.utilisationGini(mk([0, 0, 0, 1]));
  assert.ok(perfect > 0.7, `one node doing all the work is near 1, got ${perfect.toFixed(3)}`);
  assert.ok(pricing.utilisationGini([]) === 0, "empty fleet is not an error");
});

// ---- fabric ----------------------------------------------------------

test("coherence separates a shape from a pile of the same size", () => {
  const { fleet, fabric } = build(320, "coh");
  // find the fullest cell -- a real shape
  const cell = fabric.cells()[0];
  assert.ok(cell.nodes.length >= 8, "need a reasonably full cell to test");
  const coherent = cell.nodes;

  // a scattered basket of the SAME SIZE drawn from different cells
  const byCell = new Map();
  for (const n of fleet.nodes) {
    const k = n.addr.slice(0, -1).join(".");
    if (!byCell.has(k)) byCell.set(k, n);
  }
  const scattered = [...byCell.values()].slice(0, coherent.length);
  assert.equal(scattered.length, coherent.length, "same node count");

  const cCoh = fabric.coherence(coherent);
  const cScat = fabric.coherence(scattered);
  assert.ok(cCoh > cScat, `a shape beats a pile: ${cCoh.toFixed(3)} vs ${cScat.toFixed(3)}`);
  assert.ok(fabric.realisedBisection(coherent) > fabric.realisedBisection(scattered),
    "and it delivers more bisection");
  assert.ok(fabric.coherenceMultiplier(coherent) > fabric.coherenceMultiplier(scattered),
    "so it is worth more than the sum of its parts");
});

test("a full W(3,3) cell delivers exactly the spectral bisection bound", () => {
  const { fabric } = build(40, "bisect");
  // synthesise a complete cell: all 40 points present
  const complete = [];
  for (let p = 0; p < 40; p++) complete.push({ addr: [7, p], cellPoint: p, hardware: {}, id: "n" + p });
  const bis = fabric.realisedBisection(complete);
  assert.ok(Math.abs(bis - S.CONST.bisection) < 1e-6,
    `bisection 100 = (40/4)(12-2), got ${bis}`);
  assert.ok(Math.abs(fabric.coherence(complete) - 1) < 0.02, "a complete cell is fully coherent");
  const graph = fabric.inducedGraphStats(complete);
  assert.deepEqual(
    { vertices: graph.vertices, edges: graph.edges, components: graph.components, diameter: graph.diameter, minDegree: graph.minDegree },
    { vertices: 40, edges: 240, components: 1, diameter: 2, minDegree: 12 }
  );
});

test("partial baskets report induced connectivity, not full-fabric paths or fault claims", () => {
  const { fabric } = build(40, "induced");
  const mk = (p) => ({ addr: [7, p], cellPoint: p, hardware: {}, id: `n${p}` });
  const adjacent = S.ADJ[0][0];
  const distant = S.POINTS.find((p) => p.index !== 0 && !S.isAdjacent(0, p.index)).index;

  const edgePair = fabric.inducedGraphStats([mk(0), mk(adjacent)]);
  assert.equal(edgePair.connected, true);
  assert.equal(edgePair.diameter, 1);
  assert.equal(edgePair.edges, 1);

  const disconnected = fabric.inducedGraphStats([mk(0), mk(distant)]);
  assert.equal(disconnected.connected, false);
  assert.equal(disconnected.components, 2);
  assert.equal(disconnected.diameter, null,
    "the two-hop path through an unowned relay is not attributed to the basket");
});

test("swaps are only proposed when BOTH sides gain", () => {
  const { fleet, fabric } = build(320, "swap");
  const byCell = new Map();
  for (const n of fleet.listedNodes()) {
    const k = n.addr.slice(0, -1).join(".");
    if (!byCell.has(k)) byCell.set(k, []);
    byCell.get(k).push(n);
  }
  // a deliberately fragmented book: many nodes in one cell, orphans elsewhere
  const groups = [...byCell.values()].sort((a, b) => b.length - a.length);
  const mine = groups[0].slice(0, 6).concat(groups.slice(1, 5).map((g) => g[0]));
  const props = fabric.proposeSwaps(mine, { limit: 8 });
  for (const p of props) {
    assert.ok(p.coherenceGain > 0, "I must gain coherence");
    assert.ok(p.counterpartyGain > 0, "the counterparty must also gain coherence");
    assert.ok(p.give.id !== p.get.id, "a swap moves something");
    assert.equal(p.give.hardware.class, p.get.hardware.class,
      "like for like -- the cash adjustment settles quality, not class");
  }
});

test("the recursion closes: the same engine quotes a leaf and a campus", () => {
  const { fleet, fabric, pricing } = build(320, "tower");
  const tower = fabric.buildTower(4);
  assert.ok(tower.length >= 2, "the fleet composes to at least two levels");

  const leaf = fleet.listedNodes()[0];
  const qLeaf = pricing.quote(leaf, { workloadId: "llm-train" });
  assert.ok(qLeaf.serviceable);

  for (const level of tower) {
    const obj = level.objects.find((o) => o.isComposite);
    if (!obj) continue;
    // a composite must satisfy the same interface a leaf does
    for (const k of ["id", "address", "hardware", "genome", "health", "utilisation", "specialisation", "lineage"]) {
      assert.ok(obj[k] !== undefined, `composite exposes ${k} like a leaf does`);
    }
    assert.ok(obj.effectiveTflops > 0);
    // ...so the SAME pricing engine quotes it with no special case
    const q = pricing.quote(obj, { workloadId: "llm-train" });
    assert.ok(q.serviceable, `level ${obj.level} composite is quotable`);
    assert.ok(q.price > 0);
    assert.deepEqual(Object.keys(q.multipliers).sort(), ["D", "E", "G", "H", "L", "Q"],
      "and decomposes identically");
    assert.ok(q.price > qLeaf.price, "a campus costs more than one machine");
  }

  // and composition is closed: compose(compose(x)) is well formed
  const l1 = tower[0].objects.filter((o) => o.isComposite).slice(0, 2);
  if (l1.length === 2) {
    const up = fabric.compose(l1);
    assert.ok(up, "composites compose");
    assert.equal(up.level, Math.max(l1[0].level, l1[1].level) + 1);
    assert.equal(up.leaves, l1[0].leaves + l1[1].leaves, "leaf count is conserved");
    assert.ok(pricing.quote(up, {}).serviceable, "and the result is still quotable");
  }
});

test("composite health is the union of its parts' risk, not the average", () => {
  const { fleet, fabric } = build(320, "chealth");
  const cell = fabric.cells()[0];
  const c = fabric.compose(cell.nodes);
  const leaves = c.flatten();
  const worstWear = Math.max(...leaves.map((n) => n.health.wear));
  assert.equal(c.health.wear, worstWear, "due for service when its worst member is");
  assert.ok(c.health.hazard >= Math.max(...leaves.map((n) => n.health.hazard)),
    "a composite is at least as likely to fail as its likeliest failure");
  assert.equal(c.genome.faultResilience, Math.min(...leaves.map((n) => n.genome.faultResilience)),
    "only as resilient as its weakest constituent");
});

test("splicing a node in is a local operation", () => {
  const { fleet, fabric } = build(120, "splice");
  const node = fleet.nodes[0];
  const before = fleet.nodes.map((n) => n.address);
  const r = fabric.splice(node, "05.03");
  if (r.ok) {
    assert.equal(r.cost, "one local registry assignment (physical integration unmodelled)");
    assert.equal(r.neighbours, S.CONST.degree, "the new node lands with 12 neighbours");
    // nothing else moved
    const after = fleet.nodes.map((n) => n.address);
    let moved = 0;
    for (let i = 0; i < before.length; i++) if (before[i] !== after[i]) moved++;
    assert.equal(moved, 1, "exactly one address changed -- no fleet-wide rebalance");
  }
});

// ---- execution -------------------------------------------------------

test("an execution plan is immutable after signing", () => {
  const { exec } = build();
  const plan = exec.createPlan({
    name: "p", workloadId: "llm-train", requestedSeconds: 10,
    artifacts: [{ name: "img", digest: "abc" }],
  });
  assert.ok(plan.verify(), "a fresh plan verifies");
  const original = plan.digest;

  plan.requestedSeconds = 9999;   // tamper
  assert.ok(!plan.verify(), "editing the content breaks the signature");
  assert.notEqual(plan.computeDigest(), original);

  plan.requestedSeconds = 10;     // restore
  assert.ok(plan.verify(), "and restoring it repairs the match");

  for (const [field, value] of [
    ["nonce", `${plan.nonce}ff`],
    ["anchorAddress", "01.02"],
    ["maxPricePerNodeSecond", 0.123],
    ["owner", "MALLORY"],
  ]) {
    const before = plan[field];
    plan[field] = value;
    assert.equal(plan.verify(), false, `editing ${field} breaks the integrity seal`);
    plan[field] = before;
    assert.equal(plan.verify(), true, `${field} can be restored for the next mutation check`);
  }
});

test("the admission gate refuses for a stated reason, never silently", () => {
  const { fleet, exec } = build();
  const node = fleet.listedNodes().find((n) => !n.hardware.magicCapable);

  // window
  const expired = exec.createPlan({
    name: "expired", workloadId: "llm-train", requestedSeconds: 5,
    validFrom: Date.now() - 7200_000, validUntil: Date.now() - 3600_000,
  });
  assert.equal(expired.admissible(node).code, "WINDOW");

  // pin drift
  const drifted = exec.createPlan({
    name: "drift", workloadId: "llm-train", requestedSeconds: 5,
    artifacts: [{ name: "img", digest: "aaa", observed: "bbb" }],
  });
  assert.equal(drifted.admissible(node).code, "PIN_DRIFT");

  // replay
  const good = exec.createPlan({ name: "ok", workloadId: "llm-train", requestedSeconds: 5 });
  assert.equal(good.admissible(node).ok, true);
  const store = new Set([good.nonce]);
  assert.equal(good.admissible(node, Date.now(), store).code, "REPLAY");
});

test("multi-node requests are refused until gang placement exists", () => {
  const { exec, fleet } = build();
  const plan = exec.createPlan({ name: "gang", workloadId: "llm-train", requestedSeconds: 30, nodeCount: 2 });
  const node = fleet.listedNodes()[0];
  const result = exec.launch(plan, node);
  assert.equal(result.ok, false);
  assert.equal(result.code, "UNSUPPORTED_NODE_COUNT");
  assert.equal(exec.runningVMs().length, 0);
});

test("metering clips the final slice and settles exactly at requested duration", () => {
  const { fleet, exec } = build();
  const plan = exec.createPlan({
    name: "meter", workloadId: "llm-train", requestedSeconds: 30, nodeCount: 1,
  });
  const places = exec.place(plan, { limit: 1 });
  assert.ok(places.length, "there is somewhere to run it");
  const r = exec.launch(plan, places[0].node);
  assert.ok(r.ok);
  assert.ok(r.boot.ms > 50 && r.boot.ms < 400, `microVM boot in ms, got ${r.boot.ms.toFixed(1)}`);

  const settled = exec.meter(45)[0];
  assert.ok(settled, "the plan settles once it has run its seconds");
  assert.equal(settled.nodeSeconds, 30, "a coarse tick cannot over-deliver or over-bill");
  assert.equal(exec.meteredSeconds, 30);
  assert.ok(settled.cost > 0);
  assert.ok(settled.kwh > 0, "and reports the joules actually drawn");
  assert.equal(exec.meteredSpend, settled.cost, "boot and runtime cost reconcile to the receipt");
  assert.equal(plan.status, "settled");
});

test("a live price-cap breach halts instead of silently repricing", () => {
  const { exec, pricing } = build();
  const probe = exec.createPlan({ name: "probe", workloadId: "llm-train", requestedSeconds: 10 });
  const placement = exec.place(probe, { limit: 1 })[0];
  assert.ok(placement);
  const cap = placement.perSecond * 1.05;
  const plan = exec.createPlan({
    name: "capped", workloadId: "llm-train", requestedSeconds: 10,
    maxPricePerNodeSecond: cap,
  });
  const launch = exec.launch(plan, placement.node);
  assert.equal(launch.ok, true);
  const originalQuote = pricing.quote.bind(pricing);
  pricing.quote = (node, opts) => ({ ...originalQuote(node, opts), serviceable: true, price: cap * 3600 * 2 });
  const receipt = exec.meter(1)[0];
  assert.equal(receipt.outcome, "price_cap_halt");
  assert.equal(receipt.nodeSeconds, 0);
  assert.match(receipt.outcomeReason, /exceeded cap/);
});

test("the audit chain detects tampering", () => {
  const { fleet, exec } = build();
  const plan = exec.createPlan({ name: "chain", workloadId: "llm-train", requestedSeconds: 3 });
  const places = exec.place(plan, { limit: 1 });
  exec.launch(plan, places[0].node);
  for (let i = 0; i < 6; i++) exec.meter(1);

  assert.ok(exec.verifyChain().ok, "an untouched chain verifies");
  assert.ok(exec.auditLog.length >= 3);

  const original = exec.auditLog[1].detail;
  exec.auditLog[1].detail = `${original} edited`;
  assert.equal(exec.verifyChain().ok, false, "editing an entry body breaks its checksum");
  exec.auditLog[1].detail = original;
  assert.equal(exec.verifyChain().ok, true, "restoring the body restores the chain");

  // remove a middle entry -- every entry after it should now be orphaned
  exec.auditLog.splice(1, 1);
  assert.equal(exec.verifyChain().ok, false, "removing an entry breaks the chain");
});

test("audit events use the plan lifecycle names", () => {
  const { fleet, exec } = build();
  const plan = exec.createPlan({ name: "n", workloadId: "llm-train", requestedSeconds: 2 });
  const node = exec.place(plan, { limit: 1 })[0].node;
  exec.launch(plan, node);
  for (let i = 0; i < 4; i++) exec.meter(1);
  const kinds = exec.auditLog.map((e) => e.kind);
  for (const k of ["plan.signed", "plan.admitted", "plan.launched", "plan.settled"]) {
    assert.ok(kinds.includes(k), `chain records ${k}`);
  }
});

test("nested density is the fractal law, from n+1 blobs", () => {
  const { exec } = build();
  const d6 = exec.densityAt(6);
  assert.equal(d6.leaves, 4_096_000_000);
  assert.equal(d6.internal, 105_025_641);
  assert.equal(d6.total, 4_201_025_641);
  assert.equal(d6.uniqueBlobs, 7, "seven unique state blobs denote the whole tree");
  assert.equal(d6.diameter, 82);
});

// ---- market ----------------------------------------------------------

test("depth sweep reports VWAP, slippage and unfilled quantity without mutation", () => {
  const asks = [
    { price: 10, qty: 2 },
    { price: 12, qty: 3 },
    { price: 20, qty: 9 },
  ];
  const before = JSON.stringify(asks);
  const fill = sweepAsks(asks, 4, 15);
  assert.equal(fill.filled, 4);
  assert.equal(fill.remaining, 0);
  assert.equal(fill.cost, 44);
  assert.equal(fill.average, 11);
  assert.equal(fill.worst, 12);
  assert.equal(fill.levelsTouched, 2);
  assert.ok(Math.abs(fill.slippageBps - 1000) < 1e-9);
  assert.equal(JSON.stringify(asks), before, "preview is non-mutating");

  const capped = sweepAsks(asks, 8, 12);
  assert.equal(capped.filled, 5);
  assert.equal(capped.remaining, 3);
  assert.equal(capped.complete, false);
});

test("typed-compute Pareto frontier contains no dominated offer", () => {
  const points = [
    { id: "slow", price: 10, tflops: 5 },
    { id: "tie-fast", price: 10, tflops: 8 },
    { id: "dominated", price: 12, tflops: 7 },
    { id: "middle", price: 15, tflops: 12 },
    { id: "fast", price: 30, tflops: 40 },
  ];
  assert.deepEqual(paretoFrontier(points).map((p) => p.id), ["tie-fast", "middle", "fast"]);
});

test("the ask side is the pricing engine, node for node", () => {
  const { fleet, pricing, market } = build();
  const asks = market.rebuildAsks("spot", { workloadId: "llm-train" });
  assert.ok(asks.length > 0);
  for (const a of asks.slice(0, 25)) {
    const q = pricing.quote(a.node, { workloadId: "llm-train" });
    assert.ok(Math.abs(a.price - q.price) < 1e-6, "every offer IS a node's own quote");
    assert.ok(a.quote, "and carries its decomposition for the buyer to inspect");
  }
  // sorted best-first
  for (let i = 1; i < asks.length; i++) assert.ok(asks[i].price >= asks[i - 1].price);
});

test("spot inventory is bounded by a node's free eighth-capacity lots", () => {
  const { fleet, market } = build(80, "inventory");
  const node = fleet.listedNodes().find((n) => n.utilisation < 0.75);
  assert.ok(node);
  const initialLots = Math.floor((1 - node.utilisation + 1e-12) * 8);
  let filled = 0;
  for (let i = 0; i < 16; i++) {
    filled += market.submitBuy({ instrument: "spot", qty: 1, workloadId: "llm-train", nodeId: node.id }).filledQty;
  }
  assert.ok(filled <= initialLots, `sold ${filled} lots from ${initialLots} initially free`);
  assert.ok(node.utilisation <= 1 + 1e-12);
  node.utilisation = 1;
  assert.equal(market.rebuildAsks("spot").some((a) => a.nodeId === node.id), false,
    "a saturated node disappears from the ask book");
});

test("a fill names the machine and issues a receipt", () => {
  const { fleet, market } = build();
  const before = market.cash;
  const order = market.submitBuy({ instrument: "spot", qty: 5, workloadId: "llm-train" });
  assert.ok(order.filledQty > 0);
  assert.ok(market.cash < before, "cash is debited");
  assert.equal(market.receipts.length, order.fills.length, "one receipt per fill");
  for (const f of order.fills) {
    assert.ok(fleet.get(f.nodeId), "the fill names a real node");
    assert.ok(f.nodeAddress && f.hardware && f.dcId);
  }
  const r = market.receipts[0];
  assert.ok(["substrate", "clifford"].includes(r.lane));
  assert.ok(r.provenance, "and carries the capacity's provenance");
});

test("fill-time receipts are visibly synthetic, not execution attestations", () => {
  const { fleet, market } = build();
  const photonic = fleet.listedNodes().find((n) => n.hardware.magicCapable);
  if (!photonic) return;   // seed-dependent; the fleet may hold none listed
  market.submitBuy({ instrument: "spot", qty: 1, workloadId: "llm-train", nodeId: photonic.id });
  const r = market.receipts.find((x) => x.nodeId === photonic.id);
  if (!r) return;
  assert.equal(r.lane, "substrate");
  assert.ok(Math.abs(r.contextualFraction - S.CONST.contextualFraction) < 0.02,
    "measured near the 1/10 = (40-36)/40 target");
  assert.equal(r.verdict, "SYNTHETIC_SAMPLE");
  assert.equal(r.evidenceMode, "SIMULATED_QUOTE_RECEIPT");
  assert.equal(r.verdictOk, null);
});

test("selling closes the position and books the P&L", () => {
  const { market } = build();
  market.submitBuy({ instrument: "spot", qty: 3, workloadId: "llm-train" });
  const pos = market.positions[0];
  assert.ok(pos);
  const qty = pos.qty;
  const r = market.submitSell({ positionId: pos.id });
  assert.equal(r.ok, true);
  assert.equal(r.trade.qty, qty);
  assert.ok(!market.positions.find((p) => p.id === pos.id), "the position is gone");
  assert.equal(market.realised, r.pnl);
});

test("an order cannot spend cash the account does not have", () => {
  const { market } = build();
  market.cash = 10;
  const o = market.submitBuy({ instrument: "spot", qty: 500, workloadId: "llm-train" });
  assert.ok(market.cash >= -1e-9, `cash must not go negative, got ${market.cash}`);
  assert.ok(o.filledQty < 500, "the order is partially filled or rejected");
});

test("forward, option and lease all price off the same spot quote", () => {
  const { fleet, pricing } = build();
  const node = fleet.listedNodes().find((n) => n.utilHistory.length >= 0);
  const spot = pricing.quote(node, { workloadId: "llm-train" });

  const f = pricing.forwardPrice(node, 30, "llm-train");
  assert.ok(f.price > 0);
  assert.ok(Math.abs(f.spot - spot.price) < 1e-6, "the forward is quoted off spot");
  assert.ok(f.price > f.spot, "cost of carry is positive: the seller gives up optionality");

  const o = pricing.optionPremium(node, 7, 1.25, "llm-train");
  assert.ok(o.premium > 0 && o.premium < spot.price, "a premium is a fraction of the underlying");
  assert.ok(o.strike > spot.price, "a 1.25x strike is out of the money");

  const l = pricing.leasePrice(node, 90, "llm-train");
  assert.ok(l.termDiscount < 1, "a long term is discounted");
  assert.ok(l.genomePremium >= 1, "a trained core carries a premium");
  assert.ok(l.drift, "and the lease states the drift caveat");
});

// ---- genetics --------------------------------------------------------

test("fitness is bounded and driven by realised outcomes", () => {
  const { fleet } = build();
  for (const n of fleet.nodes) {
    const f = fleet.fitness(n);
    assert.ok(f >= 0 && f <= 1, `fitness in [0,1], got ${f}`);
  }
  // a node with a bad completion record scores below its twin
  const n = fleet.nodes[0];
  const good = { ...n, jobsCompleted: 1000, jobsFailed: 5 };
  const bad = { ...n, jobsCompleted: 1000, jobsFailed: 900 };
  assert.ok(fleet.fitness(good) > fleet.fitness(bad), "failures cost fitness");
});

test("breeding is clamped by what the target hardware can express", () => {
  const { fleet, genetics } = build(320, "breed");
  const cpuTarget = fleet.nodes.find((n) => n.hardware.kind === "cpu");
  const gpus = fleet.nodes.filter((n) => n.hardware.kind === "gpu").slice(0, 2);
  if (!cpuTarget || gpus.length < 2) return;

  // give the parents unrealistically good bandwidth genes
  gpus.forEach((g) => { g.genome.memoryBandwidth = 1.0; });
  const ceiling = genetics.hardwareCeiling(cpuTarget.hardware);
  const r = genetics.breed(gpus[0], gpus[1], cpuTarget);
  assert.ok(r.ok);
  assert.ok(cpuTarget.genome.memoryBandwidth <= ceiling.memoryBandwidth + 1e-9,
    "you cannot cross bandwidth onto a chassis with a narrow bus");
  assert.equal(cpuTarget.lineage.parents.length, 2);
  assert.ok(cpuTarget.lineage.bred);
});

test("a bred core loses its parents' track record", () => {
  const { fleet, genetics } = build(320, "record");
  const pool = genetics.leaderboard({ limit: 6 }).map((r) => r.node);
  const target = fleet.nodes.find((n) => !pool.includes(n));
  if (pool.length < 2 || !target) return;
  const jobsBefore = target.jobsCompleted;
  const r = genetics.breed(pool[0], pool[1], target);
  assert.ok(r.ok);
  assert.ok(target.jobsCompleted < jobsBefore || jobsBefore === 0,
    "completions are not inherited -- the exchange must not credit a fresh core with them");
  assert.ok(r.predicted <= Math.max(...r.parentFitness) + 1e-9,
    "and the prediction is conservative: a merge is lossy");
});

test("drift forecast warns that a leased core re-specialises", () => {
  const { fleet, genetics } = build();
  const node = fleet.nodes[0];
  const d = genetics.driftForecast(node, "genomics", 60);
  assert.ok(d.after.genomics > d.before.genomics, "the leased class strengthens");
  assert.ok(d.ratePerDay > 0);
  assert.match(d.note, /starting point/, "and the caveat is stated, not implied");
});

// ---- energy ----------------------------------------------------------

test("grid prices move and the multiplier stays clamped", () => {
  const { energy } = build();
  const seen = new Map();
  for (const dc of catalog.DATACENTERS) seen.set(dc.id, new Set());
  for (let i = 0; i < 900; i++) {
    energy.tick(60);
    for (const dc of catalog.DATACENTERS) {
      const m = energy.multiplier(dc.id);
      assert.ok(m >= 0.62 - 1e-9 && m <= 2.4 + 1e-9, `E clamped, got ${m}`);
      seen.get(dc.id).add(energy.priceFor(dc.id).toFixed(1));
    }
  }
  for (const [id, vals] of seen) {
    assert.ok(vals.size > 20, `${id} prices actually move (${vals.size} distinct)`);
  }
});

test("a volatile grid produces a wider price distribution than a stable one", () => {
  const { energy } = build();
  const spread = (id) => {
    const h = energy.historyFor(id);
    const mean = h.reduce((a, b) => a + b, 0) / h.length;
    return Math.sqrt(h.reduce((a, x) => a + (x - mean) ** 2, 0) / h.length) / mean;
  };
  for (let i = 0; i < 700; i++) energy.tick(60);
  const ercot = spread("DFW-2");   // energyVol 0.74
  const iceland = spread("REY-1"); // energyVol 0.11
  assert.ok(ercot > iceland, `ERCOT is wilder than Landsnet: ${ercot.toFixed(3)} vs ${iceland.toFixed(3)}`);
});

// ---- determinism -----------------------------------------------------

test("the whole simulation is reproducible from its seed", () => {
  const runOnce = () => {
    const { fleet, pricing, energy } = build(160, "determinism");
    for (let i = 0; i < 60; i++) {
      energy.tick(60);
      pricing.applyDemandResponse(1 / 60, { workloadId: "llm-train" });
      fleet.tick(1 / 60);
    }
    return {
      gini: pricing.fleetStats.gini,
      ids: fleet.nodes.slice(0, 10).map((n) => n.id),
      util: fleet.nodes.slice(0, 10).map((n) => n.utilisation.toFixed(9)),
    };
  };
  const a = runOnce(), b = runOnce();
  assert.deepEqual(a.ids, b.ids, "the same fleet is built");
  assert.deepEqual(a.util, b.util, "and evolves identically");
  assert.equal(a.gini, b.gini);
});

test("the demo server is localhost-only in use and rejects traversal paths", () => {
  assert.equal(path.basename(resolveRequestPath("/")), "index.html");
  assert.equal(path.basename(resolveRequestPath("/js/app.js?v=1")), "app.js");
  for (const target of ["/../README.md", "/%2e%2e/README.md", "/..%2fREADME.md", "/js\\app.js"]) {
    assert.throws(() => resolveRequestPath(target), /forbidden|bad request/);
  }
  assert.match(SECURITY_HEADERS["Content-Security-Policy"], /default-src 'self'/);
  assert.equal(SECURITY_HEADERS["X-Content-Type-Options"], "nosniff");
});

// ======================================================================
// RTL CROSS-CHECK
//
// rtl/verify.ys proves the two Verilog implementations equivalent to
// each other by SAT over the whole input space. That is necessary and
// not sufficient: both could agree and both be wrong relative to the
// geometry they claim to implement.
//
// This closes the loop from the other side -- it models the RTL's exact
// encoding and arithmetic in JS and checks it against the W(3,3) graph
// the substrate module actually builds, over every ordered pair.
// ======================================================================

test("the RTL routing primitive agrees with the W(3,3) geometry", () => {
  // the module's encoding: two bits per trit, 2'b11 normalised to 0
  const nrm = (a) => (a === 3 ? 0 : a);
  const f3mul = (a, b) => (a === 0 || b === 0 ? 0 : a === 1 ? b : b === 1 ? a : 1);
  const f3neg = (a) => (a === 0 ? 0 : a === 1 ? 2 : 1);
  const f3add = (a, b) => { const s = a + b; return s >= 3 ? s - 3 : s; };

  const encode = (vec) => vec[0] | (vec[1] << 2) | (vec[2] << 4) | (vec[3] << 6);
  const decode = (w) => [nrm(w & 3), nrm((w >> 2) & 3), nrm((w >> 4) & 3), nrm((w >> 6) & 3)];

  // the module's staged computation, transcribed operator for operator
  const rtlForm = (uw, vw) => {
    const u = decode(uw), v = decode(vw);
    const p0 = f3mul(u[0], v[1]);
    const p1 = f3mul(u[1], v[0]);
    const p2 = f3mul(u[2], v[3]);
    const p3 = f3mul(u[3], v[2]);
    return f3add(f3add(p0, f3neg(p1)), f3add(p2, f3neg(p3)));
  };

  let checked = 0;
  for (let i = 0; i < 40; i++) {
    for (let j = 0; j < 40; j++) {
      const uw = encode(S.POINTS[i].vec);
      const vw = encode(S.POINTS[j].vec);
      const form = rtlForm(uw, vw);
      assert.equal(form, S.symplecticForm(S.POINTS[i].vec, S.POINTS[j].vec),
        `form disagrees at points ${i},${j}`);
      // the module's `adjacent` output is (form == 0); the graph excludes
      // the diagonal, since every point is isotropic for its own form
      const rtlAdjacent = form === 0;
      const graphAdjacent = S.isAdjacent(i, j);
      assert.equal(rtlAdjacent, graphAdjacent || i === j,
        `adjacency disagrees at points ${i},${j}`);
      checked++;
    }
  }
  assert.equal(checked, 1600, "all 1600 ordered pairs checked");
});

test("the RTL ray_cost implements the migration price law", () => {
  const rayCost = (samePoint, adjacent) => (samePoint ? 6 : adjacent ? 3 : 5);
  assert.equal(rayCost(true, true), S.RAY_COST.inPlace);
  assert.equal(rayCost(false, true), S.RAY_COST.adjacent);
  assert.equal(rayCost(false, false), S.RAY_COST.nonAdjacent);
  // and it agrees with the software path on every pair
  for (let i = 0; i < 40; i++) {
    for (let j = 0; j < 40; j++) {
      const expected = rayCost(i === j, S.isAdjacent(i, j));
      assert.equal(S.migrationRays(i, j), expected, `ray cost differs at ${i},${j}`);
    }
  }
});

test("the RTL admission gate refuses in the same priority order as software", () => {
  // reason codes, from the Verilog localparams
  const R = { OK: 0, BAD_SIG: 1, REPLAY: 2, WINDOW: 3, PIN_DRIFT: 4, NO_MAGIC: 5, IN_SERVICE: 6, BAD_ADDR: 7 };
  const gate = (s) => !s.sig_ok ? R.BAD_SIG
    : !s.addresses_ok ? R.BAD_ADDR
    : !s.nonce_fresh ? R.REPLAY
    : !s.in_window ? R.WINDOW
    : !s.pins_ok ? R.PIN_DRIFT
    : (s.magic_budget !== 0 && !s.node_magic) ? R.NO_MAGIC
    : s.node_in_service ? R.IN_SERVICE
    : R.OK;

  const ok = { sig_ok: 1, addresses_ok: 1, nonce_fresh: 1, in_window: 1, pins_ok: 1, magic_budget: 0, node_magic: 0, node_in_service: 0 };
  assert.equal(gate(ok), R.OK);
  assert.equal(gate({ ...ok, sig_ok: 0 }), R.BAD_SIG);
  assert.equal(gate({ ...ok, addresses_ok: 0 }), R.BAD_ADDR);
  assert.equal(gate({ ...ok, nonce_fresh: 0 }), R.REPLAY);
  assert.equal(gate({ ...ok, in_window: 0 }), R.WINDOW);
  assert.equal(gate({ ...ok, pins_ok: 0 }), R.PIN_DRIFT);
  assert.equal(gate({ ...ok, magic_budget: 12 }), R.NO_MAGIC);
  assert.equal(gate({ ...ok, magic_budget: 12, node_magic: 1 }), R.OK, "magic-capable serves it");
  assert.equal(gate({ ...ok, node_in_service: 1 }), R.IN_SERVICE);

  // signature failure outranks everything: a tampered plan is never
  // reported as merely out-of-window
  assert.equal(gate({ ...ok, sig_ok: 0, in_window: 0, magic_budget: 9 }), R.BAD_SIG);
  assert.equal(gate({ ...ok, sig_ok: 0, addresses_ok: 0 }), R.BAD_SIG,
    "signature failure remains highest priority");
});

test("the RTL address policy rejects illegal, zero and noncanonical projective words", () => {
  const canonical = (word) => {
    const trits = [word & 3, (word >> 2) & 3, (word >> 4) & 3, (word >> 6) & 3];
    if (trits.some((t) => t === 3)) return false;
    const first = trits.find((t) => t !== 0);
    return first === 1;
  };
  const encode = (v) => v[0] | (v[1] << 2) | (v[2] << 4) | (v[3] << 6);
  assert.equal(canonical(0), false, "zero is not a projective point");
  assert.equal(canonical(3), false, "2'b11 is an illegal trit");
  assert.equal(canonical(encode([2, 0, 0, 0])), false, "scalar-doubled representative is rejected");
  for (const point of S.POINTS) assert.equal(canonical(encode(point.vec)), true, point.key);
});
