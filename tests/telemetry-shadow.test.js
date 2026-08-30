"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const P = require(path.join(root, "telemetry/procfs.js"));
const M = require(path.join(root, "telemetry/elexon-market.js"));
const B = require(path.join(root, "telemetry/shadow-balancer.js"));

const host = JSON.parse(fs.readFileSync(path.join(root, "data/telemetry_shadow_host.json"), "utf8"));
const market = JSON.parse(fs.readFileSync(path.join(root, "data/telemetry_shadow_elexon_mid.json"), "utf8"));
const certificate = JSON.parse(fs.readFileSync(path.join(root, "data/telemetry_shadow_certificate.json"), "utf8"));

test("procfs parsers preserve Linux counter semantics", () => {
  const before = P.parseProcStat([
    "cpu  100 2 40 800 8 3 7 0 0 0",
    "cpu0 60 1 20 400 4 2 3 0 0 0",
    "cpu1 40 1 20 400 4 1 4 0 0 0",
  ].join("\n"));
  const after = P.parseProcStat([
    "cpu  110 2 45 880 10 3 10 0 0 0",
    "cpu0 65 1 23 440 5 2 4 0 0 0",
    "cpu1 45 1 22 440 5 1 6 0 0 0",
  ].join("\n"));
  assert.equal(before.cpu.total, 960);
  assert.equal(after.cpu.total, 1060);
  assert.equal(P.ratioDelta(before.cpu, after.cpu), 0.18);

  const mem = P.parseMeminfo("MemTotal: 1000 kB\nMemAvailable: 625 kB\nCached: 200 kB\n");
  assert.deepEqual(mem, {
    totalBytes: 1024000,
    availableBytes: 640000,
    freeBytes: null,
    cachedBytes: 204800,
  });
  assert.deepEqual(P.parseLoadavg("0.30 0.25 0.20 2/345 123"), {
    load1: 0.3, load5: 0.25, load15: 0.2, runnable: 2, tasks: 345,
  });
});

test("the checked-in host fixture is genuine read-only kernel-counter evidence", () => {
  assert.equal(P.verifyHostFixture(host), true);
  assert.equal(host.evidence, "MEASURED_LOCAL_KERNEL_COUNTERS");
  assert.equal(host.readOnly, true);
  assert.equal(host.capture.observationCount, 48);
  assert.equal(host.platform.os, "linux");
  assert.equal(host.platform.logicalCpuCount, 12);
  assert.equal(host.environmentSha256, P.canonicalSha256(host.platform));
  assert.ok(host.capture.sources.includes("/proc/stat"));
  for (const sample of host.observations) {
    assert.equal(sample.observed.perCpuBusyFraction.length, 12);
    assert.ok(sample.observed.perCpuBusyFraction.every((x) => Number.isFinite(x) && x >= 0 && x <= 1));
    assert.ok(sample.observed.cpuBusyFraction >= 0 && sample.observed.cpuBusyFraction <= 1);
    assert.ok(sample.elapsedNs > 0);
  }
  if (!host.capabilities.raplEnergy) {
    assert.match(host.capabilities.raplReason, /no readable energy_uj/);
    assert.ok(host.observations.every((sample) => sample.observed.raplEnergyMicrojoulesDelta === null));
  }
});

test("the frozen Elexon trace verifies to its source payload and licence attribution", () => {
  assert.equal(M.verifyMarketFixture(market), true);
  assert.equal(market.evidence, "MEASURED_OFFICIAL_MARKET_DATA");
  assert.equal(market.source.authority, "Elexon Insights Solution");
  assert.equal(market.source.attribution, "Contains BSC information licensed under the BSC Open Data Licence.");
  assert.equal(market.source.httpStatus, 200);
  assert.equal(market.source.responseBytesSha256, "1b83b9643f5f2ef0332b29eda5ab64cd61fd3eab528001b90747a1ae69154f8e");
  assert.equal(P.sha256(Buffer.from(market.providerResponseRawUtf8, "utf8")), market.source.responseBytesSha256);
  assert.equal(market.rows.length, 48);
  assert.equal(market.rows[0].startTime, "2026-08-01T00:00:00.000Z");
  assert.equal(market.rows.at(-1).startTime, "2026-08-01T23:30:00.000Z");
  assert.ok(market.rows.every((row) => row.dataProvider === "APXMIDP"));
  assert.ok(market.rows.every((row, i) => i === 0 || market.rows[i - 1].startTime < row.startTime));
});

test("shadow replay is numerically canonical, paired, conservative, and never represented as a field outcome", () => {
  const replay = B.runShadowReplay(host, market);
  // The frozen certificate keeps its original bit-exact commitment. Recomputed
  // floating-point model outputs are compared through a 14-significant-digit
  // semantic commitment so Node/libm sub-ulp variation cannot masquerade as a
  // scientific regression.
  assert.equal(B.replaySemanticSha256(replay), B.replaySemanticSha256(certificate));
  assert.equal(B.verifyReplayCertificate(certificate, host, market), true);
  assert.equal(replay.evidence, "MEASURED_INPUTS_COUNTERFACTUAL_OUTPUTS");
  assert.equal(replay.actuation, "NONE");
  assert.equal(replay.design.fieldOutcome, false);
  assert.match(replay.design.timeAlignment, /not co-temporal/);
  assert.equal(replay.counterfactualSummary.worsenedIntervals, 0);
  assert.equal(replay.counterfactualSummary.improvedIntervals, 41);
  assert.equal(replay.counterfactualSummary.unchangedIntervals, 7);
  assert.ok(replay.counterfactualSummary.meanPairedGiniDifference > 0);
  for (const row of replay.rows) {
    assert.equal(row.streamsTimeAligned, false);
    assert.equal(row.observed.source, "MEASURED_LOCAL_KERNEL_COUNTERS");
    assert.equal(row.counterfactual.source, "COUNTERFACTUAL_ONE_STEP_POLICY_MODEL");
    assert.ok(Math.abs(row.observed.aggregateLaneUtilisation - row.counterfactual.aggregateLaneUtilisation) < 1e-12);
  }
});

test("fixture and replay commitments fail closed after tampering", () => {
  const hostTamper = structuredClone(host);
  hostTamper.observations[0].observed.cpuBusyFraction += 0.001;
  assert.equal(P.verifyHostFixture(hostTamper), false);

  const marketTamper = structuredClone(market);
  marketTamper.rows[0].priceGBPPerMWh += 1;
  assert.equal(M.verifyMarketFixture(marketTamper), false);

  const certificateTamper = structuredClone(certificate);
  certificateTamper.rows[0].counterfactual.utilisationGini += 0.001;
  assert.equal(B.verifyReplayCertificate(certificateTamper, host, market), false);
});

test("one common wholesale-price scalar provably cancels from within-host allocation", () => {
  const utilisation = [0.02, 0.11, 0.27, 0.44, 0.63, 0.91];
  const low = B.oneStepRecommendation(utilisation, { commonEnergyMultiplier: 0.62 });
  const high = B.oneStepRecommendation(utilisation, { commonEnergyMultiplier: 2.4 });
  assert.ok(low.proposed.every((x, i) => Math.abs(x - high.proposed[i]) < 1e-15));
  assert.ok(Math.abs(low.proposedGini - high.proposedGini) < 1e-15);
  assert.ok(Math.abs(low.totalObserved - low.totalProposed) < 1e-12);
  assert.ok(low.proposedGini < low.observedGini);
});

test("live procfs smoke check runs only under a native Linux Node process", {
  skip: process.platform !== "linux" || !fs.existsSync("/proc/stat"),
}, () => {
  const snapshot = P.readSnapshot();
  assert.ok(snapshot.cpus.cpu.total > 0);
  assert.ok(Object.keys(snapshot.cpus).some((name) => /^cpu\d+$/.test(name)));
  assert.ok(snapshot.memory.totalBytes > 0);
});
