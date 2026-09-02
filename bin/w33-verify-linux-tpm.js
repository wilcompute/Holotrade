#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const Wire = require("../js/w33-tpm-wire-signature.js");
const Prov = require("../js/w33-tpm-eventlog-provenance.js");

function fail(message, code = 2) {
  process.stdout.write(`${JSON.stringify({ ok: false, code: "W33_LINUX_TPM_CLI_ERROR", error: message }, null, 2)}\n`);
  process.exit(code);
}
function arg(name, fallback = null) {
  const i = process.argv.indexOf(name);
  return i >= 0 && i + 1 < process.argv.length ? process.argv[i + 1] : fallback;
}
function read(file, encoding = null) {
  if (!file) throw new Error("required path missing");
  return fs.readFileSync(path.resolve(file), encoding || undefined);
}

if (process.argv.includes("--help")) {
  console.log(`usage: node bin/w33-verify-linux-tpm.js \\
  --quote <TPMS_ATTEST.bin> --signature <TPMT_SIGNATURE.bin> \\
  --ak-public <ak-public.pem> --challenge <challenge.json> \\
  [--event-log /sys/kernel/security/tpm0/binary_bios_measurements] \\
  [--provenance provenance.json]\n\nchallenge.json contains challengeDigest and runtimePublicKeyDigest.\nprovenance.json may name AK/EK X.509 paths and an optional signed activation receipt.`);
  process.exit(0);
}

try {
  const eventLogPath = arg("--event-log", "/sys/kernel/security/tpm0/binary_bios_measurements");
  const quotePath = arg("--quote");
  const signaturePath = arg("--signature");
  const akPublicPath = arg("--ak-public");
  const challengePath = arg("--challenge");
  if (!quotePath || !signaturePath || !akPublicPath || !challengePath) fail("--quote, --signature, --ak-public and --challenge are required");

  const challenge = JSON.parse(read(challengePath, "utf8"));
  const akPublicKey = read(akPublicPath, "utf8");
  const verification = Wire.verifyTpmQuoteWire({
    rawEventLog: read(eventLogPath),
    tpmtSignature: read(signaturePath),
    attestation: read(quotePath),
    akPublicKey,
    challenge,
    akTrust: "LINUX_HOST_AK_INPUT",
  });
  if (!verification.ok) {
    process.stdout.write(`${JSON.stringify(verification, null, 2)}\n`);
    process.exit(1);
  }

  let provenance = null;
  const provenancePath = arg("--provenance");
  if (provenancePath) {
    const spec = JSON.parse(read(provenancePath, "utf8"));
    const maybe = (p) => p ? read(p, "utf8") : null;
    provenance = Prov.verifyTpmCredentialProvenance({
      akCertificatePem: maybe(spec.akCertificate),
      akIntermediatesPem: (spec.akIntermediates || []).map(maybe),
      akRootPem: maybe(spec.akRoot),
      akPublicKey,
      ekCertificatePem: maybe(spec.ekCertificate),
      ekIntermediatesPem: (spec.ekIntermediates || []).map(maybe),
      ekRootPem: maybe(spec.ekRoot),
      activationReceipt: spec.activationReceipt || null,
      enrollmentServicePublicKey: spec.enrollmentServicePublicKey ? maybe(spec.enrollmentServicePublicKey) : null,
    });
    if (!provenance.ok) {
      process.stdout.write(`${JSON.stringify({ ok: false, code: provenance.code, quote: verification, provenance }, null, 2)}\n`);
      process.exit(1);
    }
  }

  process.stdout.write(`${JSON.stringify({
    ok: true,
    code: provenance ? "W33_LINUX_TPM_QUOTE_AND_PROVENANCE_PASS" : "W33_LINUX_TPM_QUOTE_PASS",
    eventLogPath,
    quote: verification,
    provenance,
    honestyBoundary: provenance
      ? provenance.honestyBoundary
      : "Quote/PCR verification used the supplied AK public key; no AK/EK credential provenance was requested.",
  }, null, 2)}\n`);
  process.exit(0);
} catch (error) {
  fail(error.message, 1);
}
