"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const P=require("../js/w33-signed-resource-policy.js");
const M=require("../js/w33-representation-market-identity.js");
const H=require("../js/w33-representation-market-provenance.js");

const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
if(!certPath){test("W33 signed-resource certificate supplied by cross-repo CI",{skip:true},()=>{});}else{
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const d2=M.identityFromSelection(P.verifySignedResourceCertificate(cert,"exception-depth2"));
  const d3=M.identityFromSelection(P.verifySignedResourceCertificate(cert,"exception-depth3-mass24"));
  const kp=crypto.generateKeyPairSync("ed25519"), keys={market:kp.publicKey};
  function lifecycle(type,id,tag){
    const map={MIGRATION:[M.MIGRATION_SCHEMA,"representationMigrationMarketDigest"],SETTLEMENT:[M.SETTLEMENT_SCHEMA,"representationSettlementDigest"],REPLAY:[M.REPLAY_SCHEMA,"representationReplayKeyDigest"]};
    const [schema,field]=map[type];
    const body={schema,representationMarketIdentityDigest:id.representationMarketIdentityDigest,signedResourceSelectionDigest:id.selectionDigest,representationClass:id.representationClass,tag};
    return Object.freeze({...body,[field]:M.sha256(body)});
  }

  test("equal-priced depth2 cannot enter depth3 bid or provenance history",()=>{
    assert.equal(d2.representationAmplification,d3.representationAmplification);
    assert.equal(d2.signedSamplingSecondMomentFactor,d3.signedSamplingSecondMomentFactor);
    const b2=M.buildBid({workerId:"wrong-cheaper",identity:d2,priceDigest:M.sha256("p2"),totalUSD:1,pricingEpoch:4});
    const b3=M.buildBid({workerId:"right",identity:d3,priceDigest:M.sha256("p3"),totalUSD:1,pricingEpoch:4});
    const selected=M.selectBid([b2,b3],d3); assert.equal(selected.ok,true); assert.equal(selected.award.workerId,"right"); assert.equal(selected.rejected.length,1);
    let h=H.append(null,{type:"BID",artifact:b3,identity:d3,privateKey:kp.privateKey,keyId:"market"});
    h=H.append(h,{type:"AWARD",artifact:selected.award,identity:d3,privateKey:kp.privateKey,keyId:"market"});
    assert.throws(()=>H.append(h,{type:"BID",artifact:b2,identity:d3,privateKey:kp.privateKey,keyId:"market"}),/substitution/);
    assert.equal(H.verifyHistory(h,keys).ok,true);
  });

  test("bid award migration settlement replay form one signed append-only identity chain",()=>{
    const bid=M.buildBid({workerId:"w",identity:d3,priceDigest:M.sha256("quote"),totalUSD:7,pricingEpoch:9});
    const award=M.selectBid([bid],d3).award;
    const artifacts=[
      ["BID",bid],["AWARD",award],["MIGRATION",lifecycle("MIGRATION",d3,"w->w2")],
      ["SETTLEMENT",lifecycle("SETTLEMENT",d3,"settle")],["REPLAY",lifecycle("REPLAY",d3,"replay")]
    ];
    let h=null; for(const [type,artifact] of artifacts) h=H.append(h,{type,artifact,identity:d3,privateKey:kp.privateKey,keyId:"market"});
    const v=H.verifyHistory(h,keys); assert.equal(v.ok,true); assert.equal(v.eventCount,5);
    assert.deepEqual(h.events.map(e=>e.body.type),["BID","AWARD","MIGRATION","SETTLEMENT","REPLAY"]);
    for(let i=1;i<h.events.length;i++) assert.equal(h.events[i].body.previousSignedEventDigest,h.events[i-1].signedEventDigest);
    assert.throws(()=>H.append(h,{type:"REPLAY",artifact:artifacts[4][1],identity:d3,privateKey:kp.privateKey,keyId:"market"}),/duplicate lifecycle artifact/);
  });

  test("secondary price coordinates can change without changing representation history identity",()=>{
    const a=M.buildBid({workerId:"a",identity:d3,priceDigest:M.sha256("epoch1"),totalUSD:10,pricingEpoch:1});
    const b=M.buildBid({workerId:"b",identity:d3,priceDigest:M.sha256("epoch2"),totalUSD:8,pricingEpoch:2});
    assert.notEqual(a.priceDigest,b.priceDigest); assert.equal(a.representationMarketIdentityDigest,b.representationMarketIdentityDigest);
    let h=H.append(null,{type:"BID",artifact:a,identity:d3,privateKey:kp.privateKey,keyId:"market"});
    h=H.append(h,{type:"BID",artifact:b,identity:d3,privateKey:kp.privateKey,keyId:"market"});
    assert.equal(H.verifyHistory(h,keys).ok,true);
    assert.equal(h.representationMarketIdentityDigest,d3.representationMarketIdentityDigest);
  });
}
