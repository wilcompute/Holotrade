#!/usr/bin/env node
// ======================================================================
// GAP CERTIFICATE FOR THE W(3,3) SHAPE CATALOGUE
//
//   node analysis/w33_gap_certificate.js [--write]
//
// Runs analysis/w33_shape_catalogue.g under GAP, parses the result, and
// checks it against the JS and Python artifacts. GAP is the third
// independent route: the JS searches combinatorially, the Python check
// projects onto eigenspaces, and GAP works with the groups directly via
// GRAPE/nauty.
//
// ----------------------------------------------------------------------
// THE QUESTION IT SETTLED
//
// analysis/w33_automorphisms.js built the symmetry group by closing the
// symplectic transvections and got 25,920 = PSp(4,3). Every shape orbit
// reported there was therefore a PSp(4,3)-orbit, and that was labelled
// honestly as such -- but it left a real gap, because placement cares
// about the automorphism group of the GRAPH, which could be larger. If
// it were, shapes would have more images and the worst-case placement
// guarantees in data/w33_blocking_sat.json would be conservative.
//
// GAP settles it. The graph's full automorphism group has order 51,840,
// exactly twice PSp(4,3). But every shape orbit is UNCHANGED in size and
// every set stabiliser exactly doubles -- the extra involution carries
// each shape back into its own PSp(4,3)-orbit rather than to new images.
//
// So the blocking numbers and guarantees are not conservative. They are
// exact, and now certified against the true automorphism group rather
// than a subgroup of index two.
// ======================================================================

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const crypto = require("node:crypto");

const { runGap, findGap } = require(path.resolve(__dirname, "../scripts/run-gap.js"));

const ROOT = path.resolve(__dirname, "..");

function witnessPreamble() {
  const catPath = path.join(ROOT, "data/w33_shape_catalogue.json");
  const cat = JSON.parse(fs.readFileSync(catPath, "utf8"));
  const rows = [
    ...cat.tightSets.filter((r) => r.witness).map((r) => r.witness),
    ...cat.mOvoids.filter((r) => r.witness).map((r) => r.witness),
  ];
  return "SHAPE_WITNESSES := [\n" + rows.map((w) => "  [" + w.join(",") + "]").join(",\n") + "\n];;\n";
}

function parse(stdout) {
  const num = (re) => {
    const m = stdout.match(re);
    return m ? Number(m[1]) : null;
  };
  const bool = (re) => {
    const m = stdout.match(re);
    return m ? m[1] === "true" : null;
  };
  const orbits = [];
  // rows look like:  " 12   true     30      30     84              1080           48"
  const table = stdout.split("orbit under Aut")[1] || "";
  for (const line of table.split(/\r?\n/)) {
    const m = line.trim().match(/^(\d+)\s+(true|false)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)$/);
    if (m) {
      orbits.push({
        m: Number(m[1]), tight: m[2] === "true",
        inducedEdges: Number(m[3]), bound: Number(m[4]), boundary: Number(m[5]),
        orbitUnderAut: Number(m[6]), setStabiliser: Number(m[7]),
      });
    }
  }
  return {
    vertices: num(/vertices\s+(\d+)/),
    degree: num(/degree\s+(\d+)/),
    edges: num(/edges\s+(\d+)/),
    lambda: num(/lambda\s+\[\s*(\d+)/),
    mu: num(/mu\s+\[\s*(\d+)/),
    autOrder: num(/\|Aut\(graph\)\|\s+(\d+)/),
    pspOrder: num(/\|PSp\(4,3\)\|\s+(\d+)/),
    spOrder: num(/\|Sp\(4,3\)\|\s+(\d+)/),
    indexOverPsp: num(/index over PSp\(4,3\)\s+(\d+)/),
    pointTransitive: bool(/transitive on points\s+(true|false)/),
    rank: num(/rank \(suborbit count\)\s+(\d+)/),
    suborbits: (stdout.match(/suborbit lengths\s+\[([^\]]+)\]/) || [, ""])[1]
      .split(",").map((x) => Number(x.trim())).filter(Number.isFinite),
    pointStabiliser: num(/point stabiliser order\s+(\d+)/),
    orbitStabiliserHolds: bool(/orbit-stabiliser\s+(true|false)/),
    cliqueNumber: num(/clique number\s+(\d+)/),
    maxCliqueCount: num(/number of max cliques\s+(\d+)/),
    independenceNumber: num(/independence number\s+(\d+)/),
    ratioBound: num(/Hoffman ratio bound\s+(\d+)/),
    ratioBoundAttained: bool(/ratio bound attained\s+(true|false)/),
    ovoidExists: bool(/=> ovoid exists\s+(true|false)/),
    shapes: orbits,
  };
}

function crossCheck(gap) {
  const problems = [];
  const ok = (cond, msg) => { if (!cond) problems.push(msg); };

  ok(gap.vertices === 40 && gap.degree === 12 && gap.edges === 240,
    "graph parameters differ from SRG(40,12,2,4)");
  ok(gap.lambda === 2 && gap.mu === 4, "lambda/mu differ");
  ok(gap.autOrder === 51840, `Aut(graph) is ${gap.autOrder}, expected 51840`);
  ok(gap.pspOrder === 25920, "PSp(4,3) order differs");
  ok(gap.indexOverPsp === 2, "Aut(graph) is not an index-2 extension of PSp(4,3)");
  ok(gap.rank === 3, "the graph is not rank 3");
  ok(JSON.stringify(gap.suborbits) === JSON.stringify([1, 12, 27]),
    `suborbits ${gap.suborbits} are not 1 + 12 + 27`);
  ok(gap.cliqueNumber === 4 && gap.maxCliqueCount === 40,
    "clique data differs from 40 lines of size 4");
  ok(gap.independenceNumber === 7, "independence number differs");
  ok(gap.ratioBoundAttained === false && gap.ovoidExists === false,
    "GAP thinks an ovoid exists");

  // orbit sizes against the transvection-closure run
  const autoPath = path.join(ROOT, "data/w33_automorphisms.json");
  let orbitAgreement = null;
  if (fs.existsSync(autoPath)) {
    const auto = JSON.parse(fs.readFileSync(autoPath, "utf8"));
    orbitAgreement = [];
    for (const g of gap.shapes) {
      const kind = g.tight ? "tight" : "m-ovoid";
      const j = auto.transport.find((t) => t.m === g.m && t.kind === kind);
      if (!j) continue;
      const same = j.orbitSize === g.orbitUnderAut;
      orbitAgreement.push({
        m: g.m, kind,
        pspOrbit: j.orbitSize, autOrbit: g.orbitUnderAut, unchanged: same,
        pspStabiliser: j.setStabiliserOrder, autStabiliser: g.setStabiliser,
        stabiliserDoubled: g.setStabiliser === j.setStabiliserOrder * 2,
      });
      ok(same, `m=${g.m} ${kind}: orbit changed under the full group (${j.orbitSize} -> ${g.orbitUnderAut})`);
    }
  }

  // blocking numbers stand only because the orbits are unchanged
  const satPath = path.join(ROOT, "data/w33_blocking_sat.json");
  let guaranteesStand = null;
  if (fs.existsSync(satPath) && orbitAgreement) {
    guaranteesStand = orbitAgreement.every((r) => r.unchanged);
  }

  // shape metrics
  for (const g of gap.shapes) {
    if (g.tight) {
      ok(g.inducedEdges === g.bound, `m=${g.m}: GAP says the tight witness misses its bound`);
    }
    ok(2 * g.inducedEdges + g.boundary === 12 * g.m, `m=${g.m}: 2e+b != km`);
  }

  return { problems, orbitAgreement, guaranteesStand };
}

function run() {
  const found = findGap();
  if (!found) return { available: false };

  const preamble = witnessPreamble();
  const script = fs.readFileSync(path.join(ROOT, "analysis/w33_shape_catalogue.g"), "utf8");
  const tmp = path.join(os.tmpdir(), `holotrade_gap_${process.pid}.g`);
  fs.writeFileSync(tmp, preamble + script);

  const res = runGap(tmp, { cwd: ROOT, quiet: true });
  try { fs.unlinkSync(tmp); } catch { /* best effort */ }
  if (!res.ok) return { available: true, ok: false, stderr: res.stderr, stdout: res.stdout };

  const gap = parse(res.stdout);
  const check = crossCheck(gap);
  return {
    available: true,
    ok: check.problems.length === 0,
    schema: "holotrade.w33-gap-certificate.v1",
    gapVersion: (res.stdout.match(/version\s+([\d.]+)/) || [, "4.16.0"])[1],
    method: "GRAPE/nauty for the automorphism group; GAP CompleteSubgraphs for clique and independence",
    graph: gap,
    crossCheck: check,
    raw: res.stdout,
  };
}

if (require.main === module) {
  const res = run();
  const L = console.log;
  if (!res.available) {
    L("GAP not found. Set GAP_BIN, or install GAP.");
    process.exit(3);
  }
  if (!res.ok && res.stderr) {
    L("GAP run failed:\n" + res.stderr);
    process.exit(1);
  }

  const g = res.graph;
  L("GAP CERTIFICATE — W(3,3) SHAPE CATALOGUE");
  L("=".repeat(70));
  L(`  SRG(${g.vertices},${g.degree},${g.lambda},${g.mu}), ${g.edges} edges`);
  L(`  |Aut(graph)|         ${g.autOrder}   = ${g.indexOverPsp} x |PSp(4,3)| = ${g.pspOrder}`);
  L(`  rank ${g.rank}, suborbits ${JSON.stringify(g.suborbits)}, point stabiliser ${g.pointStabiliser}`);
  L(`  clique number ${g.cliqueNumber} with ${g.maxCliqueCount} maximum cliques (the lines)`);
  L(`  independence number ${g.independenceNumber}, ratio bound ${g.ratioBound}, attained ${g.ratioBoundAttained}`);
  L("");
  L("DOES THE FULL GROUP CHANGE THE SHAPE ORBITS?");
  L("   m   kind      PSp orbit   Aut orbit   unchanged   PSp stab   Aut stab   doubled");
  for (const r of res.crossCheck.orbitAgreement || []) {
    L(`  ${String(r.m).padStart(2)}   ${r.kind.padEnd(8)}  ${String(r.pspOrbit).padStart(9)}   ${String(r.autOrbit).padStart(9)}   `
      + `${String(r.unchanged).padStart(9)}   ${String(r.pspStabiliser).padStart(8)}   ${String(r.autStabiliser).padStart(8)}   ${r.stabiliserDoubled}`);
  }
  L("");
  L(res.crossCheck.guaranteesStand
    ? "  => every orbit is unchanged, so the blocking numbers and placement"
      + "\n     guarantees are EXACT, not conservative -- now certified against"
      + "\n     the true automorphism group rather than an index-2 subgroup."
    : "  => orbits changed; the guarantees need recomputing.");
  L("");
  L(res.crossCheck.problems.length
    ? "PROBLEMS:\n  " + res.crossCheck.problems.join("\n  ")
    : "ALL CROSS-CHECKS PASS");

  if (process.argv.includes("--write")) {
    const out = path.join(ROOT, "data/w33_gap_certificate.json");
    const payload = { ...res };
    delete payload.raw;
    payload.digest = crypto.createHash("sha256")
      .update(JSON.stringify({ graph: payload.graph, crossCheck: payload.crossCheck }))
      .digest("hex");
    fs.writeFileSync(out, JSON.stringify(payload, null, 2));
    L(`\nwritten: ${path.relative(process.cwd(), out)}`);
  }
  process.exit(res.ok ? 0 : 1);
}

module.exports = { run, parse, crossCheck };
