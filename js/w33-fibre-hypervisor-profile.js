// Canonical 1296-state fibre-product hypervisor for the two immutable W33
// 216-state guest machine types.
//
// The existing w33-execution-profile module is intentionally left as the guest
// carrier ABI: CIRCUIT_ST81 and PAIR_ST64 are inequivalent construction-time
// forks.  The newest finite-geometry result does not add a conversion between
// them.  It adds a higher-level composite:
//
//      216 x_36 216 = 36 x 6 x 6 = 1296.
//
// This module therefore binds TWO already-valid guest profiles for the SAME
// ExecutionPlan into one immutable hypervisor profile.  It exposes both
// six-to-one projections while making carrier conversion explicitly forbidden.
//
// Honest boundary: this is a deployment/control-plane object.  It does not
// claim the two guest modules are isomorphic, does not fabricate a 145-dimensional
// physical logical register, and does not by itself add a hardware scheduler.

"use strict";

const crypto = require("node:crypto");
const P = require("./w33-execution-profile.js");

const MACHINE_TYPE = "w33.fibre1296.steinberg81+64";
const BASE_STATES = 36;
const FIBRE_DEGREE = 6;
const CARRIER_STATES = BASE_STATES * FIBRE_DEGREE;
const HYPERVISOR_STATES = BASE_STATES * FIBRE_DEGREE * FIBRE_DEGREE;

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

function requireForkPair(a, b, plan) {
  if (!P.verify(a, plan) || !P.verify(b, plan)) {
    throw new Error("both W33 guest profiles must verify against the same ExecutionPlan");
  }
  const types = new Set([a.machineType, b.machineType]);
  if (!types.has(P.MACHINE_TYPE.CIRCUIT_ST81) || !types.has(P.MACHINE_TYPE.PAIR_ST64) || types.size !== 2) {
    throw new Error("fibre hypervisor requires exactly one ST81 fork and one ST64 fork");
  }
  const circuit = a.machineType === P.MACHINE_TYPE.CIRCUIT_ST81 ? a : b;
  const pair = a.machineType === P.MACHINE_TYPE.PAIR_ST64 ? a : b;
  return { circuit, pair };
}

function payloadFor(plan, a, b) {
  const { circuit, pair } = requireForkPair(a, b, plan);
  return {
    schema: "holotrade.w33-fibre-hypervisor-profile.v1",
    planDigest: plan.digest,
    machineType: MACHINE_TYPE,
    role: "HYPERVISOR_FIBRE_PRODUCT",
    stateModel: {
      baseStates: BASE_STATES,
      circuitFibre: FIBRE_DEGREE,
      pairFibre: FIBRE_DEGREE,
      carrierStatesEach: CARRIER_STATES,
      hypervisorStates: HYPERVISOR_STATES,
      formula: "216 x_36 216 = 36 x 6 x 6 = 1296",
    },
    logicalModules: [81, 64],
    guestProfiles: {
      circuitDigest: circuit.digest,
      pairDigest: pair.digest,
    },
    symmetryNamespaces: {
      cliffordLift: P.SYMMETRY_NAMESPACE.CLIFFORD_LIFT,
      projectiveWeyl: P.SYMMETRY_NAMESPACE.PROJECTIVE_WEYL,
      sameOrderNotSameNamespace: true,
      order: 51840,
    },
    fibreProductEvidence: {
      pspOrbitTransitive: true,
      stabiliserOrder: 20,
      stabiliserSignature: "F20=AGL(1,5)",
      sourceCommit: "58f0df389db596c9ee3d7893cdf8f9685c0b18a3",
    },
    projections: {
      circuit: "ONTO_SIX_TO_ONE",
      pair: "ONTO_SIX_TO_ONE",
    },
    runtimeRetype: "FORBIDDEN",
    carrierConversion: "FORBIDDEN",
  };
}

function bind(plan, a, b) {
  const payload = payloadFor(plan, a, b);
  return Object.freeze({ ...payload, digest: sha256(payload) });
}

function verify(profile, plan, a, b) {
  if (!profile || !plan) return false;
  let payload;
  try {
    payload = payloadFor(plan, a, b);
  } catch (_) {
    return false;
  }
  return (
    profile.schema === payload.schema &&
    profile.machineType === MACHINE_TYPE &&
    profile.runtimeRetype === "FORBIDDEN" &&
    profile.carrierConversion === "FORBIDDEN" &&
    profile.digest === sha256(payload)
  );
}

function coordinate(base, circuitTag, pairTag) {
  for (const [name, value, limit] of [
    ["base", base, BASE_STATES],
    ["circuitTag", circuitTag, FIBRE_DEGREE],
    ["pairTag", pairTag, FIBRE_DEGREE],
  ]) {
    if (!Number.isInteger(value) || value < 0 || value >= limit) {
      throw new RangeError(`${name} out of range`);
    }
  }
  const packed = base + BASE_STATES * (circuitTag + FIBRE_DEGREE * pairTag);
  return Object.freeze({
    base,
    circuitTag,
    pairTag,
    packed,
    circuit216: FIBRE_DEGREE * base + circuitTag,
    pair216: FIBRE_DEGREE * base + pairTag,
  });
}

function unpack(packed) {
  if (!Number.isInteger(packed) || packed < 0 || packed >= HYPERVISOR_STATES) {
    throw new RangeError("packed hypervisor address out of range");
  }
  const base = packed % BASE_STATES;
  const q = Math.floor(packed / BASE_STATES);
  const circuitTag = q % FIBRE_DEGREE;
  const pairTag = Math.floor(q / FIBRE_DEGREE);
  return coordinate(base, circuitTag, pairTag);
}

function selfCheck() {
  const packed = new Set();
  const circuitLifts = Array.from({ length: CARRIER_STATES }, () => new Set());
  const pairLifts = Array.from({ length: CARRIER_STATES }, () => new Set());
  const circuitToPair = Array.from({ length: CARRIER_STATES }, () => new Set());
  const pairToCircuit = Array.from({ length: CARRIER_STATES }, () => new Set());
  const perBase = Array(BASE_STATES).fill(0);

  for (let p = 0; p < FIBRE_DEGREE; p += 1) {
    for (let c = 0; c < FIBRE_DEGREE; c += 1) {
      for (let b = 0; b < BASE_STATES; b += 1) {
        const x = coordinate(b, c, p);
        packed.add(x.packed);
        circuitLifts[x.circuit216].add(x.packed);
        pairLifts[x.pair216].add(x.packed);
        circuitToPair[x.circuit216].add(x.pair216);
        pairToCircuit[x.pair216].add(x.circuit216);
        perBase[b] += 1;
        const y = unpack(x.packed);
        if (stable(x) !== stable(y)) throw new Error("pack/unpack mismatch");
      }
    }
  }

  const allSix = (rows) => rows.every((s) => s.size === FIBRE_DEGREE);
  const checks = Object.freeze({
    stateCount1296: packed.size === HYPERVISOR_STATES,
    statesPerBase36: perBase.every((n) => n === FIBRE_DEGREE * FIBRE_DEGREE),
    circuitProjectionSixToOne: allSix(circuitLifts),
    pairProjectionSixToOne: allSix(pairLifts),
    circuitDoesNotDeterminePair: allSix(circuitToPair),
    pairDoesNotDetermineCircuit: allSix(pairToCircuit),
  });
  return Object.freeze({
    ok: Object.values(checks).every(Boolean),
    checks,
    counts: Object.freeze({
      baseStates: BASE_STATES,
      carrierStatesEach: CARRIER_STATES,
      hypervisorStates: HYPERVISOR_STATES,
      statesPerBase: FIBRE_DEGREE * FIBRE_DEGREE,
      projectionDegree: FIBRE_DEGREE,
    }),
  });
}

module.exports = {
  MACHINE_TYPE,
  BASE_STATES,
  FIBRE_DEGREE,
  CARRIER_STATES,
  HYPERVISOR_STATES,
  bind,
  verify,
  coordinate,
  unpack,
  selfCheck,
};
