# 2026-09-19 — qutrit Hamming CZ-cross incidence lock

The W33 packet/runtime track now has a stronger exact theorem on the nine
translated CZ_3 zero-phase frames used by the 72-slot Hamming packet group.

For centers (a,b) in F_q^2, define the translated cross
C_(a,b) = {(x,y): x=a or y=b}
and its square incidence matrix B_q.  This is exactly B_q = I + A(H(2,q)).

The exact spectrum is (2q-1)^1, (q-1)^{2(q-1)}, (-1)^{(q-1)^2}, hence
|det B_q| = (2q-1)(q-1)^{2(q-1)}.

At q=3:
|det B_3| = 80 = 3^4-1 = dim sl9.
Among integer q>=2 this determinant equality is unique at q=3.  It is an
arithmetic lock between independently certified finite carriers, not an
equivariant identification.

Additional exact q=3 data:
SNF(B_3)=1^5 2^3 10.
The binary row code is [9,5,3] with weight enumerator
1 + 6 z^3 + 9 z^4 + 9 z^5 + 6 z^6 + z^9.

In native characteristic, B_q=-I+N with N^3=0, rank N=2q-2 and rank N^2=1,
so dim ker N=(q-1)^2+1.  This equals the CZ_q zero-support size 2q-1 only
at q=3 for q>1.

The exact decoder is
B_q^{-1}=((3-q)/(q-1))I + (1/(q-1))A - 2/((q-1)(2q-1))J.
At q=3, B_3^{-1}=(1/2)A-(1/5)J, so translated-frame sums invert from
rook-neighbor sums plus one global mean, with no explicit identity-channel
coefficient.

Primary W33 artifacts:
- analysis/w33_qutrit_hamming_cross_incidence.py
- data/w33_qutrit_hamming_cross_incidence.json
- tests/test_w33_qutrit_hamming_cross_incidence.py

This result is orthogonal to the current phenomenological obstruction.  It
does not resolve the flagship mu-term/exotic-vacuum tension.  At the current
Holotrade head that no-go remains an imported aggregate measurement through
total order five; the 64 and 144 raw singlet-support hyperedges are not
committed, so the reported 26,273-subset search is not independently replayable
from the repository yet.  The exact structural deduction from that premise is
the monomial-ideal containment theorem in
data/w33_mu_exotic_monomial_ideal_containment.json.
