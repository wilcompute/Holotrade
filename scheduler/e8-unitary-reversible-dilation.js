"use strict";

const crypto = require("node:crypto");
const E = require("../js/evidence.js");
const FROZEN = require("../data/e8_unitary_reversible_dilation.json");

const PLAN_SCHEMA = "holotrade.e8-unitary-reversible-plan.v1";

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

function deepFreeze(value) {
  if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
  for (const child of Object.values(value)) deepFreeze(child);
  return Object.freeze(value);
}

function verifyFrozen(frozen = FROZEN) {
  if (!frozen || frozen.schema !== "holotrade.e8-unitary-reversible-dilation.v1") return false;
  const { sha256: claimed, ...body } = frozen;
  return /^[0-9a-f]{64}$/.test(claimed || "") && sha256(body) === claimed &&
    frozen.dilation.bits === 240 && frozen.dilation.involution === true &&
    frozen.dilation.symplectic === true && frozen.cnotNetwork.gates === 2400 &&
    frozen.cnotNetwork.layers === 20 && frozen.cnotNetwork.optimal === true;
}

if (!verifyFrozen()) throw new Error("invalid reversible-dilation certificate");

function bits(value, label) {
  if (!Array.isArray(value) || value.length !== 120 ||
      value.some((bit) => bit !== 0 && bit !== 1 && bit !== false && bit !== true)) {
    throw new TypeError(`${label} must be a 120-element binary array`);
  }
  return value.map(Number);
}

function applyDilation(xInput, yInput) {
  const x = bits(xInput, "x");
  const y = bits(yInput, "y");
  for (const layer of FROZEN.cnotNetwork.schedule) {
    const updates = [];
    layer.controlYByTargetX.forEach((controlY, targetX) => {
      if (y[controlY]) updates.push(targetX);
    });
    for (const targetX of updates) x[targetX] ^= 1;
  }
  return { x, y };
}

function planReversibleDilation() {
  const body = {
    schema: PLAN_SCHEMA,
    operation: "U(x,y)=(x+A*y,y)",
    bits: FROZEN.dilation.bits,
    gates: FROZEN.cnotNetwork.gates,
    depth: FROZEN.cnotNetwork.layers,
    optimalDepth: FROZEN.cnotNetwork.optimal,
    involution: FROZEN.dilation.involution,
    symplectic: FROZEN.dilation.symplectic,
    executableSimulation: true,
    dispatchable: false,
    sourceCertificateSha256: FROZEN.sha256,
    evidenceBoundary: FROZEN.evidenceBoundary,
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function verifyPlan(plan) {
  if (!plan || plan.schema !== PLAN_SCHEMA || plan.dispatchable !== false) return false;
  const { digest, ...body } = plan;
  return digest === E.demoDigest(body) && plan.sourceCertificateSha256 === FROZEN.sha256;
}

module.exports = { PLAN_SCHEMA, verifyFrozen, applyDilation, planReversibleDilation, verifyPlan };
