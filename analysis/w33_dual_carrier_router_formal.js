#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const cp=require("node:child_process");

const ROOT=path.resolve(__dirname,"..");
const MAIN="rtl/verify_w33_dual_carrier_router.ys";
const CONTROL="rtl/verify_w33_dual_carrier_router_control.ys";
const PACKET="data/w33_five_front_breakthrough.json";
const RTL="rtl/w33_dual_carrier_router.v";
const OUT=path.join(ROOT,"data","w33_dual_carrier_router_formal.json");

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
  if(packet.schema!=="holotrade.w33-five-front-breakthrough.v2" ||
     packet.microvm.generatorCount!==2 ||
     packet.microvm.carrierTypes.join("|")!=="sentinel-circuit|complementary-hemisystem-pair" ||
     packet.fibreProduct.commonBuildingDimension!==435 ||
     packet.fibreProduct.buildingCrossHomDimension!==18) {
    throw new Error("upstream exact packet is not the corrected dual-carrier theorem");
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
    schema:"holotrade.w33-dual-carrier-router-formal.v1",
    valid:true,
    source:{
      packet:PACKET,packetSha256:shaFile(PACKET),
      rtl:RTL,rtlSha256:shaFile(RTL),
      generatorCount:packet.microvm.generatorCount,
      carriers:packet.microvm.carrierTypes,
      nativeStatesPerCarrier:216,sharedQuotientStates:36,
    },
    theorem:{
      nativeActions:"Both exact PSp(4,3) generator pairs preserve their carrier and commute with projection to the common 36-state spread quotient.",
      adapter:"A cross-carrier request returns only the shared quotient state and the native 216-state output is 8'hff.",
      failClosed:"No RTL operation asserts a fabricated 216-to-216 conversion between the inequivalent carrier forks.",
    },
    positive,
    negativeControl:{
      ...negativeControl,
      mutation:"Expose state 0 when adapt=1 instead of the forbidden-state sentinel.",
      purpose:"Shows the no-fabricated-cross-state assertion is satisfiable and has teeth.",
    },
    boundary:"Exact combinational RTL over two finite permutation actions. This is not a CPU, microVM hypervisor, fabricated device, timing result, or physical identification.",
  };
  return {...body,sha256:crypto.createHash("sha256").update(canonical(body)).digest("hex")};
}
function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("formal certificate drifted");
  process.stdout.write(JSON.stringify({status:"PASS",positive:packet.positive.proved,control:packet.negativeControl.counterexample,variables:[packet.positive.variables,packet.negativeControl.variables],sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical};
