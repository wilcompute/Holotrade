"use strict";

// Logarithmic audit layer for the signed append-only representation-market
// provenance chain.  The linear Ed25519 chain remains authoritative; this file
// commits its signedEventDigest sequence in a Merkle-mountain-range (MMR) style
// forest and supplies inclusion + append-only prefix-consistency proofs.

const crypto=require("node:crypto");
const H=require("./w33-representation-market-provenance.js");

const COMMIT_SCHEMA="holotrade.w33-representation-provenance-mmr.v1";
const INCLUSION_SCHEMA="holotrade.w33-representation-provenance-mmr-inclusion.v1";
const CONSISTENCY_SCHEMA="holotrade.w33-representation-provenance-mmr-consistency.v1";
const DOMAIN="holotrade.w33-representation-provenance-mmr.v1";

function stable(value){
  if(Array.isArray(value))return `[${value.map(stable).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map(k=>`${JSON.stringify(k)}:${stable(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value){return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;}
function isDigest(v){return typeof v==="string"&&/^sha256:[0-9a-f]{64}$/.test(v);}
function heightForSize(size){
  if(!Number.isSafeInteger(size)||size<1)throw new RangeError("size must be positive safe integer");
  let h=0,n=1;while(n<size){n*=2;h++;}if(n!==size)throw new RangeError("size must be a power of two");return h;
}
function leafHash(digest){if(!isDigest(digest))throw new TypeError("signed event digest required");return sha256([DOMAIN,"leaf",digest]);}
function nodeHash(left,right,height){if(!isDigest(left)||!isDigest(right))throw new TypeError("child hashes required");return sha256([DOMAIN,"node",height,left,right]);}

function peakIntervals(count){
  if(!Number.isSafeInteger(count)||count<0)throw new RangeError("leaf count must be natural");
  const out=[];let start=0,remaining=count;
  while(remaining>0){
    let size=1;while(size*2<=remaining)size*=2;
    out.push(Object.freeze({start,size,height:heightForSize(size)}));
    start+=size;remaining-=size;
  }
  return Object.freeze(out);
}

function appendBlock(peaks,height,hash){
  if(!Number.isSafeInteger(height)||height<0||!isDigest(hash))throw new TypeError("valid block required");
  const out=peaks.map(p=>({height:p.height,hash:p.hash}));let h=height,z=hash;
  while(out.length&&out[out.length-1].height===h){
    const left=out.pop();z=nodeHash(left.hash,z,h+1);h++;
  }
  out.push({height:h,hash:z});return out;
}

function perfectRoot(leafDigests,start,size){
  if(size===1)return leafHash(leafDigests[start]);
  const half=size/2,h=heightForSize(size);
  return nodeHash(perfectRoot(leafDigests,start,half),perfectRoot(leafDigests,start+half,half),h);
}

function buildPeaks(leafDigests){
  let peaks=[];
  for(const d of leafDigests)peaks=appendBlock(peaks,0,leafHash(d));
  return Object.freeze(peaks.map(Object.freeze));
}

function rootFromPeaks(count,peaks){
  const expected=peakIntervals(count).map(x=>x.height);
  if(!Array.isArray(peaks)||peaks.length!==expected.length)throw new Error("MMR peak count mismatch");
  for(let i=0;i<peaks.length;i++){
    if(peaks[i].height!==expected[i]||!isDigest(peaks[i].hash))throw new Error("MMR peak shape mismatch");
  }
  return sha256({domain:DOMAIN,leafCount:count,peaks:peaks.map(p=>({height:p.height,hash:p.hash}))});
}

function eventDigests(history){
  if(!history||history.schema!==H.HISTORY_SCHEMA||!Array.isArray(history.events)||!history.events.length)throw new TypeError("signed representation provenance history required");
  const ds=history.events.map(e=>e&&e.signedEventDigest);
  if(!ds.every(isDigest))throw new TypeError("history contains invalid signed event digest");
  return ds;
}

function commitHistory(history){
  const ds=eventDigests(history),peaks=buildPeaks(ds),rootDigest=rootFromPeaks(ds.length,peaks);
  return Object.freeze({schema:COMMIT_SCHEMA,historyDigest:history.historyDigest,eventCount:ds.length,
    representationMarketIdentityDigest:history.representationMarketIdentityDigest,
    signedResourceSelectionDigest:history.signedResourceSelectionDigest,representationClass:history.representationClass,
    peaks,rootDigest});
}

function pathWithinPerfectTree(ds,start,size,index){
  if(size===1)return [];
  const half=size/2,h=heightForSize(size);
  if(index<start+half){
    const lower=pathWithinPerfectTree(ds,start,half,index);
    return lower.concat([{side:"right",height:h,hash:perfectRoot(ds,start+half,half)}]);
  }
  const lower=pathWithinPerfectTree(ds,start+half,half,index);
  return lower.concat([{side:"left",height:h,hash:perfectRoot(ds,start,half)}]);
}

function inclusionProof(history,index){
  const ds=eventDigests(history);if(!Number.isSafeInteger(index)||index<0||index>=ds.length)throw new RangeError("event index out of range");
  const intervals=peakIntervals(ds.length),pi=intervals.findIndex(x=>index>=x.start&&index<x.start+x.size);if(pi<0)throw new Error("MMR peak not found");
  const I=intervals[pi],peaks=buildPeaks(ds),siblings=pathWithinPerfectTree(ds,I.start,I.size,index);
  return Object.freeze({schema:INCLUSION_SCHEMA,eventCount:ds.length,index,targetPeakIndex:pi,targetPeakStart:I.start,targetPeakHeight:I.height,
    siblings:Object.freeze(siblings.map(Object.freeze)),peaks,rootDigest:rootFromPeaks(ds.length,peaks)});
}

function verifyInclusion(commitment,signedEventDigest,proof){
  try{
    if(!commitment||commitment.schema!==COMMIT_SCHEMA||!proof||proof.schema!==INCLUSION_SCHEMA)return Object.freeze({ok:false,code:"MMR_SCHEMA_INVALID"});
    if(commitment.eventCount!==proof.eventCount||commitment.rootDigest!==proof.rootDigest)return Object.freeze({ok:false,code:"MMR_ROOT_CONTEXT_MISMATCH"});
    const intervals=peakIntervals(proof.eventCount),I=intervals[proof.targetPeakIndex];
    if(!I||proof.index<I.start||proof.index>=I.start+I.size||I.start!==proof.targetPeakStart||I.height!==proof.targetPeakHeight)return Object.freeze({ok:false,code:"MMR_TARGET_PEAK_INVALID"});
    let z=leafHash(signedEventDigest),local=proof.index-I.start;
    if(proof.siblings.length!==I.height)return Object.freeze({ok:false,code:"MMR_PATH_LENGTH_INVALID"});
    for(let level=0;level<I.height;level++){
      const s=proof.siblings[level],expectedSide=((Math.floor(local/(2**level))%2)===0)?"right":"left";
      if(!s||s.side!==expectedSide||s.height!==level+1||!isDigest(s.hash))return Object.freeze({ok:false,code:"MMR_PATH_SHAPE_INVALID"});
      z=s.side==="right"?nodeHash(z,s.hash,level+1):nodeHash(s.hash,z,level+1);
    }
    if(!Array.isArray(proof.peaks)||!proof.peaks[proof.targetPeakIndex]||proof.peaks[proof.targetPeakIndex].hash!==z)return Object.freeze({ok:false,code:"MMR_INCLUSION_PEAK_MISMATCH"});
    const root=rootFromPeaks(proof.eventCount,proof.peaks);
    if(root!==commitment.rootDigest)return Object.freeze({ok:false,code:"MMR_INCLUSION_ROOT_MISMATCH"});
    return Object.freeze({ok:true,code:"MMR_INCLUSION_VERIFIED",index:proof.index,rootDigest:root});
  }catch(e){return Object.freeze({ok:false,code:"MMR_INCLUSION_INVALID",reason:String(e.message)});}
}

function alignedSuffixBlocks(ds,oldCount){
  const blocks=[];let pos=oldCount,remaining=ds.length-oldCount;
  while(remaining>0){
    let size=1;
    while(size*2<=remaining&&pos%(size*2)===0)size*=2;
    blocks.push(Object.freeze({start:pos,size,height:heightForSize(size),hash:perfectRoot(ds,pos,size)}));
    pos+=size;remaining-=size;
  }
  return Object.freeze(blocks);
}

function consistencyProof(oldHistory,newHistory){
  const oldDs=eventDigests(oldHistory),newDs=eventDigests(newHistory);
  if(oldDs.length>newDs.length)throw new Error("old history cannot exceed new history");
  for(let i=0;i<oldDs.length;i++)if(oldDs[i]!==newDs[i])throw new Error("histories are not prefix-related");
  const oldPeaks=buildPeaks(oldDs),extensionBlocks=alignedSuffixBlocks(newDs,oldDs.length);
  return Object.freeze({schema:CONSISTENCY_SCHEMA,oldEventCount:oldDs.length,newEventCount:newDs.length,
    oldPeaks,extensionBlocks,oldRootDigest:rootFromPeaks(oldDs.length,oldPeaks),newRootDigest:rootFromPeaks(newDs.length,buildPeaks(newDs))});
}

function verifyConsistency(oldCommitment,newCommitment,proof){
  try{
    if(!oldCommitment||!newCommitment||oldCommitment.schema!==COMMIT_SCHEMA||newCommitment.schema!==COMMIT_SCHEMA||!proof||proof.schema!==CONSISTENCY_SCHEMA)return Object.freeze({ok:false,code:"MMR_SCHEMA_INVALID"});
    if(proof.oldEventCount!==oldCommitment.eventCount||proof.newEventCount!==newCommitment.eventCount||proof.oldRootDigest!==oldCommitment.rootDigest||proof.newRootDigest!==newCommitment.rootDigest)return Object.freeze({ok:false,code:"MMR_CONSISTENCY_CONTEXT_MISMATCH"});
    if(oldCommitment.representationMarketIdentityDigest!==newCommitment.representationMarketIdentityDigest||oldCommitment.signedResourceSelectionDigest!==newCommitment.signedResourceSelectionDigest||oldCommitment.representationClass!==newCommitment.representationClass)return Object.freeze({ok:false,code:"MMR_REPRESENTATION_IDENTITY_DRIFT"});
    if(rootFromPeaks(proof.oldEventCount,proof.oldPeaks)!==oldCommitment.rootDigest)return Object.freeze({ok:false,code:"MMR_OLD_ROOT_INVALID"});
    let peaks=proof.oldPeaks.map(p=>({height:p.height,hash:p.hash})),count=proof.oldEventCount;
    for(const b of proof.extensionBlocks){
      if(!b||b.start!==count||b.size!==2**b.height||count%b.size!==0||!isDigest(b.hash))return Object.freeze({ok:false,code:"MMR_EXTENSION_BLOCK_INVALID"});
      peaks=appendBlock(peaks,b.height,b.hash);count+=b.size;
    }
    if(count!==proof.newEventCount)return Object.freeze({ok:false,code:"MMR_EXTENSION_LENGTH_MISMATCH"});
    if(rootFromPeaks(count,peaks)!==newCommitment.rootDigest)return Object.freeze({ok:false,code:"MMR_NEW_ROOT_INVALID"});
    return Object.freeze({ok:true,code:"MMR_PREFIX_CONSISTENCY_VERIFIED",oldEventCount:proof.oldEventCount,newEventCount:proof.newEventCount,newRootDigest:newCommitment.rootDigest});
  }catch(e){return Object.freeze({ok:false,code:"MMR_CONSISTENCY_INVALID",reason:String(e.message)});}
}

module.exports={COMMIT_SCHEMA,INCLUSION_SCHEMA,CONSISTENCY_SCHEMA,stable,sha256,leafHash,nodeHash,peakIntervals,buildPeaks,rootFromPeaks,commitHistory,inclusionProof,verifyInclusion,consistencyProof,verifyConsistency};
