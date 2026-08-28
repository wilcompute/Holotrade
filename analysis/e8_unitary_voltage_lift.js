#!/usr/bin/env node
"use strict";

// GAP owns the affine chart.  This file only parses the exact witness,
// freezes it as JSON, and renders two independent RTL implementations:
// a thirteen-relation affine predicate and a complete logical-address ROM.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.join(__dirname, "e8_unitary_voltage_lift.g");
const DATA = path.join(ROOT, "data/e8_unitary_voltage_lift.json");
const RTL = path.join(ROOT, "rtl/e8_unitary_voltage_lift.v");

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

function bits(text) { return [...text].map(Number); }
function slotBits(slot) { return [(slot >> 2) & 1, (slot >> 1) & 1, slot & 1]; }
function dot(mask, point) {
  return mask.reduce((sum, bit, index) => sum ^ (bit & point[index]), 0);
}
function relationKey(equations) {
  return equations.map((row) => `${row.mask.join("")}:${row.rhs}`).join("|");
}

function affineImage(map, point) {
  return map.matrix.map((row, index) => row.reduce(
    (sum, bit, column) => sum ^ (bit & point[column]), map.offset[index]));
}

function relationHolds(relation, left, right) {
  const point = [...left, ...right];
  return relation.equations.every((equation) => dot(equation.mask, point) === equation.rhs);
}

function parse(stdout) {
  if (!stdout.includes("ALL_E8_UNITARY_VOLTAGE_LIFT_CHECKS_PASS")) {
    throw new Error("GAP voltage-lift completion marker missing");
  }
  const version = stdout.match(/^VERSION\|([^\r\n]+)/m)?.[1]?.trim();
  if (!/^\d+\.\d+\.\d+$/.test(version || "")) throw new Error("GAP version missing");
  for (const fragment of [
    "VOLTAGE_PROFILE|vertices=120|base=T6|blocks=15|fibre=F2^3|local=K4,4|cross=4C4|crossEdges=60|group=2^5:S6",
    "AFFINE_RELATIONS|localEquations=1|crossEquations=2|allCrossAffine=1|coordinateBits=7|affineMapsPerCross=8|twoMapDecompositions=4",
  ]) {
    if (!stdout.replace(/\s+/g, "").includes(fragment.replace(/\s+/g, ""))) {
      throw new Error(`GAP signature missing: ${fragment}`);
    }
  }

  const blocks = Array(15);
  const crossByPair = new Map();
  for (const line of stdout.split(/\r?\n/)) {
    let match = line.match(/^BLOCK\|(\d+)\|duad=(\d+),(\d+)\|kernel=([01,]+)\|rows=([01,]+)\|vertices=([\d,]+)$/);
    if (match) {
      const blockId = Number(match[1]);
      blocks[blockId] = {
        blockId,
        duad: [Number(match[2]), Number(match[3])],
        translationKernel: match[4].split(",").map(bits),
        quotientCoordinateRows: match[5].split(",").map(bits),
        coordinateVertices: match[6].split(",").map(Number),
      };
      continue;
    }
    match = line.match(/^CROSS\|(\d+)\|(\d+)\|([01]{6})\|(\d)\|([01]{6})\|(\d)$/);
    if (match) {
      const leftBlock = Number(match[1]);
      const rightBlock = Number(match[2]);
      crossByPair.set(`${leftBlock}:${rightBlock}`, {
        leftBlock,
        rightBlock,
        equations: [
          { mask: bits(match[3]), rhs: Number(match[4]) },
          { mask: bits(match[5]), rhs: Number(match[6]) },
        ],
      });
      continue;
    }
    match = line.match(/^MAPS\|(\d+)\|(\d+)\|([01]{9})\|([01]{3})\|([01]{9})\|([01]{3})$/);
    if (match) {
      const relation = crossByPair.get(`${match[1]}:${match[2]}`);
      if (!relation) throw new Error(`MAPS precedes CROSS for ${match[1]}:${match[2]}`);
      relation.selectedAffineMaps = [0, 1].map((index) => {
        const matrixText = match[3 + 2 * index];
        return {
          matrix: [0, 1, 2].map((row) => bits(matrixText.slice(3 * row, 3 * row + 3))),
          offset: bits(match[4 + 2 * index]),
        };
      });
    }
  }
  const crossRelations = [...crossByPair.values()];
  if (blocks.some((block) => !block) || crossRelations.length !== 60 ||
      crossRelations.some((relation) => !relation.selectedAffineMaps)) {
    throw new Error("incomplete GAP affine chart");
  }

  const relationTypes = [];
  const typeByKey = new Map();
  for (const relation of crossRelations) {
    const key = relationKey(relation.equations);
    if (!typeByKey.has(key)) {
      typeByKey.set(key, relationTypes.length + 1);
      relationTypes.push({ relationType: relationTypes.length + 1,
        equations: relation.equations, selectedAffineMaps: relation.selectedAffineMaps });
    }
    relation.relationType = typeByKey.get(key);
    relation.affinePermutationGraphsInRelation = 8;
    relation.twoMapDecompositions = 4;
  }
  if (relationTypes.length !== 13) throw new Error(`expected 13 relation types, got ${relationTypes.length}`);

  const vertexToAddress = Array(120);
  for (const block of blocks) {
    if (block.coordinateVertices.length !== 8 || block.translationKernel.length !== 4 ||
        block.quotientCoordinateRows.length !== 3) throw new Error(`invalid block ${block.blockId}`);
    block.coordinateVertices.forEach((vertex, slot) => {
      if (vertexToAddress[vertex]) throw new Error(`duplicate vertex ${vertex}`);
      vertexToAddress[vertex] = { blockId: block.blockId, fibreSlot: slot, coordinate: slotBits(slot) };
    });
  }
  if (vertexToAddress.some((address) => !address)) throw new Error("address chart is not bijective");

  const relationMap = new Map(crossRelations.map((relation) =>
    [`${relation.leftBlock}:${relation.rightBlock}`, relation]));
  function adjacentAddresses(leftBlock, leftSlot, rightBlock, rightSlot) {
    const left = slotBits(leftSlot);
    const right = slotBits(rightSlot);
    if (leftBlock === rightBlock) return (left[0] ^ right[0]) === 1;
    const low = Math.min(leftBlock, rightBlock);
    const high = Math.max(leftBlock, rightBlock);
    const relation = relationMap.get(`${low}:${high}`);
    if (!relation) return false;
    return leftBlock < rightBlock ? relationHolds(relation, left, right) : relationHolds(relation, right, left);
  }

  for (const relation of crossRelations) {
    const [first, second] = relation.selectedAffineMaps;
    if (canonical(first.matrix) !== canonical(second.matrix)) {
      throw new Error(`selected affine maps are not parallel on ${relation.leftBlock}:${relation.rightBlock}`);
    }
    const pairs = new Set();
    for (let slot = 0; slot < 8; slot += 1) {
      const point = slotBits(slot);
      for (const map of relation.selectedAffineMaps) {
        const image = affineImage(map, point);
        if (!relationHolds(relation, point, image)) throw new Error("affine map escapes relation");
        pairs.add(`${point.join("")}:${image.join("")}`);
      }
    }
    if (pairs.size !== 16) throw new Error("two affine channels do not partition connector");
  }

  const logicalNeighbours = Array.from({ length: 120 }, () => []);
  for (let leftBlock = 0; leftBlock < 15; leftBlock += 1) {
    for (let leftSlot = 0; leftSlot < 8; leftSlot += 1) {
      const source = 8 * leftBlock + leftSlot;
      for (let rightBlock = 0; rightBlock < 15; rightBlock += 1) {
        for (let rightSlot = 0; rightSlot < 8; rightSlot += 1) {
          if (adjacentAddresses(leftBlock, leftSlot, rightBlock, rightSlot)) {
            logicalNeighbours[source].push(8 * rightBlock + rightSlot);
          }
        }
      }
      if (logicalNeighbours[source].length !== 20 || logicalNeighbours[source].includes(source)) {
        throw new Error(`logical degree failure at ${source}`);
      }
    }
  }
  for (let source = 0; source < 120; source += 1) {
    for (const target of logicalNeighbours[source]) {
      if (!logicalNeighbours[target].includes(source)) throw new Error(`asymmetric logical edge ${source}:${target}`);
    }
  }

  const oldGraph = JSON.parse(fs.readFileSync(path.join(ROOT, "data/e8_unitary_hole_coset_rtl.json"), "utf8"));
  for (let source = 0; source < 120; source += 1) {
    const sourceVertex = blocks[Math.floor(source / 8)].coordinateVertices[source % 8];
    const mapped = logicalNeighbours[source].map((address) =>
      blocks[Math.floor(address / 8)].coordinateVertices[address % 8]).sort((a, b) => a - b);
    const expected = [...oldGraph.neighbours[sourceVertex]].sort((a, b) => a - b);
    if (canonical(mapped) !== canonical(expected)) throw new Error(`transport mismatch at ${source}`);
  }

  const body = {
    schema: "holotrade.e8-unitary-voltage-lift.v1",
    evidenceClass: "EXACT_GAP_GRAPE_AFFINE_RELATION_LIFT_AND_RTL",
    gapVersion: version,
    carrier: {
      vertices: 120,
      degree: 20,
      edges: 1200,
      automorphismModel: "2^5:S6",
      baseSimpleGraph: "T(6) on the fifteen duads",
      blocks: 15,
      fibre: "F2^3",
      fibreStates: 8,
      addressBits: 7,
    },
    localRelation: {
      equation: "x0+y0=1",
      inducedGraph: "K4,4",
      edgesPerBlock: 16,
    },
    crossRelation: {
      baseEdges: 60,
      equationsPerBaseEdge: 2,
      pointsPerAffineRelation: 16,
      inducedConnector: "4C4",
      affinePermutationGraphsPerRelation: 8,
      complementaryTwoMapDecompositions: 4,
      selectedChannelsPerBaseEdge: 2,
      selectedChannelsAreParallel: true,
      relationTypes: 13,
    },
    implementation: {
      inputEncoding: "two logical addresses (duad block[3:0], F2^3 slot[2:0])",
      compactPredicate: "same-block one-parity test or one of thirteen two-parity affine relations",
      crossPairPayloadBits: 60 * 4,
      relationTypePayloadBits: 13 * 14,
      totalLogicalPayloadBits: 60 * 4 + 13 * 14,
      priorGeneralPredicateIce40Lut4: 544,
      synthesis: {
        tool: "Yosys 0.68",
        flow: "synth_ice40 -noabc -noabc9 (built-in four-LUT mapper)",
        affinePredicateIce40Lut4: 171,
        affinePredicateIce40Carry: 4,
        priorGeneralPredicateSameFlowIce40Lut4: 720,
        sameFlowLutReduction: 549,
        sameFlowLutReductionPercent: 76.25,
      },
      formalReference: "independent complete 120-row logical-address ROM",
      formalInputSpace: 1 << 14,
    },
    blocks,
    vertexToAddress,
    relationTypes,
    crossRelations,
    logicalNeighbours,
    theorem:
      "The 120-state unitary hole graph has an exact 15-by-8 affine relation lift: each T(6) base edge lifts to four disjoint 4-cycles, the union of two parallel affine permutations of F2^3, while each fibre carries K4,4.",
    evidenceBoundary:
      "This is an affine multichannel relation lift, not a regular one-voltage graph cover. Its addresses are certified logical states, not live machines, and the generated scheduler is deliberately non-dispatchable.",
  };
  return { ...body, sha256: digest(body) };
}

function execute() {
  const result = runGap(GAP, { cwd: ROOT, quiet: true });
  if (!result.ok) throw new Error(`GAP voltage witness failed: ${result.stderr || result.stdout}`);
  return result.stdout;
}

function maskNumber(mask) {
  return mask.reduce((word, bit, index) => word | (bit << index), 0);
}

function renderPairCases(certificate) {
  return certificate.crossRelations.map((relation) =>
    `      8'h${((relation.leftBlock << 4) | relation.rightBlock).toString(16).padStart(2, "0")}: relation_type = 4'd${relation.relationType};`).join("\n");
}

function renderTypeCases(certificate) {
  return certificate.relationTypes.map((type) => {
    const [left, right] = type.equations;
    return `      4'd${type.relationType}: begin mask0 = 6'h${maskNumber(left.mask).toString(16).padStart(2, "0")}; rhs0 = 1'b${left.rhs}; mask1 = 6'h${maskNumber(right.mask).toString(16).padStart(2, "0")}; rhs1 = 1'b${right.rhs}; end`;
  }).join("\n");
}

function renderRows(certificate) {
  return certificate.logicalNeighbours.map((neighbours, source) => {
    let row = 0n;
    for (const target of neighbours) row |= 1n << BigInt(target);
    return `      7'd${source}: row = 128'h${row.toString(16).padStart(32, "0")};`;
  }).join("\n");
}

function renderVerilog(certificate) {
  return `// AUTO-GENERATED by analysis/e8_unitary_voltage_lift.js\n` +
`// GAP certificate sha256: ${certificate.sha256}\n` +
`// Exact logical-address implementation of the 120-state affine relation lift.\n` +
"`default_nettype none\n\n" +
`module e8_unitary_voltage_lift_affine(\n` +
`  input wire [3:0] u_block, input wire [2:0] u_slot,\n` +
`  input wire [3:0] v_block, input wire [2:0] v_slot,\n` +
`  output wire valid, output wire adjacent);\n` +
`  wire same_block = (u_block == v_block);\n` +
`  wire reverse = (u_block > v_block);\n` +
`  wire [3:0] low_block = reverse ? v_block : u_block;\n` +
`  wire [3:0] high_block = reverse ? u_block : v_block;\n` +
`  wire [2:0] left_slot = reverse ? v_slot : u_slot;\n` +
`  wire [2:0] right_slot = reverse ? u_slot : v_slot;\n` +
`  wire [5:0] point = {right_slot[0],right_slot[1],right_slot[2],left_slot[0],left_slot[1],left_slot[2]};\n` +
`  reg [3:0] relation_type;\n` +
`  always @* begin\n` +
`    relation_type = 4'd0;\n` +
`    case ({low_block,high_block})\n${renderPairCases(certificate)}\n` +
`      default: relation_type = 4'd0;\n` +
`    endcase\n` +
`  end\n` +
`  reg [5:0] mask0, mask1;\n` +
`  reg rhs0, rhs1;\n` +
`  always @* begin\n` +
`    mask0 = 6'd0; mask1 = 6'd0; rhs0 = 1'b0; rhs1 = 1'b0;\n` +
`    case (relation_type)\n${renderTypeCases(certificate)}\n` +
`      default: begin mask0 = 6'd0; mask1 = 6'd0; rhs0 = 1'b0; rhs1 = 1'b0; end\n` +
`    endcase\n` +
`  end\n` +
`  wire local_relation = left_slot[2] ^ right_slot[2];\n` +
`  wire cross_relation = (relation_type != 0) && (^(point & mask0) == rhs0) && (^(point & mask1) == rhs1);\n` +
`  assign valid = (u_block < 15) && (v_block < 15);\n` +
`  assign adjacent = valid && (same_block ? local_relation : cross_relation);\n` +
`endmodule\n\n` +
`module e8_unitary_voltage_lift_rom(\n` +
`  input wire [3:0] u_block, input wire [2:0] u_slot,\n` +
`  input wire [3:0] v_block, input wire [2:0] v_slot,\n` +
`  output wire valid, output wire adjacent);\n` +
`  wire [6:0] u_address = {u_block,u_slot};\n` +
`  wire [6:0] v_address = {v_block,v_slot};\n` +
`  reg [127:0] row;\n` +
`  always @* begin\n` +
`    case (u_address)\n${renderRows(certificate)}\n` +
`      default: row = 128'd0;\n` +
`    endcase\n` +
`  end\n` +
`  assign valid = (u_block < 15) && (v_block < 15);\n` +
`  assign adjacent = valid && row[v_address];\n` +
`endmodule\n\n` +
`module e8_unitary_voltage_lift_miter(\n` +
`  input wire [3:0] u_block, input wire [2:0] u_slot,\n` +
`  input wire [3:0] v_block, input wire [2:0] v_slot, output wire mismatch);\n` +
`  wire av, aa, rv, ra;\n` +
`  e8_unitary_voltage_lift_affine a(u_block,u_slot,v_block,v_slot,av,aa);\n` +
`  e8_unitary_voltage_lift_rom r(u_block,u_slot,v_block,v_slot,rv,ra);\n` +
`  assign mismatch = (av != rv) || (aa != ra);\n` +
`endmodule\n\n` +
"`default_nettype wire\n";
}

function generate() {
  const certificate = parse(execute());
  return { certificate, verilog: renderVerilog(certificate) };
}

function main() {
  const generated = generate();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(DATA, `${JSON.stringify(generated.certificate, null, 2)}\n`);
    fs.writeFileSync(RTL, generated.verilog);
  } else {
    if (!fs.existsSync(DATA) || !fs.existsSync(RTL)) throw new Error("frozen voltage-lift artifacts missing; run --write");
    if (canonical(JSON.parse(fs.readFileSync(DATA, "utf8"))) !== canonical(generated.certificate)) {
      throw new Error("frozen voltage-lift JSON drift");
    }
    if (fs.readFileSync(RTL, "utf8") !== generated.verilog) throw new Error("voltage-lift RTL drift");
  }
  console.log(JSON.stringify({
    sha256: generated.certificate.sha256,
    vertices: 120,
    baseEdges: 60,
    affineRelationTypes: 13,
    payloadBits: generated.certificate.implementation.totalLogicalPayloadBits,
    dispatchable: false,
  }, null, 2));
}

if (require.main === module) {
  try { main(); } catch (error) { console.error(error.stack || error.message); process.exitCode = 1; }
}

module.exports = {
  canonical, digest, bits, slotBits, dot, affineImage, relationHolds,
  parse, execute, renderVerilog, generate,
};
