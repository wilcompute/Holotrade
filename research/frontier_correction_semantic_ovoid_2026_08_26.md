# Frontier correction: semantic authority and the ovoid implication

Date: 2026-08-26 (America/New_York)

This note records two fail-closed corrections found while reconciling the live parallel frontier. It supersedes stronger wording where that wording conflicts with the statements below.

## 1. Ovoids collapse the depth-2 bounds; the converse is not a generic theorem

For a generalized quadrangle of order `(s,t)`, let `tau_1` be its point blocking number and `tau_2` the blocking number of the point-product against all tiles `L x M`. The existing double count and product construction give

`(st+1) tau_1 <= tau_2 <= tau_1^2`.

Define the **blocking ovoid defect**

`delta_tau = tau_1 - (st+1)`.

The width between these two generic bounds is exactly

`tau_1 * delta_tau`.

A blocker of size `st+1` is an ovoid, so `delta_tau = 0` iff an ovoid exists. Therefore the rigorous implication is

`ovoid exists  =>  tau_2 = tau_1^2 = (st+1)^2`.

That is a sufficient condition for depth-2 multiplicativity. The converse does **not** follow from the bounds: `delta_tau > 0` opens a nonzero interval, but `tau_2` could in principle still equal its product upper endpoint.

For W(3,3), nonmultiplicativity is nevertheless proved for a separate, stronger reason: the explicit certified 115-leaf blocker gives

`tau_2 <= 115 < 121 = 11^2`.

The exact value remains open in `[110,115]`.

## 2. Two ovoid deficits, not one

The same missing 10-point ovoid appears in two different extremal problems:

- blocking side: `delta_tau = tau_1 - 10 = 11 - 10 = 1`;
- coclique side: `delta_alpha = 10 - alpha(W33) = 10 - 7 = 3`.

Both vanish if the corresponding extremum reaches an ovoid, but for W(3,3) they are numerically and mathematically distinct. The coclique census constrains tight tensor fibres; it does not equal the blocking defect that measures the elementary depth-2 bound gap.

This distinction is now machine-pinned in `data/tensor_multiplicativity_ovoid_defect.json` and `tests/semantic-authority.test.js`.

## 3. Semantic result authority

`output.result.digest` / `semanticResult.digest` are first-class semantic identities. They must agree with one another. If the backwards-compatibility alias `output.metadata.resultDigest` is present, it must agree with the first-class digest or verification fails closed.

A metadata-only digest is not silently promoted. Legacy v2 replay may compare it only through an explicit advisory compatibility path. Such a mismatch can produce a correction record for review, but it cannot automatically invalidate referenced evidence. Automatic invalidation is reserved for mismatches whose source and replay both carry authoritative first-class semantic commitments.

This preserves the separation:

`semantic result identity != execution provenance identity != legacy metadata hint`.

## Evidence boundary

- Exact: the two generalized-quadrangle bounds, their width identity, the one-way ovoid implication, W(3,3) values `tau_1=11`, `alpha=7`, and the verified 115-leaf blocker as already certified by repository artifacts/tests.
- Software policy: first-class-vs-legacy semantic authority rules in the replay market.
- Open: exact `tau_2(W(3,3))` inside `[110,115]` and any general converse characterizing when `tau_2=tau_1^2` without an ovoid.
- Not claimed: physical/quantum realization or empirical market/failure probabilities.
