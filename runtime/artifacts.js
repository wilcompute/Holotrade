"use strict";

const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const ARTIFACT_SCHEMA = "holotrade.runtime-artifact.v1";

function sha256Bytes(value) {
  const bytes = Buffer.isBuffer(value) ? value : Buffer.from(value);
  return `sha256:${crypto.createHash("sha256").update(bytes).digest("hex")}`;
}

async function sha256File(filePath) {
  const hash = crypto.createHash("sha256");
  await new Promise((resolve, reject) => {
    const input = fs.createReadStream(filePath);
    input.on("error", reject);
    input.on("data", (chunk) => hash.update(chunk));
    input.on("end", resolve);
  });
  return `sha256:${hash.digest("hex")}`;
}

async function hashArtifact(filePath, { role = "artifact" } = {}) {
  if (typeof filePath !== "string" || filePath.length === 0) {
    throw new TypeError("artifact path must be a non-empty string");
  }
  const absolutePath = path.resolve(filePath);
  const link = await fs.promises.lstat(absolutePath, { bigint: true });
  if (link.isSymbolicLink()) {
    throw new Error(`artifact must not be a symbolic link: ${absolutePath}`);
  }
  if (!link.isFile()) {
    throw new Error(`artifact must be a regular file: ${absolutePath}`);
  }
  const digest = await sha256File(absolutePath);
  const after = await fs.promises.stat(absolutePath, { bigint: true });
  if (after.size !== link.size || after.mtimeNs !== link.mtimeNs) {
    throw new Error(`artifact changed while hashing: ${absolutePath}`);
  }
  if (after.size > BigInt(Number.MAX_SAFE_INTEGER)) {
    throw new RangeError(`artifact is too large to represent exactly: ${absolutePath}`);
  }
  return Object.freeze({
    schema: ARTIFACT_SCHEMA,
    role: String(role),
    path: absolutePath,
    bytes: Number(after.size),
    digest,
  });
}

async function hashArtifacts(specs) {
  if (!Array.isArray(specs)) throw new TypeError("artifact specs must be an array");
  const records = [];
  for (const spec of specs) {
    if (typeof spec === "string") records.push(await hashArtifact(spec));
    else if (spec && typeof spec === "object") {
      records.push(await hashArtifact(spec.path, { role: spec.role }));
    } else {
      throw new TypeError("each artifact must be a path or {path, role}");
    }
  }
  return Object.freeze(records);
}

module.exports = {
  ARTIFACT_SCHEMA,
  sha256Bytes,
  sha256File,
  hashArtifact,
  hashArtifacts,
};
