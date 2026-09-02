// ============================================================================
// REVERSIBLE COMPUTE + HISTORY + ERASURE SETTLEMENT
//
// Holotrade already settles modeled device delivery in node-seconds, dollars
// and joules.  This module adds a *typed* accounting plane for reversible
// computation:
//
//   REVERSIBLE_COMPUTE  - logical work that creates certified undo history
//   HISTORY_RETAIN      - keeping that history live for some duration
//   UNCOMPUTE           - consuming history to restore work state reversibly
//   DISCARD_HISTORY     - an explicitly irreversible erasure boundary
//
// Only DISCARD_HISTORY receives a Landauer lower-bound calculation.
// The lower bound k_B T ln 2 per erased bit is a thermodynamic theorem about
// logically irreversible erasure under ideal assumptions; it is NOT a measured
// energy draw and is therefore never silently added to ExecutionEngine joules.
//
// Price policy is also separate.  Default supplemental tariffs are zero.  A
// caller may explicitly price reversible operations, history-bit-seconds, or
// discarded bits, but those are market/policy numbers, not physical constants.
// ============================================================================

(function (root) {
  "use strict";

  const K_B = 1.380649e-23; // J/K, exact SI value
  const LN2 = Math.log(2);

  const RESOURCE = Object.freeze({
    REVERSIBLE_COMPUTE: "REVERSIBLE_COMPUTE",
    HISTORY_RETAIN: "HISTORY_RETAIN",
    UNCOMPUTE: "UNCOMPUTE",
    DISCARD_HISTORY: "DISCARD_HISTORY",
  });

  function finiteNonnegative(value, name) {
    const x = Number(value);
    if (!Number.isFinite(x) || x < 0) throw new RangeError(`${name} must be a finite nonnegative number`);
    return x;
  }

  function finitePositive(value, name) {
    const x = Number(value);
    if (!Number.isFinite(x) || x <= 0) throw new RangeError(`${name} must be a finite positive number`);
    return x;
  }

  function integerNonnegative(value, name) {
    const x = Number(value);
    if (!Number.isSafeInteger(x) || x < 0) throw new RangeError(`${name} must be a nonnegative safe integer`);
    return x;
  }

  function stableObject(value) {
    if (Array.isArray(value)) return value.map(stableObject);
    if (value && typeof value === "object") {
      const out = {};
      for (const key of Object.keys(value).sort()) out[key] = stableObject(value[key]);
      return out;
    }
    return value;
  }

  function defaultTariffs() {
    return Object.freeze({
      reversibleOpUSD: 0,
      historyBitSecondUSD: 0,
      discardBitUSD: 0,
    });
  }

  function normalizeTariffs(policy = {}) {
    const base = defaultTariffs();
    return Object.freeze({
      reversibleOpUSD: finiteNonnegative(policy.reversibleOpUSD ?? base.reversibleOpUSD, "reversibleOpUSD"),
      historyBitSecondUSD: finiteNonnegative(policy.historyBitSecondUSD ?? base.historyBitSecondUSD, "historyBitSecondUSD"),
      discardBitUSD: finiteNonnegative(policy.discardBitUSD ?? base.discardBitUSD, "discardBitUSD"),
    });
  }

  function landauerFloorJoules(bits, temperatureK) {
    const n = integerNonnegative(bits, "bits");
    const t = finitePositive(temperatureK, "temperatureK");
    return n * K_B * t * LN2;
  }

  class HistoryLedger {
    constructor({ planDigest = null, profileDigest = null, tariffs = {} } = {}) {
      this.planDigest = planDigest;
      this.profileDigest = profileDigest;
      this.tariffs = normalizeTariffs(tariffs);
      this.liveHistoryBits = 0;
      this.peakHistoryBits = 0;
      this.reversibleOps = 0;
      this.uncomputeOps = 0;
      this.historyBitSeconds = 0;
      this.discardedBits = 0;
      this.landauerFloorJoules = 0;
      this.measuredErasureJoules = 0;
      this.hasMeasuredErasureEnergy = false;
      this.events = [];
      this.seq = 0;
    }

    append(type, fields = {}) {
      if (!Object.values(RESOURCE).includes(type)) throw new TypeError(`unknown reversible resource type: ${type}`);
      const event = Object.freeze({
        seq: ++this.seq,
        type,
        liveHistoryBitsAfter: this.liveHistoryBits,
        ...stableObject(fields),
      });
      this.events.push(event);
      return event;
    }

    recordCompute({ logicalOps = 1, historyBitsCreated = 0, label = null } = {}) {
      const ops = integerNonnegative(logicalOps, "logicalOps");
      const bits = integerNonnegative(historyBitsCreated, "historyBitsCreated");
      this.reversibleOps += ops;
      this.liveHistoryBits += bits;
      this.peakHistoryBits = Math.max(this.peakHistoryBits, this.liveHistoryBits);
      return this.append(RESOURCE.REVERSIBLE_COMPUTE, {
        logicalOps: ops,
        historyBitsCreated: bits,
        label,
      });
    }

    retainHistory({ bits = this.liveHistoryBits, seconds, label = null } = {}) {
      const retained = integerNonnegative(bits, "bits");
      const duration = finiteNonnegative(seconds, "seconds");
      if (retained > this.liveHistoryBits) throw new RangeError("cannot retain more history bits than are live");
      const bitSeconds = retained * duration;
      this.historyBitSeconds += bitSeconds;
      return this.append(RESOURCE.HISTORY_RETAIN, {
        bits: retained,
        seconds: duration,
        bitSeconds,
        label,
      });
    }

    recordUncompute({ logicalOps = 1, historyBitsRetired = 0, label = null } = {}) {
      const ops = integerNonnegative(logicalOps, "logicalOps");
      const bits = integerNonnegative(historyBitsRetired, "historyBitsRetired");
      if (bits > this.liveHistoryBits) throw new RangeError("cannot uncompute more history bits than are live");
      this.uncomputeOps += ops;
      this.liveHistoryBits -= bits;
      return this.append(RESOURCE.UNCOMPUTE, {
        logicalOps: ops,
        historyBitsRetired: bits,
        irreversible: false,
        label,
      });
    }

    discardHistory({ bits, temperatureK, measuredJoules = null, label = null } = {}) {
      const erased = integerNonnegative(bits, "bits");
      const temp = finitePositive(temperatureK, "temperatureK");
      if (erased > this.liveHistoryBits) throw new RangeError("cannot discard more history bits than are live");
      const floor = landauerFloorJoules(erased, temp);
      let measured = null;
      if (measuredJoules != null) {
        measured = finiteNonnegative(measuredJoules, "measuredJoules");
        this.measuredErasureJoules += measured;
        this.hasMeasuredErasureEnergy = true;
      }
      this.liveHistoryBits -= erased;
      this.discardedBits += erased;
      this.landauerFloorJoules += floor;
      return this.append(RESOURCE.DISCARD_HISTORY, {
        bits: erased,
        temperatureK: temp,
        landauerFloorJoules: floor,
        measuredJoules: measured,
        irreversible: true,
        label,
      });
    }

    charges() {
      const computeOps = this.reversibleOps + this.uncomputeOps;
      const reversible = computeOps * this.tariffs.reversibleOpUSD;
      const retention = this.historyBitSeconds * this.tariffs.historyBitSecondUSD;
      const discard = this.discardedBits * this.tariffs.discardBitUSD;
      return Object.freeze({
        reversibleComputeUSD: reversible,
        historyRetentionUSD: retention,
        discardHistoryUSD: discard,
        supplementalUSD: reversible + retention + discard,
      });
    }

    summary() {
      const charges = this.charges();
      return Object.freeze({
        schema: "holotrade.reversible-history-accounting.v1",
        planDigest: this.planDigest,
        profileDigest: this.profileDigest,
        resources: Object.freeze({
          reversibleOps: this.reversibleOps,
          uncomputeOps: this.uncomputeOps,
          historyBitSeconds: this.historyBitSeconds,
          discardedBits: this.discardedBits,
          liveHistoryBits: this.liveHistoryBits,
          peakHistoryBits: this.peakHistoryBits,
        }),
        thermodynamics: Object.freeze({
          landauerFloorJoules: this.landauerFloorJoules,
          measuredErasureJoules: this.hasMeasuredErasureEnergy ? this.measuredErasureJoules : null,
          measuredToLandauerRatio:
            this.hasMeasuredErasureEnergy && this.landauerFloorJoules > 0
              ? this.measuredErasureJoules / this.landauerFloorJoules
              : null,
          floorIsMeasuredEnergy: false,
        }),
        tariffs: this.tariffs,
        charges,
        events: Object.freeze([...this.events]),
      });
    }
  }

  function extendReceipt(baseReceipt, ledger) {
    if (!baseReceipt || typeof baseReceipt !== "object") throw new TypeError("base receipt required");
    if (!(ledger instanceof HistoryLedger)) throw new TypeError("HistoryLedger required");
    const history = ledger.summary();
    const baseCost = finiteNonnegative(baseReceipt.cost ?? 0, "baseReceipt.cost");
    const deviceJoules = finiteNonnegative(baseReceipt.joules ?? 0, "baseReceipt.joules");
    return Object.freeze({
      ...baseReceipt,
      baseExecutionCost: baseCost,
      cost: baseCost,
      totalCostWithHistoryPolicy: baseCost + history.charges.supplementalUSD,
      reversibleHistory: history,
      // Preserve the simulator's device-energy meter exactly. The theoretical
      // Landauer floor remains a separate named comparison quantity.
      joules: deviceJoules,
      modeledDeviceJoules: deviceJoules,
      landauerFloorJoules: history.thermodynamics.landauerFloorJoules,
    });
  }

  function settleWithHistory(engine, vm, plan, node, ledger, outcome) {
    if (!engine || typeof engine.settle !== "function") throw new TypeError("ExecutionEngine-like settle() required");
    const baseReceipt = outcome === undefined
      ? engine.settle(vm, plan, node)
      : engine.settle(vm, plan, node, outcome);
    const receipt = extendReceipt(baseReceipt, ledger);
    if (plan && typeof plan === "object") plan.receipt = receipt;
    return receipt;
  }

  function dominates(a, b) {
    const keys = ["latencySeconds", "peakHistoryBits", "irreversibleEraseBits"];
    const av = keys.map((k) => finiteNonnegative(a[k], k));
    const bv = keys.map((k) => finiteNonnegative(b[k], k));
    const noWorse = av.every((x, i) => x <= bv[i]);
    const strictlyBetter = av.some((x, i) => x < bv[i]);
    return noWorse && strictlyBetter;
  }

  function paretoFrontier(candidates) {
    if (!Array.isArray(candidates)) throw new TypeError("candidate array required");
    const rows = candidates.map((row, index) => ({ ...row, _index: index }));
    const frontier = rows.filter((candidate, i) =>
      !rows.some((other, j) => i !== j && dominates(other, candidate))
    );
    return frontier
      .sort((a, b) => a.latencySeconds - b.latencySeconds || a.peakHistoryBits - b.peakHistoryBits || a.irreversibleEraseBits - b.irreversibleEraseBits || a._index - b._index)
      .map(({ _index, ...row }) => Object.freeze(row));
  }

  const api = {
    K_B,
    LN2,
    RESOURCE,
    HistoryLedger,
    landauerFloorJoules,
    extendReceipt,
    settleWithHistory,
    dominates,
    paretoFrontier,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.HolotradeReversibleSettlement = api;
})(typeof window !== "undefined" ? window : globalThis);
