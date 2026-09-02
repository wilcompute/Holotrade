#!/usr/bin/env node
"use strict";

// Exact software certificate for the composed near-ovoid recovery path.
// Stage one is the actual one-bit block controller, not the generic policy.
// Every later healthy move is checked against the generic policy, while the
// RTL section records only what the current source/harness really establishes.

const fs=require("node:fs");
const path=require("node:path");
const P=require("../scheduler/w33-migration-policy.js");
const B=require("../scheduler/w33-near-ovoid-block-controller.js");
const L=require("../scheduler/w33-local-recovery-controller.js");
const {buildCorpus}=require("./w33_near_ovoid_corpus.js");

const OUT=path.join(__dirname,"..","data","w33_recovery_two_stage_core.json");
function key(xs){return [...xs].sort((a,b)=>a-b).join(",");}

function starts(){
  const out=[];
  for(const record of buildCorpus().records)for(const removed of record.removals){
    out.push(record.blocker.filter((x)=>x!==removed).sort((a,b)=>a-b));
  }
  if(out.length!==2880)throw new Error("near-ovoid start count changed");
  return out;
}

function run(steps=32){
  let entryExact=0,secondMatches=0,decisions=0,exactGeneric=0;
  const visited=new Set();
  for(const start of starts()){
    const entry=B.chooseMove(start);
    const genericEntry=P.chooseMigration(start,{policy:P.POLICY.TOPOLOGY_AWARE});
    if(entry.rays!==3||entry.hops!==1||entry.freeLinesAfterMove!==6){
      throw new Error(`entry objective changed at ${key(start)}`);
    }
    if(entry.from===genericEntry.from&&entry.to===genericEntry.to)entryExact++;

    const second=L.chooseMigration(entry.nextBusy);
    const genericSecond=P.chooseMigration(entry.nextBusy,{policy:P.POLICY.TOPOLOGY_AWARE});
    if(second.from!==genericSecond.from||second.to!==genericSecond.to||
       second.freeLinesAfterMove!==genericSecond.freeLinesAfterMove||
       second.freeLinesAfterRelease!==genericSecond.freeLinesAfterRelease){
      throw new Error(`actual composed second move mismatch at ${key(entry.nextBusy)}`);
    }
    if(second.freeLinesAfterMove!==9)throw new Error("composed second move lost nine-line guarantee");
    secondMatches++;

    let busy=entry.nextBusy;
    for(let t=0;t<steps;t++){
      visited.add(key(busy));
      const local=L.chooseMigration(busy);
      const generic=P.chooseMigration(busy,{policy:P.POLICY.TOPOLOGY_AWARE});
      if(local.from===generic.from&&local.to===generic.to&&
         local.freeLinesAfterMove===generic.freeLinesAfterMove&&
         local.freeLinesAfterRelease===generic.freeLinesAfterRelease)exactGeneric++;
      else throw new Error(`local/generic mismatch at ${key(busy)}`);
      busy=local.nextBusy;decisions++;
    }
  }
  if(entryExact!==664||secondMatches!==2880||decisions!==92160||
     exactGeneric!==92160||visited.size!==21058)throw new Error("two-stage census changed");

  return {
    schema:"holotrade.w33-recovery-two-stage-core.v2",status:"PASS",
    entryStage:{
      states:2880,
      controller:"one-bit 3+3 block selector chooses one residual hinge source",
      objectiveEquivalentStates:2880,
      exactGenericMoveIdentityMatches:entryExact,
      rays:3,hops:1,freeLinesAfterMove:6,
    },
    postEntryStage:{
      startsFromActualBlockControllerMove:true,
      identity:"F_after = F + s1(source) - z(destination) - 1[shared line was singleton]",
      secondMoveExactMatches:secondMatches,
      secondMoveFreeLines:9,
      longHorizonValidation:{
        stepsAfterEntry:steps,
        decisions,
        distinctVisitedStates:visited.size,
        exactGenericDecisionMatches:exactGeneric,
      },
    },
    rtl:{
      source:"rtl/w33_recovery_two_stage_core.v",
      embeddedGeometry:"40 exact point-line masks plus the 40 four-point W33 lines",
      registeredBitsAtSourceLevel:3,
      registeredFields:["valid","entry_q","block_q"],
      externalInputs:["block_in","residual_lo","residual_hi","busy"],
      derivesSelectorMetadataInternally:false,
      updatesBusyStateInternally:false,
      verifyHarness:"rtl/verify_w33_recovery_two_stage_core.ys",
      synthesisHarness:"rtl/synth_w33_recovery_two_stage_core.ys",
      harnessScope:"structural check/stat only; no SAT miter or behavioral equivalence proof",
      formalEquivalenceProved:false,
      measuredLutCount:null,
      measuredSynthesizedCellCount:null,
    },
    boundary:"Exhaustive software regression proves the composed healthy decision semantics. The current RTL consumes externally derived selector metadata and busy-state updates; its supplied Yosys harness is structural only and has not closed elaboration or formal equivalence in the recorded toolchain. Failure-aware decisions remain a separate policy surface.",
  };
}

if(require.main===module){
  const out=run(),json=JSON.stringify(out,null,2)+"\n";
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,json);
  process.stdout.write(json);
}
module.exports={run};
