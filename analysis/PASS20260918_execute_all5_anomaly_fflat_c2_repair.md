# 2026-09-18 — execute-all-five: anomaly repair, F-flat obstruction, determinant optimum, rail intertwiner, and C2 no-go

This packet supersedes the earlier all-sector quarantine note where the first
engine reported \(A_{SU(3)^3}=-2\).

## 1. Published Z6-II benchmark repairs the non-Abelian anomaly sentinel

Rechecking the projection conventions against Chemtob--Hosteins Appendix B
finds two decisive corrections:

1. in \(T_2/T_4\), the physical gamma multiplicities are
   \[
   D_{\gamma=+1}=1,\qquad D_{\gamma=-1}=2;
   \]
2. for the \(T_3\) bosonic/chiral-multiplet projection, Table VII uses the
   vector right movers
   \[
   r_L=(0,-1,2,0),\qquad r_R=(-1,-1,1,0).
   \]

With those conventions the exact visible-sector anomaly ledger becomes

\[
\begin{array}{c|rrrrr}
&SU(3)^3&SU(3)^2Y&SU(2)^2Y&Y^3&{\rm grav}\!-\!Y\\\hline
U&1&-1/6&1/4&5/36&0\\
T_1&6&1/2&0&-1/6&2\\
T_2/T_4&1&-1/6&1/4&5/36&0\\
T_3&-8&4/3&-2&-10/9&0\\ \hline
{\rm total}&\boxed{0}&3/2&-3/2&-1&2
\end{array}
\]

Thus the old hard non-Abelian sentinel is gone:
\[
\boxed{A_{SU(3)^3}=0}.
\]
The model is nevertheless still quarantined because the hypercharge-related
sentinels are nonzero.  A non-anomalous \(U(1)_Y\) is an explicit requirement
in successful Z6-II mini-landscape models, so this is not a cosmetic failure.

Artifacts:
- \`analysis/w33_z6ii_full_spectrum_engine_v1.py\`
- \`data/w33_z6ii_full_spectrum_engine_v1.json\`

## 2. First F-flatness obstruction

The exact D-flat pair from the preceding pass is
\[
T_2(-s),\qquad T_4(s),
\qquad
s={1\over6}(1,-1,-3,3,3,3,3,3).
\]

The obvious dangerous cubic
\[
T_2(-s)\,T_4(s)\,U_3
\]
passes full gauge momentum, point-group and conventional no-oscillator
H-momentum tests.  However the independent chiral \(T_2(-s)\) state lies in
the \(\gamma=-1\) physical branch, while the \(T_4(s)\) singlet used by the
mass channel has \(\gamma=+1\); an untwisted field has eigenvalue \(+1\).
The localization product is therefore
\[
(-1)(+1)(+1)=-1,
\]
so this naive cubic is forbidden in the current physical gamma bookkeeping.

This is useful protection, not an all-order F-flat theorem.  Higher operators
may contain additional twisted singlets that compensate the gamma/discrete
charges.  A complete singlet charge ledger and superpotential search remain
necessary.

Artifacts:
- \`analysis/w33_z6ii_dflat_fflat_first_obstruction.py\`
- \`data/w33_z6ii_dflat_fflat_first_obstruction.json\`

## 3. Cross-repo order-two conclusion

The W33 outer involution and the Z6-II order-two ingredient are **not the same
extension**.  In the cyclic point group
\[
C_6=\langle\theta\rangle\cong C_3\times C_2,
\]
the order-two element \(\theta^3\) commutes with the order-three generator
\(\theta^2\):
\[
\theta^3\theta^2\theta^{-3}=\theta^2.
\]
The W33 outer involution instead obeys
\[
s z s^{-1}=z^{-1},
\]
so \(\langle z,s\rangle\cong C_3{:}C_2=S_3\).

The conjugation homomorphisms \(C_2\to{\rm Aut}(C_3)\) are therefore
inequivalent: trivial for the current Z6-II point group and nontrivial
inversion for W33.  Any genuine heterotic counterpart must be sought in a
non-Abelian \(S_3\)/dihedral-type extension rather than identified with the
present cyclic Z6-II order-two factor.

Companion W33 certificate:
\`data/w33_z6ii_c2_extension_no_go.json\`.

## Evidence boundary

The \(SU(3)^3\) repair is a concrete projection-convention correction and the
new total is exactly zero.  The nonzero hypercharge-related anomaly entries
keep the spectrum quarantined.  No three-family/MSSM or all-order flatness
claim is made.
