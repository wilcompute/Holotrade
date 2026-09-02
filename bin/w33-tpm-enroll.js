#!/usr/bin/env node
"use strict";
const fs=require("node:fs");
const path=require("node:path");
const A=require("../js/w33-tpm-credential-activation.js");

function die(msg){ console.error(msg); process.exit(2); }
const [, , configPath]=process.argv;
if(!configPath) die("usage: node bin/w33-tpm-enroll.js <config.json>");
try{
  const cfg=JSON.parse(fs.readFileSync(path.resolve(configPath),"utf8"));
  const key=cfg.enrollmentSigningKeyPath ? fs.readFileSync(path.resolve(cfg.enrollmentSigningKeyPath),"utf8") : null;
  const result=A.executeCredentialActivation({
    ekPublicPath:cfg.ekPublicPath,
    akNamePath:cfg.akNamePath,
    akContext:cfg.akContext,
    ekContext:cfg.ekContext,
    akAuth:cfg.akAuth||null,
    tcti:cfg.tcti||null,
    enrollmentSigningKey:key,
    enrollmentKeyId:cfg.enrollmentKeyId||"w33-enrollment",
    workDir:cfg.workDir||null,
  });
  process.stdout.write(`${JSON.stringify(result,null,2)}\n`);
  process.exit(result.ok?0:1);
}catch(error){
  process.stdout.write(`${JSON.stringify({ok:false,code:"TPM_ENROLLMENT_CLI_ERROR",error:error.message},null,2)}\n`);
  process.exit(1);
}
