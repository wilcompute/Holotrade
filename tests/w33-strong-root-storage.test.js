const assert = require("node:assert/strict");
const test = require("node:test");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const S = require(path.join(root, "js/w33-strong-root-storage.js"));

test("only strong roots accrue blob-seconds and byte-seconds", () => {
  const ledger = new S.StrongRootStorageLedger({ strongBlobSecondUSD: 0.001, strongByteSecondUSD: 0 });
  ledger.retain({ rootId: "live", rootType: S.ROOT_TYPE.LIVE_VM, strength: S.STRENGTH.STRONG, blobs: 10, bytes: 1000, seconds: 5 });
  ledger.retain({ rootId: "receipt", rootType: S.ROOT_TYPE.RECEIPT_AUDIT, strength: S.STRENGTH.HASH_ONLY, blobs: 10, bytes: 1000, seconds: 100 });
  const out = ledger.summary();
  assert.equal(out.strongBlobSeconds, 50);
  assert.equal(out.strongByteSeconds, 5000);
  assert.equal(out.hashOnlySeconds, 100);
  assert.equal(out.charges.strongBlobSecondUSD, 0.05);
});

test("checkpoint/history/shared-handle retention composes additively", () => {
  const ledger = new S.StrongRootStorageLedger();
  ledger.retain({ rootId: "cp", rootType: S.ROOT_TYPE.CHECKPOINT, strength: S.STRENGTH.STRONG, blobs: 3, seconds: 2 });
  ledger.retain({ rootId: "hist", rootType: S.ROOT_TYPE.HISTORY, strength: S.STRENGTH.STRONG, blobs: 5, seconds: 4 });
  ledger.retain({ rootId: "handle", rootType: S.ROOT_TYPE.SHARED_HANDLE, strength: S.STRENGTH.STRONG, blobs: 2, seconds: 7 });
  assert.equal(ledger.summary().strongBlobSeconds, 6 + 20 + 14);
});

test("receipt extension preserves base execution cost and adds explicit storage tariff", () => {
  const ledger = new S.StrongRootStorageLedger({ strongBlobSecondUSD: 0.01 });
  ledger.retain({ rootId: "hist", rootType: S.ROOT_TYPE.HISTORY, strength: S.STRENGTH.STRONG, blobs: 4, seconds: 5 });
  const receipt = S.extendReceipt({ cost: 2.5, joules: 7 }, ledger);
  assert.equal(receipt.cost, 2.5);
  assert.equal(receipt.joules, 7);
  assert.equal(receipt.w33StrongRootStorage.charges.supplementalUSD, 0.2);
  assert.equal(receipt.totalCostWithStoragePolicy, 2.7);
});

test("storage Pareto frontier separates time, retained state and irreversible erasure", () => {
  const rows = [
    { id: "fast-big", latencySeconds: 1, strongBlobSeconds: 100, irreversibleEraseBits: 0 },
    { id: "balanced", latencySeconds: 2, strongBlobSeconds: 20, irreversibleEraseBits: 0 },
    { id: "slow-small", latencySeconds: 4, strongBlobSeconds: 5, irreversibleEraseBits: 0 },
    { id: "dominated", latencySeconds: 5, strongBlobSeconds: 25, irreversibleEraseBits: 1 },
  ];
  assert.deepEqual(S.storageParetoFrontier(rows).map((x) => x.id), ["fast-big", "balanced", "slow-small"]);
});

test("negative tariffs, sizes or durations are rejected", () => {
  assert.throws(() => new S.StrongRootStorageLedger({ strongBlobSecondUSD: -1 }), /nonnegative/);
  const ledger = new S.StrongRootStorageLedger();
  assert.throws(() => ledger.retain({ rootId: "x", rootType: S.ROOT_TYPE.LIVE_VM, strength: S.STRENGTH.STRONG, blobs: -1, seconds: 1 }), /nonnegative/);
  assert.throws(() => ledger.retain({ rootId: "x", rootType: S.ROOT_TYPE.LIVE_VM, strength: S.STRENGTH.STRONG, blobs: 1, seconds: -1 }), /nonnegative/);
});
