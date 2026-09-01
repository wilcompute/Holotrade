#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");
const homology=require("../data/e8_unitary_homology_code_w33_obstruction.json");
const sentinel=require("../data/e8_pg34_sentinel_control_plane.json");

const ROOT=path.resolve(__dirname,"..");
const GAP=path.join(__dirname,"e8_unitary_homology_sentinel_bridge.g");
const OUT=path.join(ROOT,"data","e8_unitary_homology_sentinel_bridge.json");

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
function list(value,label){
  if(!/^\[.*\]$/.test(value))throw new Error(`bad list ${label}: ${value}`);
  const entries=value.match(/-?\d+/g)||[];
  return entries.map(Number);
}
function bool(value,label){
  if(value!=="0"&&value!=="1")throw new Error(`bad boolean ${label}: ${value}`);
  return value==="1";
}

function build(){
  const run=runGap(GAP,{cwd:ROOT,quiet:true});
  if(!run.ok||/Error,|Syntax error/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed\n${run.stdout}\n${run.stderr}`);
  if(!run.stdout.includes("ALL_UNITARY_HOMOLOGY_SENTINEL_BRIDGE_CHECKS_PASS"))throw new Error("GAP bridge did not reach its all-pass sentinel");
  const dims=fields(line(run.stdout,"SENTINEL_BRIDGE_DIMS"));
  const factors=fields(line(run.stdout,"SENTINEL_BRIDGE_FACTORS"));
  const iso=fields(line(run.stdout,"SENTINEL_BRIDGE_ISO"));
  const hom=fields(line(run.stdout,"SENTINEL_BRIDGE_HOM"));
  const universal=fields(line(run.stdout,"SENTINEL_BRIDGE_UNIVERSAL"));

  const body={
    schema:"holotrade.e8-unitary-homology-sentinel-bridge.v1",
    evidenceClass:"EXACT_GAP_MEATAXE_NORMAL_SUBGROUP_FACTORIZATION",
    carriers:{
      logicalHomology:{dimension:40,definition:"ker(A)/im(A) for the 120-state characteristic-two adjacency differential",sourceSha256:homology.sha256},
      normalTwoCore:{structure:"C2^5",order:32},
      w33Sentinel:{parameters:"[40,15,8]_2",minimumSupports:integer(dims.supports,"supports"),sourceSha256:sentinel.sha256},
    },
    normalSubgroupReduction:{
      relationRank:integer(dims.relations,"relations"),
      coinvariantDimension:integer(dims.coinvariants,"coinvariants"),
      fixedDimension:integer(dims.fixed,"fixed"),
      sentinelDimension:integer(dims.sentinel,"sentinel"),
      compositionFactors:{
        coinvariants:list(factors.coinvariants,"coinvariants factors"),
        fixed:list(factors.fixed,"fixed factors"),
        sentinelInner:list(factors.sentinelInner,"sentinel inner factors"),
        sentinelOuter:list(factors.sentinelOuter,"sentinel outer factors"),
      },
      pairwiseIsomorphisms:{
        coinvariantsToSentinelInner:bool(iso.coinvariantInner,"coinvariantInner"),
        coinvariantsToSentinelOuter:bool(iso.coinvariantOuter,"coinvariantOuter"),
        fixedToSentinelInner:bool(iso.fixedInner,"fixedInner"),
        fixedToSentinelOuter:bool(iso.fixedOuter,"fixedOuter"),
        fixedToCoinvariants:bool(iso.fixedCoinvariant,"fixedCoinvariant"),
        sentinelInnerToOuter:bool(iso.sentinelInnerOuter,"sentinelInnerOuter"),
      },
      reading:"Dimension and Jordan-Holder factors coincide, but the four modules are pairwise separated by modular extension data; no two are isomorphic.",
    },
    exhaustiveHomRanks:{
      coinvariantsToSentinelInner:{dimension:integer(hom.coinvariantToInnerDim,"coinvariantToInnerDim"),nonzeroRanks:list(hom.coinvariantToInnerRanks,"coinvariantToInnerRanks")},
      sentinelInnerToCoinvariants:{dimension:integer(hom.innerToCoinvariantDim,"innerToCoinvariantDim"),nonzeroRanks:list(hom.innerToCoinvariantRanks,"innerToCoinvariantRanks")},
      coinvariantsToSentinelOuter:{dimension:integer(hom.coinvariantToOuterDim,"coinvariantToOuterDim"),nonzeroRanks:list(hom.coinvariantToOuterRanks,"coinvariantToOuterRanks")},
      sentinelOuterToCoinvariants:{dimension:integer(hom.outerToCoinvariantDim,"outerToCoinvariantDim"),nonzeroRanks:list(hom.outerToCoinvariantRanks,"outerToCoinvariantRanks")},
      fixedToCoinvariants:{dimension:integer(hom.fixedToCoinvariantDim,"fixedToCoinvariantDim"),nonzeroRanks:list(hom.fixedToCoinvariantRanks,"fixedToCoinvariantRanks")},
      coinvariantsToFixed:{dimension:integer(hom.coinvariantToFixedDim,"coinvariantToFixedDim"),nonzeroRanks:list(hom.coinvariantToFixedRanks,"coinvariantToFixedRanks")},
    },
    universalW33Shadow:{
      innerIdentification:{
        forwardHomDimension:integer(universal.innerForwardHomDim,"innerForwardHomDim"),
        spanOfAllForwardImages:integer(universal.innerUniversalImageRank,"innerUniversalImageRank"),
        everyForwardImageInsideSentinel:bool(universal.innerImageInSentinel,"innerImageInSentinel"),
        backwardHomDimension:integer(universal.innerBackwardHomDim,"innerBackwardHomDim"),
        spanOfAllBackwardImages:integer(universal.innerBackwardUniversalImageRank,"innerBackwardUniversalImageRank"),
      },
      outerIdentification:{
        forwardHomDimension:integer(universal.outerForwardHomDim,"outerForwardHomDim"),
        spanOfAllForwardImages:integer(universal.outerUniversalImageRank,"outerUniversalImageRank"),
        everyForwardImageInsideSentinel:bool(universal.outerImageInSentinel,"outerImageInSentinel"),
        backwardHomDimension:integer(universal.outerBackwardHomDim,"outerBackwardHomDim"),
        spanOfAllBackwardImages:integer(universal.outerBackwardUniversalImageRank,"outerBackwardUniversalImageRank"),
      },
      everyForwardMapKillsTwoCoreRelations:bool(universal.forwardKillsO2Relations,"forwardKillsO2Relations"),
      everyBackwardImageInsideFixedHomology:bool(universal.backwardImagesInFixed,"backwardImagesInFixed"),
      theorem:"For both S6 identification classes, every equivariant map from 120-state logical homology to the genuine 40-point W33 carrier factors through the 15-dimensional C2^5 coinvariant quotient and lands inside the explicit [40,15,8] sentinel code. Every reverse equivariant map lands inside the 15-dimensional C2^5-fixed homology.",
    },
    evidenceBoundary:"The sentinel is a universal finite-module receptacle for W33-compatible shadows, not an isomorphic relabeling of logical homology. The maps are low-rank, no preferred nonzero map is selected, and no physical qubit, decoder, host identity, cryptographic authority, or dispatch binding is supplied.",
  };
  return {...body,sha256:digest(body)};
}

function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(!fs.existsSync(OUT))throw new Error("frozen homology/sentinel bridge missing; run --write");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("frozen homology/sentinel bridge drifted");
  process.stdout.write(JSON.stringify({status:"PASS",dimensions:[40,15,15],innerImage:11,outerImage:6,sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest};
