#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const ROOT = path.resolve(__dirname, "..");
const SOURCE = path.join("docs", "holotrade.tex");
const WINDOWS_FALLBACK = "C:/Users/wiljd/tools/tectonic/tectonic.exe";

function run(command) {
  const result = spawnSync(command, [SOURCE, "--outdir", "docs"], {
    cwd: ROOT,
    stdio: "inherit",
  });
  if (result.error && result.error.code === "ENOENT") return null;
  if (result.error) throw result.error;
  return result.status ?? 1;
}

function compilePaper() {
  let status = run("tectonic");
  if (status !== null) return status;
  if (fs.existsSync(WINDOWS_FALLBACK)) {
    status = run(WINDOWS_FALLBACK);
    if (status !== null) return status;
  }
  console.error("Unable to compile paper: install Tectonic or provide the Windows fallback binary.");
  return 127;
}

if (require.main === module) {
  try {
    process.exitCode = compilePaper();
  } catch (error) {
    console.error(error.message);
    process.exitCode = 2;
  }
}

module.exports = { compilePaper };
