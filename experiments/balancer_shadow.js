#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const hostPath = path.join(root, "data/telemetry_shadow_host.json");
const marketPath = path.join(root, "data/telemetry_shadow_elexon_mid.json");
const certificatePath = path.join(root, "data/telemetry_shadow_certificate.json");

const { captureHostTelemetry, verifyHostFixture } = require(path.join(root, "telemetry/procfs.js"));
const { DEFAULT_QUERY, fetchMarketFixture, verifyMarketFixture } = require(path.join(root, "telemetry/elexon-market.js"));
const { runShadowReplay, verifyReplayCertificate } = require(path.join(root, "telemetry/shadow-balancer.js"));

function intArg(name, fallback) {
  const prefix = `--${name}=`;
  const raw = process.argv.find((arg) => arg.startsWith(prefix));
  if (!raw) return fallback;
  const value = Number(raw.slice(prefix.length));
  if (!Number.isSafeInteger(value) || value <= 0) throw new RangeError(`${name} must be a positive integer`);
  return value;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function writeJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

async function main() {
  let host;
  let market;
  if (process.argv.includes("--capture-host")) {
    host = await captureHostTelemetry({
      samples: intArg("samples", 32),
      intervalMs: intArg("interval-ms", 120),
    });
    writeJson(hostPath, host);
  } else {
    host = readJson(hostPath);
  }

  if (process.argv.includes("--refresh-market")) {
    market = await fetchMarketFixture(DEFAULT_QUERY);
    writeJson(marketPath, market);
  } else {
    market = readJson(marketPath);
  }

  if (!verifyHostFixture(host)) throw new Error("host telemetry fixture failed SHA-256 verification");
  if (!verifyMarketFixture(market)) throw new Error("market fixture failed SHA-256 verification");
  const certificate = runShadowReplay(host, market);
  if (!verifyReplayCertificate(certificate, host, market)) throw new Error("shadow replay self-verification failed");
  if (process.argv.includes("--write-certificate")) writeJson(certificatePath, certificate);

  const summary = process.argv.includes("--summary")
    ? { ...certificate, rows: undefined }
    : certificate;
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    process.stderr.write(`${error.stack || error.message}\n`);
    process.exitCode = 1;
  });
}

module.exports = { hostPath, marketPath, certificatePath, main };
