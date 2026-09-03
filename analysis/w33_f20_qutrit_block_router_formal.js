#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const cp=require("node:child_process");

const ROOT=path.resolve(__dirname,"..");
const MAIN="rtl/verify_w33_f20_qutrit_block_router.ys";
const CONTROL="rtl/verify_w33_f20_qutrit_block_router_control.ys";
const PACKET="data/w33_f20_qutrit_block_bridge.json";
const RTL="rtl/w33_f20_qutrit_block_router.v";
const OUT=path.join(ROOT,"data","w33_f20_qutrit_block_router_formal.json");

function shaFile(rel){
  return crypto.createHash("sha256").update(fs.readFileSync(path.join(ROOT,rel))).digest("hex");
}
function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function run(script){
  const r=cp.spawnSync(process.execPath,["scripts/run-yosys.js",script],{
    cwd:ROOT,encoding:"utf8",maxBuffer:64*1024*1024,
  });
  const log=(r.stdout||"")+(r.stderr||"");
  const size=/Solving problem with (\d+) variables and (\d+) clauses/.exec(log);
  return {
    script,
    exitCode:r.status,
    variables:size?Number(size[1]):null,
    clauses:size?Number(size[2]):null,
    proved:/SAT proof finished - no model found: SUCCESS/.test(log),
    counterexample:/SAT proof finished - model found: FAIL/.test(log),
  };
}
function build(){
  const packet=JSON.parse(fs.readFileSync(path.join(ROOT,PACKET),"utf8"));
  const action=packet.cyclicQutritBlock?.addressedPauliAction;
  if(packet.schema!=="holotrade.w33-f20-qutrit-block-bridge.v1" ||
     packet.status!=="PASS" || packet.fibreProductF20?.stabilizerOrder!==20 ||
     action?.degree!==40 || action?.groupOrder!==20 ||
     packet.fibreProductF20?.conjugationExponent!==3) {
    throw new Error("upstream packet is not the exact presentation-matched F20 action");
  }
  const positive=run(MAIN);
  const negativeControl=run(CONTROL);
  if(positive.exitCode!==0||!positive.proved||positive.counterexample) {
    throw new Error(`positive formal proof failed: ${JSON.stringify(positive)}`);
  }
  if(negativeControl.exitCode===0||negativeControl.proved||!negativeControl.counterexample) {
    throw new Error(`negative control did not fail: ${JSON.stringify(negativeControl)}`);
  }
  const body={
    schema:"holotrade.w33-f20-qutrit-block-router-formal.v1",
    status:"PASS",
    evidenceClass:"YOSYS_SAT_PROOF_WITH_MUTATION_CONTROL",
    source:{
      packet:PACKET,packetSha256:`sha256:${shaFile(PACKET)}`,
      rtl:RTL,rtlSha256:`sha256:${shaFile(RTL)}`,
      degree:action.degree,groupOrder:action.groupOrder,
    },
    theorem:{
      closure:"Both generated transition tables map every valid six-bit address back into the forty-state Pauli address space.",
      presentation:"The hardware tables satisfy T^5=M^4=1 and M T M^-1=T^3 on all forty addressed nonidentity single-site qutrit Paulis.",
      interface:"One opcode bit selects a total, deterministic F20 generator transition on valid addresses; invalid addresses fail closed.",
    },
    positive,
    negativeControl:{
      ...negativeControl,
      mutation:"Replace the Clifford-compensated multiplier by the identity transition.",
      purpose:"Proves the order-four multiplier assertion is not vacuous and catches omission of the local Clifford compensation.",
    },
    boundary:"This proves the finite forty-address controller and its presentation. It is not a timing closure, physical qutrit device, threshold measurement, or fault-tolerant recode proof.",
  };
  return {...body,sha256:`sha256:${crypto.createHash("sha256").update(canonical(body)).digest("hex")}`};
}
function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("F20 qutrit formal certificate drifted");
  process.stdout.write(JSON.stringify({status:packet.status,positive:packet.positive.proved,control:packet.negativeControl.counterexample,variables:[packet.positive.variables,packet.negativeControl.variables],sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical};
