"use strict";

// Attested transaction path for the certified W33 octet decoder.
//
// The ordinary continuation scheduler first fixes worker/process/topology/etc.
// A nested measured-boot challenge then commits that exact parent challenge and
// the content-addressed decoder policy (library/version/input/fiber/exact-depth
// certificate).  The worker's decoder receipt is verified after execution and
// only OPTIMUM receipts ending at the independently certified exact depth are
// admitted to the signed delivery.  This prevents a worker from substituting a
// radius-two local minimum for the certified decoded result.

const A = require("../js/w33-measured-boot-attestation.js");
const B = require("../js/w33-octet-decoder-binding.js");
const S = require("./w33-continuation-scheduler.js");
const T = require("./w33-continuation-transaction.js");

const CHALLENGE_SCHEMA = "holotrade.w33-octet-decoder-attestation-challenge.v1";
const BINDING_SCHEMA = "holotrade.w33-octet-decoder-attestation-binding.v1";
const TRANSACTION_SCHEMA = "holotrade.w33-certified-decoder-transaction.v1";
const PARENT_CONTEXT_FIELDS = Object.freeze([
  "executionPolicyDigest","strictAdmissionBindingDigest","acceleratorCertificateDigest",
  "signedResourceCertificateDigest","signedResourceSelectionDigest","representationMarketIdentityDigest",
  "representationMarketHistoryRootDigest","topologyAttestationDigest","failureAssessmentDigest",
]);

function buildDecoderChallenge(dispatch, decoderPolicy) {
  if (!dispatch || !dispatch.challenge || !dispatch.challenge.challengeDigest) throw new TypeError("continuation dispatch challenge required");
  const policy=B.verifyDecoderPolicy(decoderPolicy);
  const parent=dispatch.challenge;
  const body={
    schema:CHALLENGE_SCHEMA,
    parentChallengeDigest:parent.challengeDigest,
    dispatchDigest:dispatch.dispatchDigest,
    passportId:parent.passportId,
    deploymentDigest:parent.deploymentDigest,
    runtimePublicKeyDigest:parent.runtimePublicKeyDigest,
    continuationRoot:parent.continuationRoot,
    processId:parent.processId,
    generation:parent.generation,
    decoderPolicyDigest:policy.decoderPolicyDigest,
  };
  return Object.freeze({ ...body, challengeDigest:A.sha256(body), decoderPolicy:policy });
}

function verifiedDecoderBinding(dispatch, challenge, signedVerdict, trustedVerifierPublicKey) {
  if (!challenge || challenge.schema!==CHALLENGE_SCHEMA) throw new TypeError("decoder attestation challenge required");
  if (challenge.parentChallengeDigest!==dispatch.challenge.challengeDigest || challenge.dispatchDigest!==dispatch.dispatchDigest) throw new Error("decoder challenge parent-dispatch drift");
  const v=A.verifyVerifierVerdict(signedVerdict,challenge,trustedVerifierPublicKey,{requireHardware:true});
  if (!v.ok) throw new Error(`refusing unattested decoder execution: ${v.code}`);
  const parent=dispatch.challenge;
  for (const k of ["passportId","deploymentDigest","runtimePublicKeyDigest","continuationRoot","processId","generation"]) {
    if (challenge[k]!==parent[k]) throw new Error(`decoder challenge ${k} drift`);
  }
  const inherited={};
  for (const k of PARENT_CONTEXT_FIELDS) if (parent[k]!=null) inherited[k]=parent[k];
  const body={
    schema:BINDING_SCHEMA,
    parentChallengeDigest:challenge.parentChallengeDigest,
    challengeDigest:challenge.challengeDigest,
    dispatchDigest:dispatch.dispatchDigest,
    passportId:challenge.passportId,
    deploymentDigest:challenge.deploymentDigest,
    runtimePublicKeyDigest:challenge.runtimePublicKeyDigest,
    continuationRoot:challenge.continuationRoot,
    processId:challenge.processId,
    generation:challenge.generation,
    ...inherited,
    decoderPolicyDigest:challenge.decoderPolicyDigest,
    provider:signedVerdict.body.provider,
    launchMeasurement:signedVerdict.body.launchMeasurement,
    reportedTcbDigest:signedVerdict.body.reportedTcbDigest,
    signerChainDigest:signedVerdict.body.signerChainDigest,
    verifierKeyId:signedVerdict.body.verifierKeyId,
    verifierVerdictDigest:v.verdictDigest,
    hardwareBacked:true,
  };
  return Object.freeze({ ...body, bindingDigest:A.sha256(body) });
}

function executeCertifiedDecoderTransaction({
  candidates, request, decoderPolicy, policy={}, obtainSignedVerifierVerdict,
  trustedVerifierPublicKey, executeWorker, deliveryPrivateKey, deliveryKeyId="holotrade-decoder-delivery"
}) {
  if (typeof obtainSignedVerifierVerdict!=="function") throw new TypeError("obtainSignedVerifierVerdict callback required");
  if (typeof executeWorker!=="function") throw new TypeError("executeWorker callback required");
  const verifiedPolicy=B.verifyDecoderPolicy(decoderPolicy);
  const selected=S.chooseContinuationWorker(candidates,request,policy);
  if (!selected.ok) throw new Error(selected.code);
  const dispatch=selected.dispatch, normalizedRequest=selected.ranked.request;
  const challenge=buildDecoderChallenge(dispatch,verifiedPolicy);
  const verdict=obtainSignedVerifierVerdict(Object.freeze({challenge,dispatch,request:normalizedRequest,decoderPolicy:verifiedPolicy}));
  if (!verdict) throw new TypeError("verifier callback returned no signed decoder verdict");
  const binding=verifiedDecoderBinding(dispatch,challenge,verdict,trustedVerifierPublicKey);
  const raw=executeWorker(Object.freeze({dispatch,binding,request:normalizedRequest,decoderPolicy:verifiedPolicy}));
  if (!raw || !raw.decoderReceipt) throw new TypeError("worker must return decoderReceipt");
  const decoderReceipt=B.verifyDecoderReceipt(raw.decoderReceipt,verifiedPolicy);
  const execution=T.normalizeExecution(raw,normalizedRequest);
  const base=T.deliveryBody(dispatch,binding,execution);
  const bare={...base}; delete bare.deliveryDigest;
  const augmented={
    ...bare,
    decoderPolicyDigest:verifiedPolicy.decoderPolicyDigest,
    decoderAttestationChallengeDigest:challenge.challengeDigest,
    decoderAttestationBindingDigest:binding.bindingDigest,
    decoderCertificateDigest:verifiedPolicy.decoderCertificateDigest,
    decoderLibraryDigest:verifiedPolicy.decoderLibraryDigest,
    decoderVersion:verifiedPolicy.decoderVersion,
    exactDepthCertificateDigest:verifiedPolicy.exactDepthCertificateDigest,
    certifiedExactDepth:verifiedPolicy.certifiedExactDepth,
    decoderResultDigest:decoderReceipt.decoderResultDigest,
    decoderFinalNegativeMass:decoderReceipt.finalNegativeMass,
    decoderStatus:decoderReceipt.status,
  };
  const delivery=Object.freeze({...augmented,deliveryDigest:T.sha256(augmented)});
  const signedDelivery=T.signDelivery(delivery,deliveryPrivateKey,deliveryKeyId);
  const txBody={schema:TRANSACTION_SCHEMA,dispatchDigest:dispatch.dispatchDigest,decoderPolicyDigest:verifiedPolicy.decoderPolicyDigest,
    decoderAttestationBindingDigest:binding.bindingDigest,executionDigest:execution.executionDigest,decoderResultDigest:decoderReceipt.decoderResultDigest,
    signedReceiptDigest:signedDelivery.signedReceiptDigest};
  return Object.freeze({ok:true,code:"CERTIFIED_DECODER_TRANSACTION_COMMITTED",schema:TRANSACTION_SCHEMA,dispatch,decoderPolicy:verifiedPolicy,
    decoderChallenge:challenge,attestation:binding,execution,decoderReceipt,delivery:signedDelivery,transactionDigest:T.sha256(txBody)});
}

module.exports={ CHALLENGE_SCHEMA,BINDING_SCHEMA,TRANSACTION_SCHEMA,buildDecoderChallenge,verifiedDecoderBinding,executeCertifiedDecoderTransaction };
