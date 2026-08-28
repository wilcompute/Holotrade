#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_normalizer_stable_adapter.g");
const OUT = path.resolve(ROOT, "data/e8_normalizer_stable_adapter.json");

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

function requireLine(stdout, line) {
  if (!stdout.split(/\r?\n/).includes(line)) throw new Error(`missing GAP signature: ${line}`);
}

function parse(stdout) {
  requireLine(stdout,
    "NORMALIZER_STABLE|direct4096=0|c3Local=4104|c13c3=4200|c3Correction=8|inducedCorrection=104");
  requireLine(stdout,
    "C2_DEFECT|V2Inv=2080|H1Inv=2048|difference=32|V2Blocks=J1^64+J2^2016|H1Blocks=J2^2048");
  requireLine(stdout,
    "D26_FIXED_SECTOR|dimension=316|V2=J1^64+J2^126|H1=J2^158|nontrivial=W12^315|nontrivialFixedEach=1890");
  requireLine(stdout,
    "Q6_ANTIPODAL_REPAIR|vertices=64|pairs=32|cubeBlocks=J2^32|rightExternal=J1^64|C13Action=trivial|stableDimension=4160|proved=1");
  requireLine(stdout,
    "TRANSLATION_NO_GO|localC3PairingChoices=3|pairsEach=32|C13EquivariantTranslation=0");
  requireLine(stdout, "FULL_C6_BOUNDARY|compatibleGlueBuilt=0|dispatchable=0");
  requireLine(stdout, "ALL_NORMALIZER_STABLE_ADAPTER_CHECKS_PASS");

  const body = {
    schema: "holotrade.e8-normalizer-stable-adapter.v1",
    evidenceClass: "EXACT_GAP_MODULE_ARITHMETIC",
    sourceDimension: 4096,
    oddBranch: {
      group: "C13:C3",
      localC3StableDimension: 4104,
      inducedStableDimension: 4200,
      localCorrectionDimensionEachSide: 8,
      inducedCorrectionDimensionEachSide: 104,
      leftCorrection: "Ind_C3^(C13:C3)(4*W2)",
      rightCorrection: "Ind_C3^(C13:C3)(8*1)",
      proved: true,
    },
    d26Branch: {
      group: "D26=C13:C2 with inversion",
      sourceInvariantDimensions: { F2V2: 2080, H1LeviH4: 2048, defect: 32 },
      sourceBlocks: { F2V2: "J1^64 + J2^2016", H1LeviH4: "J2^2048" },
      c13FixedSector: {
        dimension: 316,
        F2V2: "J1^64 + J2^126",
        H1LeviH4: "J2^158",
        invariantDimensions: { F2V2: 190, H1LeviH4: 158 },
      },
      nontrivialC13Sector: {
        moduleEachSide: "W12^315",
        dimension: 3780,
        c2InvariantDimensionEachSide: 1890,
        compatibleD26ExtensionUnique: true,
      },
      stableDimension: 4160,
      leftCorrection: {
        carrier: "external vertices of Q6 with antipodal C2 action and trivial C13 action",
        states: 64,
        antipodalPairs: 32,
        module: "J2^32",
      },
      rightCorrection: {
        carrier: "external 64-state trivial module (cardinality modeled by F4^3)",
        states: 64,
        module: "J1^64",
      },
      stableIdentity:
        "F2[V2] + J2^32 ~= H1(Levi H4;F2) + J1^64 as F2[D26]-modules, with C13 trivial on both corrections",
      naturalFixedConeIsCorrectionCarrier: false,
      translationBoundary: {
        localC3CompatiblePairings: 3,
        pairsEach: 32,
        c13EquivariantTranslationExists: false,
      },
      proved: true,
    },
    fullNormalizer: {
      group: "C13:C6",
      direct4096Bridge: false,
      compatibleStableGlueBuilt: false,
      dispatchable: false,
      reason:
        "The C3 and C2 restrictions are repaired exactly, but no single compatible C13:C6 module intertwiner has been constructed.",
    },
    provenance: {
      c3Defect: "W33-Theory Pass10773-10788",
      d26Defect: "W33-Theory Pass10789-10844",
      translationNoGo: "W33-Theory Pass10845-10868",
      q6Carrier: "HoloTrade external GAP construction on the 64 binary 6-cube vertices",
    },
    evidenceBoundary:
      "Stable module equivalence means auxiliary state was added to both sides. It is not a direct equivalence, a live transport map, or authority to dispatch workloads.",
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
    oddStableDimension: result.oddBranch.inducedStableDimension,
    d26StableDimension: result.d26Branch.stableDimension,
    fullNormalizerDispatchable: result.fullNormalizer.dispatchable,
  }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
