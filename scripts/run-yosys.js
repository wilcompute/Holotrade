"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const ROOT = fs.realpathSync(path.resolve(__dirname, ".."));
const RTL_ROOT = fs.realpathSync(path.join(ROOT, "rtl"));
const PYTHON_RUNNER = [
  "from yowasp_yosys import run_yosys",
  "import sys",
  "sys.exit(run_yosys(sys.argv[1:]))",
].join("; ");

function isContained(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!path.isAbsolute(relative) && relative !== ".." && !relative.startsWith(`..${path.sep}`));
}

function resolveYosysScript(input) {
  if (typeof input !== "string" || input.length === 0) {
    throw new TypeError("usage: node scripts/run-yosys.js rtl/<script>.ys");
  }
  const resolved = path.resolve(ROOT, input);
  if (!isContained(RTL_ROOT, resolved) || path.extname(resolved).toLowerCase() !== ".ys") {
    throw new RangeError("Yosys script must be a .ys file inside rtl/");
  }
  if (!fs.existsSync(resolved)) throw new RangeError(`Yosys script not found: ${input}`);
  const realScript = fs.realpathSync(resolved);
  if (!isContained(RTL_ROOT, realScript) || !fs.statSync(realScript).isFile()) {
    throw new RangeError("Yosys script must resolve to a regular file inside rtl/");
  }
  return path.relative(ROOT, realScript);
}

function runCandidate(command, args) {
  const result = spawnSync(command, args, { cwd: ROOT, stdio: "inherit" });
  if (result.error) {
    if (result.error.code === "ENOENT") return null;
    throw result.error;
  }
  if (result.signal) {
    console.error(`${command} terminated by signal ${result.signal}`);
    return 1;
  }
  return result.status ?? 1;
}

function runYosys(script) {
  const relativeScript = resolveYosysScript(script);

  // Prefer native Yosys when present. Large generated W33 case tables are
  // prohibitively slow to parse through the WASM YoWASP frontend in CI, while
  // native Yosys runs the same checked scripts directly.
  let status = runCandidate("yosys", ["-s", relativeScript]);
  if (status !== null) return status;

  // Portable fallback used on hosts without a native package.
  status = runCandidate("yowasp-yosys", ["-s", relativeScript]);
  if (status !== null) return status;

  // Retain the repository's Windows Python-launcher path as a final fallback.
  status = runCandidate("py", ["-3", "-c", PYTHON_RUNNER, "-s", relativeScript]);
  if (status !== null) return status;

  console.error(
    "Unable to run Yosys: install native yosys, yowasp-yosys on PATH, or install yowasp-yosys for the Windows `py -3` interpreter."
  );
  return 127;
}

if (require.main === module) {
  try {
    process.exitCode = runYosys(process.argv[2]);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 2;
  }
}

module.exports = { resolveYosysScript, runYosys };
