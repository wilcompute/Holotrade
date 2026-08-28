#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.join(__dirname, "e8_unitary_reversible_dilation.g");
const DATA = path.join(ROOT, "data", "e8_unitary_reversible_dilation.json");
const RTL = path.join(ROOT, "rtl", "e8_unitary_reversible_dilation.v");
const SOURCE = require("../data/e8_unitary_crossprime_fibre_differential.json");

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
  if (!run.ok || !run.stdout.includes("ALL_UNITARY_REVERSIBLE_DILATION_CHECKS_PASS")) {
    throw new Error(`GAP reversible dilation failed: ${run.stderr || run.stdout}`);
  }
  return run.stdout;
}

function parseRows(stdout) {
  const rows = Array(120);
  for (const line of stdout.split(/\r?\n/)) {
    const match = line.match(/^ADJ\|(\d+)\|([\d,]+)$/);
    if (match) rows[Number(match[1])] = match[2].split(",").map(Number);
  }
  if (rows.some((row) => !row || row.length !== 20)) {
    throw new Error("GAP emitted an incomplete 20-regular adjacency matrix");
  }
  for (let i = 0; i < 120; i += 1) {
    if (new Set(rows[i]).size !== 20 || rows[i].includes(i) ||
        rows[i].some((j) => j < 0 || j >= 120 || !rows[j]?.includes(i))) {
      throw new Error(`invalid GAP adjacency row ${i}`);
    }
  }
  return rows;
}

function perfectMatching(remaining) {
  const matchRight = Array(120).fill(-1);
  function augment(left, seen) {
    for (const right of [...remaining[left]].sort((a, b) => a - b)) {
      if (seen[right]) continue;
      seen[right] = true;
      if (matchRight[right] === -1 || augment(matchRight[right], seen)) {
        matchRight[right] = left;
        return true;
      }
    }
    return false;
  }
  for (let left = 0; left < 120; left += 1) {
    if (!augment(left, Array(120).fill(false))) {
      throw new Error(`regular bipartite matching failed at left vertex ${left}`);
    }
  }
  const rightByLeft = Array(120);
  matchRight.forEach((left, right) => { rightByLeft[left] = right; });
  if (rightByLeft.some((right) => right === undefined)) {
    throw new Error("incomplete perfect matching");
  }
  return rightByLeft;
}

function edgeColour(rows) {
  const remaining = rows.map((row) => new Set(row));
  const layers = [];
  for (let index = 0; index < 20; index += 1) {
    const controlYByTargetX = perfectMatching(remaining);
    controlYByTargetX.forEach((controlY, targetX) => {
      if (!remaining[targetX].delete(controlY)) {
        throw new Error(`matching reused edge ${targetX},${controlY}`);
      }
    });
    layers.push({ index, controlYByTargetX });
  }
  if (remaining.some((row) => row.size !== 0)) throw new Error("edge colouring left residual gates");
  return layers;
}

function parse(stdout) {
  const compact = stdout.replace(/\s+/g, "");
  for (const required of [
    "REVERSIBLE_DILATION|bits=240|control=120|target=120|involution=1|symplectic=1|rankUminusI=40|fixed=200",
    "CNOT_NETWORK|directedGates=2400|bipartiteDegree=20|optimalParallelDepth=20",
  ]) {
    if (!compact.includes(required.replace(/\s+/g, ""))) throw new Error(`missing GAP signature ${required}`);
  }
  const gapVersion = stdout.match(/^VERSION\|([^\r\n]+)/m)?.[1]?.trim();
  if (!/^\d+\.\d+\.\d+$/.test(gapVersion || "")) throw new Error("GAP version missing");
  const rows = parseRows(stdout);
  const layers = edgeColour(rows);
  const body = {
    schema: "holotrade.e8-unitary-reversible-dilation.v1",
    evidenceClass: "EXACT_GAP_SYMPLECTIC_LINEAR_ALGEBRA_AND_KONIG_EDGE_COLOURING",
    gapVersion,
    sourceCertificateSha256: SOURCE.sha256,
    differential: {
      carrierDimension: 120,
      field: "F2",
      matrix: "adjacency A of the q=3 unitary-hole graph",
      symmetric: true,
      alternatingDiagonal: true,
      squareZero: true,
      rank: 40,
    },
    dilation: {
      bits: 240,
      inputSplit: "x in F2^120, y in F2^120",
      map: "U(x,y)=(x+A*y,y)",
      blockMatrix: "[[I,A],[0,I]]",
      involution: true,
      symplecticForm: "J=[[0,I],[I,0]]",
      symplectic: true,
      rankUminusI: 40,
      fixedDimension: 200,
    },
    cnotNetwork: {
      orientation: "y_j controls x_i for every directed adjacency entry A_ij=1",
      gates: 2400,
      layers: 20,
      gatesPerLayer: 120,
      optimal: true,
      lowerBound: "each x_i and y_j participates in 20 gates, so depth is at least 20",
      attainment: "the 20-regular bipartite adjacency graph is decomposed into 20 perfect matchings",
      schedule: layers,
    },
    theorem:
      "The square-zero 120-state graph differential has an exact 240-bit reversible symplectic dilation. Its 2,400 CNOTs admit an optimal depth-20 schedule, one perfect matching per layer.",
    evidenceBoundary:
      "This is an exact logical reversible circuit and a formally checked RTL identity. It is not a quantum-hardware performance claim, a host-routing map, or live dispatch authority.",
  };
  return { ...body, sha256: digest(body) };
}

function renderVerilog(certificate) {
  const rows = Array.from({ length: 120 }, () => []);
  for (const layer of certificate.cnotNetwork.schedule) {
    layer.controlYByTargetX.forEach((controlY, targetX) => rows[targetX].push(controlY));
  }
  const assigns = rows.map((controls, target) => {
    const packed = controls.map((j) => `y_in[${j}]`).join(", ");
    return `  wire [19:0] controls_${target} = {${packed}};\n` +
      `  assign x_out[${target}] = x_in[${target}] ^ ^controls_${target};`;
  }).join("\n");
  return `// AUTO-GENERATED by analysis/e8_unitary_reversible_dilation.js\n` +
`// certificate sha256: ${certificate.sha256}\n` +
"`default_nettype none\n\n" +
"module e8_unitary_reversible_dilation(\n" +
"  input wire [119:0] x_in, input wire [119:0] y_in,\n" +
"  output wire [119:0] x_out, output wire [119:0] y_out);\n" +
"  assign y_out = y_in;\n" + assigns + "\nendmodule\n\n" +
"module e8_unitary_reversible_dilation_twice(\n" +
"  input wire [119:0] x_in, input wire [119:0] y_in, output wire mismatch);\n" +
"  wire [119:0] x_mid, y_mid, x_out, y_out;\n" +
"  e8_unitary_reversible_dilation first(.x_in(x_in), .y_in(y_in), .x_out(x_mid), .y_out(y_mid));\n" +
"  e8_unitary_reversible_dilation second(.x_in(x_mid), .y_in(y_mid), .x_out(x_out), .y_out(y_out));\n" +
"  assign mismatch = |(x_out ^ x_in) | |(y_out ^ y_in);\n" +
"endmodule\n\n`default_nettype wire\n";
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
    if (canonical(JSON.parse(fs.readFileSync(DATA, "utf8"))) !== canonical(generated.certificate)) {
      throw new Error("frozen reversible-dilation JSON drift");
    }
    if (fs.readFileSync(RTL, "utf8") !== generated.verilog) {
      throw new Error("frozen reversible-dilation RTL drift");
    }
  }
  console.log(JSON.stringify({
    sha256: generated.certificate.sha256,
    bits: 240,
    gates: 2400,
    optimalDepth: 20,
    involution: true,
    symplectic: true,
  }, null, 2));
}

if (require.main === module) main();

module.exports = { canonical, digest, execute, parseRows, perfectMatching, edgeColour, parse, renderVerilog, generate };
