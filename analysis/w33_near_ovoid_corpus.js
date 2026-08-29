#!/usr/bin/env node
"use strict";

// Exact in-memory builder for the 2,880 optimal W33 near-ovoids, compressed as
// 360 minimum blockers x eight removable shell points. This is the JavaScript
// counterpart of analysis/w33_near_ovoid_adversarial_corpus.py and exists so
// experiments/tests do not depend on a generated JSON file being pre-existing.

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const S = require("../js/substrate.js");

let CACHE = null;

function solveTarget(target, pointLines) {
  const allowed = new Set();
  for (let p = 0; p < 40; p++) if (pointLines[p].every((l) => target[l] > 0)) allowed.add(p);
  const cand = S.LINES.map((L) => L.filter((p) => allowed.has(p)));
  const cnt = Array(40).fill(0), chosen = [], solutions = new Set();

  function rec() {
    if (chosen.length > 10) return;
    const chosenSet = new Set(chosen);
    let best = null;
    for (let l = 0; l < 40; l++) {
      if (cnt[l] > target[l]) return;
      const need = target[l] - cnt[l];
      if (!need) continue;
      const F = cand[l].filter((p) => !chosenSet.has(p) && pointLines[p].every((j) => cnt[j] < target[j]));
      if (F.length < need) return;
      const key = [F.length, -need, l];
      if (!best || key[0] < best.key[0] || (key[0] === best.key[0] && (key[1] < best.key[1] || (key[1] === best.key[1] && key[2] < best.key[2])))) best = { key, F, need };
    }
    if (!best) {
      if (chosen.length === 10) solutions.add([...chosen].sort((a,b)=>a-b).join(","));
      return;
    }
    function combos(xs, k, start = 0, acc = []) {
      if (acc.length === k) {
        const d = new Map();
        for (const p of acc) for (const j of pointLines[p]) d.set(j, (d.get(j) || 0) + 1);
        for (const [j,z] of d) if (cnt[j] + z > target[j]) return;
        chosen.push(...acc); for (const [j,z] of d) cnt[j] += z;
        rec();
        for (const [j,z] of d) cnt[j] -= z; chosen.splice(chosen.length - acc.length, acc.length);
        return;
      }
      for (let i = start; i <= xs.length - (k - acc.length); i++) combos(xs, k, i + 1, acc.concat(xs[i]));
    }
    combos(best.F, best.need);
  }
  rec();
  return [...solutions].sort().map((s) => s.split(",").map(Number));
}

function buildCorpus() {
  if (CACHE) return CACHE;
  const pointLines = Array.from({length:40},()=>[]);
  S.LINES.forEach((L,li)=>L.forEach((p)=>pointLines[p].push(li)));
  const blockers = new Map(), near = new Set();
  for (let a = 0; a < 40; a++) for (let b = 0; b < 40; b++) {
    if (a === b || !S.isAdjacent(a,b)) continue;
    const common = pointLines[a].filter((l)=>pointLines[b].includes(l));
    if (common.length !== 1) throw new Error("oriented edge has no unique hinge");
    const h = common[0], target = Array(40).fill(1);
    for (const l of pointLines[a]) if (l !== h) target[l] = 0;
    for (const l of pointLines[b]) if (l !== h) target[l] = 2;
    const sols = solveTarget(target, pointLines);
    if (sols.length !== 6) throw new Error(`expected six completions for ${a}->${b}, got ${sols.length}`);
    for (const sol of sols) {
      near.add(sol.join(","));
      const B = [...sol,a].sort((x,y)=>x-y), k=B.join(",");
      if (!blockers.has(k)) blockers.set(k,{blocker:B,center:b,removals:new Set()});
      const z=blockers.get(k); if (z.center !== b) throw new Error("blocker center ambiguity"); z.removals.add(a);
    }
  }
  if (near.size !== 2880 || blockers.size !== 360) throw new Error("corpus cardinality mismatch");
  const records=[...blockers.values()].map((z)=>({blocker:z.blocker,center:z.center,removals:[...z.removals].sort((a,b)=>a-b)}))
    .sort((x,y)=>x.blocker.join(",").localeCompare(y.blocker.join(","),undefined,{numeric:true}));
  if (!records.every((r)=>r.removals.length===8)) throw new Error("8-fold cover mismatch");
  const canon=JSON.stringify(records.map((r)=>({blocker:r.blocker,center:r.center,removals:r.removals})).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b))));
  CACHE={schema:"holotrade.w33-near-ovoid-adversarial-corpus.runtime.v1",valid:true,counts:{minimumBlockers:360,removalsPerBlocker:8,nearOvoids:2880},records,runtimeSha256:crypto.createHash("sha256").update(canon).digest("hex")};
  return CACHE;
}

function materialize(file = path.resolve(__dirname,"../data/w33_near_ovoid_adversarial_corpus.json")) {
  const z=buildCorpus(); fs.writeFileSync(file,JSON.stringify(z,null,2)+"\n"); return file;
}

if (require.main === module) {
  const z=buildCorpus();
  const written=process.argv.includes("--write") ? materialize() : null;
  process.stdout.write(JSON.stringify({status:"PASS",counts:z.counts,runtimeSha256:z.runtimeSha256,written},null,2)+"\n");
}
module.exports={buildCorpus,solveTarget,materialize};
