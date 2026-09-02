#!/usr/bin/env node
"use strict";

// Linux-host collector for a real W33 portable audit bundle.  It consumes an
// already-signed measured receipt plus raw TPM quote/signature/event-log bytes,
// authority/passport histories, and physical RAPL/Kepler telemetry.  After
// writing the bundle it invokes bin/w33-verify-receipt.js as the sole acceptance
// oracle.

const fs=require("node:fs");
const path=require("node:path");
const {spawnSync}=require("node:child_process");
const Host=require("../js/w33-host-audit-bundle.js");

function readJson(p){return JSON.parse(fs.readFileSync(path.resolve(p),"utf8"));}
function readText(p){return fs.readFileSync(path.resolve(p),"utf8");}
function read64(p){return fs.readFileSync(path.resolve(p)).toString("base64");}
function numberFromFile(p){return Number(readText(p).trim());}
function die(msg){console.error(msg);process.exit(2);}

const [, , configPath]=process.argv;
if(!configPath) die("usage: node bin/w33-capture-host-bundle.js <config.json>");
try{
  const c=readJson(configPath);
  const telemetry=Host.normalizeTelemetry({
    nodeId:c.nodeId||null,
    window:c.window||null,
    rapl:c.rapl?{
      beforeUj:c.rapl.beforeUj??numberFromFile(c.rapl.beforeUjPath),
      afterUj:c.rapl.afterUj??numberFromFile(c.rapl.energyUjPath||"/sys/class/powercap/intel-rapl:0/energy_uj"),
      maxRangeUj:c.rapl.maxRangeUj??(c.rapl.maxRangeUjPath?numberFromFile(c.rapl.maxRangeUjPath):null),
    }:null,
    kepler:c.kepler?{
      beforeText:readText(c.kepler.beforeTextPath),
      afterText:readText(c.kepler.afterTextPath),
      metric:c.kepler.metric||"kepler_node_platform_joules_total",
    }:null,
    strongRoot:c.strongRootSummaryPath?readJson(c.strongRootSummaryPath):null,
  });
  const hardware={
    provider:"TPM2",
    rawEventLogBase64:read64(c.tpm.rawEventLogPath||"/sys/kernel/security/tpm0/binary_bios_measurements"),
    attestationBase64:read64(c.tpm.attestationPath),
    tpmtSignatureBase64:read64(c.tpm.tpmtSignaturePath),
    akPublicKeyPem:readText(c.tpm.akPublicKeyPath),
    challenge:readJson(c.tpm.challengePath),
    akTrust:c.tpm.akTrust||"LINUX_HOST_AK",
  };
  const trustedKey=readText(c.trustedReceiptPublicKeyPath);
  const bundle=Host.buildHostBundle({
    signedReceipt:readJson(c.signedReceiptPath),
    passport:readJson(c.passportPath),
    epochCertificates:readJson(c.epochCertificatesPath),
    authorityPublicKeys:readJson(c.authorityPublicKeysPath),
    gcEvolution:readJson(c.gcEvolutionPath),
    magicEvents:readJson(c.magicEventsPath),
    concurrency:c.concurrencyPath?readJson(c.concurrencyPath):null,
    context:c.contextPath?readJson(c.contextPath):null,
    hardware,telemetry,
  },trustedKey);
  const output=path.resolve(c.outputPath||"w33-host-bundle.json");
  fs.writeFileSync(output,`${JSON.stringify(bundle,null,2)}\n`,{mode:0o600});
  const verifyCli=path.resolve(__dirname,"w33-verify-receipt.js");
  const child=spawnSync(process.execPath,[verifyCli,output,path.resolve(c.trustedReceiptPublicKeyPath)],{encoding:"utf8"});
  process.stdout.write(child.stdout||"");
  if(child.stderr) process.stderr.write(child.stderr);
  process.exit(child.status===0?0:1);
}catch(error){
  process.stdout.write(`${JSON.stringify({ok:false,code:"W33_HOST_BUNDLE_CAPTURE_ERROR",error:error.message},null,2)}\n`);
  process.exit(1);
}
