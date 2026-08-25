"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { detectRuntimeCapabilities, findExecutable } = require("./capabilities.js");
const { hashArtifacts } = require("./artifacts.js");

const FIRECRACKER_SCHEMA = "holotrade.firecracker-runtime.v1";

function apiRequest(socketPath, method, requestPath, body = null, timeoutMs = 3000) {
  return new Promise((resolve, reject) => {
    const bytes = body === null ? null : Buffer.from(JSON.stringify(body));
    const request = http.request({
      socketPath,
      path: requestPath,
      method,
      timeout: timeoutMs,
      headers: bytes ? { "content-type": "application/json", "content-length": bytes.length } : {},
    }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        const text = Buffer.concat(chunks).toString("utf8");
        let parsed = null;
        if (text) {
          try { parsed = JSON.parse(text); } catch (_) { parsed = text; }
        }
        const result = { statusCode: response.statusCode, body: parsed };
        if (response.statusCode >= 200 && response.statusCode < 300) resolve(result);
        else {
          const error = new Error(`Firecracker API ${method} ${requestPath} returned ${response.statusCode}`);
          error.response = result;
          reject(error);
        }
      });
    });
    request.on("timeout", () => request.destroy(new Error("Firecracker API timeout")));
    request.on("error", reject);
    if (bytes) request.write(bytes);
    request.end();
  });
}

async function waitForSocket(socketPath, child, timeoutMs = 3000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Firecracker exited before opening its API socket (${child.exitCode})`);
    try {
      await fs.promises.access(socketPath, fs.constants.R_OK | fs.constants.W_OK);
      return;
    } catch (_) {
      await new Promise((resolve) => setTimeout(resolve, 25));
    }
  }
  throw new Error(`Firecracker API socket did not appear within ${timeoutMs} ms`);
}

function capture(child, limit = 64 * 1024) {
  let stdout = "";
  let stderr = "";
  child.stdout.on("data", (chunk) => { stdout = (stdout + chunk).slice(-limit); });
  child.stderr.on("data", (chunk) => { stderr = (stderr + chunk).slice(-limit); });
  return () => ({ stdout, stderr });
}

async function terminate(child, graceMs = 1000) {
  if (!child || child.exitCode !== null) return;
  child.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => child.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, graceMs)),
  ]);
  if (child.exitCode === null) child.kill("SIGKILL");
}

class FirecrackerHandle {
  constructor({ child, socketPath, api, artifacts, startedAt, logs }) {
    this.schema = FIRECRACKER_SCHEMA;
    this.status = "RUNNING";
    this.executed = true;
    this.pid = child.pid;
    this.socketPath = socketPath;
    this.api = api;
    this.artifacts = artifacts;
    this.startedAt = startedAt;
    this._child = child;
    this._logs = logs;
  }

  async describe() {
    return apiRequest(this.socketPath, "GET", "/");
  }

  async stop() {
    await terminate(this._child);
    this.status = "STOPPED";
    return { status: this.status, logs: this._logs() };
  }
}

class FirecrackerRuntime {
  constructor({
    binary = "firecracker",
    socketRoot = process.platform === "linux" ? "/tmp" : os.tmpdir(),
    capabilityOptions = {},
    spawnImpl = spawn,
  } = {}) {
    this.binary = binary;
    this.socketRoot = socketRoot;
    this.capabilityOptions = capabilityOptions;
    this.spawnImpl = spawnImpl;
  }

  socketPath(instanceId) {
    const safe = String(instanceId).replace(/[^a-zA-Z0-9_.-]/g, "_");
    return path.join(this.socketRoot, `holotrade-${safe}.firecracker.sock`);
  }

  async startControlPlane(instanceId = `probe-${process.pid}`, timeoutMs = 3000) {
    const binary = await findExecutable(this.binary, this.capabilityOptions.envPath);
    if (!binary) return { status: "UNAVAILABLE", reasonCode: "EXECUTABLE_NOT_FOUND", executed: false };
    const socketPath = this.socketPath(instanceId);
    try { await fs.promises.unlink(socketPath); } catch (error) { if (error.code !== "ENOENT") throw error; }
    const child = this.spawnImpl(binary, ["--api-sock", socketPath, "--id", instanceId], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    const logs = capture(child);
    try {
      await waitForSocket(socketPath, child, timeoutMs);
      const version = await apiRequest(socketPath, "GET", "/version");
      await apiRequest(socketPath, "PUT", "/machine-config", {
        vcpu_count: 1,
        mem_size_mib: 128,
        smt: false,
      });
      const machine = await apiRequest(socketPath, "GET", "/machine-config");
      return {
        schema: FIRECRACKER_SCHEMA,
        status: "AVAILABLE",
        reasonCode: "API_CONTROL_PLANE_RESPONDED",
        executed: true,
        version: version.body && version.body.firecracker_version,
        machineConfig: machine.body,
        socketPath,
        child,
        logs,
      };
    } catch (error) {
      await terminate(child);
      return {
        schema: FIRECRACKER_SCHEMA,
        status: "ERROR",
        reasonCode: "API_CONTROL_PLANE_FAILED",
        executed: true,
        error: error.response ? error.response.body : error.message,
        logs: logs(),
      };
    }
  }

  async probeControlPlane(instanceId) {
    const result = await this.startControlPlane(instanceId);
    if (result.child) {
      await terminate(result.child);
      const logs = result.logs();
      try { await fs.promises.unlink(result.socketPath); } catch (_) { /* best effort */ }
      return { ...result, child: undefined, logs };
    }
    return result;
  }

  async preflight(spec = {}) {
    const capabilities = await detectRuntimeCapabilities({
      ...this.capabilityOptions,
      firecrackerBinary: this.binary,
      now: spec.now,
    });
    const artifactSpecs = [];
    if (spec.kernelPath) artifactSpecs.push({ path: spec.kernelPath, role: "guest-kernel" });
    if (spec.rootfsPath) artifactSpecs.push({ path: spec.rootfsPath, role: "rootfs" });
    for (const drive of spec.additionalDrives || []) artifactSpecs.push({ path: drive.path, role: `drive:${drive.id}` });
    let artifacts = [];
    let artifactError = null;
    try { artifacts = await hashArtifacts(artifactSpecs); } catch (error) { artifactError = error.message; }
    const missing = [];
    if (!spec.kernelPath) missing.push("KERNEL_PATH_REQUIRED");
    if (!spec.rootfsPath) missing.push("ROOTFS_PATH_REQUIRED");
    if (artifactError) missing.push("ARTIFACT_HASH_FAILED");
    return {
      schema: FIRECRACKER_SCHEMA,
      status: capabilities.launchable && missing.length === 0 ? "READY" : "UNAVAILABLE",
      ready: capabilities.launchable && missing.length === 0,
      capabilities,
      artifacts,
      blockers: [
        ...capabilities.findings.filter((item) =>
          ["host_os", "host_arch", "kvm", "firecracker"].includes(item.id) && item.status !== "AVAILABLE"
        ).map((item) => ({ code: `${item.id.toUpperCase()}_${item.reasonCode}`, finding: item })),
        ...missing.map((code) => ({ code })),
      ],
      artifactError,
    };
  }

  async launch(spec = {}) {
    const preflight = await this.preflight(spec);
    if (!preflight.ready) {
      return {
        schema: FIRECRACKER_SCHEMA,
        status: "UNAVAILABLE",
        executed: false,
        preflight,
      };
    }
    const instanceId = spec.instanceId || `vm-${Date.now()}`;
    const control = await this.startControlPlane(instanceId, spec.apiTimeoutMs || 3000);
    if (control.status !== "AVAILABLE") return { ...control, preflight };
    const { child, socketPath, logs } = control;
    try {
      await apiRequest(socketPath, "PUT", "/machine-config", {
        vcpu_count: spec.vcpuCount || 1,
        mem_size_mib: spec.memoryMiB || 128,
        smt: spec.smt === true,
      });
      await apiRequest(socketPath, "PUT", "/boot-source", {
        kernel_image_path: path.resolve(spec.kernelPath),
        boot_args: spec.bootArgs || "console=ttyS0 reboot=k panic=1 pci=off",
      });
      await apiRequest(socketPath, "PUT", "/drives/rootfs", {
        drive_id: "rootfs",
        path_on_host: path.resolve(spec.rootfsPath),
        is_root_device: true,
        is_read_only: spec.rootfsReadOnly !== false,
      });
      for (const drive of spec.additionalDrives || []) {
        await apiRequest(socketPath, "PUT", `/drives/${encodeURIComponent(drive.id)}`, {
          drive_id: drive.id,
          path_on_host: path.resolve(drive.path),
          is_root_device: false,
          is_read_only: drive.readOnly !== false,
        });
      }
      for (const network of spec.networkInterfaces || []) {
        await apiRequest(socketPath, "PUT", `/network-interfaces/${encodeURIComponent(network.id)}`, {
          iface_id: network.id,
          host_dev_name: network.hostDevice,
          ...(network.guestMac ? { guest_mac: network.guestMac } : {}),
        });
      }
      await apiRequest(socketPath, "PUT", "/actions", { action_type: "InstanceStart" });
      return new FirecrackerHandle({
        child,
        socketPath,
        api: control,
        artifacts: preflight.artifacts,
        startedAt: new Date().toISOString(),
        logs,
      });
    } catch (error) {
      await terminate(child);
      return {
        schema: FIRECRACKER_SCHEMA,
        status: "FAILED",
        executed: true,
        preflight,
        error: error.response ? error.response.body : error.message,
        logs: logs(),
      };
    }
  }
}

module.exports = {
  FIRECRACKER_SCHEMA,
  apiRequest,
  waitForSocket,
  FirecrackerHandle,
  FirecrackerRuntime,
};
