#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const V = require("../js/w33-portable-audit-verifier.js");
const Host = require("../js/w33-host-audit-bundle.js");

function usage() {
  console.error("usage: node bin/w33-verify-receipt.js <bundle.json> <trusted-receipt-public-key.pem>");
  process.exit(2);
}

const [, , bundlePath, publicKeyPath] = process.argv;
if (!bundlePath || !publicKeyPath) usage();

try {
  const bundle = JSON.parse(fs.readFileSync(path.resolve(bundlePath), "utf8"));
  const key = fs.readFileSync(path.resolve(publicKeyPath), "utf8");
  const result = bundle && bundle.telemetry
    ? Host.verifyHostBundle(bundle, key)
    : V.verifyPortableBundle(bundle, key);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  process.exit(result.ok ? 0 : 1);
} catch (error) {
  process.stdout.write(`${JSON.stringify({ ok: false, code: "PORTABLE_W33_AUDIT_CLI_ERROR", error: error.message }, null, 2)}\n`);
  process.exit(1);
}
