#!/usr/bin/env node
"use strict";

// Canonical freezer for the GAP-owned maximum-partial-spread hole geometry.
// GAP and GRAPE do all enumeration, automorphism, group-isomorphism, orbital,
// and graph-isomorphism work.  This file only guards exact output signatures,
// packages the result for backend consumers, and freezes a canonical digest.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const PROFILE_GAP = path.resolve(__dirname, "e8_unitary_hole_sector_probe.g");
const COSET_GAP = path.resolve(__dirname, "e8_unitary_kummer_duad_bridge.g");
const OUT = path.resolve(ROOT, "data/e8_unitary_hole_sectors.json");

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

function executeOne(script, marker) {
  const run = runGap(script, { cwd: ROOT, quiet: true });
  if (!run.ok) throw new Error(`GAP failed (${run.status ?? "missing"}): ${run.stderr || run.stdout}`);
  if (!run.stdout.includes(marker)) throw new Error(`GAP completion marker missing: ${marker}`);
  return run.stdout;
}

function execute() {
  return {
    profiles: executeOne(PROFILE_GAP, "ALL_HOLE_CHECKS_PASS"),
    cosets: executeOne(COSET_GAP, "ALL_KUMMER_DUAD_NO_GO_CHECKS_PASS"),
  };
}

function requireText(text, fragment, label) {
  if (!text.includes(fragment)) throw new Error(`missing ${label}: ${fragment}`);
}

function parse(stdout) {
  const { profiles, cosets } = stdout;
  const version = profiles.match(/^VERSION\|([^\r\n]+)/m)?.[1]?.trim();
  if (!version || !/^\d+\.\d+\.\d+$/.test(version)) throw new Error("missing GAP version");

  const profileChecks = [
    [profiles, "HOLE_PROFILE|2|maxima=72|orbits=[ 72 ]|lineAut=51840|stabilizer=720|holes=15|degree=[ 6 ]|attachment=[ 6 ]|diameter=2|holeAut=720|holeStructure=S6|stabilizerStructure=S6", "q=2 profile"],
    [profiles, "|lineCuts=[ [ 0, 12 ], [ 3, 15 ] ]|adjCommon=[ 1 ]|nonadjCommon=[ 3 ]", "q=2 intersection profile"],
    [profiles, "HOLE_PROFILE|3|maxima=2268|orbits=[ 2268 ]|lineAut=26127360|stabilizer=11520|holes=120|degree=[ 20 ]|attachment=[ 16 ]|diameter=2|holeAut=23040", "q=3 profile"],
    [profiles, "|lineCuts=[ [ 0, 32 ], [ 6, 80 ] ]|adjCommon=[ 4 ]|nonadjCommon=[ 2, 4 ]", "q=3 intersection profile"],
    [profiles, "FACTORS|2|[ [ x_1-6, 1 ], [ x_1-1, 9 ], [ x_1+3, 5 ] ]", "q=2 spectrum"],
    [profiles, "FACTORS|3|[ [ x_1-20, 1 ], [ x_1-8, 5 ], [ x_1-4, 45 ], [ x_1, 9 ], [ x_1+4, 60 ] ]", "q=3 spectrum"],
    [profiles, "EXCEPTIONAL_OUTER|twoCore=32|quotient=S6|stabilizerQuotient=S6|holeCentre=1|wd6Centre=2|foldedQ6Iso=1", "folded-Q6 group identification"],
  ];
  const cosetChecks = [
    [cosets, "holeVertexId=[ 192, 1485 ]", "hole stabilizer ID"],
    [cosets, "duadVertexId=[ 192, 1472 ]", "duad stabilizer ID"],
    [cosets, "KUMMER_DUAD|foldedVertices=32|halves=16+16|duads=120|fullGroup=23040|colourGroup=11520", "natural duad action"],
    [cosets, "|orbitalDegrees=[ [ 16 ], [ 24 ], [ 4 ], [ 24 ], [ 48 ], [ 3 ] ]|degree20Orbitals=1|holeIsomorphic=0", "duad no-go"],
    [cosets, "ACTION_NO_GO|holeOrbitalDegrees=[ [ 48 ], [ 48 ], [ 16 ], [ 4 ], [ 3 ] ]", "hole orbital census"],
    [cosets, "FOLDED_COSET_SEARCH|embeddingClasses=1|profiles=[ [ [ 16 ], [ 48 ], [ 4 ], [ 3 ], [ 48 ] ] ]|found=1|stabilizerId=[ 192, 1485 ]|cosets=120", "coset graph identification"],
  ];
  for (const [text, fragment, label] of [...profileChecks, ...cosetChecks]) {
    requireText(text, fragment, label);
  }

  const body = {
    schema: "holotrade.e8-unitary-hole-sectors.v1",
    evidenceClass: "EXACT_GAP_GRAPE_FINITE_GEOMETRY",
    gapVersion: version,
    profiles: [
      {
        q: 2,
        carrier: "H(3,4)=GQ(4,2)",
        maximumPartialSpreads: 72,
        maximumOrbitSizes: [72],
        ambientLineGraphAutomorphismOrder: 51840,
        spreadStabilizerOrder: 720,
        holes: 15,
        holeGraph: {
          degree: 6,
          diameter: 2,
          adjacentCommonNeighbours: [1],
          nonadjacentCommonNeighbours: [3],
          spectrum: [[6, 1], [1, 9], [-3, 5]],
          automorphismOrder: 720,
          certifiedParameters: "SRG(15,6,1,3)",
          w33PriorModel: "KG(6,2)",
        },
        coveredAttachmentDegree: 6,
        originalLineHoleIntersections: [[0, 12], [3, 15]],
      },
      {
        q: 3,
        carrier: "H(3,9)=GQ(9,3)",
        maximumPartialSpreads: 2268,
        maximumOrbitSizes: [2268],
        ambientLineGraphAutomorphismOrder: 26127360,
        spreadStabilizerOrder: 11520,
        holes: 120,
        holeGraph: {
          degree: 20,
          diameter: 2,
          adjacentCommonNeighbours: [4],
          nonadjacentCommonNeighbours: [2, 4],
          stronglyRegular: false,
          spectrum: [[20, 1], [8, 5], [4, 45], [0, 9], [-4, 60]],
          automorphismOrder: 23040,
        },
        coveredAttachmentDegree: 16,
        originalLineHoleIntersections: [[0, 32], [6, 80]],
      },
    ],
    q3Symmetry: {
      group: "(F2^6/<111111>) semidirect S6",
      order: 23040,
      twoCoreOrder: 32,
      quotient: "S6",
      centreOrder: 1,
      isomorphicToFoldedQ6AutomorphismGroup: true,
      isomorphicToWeylD6: false,
      sameOrderAsWeylD6: true,
      weylD6CentreOrder: 2,
      spreadStabilizer: {
        structure: "2^4:S6",
        order: 11520,
        quotientByTwoCore: "S6",
        w33KummerModel: "colour-preserving automorphism group of the folded-Q6 Kummer 16_6 Levi graph",
      },
    },
    q3CosetModel: {
      carrier: "G/H",
      group: "Aut(folded Q6)",
      groupOrder: 23040,
      stabilizerSmallGroupId: [192, 1485],
      stabilizerOrder: 192,
      cosets: 120,
      embeddingConjugacyClasses: 1,
      nontrivialOrbitalDegrees: [16, 48, 4, 3, 48],
      adjacencyOrbitalDegrees: [16, 4],
      graphIsomorphismToH39HoleGraph: true,
    },
    naturalKummerDuadNoGo: {
      carrier: "120 point-duads / antipodal square faces of folded Q6",
      stabilizerSmallGroupId: [192, 1472],
      stabilizerStructure: "S4 x D8",
      nontrivialOrbitalDegrees: [16, 24, 4, 24, 48, 3],
      uniqueDegree20TwoOrbitalUnion: true,
      graphIsomorphismToH39HoleGraph: false,
      conclusion: "The symmetry-group bridge is exact, but the obvious 120-duad permutation representation is the wrong carrier.",
    },
    theorem: {
      allMaximumPartialSpreadsSingleAmbientOrbit: true,
      q3HoleGraphClassifiedByExactCosetAction: true,
      failedNaturalCarrierRetainedAsExecutableNoGo: true,
    },
    provenance: {
      e8Residue: "W33-Theory Pass9961-9984 unitary branch",
      maximumPartialSpreads: "W33-Theory Pass7255-7256 and the sharp Hermitian partial-spread literature",
      kummerFoldedCube: "W33-Theory Pass7001-7016 and Pass7065-7080",
    },
    evidenceBoundary:
      "This is an exact finite graph/group/coset classification. It is not a deployed network, a hardware topology, a K3 surface realization, or a claim that GAP point IDs name live hosts.",
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
    q3: result.profiles[1],
    coset: result.q3CosetModel,
    duadNoGo: result.naturalKummerDuadNoGo,
  }, null, 2));
}

module.exports = { execute, parse, run, canonical, digest };
