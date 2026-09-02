// Strong-root storage economics for persistent W33 execution state.
//
// W33 temporal GC distinguishes STRONG roots (live VM, checkpoint, history,
// shared handle) from HASH_ONLY audit roots.  This module mirrors that runtime
// distinction into Holotrade accounting:
//
//   strong blob-seconds = sum(live reachable blob count * retention seconds)
//
// Hash-only receipt/audit anchors preserve identity without pinning bytes and
// therefore do not accrue strong-root storage charges.  Tariffs are explicit
// market policy; they are not thermodynamic constants.

"use strict";

const ROOT_TYPE = Object.freeze({
  LIVE_VM: "LIVE_VM",
  CHECKPOINT: "CHECKPOINT",
  HISTORY: "HISTORY",
  SHARED_HANDLE: "SHARED_HANDLE",
  RECEIPT_AUDIT: "RECEIPT_AUDIT",
});

const STRENGTH = Object.freeze({ STRONG: "STRONG", HASH_ONLY: "HASH_ONLY" });

function nonnegative(value, name) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) throw new RangeError(`${name} must be finite nonnegative`);
  return n;
}

function integer(value, name) {
  const n = Number(value);
  if (!Number.isSafeInteger(n) || n < 0) throw new RangeError(`${name} must be nonnegative safe integer`);
  return n;
}

class StrongRootStorageLedger {
  constructor({ strongBlobSecondUSD = 0, strongByteSecondUSD = 0 } = {}) {
    this.strongBlobSecondUSD = nonnegative(strongBlobSecondUSD, "strongBlobSecondUSD");
    this.strongByteSecondUSD = nonnegative(strongByteSecondUSD, "strongByteSecondUSD");
    this.strongBlobSeconds = 0;
    this.strongByteSeconds = 0;
    this.hashOnlySeconds = 0;
    this.events = [];
  }

  retain({ rootId, rootType, strength, blobs = 0, bytes = 0, seconds }) {
    if (!rootId) throw new TypeError("rootId required");
    if (!Object.values(ROOT_TYPE).includes(rootType)) throw new TypeError("unknown rootType");
    if (!Object.values(STRENGTH).includes(strength)) throw new TypeError("unknown root strength");
    const b = integer(blobs, "blobs");
    const size = integer(bytes, "bytes");
    const duration = nonnegative(seconds, "seconds");
    const blobSeconds = strength === STRENGTH.STRONG ? b * duration : 0;
    const byteSeconds = strength === STRENGTH.STRONG ? size * duration : 0;
    if (strength === STRENGTH.STRONG) {
      this.strongBlobSeconds += blobSeconds;
      this.strongByteSeconds += byteSeconds;
    } else {
      this.hashOnlySeconds += duration;
    }
    const event = Object.freeze({
      seq: this.events.length + 1,
      rootId: String(rootId),
      rootType,
      strength,
      blobs: b,
      bytes: size,
      seconds: duration,
      blobSeconds,
      byteSeconds,
    });
    this.events.push(event);
    return event;
  }

  charges() {
    const blobUSD = this.strongBlobSeconds * this.strongBlobSecondUSD;
    const byteUSD = this.strongByteSeconds * this.strongByteSecondUSD;
    return Object.freeze({
      strongBlobSecondUSD: blobUSD,
      strongByteSecondUSD: byteUSD,
      supplementalUSD: blobUSD + byteUSD,
    });
  }

  summary() {
    return Object.freeze({
      schema: "holotrade.w33-strong-root-storage.v1",
      strongBlobSeconds: this.strongBlobSeconds,
      strongByteSeconds: this.strongByteSeconds,
      hashOnlySeconds: this.hashOnlySeconds,
      tariffs: Object.freeze({
        strongBlobSecondUSD: this.strongBlobSecondUSD,
        strongByteSecondUSD: this.strongByteSecondUSD,
      }),
      charges: this.charges(),
      events: Object.freeze([...this.events]),
    });
  }
}

function extendReceipt(baseReceipt, ledger) {
  if (!baseReceipt || typeof baseReceipt !== "object") throw new TypeError("base receipt required");
  if (!(ledger instanceof StrongRootStorageLedger)) throw new TypeError("StrongRootStorageLedger required");
  const storage = ledger.summary();
  const base = nonnegative(baseReceipt.totalCostWithHistoryPolicy ?? baseReceipt.cost ?? 0, "base cost");
  return Object.freeze({
    ...baseReceipt,
    w33StrongRootStorage: storage,
    totalCostWithStoragePolicy: base + storage.charges.supplementalUSD,
  });
}

function dominatesStorage(a, b) {
  const keys = ["latencySeconds", "strongBlobSeconds", "irreversibleEraseBits"];
  const av = keys.map((k) => nonnegative(a[k], k));
  const bv = keys.map((k) => nonnegative(b[k], k));
  return av.every((x, i) => x <= bv[i]) && av.some((x, i) => x < bv[i]);
}

function storageParetoFrontier(candidates) {
  if (!Array.isArray(candidates)) throw new TypeError("candidate array required");
  return candidates
    .map((row, i) => ({ ...row, _i: i }))
    .filter((row, i, rows) => !rows.some((other, j) => i !== j && dominatesStorage(other, row)))
    .sort((a, b) => a.latencySeconds - b.latencySeconds || a.strongBlobSeconds - b.strongBlobSeconds || a.irreversibleEraseBits - b.irreversibleEraseBits || a._i - b._i)
    .map(({ _i, ...row }) => Object.freeze(row));
}

module.exports = {
  ROOT_TYPE,
  STRENGTH,
  StrongRootStorageLedger,
  extendReceipt,
  dominatesStorage,
  storageParetoFrontier,
};
