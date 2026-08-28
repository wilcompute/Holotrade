#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.resolve(__dirname, "e8_unitary_crossprime_fibre_differential.g");
const OUT = path.resolve(ROOT, "data/e8_unitary_crossprime_fibre_differential.json");

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
  if (!run.ok || !run.stdout.includes("ALL_CROSSPRIME_FIBRE_DIFFERENTIAL_CHECKS_PASS")) {
    throw new Error(`GAP cross-prime witness failed: ${run.stderr || run.stdout}`);
  }
  return run.stdout;
}

function required(stdout, fragment, label) {
  if (!stdout.replace(/\s+/g, "").includes(fragment.replace(/\s+/g, ""))) {
    throw new Error(`missing ${label}: ${fragment}`);
  }
}

function csv(text) {
  return text === "" ? [] : text.split(",").map(Number);
}

function parse(stdout) {
  const version = stdout.match(/^VERSION\|([^\r\n]+)/m)?.[1]?.trim();
  if (!/^\d+\.\d+\.\d+$/.test(version || "")) throw new Error("GAP version missing");
  const signatures = [
    ["GROUP_TOWER|G=23040|H=192|N=32|HcapN=4|HN=1536|Nquotient=C2 x C2 x C2|HNquotient=C2 x S4|Gquotient=S6", "group tower"],
    ["FIBRE_QUOTIENT|vertices=120|blocks=15|fibre=8|blockAction=S6|kernel=32|equitable=1|weights=diag4,T6x2,KG0", "weighted quotient"],
    ["SPECTRAL_DESCENT|q3=20^1,8^5,4^45,0^9,-4^60|quotient=20^1,8^5,0^9|q2KG=6^1,1^9,-3^5|zero9FromKGplus1=1", "spectral descent"],
    ["LOCAL_FIBRE|group=C2^3|graph=K4,4|spectrum=4^1,0^6,-4^1|crossT6Connector=C16", "local fibre"],
    ["MOD2_DIFFERENTIAL|squareZero=1|rank=40|image=40|kernel=80|homology=40|graded=40,40,40", "mod-2 differential"],
  ];
  for (const [fragment, label] of signatures) required(stdout, fragment, label);

  const blocks = Array(15);
  const quotient = Array(15);
  for (const row of stdout.split(/\r?\n/)) {
    let match = row.match(/^BLOCK\|(\d+)\|duad=(\d+),(\d+)\|vertices=([\d,]+)$/);
    if (match) {
      const id = Number(match[1]);
      blocks[id] = {
        blockId: id,
        duad: [Number(match[2]), Number(match[3])],
        vertices: csv(match[4]),
      };
    }
    match = row.match(/^QROW\|(\d+)\|([\d,]+)$/);
    if (match) quotient[Number(match[1])] = csv(match[2]);
  }
  if (blocks.some((row) => !row) || quotient.some((row) => !row)) {
    throw new Error("incomplete GAP block chart");
  }
  const vertices = blocks.flatMap((row) => row.vertices);
  const duadKeys = blocks.map((row) => row.duad.join(","));
  if (new Set(vertices).size !== 120 || Math.min(...vertices) !== 0 ||
      Math.max(...vertices) !== 119 || blocks.some((row) => row.vertices.length !== 8) ||
      new Set(duadKeys).size !== 15 || quotient.some((row) => row.length !== 15)) {
    throw new Error("invalid 120-to-15 fibre chart");
  }
  const vertexToAddress = Array(120);
  blocks.forEach((block) => block.vertices.forEach((vertex, fibreSlot) => {
    vertexToAddress[vertex] = { blockId: block.blockId, duad: block.duad, fibreSlot };
  }));

  for (let i = 0; i < 15; i += 1) {
    for (let j = 0; j < 15; j += 1) {
      const intersection = blocks[i].duad.filter((x) => blocks[j].duad.includes(x)).length;
      const expected = i === j ? 4 : (intersection === 1 ? 2 : 0);
      if (quotient[i][j] !== expected) throw new Error(`weighted quotient mismatch ${i},${j}`);
    }
  }

  const body = {
    schema: "holotrade.e8-unitary-crossprime-fibre-differential.v1",
    evidenceClass: "EXACT_GAP_CROSSPRIME_FINITE_GEOMETRY_AND_LINEAR_ALGEBRA",
    gapVersion: version,
    groupTower: {
      group: "2^5:S6",
      groupOrder: 23040,
      cosetStabilizerOrder: 192,
      twoCore: "C2^5",
      twoCoreOrder: 32,
      stabilizerIntersectionTwoCore: "C2^2",
      stabilizerIntersectionOrder: 4,
      affineFibreGroup: "C2^3",
      fibreExtensionOrder: 1536,
      fibreStabilizerQuotient: "C2 x S4",
      blockAction: "S6",
      blockActionKernelOrder: 32,
    },
    crossPrimeQuotient: {
      q3Carrier: "H(3,9) maximum-partial-spread hole graph",
      q3Vertices: 120,
      q2Carrier: "H(3,4) maximum-partial-spread hole graph = KG(6,2)",
      q2Vertices: 15,
      blocks: 15,
      fibreSize: 8,
      equitable: true,
      weightedFormula: "Q = 4*I + 2*A(T(6))",
      sameBlockWeight: 4,
      intersectingDuadsWeight: 2,
      disjointDuadsWeight: 0,
      zeroWeightGraph: "KG(6,2), exactly the q=2 hole graph",
      positiveOffDiagonalSupport: "T(6), the complement of KG(6,2)",
      quotientSpectrum: [[20, 1], [8, 5], [0, 9]],
      q2Spectrum: [[6, 1], [1, 9], [-3, 5]],
      zeroEigenspaceDescent:
        "the rational q=3 zero eigenspace is the lifted q=2 KG eigenvalue-1 space",
    },
    localFibre: {
      affineStates: 8,
      affineGroup: "F2^3",
      inducedGraph: "K4,4",
      spectrum: [[4, 1], [0, 6], [-4, 1]],
      connectorForIntersectingDuads: "one C16 on the two eight-state fibres",
      connectorForDisjointDuads: "empty",
    },
    characteristicTwoDifferential: {
      operator: "the 120x120 adjacency matrix A reduced modulo 2",
      squareZero: true,
      rank: 40,
      imageDimension: 40,
      kernelDimension: 80,
      homologyDimension: 40,
      filtration: "0 < im(A) < ker(A) < F2^120",
      associatedGradedDimensions: [40, 40, 40],
      equivariantFor: "2^5:S6",
      w33ModuleIdentificationClaimed: false,
    },
    blocks,
    quotientMatrix: quotient,
    vertexToAddress,
    theorem:
      "The q=3 hole graph is an equitable eight-state F2^3 fibre extension of the q=2 S6 duad carrier. Its missing block relation is exactly KG(6,2), and in characteristic two its adjacency is a rank-40 differential with 40-dimensional image, homology, and coimage.",
    evidenceBoundary:
      "All graph, quotient, spectrum, and GF(2) statements are exact. The 40-dimensional graded pieces are not identified with W33 points or any physical particle carrier; such an identification would require an explicit equivariant map.",
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
    quotient: result.crossPrimeQuotient.weightedFormula,
    fibre: result.localFibre.inducedGraph,
    mod2: result.characteristicTwoDifferential,
  }, null, 2));
}

module.exports = { canonical, digest, execute, parse, run };
