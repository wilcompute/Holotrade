// Production-facing PSp(4,3) compiler + certified GQ(4,2) slow-path decoder.
//
// This is the Node/runtime counterpart of the exhaustive Python theorem in
// analysis/w33_projective_slowpath_microsequencer.py.  It compiles both central
// Sp lifts algorithmically, chooses the shorter projective word, and consults
// the boot-verified 45-target ROM only to classify/annotate the exceptional
// branch.  The ROM never substitutes for compilation.

"use strict";

const { SlowPathROMDecoder, matrixKey, projectiveCanonical } = require("./w33-slowpath-rom-decoder.js");

const Q = 3;
const D = 4;
const I = Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => (i === j ? 1 : 0)));
const BASIS = Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => (i === j ? 1 : 0)));

function mod(x) { const y = x % Q; return y < 0 ? y + Q : y; }
function cloneMatrix(A) { return A.map((r) => [...r]); }
function neg(A) { return A.map((r) => r.map((x) => mod(-x))); }
function matMul(A, B) {
  return Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => {
    let s = 0; for (let k = 0; k < D; k += 1) s += A[i][k] * B[k][j]; return mod(s);
  }));
}
function act(A, v) {
  return Array.from({ length: D }, (_, i) => mod(A[i].reduce((s, x, k) => s + x * v[k], 0)));
}
function equalMatrix(A, B) { return matrixKey(A) === matrixKey(B); }
function symplectic(a, b) { return mod(a[0] * b[2] - a[2] * b[0] + a[1] * b[3] - a[3] * b[1]); }
function vectorKey(v) { return v.join(""); }
function canonAxis(v) {
  const i = v.findIndex((x) => mod(x) !== 0);
  if (i < 0) throw new Error("zero vector has no projective axis");
  const inv = mod(v[i]) === 1 ? 1 : 2;
  return v.map((x) => mod(inv * x));
}
function buildAxes() {
  const map = new Map();
  for (let n = 1; n < 81; n += 1) {
    const v = [n % 3, Math.floor(n / 3) % 3, Math.floor(n / 9) % 3, Math.floor(n / 27) % 3];
    const c = canonAxis(v); map.set(vectorKey(c), c);
  }
  return [...map.values()].sort((a, b) => vectorKey(a).localeCompare(vectorKey(b)));
}
const AXES = buildAxes();
if (AXES.length !== 40) throw new Error(`expected 40 projective axes, got ${AXES.length}`);

function transvection(v, lambda) {
  if (lambda !== 1 && lambda !== 2) throw new Error("lambda must be 1 or 2");
  return Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) =>
    mod((i === j ? 1 : 0) + lambda * symplectic(BASIS[j], v) * v[i])));
}
const GENS = [];
const GEN_BY_MATRIX = new Map();
AXES.forEach((v, axis) => {
  for (const lambda of [1, 2]) {
    const matrix = transvection(v, lambda);
    const row = Object.freeze({ axis, lambda, matrix });
    GENS.push(row); GEN_BY_MATRIX.set(matrixKey(matrix), row);
  }
});
if (GEN_BY_MATRIX.size !== 80) throw new Error("transvection generator collision");

const NONZERO_VECTORS = [];
for (let n = 1; n < 81; n += 1) {
  NONZERO_VECTORS.push([n % 3, Math.floor(n / 3) % 3, Math.floor(n / 9) % 3, Math.floor(n / 27) % 3]);
}

function inverse(A) {
  const aug = Array.from({ length: D }, (_, i) => [...A[i], ...BASIS[i]]);
  let r = 0;
  for (let c = 0; c < D; c += 1) {
    let p = r; while (p < D && mod(aug[p][c]) === 0) p += 1;
    if (p === D) throw new Error("singular matrix");
    [aug[r], aug[p]] = [aug[p], aug[r]];
    const iv = mod(aug[r][c]) === 1 ? 1 : 2;
    aug[r] = aug[r].map((x) => mod(x * iv));
    for (let i = 0; i < D; i += 1) if (i !== r && mod(aug[i][c]) !== 0) {
      const f = mod(aug[i][c]); aug[i] = aug[i].map((x, j) => mod(x - f * aug[r][j]));
    }
    r += 1;
  }
  return aug.map((row) => row.slice(D));
}

function residue(A) {
  const M = Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => mod(A[i][j] - (i === j ? 1 : 0))));
  let r = 0;
  for (let c = 0; c < D; c += 1) {
    let p = r; while (p < D && M[p][c] === 0) p += 1;
    if (p === D) continue;
    [M[r], M[p]] = [M[p], M[r]];
    const iv = M[r][c] === 1 ? 1 : 2;
    M[r] = M[r].map((x) => mod(x * iv));
    for (let i = 0; i < D; i += 1) if (i !== r && M[i][c] !== 0) {
      const f = M[i][c]; M[i] = M[i].map((x, j) => mod(x - f * M[r][j]));
    }
    r += 1;
  }
  return r;
}
function projectiveResidue(A) { return Math.min(residue(A), residue(neg(A))); }

function isHyperbolic(A) {
  const B = Array.from({ length: D }, (_, i) => Array.from({ length: D }, (_, j) => symplectic(BASIS[i], act(A, BASIS[j]))));
  for (let i = 0; i < D; i += 1) if (B[i][i] !== 0) return false;
  for (let i = 0; i < D; i += 1) for (let j = 0; j < D; j += 1) if (mod(B[i][j] + B[j][i]) !== 0) return false;
  return true;
}

function compileSpPeeling(target) {
  let cur = cloneMatrix(target);
  const peeled = [];
  while (!equalMatrix(cur, I)) {
    if (isHyperbolic(cur)) {
      let chosen = null;
      for (const gen of GENS) {
        const C = matMul(cur, gen.matrix);
        if (residue(C) === residue(cur) && !isHyperbolic(C)) { chosen = { ...gen, next: C }; break; }
      }
      if (!chosen) throw new Error("hyperbolic fix-up missing");
      peeled.push([chosen.axis, chosen.lambda]); cur = chosen.next; continue;
    }

    const gi = inverse(cur);
    let fallback = null; let chosen = null;
    for (const x of NONZERO_VECTORS) {
      const gx = act(gi, x); const c = symplectic(x, gx);
      if (c === 0) continue;
      const v = gx.map((z, k) => mod(z - x[k]));
      if (v.every((z) => z === 0)) continue;
      const lambda = c === 1 ? 1 : 2;
      const M = transvection(v, lambda); const C = matMul(cur, M);
      if (residue(C) !== residue(cur) - 1) continue;
      const meta = GEN_BY_MATRIX.get(matrixKey(M));
      if (!meta) throw new Error("residue pivot is not one of the 80 transvection opcodes");
      const item = { axis: meta.axis, lambda: meta.lambda, next: C };
      if (equalMatrix(C, I) || !isHyperbolic(C)) { chosen = item; break; }
      if (!fallback) fallback = item;
    }
    const step = chosen || fallback;
    if (!step) throw new Error("residue-dropping pivot missing");
    peeled.push([step.axis, step.lambda]); cur = step.next;
  }
  // g*T1*...*Tk=I, hence execution from I is Tk^-1...T1^-1.
  return peeled.reverse().map(([axis, lambda]) => [axis, mod(-lambda)]);
}

function wordProduct(word) {
  let P = cloneMatrix(I);
  for (const [axis, lambda] of word) P = matMul(P, transvection(AXES[axis], lambda));
  return P;
}

function lexicalWord(word) { return word.map(([a, l]) => `${String(a).padStart(2, "0")}:${l}`).join("|"); }

class ProjectiveMicrosequencer {
  constructor(decoder = new SlowPathROMDecoder()) { this.decoder = decoder; }

  compile(matrix) {
    const target = projectiveCanonical(matrix);
    const candidates = [target, neg(target)].map((lift, liftBit) => {
      const word = compileSpPeeling(lift);
      return { lift, liftBit, word, key: lexicalWord(word) };
    });
    candidates.sort((a, b) => a.word.length - b.word.length || a.key.localeCompare(b.key) || a.liftBit - b.liftBit);
    const best = candidates[0];
    if (matrixKey(projectiveCanonical(wordProduct(best.word))) !== matrixKey(target)) throw new Error("compiled word failed projective reconstruction");
    const slow = this.decoder.decode(target);
    return Object.freeze({
      target: Object.freeze(target.map((r) => Object.freeze([...r]))),
      word: Object.freeze(best.word.map((x) => Object.freeze([...x]))),
      length: best.word.length,
      projectiveResidue: projectiveResidue(target),
      centralLiftBit: best.liftBit,
      slow,
      routeClass: slow.slow ? "GQ45_EXTRA_TRANSVECTION" : "RESIDUE_LENGTH",
    });
  }
}

function projectiveBfs() {
  const identity = projectiveCanonical(I); const dist = new Map([[matrixKey(identity), { matrix: identity, distance: 0 }]]);
  const queue = [identity]; let head = 0;
  while (head < queue.length) {
    const A = queue[head++]; const d = dist.get(matrixKey(A)).distance;
    for (const gen of GENS) {
      const C = projectiveCanonical(matMul(A, gen.matrix)); const key = matrixKey(C);
      if (!dist.has(key)) { dist.set(key, { matrix: C, distance: d + 1 }); queue.push(C); }
    }
  }
  return dist;
}

function verifyExhaustive() {
  const seq = new ProjectiveMicrosequencer(); const dist = projectiveBfs();
  if (dist.size !== 25920) throw new Error(`PSp census ${dist.size} != 25920`);
  const hist = new Map(); let exact = 0; let reconstruct = 0; let anomalyAgreement = 0; let slow = 0;
  for (const { matrix, distance } of dist.values()) {
    const row = seq.compile(matrix); hist.set(row.length, (hist.get(row.length) || 0) + 1);
    if (row.length === distance) exact += 1;
    if (matrixKey(projectiveCanonical(wordProduct(row.word))) === matrixKey(matrix)) reconstruct += 1;
    const expectedSlow = distance > projectiveResidue(matrix);
    if (Boolean(row.slow.slow) === expectedSlow) anomalyAgreement += 1;
    if (row.slow.slow) {
      slow += 1;
      if (row.length !== row.projectiveResidue + 1) throw new Error("slow target is not one-extra-transvection");
      if (!Array.isArray(row.slow.banks) || row.slow.banks.length !== 3) throw new Error("slow target lost GQ bank triple");
    }
  }
  const histogram = Object.fromEntries([...hist.entries()].sort((a, b) => a[0] - b[0]));
  const expected = { 0: 1, 1: 80, 2: 1980, 3: 13005, 4: 10854 };
  const checks = {
    pspOrder25920: dist.size === 25920,
    allRuntimeCompilerLengthsEqualBfs: exact === dist.size,
    allRuntimeWordsReconstructTarget: reconstruct === dist.size,
    slowDecoderExactlyEqualsResidueAnomaly: anomalyAgreement === dist.size,
    exactly45SlowTargets: slow === 45,
    expectedLengthHistogram: JSON.stringify(histogram) === JSON.stringify(expected),
  };
  return { schema: "holotrade.production-projective-microsequencer.v1", status: Object.values(checks).every(Boolean) ? "PASS" : "FAIL", checks, verification: { targets: dist.size, slowTargets: slow, histogram } };
}

if (require.main === module) {
  const out = verifyExhaustive(); console.log(JSON.stringify(out, null, 2)); process.exit(out.status === "PASS" ? 0 : 1);
}

module.exports = {
  ProjectiveMicrosequencer,
  AXES,
  GENS,
  compileSpPeeling,
  inverse,
  isHyperbolic,
  matMul,
  neg,
  projectiveBfs,
  projectiveResidue,
  residue,
  transvection,
  verifyExhaustive,
  wordProduct,
};
