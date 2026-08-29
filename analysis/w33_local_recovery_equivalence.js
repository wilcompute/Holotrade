#!/usr/bin/env node
"use strict";

const P=require("../scheduler/w33-migration-policy.js");
const L=require("../scheduler/w33-local-recovery-controller.js");
const {buildCorpus}=require("./w33_near_ovoid_corpus.js");

function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}
function run(steps=32){
  const corpus=buildCorpus(),starts=[];for(const r of corpus.records)for(const a of r.removals)starts.push(r.blocker.filter((x)=>x!==a));
  const unique=new Set();let decisions=0;
  for(const start of starts){
    let busy=[...start].sort((a,b)=>a-b);
    for(let t=0;t<steps;t++){
      unique.add(key(busy));
      const generic=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
      const local=L.chooseMigration(busy);
      if(generic.from!==local.from||generic.to!==local.to||generic.freeLinesAfterMove!==local.freeLinesAfterMove||generic.freeLinesAfterRelease!==local.freeLinesAfterRelease){
        throw new Error(`local/generic mismatch at ${key(busy)}`);
      }
      if(local.rays!==3||local.hops!==1)throw new Error("healthy trajectory left the 3-ray/1-hop floor");
      busy=local.nextBusy;decisions++;
    }
  }
  if(starts.length!==2880||decisions!==2880*steps||unique.size!==25184)throw new Error("frozen trajectory census changed");
  return {
    schema:"holotrade.w33-local-recovery-equivalence.v1",status:"PASS",startStates:starts.length,steps,decisions,distinctVisitedStates:unique.size,
    identity:"F_after = F + s1(source) - z(destination) - 1[shared line was singleton]",
    primaryFloor:"every busy source has at least three adjacent idle destinations because k=12 and there are only nine other busy points",
    exactDecisionMatches:decisions,
    theorem:"On every healthy ten-busy state encountered in the complete 32-step corpus, the local incidence-score controller makes exactly the same source/destination decision as the generic topology-aware policy. The score identity itself is algebraic for every healthy ten-busy W33 state.",
    boundary:"Failed-node masks require the failure-aware policy because failed points alter free-line counts and can remove adjacent destinations."
  };
}
if(require.main===module)process.stdout.write(JSON.stringify(run(),null,2)+"\n");
module.exports={run};
