"use strict";

const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const DEFAULT_ROOT = fs.realpathSync(path.resolve(__dirname, ".."));
const HOST = "127.0.0.1";

const CONTENT_TYPES = Object.freeze({
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".ico": "image/x-icon",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".pdf": "application/pdf",
  ".svg": "image/svg+xml; charset=utf-8",
  ".tex": "text/plain; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
});

const SECURITY_HEADERS = Object.freeze({
  "Cache-Control": "no-store",
  "Content-Security-Policy": [
    "default-src 'self'",
    "base-uri 'none'",
    "connect-src 'self'",
    "font-src 'self' https://fonts.gstatic.com",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "img-src 'self' data:",
    "object-src 'none'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
  ].join("; "),
  "Cross-Origin-Opener-Policy": "same-origin",
  "Cross-Origin-Resource-Policy": "same-origin",
  "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
});

class RequestError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function isContained(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === "" || (!path.isAbsolute(relative) && relative !== ".." && !relative.startsWith(`..${path.sep}`));
}

function resolveRequestPath(requestTarget, root = DEFAULT_ROOT) {
  if (typeof requestTarget !== "string" || !requestTarget.startsWith("/") || requestTarget.startsWith("//")) {
    throw new RequestError(400, "bad request");
  }

  // Inspect the decoded origin-form path before WHATWG URL normalization;
  // URL would otherwise collapse literal and percent-encoded dot segments.
  const rawPath = requestTarget.split("?", 1)[0];
  let decodedRawPath;
  try {
    decodedRawPath = decodeURIComponent(rawPath);
  } catch {
    throw new RequestError(400, "bad request");
  }
  if (decodedRawPath.includes("\0") || decodedRawPath.includes("\\")) {
    throw new RequestError(400, "bad request");
  }
  const rawSegments = decodedRawPath.split("/");
  if (rawSegments.includes("..")) {
    throw new RequestError(403, "forbidden");
  }
  if (rawSegments.some((segment) => segment.startsWith(".") && segment.length > 1)) {
    throw new RequestError(403, "forbidden");
  }

  let parsed;
  try {
    parsed = new URL(requestTarget, "http://127.0.0.1");
  } catch {
    throw new RequestError(400, "bad request");
  }

  let decoded;
  try {
    decoded = decodeURIComponent(parsed.pathname);
  } catch {
    throw new RequestError(400, "bad request");
  }

  if (decoded.includes("\0") || decoded.includes("\\")) {
    throw new RequestError(400, "bad request");
  }
  const segments = decoded.split("/");
  if (segments.includes("..")) {
    throw new RequestError(403, "forbidden");
  }
  if (segments.some((segment) => segment.startsWith(".") && segment.length > 1)) {
    throw new RequestError(403, "forbidden");
  }

  const relative = decoded.replace(/^\/+/, "") || "index.html";
  const candidate = path.resolve(root, relative);
  if (!isContained(root, candidate)) throw new RequestError(403, "forbidden");
  return candidate;
}

function writeError(res, status, message, headOnly = false) {
  const body = Buffer.from(`${message}\n`, "utf8");
  res.writeHead(status, {
    ...SECURITY_HEADERS,
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": body.length,
  });
  res.end(headOnly ? undefined : body);
}

async function serve(req, res, root) {
  const headOnly = req.method === "HEAD";
  if (req.method !== "GET" && !headOnly) {
    res.setHeader("Allow", "GET, HEAD");
    writeError(res, 405, "method not allowed");
    return;
  }

  try {
    let candidate = resolveRequestPath(req.url, root);
    let target = await fs.promises.realpath(candidate);
    if (!isContained(root, target)) throw new RequestError(403, "forbidden");

    let stat = await fs.promises.stat(target);
    if (stat.isDirectory()) {
      candidate = path.join(target, "index.html");
      target = await fs.promises.realpath(candidate);
      if (!isContained(root, target)) throw new RequestError(403, "forbidden");
      stat = await fs.promises.stat(target);
    }
    if (!stat.isFile()) throw new RequestError(404, "not found");

    res.writeHead(200, {
      ...SECURITY_HEADERS,
      "Content-Type": CONTENT_TYPES[path.extname(target).toLowerCase()] || "application/octet-stream",
      "Content-Length": stat.size,
    });
    if (headOnly) {
      res.end();
      return;
    }

    const stream = fs.createReadStream(target);
    stream.on("error", () => {
      if (!res.headersSent) writeError(res, 500, "internal server error");
      else res.destroy();
    });
    stream.pipe(res);
  } catch (error) {
    if (error instanceof RequestError) {
      writeError(res, error.status, error.message, headOnly);
      return;
    }
    if (error && ["ENOENT", "ENOTDIR"].includes(error.code)) {
      writeError(res, 404, "not found", headOnly);
      return;
    }
    writeError(res, 500, "internal server error", headOnly);
  }
}

function createStaticServer(root = DEFAULT_ROOT) {
  const resolvedRoot = fs.realpathSync(path.resolve(root));
  return http.createServer((req, res) => {
    void serve(req, res, resolvedRoot);
  });
}

function readPort(value) {
  if (value === undefined || value === "") return 8080;
  if (!/^[0-9]+$/.test(value)) throw new RangeError("PORT must be an integer in [1, 65535]");
  const port = Number(value);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new RangeError("PORT must be an integer in [1, 65535]");
  }
  return port;
}

if (require.main === module) {
  let port;
  try {
    port = readPort(process.env.PORT);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }

  if (port !== undefined) {
    const server = createStaticServer();
    server.on("error", (error) => {
      console.error(`Holotrade server failed: ${error.message}`);
      process.exitCode = 1;
    });
    server.listen(port, HOST, () => {
      console.log(`Holotrade on http://${HOST}:${port}`);
    });
  }
}

module.exports = { SECURITY_HEADERS, createStaticServer, isContained, readPort, resolveRequestPath };
