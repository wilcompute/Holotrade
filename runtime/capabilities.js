"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { promisify } = require("node:util");
const { execFile } = require("node:child_process");
const { sha256File } = require("./artifacts.js");

const execFileAsync = promisify(execFile);
const CAPABILITY_SCHEMA = "holotrade.runtime-capabilities.v1";
const STATUS = Object.freeze({
  AVAILABLE: "AVAILABLE",
  UNAVAILABLE: "UNAVAILABLE",
  INACCESSIBLE: "INACCESSIBLE",
  UNVERIFIED: "UNVERIFIED",
  ERROR: "ERROR",
});

function finding(id, status, reasonCode, evidence = {}) {
  return Object.freeze({ id, status, reasonCode, evidence: Object.freeze(evidence) });
}

async function probePath(target, { read = true, write = false } = {}) {
  try {
    const stat = await fs.promises.stat(target);
    let mode = 0;
    if (read) mode |= fs.constants.R_OK;
    if (write) mode |= fs.constants.W_OK;
    try {
      if (mode) await fs.promises.access(target, mode);
      return {
        exists: true,
        accessible: true,
        path: target,
        kind: stat.isCharacterDevice() ? "character-device" : stat.isFile() ? "file" : stat.isDirectory() ? "directory" : "other",
      };
    } catch (error) {
      return { exists: true, accessible: false, path: target, kind: stat.isCharacterDevice() ? "character-device" : "other", error: error.code };
    }
  } catch (error) {
    return { exists: false, accessible: false, path: target, error: error.code };
  }
}

async function findExecutable(command, envPath = process.env.PATH || "") {
  const candidates = command.includes(path.sep)
    ? [path.resolve(command)]
    : envPath.split(path.delimiter).filter(Boolean).map((dir) => path.join(dir, command));
  for (const candidate of candidates) {
    try {
      await fs.promises.access(candidate, fs.constants.X_OK);
      const stat = await fs.promises.stat(candidate);
      if (stat.isFile()) return candidate;
    } catch (_) {
      // Continue searching PATH.
    }
  }
  return null;
}

async function commandFinding(id, command, args = ["--version"], { envPath, run = execFileAsync } = {}) {
  const binary = await findExecutable(command, envPath);
  if (!binary) return finding(id, STATUS.UNAVAILABLE, "EXECUTABLE_NOT_FOUND", { command });
  try {
    const result = await run(binary, args, { timeout: 3000, maxBuffer: 128 * 1024 });
    const version = `${result.stdout || ""}${result.stderr || ""}`.trim().split(/\r?\n/)[0] || null;
    return finding(id, STATUS.AVAILABLE, "EXECUTABLE_RESPONDED", { path: binary, version });
  } catch (error) {
    return finding(id, STATUS.ERROR, "EXECUTABLE_PROBE_FAILED", {
      path: binary,
      error: error.code || error.message,
      stderr: String(error.stderr || "").trim().slice(0, 512),
    });
  }
}

async function firstAccessible(paths, access = {}) {
  const observations = [];
  for (const target of paths) {
    const observation = await probePath(target, access);
    observations.push(observation);
    if (observation.exists && observation.accessible) return { match: observation, observations };
  }
  return { match: null, observations };
}

async function findNamedFiles(root, name, maxDepth = 7) {
  const found = [];
  async function walk(current, depth) {
    if (depth > maxDepth) return;
    let dirents;
    try {
      dirents = await fs.promises.readdir(current, { withFileTypes: true });
    } catch (_) {
      return;
    }
    for (const entry of dirents) {
      const full = path.join(current, entry.name);
      if (entry.name === name) found.push(full);
      if (entry.isDirectory()) await walk(full, depth + 1);
    }
  }
  await walk(root, 0);
  return found.sort();
}

async function probeKepler(endpoint, { fetchImpl = globalThis.fetch, timeoutMs = 1500 } = {}) {
  if (!endpoint) return finding("kepler", STATUS.UNAVAILABLE, "METRICS_ENDPOINT_NOT_CONFIGURED", {});
  if (typeof fetchImpl !== "function") return finding("kepler", STATUS.UNAVAILABLE, "FETCH_NOT_AVAILABLE", { endpoint });
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetchImpl(endpoint, { signal: controller.signal });
    const body = await response.text();
    const metricNames = [...new Set(body.match(/\bkepler_[a-zA-Z0-9_:]+(?=[{\s])/g) || [])].sort();
    if (!response.ok || metricNames.length === 0) {
      return finding("kepler", STATUS.UNVERIFIED, "ENDPOINT_DID_NOT_EXPOSE_KEPLER_METRICS", {
        endpoint,
        httpStatus: response.status,
      });
    }
    return finding("kepler", STATUS.AVAILABLE, "PROMETHEUS_METRICS_OBSERVED", {
      endpoint,
      metricCount: metricNames.length,
      sampleMetrics: metricNames.slice(0, 8),
    });
  } catch (error) {
    return finding("kepler", STATUS.UNAVAILABLE, "METRICS_ENDPOINT_UNREACHABLE", {
      endpoint,
      error: error.name === "AbortError" ? "TIMEOUT" : error.code || error.message,
    });
  } finally {
    clearTimeout(timer);
  }
}

async function detectRuntimeCapabilities(options = {}) {
  const paths = {
    kvm: options.kvmPath || "/dev/kvm",
    tpmDevices: options.tpmDevices || ["/dev/tpmrm0", "/dev/tpm0"],
    measuredBootLogs: options.measuredBootLogs || [
      "/sys/kernel/security/tpm0/binary_bios_measurements",
      "/sys/kernel/security/tpm1/binary_bios_measurements",
    ],
    imaLogs: options.imaLogs || [
      "/sys/kernel/security/ima/binary_runtime_measurements",
      "/sys/kernel/security/ima/ascii_runtime_measurements",
    ],
    sevGuest: options.sevGuestPath || "/dev/sev-guest",
    sevHost: options.sevHostPath || "/dev/sev",
    sevModule: options.sevModulePath || "/sys/module/sev_guest",
    powercap: options.powercapPath || "/sys/class/powercap",
  };

  const findings = [];
  const platform = options.platform || process.platform;
  const arch = options.arch || process.arch;
  findings.push(platform === "linux"
    ? finding("host_os", STATUS.AVAILABLE, "LINUX_HOST", { platform, arch })
    : finding("host_os", STATUS.UNAVAILABLE, "FIRECRACKER_REQUIRES_LINUX", { platform, arch }));
  findings.push(["x64", "arm64"].includes(arch)
    ? finding("host_arch", STATUS.AVAILABLE, "SUPPORTED_ARCHITECTURE", { arch })
    : finding("host_arch", STATUS.UNAVAILABLE, "UNSUPPORTED_ARCHITECTURE", { arch }));

  const kvm = await probePath(paths.kvm, { read: true, write: true });
  findings.push(!kvm.exists
    ? finding("kvm", STATUS.UNAVAILABLE, "DEVICE_NOT_FOUND", kvm)
    : kvm.accessible
      ? finding("kvm", STATUS.AVAILABLE, "READ_WRITE_DEVICE", kvm)
      : finding("kvm", STATUS.INACCESSIBLE, "READ_WRITE_ACCESS_REQUIRED", kvm));

  findings.push(await commandFinding(
    "firecracker",
    options.firecrackerBinary || "firecracker",
    ["--version"],
    { envPath: options.envPath, run: options.runCommand }
  ));

  const tpm = await firstAccessible(paths.tpmDevices, { read: true, write: true });
  findings.push(tpm.match
    ? finding("tpm", STATUS.AVAILABLE, "READ_WRITE_DEVICE", tpm.match)
    : finding("tpm", tpm.observations.some((x) => x.exists) ? STATUS.INACCESSIBLE : STATUS.UNAVAILABLE,
      tpm.observations.some((x) => x.exists) ? "READ_WRITE_ACCESS_REQUIRED" : "DEVICE_NOT_FOUND",
      { observations: tpm.observations }));

  const bootLog = await firstAccessible(paths.measuredBootLogs, { read: true });
  if (bootLog.match) {
    let digest = null;
    try { digest = await sha256File(bootLog.match.path); } catch (_) { /* access can race */ }
    findings.push(finding("measured_boot", digest ? STATUS.AVAILABLE : STATUS.ERROR,
      digest ? "EVENT_LOG_HASHED" : "EVENT_LOG_HASH_FAILED", { path: bootLog.match.path, digest }));
  } else {
    findings.push(finding("measured_boot", STATUS.UNAVAILABLE, "TPM_EVENT_LOG_NOT_FOUND", {
      observations: bootLog.observations,
    }));
  }

  const ima = await firstAccessible(paths.imaLogs, { read: true });
  findings.push(ima.match
    ? finding("ima_measurements", STATUS.AVAILABLE, "RUNTIME_MEASUREMENT_LOG_READABLE", { path: ima.match.path })
    : finding("ima_measurements", STATUS.UNAVAILABLE, "RUNTIME_MEASUREMENT_LOG_NOT_FOUND", {
      observations: ima.observations,
    }));

  const sevGuest = await probePath(paths.sevGuest, { read: true, write: true });
  const sevHost = await probePath(paths.sevHost, { read: true, write: true });
  const sevModule = await probePath(paths.sevModule, { read: true });
  findings.push(sevGuest.exists && sevGuest.accessible
    ? finding("sev_snp_guest_attestation", STATUS.AVAILABLE, "SEV_GUEST_IOCTL_DEVICE", sevGuest)
    : finding("sev_snp_guest_attestation", sevGuest.exists ? STATUS.INACCESSIBLE : STATUS.UNAVAILABLE,
      sevGuest.exists ? "SEV_GUEST_DEVICE_INACCESSIBLE" : "SEV_GUEST_DEVICE_NOT_FOUND", {
        guestDevice: sevGuest,
        hostDevice: sevHost,
        kernelModulePresent: sevModule.exists,
        note: "A loaded module or host /dev/sev device is not a guest attestation report.",
      }));

  const energyFiles = await findNamedFiles(paths.powercap, "energy_uj");
  const readableEnergyFiles = [];
  for (const file of energyFiles) {
    const observation = await probePath(file, { read: true });
    if (observation.accessible) readableEnergyFiles.push(file);
  }
  findings.push(readableEnergyFiles.length
    ? finding("rapl", STATUS.AVAILABLE, "POWERCAP_ENERGY_COUNTERS", { energyFiles: readableEnergyFiles })
    : finding("rapl", STATUS.UNAVAILABLE, "NO_READABLE_ENERGY_COUNTERS", { powercapPath: paths.powercap }));

  findings.push(await probeKepler(
    options.keplerEndpoint || (options.env || process.env).KEPLER_METRICS_URL,
    { fetchImpl: options.fetchImpl, timeoutMs: options.keplerTimeoutMs }
  ));

  const byId = Object.fromEntries(findings.map((item) => [item.id, item]));
  const launchable = ["host_os", "host_arch", "kvm", "firecracker"]
    .every((id) => byId[id].status === STATUS.AVAILABLE);
  return Object.freeze({
    schema: CAPABILITY_SCHEMA,
    observedAt: options.now !== undefined ? new Date(options.now).toISOString() : new Date().toISOString(),
    launchable,
    hardwareEvidenceReady: ["measured_boot", "sev_snp_guest_attestation"]
      .some((id) => byId[id].status === STATUS.AVAILABLE),
    hardwareAttestationReady: false,
    attestationNote: "A device or measurement log is only an evidence interface; a fresh quote/report still requires cryptographic verification.",
    energyMeterReady: ["rapl", "kepler"].some((id) => byId[id].status === STATUS.AVAILABLE),
    findings: Object.freeze(findings),
  });
}

module.exports = {
  CAPABILITY_SCHEMA,
  STATUS,
  finding,
  probePath,
  findExecutable,
  findNamedFiles,
  probeKepler,
  detectRuntimeCapabilities,
};
