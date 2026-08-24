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

  // pipx/pip installs this console entry point on every supported host.
  // If it is not on PATH, retain the repository's existing Windows
  // Python-launcher path as the explicit fallback.
  let status = runCandidate("yowasp-yosys", ["-s", relativeScript]);
  if (status !== null) return status;

  status = runCandidate("py", ["-3", "-c", PYTHON_RUNNER, "-s", relativeScript]);
  if (status !== null) return status;

  console.error(
    "Unable to run Yosys: install yowasp-yosys on PATH or install it for the Windows `py -3` interpreter."
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
