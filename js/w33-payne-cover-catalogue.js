// Production catalogue for the 40 cheap-axis -> 45 slow-target Payne covers.
//
// Cover incidence remains certificate-backed, but target geometry is now decoded
// directly from the slow target matrix via ker(g-I) and ker(g+I). The frozen
// minimum-word dictionary is consulted only inside the independent eigenspace
// decoder's boot check; it is no longer the source of runtime geometry.
"use strict";

const cert = require("../data/slow_path_is_payne_derivative.json");
const spectral = require("../data/payne_cover_spectral_intertwiner.json");
const rom = require("../data/the_45_slot_rom_bijection.json");
const {
  AXES,
  axisDistance,
  bootCheck: eigenspaceBootCheck,
  geometryFromMatrix,
  stageFromMatrix,
  symplectic,
} = require("./w33-slowpath-eigenspace-geometry.js");

function intersectionSize(a, b) { let n = 0; for (const x of a) if (b.has(x)) n += 1; return n; }
function collinearSlow(a, b) { return rom.linesB.some((line) => line.includes(a) && line.includes(b)); }
function sortedNumeric(xs) { return [...xs].sort((a, b) => a - b); }
const ROM_BY_SLOT = new Map((rom.table || []).map((row) => [row.slot, row]));

function bootCheck() {
  const errors = [];
  if (cert.schema !== "holotrade.slow-path-is-payne-derivative.v1" || cert.status !== "PASS") errors.push("PAYNE_CERT");
  if (spectral.schema !== "holotrade.payne-cover-spectral-intertwiner.v1" || spectral.status !== "PASS") errors.push("SPECTRAL_CERT");
  if (!rom.valid || !Array.isArray(rom.linesB) || rom.linesB.length !== 27 || ROM_BY_SLOT.size !== 45) errors.push("ROM_CERT");
  const eig = eigenspaceBootCheck();
  if (!eig.ok) errors.push(...eig.errors.map((e) => `EIGENSPACE_${e}`));

  const raw = cert.equivariant40 && cert.equivariant40.covers;
  if (!raw || Object.keys(raw).length !== 40) errors.push("COVERS_NOT_40");
  const covers = Array.from({ length: 40 }, (_, a) => new Set((raw && raw[String(a)]) || []));
  if (covers.some((s) => s.size !== 9 || [...s].some((x) => !Number.isInteger(x) || x < 0 || x >= 45))) errors.push("COVER_NOT_9");
  const byTarget = Array.from({ length: 45 }, () => []);
  covers.forEach((s, a) => s.forEach((t) => byTarget[t].push(a)));
  if (byTarget.some((a) => a.length !== 8)) errors.push("TARGET_NOT_IN_8_COVERS");

  // The runtime derivation and the global Payne incidence certificate must agree
  // on every target, so a stale ROM or certificate fails closed at boot.
  for (let t = 0; t < 45; t += 1) {
    const row = ROM_BY_SLOT.get(t);
    if (!row) { errors.push(`ROM_SLOT_${t}`); continue; }
    try {
      const g = geometryFromMatrix(row.spMatrix);
      if (JSON.stringify(g.payneCoverAxes) !== JSON.stringify(sortedNumeric(byTarget[t]))) errors.push(`EIGENSPACE_COVER_${t}`);
      for (let a = 0; a < 40; a += 1) if (stageFromMatrix(row.spMatrix, a).routeDistance > 1) errors.push(`EIGENSPACE_RADIUS_${t}_${a}`);
    } catch (e) { errors.push(`EIGENSPACE_SLOT_${t}_${e.message}`); }
  }

  for (let i = 0; i < 40; i += 1) for (let j = i + 1; j < 40; j += 1) {
    const want = symplectic(AXES[i], AXES[j]) === 0 ? 3 : 1;
    if (intersectionSize(covers[i], covers[j]) !== want) errors.push(`FAST_PAIR_${i}_${j}`);
  }
  for (let i = 0; i < 45; i += 1) for (let j = i + 1; j < 45; j += 1) {
    const co = byTarget[i].filter((a) => byTarget[j].includes(a)).length;
    const want = collinearSlow(i, j) ? 0 : 2;
    if (co !== want) errors.push(`SLOW_PAIR_${i}_${j}`);
  }
  return { ok: errors.length === 0, errors, covers, byTarget, matrixDerivedGeometry: true };
}

class PayneCoverCatalogue {
  constructor() {
    const b = bootCheck();
    if (!b.ok) throw new Error(`Payne cover catalogue boot refused: ${b.errors.slice(0, 8).join(",")}`);
    this.covers = b.covers.map((s) => Object.freeze(sortedNumeric(s)));
    this.byTarget = b.byTarget.map((a) => Object.freeze(sortedNumeric(a)));
    this.schema = cert.schema;
    this.geometryDerivation = "TARGET_MATRIX_EIGENSPACES";
  }
  coverForAxis(axis) {
    if (!Number.isInteger(axis) || axis < 0 || axis >= 40) throw new RangeError("axis must be 0..39");
    return this.covers[axis];
  }
  axesForTarget(slot) {
    if (!Number.isInteger(slot) || slot < 0 || slot >= 45) throw new RangeError("slot must be 0..44");
    return this.byTarget[slot];
  }
  targetGeometry(slot) {
    if (!Number.isInteger(slot) || slot < 0 || slot >= 45) throw new RangeError("slot must be 0..44");
    const row = ROM_BY_SLOT.get(slot); if (!row) throw new Error(`missing ROM slot ${slot}`);
    const g = geometryFromMatrix(row.spMatrix);
    if (JSON.stringify(g.payneCoverAxes) !== JSON.stringify(this.axesForTarget(slot))) throw new Error(`matrix-derived geometry disagrees with Payne cover certificate at slot ${slot}`);
    return Object.freeze({ slot, ...g });
  }
  role(axis, slot) { return this.coverForAxis(axis).includes(slot) ? "NEW_HYPERBOLIC_LINE" : "INHERITED_W33_LINE"; }
  axisDistance(a, b) { return axisDistance(a, b); }
  stage(slot, currentAxis = null) {
    if (!Number.isInteger(slot) || slot < 0 || slot >= 45) throw new RangeError("slot must be 0..44");
    const row = ROM_BY_SLOT.get(slot); if (!row) throw new Error(`missing ROM slot ${slot}`);
    const staged = stageFromMatrix(row.spMatrix, currentAxis);
    if (JSON.stringify(staged.candidateAxes) !== JSON.stringify(this.axesForTarget(slot))) throw new Error(`matrix-derived staging disagrees with Payne certificate at slot ${slot}`);
    return Object.freeze({ slot, ...staged });
  }
}

module.exports = { PayneCoverCatalogue, AXES, bootCheck, symplectic };
