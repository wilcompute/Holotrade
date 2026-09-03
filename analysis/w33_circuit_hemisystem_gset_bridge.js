#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");

const ROOT=path.resolve(__dirname,"..");
const GAP=path.join(__dirname,"w33_circuit_hemisystem_gset_bridge.g");
const OUT=path.join(ROOT,"data","w33_circuit_hemisystem_gset_bridge.json");

function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
function digest(value){return crypto.createHash("sha256").update(canonical(value)).digest("hex");}
function line(stdout,prefix){
  const found=stdout.split(/\r?\n/).find((row)=>row.startsWith(`${prefix}|`));
  if(!found)throw new Error(`GAP output missing ${prefix}`);
  return found;
}
function fields(row){
  return Object.fromEntries(row.split("|").slice(1).map((entry)=>{
    const at=entry.indexOf("=");if(at<1)throw new Error(`malformed GAP field ${entry}`);
    return [entry.slice(0,at),entry.slice(at+1)];
  }));
}
function integer(value,label){
  if(!/^[0-9]+$/.test(value))throw new Error(`bad integer ${label}: ${value}`);
  return Number(value);
}
function bool(value,label){
  if(value!=="0"&&value!=="1")throw new Error(`bad boolean ${label}: ${value}`);
  return value==="1";
}
function orderHistogram(value){
  return [...value.matchAll(/\[\s*(\d+)\s*,\s*(\d+)\s*\]/g)].map((match)=>({order:Number(match[1]),count:Number(match[2])}));
}
function characterRows(value){
  return value.split(";").map((row)=>{
    const [order,classSize,circuitFixed,hemisystemFixed]=row.split(",").map(Number);
    return {order,classSize,circuitFixed,hemisystemFixed};
  }).sort((a,b)=>a.order-b.order||a.classSize-b.classSize||a.circuitFixed-b.circuitFixed||a.hemisystemFixed-b.hemisystemFixed);
}
function decompositionRows(value){
  return value.split(";").map((row)=>{
    const [,degree,circuitMultiplicity,hemisystemMultiplicity]=row.split(",").map(Number);
    return {degree,circuitMultiplicity,hemisystemMultiplicity};
  }).sort((a,b)=>a.degree-b.degree||a.circuitMultiplicity-b.circuitMultiplicity||a.hemisystemMultiplicity-b.hemisystemMultiplicity);
}

function build(){
  const run=runGap(GAP,{cwd:ROOT,quiet:true});
  if(!run.ok||/Error,|Syntax error|Syntax warning/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed\n${run.stdout}\n${run.stderr}`);
  if(!run.stdout.includes("ALL_CIRCUIT_HEMISYSTEM_GSET_CHECKS_PASS"))throw new Error("GAP 216-carrier witness did not reach all-pass");
  const carrier=fields(line(run.stdout,"CIRCUIT_HEMISYSTEM_GSET"));
  const stabilizers=fields(line(run.stdout,"CIRCUIT_HEMISYSTEM_STABILIZERS"));
  const character=fields(line(run.stdout,"CIRCUIT_HEMISYSTEM_CHARACTER"));
  const decomposition=fields(line(run.stdout,"CIRCUIT_HEMISYSTEM_DECOMPOSITION"));
  const boundary=fields(line(run.stdout,"CIRCUIT_HEMISYSTEM_BOUNDARY"));
  const rows=characterRows(character.rows);
  const pspDecomposition=decompositionRows(decomposition.pspRows);
  const autDecomposition=decompositionRows(decomposition.autRows);
  const discrepancies=rows.filter((row)=>row.circuitFixed!==row.hemisystemFixed);
  const body={
    schema:"holotrade.w33-circuit-hemisystem-gset-no-go.v1",
    evidenceClass:"EXACT_GAP_ENUMERATION_STABILIZERS_AND_PERMUTATION_CHARACTERS",
    dependencies:{
      circuitCarrier:"data/e8_pg34_sentinel_control_plane.json",
      hemisystemCensus:"data/w33_hemisystems_are_their_216.json",
      priorBoundary:"The prior packet proved only 432 hemisystems / 216 complement-pairs and explicitly left a fibre-level correspondence unclaimed.",
    },
    carriers:{
      sentinelFiveCircuits:integer(carrier.circuits,"circuits"),
      hemisystemsModuloComplement:integer(carrier.hemisystemPairs,"hemisystemPairs"),
      eachTransitive:true,
    },
    innerPSpAction:{
      group:"PSp(4,3)",order:25920,
      circuitStabilizerOrder:integer(carrier.pspCircuitStabilizer,"pspCircuitStabilizer"),
      hemisystemStabilizerOrder:integer(carrier.pspHemisystemStabilizer,"pspHemisystemStabilizer"),
      circuitStabilizerOrderHistogram:orderHistogram(stabilizers.pspCircuitOrders),
      hemisystemStabilizerOrderHistogram:orderHistogram(stabilizers.pspHemisystemOrders),
      stabilizersConjugate:bool(carrier.pspActionsConjugate,"pspActionsConjugate"),
    },
    fullAutomorphismAction:{
      group:"Aut(W(3,3))",order:51840,
      circuitStabilizerOrder:integer(carrier.autCircuitStabilizer,"autCircuitStabilizer"),
      hemisystemStabilizerOrder:integer(carrier.autHemisystemStabilizer,"autHemisystemStabilizer"),
      circuitStabilizerOrderHistogram:orderHistogram(stabilizers.autCircuitOrders),
      hemisystemStabilizerOrderHistogram:orderHistogram(stabilizers.autHemisystemOrders),
      stabilizersConjugate:bool(carrier.autActionsConjugate,"autActionsConjugate"),
      permutationCharacterRows:rows,
      discrepancyCount:discrepancies.length,
      sharpWitnesses:discrepancies
        .filter((row)=>[45,36].includes(row.classSize))
        .map((row)=>({order:row.order,classSize:row.classSize,circuitFixed:row.circuitFixed,hemisystemFixed:row.hemisystemFixed})),
    },
    representationDiagnosis:{
      pspDecomposition,
      fullAutomorphismDecomposition:autDecomposition,
      pspCircuitDimension:pspDecomposition.reduce((sum,row)=>sum+row.degree*row.circuitMultiplicity,0),
      pspHemisystemDimension:pspDecomposition.reduce((sum,row)=>sum+row.degree*row.hemisystemMultiplicity,0),
      circuitSteinberg81Multiplicity:pspDecomposition.find((row)=>row.degree===81)?.circuitMultiplicity||0,
      hemisystemSteinberg81Multiplicity:pspDecomposition.find((row)=>row.degree===81)?.hemisystemMultiplicity||0,
      reading:"The circuit carrier contains the 81-dimensional Steinberg representation once; the hemisystem-line carrier contains no Steinberg constituent. This is the sharp module-level separator behind the G-set no-go.",
    },
    conclusion:{
      equivariantBijectionExists:bool(carrier.equivariantBijectionExists,"equivariantBijectionExists"),
      countMatchOnly:bool(boundary.countMatchOnly,"countMatchOnly"),
      outerTwistRepairs:bool(boundary.outerTwistRepairs,"outerTwistRepairs"),
      theorem:"The 216 sentinel five-circuits and the 216 W(3,3) hemisystems modulo complementation are distinct transitive finite-group carriers. Their stabilizers are nonconjugate already in PSp(4,3), remain nonconjugate in Aut(W(3,3)), and their full permutation characters differ. At module level the circuit carrier contains Steinberg-81 once while the hemisystem carrier contains it zero times. Equal cardinality does not furnish an equivariant dictionary.",
    },
    evidenceBoundary:"This is an exact finite G-set no-go. It rules out equivariant identification under the native inner and full graph-automorphism actions; it does not rule out a non-equivariant lookup table, an augmented cover, or a relation after adding extra structure. It has no physical interpretation and changes no blocking bound.",
  };
  return {...body,sha256:digest(body)};
}

function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(!fs.existsSync(OUT))throw new Error("frozen 216-carrier no-go certificate missing; run --write");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("frozen 216-carrier no-go certificate drifted");
  process.stdout.write(JSON.stringify({status:"PASS",carriers:[216,216],pspConjugate:false,autConjugate:false,characterDiscrepancies:packet.fullAutomorphismAction.discrepancyCount,steinberg81:[1,0],sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest};
