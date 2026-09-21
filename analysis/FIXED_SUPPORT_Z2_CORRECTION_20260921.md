# Correction: fixed-support 0/24 was full-U(1), not matter parity

The legacy file analysis/w33_dflat_support_parity_exact.py says it asks whether an exact B-L shift makes an LP support matter-even. The source actually solves

3((x0+Nt).Q_s) = 0

for every support singlet.

Matter parity requires only

3((x0+Nt).Q_s) in 2 Z.

A singlet with 3(B-L)=2 is the minimal counterexample to the equivalence: it is matter-even but not neutral under the full continuous U(1).

Therefore the frozen 0 of 24 result is retained only as an exact continuous-U(1) neutral-support result. It is withdrawn as exact evidence against matter-parity-preserving D-flatness.

The separate sampled scan w33_bminusl_freedom_search.py did use the correct test, integral and even, and its zero hits over 60 sampled choices per model still stand as evidence. Because the raw sp1/*.sp, sp2/*.sp, and unbroken2.py inputs are not committed, the correct class-wide congruence problem cannot currently be rerun or exhausted.

The replacement theorem contract is an affine lattice problem plus exact cone feasibility: enumerate every realizable parity/integrality class of 3(x0+Nt).Q_s, restrict to its even singlets, and give either an exact D-flat primal ray or a Farkas dual certificate.
