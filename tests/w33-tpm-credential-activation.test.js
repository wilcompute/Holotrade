"use strict";
const assert=require("node:assert/strict");
const crypto=require("node:crypto");
const fs=require("node:fs");
const os=require("node:os");
const path=require("node:path");
const test=require("node:test");
const A=require("../js/w33-tpm-credential-activation.js");

function fixtureRunner({wrongSecret=false}={}){
  let secretPath=null;
  return function runner(command,args,{cwd}){
    const out=(flag)=>{const i=args.indexOf(flag);return i>=0?args[i+1]:null;};
    if(command==="tpm2_makecredential"){
      secretPath=out("-s"); fs.writeFileSync(out("-o"),Buffer.from("credential-blob"));
    }else if(command==="tpm2_startauthsession"){
      fs.writeFileSync(out("-S"),Buffer.from("session"));
    }else if(command==="tpm2_activatecredential"){
      const secret=fs.readFileSync(secretPath);
      fs.writeFileSync(out("-o"),wrongSecret?Buffer.alloc(secret.length,9):secret);
    }else if(command==="tpm2_flushcontext"){
      // no-op fixture; production invokes the real tool.
    }
    return {status:0,stdout:"",stderr:""};
  };
}

function setup(){
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),"w33-tpm-test-"));
  const ek=path.join(dir,"ek.pub"), name=path.join(dir,"ak.name");
  fs.writeFileSync(ek,Buffer.from("fixture-ek-public"));
  fs.writeFileSync(name,Buffer.from("fixture-ak-name"));
  return {dir,ek,name};
}

test("credential activation executes make/session/policy/activate/flush and signs transcript",()=>{
  const f=setup(); const keys=crypto.generateKeyPairSync("ed25519");
  const result=A.executeCredentialActivation({
    ekPublicPath:f.ek,akNamePath:f.name,akContext:"ak.ctx",ekContext:"0x81010001",
    secret:Buffer.alloc(32,7),runner:fixtureRunner(),enrollmentSigningKey:keys.privateKey,workDir:f.dir,
  });
  assert.equal(result.ok,true);
  assert.equal(result.body.hardwareBacked,false);
  assert.deepEqual(result.body.commands.map(x=>x.command),[
    "tpm2_makecredential","tpm2_startauthsession","tpm2_policysecret","tpm2_activatecredential","tpm2_flushcontext"
  ]);
  assert.equal(result.body.secretDigest,result.body.recoveredSecretDigest);
  assert.equal(A.verifyTranscriptReceipt(result.receipt,keys.publicKey),true);
});

test("credential activation refuses a wrong recovered registrar secret",()=>{
  const f=setup();
  assert.throws(()=>A.executeCredentialActivation({
    ekPublicPath:f.ek,akNamePath:f.name,akContext:"ak.ctx",ekContext:"0x81010001",
    secret:Buffer.alloc(32,3),runner:fixtureRunner({wrongSecret:true}),workDir:f.dir,
  }),/wrong secret/);
});
