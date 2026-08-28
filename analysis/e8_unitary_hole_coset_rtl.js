#!/usr/bin/env node
"use strict";

// Freezes the GAP-owned 120-coset carrier into two synthesizable circuits:
// a compact GF(9) coordinate/Hermitian-form implementation and an independent
// complete adjacency-row ROM.  Yosys proves the two equal on all 2^14 input
// address pairs.  JavaScript only parses and renders GAP's exact output.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { runGap } = require("../scripts/run-gap.js");

const ROOT = path.resolve(__dirname, "..");
const GAP = path.join(__dirname, "e8_unitary_hole_coset_rtl.g");
const DATA = path.join(ROOT, "data", "e8_unitary_hole_coset_rtl.json");
const RTL = path.join(ROOT, "rtl", "e8_unitary_hole_adj.v");

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

function parseGapList(text) {
  return JSON.parse(text);
}

function parseGapOutput(stdout) {
  if (!stdout.includes("ALL_COSET_RTL_CHECKS_PASS")) {
    throw new Error("GAP coset/RTL completion marker missing");
  }
  const version = stdout.match(/^VERSION\|([^\r\n]+)/m)?.[1]?.trim();
  if (!/^\d+\.\d+\.\d+$/.test(version || "")) throw new Error("GAP version missing");
  const profile = stdout.match(/^RTL_PROFILE\|([^\r\n]+)/m)?.[1];
  const field = stdout.match(/^GF9_MODEL\|([^\r\n]+)/m)?.[1];
  if (!profile || !field) throw new Error("GAP hardware profile missing");
  for (const required of [
    "vertices=120|degree=20|edges=1200",
    "stabilizerId=[ 192, 1485 ]",
    "adjacencyDoubleCosetDegrees=[ 4, 16 ]",
    "coordinateBits=16|rowBits=120",
  ]) {
    if (!profile.includes(required)) throw new Error(`GAP profile mismatch: ${required}`);
  }
  if (!field.includes("alphaSquared=alpha+1") || !field.includes("(a+b)+2*b*alpha")) {
    throw new Error("GAP GF(9) model mismatch");
  }

  const coordinates = Array(120);
  const neighbours = Array(120);
  const transport = Array(120);
  for (const line of stdout.split(/\r?\n/)) {
    let match = line.match(/^COORD\|(\d+)\|(\[.*\])$/);
    if (match) coordinates[Number(match[1])] = parseGapList(match[2]);
    match = line.match(/^ADJ\|(\d+)\|(\[.*\])$/);
    if (match) neighbours[Number(match[1])] = parseGapList(match[2]);
    match = line.match(/^MAP\|(\d+)\|(\d+)\|(\d+)$/);
    if (match) {
      transport[Number(match[1])] = {
        cosetId: Number(match[1]),
        holeVertex: Number(match[2]),
        ambientH39Point: Number(match[3]),
      };
    }
  }
  if (coordinates.some((x) => !x) || neighbours.some((x) => !x) || transport.some((x) => !x)) {
    throw new Error("GAP emitted an incomplete 120-state carrier");
  }
  for (let i = 0; i < 120; i += 1) {
    if (coordinates[i].length !== 8 || coordinates[i].some((x) => !Number.isInteger(x) || x < 0 || x > 2)) {
      throw new Error(`invalid GF(9) coordinate at coset ${i}`);
    }
    if (neighbours[i].length !== 20 || neighbours[i].includes(i)) {
      throw new Error(`invalid adjacency row at coset ${i}`);
    }
    for (const j of neighbours[i]) {
      if (!neighbours[j]?.includes(i)) throw new Error(`asymmetric edge ${i}-${j}`);
    }
  }

  const packedCoordinates = coordinates.map((digits) => digits.reduce(
    (word, digit, index) => word | (digit << (2 * index)), 0));
  const rowHex = neighbours.map((row) => {
    let word = 0n;
    for (const vertex of row) word |= 1n << BigInt(vertex);
    return word.toString(16).padStart(30, "0");
  });
  const body = {
    schema: "holotrade.e8-unitary-hole-coset-rtl.v1",
    evidenceClass: "EXACT_GAP_GRAPE_TO_SYNTHESIZABLE_RTL",
    gapVersion: version,
    carrier: {
      group: "Aut(folded Q6)",
      groupOrder: 23040,
      stabilizerSmallGroupId: [192, 1485],
      stabilizerOrder: 192,
      vertices: 120,
      degree: 20,
      edges: 1200,
      adjacencyDoubleCosetDegrees: [4, 16],
    },
    field: {
      name: "GF(9)",
      encoding: "a+b*alpha as four bits {b[1:0],a[1:0]}",
      relation: "alpha^2=alpha+1",
      conjugation: "(a+b*alpha)^3=(a+b)+2*b*alpha",
      coordinateDigits: 8,
      packedCoordinateBits: 16,
    },
    implementation: {
      compactCarrierBits: 120 * 16,
      fullRowRomBits: 120 * 120,
      tableCompressionRatio: 7.5,
      predicate: "distinct valid cosets are adjacent iff their transported H(3,9) Hermitian product vanishes",
      formalInputSpace: 1 << 14,
    },
    transport,
    coordinates,
    packedCoordinates,
    neighbours,
    rowHex,
    evidenceBoundary:
      "The circuit implements the certified finite coset graph. Coset IDs are logical states, not discovered hosts; deployment still requires topology attestation.",
  };
  return { ...body, sha256: digest(body) };
}

function runGapCertificate() {
  const result = runGap(GAP, { cwd: ROOT, quiet: true });
  if (!result.ok || !result.stdout.includes("ALL_COSET_RTL_CHECKS_PASS")) {
    throw new Error(`GAP failed: ${result.stderr || result.stdout || result.status}`);
  }
  return parseGapOutput(result.stdout);
}

function renderCoordinateCase(certificate) {
  return certificate.packedCoordinates.map((word, id) =>
    `      7'd${id}: coordinate = 16'h${word.toString(16).padStart(4, "0")};`).join("\n");
}

function renderRowCase(certificate) {
  return certificate.rowHex.map((word, id) =>
    `      7'd${id}: row = 120'h${word};`).join("\n");
}

function renderVerilog(certificate) {
  return `// AUTO-GENERATED by analysis/e8_unitary_hole_coset_rtl.js\n` +
`// GAP/GRAPE certificate sha256: ${certificate.sha256}\n` +
`// Exact q=3 maximum-spread hole graph: 120 vertices, degree 20.\n` +
`// The compact circuit stores 1,920 coordinate bits; the independent\n` +
`// row-ROM reference stores 14,400 adjacency bits.\n` +
"`default_nettype none\n\n" +
`module e8_hole_f3_add(input wire [1:0] a, input wire [1:0] b, output wire [1:0] y);\n` +
`  wire [2:0] sum = {1'b0,a} + {1'b0,b};\n` +
`  assign y = (sum >= 3) ? sum - 3 : sum[1:0];\n` +
`endmodule\n\n` +
`module e8_hole_f3_neg(input wire [1:0] a, output wire [1:0] y);\n` +
`  assign y = (a == 0) ? 0 : ((a == 1) ? 2 : 1);\n` +
`endmodule\n\n` +
`module e8_hole_f3_mul(input wire [1:0] a, input wire [1:0] b, output wire [1:0] y);\n` +
`  assign y = (a == 0 || b == 0) ? 0 : ((a == 1) ? b : ((b == 1) ? a : 1));\n` +
`endmodule\n\n` +
`module e8_hole_f9_add(input wire [3:0] x, input wire [3:0] y, output wire [3:0] z);\n` +
`  e8_hole_f3_add ar(.a(x[1:0]), .b(y[1:0]), .y(z[1:0]));\n` +
`  e8_hole_f3_add ai(.a(x[3:2]), .b(y[3:2]), .y(z[3:2]));\n` +
`endmodule\n\n` +
`// x * conjugate(y), with alpha^2 = alpha+1.\n` +
`module e8_hole_f9_hermitian_term(input wire [3:0] x, input wire [3:0] y, output wire [3:0] z);\n` +
`  wire [1:0] yc, yd_neg;\n` +
`  e8_hole_f3_add conj_real(.a(y[1:0]), .b(y[3:2]), .y(yc));\n` +
`  e8_hole_f3_neg conj_alpha(.a(y[3:2]), .y(yd_neg));\n` +
`  wire [1:0] ac, bd, ad, bc, real_sum, alpha_ab;\n` +
`  e8_hole_f3_mul m_ac(.a(x[1:0]), .b(yc), .y(ac));\n` +
`  e8_hole_f3_mul m_bd(.a(x[3:2]), .b(yd_neg), .y(bd));\n` +
`  e8_hole_f3_mul m_ad(.a(x[1:0]), .b(yd_neg), .y(ad));\n` +
`  e8_hole_f3_mul m_bc(.a(x[3:2]), .b(yc), .y(bc));\n` +
`  e8_hole_f3_add add_real(.a(ac), .b(bd), .y(real_sum));\n` +
`  e8_hole_f3_add add_alpha0(.a(ad), .b(bc), .y(alpha_ab));\n` +
`  e8_hole_f3_add add_alpha1(.a(alpha_ab), .b(bd), .y(z[3:2]));\n` +
`  assign z[1:0] = real_sum;\n` +
`endmodule\n\n` +
`module e8_unitary_hole_coordinate_rom(input wire [6:0] id, output reg valid, output reg [15:0] coordinate);\n` +
`  always @* begin\n` +
`    valid = 1'b1;\n` +
`    case (id)\n${renderCoordinateCase(certificate)}\n` +
`      default: begin valid = 1'b0; coordinate = 16'h0000; end\n` +
`    endcase\n` +
`  end\n` +
`endmodule\n\n` +
`module e8_unitary_hole_adj_compact(\n` +
`  input wire [6:0] u_id, input wire [6:0] v_id, output wire valid, output wire adjacent);\n` +
`  wire u_valid, v_valid;\n` +
`  wire [15:0] u, v;\n` +
`  e8_unitary_hole_coordinate_rom ur(.id(u_id), .valid(u_valid), .coordinate(u));\n` +
`  e8_unitary_hole_coordinate_rom vr(.id(v_id), .valid(v_valid), .coordinate(v));\n` +
`  wire [3:0] t0, t1, t2, t3, s0, s1, form;\n` +
`  e8_hole_f9_hermitian_term h0(.x(u[3:0]), .y(v[3:0]), .z(t0));\n` +
`  e8_hole_f9_hermitian_term h1(.x(u[7:4]), .y(v[7:4]), .z(t1));\n` +
`  e8_hole_f9_hermitian_term h2(.x(u[11:8]), .y(v[11:8]), .z(t2));\n` +
`  e8_hole_f9_hermitian_term h3(.x(u[15:12]), .y(v[15:12]), .z(t3));\n` +
`  e8_hole_f9_add a0(.x(t0), .y(t1), .z(s0));\n` +
`  e8_hole_f9_add a1(.x(t2), .y(t3), .z(s1));\n` +
`  e8_hole_f9_add a2(.x(s0), .y(s1), .z(form));\n` +
`  assign valid = u_valid && v_valid;\n` +
`  assign adjacent = valid && (u_id != v_id) && (form == 4'b0000);\n` +
`endmodule\n\n` +
`// Independent full-row implementation retained as the formal golden model.\n` +
`module e8_unitary_hole_adj_rom(\n` +
`  input wire [6:0] u_id, input wire [6:0] v_id, output wire valid, output wire adjacent);\n` +
`  reg [119:0] row;\n` +
`  wire valid_u = (u_id < 120);\n` +
`  wire valid_v = (v_id < 120);\n` +
`  wire [6:0] safe_v = valid_v ? v_id : 0;\n` +
`  always @* begin\n` +
`    case (u_id)\n${renderRowCase(certificate)}\n` +
`      default: row = 120'h000000000000000000000000000000;\n` +
`    endcase\n` +
`  end\n` +
`  assign valid = valid_u && valid_v;\n` +
`  assign adjacent = valid && row[safe_v];\n` +
`endmodule\n\n` +
"`default_nettype wire\n";
}

function generate() {
  const certificate = runGapCertificate();
  return { certificate, verilog: renderVerilog(certificate) };
}

function main() {
  const generated = generate();
  if (process.argv.includes("--write")) {
    fs.writeFileSync(DATA, `${JSON.stringify(generated.certificate, null, 2)}\n`);
    fs.writeFileSync(RTL, generated.verilog);
  } else {
    if (!fs.existsSync(DATA) || !fs.existsSync(RTL)) {
      throw new Error("frozen coset RTL artifacts missing; run with --write");
    }
    const frozen = JSON.parse(fs.readFileSync(DATA, "utf8"));
    const rtl = fs.readFileSync(RTL, "utf8");
    if (canonical(frozen) !== canonical(generated.certificate)) throw new Error("frozen coset RTL JSON drift");
    if (rtl !== generated.verilog) throw new Error("generated coset RTL drift");
  }
  console.log(JSON.stringify({
    sha256: generated.certificate.sha256,
    vertices: 120,
    edges: 1200,
    coordinateBits: 1920,
    rowRomBits: 14400,
    compressionRatio: 7.5,
  }, null, 2));
}

if (require.main === module) {
  try { main(); } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

module.exports = {
  canonical,
  digest,
  parseGapOutput,
  runGapCertificate,
  renderVerilog,
  generate,
};
