"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const D = require("../scripts/demo-capsule.js");

test("the capsule maps every segment of the six-minute runbook", () => {
  assert.deepEqual(D.VIEWS.map((stage) => stage.minute), ["00:25", "01:30", "02:25", "03:35", "04:15", "05:05"]);
  assert.deepEqual(new Set(D.VIEWS.map((stage) => stage.action)),
    new Set(["exchange", "balance", "fabric", "plan", "launch", "receipt"]));
});

test("canonicalization and artifact hashes are stable", () => {
  assert.equal(D.EvidenceCanonical({ z: 1, a: [true, "x"] }), '{"a":[true,"x"],"z":1}');
  const first = D.artifactEntry("index.html");
  const second = D.artifactEntry(path.join("index.html"));
  assert.deepEqual(first, second);
  assert.match(first.sha256, /^[0-9a-f]{64}$/);
  assert.equal(first.bytes, fs.statSync(path.join(D.ROOT, "index.html")).size);
});

test("the tracked shape packet verifies its self-address", () => {
  const checks = D.verifyFrozenPackets();
  assert.ok(checks.length >= 1);
  assert.ok(checks.every((check) => check.ok), JSON.stringify(checks));
});

test("critical demo artifacts are present, nonempty, and uniquely named", () => {
  const entries = D.criticalArtifacts();
  assert.ok(entries.length >= 12);
  assert.equal(new Set(entries.map((entry) => entry.path)).size, entries.length);
  assert.ok(entries.every((entry) => entry.bytes > 0));
  assert.ok(entries.every((entry) => /^[0-9a-f]{64}$/.test(entry.sha256)));
});
