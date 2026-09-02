#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");

const ROOT=path.resolve(__dirname,"..");
const MAIN_GAP=path.join(__dirname,"w33_steinberg_doublecoset_colour_swap.g");
const DEFECT_GAP=path.join(__dirname,"w33_tau111_defect_aware_trichotomy.g");
const OUT=path.join(ROOT,"data","w33_five_front_breakthrough.json");
const RTL=path.join(ROOT,"rtl","w33_dual_carrier_router.v");

function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
function digest(value){return crypto.createHash("sha256").update(canonical(value)).digest("hex");}
function gap(file,marker){
  const run=runGap(file,{cwd:ROOT,quiet:true,timeout:600000,maxBuffer:96*1024*1024});
  if(!run.ok||/Error,|Syntax error|Syntax warning/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed: ${path.basename(file)}\n${run.stdout}\n${run.stderr}`);
  if(!run.stdout.includes(marker))throw new Error(`GAP witness missed ${marker}`);
  return run.stdout;
}
function line(stdout,prefix){
  const found=stdout.split(/\r?\n/).find((row)=>row.startsWith(`${prefix}|`));
  if(!found)throw new Error(`missing GAP row ${prefix}`);
  return found;
}
function section(stdout,start,end){
  const a=stdout.indexOf(`${start}|`);
  const b=stdout.indexOf(`${end}|`,a);
  if(a<0||b<0)throw new Error(`missing GAP section ${start}..${end}`);
  return stdout.slice(a,b).replace(/\\\r?\n/g,"").replace(/\r?\n/g,"");
}
function fields(row){
  return Object.fromEntries(row.split("|").slice(1).map((entry)=>{
    const at=entry.indexOf("=");
    if(at<1)throw new Error(`malformed field ${entry}`);
    return [entry.slice(0,at),entry.slice(at+1)];
  }));
}
function ints(value){return value===""?[]:value.split(",").map(Number);}
function maps(value){return value.split("/").map((row)=>ints(row).map((x)=>x-1));}
function pair(value){return ints(value);}
function matrix(value){return value.split(";").map((row)=>row.split(","));}
function assertPermutation(p,n,label){
  if(p.length!==n||new Set(p).size!==n||Math.min(...p)!==0||Math.max(...p)!==n-1)throw new Error(`${label} is not degree ${n}`);
}

function build(){
  const main=gap(MAIN_GAP,"ALL_STEINBERG_DOUBLECOSET_COLOUR_SWAP_CHECKS_PASS");
  const defect=gap(DEFECT_GAP,"ALL_TAU111_DEFECT_AWARE_TRICHOTOMY_CHECKS_PASS");
  const st=fields(line(main,"STEINBERG_1080_TO_216"));
  const projector=fields(line(main,"STEINBERG_PROJECTOR"));
  const dc=fields(line(main,"TWO_S5_DOUBLE_COSETS"));
  const swap=fields(line(main,"COLOUR_SWAP"));
  const fibreProduct=fields(line(main,"FIBRE_PRODUCT_BUILDINGS"));
  const actions=fields(section(main,"MICROVM_ACTIONS","FIVE_FRONT_BOUNDARY"));
  const pencils=fields(line(defect,"TAU111_DELETED_PENCILS"));
  const closure=fields(line(defect,"TAU111_RECIPROCAL_CLOSURE"));
  const inequality=fields(line(defect,"TAU111_TRIPLE_INEQUALITY"));
  const defectBoundary=fields(line(defect,"TAU111_BOUNDARY"));

  const circuitGenerators=maps(actions.circuitGenerators);
  const hemisystemGenerators=maps(actions.hemiGenerators);
  const quotientGenerators=maps(actions.quotientGenerators);
  const circuitBlockIds=ints(actions.circuitBlockIds).map((x)=>x-1);
  const hemisystemBlockIds=ints(actions.hemiBlockIds).map((x)=>x-1);
  const generatorCount=Number(actions.generatorCount);
  if(circuitGenerators.length!==generatorCount||hemisystemGenerators.length!==generatorCount||quotientGenerators.length!==generatorCount)throw new Error("generator count drift");
  circuitGenerators.forEach((p,i)=>assertPermutation(p,216,`circuit generator ${i}`));
  hemisystemGenerators.forEach((p,i)=>assertPermutation(p,216,`hemisystem generator ${i}`));
  quotientGenerators.forEach((p,i)=>assertPermutation(p,36,`quotient generator ${i}`));
  for(let g=0;g<generatorCount;g++)for(let x=0;x<216;x++){
    if(circuitBlockIds[circuitGenerators[g][x]]!==quotientGenerators[g][circuitBlockIds[x]])throw new Error("circuit quotient equivariance drift");
    if(hemisystemBlockIds[hemisystemGenerators[g][x]]!==quotientGenerators[g][hemisystemBlockIds[x]])throw new Error(`pair-carrier quotient equivariance drift at generator ${g}, state ${x}: ${hemisystemBlockIds[hemisystemGenerators[g][x]]} != ${quotientGenerators[g][hemisystemBlockIds[x]]}`);
  }

  const body={
    schema:"holotrade.w33-five-front-breakthrough.v2",
    evidenceClass:"EXACT_GAP_ACTIONS_RATIONAL_PROJECTORS_AND_FORMAL_RTL_INPUTS",
    corpusPriorArt:{
      singleGeneratorTypeProof:"HoloTrade 8f2921e proves one circuit-carrier generator preserves the canonical six-fibration in RTL.",
      heterogeneousSoftwareABI:"W33-Theory 0bdbb5422 implements SEND36/RECV36/ACK36 over the common base without carrier translation.",
      typedUniversalVM:"W33-Theory 5cb07b570 implements typed two-counter VM semantics with immutable carrier identity.",
      buildingHomology:"W33-Theory 89e39e849 identifies the 81 and 64 modules as the two building H1 representations and gives obstruction multiplicities 3+3.",
      addedHere:"Corrects the HoloTrade obstruction from points to lines, proves the F20 fibre product has the same 3+3 building block, freezes the 18-dimensional cross-Hom count, and compiles both exact generator pairs into a quotient-only formal RTL router.",
    },
    steinbergIntertwiner:{
      sourceCarrier:Number(st.source),targetCarrier:Number(st.target),sourceStabilizerOrder:Number(st.sourceStabilizer),
      sourceFactorization:st.sourceFactorization,
      orbitCount:Number(st.homOrbitCount),orbitSizes:ints(st.orbitSizes),rank:Number(st.steinbergHomRank),
      basisOrbitIndices:ints(st.basisIndices),basisOrbitSizes:ints(st.basisOrbitSizes),basisGram:matrix(st.basisGram),
      projector:{degree:Number(projector.degree),characterValueDistribution:projector.characterValueDistribution,rank:Number(projector.rank),idempotent:projector.idempotent==="1"},
      theorem:"Three explicit orbit-incidence relations form a basis of Hom_PSp(St_81^3,St_81). The displayed positive Gram matrix certifies independence and makes the 1080-to-216 Steinberg bridge constructive.",
    },
    twoS5Correspondence:{
      doubleCosets:Number(dc.count),valencies:ints(dc.valencies),ranks:ints(dc.ranks),steinbergRanks:ints(dc.steinbergRanks),
      minimumRelation:{index:Number(dc.optimalIndex),valency:Number(dc.optimalValency),gramFactors:dc.optimalGramFactors,components:Number(dc.components),component:dc.component,quotientDegree:Number(dc.quotientDegree),quotientStabilizerOrder:Number(dc.quotientStabilizerOrder),quotientStabilizerType:dc.quotientStabilizerType},
      theorem:"The two nonconjugate 216-actions share a canonical degree-36 quotient. Their minimum cross relation is exactly 36 disjoint K(6,6) components. Every equivariant cross relation annihilates circuit Steinberg-81.",
    },
    colourSwap:{
      outerOrder:Number(swap.outerOrder),exchangesColours:swap.exchangesColours==="1",commonParity:pair(swap.commonParity),circuitParity:pair(swap.circuitParity),residual15Parity:pair(swap.residual15Parity),
      theorem:"An outer involution exchanges the two bicolour incidence matrices. On common60 its parity is 34+26; on circuit45 it is 26+19; hence the residual diagonal15 has the nontrivial split 8+7 and is not a scalar-parity line.",
    },
    fibreProduct:{
      states:Number(fibreProduct.degree),stabilizerOrder:Number(fibreProduct.stabilizerOrder),
      stabilizerType:fibreProduct.stabilizerType,
      building81Multiplicity:Number(fibreProduct.building81Multiplicity),
      building64Multiplicity:Number(fibreProduct.building64Multiplicity),
      obstruction81Multiplicity:Number(fibreProduct.obstruction81Multiplicity),
      obstruction64Multiplicity:Number(fibreProduct.obstruction64Multiplicity),
      commonBuildingDimension:Number(fibreProduct.commonBuildingDimension),
      buildingCrossHomDimension:Number(fibreProduct.buildingCrossHomDimension),
      abstractIsotypicIsomorphism:fibreProduct.abstractIsotypicIsomorphism==="1",
      explicitIntertwinerBuilt:fibreProduct.explicitIntertwinerBuilt==="1",
      seesBoth:fibreProduct.seesBoth==="1",
      theorem:"The canonical fibre product of the two inequivalent 216-state carriers is a transitive 1,296-state G/F20 carrier. Its building block is 3*81 + 3*64 = 435, exactly matching the 1,080-state obstruction carrier, so the two 435-dimensional isotypic components are abstractly G-isomorphic and their equivariant cross-Hom has dimension 18.",
    },
    tau111Defect:{
      cleanRows:Number(pencils.cleanRows),cleanColumns:Number(pencils.cleanColumns),deletedPencilDegreeProfile:pencils.degreeProfile,
      tripleAddresses:Number(closure.tripleAddresses),fullAddresses:Number(closure.fullAddresses),degreeMismatchAddressesKilled:Number(closure.degreeMismatchAddressesKilled),
      inequality:inequality.formula,maximumTripleFibres:Number(inequality.maximumTripleFibres),maximumPairedTriples:Number(inequality.maximumPairedTriples),maximumSinkTriples:Number(inequality.maximumSinkTriples),elevenTripleWitnessPatternExcluded:inequality.elevenTripleWitnessPatternExcluded==="1",
      remainingIntegerProfiles:Number(defectBoundary.profilesRemain),raisesLowerBound:defectBoundary.raisesLowerBound==="1",interval:pair(defectBoundary.interval),
      theorem:"At 111, reciprocal closure replaces the false {0,1,4} rule: every non-sink repeated fibre is a complete deleted-pencil fibre of matching degree 3 or 4. The occupancy inequality limits triple fibres to ten, excluding descent of the 115 witness's eleven-triple pattern but not all 111 configurations.",
    },
    microvm:{
      statesPerCarrier:216,carrierTypes:["sentinel-circuit","complementary-hemisystem-pair"],generatorCount,
      quotientStates:36,fibreSize:6,circuitGenerators,hemisystemGenerators,quotientGenerators,circuitBlockIds,hemisystemBlockIds,
      adapterContract:"Cross-carrier adaptation returns only the common 36-state quotient. It never fabricates a forbidden 216-to-216 bijection.",
    },
    boundary:"All bridges are exact finite incidence, group-representation, and logic statements. The micro-VM is a verified finite controller, not evidence of physical particles, fields, spacetime, or quantum hardware. tau_2 remains in [111,115].",
  };
  return {...body,sha256:digest(body)};
}

function verilogCase(name,widthIn,widthOut,tables){
  const lines=[];
  lines.push(`function [${widthOut-1}:0] ${name};`);
  lines.push(`  input [0:0] carrier; input [1:0] opcode; input [${widthIn-1}:0] state;`);
  lines.push("  begin");
  lines.push(`    ${name} = {${widthOut}{1'b0}};`);
  lines.push("    case ({carrier, opcode, state})");
  for(let carrier=0;carrier<tables.length;carrier++)for(let op=0;op<tables[carrier].length;op++)for(let state=0;state<tables[carrier][op].length;state++){
    lines.push(`      ${1+2+widthIn}'d${(carrier<<(2+widthIn))|(op<<widthIn)|state}: ${name} = ${widthOut}'d${tables[carrier][op][state]};`);
  }
  lines.push("      default: ;");
  lines.push("    endcase");
  lines.push("  end");
  lines.push("endfunction");
  return lines.join("\n");
}
function unaryCase(name,widthIn,widthOut,tables){
  const lines=[];
  lines.push(`function [${widthOut-1}:0] ${name};`);
  lines.push(`  input [0:0] carrier; input [${widthIn-1}:0] state;`);
  lines.push("  begin");
  lines.push(`    ${name} = {${widthOut}{1'b0}};`);
  lines.push("    case ({carrier, state})");
  for(let carrier=0;carrier<tables.length;carrier++)for(let state=0;state<tables[carrier].length;state++){
    lines.push(`      ${1+widthIn}'d${(carrier<<widthIn)|state}: ${name} = ${widthOut}'d${tables[carrier][state]};`);
  }
  lines.push("      default: ;");
  lines.push("    endcase");
  lines.push("  end");
  lines.push("endfunction");
  return lines.join("\n");
}
function quotientCase(packet){
  const lines=[];
  lines.push("function [5:0] quotient_step;");
  lines.push("  input [1:0] opcode; input [5:0] quotient;");
  lines.push("  begin quotient_step=6'd0; case ({opcode, quotient})");
  for(let op=0;op<packet.microvm.quotientGenerators.length;op++)for(let q=0;q<36;q++)lines.push(`    8'd${(op<<6)|q}: quotient_step=6'd${packet.microvm.quotientGenerators[op][q]};`);
  lines.push("    default: ; endcase end");
  lines.push("endfunction");
  return lines.join("\n");
}
function renderRTL(packet){
  const stateTables=[packet.microvm.circuitGenerators,packet.microvm.hemisystemGenerators];
  return `// Generated from data/w33_five_front_breakthrough.json.\n// Two typed 216-state actions share only a 36-state quotient adapter.\nmodule w33_dual_carrier_router(\n  input wire carrier_type, input wire [1:0] opcode, input wire [7:0] state, input wire adapt,\n  output reg valid, output reg typed_transition, output reg quotient_valid,\n  output reg [7:0] next_state, output reg [5:0] quotient_now, output reg [5:0] quotient_next,\n  output reg [5:0] state_next_quotient\n);\n${verilogCase("state_step",8,8,stateTables)}\n${unaryCase("block_id",8,6,[packet.microvm.circuitBlockIds,packet.microvm.hemisystemBlockIds])}\n${quotientCase(packet)}\nalways @* begin\n  valid=(state<8'd216)&&(opcode<2'd${packet.microvm.generatorCount});\n  quotient_valid=valid; typed_transition=valid&&!adapt;\n  next_state=8'hff; quotient_now=6'd0; quotient_next=6'd0; state_next_quotient=6'd0;\n  if(valid) begin\n    quotient_now=block_id(carrier_type,state);\n    quotient_next=quotient_step(opcode,quotient_now);\n    if(!adapt) begin\n      next_state=state_step(carrier_type,opcode,state);\n      state_next_quotient=block_id(carrier_type,next_state);\n    end\n  end\nend\nendmodule\n\nmodule w33_dual_carrier_router_formal(\n  input wire carrier_type, input wire [1:0] opcode, input wire [7:0] state, input wire adapt\n);\nwire valid,typed_transition,quotient_valid; wire [7:0] next_state; wire [5:0] quotient_now,quotient_next,state_next_quotient;\nw33_dual_carrier_router dut(carrier_type,opcode,state,adapt,valid,typed_transition,quotient_valid,next_state,quotient_now,quotient_next,state_next_quotient);\nalways @* begin\n  if(valid) begin\n    assert(quotient_now<6'd36); assert(quotient_next<6'd36);\n    if(adapt) begin assert(next_state==8'hff); assert(!typed_transition); end\n    else begin assert(next_state<8'd216); assert(state_next_quotient==quotient_next); assert(typed_transition); end\n  end\nend\nendmodule\n\nmodule w33_dual_carrier_router_control(\n  input wire carrier_type, input wire [1:0] opcode, input wire [7:0] state, input wire adapt\n);\nwire valid,typed_transition,quotient_valid; wire [7:0] next_state; wire [5:0] quotient_now,quotient_next,state_next_quotient;\nw33_dual_carrier_router dut(carrier_type,opcode,state,adapt,valid,typed_transition,quotient_valid,next_state,quotient_now,quotient_next,state_next_quotient);\nwire [7:0] illegal_cross_state = adapt ? 8'd0 : next_state;\nalways @* if(valid && adapt) assert(illegal_cross_state==8'hff);\nendmodule\n`;
}

function main(){
  const packet=build();
  const rtl=renderRTL(packet);
  if(process.argv.includes("--write")){
    fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
    fs.writeFileSync(RTL,rtl);
  }else{
    if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("five-front certificate drifted");
    if(rtl!==fs.readFileSync(RTL,"utf8"))throw new Error("typed micro-VM RTL drifted");
  }
  process.stdout.write(JSON.stringify({status:"PASS",steinbergRank:packet.steinbergIntertwiner.rank,quotient:packet.twoS5Correspondence.minimumRelation.quotientDegree,residualParity:packet.colourSwap.residual15Parity,fibreProduct:[packet.fibreProduct.states,packet.fibreProduct.building81Multiplicity,packet.fibreProduct.building64Multiplicity],maxTriple:packet.tau111Defect.maximumTripleFibres,microvm:[2,216,36],sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest,renderRTL};
