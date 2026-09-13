"use strict";

const test=require("node:test");
const assert=require("node:assert/strict");
const crypto=require("node:crypto");

const A=require("../js/w33-measured-boot-attestation.js");
const D=require("../js/w33-passport-deployment.js");
const B=require("../js/w33-octet-decoder-binding.js");
const S=require("../scheduler/w33-continuation-scheduler.js");
const T=require("../scheduler/w33-continuation-transaction.js");
const X=require("../scheduler/w33-certified-decoder-transaction.js");

function d(x){return S.sha256(x);}
function verdict(challenge,key){return A.signVerifierVerdict({provider:A.PROVIDER.SEV_SNP,challengeDigest:challenge.challengeDigest,
  launchMeasurement:d("decoder-launch"),reportedTcbDigest:d("decoder-tcb"),signerChainDigest:d("decoder-chain"),hardwareBacked:true,
  vendorSignatureVerified:true,measurementPolicyVerified:true,tcbPolicyVerified:true,runtimeKeyBound:true,verifierKeyId:"decoder-verifier"},key);}

function fixture(){
  const deploymentDigest=d("decoder-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("decoder-passport"),deploymentDigest,machineType:"w33.decoder",logicalDimension:81,capabilityEpoch:1,revocationRoot:d("decoder-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const request=Object.freeze({continuationRoot:d("decoder-parent"),processId:d("decoder-process"),generation:7,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,requiredPoints:[0],durationSeconds:1});
  const worker=Object.freeze({id:"decoder-worker",evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d("decoder-runtime"),topology:Object.freeze({attested:true,attestationDigest:d("decoder-topology"),points:[0,1,2]}),retainedUnionDeltaBytes:{[request.continuationRoot]:0},computePerSecondUSD:0,startupUSD:0});
  const decoderPolicy=B.verifyDecoderPolicy({schema:B.POLICY_SCHEMA,decoderVersion:"octet-hybrid-v2",radiusTwoLibraryDigest:d("r2-4140"),circuitLibraryDigest:d("circuit-min"),decoderLibraryDigest:d("decoder-library"),decoderCertificateDigest:d("decoder-cert"),exactDepthCertificateDigest:d("mass28-depth-cert"),inputPreimageDigest:d("radius2-trap"),fiberDigest:d("trap-fiber"),certifiedExactDepth:1});
  const execution={schema:T.EXECUTION_SCHEMA,parentContinuationRoot:request.continuationRoot,childContinuationRoot:d("decoder-child"),processId:request.processId,generationBefore:7,generationAfter:8,emissionId:d("decoder-emission"),guestReceiptIds:[d("decoder-guest-receipt")],stopReason:"decoded"};
  return {request,worker,decoderPolicy,execution};
}

function goodReceipt(policy){return {schema:B.RECEIPT_SCHEMA,decoderPolicyDigest:policy.decoderPolicyDigest,status:"OPTIMUM",initialNegativeMass:2,finalNegativeMass:1,finalPreimageDigest:d("decoded-preimage"),steps:[{kind:"circuit",before:2,after:1,moveDigest:d("certified-circuit-move")}]};}

test("decoder library and exact-depth contract enter measured boot and signed delivery",()=>{
  const {request,worker,decoderPolicy,execution}=fixture();
  const verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519");
  let seenChallenge;
  const tx=X.executeCertifiedDecoderTransaction({candidates:[worker],request,decoderPolicy,
    obtainSignedVerifierVerdict:({challenge})=>{seenChallenge=challenge;return verdict(challenge,verifier.privateKey);},
    trustedVerifierPublicKey:verifier.publicKey,
    executeWorker:()=>({...execution,decoderReceipt:goodReceipt(decoderPolicy)}),deliveryPrivateKey:delivery.privateKey});
  assert.equal(seenChallenge.decoderPolicyDigest,decoderPolicy.decoderPolicyDigest);
  assert.equal(seenChallenge.parentChallengeDigest,tx.dispatch.challenge.challengeDigest);
  assert.equal(tx.attestation.decoderPolicyDigest,decoderPolicy.decoderPolicyDigest);
  assert.equal(tx.delivery.body.decoderPolicyDigest,decoderPolicy.decoderPolicyDigest);
  assert.equal(tx.delivery.body.decoderLibraryDigest,decoderPolicy.decoderLibraryDigest);
  assert.equal(tx.delivery.body.decoderFinalNegativeMass,1);
  assert.equal(tx.delivery.body.decoderStatus,"OPTIMUM");
  assert.equal(T.verifyDelivery(tx.delivery,delivery.publicKey).ok,true);
});

test("optimizer cannot substitute the certified radius-two local minimum",()=>{
  const {request,worker,decoderPolicy,execution}=fixture();
  const verifier=crypto.generateKeyPairSync("ed25519"),delivery=crypto.generateKeyPairSync("ed25519");
  const localMinimum={schema:B.RECEIPT_SCHEMA,decoderPolicyDigest:decoderPolicy.decoderPolicyDigest,status:"OPTIMUM",initialNegativeMass:2,finalNegativeMass:2,finalPreimageDigest:d("uncertified-local-minimum"),steps:[]};
  assert.throws(()=>X.executeCertifiedDecoderTransaction({candidates:[worker],request,decoderPolicy,
    obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
    executeWorker:()=>({...execution,decoderReceipt:localMinimum}),deliveryPrivateKey:delivery.privateKey}),/does not reach independently certified exact depth/);
});

test("changing decoder library identity changes the measured-boot challenge",()=>{
  const {request,worker,decoderPolicy}=fixture();
  const dispatch=S.chooseContinuationWorker([worker],request).dispatch;
  const c1=X.buildDecoderChallenge(dispatch,decoderPolicy);
  const p2=B.verifyDecoderPolicy({...decoderPolicy,circuitLibraryDigest:d("different-circuit-library"),decoderPolicyDigest:undefined});
  const c2=X.buildDecoderChallenge(dispatch,p2);
  assert.notEqual(p2.decoderPolicyDigest,decoderPolicy.decoderPolicyDigest);
  assert.notEqual(c2.challengeDigest,c1.challengeDigest);
});

const exactFixture=require('../analysis/octet_dual_transaction_fixture.json');
function exactCase(index=0){
  const base=fixture(),w=structuredClone(exactFixture.receipts[index]);
  w.lines=structuredClone(exactFixture.lines);
  const decoderPolicy=B.verifyDecoderPolicy({...base.decoderPolicy,decoderPolicyDigest:undefined,
    proofMode:'dual-one-step-v1',geometryDigest:d(w.lines),permittedMoveDigests:[d(w.move)],
    inputPreimageDigest:d(w.start),fiberDigest:d(w.lineImage)});
  const receipt={...goodReceipt(decoderPolicy),finalPreimageDigest:d(w.end),dualWitness:w,
    steps:[{kind:'circuit',before:2,after:1,moveDigest:d(w.move)}]};
  return {...base,decoderPolicy,receipt};
}
function executeExact(f){
  const verifier=crypto.generateKeyPairSync('ed25519'),delivery=crypto.generateKeyPairSync('ed25519');
  const tx=X.executeCertifiedDecoderTransaction({candidates:[f.worker],request:f.request,decoderPolicy:f.decoderPolicy,
    obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,
    executeWorker:()=>({...f.execution,decoderReceipt:f.receipt}),deliveryPrivateKey:delivery.privateKey});
  assert.equal(T.verifyDelivery(tx.delivery,delivery.publicKey).ok,true);
  return tx;
}
test('both actual dual witnesses are checked before signed delivery',()=>{
  for(let i=0;i<2;i++){
    const f=exactCase(i),tx=executeExact(f);
    assert.equal(tx.delivery.body.decoderDualVerified,true);
    assert.equal(tx.delivery.body.decoderDualWitnessDigest,d(f.receipt.dualWitness));
    assert.equal(tx.decoderReceipt.dualVerified,true);
  }
});
test('declared optimum cannot bypass actual vector and rational proof checks',()=>{
  const attacks=[
    f=>{delete f.receipt.dualWitness;},
    f=>{f.receipt.dualWitness.end[0]+=1;f.receipt.finalPreimageDigest=d(f.receipt.dualWitness.end);},
    f=>{f.receipt.dualWitness.start[0]+=1;},
    f=>{f.receipt.dualWitness.move[0]+=1;},
    f=>{f.receipt.dualWitness.lines[0][0]=(f.receipt.dualWitness.lines[0][0]+1)%40;},
    f=>{f.receipt.dualWitness.dual[0]='1000000000000000000000000000001/1000000000000000000000000000000';},
    f=>{f.receipt.dualWitness.dual[0]='1/0';},
    f=>{f.receipt.dualWitness.dual[0]='NaN';},
    f=>{f.receipt.steps[0].moveDigest=d('unapproved');},
    f=>{f.receipt.dualWitness.end[0]=Number.MAX_SAFE_INTEGER+1;},
    f=>{f.receipt.dualWitness=exactCase(1).receipt.dualWitness;},
  ];
  for(const attack of attacks){const f=exactCase();attack(f);assert.throws(()=>executeExact(f));}
});
test('proof requirement and permitted circuit set are committed before execution',()=>{
  const f=exactCase(),dispatch=S.chooseContinuationWorker([f.worker],f.request).dispatch;
  const p=B.verifyDecoderPolicy({...f.decoderPolicy,permittedMoveDigests:[d('other')],decoderPolicyDigest:undefined});
  assert.notEqual(X.buildDecoderChallenge(dispatch,p).challengeDigest,X.buildDecoderChallenge(dispatch,f.decoderPolicy).challengeDigest);
  assert.throws(()=>B.verifyDecoderReceipt(f.receipt,{...f.decoderPolicy,proofMode:undefined}),/decoderPolicyDigest mismatch/);
  assert.throws(()=>executeExact({...f,decoderPolicy:p,receipt:{...f.receipt,decoderPolicyDigest:p.decoderPolicyDigest}}),/unapproved/);
  const equivalent=exactCase();equivalent.receipt.dualWitness.dual=equivalent.receipt.dualWitness.dual.map(v=>String(2*Number(v))+'/2');
  assert.equal(executeExact(equivalent).decoderReceipt.dualVerified,true);
});
