"use strict";

// TPM wire-format signature parsing for portable W33 attestation.
// Supports the common TPMT_SIGNATURE schemes RSASSA, RSAPSS and ECDSA.
// TPM structures use network byte order; PC Client event logs are parsed by
// w33-tpm-eventlog-provenance.js using their specified little-endian layout.

const crypto = require("node:crypto");
const Native = require("./w33-native-attestation.js");
const EventLog = require("./w33-tpm-eventlog-provenance.js");

const SIG = Object.freeze({ RSASSA: 0x0014, RSAPSS: 0x0016, ECDSA: 0x0018 });
const HASH = Object.freeze({ 0x0004: "sha1", 0x000b: "sha256", 0x000c: "sha384", 0x000d: "sha512" });

function need(buf, off, count, what) {
  if (!Buffer.isBuffer(buf) || off + count > buf.length) throw new RangeError(`truncated ${what}`);
}
function tpm2b(buf, state) {
  need(buf, state.i, 2, "TPM2B size"); const n = buf.readUInt16BE(state.i); state.i += 2;
  need(buf, state.i, n, "TPM2B payload"); const out = Buffer.from(buf.subarray(state.i, state.i+n)); state.i += n; return out;
}
function derLen(n) { return n < 0x80 ? Buffer.from([n]) : n < 0x100 ? Buffer.from([0x81,n]) : Buffer.from([0x82,n>>8,n&255]); }
function derInt(v) {
  let i=0; while (i<v.length-1 && v[i]===0) i++; let x=v.subarray(i);
  if (x[0]&0x80) x=Buffer.concat([Buffer.from([0]),x]);
  return Buffer.concat([Buffer.from([0x02]),derLen(x.length),x]);
}
function ecdsaDer(r,s) { const body=Buffer.concat([derInt(r),derInt(s)]); return Buffer.concat([Buffer.from([0x30]),derLen(body.length),body]); }

function parseTpmtSignature(raw) {
  if (!Buffer.isBuffer(raw)) throw new TypeError("TPMT_SIGNATURE bytes required");
  const state={i:0}; need(raw,0,4,"TPMT_SIGNATURE header");
  const sigAlg=raw.readUInt16BE(state.i); state.i+=2;
  const hashAlg=raw.readUInt16BE(state.i); state.i+=2;
  const hashAlgorithm=HASH[hashAlg];
  if (!hashAlgorithm) throw new Error(`unsupported TPM signature hash 0x${hashAlg.toString(16)}`);
  let signature, scheme, verifyOptions=null;
  if (sigAlg===SIG.RSASSA || sigAlg===SIG.RSAPSS) {
    signature=tpm2b(raw,state);
    scheme=sigAlg===SIG.RSASSA?"RSASSA":"RSAPSS";
    if (sigAlg===SIG.RSAPSS) verifyOptions={padding:crypto.constants.RSA_PKCS1_PSS_PADDING,saltLength:crypto.constants.RSA_PSS_SALTLEN_DIGEST};
  } else if (sigAlg===SIG.ECDSA) {
    const r=tpm2b(raw,state), s=tpm2b(raw,state); signature=ecdsaDer(r,s); scheme="ECDSA";
  } else throw new Error(`unsupported TPM signature algorithm 0x${sigAlg.toString(16)}`);
  if (state.i!==raw.length) throw new Error("unexpected trailing TPMT_SIGNATURE bytes");
  return Object.freeze({sigAlg,hashAlg,hashAlgorithm,scheme,signature,verifyOptions});
}

function equal(a,b) { return Buffer.isBuffer(a)&&Buffer.isBuffer(b)&&a.length===b.length&&crypto.timingSafeEqual(a,b); }

function verifyTpmQuoteWire({rawEventLog,tpmtSignature,attestation,akPublicKey,challenge,akTrust="PORTABLE_TRUSTED_AK"}) {
  let log,sig,quote;
  try { log=EventLog.parsePcClientEventLog(rawEventLog); sig=parseTpmtSignature(tpmtSignature); quote=Native.parseTpmQuoteAttest(attestation); }
  catch (error) { return Object.freeze({ok:false,code:"TPM_WIRE_EVIDENCE_MALFORMED",error:error.message}); }
  if (!challenge || !akPublicKey) return Object.freeze({ok:false,code:"TPM_WIRE_TRUST_INPUT_REQUIRED"});
  if (!equal(quote.extraData,Native.digestBytes(challenge.challengeDigest))) return Object.freeze({ok:false,code:"TPM_QUOTE_NONCE_MISMATCH"});
  let signatureValid=false;
  try {
    const key=sig.verifyOptions?{key:akPublicKey,...sig.verifyOptions}:akPublicKey;
    signatureValid=crypto.verify(sig.hashAlgorithm,attestation,key,sig.signature);
  } catch (error) { return Object.freeze({ok:false,code:"TPM_QUOTE_SIGNATURE_ERROR",error:error.message}); }
  if (!signatureValid) return Object.freeze({ok:false,code:"TPM_QUOTE_SIGNATURE_INVALID"});
  let expected;
  try {
    const replay=Native.replayPcrEventDigests(log.replayDigests);
    expected=crypto.createHash(sig.hashAlgorithm).update(Native.selectedPcrBytes(quote.selections,replay)).digest();
  } catch (error) { return Object.freeze({ok:false,code:"TPM_EVENT_LOG_REPLAY_FAILED",error:error.message}); }
  if (!equal(quote.pcrDigest,expected)) return Object.freeze({ok:false,code:"TPM_QUOTED_PCR_DIGEST_MISMATCH"});
  const evidence=Object.freeze({
    schema:"holotrade.w33-native-tpm2-wire-verification.v1",provider:"TPM2",akTrust,
    challengeDigest:challenge.challengeDigest,attestationDigest:Native.sha256(attestation),
    rawEventLogDigest:log.rawDigest,rawEventRecordCount:log.recordCount,replayDigestCount:log.replayDigestCount,
    quotedPcrDigest:quote.pcrDigest.toString("hex"),quoteHashAlgorithm:sig.hashAlgorithm,signatureScheme:sig.scheme,
    selectedBanks:quote.selections.map(x=>({hashAlgorithm:x.hashName,bitmapHex:x.bitmap.toString("hex")})),
  });
  return Object.freeze({ok:true,code:"TPM_QUOTE_RAW_EVENT_LOG_AND_TPMT_SIGNATURE_VERIFIED",hardwareBacked:true,evidence,parsedEventLog:log});
}

module.exports={SIG,HASH,parseTpmtSignature,verifyTpmQuoteWire};
