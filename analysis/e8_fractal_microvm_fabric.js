#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");
const fano = require("../data/e8_fano_zappa_szep_codec.json");
const fibre = require("../data/e8_unitary_crossprime_fibre_differential.json");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_fractal_microvm_fabric.g");
const OUT = path.resolve(ROOT, "data/e8_fractal_microvm_fabric.json");

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
  requireLine(stdout, "GOURSAT|control=PSL(3,2)|controlOrder=168|controlSimple=1|execution=2^5:S6|executionOrder=23040|gcd=24|commonQuotient=0");
  requireLine(stdout, "FABRIC|controlChart=21x8|executionChart=15x8|states=20160|productGroupOrder=3870720|stabilizerOrder=192");
  requireLine(stdout, "BOUNDARY|stateCountEqualsA8Order=1|A8Identification=0|liveInventory=0|dispatchable=0");
  requireLine(stdout, "ALL_FRACTAL_MICROVM_FABRIC_CHECKS_PASS");

  const body = {
    schema: "holotrade.e8-fractal-microvm-fabric.v1",
    evidenceClass: "EXACT_GAP_GOURSAT_AND_COMPILED_ADDRESS_PRODUCT",
    controlPlane: {
      group: "PSL(3,2)=GL(3,2)", order: 168, simple: true,
      chart: "(C7:C3) matched with D8", factorShape: [21, 8],
      sourceCertificateSha256: fano.sha256,
    },
    executionPlane: {
      group: "2^5:S6", order: 23040, quotientByTwoCore: "S6",
      carrierStates: 120, chart: "15 duads x 8 fibre states", factorShape: [15, 8],
      pointStabilizerOrder: 192,
      sourceCertificateSha256: fibre.sha256,
    },
    independence: {
      theorem: "every subdirect coupling with both projections surjective is the direct product",
      reason: "Goursat plus simplicity of PSL(3,2); 168 does not divide 23040, so the factors have no common nontrivial quotient",
      orderGcd: 24,
      commonNontrivialQuotient: false,
      productGroupOrder: 3870720,
    },
    fabric: {
      addressShape: [21, 8, 15, 8],
      states: 20160,
      transitiveProductAction: true,
      pointStabilizerOrder: 192,
      stateCountEqualsOrderA8: true,
      a8IdentificationClaimed: false,
    },
    theorem:
      "The 168-state Fano matched-action controller and 120-state unitary fibre switch form a forced direct-product control/execution fabric with one bijective 20,160-state abstract address chart.",
    evidenceBoundary:
      "The 20,160 states are Cartesian logical addresses, not A8 elements, hosts, microVMs, or dispatchable inventory. Signed live binding remains external.",
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
  console.log(JSON.stringify({ sha256: result.sha256, states: result.fabric.states,
    commonNontrivialQuotient: result.independence.commonNontrivialQuotient }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
