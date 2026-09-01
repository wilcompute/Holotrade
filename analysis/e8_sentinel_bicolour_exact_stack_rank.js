#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");
const sentinel=require("../data/e8_pg34_sentinel_control_plane.json");

const ROOT=path.resolve(__dirname,"..");
const GAP=path.join(__dirname,"e8_sentinel_bicolour_exact_stack_rank.g");
const OUT=path.join(ROOT,"data","e8_sentinel_bicolour_exact_stack_rank.json");

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

function build(){
  const run=runGap(GAP,{cwd:ROOT,quiet:true});
  if(!run.ok||/Error,|Syntax error/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed\n${run.stdout}\n${run.stderr}`);
  if(!run.stdout.includes("ALL_SENTINEL_BICOLOUR_EXACT_STACK_RANK_CHECKS_PASS"))throw new Error("GAP bicolour witness did not reach all-pass");
  const rank=fields(line(run.stdout,"BICOLOUR_EXACT_RANK"));
  const common=fields(line(run.stdout,"BICOLOUR_EXACT_COMMON"));
  const circuit=fields(line(run.stdout,"BICOLOUR_CIRCUIT_BRIDGE"));
  const boundary=fields(line(run.stdout,"BICOLOUR_EXACT_BOUNDARY"));
  const intersections=common.sectorIntersections.split(",").map((value)=>integer(value,"sector intersection"));
  const circuitScalars=circuit.gramScalars.split(",").map((value)=>integer(value,"circuit Gram scalar"));
  const circuitIntersections=circuit.sectorIntersections.split(",").map((value)=>integer(value,"circuit sector intersection"));
  const body={
    schema:"holotrade.e8-sentinel-bicolour-exact-stack-rank.v1",
    evidenceClass:"EXACT_GAP_CHARACTERISTIC_ZERO_ROW_SPACE_RECONSTRUCTION",
    source:{
      sentinelCertificateSha256:sentinel.sha256,
      companionRepository:"W33-Theory",
      companionInputs:["c6170fa8e","609a42c77837b4be047182ab77812958e03314f7","4c9a51597"],
      repair:"The earlier 372 calculation used rank modulo 1000003, which is only a lower bound for rational rank. This witness computes the rational rank and intersections directly in GAP.",
    },
    incidence:{
      fiveCircuits:216,
      sixCircuits:540,
      maximalOverlap:"|C5 intersection C6| = 3",
      uncolouredDegrees:[20,8],
      colourOrbitSizes:[2160,2160],
      eachColourDegrees:[10,4],
    },
    rationalRowSpaces:{
      rankMplus:integer(rank.rankPlus,"rankPlus"),
      rankMminus:integer(rank.rankMinus,"rankMinus"),
      stackedRank:integer(rank.stackRankQ,"stackRankQ"),
      commonDimension:integer(rank.commonDimensionQ,"commonDimensionQ"),
      characteristic:"Q",
    },
    jointSectorResolution:{
      separatorEigenvalues:[-58,-22,-18,8,14,62,170],
      sectorDimensions:[15,15,81,20,60,24,1],
      directCommonIntersections:intersections,
      doubledFifteenIsotypicCommonDimension:integer(common.doubled15IsotypicIntersection,"doubled15IsotypicIntersection"),
      exactCommonDecomposition:common.decomposition,
      equalsSymmetricSixtySector:bool(boundary.commonIsSymmetric60Sector,"commonIsSymmetric60Sector"),
      reading:"The common colour row space contains the complete 1-, 20-, and 24-dimensional sectors plus one diagonal 15-dimensional copy inside the doubled 15-isotypic component; it has zero intersection with the symmetric 60-sector.",
    },
    circuitCarrierBridge:{
      circuitIncidenceShape:[216,45],
      circuitCarrierDimension:integer(circuit.circuitDimension,"circuitDimension"),
      gramScalarsByJointSector:circuitScalars,
      directSectorIntersections:circuitIntersections,
      moduleShape:circuit.circuitCarrier,
      plusTransportedIntoCommon:integer(circuit.plusTransportedIntoCommon,"plusTransportedIntoCommon"),
      minusTransportedIntoCommon:integer(circuit.minusTransportedIntoCommon,"minusTransportedIntoCommon"),
      plusMinusImagesEqual:bool(circuit.plusMinusImagesEqual,"plusMinusImagesEqual"),
      commonComplementDimension:integer(circuit.commonComplement,"commonComplement"),
      exactSplit:"common60 = common circuit image(1+20+24) direct-sum diagonal15",
      reading:"The two colours transport the canonical five-circuit carrier to exactly the same 45-dimensional subspace. The entire distinction left inside their common 60-space is the complementary diagonal 15.",
    },
    proofBoundary:{
      modularRankUsedAsProof:bool(boundary.modularRankUsedAsProof,"modularRankUsedAsProof"),
      characteristicZeroRankComputed:bool(boundary.characteristicZeroRankComputed,"characteristicZeroRankComputed"),
    },
    theorem:"The two 216x540 colour-incidence matrices have rational row rank 216, stacked rational rank 372, and a 60-dimensional common row space. Their M+ and M- images of the canonical 45-dimensional five-circuit carrier coincide exactly as the 1+20+24 summand, leaving the diagonal 15 as the complementary common residue.",
    evidenceBoundary:"This is an exact finite circuit-incidence and rational-module theorem. It does not identify optical modes, physical qubits, hardware channels, host identities, cryptographic authority, or dispatch bindings.",
  };
  return {...body,sha256:digest(body)};
}

function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(!fs.existsSync(OUT))throw new Error("frozen exact bicolour stack certificate missing; run --write");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("frozen exact bicolour stack certificate drifted");
  process.stdout.write(JSON.stringify({status:"PASS",stackRank:372,common:60,circuitCommon:45,residual:15,decomposition:"1+15+20+24",sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest};
