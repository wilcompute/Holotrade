"use strict";

const crypto = require("node:crypto");
const E = require("../js/evidence.js");
const Codec = require("../analysis/e8_fano_zappa_szep_codec.js");
const Switch = require("./e8-unitary-fibre-switch.js");
const FABRIC = require("../data/e8_fractal_microvm_fabric.json");
const GRAPH = require("../data/e8_unitary_hole_coset_rtl.json");

const ADDRESS_SPACE = "ABSTRACT_E8_FRACTAL_MICROVM_FABRIC";
const TRANSITION_SCHEMA = "holotrade.e8-fractal-microvm-transition.v1";

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

function verifyFrozen(frozen = FABRIC) {
  if (!frozen || frozen.schema !== "holotrade.e8-fractal-microvm-fabric.v1") return false;
  const { sha256: claimed, ...body } = frozen;
  return /^[0-9a-f]{64}$/.test(claimed || "") && sha256(body) === claimed &&
    frozen.fabric.states === 20160 && frozen.independence.commonNontrivialQuotient === false &&
    frozen.fabric.a8IdentificationClaimed === false && Codec.verifyFrozen() && Switch.verifyFrozen();
}

if (!verifyFrozen()) throw new Error("invalid E8 fractal microVM fabric certificate");

function intRange(value, limit, name) {
  if (!Number.isInteger(value) || value < 0 || value >= limit) {
    throw new RangeError(`${name} must be an integer in [0, ${limit - 1}]`);
  }
  return value;
}

function addressFromId(id) {
  intRange(id, 20160, "fabric ID");
  const controlId = Math.floor(id / 120);
  const executionVertex = id % 120;
  const control = Codec.addressFromId(controlId);
  const execution = Switch.addressOf(executionVertex);
  return deepFreeze({
    addressSpace: ADDRESS_SPACE,
    id,
    controlId,
    executionVertex,
    coordinates: {
      fanoClock: control.clock,
      fanoLocal: control.local,
      duad: execution.duad,
      fibreSlot: execution.fibreSlot,
    },
    dispatchable: false,
    liveMachineBinding: null,
    requiredNextEvidence: "SIGNED_LIVE_INVENTORY_BINDING",
  });
}

function makeAddress(controlId, executionVertex) {
  intRange(controlId, 168, "control ID");
  intRange(executionVertex, 120, "execution vertex");
  return addressFromId(controlId * 120 + executionVertex);
}

function compileTransition(current, instructionControlId) {
  const address = typeof current === "number" ? addressFromId(current) : current;
  if (!address || address.addressSpace !== ADDRESS_SPACE) {
    throw new TypeError(`transition requires an ${ADDRESS_SPACE} address`);
  }
  intRange(instructionControlId, 168, "instruction control ID");
  const nextControl = Codec.multiplyIds(address.controlId, instructionControlId);
  const fanout = [...GRAPH.neighbours[address.executionVertex]].sort((a, b) => a - b);
  const destinations = fanout.map((vertex) => nextControl * 120 + vertex);
  const body = {
    schema: TRANSITION_SCHEMA,
    sourceFabricId: address.id,
    instructionControlId,
    matchedActionControlResult: nextControl,
    executionRelation: "one adjacency-differential basis fanout",
    destinationFabricIds: destinations,
    destinationCount: destinations.length,
    sourceCertificateSha256: FABRIC.sha256,
    dispatchable: false,
    evidenceBoundary:
      "This compiles one abstract matched-action control update and one 20-way logical graph fanout. It does not select or execute a live microVM.",
  };
  return deepFreeze({ ...body, digest: E.demoDigest(body) });
}

function verifyTransition(transition) {
  if (!transition || transition.schema !== TRANSITION_SCHEMA || transition.dispatchable !== false) return false;
  const { digest, ...body } = transition;
  if (digest !== E.demoDigest(body) || transition.sourceCertificateSha256 !== FABRIC.sha256 ||
      transition.destinationCount !== 20) return false;
  const source = addressFromId(transition.sourceFabricId);
  const next = Codec.multiplyIds(source.controlId, transition.instructionControlId);
  const expected = [...GRAPH.neighbours[source.executionVertex]].sort((a, b) => a - b)
    .map((vertex) => next * 120 + vertex);
  return canonical(expected) === canonical(transition.destinationFabricIds);
}

module.exports = {
  ADDRESS_SPACE, TRANSITION_SCHEMA, verifyFrozen, addressFromId, makeAddress,
  compileTransition, verifyTransition,
};
