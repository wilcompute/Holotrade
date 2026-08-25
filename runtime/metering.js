"use strict";

const fs = require("node:fs");
const path = require("node:path");
const { findNamedFiles } = require("./capabilities.js");

const METER_SCHEMA = "holotrade.runtime-energy-meter.v1";

async function readInteger(file) {
  const value = (await fs.promises.readFile(file, "utf8")).trim();
  if (!/^\d+$/.test(value)) throw new Error(`energy counter is not an unsigned integer: ${file}`);
  return BigInt(value);
}

class RaplMeter {
  constructor(zones) {
    this.zones = Object.freeze(zones.map((zone) => Object.freeze(zone)));
  }

  static async discover(root = "/sys/class/powercap") {
    const discovered = await findNamedFiles(root, "energy_uj");
    // Package counters overlap their core/uncore descendants. Select root
    // zones so summing the readings does not double-count the host total.
    const files = discovered.filter((file) => !discovered.some((other) =>
      other !== file && path.dirname(file).startsWith(`${path.dirname(other)}${path.sep}`)
    ));
    const zones = [];
    for (const energyFile of files) {
      try {
        await fs.promises.access(energyFile, fs.constants.R_OK);
        const dir = path.dirname(energyFile);
        const maxFile = path.join(dir, "max_energy_range_uj");
        let maxMicrojoules = null;
        try { maxMicrojoules = await readInteger(maxFile); } catch (_) { /* optional */ }
        let name = path.basename(dir);
        try { name = (await fs.promises.readFile(path.join(dir, "name"), "utf8")).trim() || name; } catch (_) { /* optional */ }
        zones.push({ id: dir, name, energyFile, maxMicrojoules });
      } catch (_) {
        // An unreadable counter cannot meter delivery.
      }
    }
    return new RaplMeter(zones);
  }

  async snapshot(now = Date.now()) {
    if (this.zones.length === 0) {
      return { schema: METER_SCHEMA, source: "RAPL", scope: "HOST_TOP_LEVEL_POWERCAP_ZONES", status: "UNAVAILABLE", observedAtMs: now, readings: [] };
    }
    const readings = [];
    for (const zone of this.zones) {
      try {
        readings.push({ id: zone.id, name: zone.name, microjoules: await readInteger(zone.energyFile) });
      } catch (error) {
        readings.push({ id: zone.id, name: zone.name, error: error.code || error.message });
      }
    }
    return {
      schema: METER_SCHEMA,
      source: "RAPL",
      scope: "HOST_TOP_LEVEL_POWERCAP_ZONES",
      status: readings.some((item) => typeof item.microjoules === "bigint") ? "OBSERVED" : "UNAVAILABLE",
      observedAtMs: now,
      readings,
    };
  }

  delta(before, after) {
    if (!before || !after || before.source !== "RAPL" || after.source !== "RAPL") {
      throw new TypeError("RAPL snapshots are required");
    }
    const prior = new Map(before.readings.map((item) => [item.id, item]));
    const readings = [];
    let total = 0n;
    for (const current of after.readings) {
      const old = prior.get(current.id);
      if (!old || typeof old.microjoules !== "bigint" || typeof current.microjoules !== "bigint") continue;
      const zone = this.zones.find((item) => item.id === current.id);
      let change = current.microjoules - old.microjoules;
      let wrapped = false;
      if (change < 0n && zone && zone.maxMicrojoules !== null) {
        change += zone.maxMicrojoules;
        wrapped = true;
      }
      if (change < 0n) {
        readings.push({ id: current.id, status: "COUNTER_RESET" });
        continue;
      }
      total += change;
      readings.push({ id: current.id, name: current.name, microjoules: change, wrapped });
    }
    return {
      schema: METER_SCHEMA,
      source: "RAPL",
      scope: "HOST_TOP_LEVEL_POWERCAP_ZONES",
      status: readings.some((item) => typeof item.microjoules === "bigint") ? "MEASURED" : "UNAVAILABLE",
      durationMs: Math.max(0, after.observedAtMs - before.observedAtMs),
      totalMicrojoules: total,
      readings,
    };
  }
}

function parsePrometheus(text, metricPrefix = "kepler_") {
  const values = new Map();
  for (const raw of String(text).split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})?\s+([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$/);
    if (!match || !match[1].startsWith(metricPrefix)) continue;
    const value = Number(match[3]);
    if (!Number.isFinite(value)) continue;
    values.set(`${match[1]}${match[2] || ""}`, value);
  }
  return values;
}

class KeplerMeter {
  constructor(endpoint, { fetchImpl = globalThis.fetch, metricPattern = /^kepler_node_cpu_joules_total(?:\{|$)/ } = {}) {
    this.endpoint = endpoint;
    this.fetchImpl = fetchImpl;
    this.metricPattern = metricPattern;
  }

  async snapshot(now = Date.now()) {
    if (!this.endpoint || typeof this.fetchImpl !== "function") {
      return { schema: METER_SCHEMA, source: "KEPLER", scope: "CONFIGURED_PROMETHEUS_SERIES", status: "UNAVAILABLE", observedAtMs: now, readings: [] };
    }
    try {
      const response = await this.fetchImpl(this.endpoint);
      if (!response.ok) throw new Error(`HTTP_${response.status}`);
      const values = parsePrometheus(await response.text());
      const readings = [...values]
        .filter(([metric]) => this.metricPattern.test(metric))
        .map(([metric, joules]) => ({ metric, joules }));
      return {
        schema: METER_SCHEMA,
        source: "KEPLER",
        scope: "CONFIGURED_PROMETHEUS_SERIES",
        status: readings.length ? "OBSERVED" : "UNAVAILABLE",
        observedAtMs: now,
        readings,
      };
    } catch (error) {
      return {
        schema: METER_SCHEMA,
        source: "KEPLER",
        scope: "CONFIGURED_PROMETHEUS_SERIES",
        status: "UNAVAILABLE",
        observedAtMs: now,
        error: error.code || error.message,
        readings: [],
      };
    }
  }

  delta(before, after) {
    const prior = new Map(before.readings.map((item) => [item.metric, item.joules]));
    const readings = [];
    let totalJoules = 0;
    for (const current of after.readings) {
      if (!prior.has(current.metric)) continue;
      const joules = current.joules - prior.get(current.metric);
      if (joules < 0) {
        readings.push({ metric: current.metric, status: "COUNTER_RESET" });
        continue;
      }
      totalJoules += joules;
      readings.push({ metric: current.metric, joules });
    }
    return {
      schema: METER_SCHEMA,
      source: "KEPLER",
      scope: "CONFIGURED_PROMETHEUS_SERIES",
      status: readings.some((item) => Number.isFinite(item.joules)) ? "MEASURED" : "UNAVAILABLE",
      durationMs: Math.max(0, after.observedAtMs - before.observedAtMs),
      totalMicrojoules: BigInt(Math.round(totalJoules * 1_000_000)),
      readings,
    };
  }
}

function serializeMeasurement(value) {
  if (typeof value === "bigint") return value.toString(10);
  if (Array.isArray(value)) return value.map(serializeMeasurement);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, serializeMeasurement(item)]));
  }
  return value;
}

module.exports = {
  METER_SCHEMA,
  readInteger,
  RaplMeter,
  parsePrometheus,
  KeplerMeter,
  serializeMeasurement,
};
