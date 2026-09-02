#!/usr/bin/env node
"use strict";

// Second-stage signer for already verified W33 host evidence.
// Usage:
//   node bin/w33-bind-hardware-settlement.js \
//     <host-bundle.json> <host-receipt-public-key.pem> \
//     <settlement-receipt-spec.json> <settlement-private-key.pem> \
//     [settlement-public-key.pem] [output.json]
//
// Deliberately separate from w33-capture-host-bundle.js: the TPM/host collector
// does not need possession of the market settlement signing key.

const fs = require("node:fs");
const path = require("node:path");
const Settlement = require("../js/w33-hardware-evidence-settlement.js");

function readJson(p) { return JSON.parse(fs.readFileSync(path.resolve(p), "utf8")); }
function readText(p) { return fs.readFileSync(path.resolve(p), "utf8"); }
function die(message) { process.stdout.write(`${JSON.stringify({ ok: false, code: "W33_HARDWARE_SETTLEMENT_BIND_ERROR", error: message }, null, 2)}\n`); process.exit(2); }

const [, , bundlePath, hostPublicKeyPath, settlementSpecPath, settlementPrivateKeyPath, settlementPublicKeyPath = null, outputPath = "w33-hardware-bound-settlement.json"] = process.argv;
if (!bundlePath || !hostPublicKeyPath || !settlementSpecPath || !settlementPrivateKeyPath) {
  die("usage: node bin/w33-bind-hardware-settlement.js <host-bundle.json> <host-receipt-public-key.pem> <settlement-receipt-spec.json> <settlement-private-key.pem> [settlement-public-key.pem] [output.json]");
}

try {
  const bundle = readJson(bundlePath);
  const hostPublicKey = readText(hostPublicKeyPath);
  const evidence = Settlement.admitVerifiedHostBundle(bundle, hostPublicKey);
  const spec = readJson(settlementSpecPath);
  const settlementPrivateKey = readText(settlementPrivateKeyPath);
  const options = settlementPublicKeyPath ? { publicKey: readText(settlementPublicKeyPath), keyId: "w33-hardware-settlement" } : { keyId: "w33-hardware-settlement" };
  const signed = Settlement.createHardwareBoundSettlementReceipt(spec, evidence, settlementPrivateKey, options);
  const output = path.resolve(outputPath);
  fs.writeFileSync(output, `${JSON.stringify({ schema: "holotrade.w33-hardware-bound-settlement-envelope.v1", evidence, signed }, null, 2)}\n`, { mode: 0o600 });
  process.stdout.write(`${JSON.stringify({ ok: true, code: "W33_HARDWARE_BOUND_SETTLEMENT_CREATED", output, hostBundleDigest: evidence.hostBundleDigest, passportId: evidence.passportId }, null, 2)}\n`);
} catch (error) {
  die(error.message);
}
