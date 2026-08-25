"use strict";

// Linux procfs/cgroup telemetry reader for HoloTrade shadow experiments.
// This module is intentionally read-only: it never writes a cgroup, changes a
// scheduler, pins a CPU, or actuates the host.  The checked-in fixture records
// measurements from these kernel-maintained counters; it is not an estimate
// manufactured from the HoloTrade simulation.

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const crypto = require("node:crypto");

function sha256(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function canonicalize(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new TypeError("canonical JSON rejects non-finite numbers");
    return Object.is(value, -0) ? 0 : value;
  }
  if (Array.isArray(value)) return value.map(canonicalize);
  if (typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value).sort()) {
      if (value[key] !== undefined) out[key] = canonicalize(value[key]);
    }
    return out;
  }
  throw new TypeError(`canonical JSON cannot encode ${typeof value}`);
}

function canonicalJson(value) {
  return JSON.stringify(canonicalize(value));
}

function canonicalSha256(value) {
  return sha256(canonicalJson(value));
}

function readText(file) {
  try {
    return fs.readFileSync(file, "utf8");
  } catch (_) {
    return null;
  }
}

function parseProcStat(text) {
  if (typeof text !== "string") throw new TypeError("/proc/stat text is required");
  const cpus = {};
  for (const line of text.split(/\r?\n/)) {
    const match = /^(cpu\d*|cpu)\s+(.+)$/.exec(line.trim());
    if (!match) continue;
    const values = match[2].trim().split(/\s+/).map(Number);
    if (values.length < 4 || values.some((x) => !Number.isFinite(x) || x < 0)) {
      throw new Error(`invalid CPU counter row: ${line}`);
    }
    const names = ["user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal", "guest", "guestNice"];
    const counters = {};
    names.forEach((name, i) => { counters[name] = values[i] || 0; });
    // guest and guest_nice are already included in user and nice on Linux.
    counters.total = values.slice(0, 8).reduce((sum, x) => sum + x, 0);
    counters.idleTotal = counters.idle + counters.iowait;
    counters.busy = counters.total - counters.idleTotal;
    cpus[match[1]] = counters;
  }
  if (!cpus.cpu) throw new Error("/proc/stat contains no aggregate cpu row");
  return cpus;
}

function parseMeminfo(text) {
  if (typeof text !== "string") throw new TypeError("/proc/meminfo text is required");
  const values = {};
  for (const line of text.split(/\r?\n/)) {
    const match = /^([A-Za-z_()]+):\s+(\d+)\s*(kB)?$/.exec(line.trim());
    if (!match) continue;
    values[match[1]] = Number(match[2]) * (match[3] ? 1024 : 1);
  }
  return {
    totalBytes: values.MemTotal ?? null,
    availableBytes: values.MemAvailable ?? null,
    freeBytes: values.MemFree ?? null,
    cachedBytes: values.Cached ?? null,
  };
}

function parseLoadavg(text) {
  if (typeof text !== "string") throw new TypeError("/proc/loadavg text is required");
  const fields = text.trim().split(/\s+/);
  if (fields.length < 5) throw new Error("invalid /proc/loadavg");
  const runnable = fields[3].split("/").map(Number);
  return {
    load1: Number(fields[0]),
    load5: Number(fields[1]),
    load15: Number(fields[2]),
    runnable: runnable[0],
    tasks: runnable[1],
  };
}

function parseSelfStat(text) {
  if (typeof text !== "string") throw new TypeError("/proc/self/stat text is required");
  const close = text.lastIndexOf(")");
  if (close < 0) throw new Error("invalid /proc/self/stat command field");
  // Fields after ')' begin at field 3 (state). utime/stime are fields 14/15.
  const fields = text.slice(close + 1).trim().split(/\s+/);
  if (fields.length < 22) throw new Error("invalid /proc/self/stat field count");
  return {
    userJiffies: Number(fields[11]),
    systemJiffies: Number(fields[12]),
    residentPages: Number(fields[21]),
  };
}

function parseCgroupCpuStat(text) {
  if (typeof text !== "string") return null;
  const out = {};
  for (const line of text.split(/\r?\n/)) {
    const [key, raw] = line.trim().split(/\s+/);
    if (key && raw !== undefined && /^\d+$/.test(raw)) out[key] = Number(raw);
  }
  return Object.keys(out).length ? out : null;
}

function readRapl(powercapRoot) {
  const domains = [];
  function visit(dir) {
    let entries;
    try {
      entries = fs.readdirSync(dir, { withFileTypes: true });
    } catch (_) {
      return;
    }
    const energyFile = path.join(dir, "energy_uj");
    const energyText = readText(energyFile);
    if (energyText !== null && /^\d+\s*$/.test(energyText)) {
      domains.push({
        domain: (readText(path.join(dir, "name")) || path.basename(dir)).trim(),
        path: energyFile,
        energyMicrojoules: Number(energyText.trim()),
      });
    }
    for (const entry of entries) if (entry.isDirectory()) visit(path.join(dir, entry.name));
  }
  visit(powercapRoot);
  domains.sort((a, b) => a.path.localeCompare(b.path));
  return {
    available: domains.length > 0,
    source: powercapRoot,
    domains,
    totalMicrojoules: domains.length ? domains.reduce((sum, x) => sum + x.energyMicrojoules, 0) : null,
    reason: domains.length ? null : "no readable energy_uj domains were exposed by the host kernel",
  };
}

function readSnapshot({
  procRoot = "/proc",
  cgroupRoot = "/sys/fs/cgroup",
  powercapRoot = "/sys/class/powercap",
} = {}) {
  const procStat = readText(path.join(procRoot, "stat"));
  const meminfo = readText(path.join(procRoot, "meminfo"));
  const loadavg = readText(path.join(procRoot, "loadavg"));
  const selfStat = readText(path.join(procRoot, "self/stat"));
  if ([procStat, meminfo, loadavg, selfStat].some((x) => x === null)) {
    throw new Error("required Linux procfs counters are unavailable");
  }
  const cgroupCpu = parseCgroupCpuStat(readText(path.join(cgroupRoot, "cpu.stat")));
  const cgroupMemoryText = readText(path.join(cgroupRoot, "memory.current"));
  return {
    monotonicNs: process.hrtime.bigint().toString(10),
    wallTime: new Date().toISOString(),
    cpus: parseProcStat(procStat),
    memory: parseMeminfo(meminfo),
    load: parseLoadavg(loadavg),
    self: parseSelfStat(selfStat),
    cgroup: {
      cpu: cgroupCpu,
      memoryCurrentBytes: cgroupMemoryText && /^\d+\s*$/.test(cgroupMemoryText)
        ? Number(cgroupMemoryText.trim())
        : null,
    },
    rapl: readRapl(powercapRoot),
  };
}

function ratioDelta(before, after) {
  const total = after.total - before.total;
  const busy = after.busy - before.busy;
  if (!(total > 0) || busy < 0) return null;
  return Math.max(0, Math.min(1, busy / total));
}

function deltaSnapshot(before, after, sequence) {
  const elapsedNs = Number(BigInt(after.monotonicNs) - BigInt(before.monotonicNs));
  const cpuNames = Object.keys(after.cpus)
    .filter((name) => /^cpu\d+$/.test(name) && before.cpus[name])
    .sort((a, b) => Number(a.slice(3)) - Number(b.slice(3)));
  const perCpuBusyFraction = cpuNames.map((name) => ratioDelta(before.cpus[name], after.cpus[name]));
  const raplDelta = before.rapl.available && after.rapl.available &&
    Number.isFinite(before.rapl.totalMicrojoules) && Number.isFinite(after.rapl.totalMicrojoules)
    ? after.rapl.totalMicrojoules - before.rapl.totalMicrojoules
    : null;
  const beforeCgroup = before.cgroup.cpu && before.cgroup.cpu.usage_usec;
  const afterCgroup = after.cgroup.cpu && after.cgroup.cpu.usage_usec;
  return {
    sequence,
    intervalStart: before.wallTime,
    intervalEnd: after.wallTime,
    elapsedNs,
    observed: {
      cpuBusyFraction: ratioDelta(before.cpus.cpu, after.cpus.cpu),
      perCpuBusyFraction,
      logicalCpuLanes: perCpuBusyFraction.length,
      loadAverage1m: after.load.load1,
      runnableTasks: after.load.runnable,
      totalTasks: after.load.tasks,
      memoryAvailableBytes: after.memory.availableBytes,
      memoryTotalBytes: after.memory.totalBytes,
      memoryAvailableFraction: after.memory.totalBytes > 0
        ? after.memory.availableBytes / after.memory.totalBytes
        : null,
      processUserJiffiesDelta: after.self.userJiffies - before.self.userJiffies,
      processSystemJiffiesDelta: after.self.systemJiffies - before.self.systemJiffies,
      processResidentPages: after.self.residentPages,
      cgroupCpuUsageMicrosecondsDelta: beforeCgroup !== undefined && afterCgroup !== undefined
        ? afterCgroup - beforeCgroup
        : null,
      cgroupMemoryCurrentBytes: after.cgroup.memoryCurrentBytes,
      raplEnergyMicrojoulesDelta: raplDelta !== null && raplDelta >= 0 ? raplDelta : null,
    },
  };
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function captureHostTelemetry({ samples = 32, intervalMs = 120 } = {}) {
  if (!Number.isSafeInteger(samples) || samples < 2 || samples > 10000) {
    throw new RangeError("samples must be an integer in [2,10000]");
  }
  if (!Number.isFinite(intervalMs) || intervalMs < 20 || intervalMs > 60000) {
    throw new RangeError("intervalMs must be in [20,60000]");
  }
  const startedAt = new Date().toISOString();
  let before = readSnapshot();
  const observations = [];
  for (let i = 0; i < samples; i++) {
    await wait(intervalMs);
    const after = readSnapshot();
    observations.push(deltaSnapshot(before, after, i));
    before = after;
  }
  const platform = {
    os: os.platform(),
    architecture: os.arch(),
    kernelRelease: os.release(),
    logicalCpuCount: os.cpus().length,
    nodeVersion: process.version,
    cgroupVersion: fs.existsSync("/sys/fs/cgroup/cgroup.controllers") ? 2 : 1,
  };
  const body = {
    schema: "holotrade.telemetry-shadow.host.v1",
    evidence: "MEASURED_LOCAL_KERNEL_COUNTERS",
    readOnly: true,
    startedAt,
    finishedAt: new Date().toISOString(),
    capture: {
      requestedSamples: samples,
      requestedIntervalMs: intervalMs,
      observationCount: observations.length,
      sources: [
        "/proc/stat",
        "/proc/meminfo",
        "/proc/loadavg",
        "/proc/self/stat",
        "/sys/fs/cgroup/cpu.stat",
        "/sys/fs/cgroup/memory.current",
        "/sys/class/powercap/**/energy_uj",
      ],
      boundary: "host and current-process counters only; no DCIM, BMC, operator, or application SLO telemetry",
    },
    platform,
    environmentSha256: canonicalSha256(platform),
    capabilities: {
      procfs: true,
      cgroupCpu: before.cgroup.cpu !== null,
      cgroupMemory: before.cgroup.memoryCurrentBytes !== null,
      raplEnergy: before.rapl.available,
      raplReason: before.rapl.reason,
    },
    observations,
  };
  return { ...body, fixtureSha256: canonicalSha256(body) };
}

function verifyHostFixture(fixture) {
  if (!fixture || fixture.schema !== "holotrade.telemetry-shadow.host.v1") return false;
  const { fixtureSha256, ...body } = fixture;
  return typeof fixtureSha256 === "string" && fixtureSha256 === canonicalSha256(body);
}

module.exports = {
  sha256,
  canonicalJson,
  canonicalSha256,
  parseProcStat,
  parseMeminfo,
  parseLoadavg,
  parseSelfStat,
  parseCgroupCpuStat,
  readRapl,
  readSnapshot,
  ratioDelta,
  deltaSnapshot,
  captureHostTelemetry,
  verifyHostFixture,
};
