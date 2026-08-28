#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");
const source = require("../data/e8_unitary_crossprime_fibre_differential.json");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_unitary_canonical_fibre_partition.g");
const OUT = path.resolve(ROOT, "data/e8_unitary_canonical_fibre_partition.json");

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
  const run = runGap(GAP, { cwd: ROOT, quiet: true, timeout: 180000 });
  if (!run.ok) throw new Error(`GAP failed: ${run.stderr || run.stdout}`);
  return run.stdout;
}

function requireLine(stdout, line) {
  if (!stdout.split(/\r?\n/).includes(line)) throw new Error(`missing GAP signature: ${line}`);
}

function parse(stdout) {
  requireLine(stdout, "FULL_AUT|order=23040|structure=2^5:S6|O2=32|quotient=S6");
  requireLine(stdout, "CANONICAL_PARTITION|orbits=15|size=8|blockKernel=O2|matchesFrozen=1|invariantUnderFullAut=1");
  requireLine(stdout, "FIBRE_ACTION|O2pointKernel=4|induced=C2^3|partitionCanonical=1|slotCanonical=0");
  requireLine(stdout, "ALL_UNITARY_CANONICAL_FIBRE_PARTITION_CHECKS_PASS");

  const body = {
    schema: "holotrade.e8-unitary-canonical-fibre-partition.v1",
    evidenceClass: "EXACT_GAP_FULL_GRAPH_AUTOMORPHISM_CANONICALITY",
    graph: { vertices: 120, fullAutomorphismGroup: "2^5:S6", order: 23040 },
    intrinsicTwoCore: {
      group: "O2(Aut graph)=C2^5", order: 32, characteristicInAutomorphismGroup: true,
      quotient: "S6",
    },
    partition: {
      orbitCount: 15, orbitSize: 8, blockAction: "S6", blockKernel: "O2(Aut graph)",
      equalsFrozenFibrePartition: true, invariantUnderFullGraphAutomorphismGroup: true,
      canonicalAsUnlabelledPartition: true,
    },
    fibreAction: {
      pointKernelOrder: 4, inducedGroup: "C2^3",
      individualSlotLabellingCanonical: false,
    },
    theorem:
      "The fifteen eight-state fibres are intrinsic orbits of the characteristic 2-core of the full graph automorphism group; only the within-fibre slot labels remain gauge choices.",
    evidenceBoundary:
      "Canonical graph blocks are still logical cosets, not machines or physical sites. Canonicality does not supply inventory binding.",
    sourceCertificateSha256: source.sha256,
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
  console.log(JSON.stringify({ sha256: result.sha256,
    canonicalPartition: result.partition.canonicalAsUnlabelledPartition,
    canonicalSlots: result.fibreAction.individualSlotLabellingCanonical }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
