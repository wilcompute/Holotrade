"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const P=require("../js/w33-signed-resource-policy.js");
const M=require("../js/w33-representation-market-identity.js");
const H=require("../js/w33-representation-market-provenance.js");
const T=require("../js/w33-representation-market-merkle-provenance.js");

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if(!certPath){test("W33 signed-resource certificate supplied by cross-repo CI",{skip:true},()=>{});}else{
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const d2=M.identityFromSelection(P.verifySignedResourceCertificate(cert,"exception-depth2"));
  const d3=M.identityFromSelection(P.verifySignedResourceCertificate(cert,"exception-depth3-mass24"));
  const kp=crypto.generateKeyPairSync("ed25519");
  function lifecycle(type,id,tag){
    const map={MIGRATION:[M.MIGRATION_SCHEMA,"representationMigrationMarketDigest"],SETTLEMENT:[M.SETTLEMENT_SCHEMA,"representationSettlementDigest"],REPLAY:[M.REPLAY_SCHEMA,"representationReplayKeyDigest"]};
    const [schema,field]=map[type];
    const body={schema,representationMarketIdentityDigest:id.representationMarketIdentityDigest,signedResourceSelectionDigest:id.selectionDigest,representationClass:id.representationClass,tag};
    return Object.freeze({...body,[field]:M.sha256(body)});
  }
  function buildHistory(id){
    const bid=M.buildBid({workerId:"w",identity:id,priceDigest:M.sha256("quote"),totalUSD:7,pricingEpoch:9});
    const award=M.selectBid([bid],id).award;
    const artifacts=[["BID",bid],["AWARD",award],["MIGRATION",lifecycle("MIGRATION",id,"w->w2")],["SETTLEMENT",lifecycle("SETTLEMENT",id,"settle")],["REPLAY",lifecycle("REPLAY",id,"replay")]];
    let h=null;const prefixes=[];
    for(const [type,artifact] of artifacts){h=H.append(h,{type,artifact,identity:id,privateKey:kp.privateKey,keyId:"market"});prefixes.push(h);}
    return {h,prefixes,artifacts};
  }

  test("MMR inclusion proof authenticates one signed lifecycle event in logarithmic path length",()=>{
    const {h}=buildHistory(d3),c=T.commitHistory(h),p=T.inclusionProof(h,2);
    const v=T.verifyInclusion(c,h.events[2].signedEventDigest,p);
    assert.equal(v.ok,true);assert.equal(v.index,2);
    assert.ok(p.siblings.length<=Math.ceil(Math.log2(h.eventCount)));
    assert.ok(p.peaks.length<=Math.ceil(Math.log2(h.eventCount+1)));
    const wrong=h.events[1].signedEventDigest;
    assert.equal(T.verifyInclusion(c,wrong,p).ok,false);
  });

  test("MMR consistency proof proves an old signed history is an exact prefix of a longer one",()=>{
    const {h,prefixes}=buildHistory(d3),old=prefixes[1];
    const co=T.commitHistory(old),cn=T.commitHistory(h),p=T.consistencyProof(old,h);
    const v=T.verifyConsistency(co,cn,p);assert.equal(v.ok,true);assert.equal(v.oldEventCount,2);assert.equal(v.newEventCount,5);
    assert.ok(p.oldPeaks.length+p.extensionBlocks.length<=2*Math.ceil(Math.log2(h.eventCount+1))+1);
  });

  test("same economic factors do not make distinct representation histories Merkle-substitutable",()=>{
    assert.equal(d2.representationAmplification,d3.representationAmplification);
    assert.equal(d2.signedSamplingSecondMomentFactor,d3.signedSamplingSecondMomentFactor);
    const a=buildHistory(d2).h,b=buildHistory(d3).h,ca=T.commitHistory(a),cb=T.commitHistory(b);
    assert.notEqual(ca.representationMarketIdentityDigest,cb.representationMarketIdentityDigest);
    assert.notEqual(ca.rootDigest,cb.rootDigest);
    const p=T.inclusionProof(b,0);
    assert.equal(T.verifyInclusion(cb,a.events[0].signedEventDigest,p).ok,false);
    assert.throws(()=>T.consistencyProof(a,b),/not prefix-related/);
  });

  test("tampering with an MMR sibling or extension block is detected",()=>{
    const {h,prefixes}=buildHistory(d3),c=T.commitHistory(h),inc=T.inclusionProof(h,3);
    const badInc=structuredClone(inc);badInc.siblings[0].hash=T.sha256("tampered");
    assert.equal(T.verifyInclusion(c,h.events[3].signedEventDigest,badInc).ok,false);
    const old=prefixes[0],co=T.commitHistory(old),con=T.consistencyProof(old,h),badCon=structuredClone(con);
    badCon.extensionBlocks[0].hash=T.sha256("tampered-block");
    assert.equal(T.verifyConsistency(co,c,badCon).ok,false);
  });
}
