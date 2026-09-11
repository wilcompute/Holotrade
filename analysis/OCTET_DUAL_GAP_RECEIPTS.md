# Portable optimum receipts for the existing circuit escapes

The traps and escape circuit belong to the parallel work frozen in
`octet_circuit_decoder_trap_certificate.json` and
`octet_single_circuit_obstruction_certificate.json`. The hybrid decoder already
uses those escapes. This packet adds independent rational optimality checking.

For a signed point preimage x of line excess e, let B be the line/point incidence
matrix. A rational line vector y is dual-feasible when |B-transpose y| <= 1.
Then ||x||1 >= y.e. Since sum x = sum e/4 = k, the negative mass is at least
(y.e-k)/2. Equality certifies a global optimum, without a solver at runtime.

The receipt includes start, end, actual move, its digest, line image and rational
dual. The checker derives the bound and rejects wrong dimensions, noninteger
preimages, a changed move digest, a changed fiber, infeasible duals, non-descent
and a nonzero final gap. It does not trust an `OPTIMUM` label or scalar target.

For both already-known mass-28 traps, all 4,140 radius-two endpoints fail to
improve negativity 2, while the stored circuit reaches negativity 1. The new
duals prove a lower bound of 1; the exact l1 gap decreases from 2 to zero.

Reproduce:

```
python analysis/octet_dual_gap_receipts.py
python -S analysis/octet_dual_gap_receipts.py --check
```

The first command uses SciPy to find duals and verifies all 8,280 endpoints.
The second uses only the standard library and frozen rational witnesses;
three corruption controls must be rejected. The existing hybrid decoder and
attestation transaction are unchanged. Wiring these receipts into its current
JavaScript verifier is a separate integration, not claimed here.

Companion W33 `W33_SEPT11_EXECUTION_FRONTIERS.md` records durable guest
consumption, exact Clifford+T lowering and adaptive observer policies.
All are mathematical/software results; physical reset-work data remains absent.
