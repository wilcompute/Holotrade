// Production-facing decoder for the 45 projective qutrit slow-path targets.
//
// The exhaustive mathematics lives in data/the_45_slot_rom_bijection.json.  A
// runtime should not rerun a 51,840-element group census at boot; it should load
// one fixed certificate, recheck the incidence contract cheaply, and only then
// admit the target->slot map.  This module is that boundary.
//
// The certificate's `table` order is the canonical anomaly-class order used by
// its generator. Each row stores the chosen H(3,4) slot and one Sp(4,3) lift.
// Projectively g and -g are the same target, so lookup normalizes a matrix under
// ± before consulting the ROM.
//
// Boot admission verifies more than cardinalities:
//   * 45 unique concrete projective targets and 45 unique slots;
//   * 27 banks of five, every slot in exactly three banks;
//   * every collinear pair appears in exactly one bank;
//   * collinearity graph SRG(45,12,3,3) and the GQ axiom;
//   * the concrete anomaly-line set, transported through the committed table,
//     is exactly the abstract H(3,4) bank set.
//
// Unknown well-shaped matrices are returned as `slow:false`; this module is an
// exception decoder, not a general Sp/PSp membership checker. The upstream
// compiler remains responsible for proving that a requested target is in the
// admitted projective control group.

"use strict";

const crypto = require("node:crypto");
const certificate = require("../data/the_45_slot_rom_bijection.json");

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;
}

function validateMatrix(matrix) {
  if (!Array.isArray(matrix) || matrix.length !== 4 || matrix.some((r) => !Array.isArray(r) || r.length !== 4)) {
    throw new TypeError("Sp lift must be a 4x4 matrix");
  }
  const out = matrix.map((row) => row.map((x) => {
    if (!Number.isInteger(x)) throw new TypeError("Sp matrix entries must be integers mod 3");
    const y = ((x % 3) + 3) % 3;
    return y;
  }));
  return out;
}

function matrixKey(matrix) {
  return validateMatrix(matrix).flat().join("");
}

function projectiveCanonical(matrix) {
  const g = validateMatrix(matrix);
  const minus = g.map((row) => row.map((x) => (3 - x) % 3));
  return matrixKey(g) <= matrixKey(minus) ? g : minus;
}

function lineKey(line) {
  return [...line].sort((a, b) => a - b).join(",");
}

function setEqual(a, b) {
  if (a.size !== b.size) return false;
  for (const x of a) if (!b.has(x)) return false;
  return true;
}

function bootCheck(cert = certificate) {
  const errors = [];
  if (!cert || cert.schema !== "holotrade.45-slot-rom-bijection.v1" || cert.valid !== true) {
    errors.push("CERTIFICATE_SCHEMA_OR_VALIDITY");
    return { ok: false, errors };
  }
  const table = Array.isArray(cert.table) ? cert.table : [];
  const linesA = Array.isArray(cert.linesA) ? cert.linesA : [];
  const linesB = Array.isArray(cert.linesB) ? cert.linesB : [];
  if (table.length !== 45) errors.push("TABLE_NOT_45");
  if (linesA.length !== 27) errors.push("CONCRETE_LINES_NOT_27");
  if (linesB.length !== 27) errors.push("ABSTRACT_BANKS_NOT_27");

  const slots = new Set();
  const targetKeys = new Set();
  const slotToRow = new Map();
  for (let i = 0; i < table.length; i += 1) {
    const row = table[i] || {};
    if (!Number.isInteger(row.slot) || row.slot < 0 || row.slot >= 45) {
      errors.push(`BAD_SLOT_${i}`);
      continue;
    }
    slots.add(row.slot);
    slotToRow.set(row.slot, row);
    if (!Array.isArray(row.h34Point) || row.h34Point.length !== 4 || row.h34Point.some((x) => !Number.isInteger(x) || x < 0 || x > 3)) {
      errors.push(`BAD_H34_POINT_${i}`);
    }
    try {
      const canonical = projectiveCanonical(row.spMatrix);
      const key = matrixKey(canonical);
      if (matrixKey(row.spMatrix) !== key) errors.push(`NONCANONICAL_SP_REP_${i}`);
      targetKeys.add(key);
    } catch (_) {
      errors.push(`BAD_SP_MATRIX_${i}`);
    }
  }
  if (slots.size !== 45) errors.push("SLOTS_NOT_BIJECTIVE");
  if (targetKeys.size !== 45) errors.push("PROJECTIVE_TARGETS_NOT_UNIQUE");

  const incidence = Array.from({ length: 45 }, () => []);
  const pairCounts = new Map();
  const adjacency = Array.from({ length: 45 }, () => Array(45).fill(0));
  for (let bi = 0; bi < linesB.length; bi += 1) {
    const line = linesB[bi];
    if (!Array.isArray(line) || line.length !== 5 || new Set(line).size !== 5 || line.some((x) => !Number.isInteger(x) || x < 0 || x >= 45)) {
      errors.push(`BAD_BANK_${bi}`);
      continue;
    }
    for (const p of line) incidence[p].push(bi);
    for (let i = 0; i < line.length; i += 1) {
      for (let j = i + 1; j < line.length; j += 1) {
        const a = Math.min(line[i], line[j]);
        const b = Math.max(line[i], line[j]);
        const key = `${a},${b}`;
        pairCounts.set(key, (pairCounts.get(key) || 0) + 1);
        adjacency[a][b] = adjacency[b][a] = 1;
      }
    }
  }
  if (incidence.some((banks) => banks.length !== 3)) errors.push("TARGET_NOT_IN_EXACTLY_THREE_BANKS");
  if ([...pairCounts.values()].some((n) => n !== 1)) errors.push("COLLINEAR_PAIR_REPEATED");
  if (pairCounts.size !== 270) errors.push("COLLINEAR_PAIR_COUNT_NOT_270");

  const degrees = adjacency.map((row) => row.reduce((a, b) => a + b, 0));
  if (degrees.some((d) => d !== 12)) errors.push("DEGREE_NOT_12");
  let lambdaOk = true;
  let muOk = true;
  for (let i = 0; i < 45; i += 1) {
    for (let j = i + 1; j < 45; j += 1) {
      let common = 0;
      for (let k = 0; k < 45; k += 1) common += adjacency[i][k] && adjacency[j][k] ? 1 : 0;
      if (adjacency[i][j] && common !== 3) lambdaOk = false;
      if (!adjacency[i][j] && common !== 3) muOk = false;
    }
  }
  if (!lambdaOk) errors.push("SRG_LAMBDA_NOT_3");
  if (!muOk) errors.push("SRG_MU_NOT_3");

  let gqOk = true;
  for (let p = 0; p < 45; p += 1) {
    for (const line of linesB) {
      if (!Array.isArray(line) || line.includes(p)) continue;
      const count = line.reduce((n, q) => n + (adjacency[p][q] ? 1 : 0), 0);
      if (count !== 1) gqOk = false;
    }
  }
  if (!gqOk) errors.push("GQ_AXIOM_FAILED");

  // Transport each concrete anomaly line through table[i].slot. Table index i
  // is the concrete anomaly-class index by the certificate generator contract.
  const transported = new Set();
  for (let li = 0; li < linesA.length; li += 1) {
    const line = linesA[li];
    if (!Array.isArray(line) || line.length !== 5 || line.some((i) => !Number.isInteger(i) || i < 0 || i >= table.length)) {
      errors.push(`BAD_CONCRETE_LINE_${li}`);
      continue;
    }
    transported.add(lineKey(line.map((i) => table[i].slot)));
  }
  const abstract = new Set(linesB.map(lineKey));
  if (!setEqual(transported, abstract)) errors.push("CONCRETE_TO_ABSTRACT_LINE_SET_MISMATCH");

  return {
    ok: errors.length === 0,
    errors,
    digest: sha256(cert),
    counts: {
      targets: targetKeys.size,
      slots: slots.size,
      banks: linesB.length,
      incidences: incidence.reduce((n, x) => n + x.length, 0),
      collinearityEdges: pairCounts.size,
    },
  };
}

class SlowPathROMDecoder {
  constructor(cert = certificate) {
    const boot = bootCheck(cert);
    if (!boot.ok) throw new Error(`W33 slow-path ROM boot refused: ${boot.errors.join(",")}`);
    this.certificate = cert;
    this.boot = Object.freeze(boot);
    this.byTarget = new Map();
    this.targetToBanks = Array.from({ length: 45 }, () => []);
    cert.linesB.forEach((line, bank) => line.forEach((slot) => this.targetToBanks[slot].push(bank)));
    cert.table.forEach((row, anomalyIndex) => {
      const canonical = projectiveCanonical(row.spMatrix);
      this.byTarget.set(matrixKey(canonical), Object.freeze({
        anomalyIndex,
        slot: row.slot,
        h34Point: Object.freeze([...row.h34Point]),
        canonicalSpMatrix: Object.freeze(canonical.map((r) => Object.freeze([...r]))),
      }));
    });
  }

  decode(matrix) {
    const canonical = projectiveCanonical(matrix);
    const row = this.byTarget.get(matrixKey(canonical));
    if (!row) {
      return Object.freeze({
        slow: false,
        extraTransvections: 0,
        certificateDigest: this.boot.digest,
      });
    }
    return Object.freeze({
      slow: true,
      extraTransvections: 1,
      anomalyIndex: row.anomalyIndex,
      slot: row.slot,
      banks: Object.freeze([...this.targetToBanks[row.slot]]),
      h34Point: row.h34Point,
      canonicalSpMatrix: row.canonicalSpMatrix,
      certificateDigest: this.boot.digest,
    });
  }
}

module.exports = {
  SlowPathROMDecoder,
  bootCheck,
  matrixKey,
  projectiveCanonical,
};
