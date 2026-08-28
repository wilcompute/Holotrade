"use strict";

const crypto = require("node:crypto");
const frozen = require("../data/e8_unitary_voltage_lift.json");

const ADDRESS_SPACE = "E8_UNITARY_AFFINE_RELATION_LIFT";
const PLAN_SCHEMA = "holotrade.e8-unitary-voltage-lift-plan.v1";

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

function verifyFrozen(certificate = frozen) {
  if (!certificate || certificate.schema !== "holotrade.e8-unitary-voltage-lift.v1") return false;
  const { sha256: claimed, ...body } = certificate;
  return sha256(body) === claimed && certificate.carrier.vertices === 120 &&
    certificate.crossRelation.relationTypes === 13 &&
    certificate.crossRelation.selectedChannelsAreParallel === true &&
    certificate.evidenceBoundary.includes("not live machines");
}

if (!verifyFrozen()) throw new Error("invalid E8 unitary affine relation-lift certificate");

function checkedInteger(value, limit, label) {
  if (!Number.isInteger(value) || value < 0 || value >= limit) {
    throw new RangeError(`${label} must be an integer in [0, ${limit - 1}]`);
  }
  return value;
}

function address(blockId, fibreSlot) {
  checkedInteger(blockId, 15, "blockId");
  checkedInteger(fibreSlot, 8, "fibreSlot");
  const block = frozen.blocks[blockId];
  return deepFreeze({
    addressSpace: ADDRESS_SPACE,
    logicalId: 8 * blockId + fibreSlot,
    blockId,
    duad: [...block.duad],
    fibreSlot,
    coordinate: [...frozen.vertexToAddress[block.coordinateVertices[fibreSlot]].coordinate],
    transportedCosetVertex: block.coordinateVertices[fibreSlot],
    dispatchable: false,
    liveBinding: null,
  });
}

function addressFromLogicalId(logicalId) {
  checkedInteger(logicalId, 120, "logicalId");
  return address(Math.floor(logicalId / 8), logicalId % 8);
}

function addressFromCosetVertex(vertex) {
  checkedInteger(vertex, 120, "coset vertex");
  const found = frozen.vertexToAddress[vertex];
  return address(found.blockId, found.fibreSlot);
}

function normalizeAddress(value) {
  if (Number.isInteger(value)) return addressFromLogicalId(value);
  if (!value || value.addressSpace !== ADDRESS_SPACE) {
    throw new TypeError(`expected an ${ADDRESS_SPACE} address or logical ID`);
  }
  return address(value.blockId, value.fibreSlot);
}

function adjacent(leftValue, rightValue) {
  const left = normalizeAddress(leftValue);
  const right = normalizeAddress(rightValue);
  return frozen.logicalNeighbours[left.logicalId].includes(right.logicalId);
}

function neighbours(value) {
  const source = normalizeAddress(value);
  return deepFreeze(frozen.logicalNeighbours[source.logicalId].map(addressFromLogicalId));
}

function compileFanout(value) {
  const source = normalizeAddress(value);
  const destinations = neighbours(source).map((target) => target.logicalId);
  const body = {
    schema: PLAN_SCHEMA,
    addressSpace: ADDRESS_SPACE,
    sourceLogicalId: source.logicalId,
    sourceBlock: source.blockId,
    sourceFibreSlot: source.fibreSlot,
    destinationLogicalIds: destinations,
    fanout: destinations.length,
    sourceCertificateSha256: frozen.sha256,
    implementation: "thirteen-relation affine predicate over two seven-bit logical addresses",
    dispatchable: false,
    liveBindings: [],
    evidenceBoundary:
      "This is a deterministic logical fanout plan. It neither selects nor contacts a host, VM, market endpoint, or actuator.",
  };
  return deepFreeze({ ...body, sha256: sha256(body) });
}

function verifyFanout(plan) {
  if (!plan || plan.schema !== PLAN_SCHEMA || plan.dispatchable !== false ||
      plan.sourceCertificateSha256 !== frozen.sha256) return false;
  const { sha256: claimed, ...body } = plan;
  if (sha256(body) !== claimed) return false;
  try {
    const expected = compileFanout(plan.sourceLogicalId);
    return canonical(expected.destinationLogicalIds) === canonical(plan.destinationLogicalIds) &&
      plan.fanout === 20;
  } catch {
    return false;
  }
}

module.exports = {
  ADDRESS_SPACE, PLAN_SCHEMA, verifyFrozen, address, addressFromLogicalId,
  addressFromCosetVertex, adjacent, neighbours, compileFanout, verifyFanout,
};
