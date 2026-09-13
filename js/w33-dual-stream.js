'use strict';
// Incremental admission with replay-verified checkpoints. A digest is not a signature:
// callers must retain the expected checkpoint digest in trusted continuation state.
const B=require('./w33-octet-decoder-binding.js');
const clone=x=>structuredClone(x);
const hash=B.sha256;
const integerVector=v=>{if(!Array.isArray(v)||v.length!==40||v.some(x=>!Number.isSafeInteger(x)))throw new TypeError('40 safe integer coordinates required');return v.map(BigInt);};
const negative=v=>v.reduce((s,x)=>s+(x<0n?-x:0n),0n);
const safe=x=>{const n=Number(x);if(!Number.isSafeInteger(n)||BigInt(n)!==x)throw new RangeError('checkpoint integer overflow');return n;};
function createDualStream(rawPolicy,rawHeader){
  const policy=B.verifyDecoderPolicy(rawPolicy);
  if(policy.proofMode!=='dual-chain-v1')throw new Error('chain policy required');
  const header=clone(rawHeader),start=integerVector(header.start),image=integerVector(header.lineImage);
  if(hash(header.start)!==policy.inputPreimageDigest||hash(header.lineImage)!==policy.fiberDigest||hash(header.lines)!==policy.geometryDigest)throw new Error('stream header identity mismatch');
  if(!Array.isArray(header.lines)||header.lines.length!==40||header.lines.some(L=>!Array.isArray(L)||L.length!==4||new Set(L).size!==4||L.some(x=>!Number.isInteger(x)||x<0||x>=40)))throw new Error('invalid stream geometry');
  if(header.lines.some((L,i)=>L.reduce((s,j)=>s+start[j],0n)!==image[i]))throw new Error('initial fiber mismatch');
  const seed=hash({schema:'holotrade.dual-stream.v1',policyDigest:policy.decoderPolicyDigest,header});
  let cursor=start,records=[],root=seed,closed=false;
  function append(chunk){
    if(closed)throw new Error('stream already finalized');
    if(!Array.isArray(chunk)||chunk.length<1||records.length+chunk.length>policy.maxSteps)throw new Error('bounded nonempty chunk required');
    // All-or-nothing admission: no state mutation before the entire chunk passes.
    let next=cursor,nextRoot=root;const accepted=[];
    for(const raw of chunk){
      const r=clone(raw),index=records.length+accepted.length;
      if(r.index!==index||r.previousDigest!==nextRoot)throw new Error('stream order or prefix mismatch');
      const m=integerVector(r.move),step=r.step;
      if(!step||step.kind!=='circuit'||hash(r.move)!==step.moveDigest||!policy.permittedMoveDigests.includes(step.moveDigest))throw new Error('unapproved stream move');
      if(header.lines.some(L=>L.reduce((s,j)=>s+m[j],0n)!==0n))throw new Error('stream move leaves fiber');
      const after=next.map((x,i)=>x+m[i]);after.forEach(safe);
      if(!Number.isSafeInteger(step.before)||!Number.isSafeInteger(step.after)||step.after<0||step.after>=step.before||negative(next)!==BigInt(step.before)||negative(after)!==BigInt(step.after))throw new Error('actual stream descent mismatch');
      nextRoot=hash({previousDigest:nextRoot,index,move:r.move,step});accepted.push(r);next=after;
    }
    cursor=next;root=nextRoot;records=records.concat(accepted);
    return Object.freeze({acceptedSteps:records.length,prefixDigest:root,negativeMass:safe(negative(cursor)),optimalityVerified:false});
  }
  function checkpoint(){
    const body={schema:'holotrade.dual-stream-checkpoint.v1',policyDigest:policy.decoderPolicyDigest,header:clone(header),records:clone(records),prefixDigest:root};
    return {body,checkpointDigest:hash(body)};
  }
  function finish(dual){
    if(closed)throw new Error('stream already finalized');
    const end=cursor.map(safe),move=cursor.map((x,i)=>safe(x-start[i]));
    const witness={...clone(header),end,move,moveDigest:hash(move),moves:records.map(r=>clone(r.move)),dual:clone(dual)};
    const receipt={schema:B.RECEIPT_SCHEMA,decoderPolicyDigest:policy.decoderPolicyDigest,status:'OPTIMUM',initialNegativeMass:safe(negative(start)),finalNegativeMass:safe(negative(cursor)),finalPreimageDigest:hash(end),steps:records.map(r=>clone(r.step)),dualWitness:witness};
    const verified=B.verifyDecoderReceipt(receipt,policy);closed=true;
    return {receipt,verified,prefixDigest:root};
  }
  return Object.freeze({append,checkpoint,finish});
}
function resumeDualStream(policy,checkpoint,expectedCheckpointDigest){
  if(typeof expectedCheckpointDigest!=='string'||checkpoint.checkpointDigest!==expectedCheckpointDigest||hash(checkpoint.body)!==expectedCheckpointDigest)throw new Error('trusted checkpoint identity mismatch');
  const body=checkpoint.body,p=B.verifyDecoderPolicy(policy);
  if(body.schema!=='holotrade.dual-stream-checkpoint.v1'||body.policyDigest!==p.decoderPolicyDigest)throw new Error('checkpoint policy mismatch');
  const stream=createDualStream(p,body.header);
  if(!Array.isArray(body.records)||body.records.length>p.maxSteps)throw new Error('checkpoint history bound');
  if(body.records.length)stream.append(body.records);
  if(stream.checkpoint().body.prefixDigest!==body.prefixDigest)throw new Error('checkpoint replay mismatch');
  return stream;
}
module.exports={createDualStream,resumeDualStream};
