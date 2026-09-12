"use strict";

// Deterministic end-to-end provenance certificate for the certified W33 octet
// decoder.  Unlike the regression test, this uses fixed TEST-ONLY Ed25519 seeds
// so all challenge/binding/delivery digests are reproducible and can be frozen.

const fs=require("node:fs");
const path=require("node:path");
const crypto=require("node:crypto");
const A=require("../js/w33-measured-boot-attestation.js");
const D=require("../js/w33-passport-deployment.js");
const B=require("../js/w33-octet-decoder-binding.js");
const S=require("../scheduler/w33-continuation-scheduler.js");
const T=require("../scheduler/w33-continuation-transaction.js");
const X=require("../scheduler/w33-certified-decoder-transaction.js");

function d(x){return S.sha256(x);}
function fixedEd25519(byte){
  const seed=Buffer.alloc(32,byte);
  const der=Buffer.concat([Buffer.from("302e020100300506032b657004220420","hex"),seed]);
  const privateKey=crypto.createPrivateKey({key:der,format:"der",type:"pkcs8"});
  return {privateKey,publicKey:crypto.createPublicKey(privateKey)};
}
function verdict(challenge,key){return A.signVerifierVerdict({provider:A.PROVIDER.SEV_SNP,challengeDigest:challenge.challengeDigest,
  launchMeasurement:d("decoder-launch"),reportedTcbDigest:d("decoder-tcb"),signerChainDigest:d("decoder-chain"),hardwareBacked:true,
  vendorSignatureVerified:true,measurementPolicyVerified:true,tcbPolicyVerified:true,runtimeKeyBound:true,verifierKeyId:"decoder-verifier"},key);}

function main(){
  const here=__dirname;
  const hybrid=JSON.parse(fs.readFileSync(path.join(here,"octet_hybrid_certified_decoder_certificate.json"),"utf8"));
  const trap=JSON.parse(fs.readFileSync(path.join(here,"octet_circuit_decoder_trap_certificate.json"),"utf8"));
  const minlib=JSON.parse(fs.readFileSync(path.join(here,"octet_circuit_library_minimization_certificate.json"),"utf8"));
  if(hybrid.status!=="PASS"||hybrid.schema!=="holotrade.octet-hybrid-certified-decoder.v3")throw new Error("hybrid v3 certificate required");
  if(minlib.status!=="PASS"||hybrid.circuitLibraryDigest!==minlib.minimalLibraryDigest||hybrid.signedCircuitMoveCount!==1080)throw new Error("minimal circuit library drift");
  if(trap.status!=="PASS"||trap.traps.length!==2)throw new Error("frozen radius-two trap certificate required");

  const deploymentDigest=d("decoder-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("decoder-passport"),deploymentDigest,machineType:"w33.decoder",logicalDimension:81,capabilityEpoch:1,revocationRoot:d("decoder-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const request=Object.freeze({continuationRoot:d("decoder-parent"),processId:d("decoder-process"),generation:7,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,requiredPoints:[0],durationSeconds:1});
  const worker=Object.freeze({id:"decoder-worker",evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d("decoder-runtime"),topology:Object.freeze({attested:true,attestationDigest:d("decoder-topology"),points:[0,1,2]}),retainedUnionDeltaBytes:{[request.continuationRoot]:0},computePerSecondUSD:0,startupUSD:0});
  const selectedTrap=trap.traps.find(x=>x.orientation===1)||trap.traps[0];
  const decoderPolicy=B.verifyDecoderPolicy({schema:B.POLICY_SCHEMA,decoderVersion:"octet-hybrid-v3-minimal-1080",radiusTwoLibraryDigest:hybrid.radiusTwoLibraryDigest,circuitLibraryDigest:hybrid.circuitLibraryDigest,
    decoderLibraryDigest:d({radiusTwoLibraryDigest:hybrid.radiusTwoLibraryDigest,circuitLibraryDigest:hybrid.circuitLibraryDigest}),decoderCertificateDigest:d(hybrid),exactDepthCertificateDigest:d(trap),
    inputPreimageDigest:d(selectedTrap.witness),fiberDigest:d(selectedTrap.lineImage),certifiedExactDepth:1});
  const execution={schema:T.EXECUTION_SCHEMA,parentContinuationRoot:request.continuationRoot,childContinuationRoot:d("decoder-child"),processId:request.processId,generationBefore:7,generationAfter:8,emissionId:d("decoder-emission"),guestReceiptIds:[d("decoder-guest-receipt")],stopReason:"decoded"};
  const goodReceipt={schema:B.RECEIPT_SCHEMA,decoderPolicyDigest:decoderPolicy.decoderPolicyDigest,status:"OPTIMUM",initialNegativeMass:2,finalNegativeMass:1,finalPreimageDigest:d("decoded-preimage"),steps:[{kind:"circuit",before:2,after:1,moveDigest:d("certified-circuit-move")} ]};
  const verifier=fixedEd25519(1),delivery=fixedEd25519(2);
  let seenChallenge;
  const tx=X.executeCertifiedDecoderTransaction({candidates:[worker],request,decoderPolicy,
    obtainSignedVerifierVerdict:({challenge})=>{seenChallenge=challenge;return verdict(challenge,verifier.privateKey);},trustedVerifierPublicKey:verifier.publicKey,
    executeWorker:()=>({...execution,decoderReceipt:goodReceipt}),deliveryPrivateKey:delivery.privateKey,deliveryKeyId:"deterministic-test-delivery"});
  const deliveryCheck=T.verifyDelivery(tx.delivery,delivery.publicKey); if(!deliveryCheck.ok)throw new Error("signed delivery verification failed");

  let attackRejected=false,attackMessage="";
  const localMinimum={schema:B.RECEIPT_SCHEMA,decoderPolicyDigest:decoderPolicy.decoderPolicyDigest,status:"OPTIMUM",initialNegativeMass:2,finalNegativeMass:2,finalPreimageDigest:d("uncertified-local-minimum"),steps:[]};
  try{
    X.executeCertifiedDecoderTransaction({candidates:[worker],request,decoderPolicy,obtainSignedVerifierVerdict:({challenge})=>verdict(challenge,verifier.privateKey),trustedVerifierPublicKey:verifier.publicKey,executeWorker:()=>({...execution,decoderReceipt:localMinimum}),deliveryPrivateKey:delivery.privateKey});
  }catch(e){attackMessage=String(e&&e.message||e);attackRejected=/does not reach independently certified exact depth/.test(attackMessage);}
  if(!attackRejected)throw new Error("local-minimum substitution attack was not rejected");

  const dispatch=S.chooseContinuationWorker([worker],request).dispatch;
  const c1=X.buildDecoderChallenge(dispatch,decoderPolicy);
  const mutated=B.verifyDecoderPolicy({...decoderPolicy,circuitLibraryDigest:d("different-circuit-library"),decoderPolicyDigest:undefined});
  const c2=X.buildDecoderChallenge(dispatch,mutated);
  if(mutated.decoderPolicyDigest===decoderPolicy.decoderPolicyDigest||c1.challengeDigest===c2.challengeDigest)throw new Error("decoder library mutation did not alter measured-boot challenge");

  const chain={decoderPolicyDigest:decoderPolicy.decoderPolicyDigest,decoderAttestationChallengeDigest:seenChallenge.challengeDigest,
    decoderAttestationBindingDigest:tx.attestation.bindingDigest,decoderResultDigest:tx.decoderReceipt.decoderResultDigest,
    deliveryDigest:tx.delivery.body.deliveryDigest,signedReceiptDigest:tx.delivery.signedReceiptDigest,transactionDigest:tx.transactionDigest};
  const agreement={challengeCarriesPolicy:seenChallenge.decoderPolicyDigest===decoderPolicy.decoderPolicyDigest,
    bindingCarriesPolicy:tx.attestation.decoderPolicyDigest===decoderPolicy.decoderPolicyDigest,deliveryCarriesPolicy:tx.delivery.body.decoderPolicyDigest===decoderPolicy.decoderPolicyDigest,
    deliveryCarriesLibrary:tx.delivery.body.decoderLibraryDigest===decoderPolicy.decoderLibraryDigest,deliveryCarriesExactDepth:tx.delivery.body.certifiedExactDepth===1,
    deliveryCarriesResult:tx.delivery.body.decoderResultDigest===tx.decoderReceipt.decoderResultDigest,signedDeliveryVerifies:deliveryCheck.ok};
  if(!Object.values(agreement).every(Boolean))throw new Error("decoder provenance agreement failure");

  const out={schema:"holotrade.w33-certified-decoder-provenance.v1",status:"PASS",
    historicalGreenRun:{workflowRunId:34643511926,workflowJobId:103408680746,headSha:"9185d063d67870a71a867ee65a3d626d7fa19baa",focusedTestsPassed:3,focusedTestsFailed:0,
      testNames:["decoder library and exact-depth contract enter measured boot and signed delivery","optimizer cannot substitute the certified radius-two local minimum","changing decoder library identity changes the measured-boot challenge"]},
    decoder:{version:decoderPolicy.decoderVersion,radiusTwoMoveCount:hybrid.radiusTwoMoveCount,circuitMoveCount:hybrid.signedCircuitMoveCount,radiusTwoLibraryDigest:hybrid.radiusTwoLibraryDigest,circuitLibraryDigest:hybrid.circuitLibraryDigest,decoderLibraryDigest:decoderPolicy.decoderLibraryDigest,certifiedExactDepth:1},
    digestChain:chain,agreement,
    adversarialRegression:{radiusTwoLocalMinimumSubstitutionRejected:attackRejected,rejectionMessage:attackMessage,libraryIdentityMutationChangesPolicyDigest:true,libraryIdentityMutationChangesMeasuredBootChallenge:true,mutatedPolicyDigest:mutated.decoderPolicyDigest,mutatedChallengeDigest:c2.challengeDigest},
    theorem:"The content-addressed certified decoder identity is committed before execution into measured boot, propagated through the verified hardware binding, checked against an independently certified exact depth after execution, and carried into signed delivery. A worker cannot substitute the known radius-two local minimum at negativity 2 for the certified depth-1 result, and changing the circuit-library identity changes the measured-boot challenge.",
    boundary:"Cryptographic/software attestation and exact integer-decoder provenance only. This is not evidence of physical fault tolerance, hardware energy advantage, or quantum speedup."};
  const p=path.join(here,"w33_certified_decoder_provenance_certificate.json"); fs.writeFileSync(p,JSON.stringify(out,null,2)+"\n");
  console.log(JSON.stringify({status:out.status,decoder:out.decoder,digestChain:out.digestChain,adversarialRegression:out.adversarialRegression},null,2));
  console.log(`written: ${p}`);
}
main();
