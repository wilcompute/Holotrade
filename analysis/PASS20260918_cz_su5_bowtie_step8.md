# 2026-09-18 — CZ/W33/SU5 weld and flagship step-8 reduction

## 1. The flagship Wilson line is the entangling qutrit branch

The W33-class Z6-I flagship's order-three Wilson line on the local
\(A_8=\mathfrak{su}_9\) factor has exact root grading
\[
72=24_0+24_1+24_2
\]
with neutral subsystem
\[
A_4+A_1+A_1.
\]
Therefore its defining-representation spectrum is \(5+2+2\), and it is
projectively \(SU(9)\)-conjugate to the qutrit controlled phase
\[
CZ_3|x,y\rangle=\omega^{xy}|x,y\rangle.
\]

The local single-qutrit phase/transvection branch would instead have spectrum
\(6+3\), adjoint grading \(44+18+18\), and W33 profile \(1^{13}3^9\).
The flagship has
\[
32+24+24,\qquad 1^4 3^{12},
\]
so it is the rank-two entangling branch.

## 2. All-q controlled-Z theorem

For prime \(q\),
\[
CZ_q|x,y\rangle=\zeta^{xy}|x,y\rangle
\]
has fundamental phase multiplicities
\[
m_0=2q-1,\qquad m_a=q-1\quad(a\neq0).
\]
The induced \(\mathbb Z_q\)-grading of \(\mathfrak{sl}_{q^2}\) is
\[
\dim\mathfrak g_0=(q+1)(q^2-1),\qquad
\dim\mathfrak g_a=q(q^2-1)\quad(a\neq0).
\]
The charged dimension is exactly
\[
q(q^2-1)=|SL(2,q)|.
\]

On \(W(3,q)\), the projective Pauli action has cycle profile
\[
1^{\,q+1}\,q^{\,q(q+1)}.
\]
The fixed set is one totally isotropic line \(PG(1,q)\), and the number of
nontrivial projective cycles is
\[
q(q+1)=k,
\]
the GQ\((q,q)\) collinearity valency.

On all nonzero Pauli vectors the cycle profile is
\[
1^{\,q^2-1}\,q^{\,q(q^2-1)},
\]
so the number of nontrivial vector cycles equals every charged adjoint-grade
dimension and \(|SL(2,q)|\).

At \(q=3\):
\[
9=5+2+2,\qquad
\mathfrak{sl}_9=32+24+24,\qquad
W(3,3):1^4 3^{12},\qquad
80=8+24\cdot3.
\]

## 3. Why the flagship contains canonical SU(5) hypercharge

For \(CZ_3\), the zero-phase states are exactly
\[
(0,0),(0,1),(0,2),(1,0),(2,0),
\]
the zero locus \(xy=0\subset\mathbb F_3^2\). Hence the connected centralizer is
\[
S(U(5)\times U(2)\times U(2)).
\]
The independently measured flagship neutral \(A_4\) is therefore the \(SU(5)\)
acting on this five-dimensional zero-phase block, after the projective
\(SU(9)\) conjugation.

Inside that five-space,
\[
Y=\operatorname{diag}\left(-\frac13,-\frac13,-\frac13,\frac12,\frac12\right)
\]
satisfies
\[
\operatorname{tr}Y=0,\qquad
\operatorname{tr}Y^2=\frac56,\qquad
k_Y=2\operatorname{tr}Y^2=\frac53.
\]
Thus the entangling qutrit phase class and the flagship's canonical
GUT-normalised hypercharge live in the same exact \(SU(9)\) centralizer
structure.

This is a conjugacy-class theorem; the stored heterotic root basis has not been
canonically identified with the displayed qutrit computational basis.

## 4. Step-eight exotic decoupling reduces to a 6x6 block

The committed flagship \(v/\bar v\) mass support has structural rank \(13/18\).
Its defect is concentrated in two opposite six-leaf stars:
\[
S=\{0,2,4,6,8,10\}\longrightarrow c_{10},
\]
and, in the matched complement,
\[
r_{14}\longrightarrow R=\{1,3,5,7,9,13\}.
\]
Deleting the two hubs and the twelve leaves leaves an \(11\times11\) core with
a perfect matching.

Therefore, if higher-order corrections are sought only where they are needed,
the unresolved problem is the \(6\times6\) cross-block \(S\times R\), only
\(36\) entries rather than all \(324\). Full structural rank is equivalent to
that cross-block acquiring matching number at least five. The minimum repair is
five higher-order edges.

All \(4320\) size-five bijective repair patterns were checked and close the
full matrix.

## 5. Order-five bookkeeping correction

The parent mass-support source says the coupling engine was searched through
\[
ABn^k,\qquad k\le3,
\]
and records an order list of 2,3,4,5. Orbifolder Appendix B.2.5 defines
max-order as the order in singlet insertions. Therefore \(k\le3\) means total
superpotential field order \(\le5\).

No committed support entry first appears at order five. Hence, **if the parent
comment accurately records the executed run**, order five is already exhausted
and the untested total orders are \(6,7,8\), not \(5\)–\(8\).

A raw command/config/coupling dump is still required for provenance-complete
reproduction.

## Boundaries

- No claim identifies the five flagship cubic top couplings with the five
  \(CZ_3\) zero-phase basis states.
- No claim identifies the five low-order Hall-defect modes with those states.
- Structural rank assumes generic singlet VEVs; D/F-flat realization remains
  separate.
- The \(w\)-doublet multiplicity is not stored in the current flagship artifact,
  so its antisymmetric-mass question remains unresolved.

Artifacts:
- W33: data/w33_allq_cz_orbit_adjoint_weld.json
- W33: data/w33_cz_zero_phase_su5_hypercharge.json
- Holotrade: data/w33_flagship_vbv_hall_obstruction.json
- Holotrade: data/w33_flagship_vbv_bowtie_repair.json
- Holotrade: data/w33_flagship_mass_order_provenance_audit.json
