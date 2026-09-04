#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");
const fiveFront=require("./w33_five_front_breakthrough.js");

const ROOT=path.resolve(__dirname,"..");
const GAP_FILE=path.join(__dirname,"w33_f20_qutrit_block_bridge.g");
const FIBRE_GAP=path.join(__dirname,"w33_steinberg_doublecoset_colour_swap.g");
const OUT=path.join(ROOT,"data","w33_f20_qutrit_block_bridge.json");
const RTL=path.join(ROOT,"rtl","w33_f20_qutrit_block_router.v");

function shaFile(file){return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");}
function markerRow(stdout,marker){
  const at=stdout.indexOf(`${marker}|`);
  if(at<0)throw new Error(`GAP output missed ${marker}`);
  return stdout.slice(at).replace(/\\\r?\n/g,"").replace(/\r?\n[ \t]*/g,"").trim();
}
function fields(row){
  return Object.fromEntries(row.split("|").slice(1).map((entry)=>{
    const at=entry.indexOf("=");
    if(at<1)throw new Error(`malformed GAP field ${entry}`);
    return [entry.slice(0,at),entry.slice(at+1)];
  }));
}
function ints(value){return value.split(",").map(Number);}
function bool(value){return value==="true"||value==="1";}
function matrix(value,n){
  const flat=ints(value);
  if(flat.length!==n*n)throw new Error(`expected ${n*n} matrix entries, got ${flat.length}`);
  return Array.from({length:n},(_,i)=>flat.slice(i*n,(i+1)*n));
}
function matrices(value,n){return value.split("/").map((part)=>matrix(part,n));}
function det2(m){return ((m[0][0]*m[1][1]-m[0][1]*m[1][0])%3+3)%3;}
function assertPermutation(p,n,label){
  if(p.length!==n||new Set(p).size!==n||Math.min(...p)!==0||Math.max(...p)!==n-1)throw new Error(`${label} is not a degree-${n} permutation`);
}
function inverse(p){const q=Array(p.length);p.forEach((v,i)=>{q[v]=i;});return q;}
function compose(a,b){return a.map((x)=>b[x]);}
function power(p,n){let out=p.map((_,i)=>i);for(let i=0;i<n;i++)out=compose(out,p);return out;}

function build(){
  const five=fiveFront.build();
  const run=runGap(GAP_FILE,{cwd:ROOT,quiet:true,timeout:600000,maxBuffer:16*1024*1024});
  if(!run.ok||/Error,|Syntax error|Syntax warning/.test(run.stdout+run.stderr))throw new Error(`F20 qutrit GAP witness failed\n${run.stdout}\n${run.stderr}`);
  const q=fields(markerRow(run.stdout,"F20_QUTRIT_BLOCK"));
  const localMatrices=matrices(q.multiplierTwoLocalMatrices,2);
  const inverseLocalMatrices=matrices(q.multiplierTwoInverseLocalMatrices,2);
  const fibre=five.fibreProduct;
  const qPermutation=ints(q.multiplierTwoPermutation).map((x)=>x-1);
  const qInversePermutation=ints(q.multiplierTwoInversePermutation).map((x)=>x-1);
  const physicalTranslation=ints(q.physicalTranslationAction).map((x)=>x-1);
  const physicalMultiplier=ints(q.physicalMultiplierAction).map((x)=>x-1);
  assertPermutation(qPermutation,5,"multiplier-two");
  assertPermutation(qInversePermutation,5,"inverse multiplier-two");
  assertPermutation(fibre.presentation.order5GeneratorOnW33Points,40,"fibre order-five generator");
  assertPermutation(fibre.presentation.order4GeneratorOnW33Points,40,"fibre order-four generator");
  assertPermutation(physicalTranslation,40,"physical translation");
  assertPermutation(physicalMultiplier,40,"physical multiplier");
  const identity=physicalTranslation.map((_,i)=>i);
  const physicalConjugate=compose(compose(inverse(physicalMultiplier),physicalTranslation),physicalMultiplier);

  const checks={
    cyclicCodeDimension:Number(q.codeDimension)===4,
    bareCoordinateGroupIsD10:Number(q.plainPermutationOrder)===10&&q.plainPermutationStructure==="D10",
    localCliffordCoordinateGroupIsF20:Number(q.localCliffordCoordinateOrder)===20&&q.localCliffordCoordinateStructure==="C5 : C4"&&bool(q.F20Realized),
    missingMultiplierRequiresClifford:!bool(q.multiplierTwoPlain)&&bool(q.multiplierTwoLocalClifford),
    allLocalMapsAreSymplectic:[...localMatrices,...inverseLocalMatrices].every((m)=>det2(m)===1),
    physicalLiftPreservesCode:bool(q.liftPreservesCode),
    physicalLiftPreservesPauliForm:bool(q.liftIsSymplectic),
    physicalGeneratorOrders:ints(q.liftOrders).slice(0,2).join(",")==="5,4",
    commonF20Presentation:fibre.presentation.generatorOrders.join(",")==="5,4"&&Number(q.physicalPresentationExponent)===fibre.presentation.conjugationExponent,
    faithfulFortyStateAction:Number(q.physicalPauliDegree)===40&&Number(q.physicalPauliGroupOrder)===20&&ints(q.physicalPauliGeneratorOrders).join(",")==="5,4",
    transitionTablesSatisfyPresentation:power(physicalTranslation,5).join(",")===identity.join(",")&&power(physicalMultiplier,4).join(",")===identity.join(",")&&physicalConjugate.join(",")===power(physicalTranslation,3).join(","),
  };
  if(!Object.values(checks).every(Boolean))throw new Error(`F20 qutrit bridge check failed: ${JSON.stringify(checks)}`);

  const body={
    schema:"holotrade.w33-f20-qutrit-block-bridge.v1",
    status:"PASS",
    evidenceClass:"EXACT_GAP_STABILIZER_AND_LOCAL_CLIFFORD_ISOMORPHISM",
    corpusPriorArt:{
      fibreProduct:"HoloTrade 58f0df3 owns the 1,296-state 216 x_36 216 fibre product and its F20 point stabilizer.",
      qutritBlock:"W33-Theory w33_pass79_full_closure.py owns the cyclic [[5,1,3]]_3 block generated by X Z Z^-1 X^-1 I.",
      storageStack:"W33-Theory 94cf718a0 and df284a029 own the corrected singular-K12 [[66,8,3]]_3 storage construction and the no-go for a bare logical recode.",
      addedHere:"Computes the five-site permutation image as D10, the local-Clifford coordinate image as F20, and an explicit presentation-matched isomorphism from the fibre-product stabilizer into physical qutrit Pauli-space code automorphisms.",
    },
    fibreProductF20:{
      carrierStates:fibre.states,
      stabilizerOrder:fibre.stabilizerOrder,
      stabilizerType:fibre.stabilizerType,
      generatorOrders:fibre.presentation.generatorOrders,
      conjugationExponent:fibre.presentation.conjugationExponent,
      order5GeneratorOnW33Points:fibre.presentation.order5GeneratorOnW33Points,
      order4GeneratorOnW33Points:fibre.presentation.order4GeneratorOnW33Points,
    },
    cyclicQutritBlock:{
      parameters:"[[5,1,3]]_3",
      stabilizerDimension:Number(q.codeDimension),
      plainPermutationImage:{order:Number(q.plainPermutationOrder),structure:q.plainPermutationStructure},
      localCliffordCoordinateImage:{order:Number(q.localCliffordCoordinateOrder),structure:q.localCliffordCoordinateStructure},
      translationOrder:ints(q.presentationOrders)[0],
      multiplierOrder:ints(q.presentationOrders)[1],
      multiplierCoordinatePermutation:qPermutation,
      multiplierRowBasisChange:matrix(q.multiplierTwoRowChange,4),
      multiplierLocalCliffords:localMatrices,
      physicalConjugationExponent:Number(q.physicalPresentationExponent),
      physicalLiftOrders:ints(q.liftOrders),
      addressedPauliAction:{
        degree:Number(q.physicalPauliDegree),
        groupOrder:Number(q.physicalPauliGroupOrder),
        translation:physicalTranslation,
        multiplier:physicalMultiplier,
      },
    },
    explicitIsomorphism:{
      source:"Stab_PSp(fibre-product state) = <a,b | a^5=b^4=1, a^b=a^3>",
      target:"Local-Clifford automorphisms of the cyclic five-qutrit block generated by the cyclic shift T and physical multiplier lift M, with T^M=T^3",
      generatorMap:{a:"T",b:"M"},
      interpretation:"The fibre-product router stabilizer has a native, presentation-matched action on one protected five-qutrit block. The order-four affine multiplier is invisible to bare coordinate permutations and is restored exactly by sitewise qutrit Clifford compensation.",
    },
    checks,
    sourceHashes:{
      fibreGap:`sha256:${shaFile(FIBRE_GAP)}`,
      qutritGap:`sha256:${shaFile(GAP_FILE)}`,
    },
    boundary:"This is an exact finite stabilizer-code automorphism and router-control interface. It does not identify the 1,296 fibre-product states with qutrit codewords, does not make the nonlocal 20-to-240 embedding local, and does not close the physical calibration, threshold, or fault-tolerant recode gates.",
  };
  return {...body,sha256:crypto.createHash("sha256").update(fiveFront.canonical(body)).digest("hex")};
}

function caseFunction(name,table){
  const rows=[`function [5:0] ${name};`,`  input [5:0] state;`,`  begin ${name}=6'h3f; case(state)`];
  table.forEach((v,i)=>rows.push(`    6'd${i}: ${name}=6'd${v};`));
  rows.push("    default: ; endcase end","endfunction");
  return rows.join("\n");
}
function renderRTL(packet){
  const t=packet.cyclicQutritBlock.addressedPauliAction.translation;
  const m=packet.cyclicQutritBlock.addressedPauliAction.multiplier;
  const mi=inverse(m);
  return `// Generated from data/w33_f20_qutrit_block_bridge.json.\n// F20 acts on five sites x eight nonidentity qutrit Paulis.\nmodule w33_f20_qutrit_block_router(input wire opcode, input wire [5:0] state, output reg valid, output reg [5:0] next_state);\n${caseFunction("step_t",t)}\n${caseFunction("step_m",m)}\nalways @* begin valid=(state<6'd40); next_state=6'h3f; if(valid) next_state=opcode?step_m(state):step_t(state); end\nendmodule\n\nmodule w33_f20_qutrit_block_router_formal(input wire [5:0] state);\n${caseFunction("step_t",t)}\n${caseFunction("step_m",m)}\n${caseFunction("step_mi",mi)}\nwire [5:0] t5=step_t(step_t(step_t(step_t(step_t(state)))));\nwire [5:0] m4=step_m(step_m(step_m(step_m(state))));\nwire [5:0] conj=step_m(step_t(step_mi(state)));\nwire [5:0] t3=step_t(step_t(step_t(state)));\nalways @* if(state<6'd40) begin assert(t5==state); assert(m4==state); assert(conj==t3); assert(step_t(state)<6'd40); assert(step_m(state)<6'd40); end\nendmodule\n\nmodule w33_f20_qutrit_block_router_control(input wire [5:0] state);\n${caseFunction("step_m",m)}\nwire [5:0] missing_clifford_multiplier=state;\nalways @* if(state<6'd40) assert(missing_clifford_multiplier==step_m(state));\nendmodule\n`;
}

function main(){
  const packet=build();
  const rtl=renderRTL(packet);
  if(process.argv.includes("--write")){
    fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
    fs.writeFileSync(RTL,rtl);
  }else{
    if(fiveFront.canonical(packet)!==fiveFront.canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("F20 qutrit bridge certificate drifted");
    if(rtl!==fs.readFileSync(RTL,"utf8"))throw new Error("F20 qutrit router RTL drifted");
  }
  process.stdout.write(JSON.stringify({status:packet.status,plain:packet.cyclicQutritBlock.plainPermutationImage.structure,localClifford:packet.cyclicQutritBlock.localCliffordCoordinateImage.structure,presentation:packet.fibreProductF20.conjugationExponent,sha256:packet.sha256})+"\n");
}

if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,renderRTL};
