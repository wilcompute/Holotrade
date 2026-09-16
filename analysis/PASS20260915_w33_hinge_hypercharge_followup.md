# 2026-09-15 — W33 hinge orbit and canonical-hypercharge follow-up

Status: **PASS with a preserved model-building boundary**.

This pass follows two finite-geometric questions raised by the exact E8 -> two-qutrit Pauli bridge in W33-Theory.

## Two-Cartan hinges are not a selector

`data/w33_two_cartan_hinge_orbits.json` classifies all pairs of W33 Pauli Cartans meeting in one projective point.  There are 240 undecorated hinges.  If one additionally chooses one nonshared Pauli projective point on each Cartan there are 2160 decorated hinges.

Projective symplectic transvections generate `PSp(4,3)` of order 25920 on the 40 W33 points.  The 240 hinges form one orbit (stabilizer 108) and the 2160 decorated hinges form one orbit (stabilizer 12).  The frozen verified net-three Wilson-line witness lies in this unique decorated orbit.

Therefore the witness's previously observed two-Cartan geometry is real but not exceptional under bare W33 incidence.  Any W33-based selector for hypercharge or exotic lifting must use data beyond the projective hinge: orientation/phase, lattice norms, the second E8, or the massless spectrum.

## The three-family SU(5) witness has canonical k_Y = 5/3

The newer frozen GUT witness in `data/w33_vacuum_three_family_gut.json` contains a selected SU(5) factor with exact net indices

- `n10 = 3`,
- `n5bar = 3`.

`data/w33_gut_hypercharge_exotics.json` reconstructs its full massless weights and fixes the conventional SU(5) hypercharge Cartan generator, up to overall sign/Weyl conjugacy,

\[
Y=\operatorname{diag}(-1/3,-1/3,-1/3,1/2,1/2).
\]

In the lattice normalization used by the model,

\[
Y^2=\frac56,
\qquad
k_Y=2Y^2=\frac53.
\]

The selected SU(5) representation multiplicities are

- 3 tens and 0 anti-tens;
- 12 anti-fives and 9 fives;
- no other nontrivial SU(5) irreps;
- 270 SU(5) singlets.

Thus the witness contains exactly three chiral `10 + 5bar` families plus nine SU(5)-vectorlike `5 + 5bar` pairs.  The standard branching is

\[
10\to(3,2)_{1/6}+(\bar3,1)_{-2/3}+(1,1)_1,
\qquad
\bar5\to(\bar3,1)_{1/3}+(1,2)_{-1/2}.
\]

This is the canonical normalization one wants from an SU(5) embedding, but it is not yet an actual broken Standard Model vacuum: the level-1 witness still has unbroken SU(5).

## Exotic boundary

The nine additional `5+5bar` pairs are vectorlike only with respect to the selected SU(5) factor.  In the complete rank-16 weight data, none of the 405 weighted massless states has its exact opposite weight.  In particular, the extra fives and anti-fives carry spectator gauge/U(1) charges and are not certified to admit a bare gauge-invariant mass term.

They could still be lifted after further breaking or through allowed singlet-VEV/higher-order couplings, but that is a separate dynamical calculation.  This pass intentionally does not assume it.

## W33 consequence

The one-Wilson-line SU(5) and SO(10) witnesses each determine a single nonzero first-E8 Pauli projective point.  `PSp(4,3)` is transitive on all 40 points.  Combined with the single decorated-hinge orbit above, neither bare W33 point incidence nor bare hinge incidence distinguishes the successful GUT witnesses.  The next finite-geometric discriminator must be enriched by non-projective information.
