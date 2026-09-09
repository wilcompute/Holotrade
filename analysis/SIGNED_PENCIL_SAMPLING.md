# Signed pencil witnesses: negativity survives fractional relaxation

The depth classifications in 1075622 and 66062ec now have exported coordinate
witnesses and independent optimality certificates. This adds reproducible
objects and a computational resource interpretation; it is not a new census.

`analysis/signed_pencil_sampling_certificate.json` stores the exact 40-line
geometry, two excess vectors, signed point preimages, rational LP primal/dual
vectors and signed-sampling bounds. The selected profiles have mass/depth
(12,1) and (16,2). The second has histogram {0:26,1:12,2:2}, agreeing with the
previous depth-two class. Their minimum integer l1 weights are 5 and 8.

The discovery uses existing `the_mass12_census_is_complete_and_has_one_exception.py`
geometry. One negative pencil is covered by four positive neighbours; two
noncollinear negative pencils are covered using common neighbours and residual
line choices. An exact recursive cover search excludes smaller negativity:
every positive residual line must receive a pencil from one of its four points.
Branching over those points, subtracting each pencil, and exhausting the tree
is complete. Depth-one tests also range over all forty negative pencils.
This avoids another full mass-16 census and supplies concrete coordinates.

For a profile e of mass 4k, every preimage x satisfies sum(x)=k. Hence

    min ||x||_1 = k + 2 depth(e).

For the signed sampler, choose point p proportional to |x_p|, sample one of its
four incident lines uniformly, and multiply a bounded line observable by
sign(x_p)*||x||_1/k. Its mean is the observable's mean under e/(4k), and its
second moment is at most (||x||_1/k)^2. Exact fractional checks cover forty line
indicators and one alternating-sign observable for each profile: 82 checks.
The resulting bounds are 25/9 and 4. These are bounds for this sampler, not
optimal variances over all sampling algorithms.

The additional experiment asked whether fractional coefficients remove some
of this cost. **They do not for either representative.** SciPy finds candidate
real LP solutions, then all coordinates are reconstructed as rational numbers
and checked exactly. With B=N^T, the certificate verifies

    Bx=e; |B^T y| <= 1; ||x||_1 = y.e.

The dual inequality lower-bounds every real preimage's l1 norm. Equality with
the primal proves exact real optima 5 and 8, also certifying the integer optima.
There is no integrality gap here: the negativity is not an integer-rounding
artifact. This is a result about these pencil representations, not quantum
magic, blocker existence or tau_2. The general signed-sampling/l1 connection
is prior work, e.g. [Pashayan, Wallman and Bartlett](https://arxiv.org/abs/1503.07525).
The W33 architecture connection is developed in
[the eight-experiment report](https://github.com/wilcompute/W33-Theory/blob/master/analysis/W33_EIGHT_COMPUTATION_EXPERIMENTS.md).

Reproduce discovery with NumPy and SciPy installed:

    python analysis/signed_pencil_sampling_witness.py

Independently check the exported coordinates and rational duality without a
solver or any site packages:

    python -S analysis/signed_pencil_sampling_witness.py --check

Three mutation controls alter an integer preimage, fractional primal, and dual;
all are rejected. The checker also verifies the stored geometry against the
existing geometric construction. The source/certificate/report belong in
Holotrade; counter execution and observation experiments belong in W33.
