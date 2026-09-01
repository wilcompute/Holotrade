"use strict";

const crypto=require("node:crypto");
const E=require("../js/evidence.js");
const FROZEN=require("../data/e8_pg34_sentinel_control_plane.json");

const PLAN_SCHEMA="holotrade.e8-pg34-sentinel-plan.v1";
function canonical(value){
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.keys(value).sort().map((k)=>`${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}`;
  return JSON.stringify(value);
}
function sha256(value){return crypto.createHash("sha256").update(canonical(value)).digest("hex");}
function deepFreeze(value){
  if(!value||typeof value!=="object"||Object.isFrozen(value))return value;
  for(const child of Object.values(value))deepFreeze(child);return Object.freeze(value);
}
function verifyFrozen(certificate=FROZEN){
  if(!certificate||certificate.schema!=="holotrade.e8-pg34-sentinel-control-plane.v1")return false;
  const {sha256:claimed,...body}=certificate;
  return sha256(body)===claimed&&certificate.carrier.states===85&&
    certificate.sentinel.parameters==="[40,15,8]_2"&&certificate.shell.fiveCircuits===216&&
    certificate.logicalArtifacts.supports.length===45&&certificate.logicalArtifacts.polarityRows.length===85;
}
if(!verifyFrozen())throw new Error("invalid PG(3,4) sentinel control-plane certificate");

function integer(value,limit,label){
  if(!Number.isInteger(value)||value<0||value>=limit)throw new RangeError(`${label} must be in [0, ${limit-1}]`);
  return value;
}
function seal(body){return deepFreeze({...body,digest:E.demoDigest(body)});}

function sentinelReservation(minimumWordId){
  integer(minimumWordId,45,"minimumWordId");
  return seal({
    schema:PLAN_SCHEMA,operation:"reserve one minimum sentinel support",
    minimumWordId,w33LogicalPoints:[...FROZEN.logicalArtifacts.supports[minimumWordId]],
    nodeCount:8,codeParameters:FROZEN.sentinel.parameters,
    sourceCertificateSha256:FROZEN.sha256,dispatchable:false,liveBindings:[],
    evidenceBoundary:"The eight entries are logical W33 positions in one exact codeword, not reserved hosts or authenticated inventory.",
  });
}

function polarityFanout(stateId){
  integer(stateId,85,"stateId");
  const absolute=stateId>=40;
  return seal({
    schema:PLAN_SCHEMA,operation:"PG(3,4) polar-plane incidence fanout",stateId,
    carrier:absolute?"GQ(4,2) absolute":"W(3,3) nonabsolute",
    destinationStateIds:[...FROZEN.logicalArtifacts.polarityRows[stateId]],fanout:21,
    containsSource: absolute,
    sourceCertificateSha256:FROZEN.sha256,dispatchable:false,liveBindings:[],
    evidenceBoundary:"This is one logical incidence row. A polarity loop is incidence of an absolute point with its polar plane, not a network self-loop.",
  });
}

function fiveCircuitParity(circuitId){
  integer(circuitId,216,"circuitId");
  const minimumWordIds=[...FROZEN.logicalArtifacts.circuits[circuitId]];
  const counts=Array(40).fill(0);
  for(const id of minimumWordIds)for(const point of FROZEN.logicalArtifacts.supports[id])counts[point]^=1;
  if(counts.some(Boolean))throw new Error("frozen circuit parity changed");
  return seal({
    schema:PLAN_SCHEMA,operation:"five-minimum-word zero-parity check",circuitId,
    minimumWordIds,xorIsZero:true,stabilizer:"S5",ambientOrbit:"PSp(4,3)/S5",
    sourceCertificateSha256:FROZEN.sha256,dispatchable:false,
    evidenceBoundary:"This is a binary dependency check among logical supports, not a cryptographic MAC, a qutrit Clifford torsor, or a hardware fault-injection result.",
  });
}

function verifyPlan(plan){
  if(!plan||plan.schema!==PLAN_SCHEMA||plan.dispatchable!==false||plan.sourceCertificateSha256!==FROZEN.sha256)return false;
  const {digest,...body}=plan;if(digest!==E.demoDigest(body))return false;
  try{
    let expected;
    if(plan.operation==="reserve one minimum sentinel support")expected=sentinelReservation(plan.minimumWordId);
    else if(plan.operation==="PG(3,4) polar-plane incidence fanout")expected=polarityFanout(plan.stateId);
    else if(plan.operation==="five-minimum-word zero-parity check")expected=fiveCircuitParity(plan.circuitId);
    else return false;
    return canonical(expected)===canonical(plan);
  }catch{return false;}
}

module.exports={PLAN_SCHEMA,verifyFrozen,sentinelReservation,polarityFanout,fiveCircuitParity,verifyPlan};
