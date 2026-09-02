#!/usr/bin/env node
"use strict";

const crypto=require("node:crypto");
const fs=require("node:fs");
const path=require("node:path");
const {runGap}=require("../scripts/run-gap.js");

const ROOT=path.resolve(__dirname,"..");
const GAP=path.join(__dirname,"e8_unitary_homology_code_w33_obstruction.g");
const OUT=path.join(ROOT,"data","e8_unitary_homology_code_w33_obstruction.json");

function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map((key)=>`${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  return JSON.stringify(value);
}
function digest(value){return crypto.createHash("sha256").update(canonical(value)).digest("hex");}
function requireLine(stdout,prefix){
  const line=stdout.split(/\r?\n/).find((row)=>row.startsWith(prefix));
  if(!line)throw new Error(`GAP output missing ${prefix}`);
  return line;
}
function sparse(enumerator){
  return Object.fromEntries(enumerator.map((count,weight)=>[weight,count.toString()]).filter(([,count])=>count!=="0"));
}
function parseRankDistribution(text){
  return Object.fromEntries(text.split(",").map((pair)=>{const [rank,count]=pair.split(":");return [rank,Number(count)];}));
}
function wordsFromBits(bits){
  if(bits.length!==120||/[^01]/.test(bits))throw new Error("malformed 120-bit GAP basis word");
  const words=new Uint32Array(4);
  for(let i=0;i<120;i++)if(bits[i]==="1")words[i>>>5]=(words[i>>>5]|(1<<(i&31)))>>>0;
  return words;
}
function binomialTable(n){
  const rows=Array.from({length:n+1},()=>Array(n+1).fill(0n));
  rows[0][0]=1n;
  for(let i=1;i<=n;i++)for(let j=0;j<=i;j++)rows[i][j]=(j?rows[i-1][j-1]:0n)+(j<i?rows[i-1][j]:0n);
  return rows;
}
function macWilliams(binaryEnumerator){
  const n=binaryEnumerator.length-1,choose=binomialTable(n),size=binaryEnumerator.reduce((a,b)=>a+b,0n);
  const dual=Array(n+1).fill(0n);
  for(let j=0;j<=n;j++){
    let numerator=0n;
    for(let i=0;i<=n;i++)if(binaryEnumerator[i]){
      let krawtchouk=0n;
      for(let ell=Math.max(0,j-(n-i));ell<=Math.min(i,j);ell++){
        const term=choose[i][ell]*choose[n-i][j-ell];
        krawtchouk+=(ell&1)?-term:term;
      }
      numerator+=binaryEnumerator[i]*krawtchouk;
    }
    if(numerator%size)throw new Error(`nonintegral MacWilliams coefficient at ${j}`);
    dual[j]=numerator/size;
  }
  return dual;
}

// The GAP witness supplies C=im(A) as S plus a 25-dimensional transversal.
// S consists of the even full-fibre flips (dimension 14) and one half-fibre
// word.  Thus each of the 2^25 transversal words contributes two histograms,
// and an even-parity product recovers all 2^15 words in its structured coset.
function exactEnumerators(transversalBits,globalHalfBits){
  if(transversalBits.length!==25)throw new Error("GAP did not supply the 25-dimensional transversal");
  const basis=transversalBits.map(wordsFromBits),half=wordsFromBits(globalHalfBits);
  const halfBytes=Array.from({length:15},(_,block)=>(half[block>>>2]>>>((block&3)*8))&255);
  const pop8=Uint8Array.from({length:256},(_,x)=>{let n=0;for(let y=x;y;y>>>=1)n+=y&1;return n;});
  const place=Array.from({length:9},(_,weight)=>16**weight);
  const profiles=new Map(),word=new Uint32Array(4),limit=2**25;
  const bump=(key)=>profiles.set(key,(profiles.get(key)||0)+1);
  for(let index=0;index<limit;index++){
    let key0=0,key1=0;
    for(let block=0;block<15;block++){
      const byte=(word[block>>>2]>>>((block&3)*8))&255;
      key0+=place[pop8[byte]];
      key1+=place[pop8[byte^halfBytes[block]]];
    }
    bump(key0);bump(key1);
    if(index+1<limit){
      const changed=31-Math.clz32((index+1)&-(index+1)),row=basis[changed];
      for(let part=0;part<4;part++)word[part]=(word[part]^row[part])>>>0;
    }
  }

  const image=Array(121).fill(0n);
  for(const [encoded,multiplicity] of profiles){
    let key=encoded;
    let even=Array(121).fill(0n),odd=Array(121).fill(0n);even[0]=1n;
    for(let weight=0;weight<=8;weight++){
      const count=key%16;key=Math.floor(key/16);
      for(let copy=0;copy<count;copy++){
        const nextEven=Array(121).fill(0n),nextOdd=Array(121).fill(0n),flipped=8-weight;
        for(let total=0;total<=120;total++){
          if(even[total]){nextEven[total+weight]+=even[total];nextOdd[total+flipped]+=even[total];}
          if(odd[total]){nextOdd[total+weight]+=odd[total];nextEven[total+flipped]+=odd[total];}
        }
        even=nextEven;odd=nextOdd;
      }
    }
    const scale=BigInt(multiplicity);
    for(let weight=0;weight<=120;weight++)image[weight]+=scale*even[weight];
  }
  const kernel=macWilliams(image);
  if(image.reduce((a,b)=>a+b,0n)!==(1n<<40n))throw new Error("image enumerator does not total 2^40");
  if(kernel.reduce((a,b)=>a+b,0n)!==(1n<<80n))throw new Error("kernel enumerator does not total 2^80");
  return {image,kernel,profileCount:profiles.size};
}

function build(){
  const run=runGap(GAP,{cwd:ROOT,quiet:true});
  if(!run.ok||/Error,|Syntax error/.test(run.stdout+run.stderr))throw new Error(`GAP witness failed\n${run.stdout}\n${run.stderr}`);
  for(const expected of [
    "CODE_CHAIN|n=120|image=40|kernel=80|homology=40|coimage=40|selfOrthogonal=1|doublyEven=1",
    "CODE_TRANSVERSAL|structured=15|evenFibre=14|globalHalf=1|transversal=25|enumeratedCosets=33554432",
    "MODULES|imageFactors=1^4,4^5,16^1|homologyFactors=1^8,4^8|coimageFactors=1^4,4^5,16^1|imageIsoCoimage=1|imageIsoHomology=0",
    "O2_ACTION|order=32|homologyMoveRanks=0,12,14,16|homologyFixed=15|homologyCoinvariants=15|imageMoveRanks=0,10,16,18|imageFixed=14|imageCoinvariants=14",
    "GENUINE_W33|points=40|lines=40|PSpOrder=25920|spreadStabilizer=S6|order=720|transitive=1|pointStabilizer=18",
    "W33_OBSTRUCTION|sameFactors=1|twoS6Classes=2|isomorphisms=0|homDimensions=2,2|nonzeroRankProfiles=1,6;1,11|O2HomologyTrivial=0|O2W33Trivial=1",
    "ALL_UNITARY_HOMOLOGY_CODE_W33_OBSTRUCTION_CHECKS_PASS",
  ])if(!run.stdout.includes(expected))throw new Error(`GAP theorem line changed: ${expected}`);
  const rankLine=requireLine(run.stdout,"O2_RANK_DISTRIBUTIONS|");
  const match=rankLine.match(/^O2_RANK_DISTRIBUTIONS\|homology=([^|]+)\|image=(.+)$/);
  if(!match)throw new Error("malformed O2 rank distribution");
  const transversal=run.stdout.split(/\r?\n/).filter((row)=>row.startsWith("QBASIS|")).map((row)=>row.slice(7));
  const globalHalf=requireLine(run.stdout,"GLOBAL_HALF|").slice(12);
  const {image,kernel,profileCount}=exactEnumerators(transversal,globalHalf);
  const imageDistance=image.findIndex((count,weight)=>weight>0&&count>0n);
  const kernelDistance=kernel.findIndex((count,weight)=>weight>0&&count>0n);
  if(imageDistance!==16||kernelDistance!==8||kernel[8]!==435n)throw new Error(`code parameters changed: image d=${imageDistance}, kernel d=${kernelDistance}, A8=${kernel[8]}`);
  if(image.some((count,weight)=>count&&weight%4))throw new Error("image enumerator is not doubly even");

  const body={
    schema:"holotrade.e8-unitary-homology-code-w33-obstruction.v1",
    evidenceClass:"EXACT_GAP_MEATAXE_WITH_COMPLETE_COSET_ENUMERATOR_AND_MACWILLIAMS_DUAL",
    differential:{length:120,squareZero:true,rank:40,imageDimension:40,kernelDimension:80,homologyDimension:40,coimageDimension:40},
    codes:{image:{parameters:"[120,40,16]_2",doublyEven:true,selfOrthogonal:true,weightEnumerator:sparse(image)},kernel:{parameters:"[120,80,8]_2",isImageDual:true,minimumWords:kernel[8].toString(),weightEnumerator:sparse(kernel)},css:{parameters:"[[120,40,8]]_2",construction:"H_X = H_Z = a basis of im(A); logical quotient ker(A)/im(A)",exactDistanceReason:"Every nonzero image word has weight at least 16, while all 435 kernel words of weight 8 therefore represent nonzero logical classes."}},
    exhaustiveEnumerator:{structuredDimension:15,evenFullFibreDimension:14,globalHalfDimension:1,transversalDimension:25,transversalWords:2**25,profileCount,representedImageWords:"1099511627776",method:"Enumerate every transversal word by Gray code; factor each structured coset through its fifteen 8-point fibres; derive the dual enumerator by the exact binary MacWilliams transform."},
    modules:{group:"2^5:S6",imageFactors:{"1":4,"4":5,"16":1},homologyFactors:{"1":8,"4":8},coimageFactors:{"1":4,"4":5,"16":1},imageIsomorphicToCoimage:true,imageIsomorphicToHomology:false},
    twoCore:{structure:"C2^5",order:32,homologyMoveRankDistribution:parseRankDistribution(match[1]),imageMoveRankDistribution:parseRankDistribution(match[2]),homologyFixedDimension:15,homologyCoinvariantDimension:15,imageFixedDimension:14,imageCoinvariantDimension:14},
    w33Comparison:{carrier:"the genuine 40-point permutation module of W(3,3)",routeSubgroup:"a spread stabilizer S6 in PSp(4,3)",routeOrder:720,routePointStabilizerOrder:18,s6IdentificationClassesTested:2,compositionFactorsMatchHomology:true,isomorphicInEitherClass:false,homSpaceDimensionEachDirection:2,nonzeroRankProfiles:[[1,6],[1,11]],obstruction:"The normal C2^5 acts nontrivially on differential homology but trivially on every module inflated from the S6 quotient."},
    theorem:"The characteristic-two 120-state adjacency differential defines an exact [[120,40,8]] CSS code. Its 40-dimensional logical homology has the same composition-factor dimensions as the W(3,3) point carrier restricted to a spread stabilizer, but is not that module under either S6 identification class.",
    evidenceBoundary:"This is an exact finite binary code and representation-module certificate. Matching composition factors do not imply module isomorphism; the witness proves the opposite here. No physical qubits, noise model, decoder threshold, integral E8 coordinates, cryptographic identity, or dispatch authority are supplied.",
    provenance:{localInputs:["analysis/e8_unitary_crossprime_fibre_differential.g"],externalCarrier:"W(3,3) is rebuilt directly as the symplectic polar space in PG(3,3); no imported coordinate table is trusted."},
  };
  return {...body,sha256:digest(body)};
}

function main(){
  const packet=build();
  if(process.argv.includes("--write"))fs.writeFileSync(OUT,JSON.stringify(packet,null,2)+"\n");
  else if(!fs.existsSync(OUT))throw new Error("frozen homology/code certificate missing; run --write");
  else if(canonical(packet)!==canonical(JSON.parse(fs.readFileSync(OUT,"utf8"))))throw new Error("frozen homology/code certificate drifted");
  process.stdout.write(JSON.stringify({status:"PASS",image:"[120,40,16]",kernel:"[120,80,8]",css:"[[120,40,8]]",minimumLogicalWords:packet.codes.kernel.minimumWords,sha256:packet.sha256})+"\n");
}
if(require.main===module){try{main();}catch(error){console.error(error.stack||error.message);process.exitCode=1;}}
module.exports={build,canonical,digest,exactEnumerators,macWilliams};
