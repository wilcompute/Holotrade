# Point potentials of the existing signed-pencil duals

This extends `SIGNED_PENCIL_SAMPLING.md` and its two exact representatives.
It does not rediscover their l1 optima or establish a new orbit census.
Run `python analysis/signed_pencil_dual_geometry.py` (SymPy required).

Let B map point coefficients to line excesses. The stored rational dual y
assigns each point p a potential h_p = sum of y_L over lines containing p.
Dual feasibility says |h_p| <= 1. For any feasible x,

    ||x||_1 - y.e = sum_p (|x_p| - h_p*x_p) >= 0.

Every summand must vanish at an optimum. Consequently every optimal preimage
vanishes at unsaturated points, is nonnegative on h=1, and nonpositive on h=-1.
This converts an objective-value certificate into a support/sign compiler.
The statement applies to every optimum, not only the stored primal witness.

| Existing representative | h=1 | h=-1 | Forced zeros | Active rank | Face dimension upper bound |
|---|---:|---:|---:|---:|---:|
| Mass 12, depth 1 | 18 | 6 | 16 | 22 | 2 |
| Mass 16, depth 2 | 28 | 12 | 0 | 25 | 15 |

The bounds are exact nullities of active incidence columns; sign inequalities
can shrink the feasible face further. No uniqueness or exact face dimension
is inferred. The mass-16 negative-saturated points induce a 5-regular graph on
12 points. This is a property of the stored dual in the existing incidence
labeling; another optimal dual need not have the same saturation pattern.
The certificate exports point lists and potentials for independent checking.

Since every column sums to four, sum x = k = mass/4. A nonnegative preimage
would have norm k, whereas the dual certifies norms 5 and 8 at k=3 and 4.
The separation margins are therefore 2 and 4, and every feasible preimage
has negative mass at least 1 and 2 respectively. Existing primal witnesses
attain these bounds. This supplies a geometric explanation of the existing
sampling overhead, not a claim of measured physical cost.

The companion W33 packet `W33_FIVE_COMPUTATION_FOLLOWUPS.md` connects this
support interpretation with guest arithmetic, coherent gate compilation and
fresh-seed memory policies. Physical reset-work collection remains unavailable.

Parallel intake reviewed through `460618d`: the new mass-20 birth/extension
search and octet local-minimum search add independent computational directions.
Their new files do not supersede these two stored primal/dual certificates.
The point-potential gap offers a lower-bound target for those local searches: a
local minimum with positive gap is not globally optimal. No new search outputs
from those workflows were assumed in this report.
