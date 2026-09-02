#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");
const engineFabric = require("../data/e8_fractal_microvm_fabric.json");
const w33Certificate = require("../data/w33_gap_certificate.json");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_holobox_engine_goursat_bridge.g");
const OUT = path.resolve(ROOT, "data/e8_holobox_engine_goursat_bridge.json");

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

function lineWithPrefix(stdout, prefix) {
  const line = stdout.split(/\r?\n/).find((entry) => entry.startsWith(`${prefix}|`));
  if (!line) throw new Error(`missing GAP signature ${prefix}`);
  return line;
}

function fields(line) {
  return Object.fromEntries(line.split("|").slice(1).map((entry) => {
    const split = entry.indexOf("=");
    if (split < 1) throw new Error(`malformed GAP field ${entry}`);
    return [entry.slice(0, split), entry.slice(split + 1)];
  }));
}

function integer(value, label) {
  if (!/^[0-9]+$/.test(value)) throw new Error(`invalid integer for ${label}: ${value}`);
  return Number(value);
}

function parse(stdout) {
  if (!stdout.split(/\r?\n/).includes(
    "ALL_HOLOBOX_ENGINE_GOURSAT_BRIDGE_CHECKS_PASS")) {
    throw new Error("GAP bridge did not reach its all-pass sentinel");
  }

  const router = fields(lineWithPrefix(stdout, "ROUTER"));
  const engine = fields(lineWithPrefix(stdout, "ENGINE"));
  const goursat = fields(lineWithPrefix(stdout, "GOURSAT"));
  const carrier = fields(lineWithPrefix(stdout, "CARRIER"));
  const boundary = fields(lineWithPrefix(stdout, "BOUNDARY"));
  if (router.connected !== "PSp(4,3)" || router.full !== "PGSp(4,3)" ||
      router.normalOrders !== "1,25920,51840" ||
      engine.control !== "PSL(3,2)" || engine.execution !== "2^5:S6" ||
      engine.engineAbelianization !== "C2xC2" ||
      goursat.connectedKind !== "direct_product" ||
      goursat.fullKinds !== "direct_product_plus_three_C2_pullbacks" ||
      boundary.dispatchable !== "0") {
    throw new Error("unexpected GAP bridge classification");
  }

  // The printed CHARACTER form puts its label in position one rather than in
  // a key=value field, so recover that token before parsing the remaining row.
  const parsedCharacters = stdout.split(/\r?\n/)
    .filter((line) => line.startsWith("CHARACTER|"))
    .map((line) => {
      const parts = line.split("|");
      const label = parts[1];
      const row = fields([parts[0], ...parts.slice(2)].join("|"));
      return {
        label,
        quotient: "C2",
        kernelOrder: integer(row.kernelOrder, `${label}.kernelOrder`),
        kernelStructure: row.kernelStructure,
        translationCoreIntersection: integer(row.translationIntersection,
          `${label}.translationIntersection`),
        permutationComplementIntersection: integer(row.permutationIntersection,
          `${label}.permutationIntersection`),
        canonical: false,
        dispatchable: false,
      };
    });
  if (parsedCharacters.map((row) => row.label).join(",") !==
      "permutation_sign,translation_parity,translation_xor_sign") {
    throw new Error("the three execution parity characters were not recovered");
  }

  const body = {
    schema: "holotrade.e8-holobox-engine-goursat-bridge.v1",
    evidenceClass: "EXACT_GAP_NORMAL_QUOTIENT_AND_SUBDIRECT_CLASSIFICATION",
    router: {
      carrier: "one local radix-40 W33 digit",
      vertices: integer(router.vertices, "router.vertices"),
      degree: integer(router.degree, "router.degree"),
      connectedGroup: router.connected,
      connectedOrder: integer(router.connectedOrder, "router.connectedOrder"),
      connectedSimple: router.connectedSimple === "1",
      fullGroup: router.full,
      fullOrder: integer(router.fullOrder, "router.fullOrder"),
      fullAbelianization: router.fullAbelianization,
      fullNormalSubgroupOrders: router.normalOrders.split(",").map(Number),
      connectedAndFullPointStabilizers: router.pointStabilizers.split(",").map(Number),
      outerParityVisibleInFullPointStabilizer:
        carrier.routerOuterVisibleInPointStabilizer === "1",
      sourceGraphCertificateDigest: digest(w33Certificate),
    },
    engine: {
      controlGroup: engine.control,
      controlOrder: integer(engine.controlOrder, "engine.controlOrder"),
      controlPerfect: engine.controlPerfect === "1",
      executionGroup: engine.execution,
      executionOrder: integer(engine.executionOrder, "engine.executionOrder"),
      executionAbelianization: engine.executionAbelianization,
      actionGroupOrder: integer(engine.engineOrder, "engine.engineOrder"),
      actionAbelianization: engine.engineAbelianization,
      logicalChartStates: engineFabric.fabric.states,
      logicalChartShape: engineFabric.fabric.addressShape,
      sourceFabricCertificateSha256: engineFabric.sha256,
    },
    goursat: {
      connectedRouter: {
        subdirectClasses: integer(goursat.connectedClasses,
          "goursat.connectedClasses"),
        classification: "forced direct product",
        groupOrder: integer(goursat.connectedEngineOrder,
          "goursat.connectedEngineOrder"),
        reason:
          "PSp(4,3) is simple, and its order 25920 does not divide the engine action order 3870720.",
      },
      fullRouter: {
        subdirectClasses: integer(goursat.fullClasses, "goursat.fullClasses"),
        classification: "one direct product plus three C2 fibre products",
        directProductOrder: integer(goursat.fullProductOrder,
          "goursat.fullProductOrder"),
        parityFibreProductOrder: integer(goursat.parityPullbackOrder,
          "goursat.parityPullbackOrder"),
        executionOnlyEnumerationOrders: goursat.fullExecutionClassOrders
          .split(",").map(Number),
        parityCharacters: parsedCharacters,
        canonicalChoice: false,
      },
    },
    localCarrier: {
      addressShape: [40, engineFabric.fabric.states],
      logicalStates: integer(carrier.states, "carrier.states"),
      connectedOrParityActionStabilizerOrder:
        integer(carrier.connectedOrParityStabilizer,
          "carrier.connectedOrParityStabilizer"),
      fullIndependentActionStabilizerOrder:
        integer(carrier.fullProductStabilizer, "carrier.fullProductStabilizer"),
    },
    theorem:
      "For one W33 radix digit, connected PSp(4,3) routing is symmetry-independent of the 20,160-state engine action. Full PGSp(4,3) routing admits exactly three additional index-two Goursat pullbacks, selected by translation parity, S6 sign, or their XOR.",
    evidenceBoundary:
      "The three parity pullbacks are exact but noncanonical. No parity is inferred from a router vertex or engine state, no recursive depth-n parity composition has been selected, and no live host, microVM, or dispatch binding is produced.",
    dispatchable: false,
    recursiveParityPolicyBuilt: boundary.recursiveParityPolicyBuilt === "1",
    liveBindingBuilt: boundary.liveBindingBuilt === "1",
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
    localStates: result.localCarrier.logicalStates,
    connectedClasses: result.goursat.connectedRouter.subdirectClasses,
    fullClasses: result.goursat.fullRouter.subdirectClasses,
    dispatchable: result.dispatchable,
  }, null, 2));
}

module.exports = { canonical, digest, execute, fields, parse, run };
