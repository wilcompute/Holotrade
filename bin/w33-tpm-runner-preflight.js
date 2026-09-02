#!/usr/bin/env node
"use strict";

// Non-secret preflight for the self-hosted [linux,w33-tpm] runner.  It checks
// capabilities and file readability only; it never prints config contents,
// TPM secrets, private keys, or credential blobs.
const fs=require("node:fs");
const {spawnSync}=require("node:child_process");
const path=require("node:path");

function command(name){
  const p=spawnSync("bash",["-lc",`command -v ${name}`],{encoding:"utf8"});
  return {ok:p.status===0,path:(p.stdout||"").trim()||null};
}
function file(p,kind="file"){
  try{
    const s=fs.statSync(p);
    return {ok:kind==="char"?s.isCharacterDevice():s.isFile(),path:p,bytes:s.size,mode:(s.mode&0o777).toString(8)};
  }catch(e){return {ok:false,path:p,error:e.code||e.message};}
}
function readable(p){try{fs.accessSync(p,fs.constants.R_OK);return {ok:true,path:p};}catch(e){return {ok:false,path:p,error:e.code||e.message};}}
function main(){
  const enrollment=process.argv[2]||"/etc/holotrade/w33-tpm-enrollment.json";
  const capture=process.argv[3]||"/etc/holotrade/w33-host-capture.json";
  const tools={};
  for(const n of ["node","tpm2_makecredential","tpm2_activatecredential","tpm2_startauthsession","tpm2_policysecret","tpm2_flushcontext","tpm2_quote","tpm2_pcrread"])tools[n]=command(n);
  const tpm0=file("/dev/tpm0","char"),tpmrm=file("/dev/tpmrm0","char");
  const eventLog=readable("/sys/kernel/security/tpm0/binary_bios_measurements");
  const configs={enrollment:readable(path.resolve(enrollment)),capture:readable(path.resolve(capture))};
  const raplCandidates=["/sys/class/powercap/intel-rapl:0/energy_uj","/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj"];
  const rapl=raplCandidates.map(readable);
  const requiredTools=["tpm2_makecredential","tpm2_activatecredential","tpm2_startauthsession","tpm2_policysecret","tpm2_flushcontext","tpm2_quote","tpm2_pcrread"];
  const checks={
    requiredTools:requiredTools.every(x=>tools[x].ok),
    tpmCharacterDevice:tpm0.ok||tpmrm.ok,
    measuredBootEventLog:eventLog.ok,
    enrollmentConfig:configs.enrollment.ok,
    captureConfig:configs.capture.ok,
    physicalEnergyInput:rapl.some(x=>x.ok),
  };
  const report={schema:"holotrade.w33-tpm-runner-preflight.v1",hostname:require("node:os").hostname(),platform:process.platform,arch:process.arch,node:process.version,runnerName:process.env.RUNNER_NAME||null,runnerLabelsExpected:["self-hosted","linux","w33-tpm"],tools,devices:{tpm0,tpmrm},eventLog,configs,rapl,checks,ok:Object.values(checks).every(Boolean),boundary:"Capability-only report. No config contents, keys, secrets, TPM blobs, quote bytes or event-log contents are emitted."};
  process.stdout.write(JSON.stringify(report,null,2)+"\n");
  return report.ok?0:1;
}
process.exitCode=main();
