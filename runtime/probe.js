#!/usr/bin/env node
"use strict";

const { FirecrackerRuntime } = require("./firecracker.js");
const { RaplMeter } = require("./metering.js");

function json(value) {
  return JSON.stringify(value, (_, item) => typeof item === "bigint" ? item.toString(10) : item, 2);
}

async function main() {
  const binary = process.env.FIRECRACKER_BIN || "firecracker";
  const runtime = new FirecrackerRuntime({
    binary,
    capabilityOptions: {
      keplerEndpoint: process.env.KEPLER_METRICS_URL,
    },
  });
  const capabilities = await runtime.preflight({
    kernelPath: process.env.FIRECRACKER_KERNEL,
    rootfsPath: process.env.FIRECRACKER_ROOTFS,
  });
  const controlPlane = await runtime.probeControlPlane(`holotrade-probe-${process.pid}`);
  const rapl = await RaplMeter.discover();
  const energy = await rapl.snapshot();
  process.stdout.write(`${json({
    schema: "holotrade.runtime-probe.v1",
    note: "The control-plane probe starts no guest. READY additionally requires KVM access and hashed kernel/rootfs inputs.",
    preflight: capabilities,
    controlPlane,
    energy,
  })}\n`);
}

main().catch((error) => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
});
