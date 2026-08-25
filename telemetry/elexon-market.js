"use strict";

// Primary-source wholesale-price adapter. Elexon Insights is the official
// Balancing and Settlement Code data platform; its Market Index Data endpoint
// is public and requires no API key.

const { canonicalSha256, sha256 } = require("./procfs.js");

const ENDPOINT = "https://data.elexon.co.uk/bmrs/api/v1/balancing/pricing/market-index";
const DEFAULT_QUERY = Object.freeze({
  from: "2026-08-01T00:00:00Z",
  to: "2026-08-02T00:00:00Z",
  dataProvider: "APXMIDP",
});

function sourceUrl(query = DEFAULT_QUERY) {
  const url = new URL(ENDPOINT);
  url.searchParams.set("from", query.from);
  url.searchParams.set("to", query.to);
  url.searchParams.set("dataProviders", query.dataProvider);
  url.searchParams.set("format", "json");
  return url.toString();
}

function normalizeRows(response, query = DEFAULT_QUERY) {
  if (!response || !Array.isArray(response.data)) throw new Error("Elexon response has no data array");
  const fromMs = Date.parse(query.from);
  const toMs = Date.parse(query.to);
  if (!Number.isFinite(fromMs) || !Number.isFinite(toMs) || !(fromMs < toMs)) {
    throw new RangeError("query must define a valid half-open UTC interval");
  }
  const rows = response.data
    .filter((row) => {
      const t = Date.parse(row.startTime);
      return row.dataProvider === query.dataProvider && t >= fromMs && t < toMs;
    })
    .map((row) => ({
      startTime: new Date(row.startTime).toISOString(),
      settlementDate: String(row.settlementDate),
      settlementPeriod: Number(row.settlementPeriod),
      dataProvider: String(row.dataProvider),
      priceGBPPerMWh: Number(row.price),
      volumeMWh: Number(row.volume),
    }))
    .sort((a, b) => a.startTime.localeCompare(b.startTime));
  for (const row of rows) {
    if (!Number.isInteger(row.settlementPeriod) || row.settlementPeriod < 1 || row.settlementPeriod > 50) {
      throw new Error(`invalid settlement period ${row.settlementPeriod}`);
    }
    if (!Number.isFinite(row.priceGBPPerMWh) || !Number.isFinite(row.volumeMWh) || row.volumeMWh < 0) {
      throw new Error("invalid Market Index price/volume row");
    }
  }
  if (!rows.length) throw new Error("Elexon response has no rows inside the requested half-open interval");
  return rows;
}

async function fetchMarketFixture(query = DEFAULT_QUERY) {
  const url = sourceUrl(query);
  const response = await fetch(url, {
    headers: { "user-agent": "HoloTrade-shadow-calibration/1.0" },
    signal: AbortSignal.timeout(30000),
  });
  const raw = Buffer.from(await response.arrayBuffer());
  if (!response.ok) throw new Error(`Elexon request failed: HTTP ${response.status}: ${raw.toString("utf8").slice(0, 240)}`);
  const providerResponse = JSON.parse(raw.toString("utf8"));
  const rows = normalizeRows(providerResponse, query);
  const body = {
    schema: "holotrade.telemetry-shadow.market.v1",
    evidence: "MEASURED_OFFICIAL_MARKET_DATA",
    retrievedAt: new Date().toISOString(),
    source: {
      authority: "Elexon Insights Solution",
      dataset: "Market Index Data (MID)",
      documentation: "https://bmrs.elexon.co.uk/api-documentation/endpoint/balancing/pricing/market-index",
      apiDocumentation: "https://developer.data.elexon.co.uk/",
      licence: "https://www.elexon.co.uk/bsc/data/open-data-requests/bsc-open-data-licence/",
      attribution: "Contains BSC information licensed under the BSC Open Data Licence.",
      url,
      httpStatus: response.status,
      contentType: response.headers.get("content-type"),
      responseBytes: raw.length,
      responseBytesSha256: sha256(raw),
      responseCanonicalSha256: canonicalSha256(providerResponse),
      note: "MID prices reflect short-term wholesale electricity trading in Great Britain; APXMIDP is the selected provider.",
    },
    query: { ...query, intervalConvention: "half-open [from,to) after filtering the API's inclusive response" },
    units: { price: "GBP/MWh", volume: "MWh" },
    providerResponseRawUtf8: raw.toString("utf8"),
    providerResponse,
    rows,
    rowsSha256: canonicalSha256(rows),
  };
  return { ...body, fixtureSha256: canonicalSha256(body) };
}

function verifyMarketFixture(fixture) {
  if (!fixture || fixture.schema !== "holotrade.telemetry-shadow.market.v1") return false;
  const { fixtureSha256, ...body } = fixture;
  if (fixtureSha256 !== canonicalSha256(body)) return false;
  if (fixture.rowsSha256 !== canonicalSha256(fixture.rows)) return false;
  if (sha256(Buffer.from(fixture.providerResponseRawUtf8, "utf8")) !== fixture.source.responseBytesSha256) return false;
  if (canonicalSha256(JSON.parse(fixture.providerResponseRawUtf8)) !== fixture.source.responseCanonicalSha256) return false;
  if (fixture.source.responseCanonicalSha256 !== canonicalSha256(fixture.providerResponse)) return false;
  const normalized = normalizeRows(fixture.providerResponse, fixture.query);
  return canonicalSha256(normalized) === fixture.rowsSha256;
}

module.exports = {
  ENDPOINT,
  DEFAULT_QUERY,
  sourceUrl,
  normalizeRows,
  fetchMarketFixture,
  verifyMarketFixture,
};
