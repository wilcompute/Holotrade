#!/usr/bin/env node
"use strict";

// Thin freezer and runtime codec for the GAP-owned exact factorization
// GL(3,2)=(C7:C3)D8.  GAP enumerates and verifies the groups, matched actions,
// 28,224 products, and 4,741,632 associativity triples.  JavaScript only
// freezes those tables and exposes a fail-closed abstract-address API.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP_WITNESS = path.resolve(__dirname, "e8_fano_zappa_szep_codec.g");
const OUT = path.resolve(ROOT, "data/e8_fano_zappa_szep_codec.json");
const ADDRESS_SPACE = "ABSTRACT_FANO_GL32_BUS";

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
  const run = runGap(GAP_WITNESS, { cwd: ROOT, quiet: true });
  if (!run.ok) {
    throw new Error(`GAP codec witness failed (${run.status ?? "missing"}): ${run.stderr || run.stdout}`);
  }
  if (!run.stdout.includes("ALL_FANO_ZAPPA_SZEP_CODEC_CHECKS_PASS")) {
    throw new Error("GAP codec completion marker missing");
  }
  return run.stdout;
}

function integers(value) {
  if (value === "") return [];
  return value.split(",").map((x) => Number.parseInt(x, 10));
}

function exactLine(stdout, prefix) {
  const line = stdout.split(/\r?\n/).find((row) => row.startsWith(`${prefix}|`));
  if (!line) throw new Error(`missing GAP row ${prefix}`);
  return line;
}

function rows(stdout, prefix) {
  return stdout.split(/\r?\n/).filter((row) => row.startsWith(`${prefix}|`));
}

function parse(stdout) {
  const version = exactLine(stdout, "VERSION").split("|")[1];
  if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error("invalid GAP version");

  const summary = exactLine(stdout, "SUMMARY").match(
    /^SUMMARY\|G=(\d+)\|H=(\d+)\|K=(\d+)\|intersection=(\d+)\|flags=(\d+)\|identity=(\d+)$/);
  if (!summary) throw new Error("invalid GAP summary");
  const summaryValues = summary.slice(1).map(Number);
  if (canonical(summaryValues) !== canonical([168, 21, 8, 1, 21, 0])) {
    throw new Error(`unexpected GAP summary ${summaryValues}`);
  }

  const structures = exactLine(stdout, "STRUCTURES").match(
    /^STRUCTURES\|G=([^|]+)\|H=([^|]+)\|K=([^|]+)$/);
  if (!structures || structures[1] !== "PSL(3,2)" ||
      structures[2] !== "C7 : C3" || structures[3] !== "D8") {
    throw new Error("unexpected factor structures");
  }

  const matched = exactLine(stdout, "MATCHED_ACTIONS").match(
    /^MATCHED_ACTIONS\|K_on_H_image=(\d+)\|K_on_H_orbits=([\d,]+)\|H_on_K_image=(\d+)\|H_on_K_orbits=([\d,]+)\|H_normal=(\d+)\|K_normal=(\d+)$/);
  if (!matched || canonical([Number(matched[1]), integers(matched[2]),
    Number(matched[3]), integers(matched[4]), Number(matched[5]), Number(matched[6])]) !==
    canonical([8, [1, 2, 4, 8, 4, 2], 21, [1, 7], 0, 0])) {
    throw new Error("unexpected matched-action structure");
  }

  const baseFlagMatch = exactLine(stdout, "BASE_FLAG").match(
    /^BASE_FLAG\|point=(\d+)\|line=([\d,]+)$/);
  if (!baseFlagMatch) throw new Error("invalid base flag");

  const hChart = rows(stdout, "H").map((line) => {
    const [, id, translation, phase, permutation] = line.split("|");
    return {
      id: Number(id),
      translation: Number(translation),
      phase: Number(phase),
      permutation: integers(permutation),
    };
  });
  const kChart = rows(stdout, "K").map((line) => {
    const [, id, rotation, reflection, permutation] = line.split("|");
    return {
      id: Number(id),
      rotation: Number(rotation),
      reflection: Number(reflection),
      permutation: integers(permutation),
    };
  });
  if (hChart.length !== 21 || kChart.length !== 8) throw new Error("incomplete factor charts");
  hChart.forEach((row, index) => {
    if (row.id !== index || row.id !== row.translation * 3 + row.phase) {
      throw new Error("noncanonical H chart");
    }
  });
  kChart.forEach((row, index) => {
    if (row.id !== index || row.id !== row.reflection * 4 + row.rotation) {
      throw new Error("noncanonical K chart");
    }
  });

  const crossH = Array.from({ length: 8 }, () => Array(21));
  const crossK = Array.from({ length: 8 }, () => Array(21));
  const crossRows = rows(stdout, "CROSS");
  if (crossRows.length !== 168) throw new Error("incomplete matched-action table");
  for (const line of crossRows) {
    const [, k, h, hp, kp] = line.split("|").map(Number);
    crossH[k][h] = hp;
    crossK[k][h] = kp;
  }

  const addresses = rows(stdout, "BUS").map((line) => {
    const [, id, h, k, permutation, inverse] = line.split("|");
    return {
      id: Number(id),
      h: Number(h),
      k: Number(k),
      permutation: integers(permutation),
      inverse: Number(inverse),
    };
  });
  if (addresses.length !== 168) throw new Error("incomplete abstract bus chart");
  addresses.forEach((row, index) => {
    if (row.id !== index || row.id !== row.h * 8 + row.k) {
      throw new Error("noncanonical bus chart");
    }
    if (new Set(row.permutation).size !== 7 ||
        Math.min(...row.permutation) !== 1 || Math.max(...row.permutation) !== 7) {
      throw new Error("invalid Fano permutation");
    }
  });

  const checksLine = exactLine(stdout, "CHECKS").replace(/\s+/g, "");
  const checks = checksLine.match(
    /^CHECKS\|decompositions=(\d+)\|products=(\d+)\|associativity=(\d+)\|coordinatewiseMismatches=(\d+)\|commutingCrossPairs=(\d+)$/);
  if (!checks) throw new Error("invalid exhaustive-check row");
  const checkValues = checks.slice(1).map(Number);
  if (canonical(checkValues.slice(0, 3)) !== canonical([168, 28224, 4741632])) {
    throw new Error(`exhaustive-check count mismatch ${checkValues}`);
  }
  if (checkValues[3] <= 0 || checkValues[3] >= 28224) {
    throw new Error("matched action was not shown to be nontrivial");
  }

  const witness = exactLine(stdout, "NONTRIVIAL_WITNESS").match(
    /^NONTRIVIAL_WITNESS\|left=(\d+)\|right=(\d+)\|zappa=(\d+)\|coordinatewise=(\d+)$/);
  if (!witness || witness[3] === witness[4]) throw new Error("missing nontrivial product witness");

  const body = {
    schema: "holotrade.e8-fano-zappa-szep-codec.v1",
    evidenceClass: "EXACT_GAP_FINITE_GROUP_CODEC",
    gapVersion: version,
    addressSpace: {
      id: ADDRESS_SPACE,
      states: 168,
      carrier: "GL(3,2)=Aut(Fano plane)",
      meaning: "abstract control-plane bus addresses",
      dispatchable: false,
      liveMachineBinding: null,
      requiredNextEvidence: "SIGNED_LIVE_INVENTORY_BINDING",
    },
    exactFactorization: {
      identity: "GL(3,2)=(C7:C3)D8",
      type: "exact Zappa-Szep factorization",
      directProduct: false,
      semidirectProductClaimed: false,
      clockFactorNormal: false,
      localFactorNormal: false,
      intersectionOrder: 1,
      uniqueDecomposition: true,
      clockFactor: { structure: "C7:C3", order: 21 },
      localFactor: { structure: "D8", order: 8 },
    },
    fano: {
      points: 7,
      lines: 7,
      flags: 21,
      singerDifferenceSet: [1, 2, 4],
      baseFlag: {
        point: Number(baseFlagMatch[1]),
        line: integers(baseFlagMatch[2]),
      },
      clockFactorActsRegularlyOnFlags: true,
    },
    charts: { clock: hChart, local: kChart },
    matchedAction: {
      convention: "k*h = crossH[k][h] * crossK[k][h]",
      crossH,
      crossK,
      localActionOnClock: {
        faithfulImageOrder: Number(matched[1]),
        orbitSizes: integers(matched[2]),
      },
      clockActionOnLocal: {
        faithfulImageOrder: Number(matched[3]),
        orbitSizes: integers(matched[4]),
      },
    },
    addresses,
    exhaustiveChecks: {
      uniqueDecompositions: checkValues[0],
      productsAgainstPermutations: checkValues[1],
      associativityTriples: checkValues[2],
      productsDifferentFromCoordinatewise: checkValues[3],
      productsEqualToCoordinatewise: checkValues[1] - checkValues[3],
      commutingCrossPairs: checkValues[4],
      coordinatewiseEqualityIdentity: `${checkValues[1] - checkValues[3]}=168*${checkValues[4]}`,
    },
    nontrivialWitness: {
      left: Number(witness[1]),
      right: Number(witness[2]),
      zappaProduct: Number(witness[3]),
      coordinatewiseProduct: Number(witness[4]),
    },
    theorem:
      "Every abstract Fano-bus automorphism has one clock/local address, and its multiplication is compiled from the nontrivial D8-by-(C7:C3) matched actions.",
    evidenceBoundary:
      "The 168 IDs are abstract group addresses. They do not identify, attest, reserve, or dispatch to live machines; an independent signed inventory binding is required.",
    provenance: {
      factorization: "W33-Theory Pass10701-10708",
      activeBus: "W33-Theory BT1422",
      implementation: "GAP-owned enumeration with a thin JavaScript freezer/codec",
    },
  };
  return { ...body, sha256: digest(body) };
}

function run() {
  return parse(execute());
}

let frozenCache;
const tableCache = new WeakMap();

function loadFrozen() {
  if (!frozenCache) frozenCache = JSON.parse(fs.readFileSync(OUT, "utf8"));
  return frozenCache;
}

function verifyFrozen(frozen = loadFrozen()) {
  const { sha256, ...body } = frozen;
  return digest(body) === sha256;
}

// GAP permutations act on the right: g*q means first g, then q.
function composePermutations(g, q) {
  return g.map((image) => q[image - 1]);
}

function productTable(chart) {
  const byPermutation = new Map(chart.map((row) => [row.permutation.join(","), row.id]));
  return chart.map((left) => chart.map((right) => {
    const id = byPermutation.get(composePermutations(left.permutation, right.permutation).join(","));
    if (id === undefined) throw new Error("factor product escaped its chart");
    return id;
  }));
}

function factorTables(frozen) {
  let tables = tableCache.get(frozen);
  if (!tables) {
    tables = {
      hProduct: productTable(frozen.charts.clock),
      kProduct: productTable(frozen.charts.local),
    };
    tableCache.set(frozen, tables);
  }
  return tables;
}

function validateId(id) {
  if (!Number.isInteger(id) || id < 0 || id >= 168) {
    throw new RangeError("abstract Fano bus ID must be an integer in [0,167]");
  }
}

function abstractAddressId(value) {
  if (typeof value === "number") {
    validateId(value);
    return value;
  }
  if (!value || typeof value !== "object" || value.addressSpace !== ADDRESS_SPACE) {
    throw new TypeError(`operation requires an ${ADDRESS_SPACE} address, not a live-machine record`);
  }
  validateId(value.id);
  return value.id;
}

function addressFromId(id, frozen = loadFrozen()) {
  validateId(id);
  const bus = frozen.addresses[id];
  const h = frozen.charts.clock[bus.h];
  const k = frozen.charts.local[bus.k];
  return Object.freeze({
    addressSpace: ADDRESS_SPACE,
    id,
    clock: Object.freeze({ translation: h.translation, phase: h.phase }),
    local: Object.freeze({ rotation: k.rotation, reflection: k.reflection }),
    permutation: Object.freeze([...bus.permutation]),
    dispatchable: false,
    liveMachineBinding: null,
    requiredNextEvidence: "SIGNED_LIVE_INVENTORY_BINDING",
  });
}

function makeAddress({ translation, phase, rotation, reflection }, frozen = loadFrozen()) {
  if (!Number.isInteger(translation) || translation < 0 || translation > 6 ||
      !Number.isInteger(phase) || phase < 0 || phase > 2 ||
      !Number.isInteger(rotation) || rotation < 0 || rotation > 3 ||
      !Number.isInteger(reflection) || reflection < 0 || reflection > 1) {
    throw new RangeError("address coordinates require translation<7, phase<3, rotation<4, reflection<2");
  }
  const h = translation * 3 + phase;
  const k = reflection * 4 + rotation;
  return addressFromId(h * 8 + k, frozen);
}

function multiplyIds(leftId, rightId, frozen = loadFrozen()) {
  validateId(leftId); validateId(rightId);
  const left = frozen.addresses[leftId];
  const right = frozen.addresses[rightId];
  const { hProduct, kProduct } = factorTables(frozen);
  const crossH = frozen.matchedAction.crossH[left.k][right.h];
  const crossK = frozen.matchedAction.crossK[left.k][right.h];
  const outH = hProduct[left.h][crossH];
  const outK = kProduct[crossK][right.k];
  return outH * 8 + outK;
}

function multiply(left, right, frozen = loadFrozen()) {
  const leftId = abstractAddressId(left);
  const rightId = abstractAddressId(right);
  return addressFromId(multiplyIds(leftId, rightId, frozen), frozen);
}

function coordinatewiseProductId(leftId, rightId, frozen = loadFrozen()) {
  validateId(leftId); validateId(rightId);
  const left = frozen.addresses[leftId];
  const right = frozen.addresses[rightId];
  const { hProduct, kProduct } = factorTables(frozen);
  return hProduct[left.h][right.h] * 8 + kProduct[left.k][right.k];
}

function inverse(address, frozen = loadFrozen()) {
  const id = abstractAddressId(address);
  return addressFromId(frozen.addresses[id].inverse, frozen);
}

function decodePermutation(permutation, frozen = loadFrozen()) {
  if (!Array.isArray(permutation) || permutation.length !== 7) {
    throw new TypeError("a Fano permutation must contain seven images");
  }
  const key = permutation.join(",");
  const row = frozen.addresses.find((candidate) => candidate.permutation.join(",") === key);
  if (!row) throw new RangeError("permutation is not a Fano-plane automorphism in the frozen carrier");
  return addressFromId(row.id, frozen);
}

if (require.main === module) {
  const result = run();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(OUT, `${JSON.stringify(result, null, 2)}\n`);
    console.log(path.relative(process.cwd(), OUT));
  }
  console.log(JSON.stringify({
    sha256: result.sha256,
    states: result.addressSpace.states,
    factorization: result.exactFactorization.identity,
    exhaustiveChecks: result.exhaustiveChecks,
    nontrivialWitness: result.nontrivialWitness,
    dispatchable: result.addressSpace.dispatchable,
  }, null, 2));
}

module.exports = {
  ADDRESS_SPACE,
  canonical,
  digest,
  execute,
  parse,
  run,
  loadFrozen,
  verifyFrozen,
  composePermutations,
  addressFromId,
  makeAddress,
  multiplyIds,
  multiply,
  coordinatewiseProductId,
  inverse,
  decodePermutation,
};
