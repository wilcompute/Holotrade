"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const root=path.resolve(__dirname,"..");
const S=require(path.join(root,"js/substrate.js"));
const P=require(path.join(root,"scheduler/w33-migration-policy.js"));
const B=require(path.join(root,"scheduler/w33-near-ovoid-block-controller.js"));
const L=require(path.join(root,"scheduler/w33-local-recovery-controller.js"));
const {buildCorpus}=require(path.join(root,"analysis/w33_near_ovoid_corpus.js"));

function maskForPoint(p){
  let m=0n;
  S.LINES.forEach((line,li)=>{if(line.includes(p))m|=1n<<BigInt(li);});
  return m;
}

test("combined RTL embeds the exact W33 point-line masks",()=>{
  const rtl=fs.readFileSync(path.join(root,"rtl/w33_recovery_two_stage_core.v"),"utf8");
  const found=new Map();
  for(const m of rtl.matchAll(/6'd(\d+): plmask=40'h([0-9a-f]+);/g))found.set(Number(m[1]),BigInt(`0x${m[2]}`));
  assert.equal(found.size,40);
  for(let p=0;p<40;p++){
    assert.equal(found.get(p),maskForPoint(p),`point-line mask mismatch at ${p}`);
    assert.equal(found.get(p).toString(2).split("1").length-1,4);
  }
});

test("entry selector matches the generic policy objective on all 2880 near-ovoids",()=>{
  let n=0,identity=0;
  for(const r of buildCorpus().records)for(const a of r.removals){
    const busy=r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
    const tiny=B.chooseMove(busy);
    const full=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
    assert.equal(tiny.rays,3); assert.equal(tiny.hops,1);
    assert.equal(tiny.freeLinesAfterMove,6);
    assert.equal(tiny.freeLinesAfterMove,full.freeLinesAfterMove);
    if(tiny.from===full.from&&tiny.to===full.to)identity++;
    n++;
  }
  assert.equal(n,2880);
  assert.equal(identity,664);
});

test("post-entry local scorer reproduces the exact generic second move",()=>{
  let n=0;
  for(const r of buildCorpus().records)for(const a of r.removals){
    const start=r.blocker.filter((x)=>x!==a).sort((x,y)=>x-y);
    const first=P.chooseMigration(start,{policy:P.POLICY.TOPOLOGY_AWARE}).nextBusy;
    const local=L.chooseMigration(first);
    const full=P.chooseMigration(first,{policy:P.POLICY.TOPOLOGY_AWARE});
    assert.deepEqual([local.from,local.to],[full.from,full.to]);
    assert.equal(local.freeLinesAfterMove,9);
    n++;
  }
  assert.equal(n,2880);
});
