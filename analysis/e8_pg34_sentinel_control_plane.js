#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const S=require("../js/substrate.js");
const {runGap:runGapPortable}=require("../scripts/run-gap.js");

const ROOT=path.resolve(__dirname,"..");
const GAP=path.join(__dirname,"e8_pg34_sentinel_control_plane.g");
const OUT=path.join(ROOT,"data","e8_pg34_sentinel_control_plane.json");

function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map((k)=>`${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function digest(value){return crypto.createHash("sha256").update(canonical(value)).digest("hex");}
function requireLine(stdout,prefix){
  const line=stdout.split(/\r?\n/).find((row)=>row.startsWith(prefix));
  if(!line)throw new Error(`GAP output missing ${prefix}`);
  return line;
}
function parseSets(line,prefix,size){
  const body=line.slice(prefix.length);
  const sets=body?body.split(";").map((row)=>row.split(",").map((x)=>Number(x)-1)):[];
  if(sets.some((row)=>row.length!==size||new Set(row).size!==size))throw new Error(`${prefix} malformed`);
  return sets;
}
function mm(A,B){
  return A.map((row)=>B[0].map((_,j)=>row.reduce((sum,x,k)=>sum+x*B[k][j],0)));
}
function transpose(A){return A[0].map((_,j)=>A.map((row)=>row[j]));}
function equal(A,B){return canonical(A)===canonical(B);}
function bitCount(x){let n=0;for(;x;x>>=1n)n+=Number(x&1n);return n;}
function xorBasis(words){
  const pivots=new Map();
  for(const word of words){
    let x=word;
    while(x){
      const p=x.toString(2).length-1;
      if(pivots.has(p))x^=pivots.get(p);else{pivots.set(p,x);break;}
    }
  }
  return [...pivots.entries()].sort((a,b)=>b[0]-a[0]).map(([,x])=>x);
}

function runGap(){
  const run=runGapPortable(GAP,{cwd:ROOT,quiet:true});
  if(!run.ok||/Error,|Syntax error/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed\n${run.stdout}\n${run.stderr}`);
  for(const expected of [
    "PG34|points=85|absolute=45|nonabsolute=40|row=21|lambda=5|trace=45|identity=H2=16I+5J|spectrum=21^1,4^45,-4^39",
    "SENTINEL|length=40|dimension=15|distance=8|minimumWords=45|doublyEven=1|selfOrthogonal=1|weights=0:1,8:45,12:720,16:6930,20:17376,24:6930,28:720,32:45,40:1",
    "SHELL|distance12=720|distance16=270|weight12Unique=720|girth=5|circuits=216|nonedgeMultiplicity=3",
    "GROUP|autW33=51840|psp=25920|circuitOrbit=216|stabilizer=120|stabilizerAction=120",
    "FLATBAND|rankExact=25|zeroExact=35|rankPerturbed=40|zeroPerturbed=5|indexFloor=5|extraSymmetry=30",
  ])if(!run.stdout.includes(expected))throw new Error(`GAP theorem line changed: ${expected}`);
  return {
    supports:parseSets(requireLine(run.stdout,"SUPPORTS|"),"SUPPORTS|",8),
    circuits:parseSets(requireLine(run.stdout,"CIRCUITS|"),"CIRCUITS|",5),
  };
}

function build(){
  const {supports,circuits}=runGap();
  if(supports.length!==45||circuits.length!==216)throw new Error("GAP carrier counts changed");

  const A=Array.from({length:40},()=>Array(40).fill(0));
  for(const line of S.LINES)for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)A[line[i]][line[j]]=A[line[j]][line[i]]=1;
  const B=Array.from({length:40},(_,i)=>supports.map((support)=>Number(support.includes(i))));
  const G=Array.from({length:45},()=>Array(45).fill(0));
  for(let i=0;i<45;i++)for(let j=i+1;j<45;j++)if(supports[i].every((x)=>!supports[j].includes(x)))G[i][j]=G[j][i]=1;
  if(A.some((row)=>row.reduce((a,b)=>a+b)!==12)||B.some((row)=>row.reduce((a,b)=>a+b)!==9)||G.some((row)=>row.reduce((a,b)=>a+b)!==12))throw new Error("carrier degree mismatch");

  const Bt=transpose(B),BBt=mm(B,Bt),BtB=mm(Bt,B);
  const targetBBt=A.map((row,i)=>row.map((x,j)=>8*Number(i===j)+2*x+1));
  const targetBtB=G.map((row,i)=>row.map((x,j)=>8*Number(i===j)+2*Number(i!==j&&x===0)));
  if(!equal(BBt,targetBBt)||!equal(BtB,targetBtB))throw new Error("cross-incidence Gram identity failed");

  const H=[];
  for(let i=0;i<40;i++)H.push([...A[i],...B[i]]);
  for(let j=0;j<45;j++)H.push([...Bt[j],...G[j].map((x,k)=>x+Number(j===k))]);
  const H2=mm(H,H);
  for(let i=0;i<85;i++)for(let j=0;j<85;j++)if(H2[i][j]!==16*Number(i===j)+5)throw new Error("H^2 identity failed");
  if(H.some((row)=>row.reduce((a,b)=>a+b)!==21)||H.reduce((sum,row,i)=>sum+row[i],0)!==45)throw new Error("polarity design parameters failed");

  const masks=supports.map((support)=>support.reduce((m,i)=>m|(1n<<BigInt(i)),0n));
  const basis=xorBasis(masks);
  if(basis.length!==15)throw new Error("sentinel dimension failed");
  const enumerator={};const minimum=[];
  for(let coeff=0;coeff<(1<<basis.length);coeff++){
    let word=0n;for(let i=0;i<basis.length;i++)if((coeff>>i)&1)word^=basis[i];
    const weight=bitCount(word);enumerator[weight]=(enumerator[weight]||0)+1;if(weight===8)minimum.push(word);
    if(weight%4)throw new Error("sentinel is not doubly even");
  }
  const expected={0:1,8:45,12:720,16:6930,20:17376,24:6930,28:720,32:45,40:1};
  if(canonical(enumerator)!==canonical(expected)||
     canonical(minimum.map(String).sort())!==canonical(masks.map(String).sort()))throw new Error("sentinel enumerator/minima failed");
  if(basis.some((x)=>basis.some((y)=>bitCount(x&y)%2)))throw new Error("sentinel self-orthogonality failed");
  const perturbedRows=B.map((row,i)=>row.reduce((mask,x,j)=>mask|(BigInt(x^Number(i===j))<<BigInt(j)),0n));
  if(xorBasis(perturbedRows).length!==40)throw new Error("full-rank chiral perturbation failed over F2");

  const pairWords=new Set();let distance12=0,distance16=0;
  for(let i=0;i<45;i++)for(let j=i+1;j<45;j++){
    const word=masks[i]^masks[j],key=word.toString(16);if(pairWords.has(key))throw new Error("four-circuit found");pairWords.add(key);
    const d=bitCount(word);if(d===12)distance12++;else if(d===16)distance16++;else throw new Error("minimum-shell distance changed");
  }
  if(distance12!==720||distance16!==270)throw new Error("minimum-shell census failed");
  for(const circuit of circuits){
    const xor=circuit.reduce((word,i)=>word^masks[i],0n);if(xor!==0n)throw new Error("invalid five-circuit");
    for(let i=0;i<5;i++)for(let j=i+1;j<5;j++)if(bitCount(masks[circuit[i]]^masks[circuit[j]])!==12)throw new Error("circuit is not a coclique");
  }

  const body={
    schema:"holotrade.e8-pg34-sentinel-control-plane.v1",
    evidenceClass:"EXACT_GAP_RECONSTRUCTION_WITH_INDEPENDENT_JS_REPLAY",
    carrier:{states:85,split:{w33Nonabsolute:40,gq42Absolute:45},crossIncidence:"B is 40x45",crossDegrees:{fromW33:9,fromGQ42:8}},
    gramIdentities:{BBt:"8I_40 + 2A_W33 + J_40",BtB:"8I_45 + 2A_complement(GQ42)",rankOverQ:25,chiralKernelSplit:[15,20],chiralSpectrum:"0^35, +/-sqrt(72)^1, +/-sqrt(12)^24"},
    chiralProtection:{exactZeroModes:35,rectangularIndexFloor:5,explicitDiagonalPerturbationRank:40,perturbedZeroModes:5,symmetryDependentExtraModes:30,reading:"Five zero modes survive every off-diagonal 40x45 coupling by rectangular index; the additional thirty in the exact incidence operator depend on its special symmetry/rank."},
    polarityDesign:{parameters:"2-(85,21,5)",matrixIdentity:"H^2 = 16I + 5J",rowSum:21,trace:45,spectrum:{"21":1,"4":45,"-4":39},determinant:"-21 * 4^84",inverse:"H/16 - 5J/336",binaryRank:17},
    sentinel:{parameters:"[40,15,8]_2",dimension:15,minimumDistance:8,doublyEven:true,selfOrthogonal:true,weightEnumerator:expected,minimumWords:45,minimumWordsExactlyCrossIncidenceColumns:true},
    shell:{distance12Pairs:720,distance16Pairs:270,weight12WordsAsUniqueNoncollinearPairXors:720,matroidRank:15,girth:5,fiveCircuits:216,everyCircuitIsGQ42Coclique:true,nonedgeCircuitMultiplicity:3,orbit:"PSp(4,3)/S5",ambientGroupOrder:25920,stabilizerOrder:120},
    logicalArtifacts:{supports,circuits,polarityRows:H.map((row)=>row.flatMap((x,j)=>x?[j]:[]))},
    theorem:"One exact 40x45 cross-incidence matrix simultaneously couples the W33 and GQ(4,2) carriers, generates exactly the 45 minimum words of the binary sentinel, and completes to the 85-point PG(3,4) polarity design after restoring the 45 absolute loops.",
    attributionBoundary:"The 2-(85,21,5) PG(3,4) design, its [85,17,21]_2 plane code, and the invariant [40,15,8]_2 code are classical. The certified integration result is their explicit equality in the independently reconstructed W33/GQ(4,2) cross-incidence coordinates.",
    evidenceBoundary:"These are finite logical incidence, code, and module objects. They do not identify physical E8 coordinates in this repository, bind machines, implement cryptographic authentication, or authorize dispatch.",
    provenance:{w33Source:"W33-Theory commits c54629837, e7943e9d5, 4e660507f, 932a16524, b5e9823d3, 74aa9507a",e8ResidueContext:"W33-Theory Pass9961-9984 and Pass10377-10388",localInputs:["js/substrate.js","analysis/e8_unitary_elastic_ladders.g"]},
  };
  return {...body,sha256:digest(body)};
}

function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(!fs.existsSync(OUT))throw new Error("frozen sentinel control-plane certificate missing; run --write");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("frozen sentinel control-plane certificate drifted");
  process.stdout.write(JSON.stringify({status:"PASS",states:85,sentinel:[40,15,8],circuits:216,sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest};
