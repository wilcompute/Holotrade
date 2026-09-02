# Reversible compute, retained history, and erasure settlement

Holotrade's existing execution layer meters delivered node-seconds, modeled device energy, and market cost. `js/reversible-compute-settlement.js` adds a separate accounting plane for workloads whose runtime exposes reversible-history semantics.

The four resource classes are deliberately distinct:

| Resource | Meaning | Changes live history? | Landauer floor attributed? |
| --- | --- | ---: | ---: |
| `REVERSIBLE_COMPUTE` | logical reversible work that creates certified undo history | may increase | no |
| `HISTORY_RETAIN` | keep an existing history state live for a duration | no | no |
| `UNCOMPUTE` | consume history to restore work state reversibly | decreases | no |
| `DISCARD_HISTORY` | deliberately erase live logical history | decreases | yes |

For an explicit discard of `b` logical bits at temperature `T`, the module reports the comparison floor

`E_L = b k_B T ln 2`.

That value is **not** silently added to the execution receipt's `joules` field. The existing `joules` field remains the simulator's modeled device-energy quantity. A measured erasure-energy value can be attached explicitly and compared with the floor, but the two retain different field names and evidence status.

Likewise, economics are policy rather than thermodynamics. Supplemental tariffs for reversible operations, retained bit-seconds, and discarded bits default to zero and must be supplied explicitly. `extendReceipt()` preserves base execution cost and reports `totalCostWithHistoryPolicy` separately.

`settleWithHistory()` composes this ledger with an existing `ExecutionEngine.settle()` call and replaces `plan.receipt` with the extended receipt. A three-objective `paretoFrontier()` routine exposes non-dominated strategies in `(latencySeconds, peakHistoryBits, irreversibleEraseBits)` rather than inventing a scalar conversion between time, memory, and erasure.

## Verification

```bash
node --test tests/reversible-compute-settlement.test.js
```

The focused GitHub Actions workflow is `.github/workflows/reversible-compute-settlement.yml`.

## Scope

This is a typed software settlement/accounting model. It does not measure a hardware erasure process, infer logical erased bits from ordinary byte counts, or claim that the runtime operates near the Landauer limit.
