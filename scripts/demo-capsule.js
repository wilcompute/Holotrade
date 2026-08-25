#!/usr/bin/env node
"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const net = require("node:net");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync, execFileSync } = require("node:child_process");
const { createStaticServer } = require("./serve.js");

const ROOT = fs.realpathSync(path.resolve(__dirname, ".."));
const DEFAULT_OUTPUT = path.join(ROOT, "artifacts", "demo-capsule");

const VIEWS = Object.freeze([
  { minute: "00:25", name: "exchange-filled", view: "exchange", action: "exchange" },
  { minute: "01:30", name: "balance-paired-result", view: "balance", action: "balance" },
  { minute: "02:25", name: "fabric-exact-topology", view: "fabric", action: "fabric" },
  { minute: "03:35", name: "execution-plan", view: "execution", action: "plan" },
  { minute: "04:15", name: "execution-running", view: "execution", action: "launch" },
  { minute: "05:05", name: "receipts-reconciled", view: "receipts", action: "receipt" },
]);

function sha256Bytes(bytes) {
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

function sha256File(file) {
  return sha256Bytes(fs.readFileSync(file));
}

function artifactEntry(file) {
  const absolute = path.resolve(ROOT, file);
  const stat = fs.statSync(absolute);
  return { path: file.replaceAll(path.sep, "/"), bytes: stat.size, sha256: sha256File(absolute) };
}

function criticalArtifacts() {
  const fixed = [
    "index.html",
    "holotrade.html",
    "README.md",
    "DEMO.md",
    "docs/holotrade.tex",
    "docs/holotrade.pdf",
    "js/substrate.js",
    "js/execution.js",
    "js/evidence.js",
    "js/projection.js",
    "js/w33-transition-certificate.js",
    "reservations/shape-reservation.js",
    "data/balancer_ab_64.json",
    "data/shape_reservation_demo.json",
    "rtl/holotrade_admit.v",
    "rtl/build/synth_generic.txt",
    "rtl/build/synth_ice40.txt",
  ];
  return fixed.filter((file) => fs.existsSync(path.join(ROOT, file))).map(artifactEntry);
}

function runCheck(name, command, args, outputDir) {
  const started = Date.now();
  const result = spawnSync(command, args, {
    cwd: ROOT,
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
    windowsHide: true,
  });
  const stdout = result.stdout || "";
  const stderr = result.stderr || (result.error ? String(result.error.message || result.error) : "");
  const log = `${stdout}${stderr ? `${stdout ? "\n" : ""}${stderr}` : ""}`;
  const logFile = path.join(outputDir, `${name}.log`);
  fs.writeFileSync(logFile, log);
  return {
    name,
    ok: result.status === 0 && !result.error,
    exitCode: result.status,
    signal: result.signal || null,
    durationMs: Date.now() - started,
    log: path.relative(ROOT, logFile).replaceAll(path.sep, "/"),
    logSha256: sha256File(logFile),
    error: result.error ? result.error.message : null,
  };
}

function discoverBrowser() {
  const candidates = process.platform === "win32"
    ? [
      process.env.CHROME_PATH,
      "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
      process.env.EDGE_PATH,
      "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
      "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    ]
    : [
      process.env.CHROME_PATH,
      "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
      process.env.EDGE_PATH,
      "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
      "/usr/bin/microsoft-edge",
      "/usr/bin/google-chrome",
      "/usr/bin/chromium",
      "/usr/bin/chromium-browser",
    ];
  return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || null;
}

function windowsPathIfNeeded(value, executable) {
  if (process.platform !== "win32" && /\.exe$/i.test(executable)) {
    return execFileSync("wslpath", ["-w", value], { encoding: "utf8" }).trim();
  }
  return value;
}

async function freePort() {
  return await new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close((error) => error ? reject(error) : resolve(port));
    });
  });
}

function jsonGet(url) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, { timeout: 1000 }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        try { resolve(JSON.parse(Buffer.concat(chunks).toString("utf8"))); }
        catch (error) { reject(error); }
      });
    });
    request.on("timeout", () => request.destroy(new Error("timeout")));
    request.on("error", reject);
  });
}

async function poll(fn, { timeoutMs = 15000, intervalMs = 100 } = {}) {
  const deadline = Date.now() + timeoutMs;
  let last;
  while (Date.now() < deadline) {
    try {
      const value = await fn();
      if (value) return value;
    } catch (error) {
      last = error;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error(`timed out waiting for browser${last ? `: ${last.message}` : ""}`);
}

class CdpClient {
  constructor(url) {
    if (typeof WebSocket !== "function") throw new Error("this Node runtime does not expose WebSocket");
    this.socket = new WebSocket(url);
    this.seq = 1;
    this.pending = new Map();
  }

  async open() {
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", () => reject(new Error("CDP websocket failed")), { once: true });
    });
    this.socket.addEventListener("message", (event) => {
      const message = JSON.parse(String(event.data));
      if (!message.id || !this.pending.has(message.id)) return;
      const { resolve, reject } = this.pending.get(message.id);
      this.pending.delete(message.id);
      if (message.error) reject(new Error(`${message.error.code}: ${message.error.message}`));
      else resolve(message.result || {});
    });
    return this;
  }

  send(method, params = {}) {
    const id = this.seq++;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.socket.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    try { this.socket.close(); } catch (_) { /* best effort */ }
  }
}

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "browser expression failed");
  return result.result && result.result.value;
}

async function waitForApp(cdp) {
  return poll(async () => evaluate(cdp,
    `document.readyState === "complete" &&
      (document.getElementById("exchangeStats")?.textContent.trim().length || 0) > 0 &&
      (document.getElementById("book")?.children.length || 0) > 0`
  ), { timeoutMs: 20000, intervalMs: 150 });
}

async function reloadApp(cdp, token) {
  await evaluate(cdp, `document.documentElement.dataset.capsuleReload = ${JSON.stringify(token)}`);
  await cdp.send("Page.reload", { ignoreCache: true });
  await poll(async () => evaluate(cdp,
    `document.readyState === "complete" && document.documentElement.dataset.capsuleReload !== ${JSON.stringify(token)}`
  ), { timeoutMs: 20000, intervalMs: 100 });
  await waitForApp(cdp);
}

async function click(cdp, selector) {
  const encoded = JSON.stringify(selector);
  const ok = await evaluate(cdp, `(() => { const el = document.querySelector(${encoded}); if (!el) return false; el.click(); return true; })()`);
  if (!ok) throw new Error(`demo element not found: ${selector}`);
  await new Promise((resolve) => setTimeout(resolve, 180));
}

async function screenshot(cdp, outputDir, name, metrics) {
  await cdp.send("Emulation.setDeviceMetricsOverride", metrics);
  const result = await cdp.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
  });
  const file = path.join(outputDir, `${name}.png`);
  fs.writeFileSync(file, Buffer.from(result.data, "base64"));
  return {
    file: path.relative(ROOT, file).replaceAll(path.sep, "/"),
    bytes: fs.statSync(file).size,
    sha256: sha256File(file),
    viewport: metrics,
  };
}

async function stateFingerprint(cdp) {
  const state = await evaluate(cdp, `(() => ({
    exchange: document.getElementById("exchangeStats")?.innerText || "",
    quote: document.getElementById("bestDecomp")?.innerText || "",
    book: Array.from(document.querySelectorAll("#book tr")).slice(0, 8).map(x => x.innerText),
    w33: document.getElementById("fabricStats")?.innerText || ""
  }))()`);
  return { digest: sha256Bytes(Buffer.from(JSON.stringify(state), "utf8")), state };
}

async function driveBrowser({ url, outputDir }) {
  const browser = discoverBrowser();
  if (!browser) return { available: false, reason: "Edge/Chrome/Chromium not found", screenshots: [] };
  const debugPort = await freePort();
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "holotrade-capsule-"));
  const profileArg = windowsPathIfNeeded(profile, browser);
  const child = spawn(browser, [
    "--headless=new",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-default-apps",
    "--disable-extensions",
    "--disable-gpu",
    "--disable-sync",
    "--hide-scrollbars",
    "--no-first-run",
    "--no-default-browser-check",
    "--remote-allow-origins=*",
    `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${profileArg}`,
    "--window-size=1440,1100",
    url,
  ], { stdio: "ignore", windowsHide: true });

  let cdp;
  try {
    const page = await poll(async () => {
      const pages = await jsonGet(`http://127.0.0.1:${debugPort}/json/list`);
      return pages.find((item) => item.type === "page" && item.webSocketDebuggerUrl);
    }, { timeoutMs: 20000 });
    cdp = await new CdpClient(page.webSocketDebuggerUrl.replace("localhost", "127.0.0.1")).open();
    await cdp.send("Page.enable");
    await cdp.send("Runtime.enable");
    // Freeze only the one-second simulation clock before establishing the
    // baseline.  The synchronous 220-step warm-up still runs, so screenshots
    // show the normal seeded demo state; asynchronous drift cannot race the
    // before/after reset comparison.
    await cdp.send("Page.addScriptToEvaluateOnNewDocument", {
      source: `(() => {
        const nativeSetInterval = window.setInterval.bind(window);
        window.setInterval = (fn, delay, ...args) => Number(delay) === 1000 ? 0 : nativeSetInterval(fn, delay, ...args);
      })();`,
    });
    await reloadApp(cdp, "baseline");
    const initialFingerprint = await stateFingerprint(cdp);
    const shots = [];
    const desktop = { width: 1440, height: 1100, deviceScaleFactor: 2, mobile: false };

    for (const stage of VIEWS) {
      if (stage.action === "exchange") await click(cdp, "#tkBuy");
      await click(cdp, `[data-view="${stage.view}"]`);
      if (stage.action === "balance") {
        await click(cdp, "#balancerToggle");
        await click(cdp, "#balancerToggle");
      } else if (stage.action === "fabric") {
        await evaluate(cdp, `document.getElementById("w33Canvas")?.dispatchEvent(new MouseEvent("mousemove", {clientX: 420, clientY: 320, bubbles: true}))`);
      } else if (stage.action === "plan") {
        await evaluate(cdp, `document.getElementById("planSeconds").value = "120"`);
        await click(cdp, "#planCreate");
      } else if (stage.action === "launch") {
        await click(cdp, "[data-place]");
      } else if (stage.action === "receipt") {
        await click(cdp, "[data-view=\"execution\"]");
        const hasHalt = await evaluate(cdp, `!!document.querySelector("[data-halt]")`);
        if (hasHalt) await click(cdp, "[data-halt]");
        await click(cdp, "[data-view=\"receipts\"]");
      }
      shots.push({ minute: stage.minute, ...(await screenshot(cdp, outputDir, stage.name, desktop)) });
    }

    await click(cdp, "[data-view=\"fabric\"]");
    shots.push({ minute: "mobile", ...(await screenshot(cdp, outputDir, "mobile-fabric", {
      width: 390, height: 844, deviceScaleFactor: 3, mobile: true,
    })) });

    // A hard reload is the product's reset contract.  Pause immediately and
    // compare only deterministic model surfaces (never wall-clock strings).
    await reloadApp(cdp, "restore");
    const restoredFingerprint = await stateFingerprint(cdp);
    return {
      available: true,
      executable: browser,
      initialFingerprint,
      restoredFingerprint,
      exactSeedRestored: initialFingerprint.digest === restoredFingerprint.digest,
      screenshots: shots,
    };
  } finally {
    if (cdp) {
      try { await cdp.send("Browser.close"); } catch (_) { /* best effort */ }
      cdp.close();
    }
    if (!child.killed) child.kill();
    try { fs.rmSync(profile, { recursive: true, force: true }); } catch (_) { /* browser may still own it */ }
  }
}

function verifyFrozenPackets() {
  const checks = [];
  const shapePath = path.join(ROOT, "data", "shape_reservation_demo.json");
  if (fs.existsSync(shapePath)) {
    const packet = JSON.parse(fs.readFileSync(shapePath, "utf8"));
    const body = { ...packet };
    delete body.packetDigest;
    const actual = `sha256:${sha256Bytes(Buffer.from(JSON.stringify(JSON.parse(EvidenceCanonical(body))), "utf8"))}`;
    checks.push({ name: "shape-reservation-packet", expected: packet.packetDigest, actual, ok: actual === packet.packetDigest });
  }
  return checks;
}

// Local canonicalization matching js/evidence.js without loading browser globals.
function EvidenceCanonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(EvidenceCanonical).join(",")}]`;
  return `{${Object.keys(value).filter((key) => value[key] !== undefined).sort()
    .map((key) => `${JSON.stringify(key)}:${EvidenceCanonical(value[key])}`).join(",")}}`;
}

async function listen(server) {
  return await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
}

async function main(argv = process.argv.slice(2)) {
  const outputFlag = argv.indexOf("--output");
  const outputDir = path.resolve(outputFlag >= 0 ? argv[outputFlag + 1] : DEFAULT_OUTPUT);
  const skipHeavy = argv.includes("--quick");
  const noBrowser = argv.includes("--no-browser");
  fs.mkdirSync(outputDir, { recursive: true });

  const testFiles = fs.readdirSync(path.join(ROOT, "tests"))
    .filter((name) => name.endsWith(".test.js"))
    .sort()
    .map((name) => path.join("tests", name));
  const checks = [runCheck("node-tests", process.execPath, ["--test", ...testFiles], outputDir)];
  if (!skipHeavy) {
    checks.push(runCheck("rtl-formal", process.execPath, ["scripts/run-yosys.js", "rtl/verify.ys"], outputDir));
    checks.push(runCheck("rtl-synthesis", process.execPath, ["scripts/run-yosys.js", "rtl/synth.ys"], outputDir));
    checks.push(runCheck("paper", process.execPath, ["scripts/run-paper.js"], outputDir));
  }

  const packetChecks = verifyFrozenPackets();
  const server = createStaticServer();
  const port = await listen(server);
  let browser;
  try {
    browser = noBrowser
      ? { available: false, reason: "disabled by --no-browser", screenshots: [] }
      : await driveBrowser({ url: `http://127.0.0.1:${port}`, outputDir });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }

  const manifestBody = {
    schema: "holotrade.demo-capsule.v1",
    generatedAt: new Date().toISOString(),
    sixMinuteScenario: VIEWS,
    checks,
    packetChecks,
    artifacts: criticalArtifacts(),
    browser,
    pass: checks.every((check) => check.ok) && packetChecks.every((check) => check.ok) &&
      (!browser.available || browser.exactSeedRestored),
    boundary: "Local reproducibility capsule. Browser screenshots and hashes are evidence of this build; they are not remote attestation or production execution evidence.",
  };
  const manifest = { ...manifestBody, manifestSha256: sha256Bytes(Buffer.from(EvidenceCanonical(manifestBody), "utf8")) };
  const manifestPath = path.join(outputDir, "manifest.json");
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  console.log(`HoloTrade demo capsule: ${manifest.pass ? "PASS" : "FAIL"}`);
  console.log(`Manifest: ${manifestPath}`);
  console.log(`Checks: ${checks.map((check) => `${check.name}=${check.ok ? "PASS" : "FAIL"}`).join(" ")}`);
  console.log(`Browser: ${browser.available ? `${browser.screenshots.length} screenshots; reset=${browser.exactSeedRestored}` : browser.reason}`);
  if (!manifest.pass) process.exitCode = 1;
  return manifest;
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 2;
  });
}

module.exports = {
  ROOT,
  VIEWS,
  EvidenceCanonical,
  artifactEntry,
  criticalArtifacts,
  discoverBrowser,
  sha256Bytes,
  sha256File,
  verifyFrozenPackets,
  main,
};
