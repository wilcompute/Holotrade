// ======================================================================
// HOLOTRADE TRANSPARENCY-BACKED DSSE WORKFLOW
//
// RFC6962-style SHA-256 Merkle hashing (0x00 leaves, 0x01 internal nodes),
// Ed25519-signed checkpoints, inclusion proofs, and threshold DSSE verification.
// This is a real cryptographic local append-only log, but NOT Rekor/Sigstore
// interoperability, public witnessing, certificate identity, or attestation.
// ======================================================================
(function(root){
  "use strict";
  const E=root.HolotradeEvidence||(typeof require!=="undefined"?require("./evidence.js"):null);
  const Sig=root.HolotradeSigning||(typeof require!=="undefined"?require("./signing.js"):null);
  let crypto=null;if(typeof require!=="undefined"){try{crypto=require("node:crypto");}catch(_){crypto=null;}}
  if(!E||!Sig||!crypto)throw new Error("transparency requires evidence, signing, and node:crypto");
  const SCHEMA="holotrade.transparency.v1";
  const hash=(b)=>crypto.createHash("sha256").update(b).digest();
  const b64=(b)=>Buffer.from(b).toString("base64");
  const unb64=(s)=>Buffer.from(s,"base64");
  const leafHash=(bytes)=>hash(Buffer.concat([Buffer.from([0]),Buffer.from(bytes)]));
  const nodeHash=(a,b)=>hash(Buffer.concat([Buffer.from([1]),Buffer.from(a),Buffer.from(b)]));
  function largestPowerLessThan(n){let k=1;while((k<<1)<n)k<<=1;return k;}
  function treeHash(leaves){
    if(leaves.length===0)return hash(Buffer.alloc(0));
    if(leaves.length===1)return leafHash(leaves[0]);
    const k=largestPowerLessThan(leaves.length);
    return nodeHash(treeHash(leaves.slice(0,k)),treeHash(leaves.slice(k)));
  }
  function auditPath(leaves,index){
    if(!Number.isInteger(index)||index<0||index>=leaves.length)throw new RangeError("invalid leaf index");
    function rec(xs,i){
      if(xs.length===1)return [];
      const k=largestPowerLessThan(xs.length);
      if(i<k)return [{side:"right",hash:b64(treeHash(xs.slice(k)))} , ...rec(xs.slice(0,k),i)];
      return [{side:"left",hash:b64(treeHash(xs.slice(0,k)))} , ...rec(xs.slice(k),i-k)];
    }
    // rec emits siblings root-to-leaf; reverse for leaf-to-root verification.
    return Object.freeze(rec(leaves,index).reverse().map(Object.freeze));
  }
  function verifyInclusion(bytes,index,treeSize,path,rootHash){
    if(!Number.isInteger(treeSize)||treeSize<1||index<0||index>=treeSize)return false;
    let cur=leafHash(bytes);
    for(const step of path||[]){const sib=unb64(step.hash);cur=step.side==="left"?nodeHash(sib,cur):step.side==="right"?nodeHash(cur,sib):Buffer.alloc(0);if(cur.length!==32)return false;}
    return b64(cur)===rootHash;
  }
  function checkpointBytes(body){return Buffer.from(E.canonicalJson(body),"utf8");}
  class TransparencyLog{
    constructor({privateKey,publicKey,logId="holotrade-local"}={}){
      if(!privateKey||!publicKey)throw new TypeError("log Ed25519 keypair required");
      this.privateKey=privateKey;this.publicKey=publicKey;this.logId=String(logId);this.entries=[];
    }
    appendEnvelope(envelope){
      const bytes=Buffer.from(E.canonicalJson(envelope),"utf8");
      const index=this.entries.length;this.entries.push(bytes);
      return Object.freeze({index,leafHash:b64(leafHash(bytes)),envelopeDigest:`sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`});
    }
    checkpoint(issuedAt=Date.now()){
      const body={schema:`${SCHEMA}.checkpoint`,logId:this.logId,treeSize:this.entries.length,rootHash:b64(treeHash(this.entries)),issuedAt};
      const signature=crypto.sign(null,checkpointBytes(body),this.privateKey);
      return Object.freeze({...body,logKeyId:Sig.keyId(this.publicKey),signature:b64(signature)});
    }
    inclusion(index,issuedAt=Date.now()){
      if(index<0||index>=this.entries.length)throw new RangeError("invalid log index");
      const checkpoint=this.checkpoint(issuedAt);
      return Object.freeze({schema:`${SCHEMA}.bundle`,index,treeSize:this.entries.length,path:auditPath(this.entries,index),checkpoint});
    }
  }
  function verifyCheckpoint(checkpoint,logPublicKey){
    try{
      if(!checkpoint||checkpoint.schema!==`${SCHEMA}.checkpoint`)return {ok:false,code:"CHECKPOINT_SHAPE"};
      const key=logPublicKey?.type?logPublicKey:crypto.createPublicKey(logPublicKey);
      if(Sig.keyId(key)!==checkpoint.logKeyId)return {ok:false,code:"LOG_KEY_ID"};
      const body={schema:checkpoint.schema,logId:checkpoint.logId,treeSize:checkpoint.treeSize,rootHash:checkpoint.rootHash,issuedAt:checkpoint.issuedAt};
      const ok=crypto.verify(null,checkpointBytes(body),key,unb64(checkpoint.signature));
      return {ok,code:ok?"OK":"BAD_CHECKPOINT_SIGNATURE"};
    }catch(error){return {ok:false,code:"CHECKPOINT_VERIFY_ERROR",error:String(error.message||error)};}
  }
  function verifyTransparentThreshold(envelope,trustedKeys,bundle,{threshold=1,expectedPayload=null,expectedPayloadType=null,logPublicKey}={}){
    const signatures=Sig.verifyThreshold(envelope,trustedKeys,{threshold,expectedPayload,expectedPayloadType});
    if(!signatures.ok)return {ok:false,code:`DSSE_${signatures.code}`,signatures,transparency:null};
    const checkpoint=verifyCheckpoint(bundle?.checkpoint,logPublicKey);
    if(!checkpoint.ok)return {ok:false,code:checkpoint.code,signatures,transparency:checkpoint};
    const bytes=Buffer.from(E.canonicalJson(envelope),"utf8");
    const included=bundle&&bundle.treeSize===bundle.checkpoint.treeSize&&verifyInclusion(bytes,bundle.index,bundle.treeSize,bundle.path,bundle.checkpoint.rootHash);
    if(!included)return {ok:false,code:"INCLUSION_PROOF",signatures,transparency:{checkpoint,included:false}};
    return {ok:true,code:"OK",signatures,transparency:{checkpoint,included:true,logId:bundle.checkpoint.logId,treeSize:bundle.treeSize,index:bundle.index},
      externalPublicLog:false,identityVerified:false,remoteAttestationVerified:false,
      boundary:"Threshold DSSE signature plus cryptographic inclusion in a locally operated append-only Merkle log. No Rekor interoperability, public witness quorum, certificate identity, or hardware attestation is inferred."};
  }
  function signAndLog(payload,signers,log,{payloadType=Sig.PAYLOAD_TYPE,issuedAt=Date.now()}={}){
    const envelope=Sig.signDSSE(payload,signers,payloadType);const entry=log.appendEnvelope(envelope);const bundle=log.inclusion(entry.index,issuedAt);return Object.freeze({envelope,entry,bundle});
  }
  const API={SCHEMA,leafHash,nodeHash,treeHash,auditPath,verifyInclusion,TransparencyLog,verifyCheckpoint,verifyTransparentThreshold,signAndLog};
  root.HolotradeTransparency=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof window!=="undefined"?window:globalThis);
