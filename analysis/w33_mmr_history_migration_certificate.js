"use strict";

const fs=require("node:fs");
const crypto=require("node:crypto");
const path=require("node:path");

const P=require("../js/w33-signed-resource-policy.js");
const I=require("../js/w33-representation-market-identity.js");
const H=require("../js/w33-representation-market-provenance.js");
const MMR=require("../js/w33-representation-market-merkle-provenance.js");
const D=require("../js/w33-passport-deployment.js");
const S=require("../scheduler/w33-continuation-scheduler.js");

function d(label){return S.sha256(label);}
function prices(){return Object.freeze({semanticGuestStepUSD:0,w33RouteHopUSD:0,authenticatedRetainedByteTickUSD:0,
  authenticatedSweptPayloadByteUSD:0,deterministicReplayStepUSD:0,representationExcessUSD:3,samplingExcessUSD:5});}

function main(){
  const certPath=process.env.W33_SIGNED_RESOURCE_CERT;
  if(!certPath) throw new Error("W33_SIGNED_RESOURCE_CERT required");
  const cert=JSON.parse(fs.readFileSync(certPath,"utf8"));
  const selection=P.verifySignedResourceCertificate(cert,"exception-depth3-mass24");
  const identity=I.identityFromSelection(selection);
  const keys=crypto.generateKeyPairSync("ed25519");
  const bid1=I.buildBid({workerId:"mmr-cert-worker",identity,priceDigest:d("mmr-cert-price-1"),totalUSD:4,pricingEpoch:1});
  const bid2=I.buildBid({workerId:"mmr-cert-worker",identity,priceDigest:d("mmr-cert-price-2"),totalUSD:3,pricingEpoch:2});
  const h1=H.append(null,{type:"BID",artifact:bid1,identity,privateKey:keys.privateKey,keyId:"mmr-cert-market"});
  const h2=H.append(h1,{type:"BID",artifact:bid2,identity,privateKey:keys.privateKey,keyId:"mmr-cert-market"});
  const c1=MMR.commitHistory(h1), c2=MMR.commitHistory(h2), proof=MMR.consistencyProof(h1,h2);
  const verified=MMR.verifyConsistency(c1,c2,proof);
  if(!verified.ok || verified.code!=="MMR_PREFIX_CONSISTENCY_VERIFIED") throw new Error(`consistency failed: ${verified.code}`);

  const deploymentDigest=d("mmr-cert-deployment");
  const passport=Object.freeze({schema:D.SCHEMA,passportId:d("mmr-cert-passport"),deploymentDigest,machineType:"w33.circuit216.steinberg81",
    logicalDimension:81,capabilityEpoch:1,revocationRoot:d("mmr-cert-revocations")});
  const contract=Object.freeze({deploymentDigest});
  const continuationRoot=d("mmr-cert-root"),processId=d("mmr-cert-process");
  const base=Object.freeze({continuationRoot,processId,generation:12,passport,contract,evidenceFloor:S.EVIDENCE.HARDWARE_ATTESTED,
    requiredPoints:[0],durationSeconds:0,signedResourceCertificate:cert,representationClass:"exception-depth3-mass24"});
  const request1=Object.freeze({...base,representationMarketHistoryCommitment:c1});
  const request2=Object.freeze({...base,representationMarketHistoryCommitment:c2,
    representationMarketPreviousHistoryCommitment:c1,representationMarketHistoryConsistencyProof:proof});
  const candidate=(id,tag)=>Object.freeze({id,evidenceLevel:S.EVIDENCE.HARDWARE_ATTESTED,runtimePublicKeyDigest:d(`${tag}-runtime`),
    topology:Object.freeze({attested:true,attestationDigest:d(`${tag}-topology`),points:[0,1,2]}),retainedUnionDeltaBytes:{[continuationRoot]:0},
    computePerSecondUSD:0,startupUSD:0,signedResourceUnitPrices:prices()});
  const oldDispatch=S.dispatchFor(candidate("mmr-old","mmr-old"),S.normalizeRequest(request1));
  const migration=S.migrateWorker(oldDispatch,candidate("mmr-new","mmr-new"),request2);
  if(!migration.historyAdvanced || !migration.attestationMustBeRenewed) throw new Error("history advance did not force renewed attestation");
  if(migration.previousRepresentationMarketHistoryRootDigest!==c1.rootDigest || migration.representationMarketHistoryRootDigest!==c2.rootDigest) throw new Error("migration root binding mismatch");
  if(migration.previousRepresentationMarketHistoryEventCount!==1 || migration.representationMarketHistoryEventCount!==2) throw new Error("migration event-count binding mismatch");

  const tampered=JSON.parse(JSON.stringify(proof));
  tampered.extensionBlocks[0].hash=d("forged-extension-block");
  let tamperRejected=false;
  try{S.migrateWorker(oldDispatch,candidate("mmr-forged","mmr-forged"),{...request2,representationMarketHistoryConsistencyProof:tampered});}
  catch(_){tamperRejected=true;}
  if(!tamperRejected) throw new Error("tampered consistency proof was accepted");
  let missingRejected=false;
  try{S.migrateWorker(oldDispatch,candidate("mmr-missing","mmr-missing"),{...base,representationMarketHistoryCommitment:c2});}
  catch(_){missingRejected=true;}
  if(!missingRejected) throw new Error("history-root jump without proof was accepted");

  const out={
    schema:"holotrade.w33-mmr-history-migration-certificate.v1",status:"PASS",
    representationClass:selection.representationClass,representationMarketIdentityDigest:identity.representationMarketIdentityDigest,
    signedResourceSelectionDigest:selection.selectionDigest,
    oldHistoryRootDigest:c1.rootDigest,newHistoryRootDigest:c2.rootDigest,oldEventCount:c1.eventCount,newEventCount:c2.eventCount,
    oldHistoryDigest:c1.historyDigest,newHistoryDigest:c2.historyDigest,
    consistencyCode:verified.code,consistencyProofDigest:S.sha256(proof),
    oldAttestationChallengeDigest:oldDispatch.attestationChallengeDigest,newAttestationChallengeDigest:migration.newChallengeDigest,
    challengeChanged:oldDispatch.attestationChallengeDigest!==migration.newChallengeDigest,attestationMustBeRenewed:migration.attestationMustBeRenewed,
    migrationDigest:migration.migrationDigest,historyAdvanced:migration.historyAdvanced,
    adversarialChecks:{tamperedConsistencyProofRejected:tamperRejected,rootJumpWithoutProofRejected:missingRejected},
    theorem:"A continuation worker migration may advance the bound representation-market history only when the previously attested commitment is an exact MMR prefix of the new commitment. The accepted advance strictly increases event count, changes the measured-boot continuation challenge, and therefore requires fresh attestation.",
    boundary:"This certificate authenticates append-only software provenance and execution-context binding. It does not claim physical immutability, consensus finality, or economic correctness of the underlying bids."
  };
  const outPath=path.join(__dirname,"w33_mmr_history_migration_certificate.json");
  fs.writeFileSync(outPath,JSON.stringify(out,null,2)+"\n");
  console.log(JSON.stringify(out,null,2));
  console.log(`written: ${outPath}`);
}

main();
