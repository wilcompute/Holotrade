// Production catalogue for the 40 cheap-axis -> 45 slow-target Payne covers.
// The certificate is generated and proved by analysis/the_slow_path_is_the_payne_derivative.py.
"use strict";

const cert = require("../data/slow_path_is_payne_derivative.json");
const spectral = require("../data/payne_cover_spectral_intertwiner.json");
const rom = require("../data/the_45_slot_rom_bijection.json");

const Q = 3;
function mod(x) { const y = x % Q; return y < 0 ? y + Q : y; }
function symplectic(a, b) { return mod(a[0] * b[2] - a[2] * b[0] + a[1] * b[3] - a[3] * b[1]); }
function key(v) { return v.join(""); }
function canon(v) {
  const i = v.findIndex((x) => mod(x) !== 0);
  if (i < 0) throw new Error("zero axis");
  const z = mod(v[i]) === 1 ? 1 : 2;
  return v.map((x) => mod(z * x));
}
function buildAxes() {
  const m = new Map();
  for (let n = 1; n < 81; n += 1) {
    const v = [n % 3, Math.floor(n / 3) % 3, Math.floor(n / 9) % 3, Math.floor(n / 27) % 3];
    const c = canon(v); m.set(key(c), c);
  }
  return [...m.values()].sort((a, b) => key(a).localeCompare(key(b)));
}
const AXES = buildAxes();

function intersectionSize(a, b) { let n = 0; for (const x of a) if (b.has(x)) n += 1; return n; }
function collinearSlow(a, b) { return rom.linesB.some((line) => line.includes(a) && line.includes(b)); }

function bootCheck() {
  const errors = [];
  if (cert.schema !== "holotrade.slow-path-is-payne-derivative.v1" || cert.status !== "PASS") errors.push("PAYNE_CERT");
  if (spectral.schema !== "holotrade.payne-cover-spectral-intertwiner.v1" || spectral.status !== "PASS") errors.push("SPECTRAL_CERT");
  if (!rom.valid || !Array.isArray(rom.linesB) || rom.linesB.length !== 27) errors.push("ROM_CERT");
  const raw = cert.equivariant40 && cert.equivariant40.covers;
  if (!raw || Object.keys(raw).length !== 40) errors.push("COVERS_NOT_40");
  const covers = Array.from({ length: 40 }, (_, a) => new Set((raw && raw[String(a)]) || []));
  if (covers.some((s) => s.size !== 9 || [...s].some((x) => !Number.isInteger(x) || x < 0 || x >= 45))) errors.push("COVER_NOT_9");
  const byTarget = Array.from({ length: 45 }, () => []);
  covers.forEach((s, a) => s.forEach((t) => byTarget[t].push(a)));
  if (byTarget.some((a) => a.length !== 8)) errors.push("TARGET_NOT_IN_8_COVERS");
  if (AXES.length !== 40 || key(AXES[0]) !== cert.baseW33Vector.join("")) errors.push("AXIS_ORDER_MISMATCH");
  for (let i = 0; i < 40; i += 1) for (let j = i + 1; j < 40; j += 1) {
    const want = symplectic(AXES[i], AXES[j]) === 0 ? 3 : 1;
    if (intersectionSize(covers[i], covers[j]) !== want) errors.push(`FAST_PAIR_${i}_${j}`);
  }
  for (let i = 0; i < 45; i += 1) for (let j = i + 1; j < 45; j += 1) {
    const co = byTarget[i].filter((a) => byTarget[j].includes(a)).length;
    const want = collinearSlow(i, j) ? 0 : 2;
    if (co !== want) errors.push(`SLOW_PAIR_${i}_${j}`);
  }
  return { ok: errors.length === 0, errors, covers, byTarget };
}

class PayneCoverCatalogue {
  constructor() {
    const b = bootCheck();
    if (!b.ok) throw new Error(`Payne cover catalogue boot refused: ${b.errors.slice(0, 8).join(",")}`);
    this.covers = b.covers.map((s) => Object.freeze([...s].sort((a, b) => a - b)));
    this.byTarget = b.byTarget.map((a) => Object.freeze([...a].sort((x, y) => x - y)));
    this.schema = cert.schema;
  }
  coverForAxis(axis) {
    if (!Number.isInteger(axis) || axis < 0 || axis >= 40) throw new RangeError("axis must be 0..39");
    return this.covers[axis];
  }
  axesForTarget(slot) {
    if (!Number.isInteger(slot) || slot < 0 || slot >= 45) throw new RangeError("slot must be 0..44");
    return this.byTarget[slot];
  }
  role(axis, slot) { return this.coverForAxis(axis).includes(slot) ? "NEW_HYPERBOLIC_LINE" : "INHERITED_W33_LINE"; }
  axisDistance(a, b) {
    if (a === b) return 0;
    return symplectic(AXES[a], AXES[b]) === 0 ? 1 : 2;
  }
  stage(slot, currentAxis = null) {
    const choices = this.axesForTarget(slot);
    if (currentAxis === null || currentAxis === undefined) {
      return Object.freeze({ slot, chosenAxis: choices[0], routeDistance: null, role: "NEW_HYPERBOLIC_LINE", candidateAxes: choices });
    }
    if (!Number.isInteger(currentAxis) || currentAxis < 0 || currentAxis >= 40) throw new RangeError("currentAxis must be 0..39");
    const chosenAxis = [...choices].sort((a, b) => this.axisDistance(currentAxis, a) - this.axisDistance(currentAxis, b) || a - b)[0];
    return Object.freeze({ slot, currentAxis, chosenAxis, routeDistance: this.axisDistance(currentAxis, chosenAxis), role: "NEW_HYPERBOLIC_LINE", candidateAxes: choices });
  }
}

module.exports = { PayneCoverCatalogue, AXES, bootCheck, symplectic };
