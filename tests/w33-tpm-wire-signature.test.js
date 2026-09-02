"use strict";
const assert=require("node:assert/strict"), crypto=require("node:crypto"), test=require("node:test");
const N=require("../js/w33-native-attestation.js"), P=require("../js/w33-tpm-eventlog-provenance.js"), W=require("../js/w33-tpm-wire-signature.js");
function d(x){return `sha256:${crypto.createHash("sha256").update(x).digest("hex")}`;}
function spec(){const s=Buffer.alloc(16);Buffer.from("Spec ID Event03").copy(s);const f=Buffer.alloc(12);f[5]=2;f[7]=2;f.writeUInt32LE(1,8);const a=Buffer.alloc(4);a.writeUInt16LE(0x000b,0);a.writeUInt16LE(32,2);return Buffer.concat([s,f,a,Buffer.from([0])]);}
function first(){const e=spec(),h=Buffer.alloc(32);h.writeUInt32LE(P.EVENT.EV_NO_ACTION,4);h.writeUInt32LE(e.length,28);return Buffer.concat([h,e]);}
function ev2(pcr,data){const dg=crypto.createHash("sha256").update(data).digest(),h=Buffer.alloc(12);h.writeUInt32LE(pcr,0);h.writeUInt32LE(P.EVENT.EV_ACTION,4);h.writeUInt32LE(1,8);const a=Buffer.alloc(2);a.writeUInt16LE(0x000b);const z=Buffer.alloc(4);z.writeUInt32LE(data.length);return {bytes:Buffer.concat([h,a,dg,z,data]),dg};}
function ext(old,dg){return crypto.createHash("sha256").update(old).update(dg).digest();}
function b2(x){const b=Buffer.alloc(2+x.length);b.writeUInt16BE(x.length);x.copy(b,2);return b;}
function fixture(){
 const challenge={challengeDigest:d("wire-challenge"),runtimePublicKeyDigest:d("runtime")},ak=crypto.generateKeyPairSync("rsa",{modulusLength:2048});
 const e0=ev2(0,Buffer.from("fw")),e7=ev2(7,Buffer.from("sb")),rawEventLog=Buffer.concat([first(),e0.bytes,e7.bytes]);
 const quoted=crypto.createHash("sha256").update(Buffer.concat([ext(Buffer.alloc(32),e0.dg),ext(Buffer.alloc(32),e7.dg)])).digest();
 const header=Buffer.alloc(6);header.writeUInt32BE(N.TPM.GENERATED_VALUE);header.writeUInt16BE(N.TPM.ST_ATTEST_QUOTE,4);const count=Buffer.alloc(4);count.writeUInt32BE(1);const sel=Buffer.alloc(6);sel.writeUInt16BE(0x000b);sel[2]=3;sel[3]=0x81;
 const attestation=Buffer.concat([header,b2(Buffer.alloc(0)),b2(N.digestBytes(challenge.challengeDigest)),Buffer.alloc(17),Buffer.alloc(8),count,sel,b2(quoted)]);
 const sig=crypto.sign("sha256",attestation,ak.privateKey);const alg=Buffer.alloc(4);alg.writeUInt16BE(W.SIG.RSASSA);alg.writeUInt16BE(0x000b,2);const tpmtSignature=Buffer.concat([alg,b2(sig)]);
 return {challenge,ak,rawEventLog,attestation,tpmtSignature};
}
test("parses TPMT_SIGNATURE RSASSA wire format",()=>{const f=fixture(),s=W.parseTpmtSignature(f.tpmtSignature);assert.equal(s.scheme,"RSASSA");assert.equal(s.hashAlgorithm,"sha256");});
test("verifies raw TPM quote + PC Client log + TPMT_SIGNATURE",()=>{const f=fixture(),r=W.verifyTpmQuoteWire({rawEventLog:f.rawEventLog,tpmtSignature:f.tpmtSignature,attestation:f.attestation,akPublicKey:f.ak.publicKey,challenge:f.challenge});assert.equal(r.ok,true);assert.equal(r.code,"TPM_QUOTE_RAW_EVENT_LOG_AND_TPMT_SIGNATURE_VERIFIED");assert.equal(r.evidence.signatureScheme,"RSASSA");});
test("TPMT_SIGNATURE tampering is rejected",()=>{const f=fixture(),bad=Buffer.from(f.tpmtSignature);bad[bad.length-1]^=1;const r=W.verifyTpmQuoteWire({rawEventLog:f.rawEventLog,tpmtSignature:bad,attestation:f.attestation,akPublicKey:f.ak.publicKey,challenge:f.challenge});assert.equal(r.code,"TPM_QUOTE_SIGNATURE_INVALID");});
