"use strict";

// Executable abstract logic-switch surface for the exact 120-state graph.
// It exposes the certified 15 x 8 fibre chart and the characteristic-two
// adjacency differential.  It never treats logical cosets as live hosts.

const crypto = require("node:crypto");
const E = require("../js/evidence.js");
const FIBRE = require("../data/e8_unitary_crossprime_fibre_differential.json");
const GRAPH = require("../data/e8_unitary_hole_coset_rtl.json");

const SWITCH_SCHEMA = "holotrade.e8-unitary-fibre-switch.v1";

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) =>
      `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return crypto.createHash("sha256").update(canonical(value)).digest("hex");
}

function verifyHash(value, schema) {
  if (!value || value.schema !== schema) return false;
  const { sha256: claimed, ...body } = value;
  return /^[0-9a-f]{64}$/.test(claimed || "") && sha256(body) === claimed;
}

function verifyFrozen() {
  if (!verifyHash(FIBRE, "holotrade.e8-unitary-crossprime-fibre-differential.v1") ||
      !verifyHash(GRAPH, "holotrade.e8-unitary-hole-coset-rtl.v1")) return false;
  return FIBRE.characteristicTwoDifferential.squareZero === true &&
    FIBRE.characteristicTwoDifferential.rank === 40 &&
    FIBRE.vertexToAddress.length === 120 && GRAPH.neighbours.length === 120;
}

if (!verifyFrozen()) throw new Error("invalid E8 unitary fibre-switch certificates");

function vertexId(value, name = "vertex") {
  if (!Number.isInteger(value) || value < 0 || value >= 120) {
    throw new RangeError(`${name} must be an integer in [0, 119]`);
  }
  return value;
}

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

function addressOf(vertex) {
  vertexId(vertex);
  const address = FIBRE.vertexToAddress[vertex];
  return deepFreeze({
    vertex,
    blockId: address.blockId,
    duad: [...address.duad],
    fibreSlot: address.fibreSlot,
    fibreStates: 8,
    abstractFibreGroup: "F2^3",
    coordinateBoundary:
      "fibreSlot is a deterministic chart index, not a canonical F2^3 basis or a host address",
  });
}

function blockRelation(leftBlock, rightBlock) {
  if (!Number.isInteger(leftBlock) || leftBlock < 0 || leftBlock >= 15 ||
      !Number.isInteger(rightBlock) || rightBlock < 0 || rightBlock >= 15) {
    throw new RangeError("block IDs must be integers in [0, 14]");
  }
  const weight = FIBRE.quotientMatrix[leftBlock][rightBlock];
  const left = FIBRE.blocks[leftBlock].duad;
  const right = FIBRE.blocks[rightBlock].duad;
  const relation = leftBlock === rightBlock ? "same-fibre-K4,4" :
    (weight === 2 ? "intersecting-duads-C16-connector" : "disjoint-duads-KG6,2-zero");
  return deepFreeze({ leftBlock, rightBlock, leftDuad: [...left], rightDuad: [...right],
    neighbourCountPerSourceVertex: weight, relation });
}

function adjacent(left, right) {
  vertexId(left, "left");
  vertexId(right, "right");
  return GRAPH.neighbours[left].includes(right);
}

function normalizeBits(input) {
  if (!input || typeof input.length !== "number" || input.length !== 120) {
    throw new RangeError("switch input must contain exactly 120 bits");
  }
  return Array.from(input, (value, index) => {
    if (value !== 0 && value !== 1 && value !== false && value !== true) {
      throw new TypeError(`switch input ${index} is not a bit`);
    }
    return value ? 1 : 0;
  });
}

function applyDifferential(input) {
  const bits = normalizeBits(input);
  return Object.freeze(GRAPH.neighbours.map((row) =>
    row.reduce((parity, vertex) => parity ^ bits[vertex], 0)));
}

function hammingWeight(bits) {
  return bits.reduce((sum, bit) => sum + Number(Boolean(bit)), 0);
}

function buildSwitchCertificate(input) {
  const normalized = normalizeBits(input);
  const first = applyDifferential(normalized);
  const second = applyDifferential(first);
  const squareZeroObserved = second.every((bit) => bit === 0);
  const body = {
    schema: SWITCH_SCHEMA,
    operator: "q=3 hole adjacency modulo 2",
    input: normalized,
    output: first,
    inputWeight: hammingWeight(normalized),
    outputWeight: hammingWeight(first),
    secondApplication: second,
    squareZeroObserved,
    certifiedGlobalRank: FIBRE.characteristicTwoDifferential.rank,
    certifiedFiltration: FIBRE.characteristicTwoDifferential.filtration,
    certifiedAssociatedGradedDimensions:
      FIBRE.characteristicTwoDifferential.associatedGradedDimensions,
    sourceCertificateSha256: FIBRE.sha256,
    graphCertificateSha256: GRAPH.sha256,
    dispatchable: false,
    evidenceBoundary:
      "This is an exact parity transform on 120 logical cosets. It does not execute, isolate, migrate, or roll back a live machine.",
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function verifySwitchCertificate(certificate) {
  if (!certificate || certificate.schema !== SWITCH_SCHEMA || certificate.dispatchable !== false) return false;
  const { digest, ...body } = certificate;
  return digest === E.demoDigest(body) && certificate.squareZeroObserved === true &&
    certificate.sourceCertificateSha256 === FIBRE.sha256 &&
    certificate.graphCertificateSha256 === GRAPH.sha256;
}

module.exports = {
  SWITCH_SCHEMA,
  verifyFrozen,
  addressOf,
  blockRelation,
  adjacent,
  applyDifferential,
  buildSwitchCertificate,
  verifySwitchCertificate,
};
