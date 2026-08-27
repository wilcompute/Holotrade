#!/usr/bin/env node
/**
 * Run a GAP script, portably.
 *
 *   node scripts/run-gap.js analysis/w33_shape_catalogue.g
 *
 * GAP is a third independent check on the finite mathematics in this
 * repository. The JS analyses search combinatorially, the Python check
 * projects onto eigenspaces, and GAP works with the groups directly --
 * three unrelated routes to the same statements.
 *
 * Locating it is the fiddly part. The Windows build ships as a Cygwin
 * runtime whose launcher is an interactive .bat, and the binary cannot
 * start unless the Cygwin bin directory is on PATH -- without it the
 * process dies with "cannot open shared object file: cygwin1.dll" and an
 * exit code that looks like a GAP error rather than a launcher problem.
 * That is handled here so callers never see it.
 */

"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

/** Candidate installations, most specific first. */
function findGap() {
  if (process.env.GAP_BIN && fs.existsSync(process.env.GAP_BIN)) {
    return { exe: process.env.GAP_BIN, extraPath: process.env.GAP_CYGWIN_BIN || null };
  }

  // POSIX: a plain `gap` on PATH is enough
  const which = spawnSync(process.platform === "win32" ? "where" : "which", ["gap"], { encoding: "utf8" });
  if (which.status === 0 && which.stdout.trim()) {
    const first = which.stdout.trim().split(/\r?\n/)[0].trim();
    if (first && fs.existsSync(first) && !first.toLowerCase().endsWith(".bat")) {
      return { exe: first, extraPath: null };
    }
  }

  // A common mixed Windows/WSL setup invokes Windows node.exe from a WSL
  // shell.  process.platform is then win32 even though the actual GAP binary
  // is installed inside WSL.  Detect that bridge explicitly instead of
  // declaring GAP missing or asking every certificate to special-case it.
  if (process.platform === "win32") {
    const probe = spawnSync("wsl.exe", ["sh", "-lc",
      "command -v gap; printf '%s\\n%s\\n%s\\n' \"$HOME\" \"$PATH\" \"${LD_LIBRARY_PATH:-}\""], {
      encoding: "utf8",
    });
    if (probe.status === 0 && probe.stdout.trim()) {
      const lines = probe.stdout.trim().split(/\r?\n/);
      return {
        exe: "wsl.exe",
        extraPath: null,
        wsl: true,
        gap: lines[0],
        wslPath: (lines[1] ? lines[1] + "/.local/bin:" : "") +
          (lines[2] || "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"),
        wslLdLibraryPath: (lines[1] ? lines[1] + "/.local/lib:" : "") +
          (lines[3] || ""),
      };
    }
  }

  // Windows: the Cygwin-packaged installer
  const roots = [];
  for (const base of ["C:/Program Files", "C:/Program Files (x86)", "C:/"]) {
    let entries = [];
    try { entries = fs.readdirSync(base); } catch { continue; }
    for (const e of entries) {
      if (/^GAP[-\d.]*$/i.test(e)) roots.push(path.join(base, e));
    }
  }
  for (const root of roots.sort().reverse()) {
    const runtime = path.join(root, "runtime");
    let opt = [];
    try { opt = fs.readdirSync(path.join(runtime, "opt")); } catch { continue; }
    for (const d of opt) {
      const exe = path.join(runtime, "opt", d, "gap.exe");
      if (fs.existsSync(exe)) {
        return { exe, extraPath: path.join(runtime, "bin") };
      }
    }
  }
  return null;
}

function toWslPath(value) {
  const normalized = path.resolve(value).replace(/\\/g, "/");
  const drive = normalized.match(/^([A-Za-z]):\/(.*)$/);
  return drive ? `/mnt/${drive[1].toLowerCase()}/${drive[2]}` : normalized;
}

function runGap(scriptPath, { cwd = process.cwd(), quiet = false } = {}) {
  const found = findGap();
  if (!found) {
    return { ok: false, missing: true, stdout: "", stderr: "GAP not found" };
  }
  const env = { ...process.env };
  if (found.extraPath) {
    // the Cygwin DLLs must be resolvable or the binary will not start
    env.PATH = found.extraPath + path.delimiter + env.PATH;
  }
  const exe = found.wsl ? "wsl.exe" : found.exe;
  const args = found.wsl
    ? ["--cd", toWslPath(cwd), "/usr/bin/env", "PATH=" + found.wslPath,
       "LD_LIBRARY_PATH=" + found.wslLdLibraryPath,
       found.gap || "gap", "-q", "-b", "--nointeract", toWslPath(scriptPath)]
    : ["-q", "-b", "--nointeract", scriptPath];
  const res = spawnSync(exe, args, {
    cwd, env, encoding: "utf8", maxBuffer: 64 * 1024 * 1024,
  });
  if (!quiet && res.stdout) process.stdout.write(res.stdout);
  if (!quiet && res.stderr) process.stderr.write(res.stderr);
  return {
    ok: res.status === 0,
    missing: false,
    status: res.status,
    stdout: res.stdout || "",
    stderr: res.stderr || "",
    exe: found.wsl ? `${found.exe}:${found.gap}` : found.exe,
  };
}

if (require.main === module) {
  const script = process.argv[2];
  if (!script) {
    console.error("usage: node scripts/run-gap.js <script.g>");
    process.exit(2);
  }
  const found = findGap();
  if (!found) {
    console.error("GAP not found. Set GAP_BIN to the gap executable, and");
    console.error("GAP_CYGWIN_BIN to the Cygwin bin directory on Windows.");
    process.exit(3);
  }
  const res = runGap(path.resolve(script));
  process.exit(res.ok ? 0 : 1);
}

module.exports = { findGap, runGap, toWslPath };
