// Bind reversible-history accounting into the same signed receipt metadata
// envelope as immutable W33 carrier identity.
//
// This composes the parallel w33-profiled-receipt track with
// reversible-compute-settlement.  The complete history summary is carried in
// metadata and receives its own SHA-256 commitment.  Because runtime/receipt.js
// signs the whole delivery payload including metadata, a signed receipt commits
// to plan/profile/carrier/deployment identity *and* the typed history/erasure
// ledger.

"use strict";

const crypto = require("node:crypto");
const W33 = require("./w33-profiled-receipt.js");
const Reversible = require("./reversible-compute-settlement.js");

const SCHEMA = "holotrade.w33-reversible-receipt.v1";

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function sha256(value) {
  return `sha256:${crypto.createHash("sha256").update(stable(value)).digest("hex")}`;
}

function accountingBinding(plan, profile, ledger) {
  if (!(ledger instanceof Reversible.HistoryLedger)) throw new TypeError("HistoryLedger required");
  if (ledger.planDigest != null && ledger.planDigest !== plan.digest) {
    throw new Error("history ledger plan digest does not match execution plan");
  }
  if (ledger.profileDigest != null && ledger.profileDigest !== profile.digest) {
    throw new Error("history ledger profile digest does not match immutable W33 profile");
  }
  const summary = ledger.summary();
  const core = {
    schema: Reversible ? "holotrade.reversible-history-accounting.v1" : null,
    planDigest: plan.digest,
    profileDigest: profile.digest,
    summary,
  };
  return Object.freeze({ ...core, accountingDigest: sha256(core) });
}

function attachToReceiptMetadata(metadata, plan, profile, vm, contract, ledger) {
  const withW33 = W33.attachToReceiptMetadata(metadata, plan, profile, vm, contract);
  const history = accountingBinding(plan, profile, ledger);
  return Object.freeze({
    ...withW33,
    reversibleHistory: Object.freeze({
      schema: SCHEMA,
      ...history,
    }),
  });
}

function verifyReceiptMetadata(metadata, plan, profile, vm, contract, ledger) {
  if (!metadata || typeof metadata !== "object") return false;
  if (!W33.verifyReceiptMetadata(metadata.w33, plan, profile, vm, contract)) return false;
  let expected;
  try { expected = attachToReceiptMetadata({}, plan, profile, vm, contract, ledger); }
  catch (_) { return false; }
  return stable(metadata.reversibleHistory) === stable(expected.reversibleHistory);
}

module.exports = {
  SCHEMA,
  accountingBinding,
  attachToReceiptMetadata,
  verifyReceiptMetadata,
};
