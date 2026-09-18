# 2026-09-18 — execute-all-five continuation: external benchmark, singlet search, determinant compression, transducer, S3 target

## 1. Published Z6-II regression fixture

The Buchmueller--Hamaguchi--Lebedev--Ratz model of Nucl.Phys.B785 (2007)
provides an external regression target with explicit 16D V6, W2 and W3.

The repo now reproduces exactly:

- visible global roots: A2+A1, 8 roots;
- hidden global roots: A3+A1, 14 roots;
- non-Abelian group SU(3)xSU(2)x[SU(4)xSU(2)];
- the origin T1 visible shell norm 23/18 with exactly 16 weights;
- the hidden T1 shell norm 1/9 with exactly one weight.

The published Table 5.1 aggregate spectrum has also been frozen as a future
checksum: 3 Q, 3 u^c, 7 d^c, 4 d, 5 anti-doublets, 8 doublets, 8 neutral
doublets, 3 e^c, 69 neutral singlets, and the hidden-sector multiplicities.

This is a strong core benchmark, but it is not yet a row-by-row reproduction
of every state in Tables D.2-D.3. That remains a fail-closed regression target.

Artifacts:
- analysis/z6ii_buchmuller2007_benchmark_regression.py
- data/z6ii_buchmuller2007_benchmark_regression.json

## 2. D-flat pair superpotential search

For a=T2(-s), b=T4(+s), gauge invariance of a pair-only monomial forces
(a b)^n. Since both have R3=0, every pair-only monomial has total R3=0,
whereas a superpotential coupling requires R3=-1 mod2.

Therefore:
\[
\boxed{\text{no pair-only superpotential self-coupling exists at any order}.}
\]

Adding a gauge-neutral U3 modulus u with R=(0,0,-1), the R rules for u(ab)^n
require n=1 mod6. The cubic n=1 is forbidden by the G2 localization/gamma
rule because it has exactly one nontrivial T2 gamma eigenstate. The next
standard-rule candidate is
\[
\boxed{u\,[T_2(-s)T_4(s)]^7}
\]
at degree 15.

No nonzero degree-15 CFT coefficient is claimed, and other external singlets
may produce lower-order lifting terms once the complete charge ledger exists.

Artifacts:
- analysis/w33_z6ii_singlet_pair_superpotential_search.py
- data/w33_z6ii_singlet_pair_superpotential_search.json

## 3. Correct non-Abelian outer target

The cyclic Z6-II order-two factor remains a no-go for identification with the
W33 outer inversion because it commutes with its order-three subgroup.

The correct heterotic symmetry class exists in the literature: Konopka's
explicit S3 heterotic toroidal orbifold has
\[
S_3=\langle\tau,\sigma\mid\tau^2=\sigma^3=(\tau\sigma)^2=1\rangle,
\]
hence
\[
\tau\sigma\tau^{-1}=\sigma^{-1}.
\]

This is exactly the W33 extension law under
\[
\tau\mapsto s,\qquad \sigma\mapsto z.
\]

The abstract semidirect product bridge is therefore exact. The physical
representations are not yet identified: sigma is a geometric point-group
generator while z is the Heisenberg center phase.

Companion W33 artifact:
- data/w33_heterotic_s3_outer_target.json

## Boundary

The external benchmark is only core-complete, not full D.2/D.3 state-by-state.
The pair-only F-term no-go is all-order, but the complete singlet
superpotential is not. The S3 bridge is exact at the group-extension level,
not yet at the gauge-spectrum or VOA representation level.
