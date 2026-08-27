#!/usr/bin/env node
"use strict";

// Thin freezer for the GAP-owned H(3,4)/H(3,9) elastic-ladder witness.
// No geometry is recomputed here: GAP emits the full profile, explicit
// maximum partial spread, and every rung.  This wrapper parses, cross-checks,
// hashes, and optionally freezes that exact output for backend consumers.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_unitary_elastic_ladders.g");
const OUT = path.resolve(ROOT, "data/e8_unitary_elastic_ladders.json");

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function execute() {
  const run = runGap(GAP, { cwd: ROOT, quiet: true });
  if (!run.ok) throw new Error(`GAP failed (${run.status ?? "missing"}): ${run.stderr || run.stdout}`);
  if (!run.stdout.includes("ALL_CHECKS_PASS")) throw new Error("GAP completion marker missing");
  return run.stdout;
}

function parse(stdout) {
  const profiles = new Map();
  let gapVersion = null;
  for (const line of stdout.trim().split(/\r?\n/)) {
    if (line.startsWith("VERSION|")) {
      gapVersion = line.slice("VERSION|".length).trim() || null;
    } else if (line.startsWith("PROFILE|")) {
      const [_, q0, points, lines, lineSize, degree, lambda, mu, maxPartial,
        maximumCount, covered, holes, fullSpreadSize] = line.split("|").map(Number);
      const q = q0;
      profiles.set(q, {
        q,
        field: q * q,
        identification: q === 2 ? "H(3,4)=GQ(4,2)" : "H(3,9)=GQ(9,3)",
        points,
        lines,
        lineSize,
        degree,
        lambda,
        mu,
        maxPartialSpreadLines: maxPartial,
        maximumPartialSpreadCount: maximumCount,
        coveredPoints: covered,
        holePoints: holes,
        fullSpreadWouldNeedLines: fullSpreadSize,
        hasFullSpread: maxPartial === fullSpreadSize,
        rungs: [],
      });
    } else if (line.startsWith("WITNESS|")) {
      const first = line.indexOf("|", 8);
      const q = Number(line.slice(8, first));
      profiles.get(q).partialSpread = JSON.parse(line.slice(first + 1));
    } else if (line.startsWith("RUNG|")) {
      const [_, q, rung, vertices, internalEdges, boundaryEdges,
        inducedDegree, outsideAttachmentDegree] = line.split("|").map(Number);
      profiles.get(q).rungs.push({
        rung,
        vertices,
        internalEdges,
        boundaryEdges,
        inducedDegree,
        outsideAttachmentDegree,
      });
    }
  }
  if (profiles.size !== 2 || !profiles.has(2) || !profiles.has(3)) {
    throw new Error("expected q=2 and q=3 GAP profiles");
  }

  for (const row of profiles.values()) {
    const s = row.q ** 2;
    const t = row.q;
    if (row.partialSpread.length !== row.maxPartialSpreadLines) throw new Error(`q=${row.q}: witness size`);
    if (new Set(row.partialSpread.flat()).size !== row.coveredPoints) throw new Error(`q=${row.q}: witness overlap`);
    if (row.rungs.length !== row.maxPartialSpreadLines) throw new Error(`q=${row.q}: rung count`);
    for (const rung of row.rungs) {
      const i = rung.rung;
      const expected = {
        vertices: (s + 1) * i,
        internalEdges: ((s + 1) * i * (s + i - 1)) / 2,
        boundaryEdges: (s + 1) * i * (s * t + 1 - i),
        inducedDegree: s + i - 1,
        outsideAttachmentDegree: i,
      };
      for (const [key, value] of Object.entries(expected)) {
        if (rung[key] !== value) throw new Error(`q=${row.q}, rung=${i}: ${key}`);
      }
      rung.spectralMinimumBoundary = rung.boundaryEdges;
      rung.attainsSpectralMinimum = true;
    }
  }

  const body = {
    schema: "holotrade.e8-unitary-elastic-ladders.v1",
    evidenceClass: "EXACT_GAP_FINITE_GEOMETRY",
    gapVersion,
    profiles: [...profiles.values()].sort((a, b) => a.q - b.q),
    theorem: {
      hermitianModelsRebuilt: true,
      maximumPartialSpreadsExhaustive: true,
      everyRungConnectedRegularAndSpectrallyOptimal: true,
      neitherUnitaryCarrierHasFullSpread: [...profiles.values()].every((row) => !row.hasFullSpread),
      exactHoleSectors: { H34: 15, H39: 120 },
    },
    provenance: {
      e8ResidueIdentifications:
        "W33-Theory analysis/w33_pass9961_9984_the_unitary_branch.py and its independent driver",
      maximumPriorArt:
        "W33-Theory Passes 7255-7256; De Beule-Klein-Metsch-Storme sharp bound (q^3+q+2)/2",
      classicalPartialSpreadReference:
        "Ihringer-Sin-Xiang, arXiv:1604.06172, and the cited earlier sharp bound",
    },
    evidenceBoundary:
      "The standard Hermitian incidence models are isomorphic to the E8 residue geometries certified in W33-Theory, but this file does not construct an E8-coordinate isomorphism. The ladders are exact topology plans, not deployed inventory or hardware SLAs.",
  };
  return { ...body, sha256: digest(body) };
}

function run() {
  return parse(execute());
}

if (require.main === module) {
  const result = run();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`);
    console.log(path.relative(process.cwd(), OUT));
  }
  console.log(JSON.stringify({
    sha256: result.sha256,
    profiles: result.profiles.map((row) => ({
      q: row.q,
      carrier: row.identification,
      maxPartialSpreadLines: row.maxPartialSpreadLines,
      coveredPoints: row.coveredPoints,
      holePoints: row.holePoints,
      maximumPartialSpreadCount: row.maximumPartialSpreadCount,
    })),
  }, null, 2));
}

module.exports = { execute, parse, run, canonical, digest };
