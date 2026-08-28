#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_full_normalizer_stable_closure.g");
const OUT = path.resolve(ROOT, "data/e8_full_normalizer_stable_closure.json");

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) =>
      `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digest(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function execute() {
  const run = runGap(GAP, { cwd: ROOT, quiet: true });
  if (!run.ok) throw new Error(`GAP failed: ${run.stderr || run.stdout}`);
  return run.stdout;
}

function requireLine(stdout, expected) {
  if (!stdout.split(/\r?\n/).includes(expected)) {
    throw new Error(`missing GAP signature: ${expected}`);
  }
}

function parse(stdout) {
  requireLine(stdout, "C6_ACTION|order=6|fixedVectors=4,16,64,4096|cycles=1^4,2^6,3^20,6^670|permutationFixed=700");
  requireLine(stdout, "C6_SOURCES|V=A^24+B^676+C^20+D^670|H=A^0+B^684+C^0+D^682|Hfixed=684");
  requireLine(stdout, "C6_CORRECTIONS|left=B^8+D^12|right=A^24+C^20|dimensionEach=64|stable=A^24+B^684+C^20+D^682");
  requireLine(stdout, "RESTRICTIONS|C2left=J2^32|C2right=J1^64|C3left=1^16+W2^24|C3right=1^24+W2^20");
  requireLine(stdout, "TATE_EXT|Ext1(1,1)=F2|missingNonsplitJ2=32|leftTate=0|rightTate=64|identity=64=2*32");
  requireLine(stdout, "FULL_NORMALIZER|group=C13:C6|stableDimension=4160|abstractModuleIsomorphism=1|chainMap=0|dispatchable=0");
  requireLine(stdout, "ALL_FULL_NORMALIZER_STABLE_CLOSURE_CHECKS_PASS");

  const body = {
    schema: "holotrade.e8-full-normalizer-stable-closure.v1",
    evidenceClass: "EXACT_GAP_CYCLIC_MODULE_DECOMPOSITION",
    group: {
      name: "C13:C6",
      order: 78,
      complementGeneratorOrder: 6,
      actionOnC13: "a -> a^4",
      fieldActionOnW12: "Frobenius^2 on F_2^12/F_4",
    },
    complementAction: {
      naturalCarrier: "F4^6",
      fixedVectorsOfPowers: { n: 4, n2: 16, n3: 64, n6: 4096 },
      vectorOrbitProfile: { "1": 4, "2": 6, "3": 20, "6": 670 },
      permutationModuleFixedDimension: 700,
    },
    indecomposables: {
      A: { module: "J1 tensor 1", dimension: 1 },
      B: { module: "J2 tensor 1", dimension: 2 },
      C: { module: "J1 tensor W2", dimension: 2 },
      D: { module: "J2 tensor W2", dimension: 4 },
    },
    sourceDecomposition: {
      F2V2: { A: 24, B: 676, C: 20, D: 670 },
      H1LeviH4: { A: 0, B: 684, C: 0, D: 682 },
      dimensionEach: 4096,
    },
    correction: {
      c13Action: "trivial",
      left: { decomposition: { A: 0, B: 8, C: 0, D: 12 }, module: "B^8 + D^12", dimension: 64 },
      right: { decomposition: { A: 24, B: 0, C: 20, D: 0 }, module: "A^24 + C^20", dimension: 64 },
      commonStableDecomposition: { A: 24, B: 684, C: 20, D: 682 },
      c2Restriction: { left: "J2^32", right: "J1^64", recoversD26Repair: true },
      c2StableMeaning: {
        ext1TrivialSelfDimension: 1,
        uniqueNonzeroExtension: "0 -> 1 -> J2 -> 1 -> 0",
        missingNonsplitExtensions: 32,
        tateDimensionLeftCorrection: 0,
        tateDimensionRightCorrection: 64,
        identity: "64 = 2*32",
      },
      c3Restriction: { left: "1^16 + W2^24", right: "1^24 + W2^20", repairsDefect: true },
    },
    nontrivialC13Sector: {
      moduleEachSide: "W12^315",
      fullComplementExtensionUnique: true,
      reason: "nonabelian Hilbert 90 for the Frobenius^2 cyclic action on GL_315(F_2^12)",
    },
    stableClosure: {
      statement: "F2[V2] + (B^8 + D^12) ~= H1(Levi H4;F2) + (A^24 + C^20) as F2[C13:C6]-modules",
      stableDimensionEachSide: 4160,
      abstractModuleIsomorphismProved: true,
      direct4096Bridge: false,
      chainLevelIntertwinerBuilt: false,
      dispatchable: false,
    },
    rejectedCardinalityBridge: {
      carrier: "32 Hall-Janko C13 cycles",
      correctionCarrierClaimed: false,
      reason: "its C3 profile 1^5 3^9 differs from the local extension-pair profile 1^2 3^10",
    },
    theorem:
      "The previously separate C3 and D26 repairs are restrictions of one 64-dimensional C13:C6 correction pair, closing the abstract stable-module problem at dimension 4160.",
    evidenceBoundary:
      "This proves an abstract stable module isomorphism. It does not construct a chain-level 4160-by-4160 intertwiner or authorize live dispatch.",
    provenance: {
      restrictions: "W33-Theory Pass10709-10844",
      complementMatrix: "W33-Theory Pass10845-10852",
      tateExtInterpretation: "W33-Theory Pass10885-10892, commits 82c618225 and c0aa480c9",
      hallJanko32NoGo: "W33-Theory Pass10901-10908, commits 4565df3d6 and 3163897fc",
      localPredecessor: "data/e8_normalizer_stable_adapter.json",
    },
  };
  return { ...body, sha256: digest(body) };
}

function run() { return parse(execute()); }

if (require.main === module) {
  const result = run();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`);
    console.log(path.relative(process.cwd(), OUT));
  }
  console.log(JSON.stringify({
    sha256: result.sha256,
    stableDimension: result.stableClosure.stableDimensionEachSide,
    abstractModuleIsomorphism: result.stableClosure.abstractModuleIsomorphismProved,
    chainMap: result.stableClosure.chainLevelIntertwinerBuilt,
  }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
