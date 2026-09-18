# 2026-09-18 — execute-all-five continuation: full T1 oscillators, Rule456, and all-sector anomaly quarantine

This packet supersedes the earlier shorthand that the current Z6-II witness was
already reduced to "two local families + an untwisted ten + one missing anti-five."

## 1. Full T1/T5 oscillator execution

The complete singly twisted T1 projection has now been implemented directly
from Chemtob--Hosteins (B.3)-(B.5), including:

- all 12 fixed points;
- the six temporal twists h=0,...,5;
- every massless left-oscillator shell;
- the B.5 oscillator phase;
- the exact global SU(3)xSU(2)xU(1)_Y decomposition.

The two local-E6 fixed points remain exactly as before: each contains a complete
unoscillated E6 27.  This part of the previous result survives.

What changes is the rest of T1.  The other ten fixed points are not empty.
After all fixed-point and oscillator multiplicities, the T1 ledger contains

\[
\begin{array}{c|c}
\text{SM representation} & \text{multiplicity}\\ \hline
(3,2)_{1/6}&2\\
(\bar3,1)_{-2/3}&2\\
(\bar3,1)_{1/3}&6\\
(3,1)_{-1/3}&4\\
(3,1)_{1/6}&6\\
(1,2)_{-1/2}&6\\
(1,2)_{1/2}&4\\
(1,2)_0&6
\end{array}
\]
plus charged and neutral singlets.

Therefore "only one anti-five is missing" was not a complete-spectrum theorem.
T5 is the CPT partner of T1; it is typed as such rather than blindly double
counted as a second independent left-chiral ledger.

Artifacts:
- analysis/w33_z6ii_t1_full_oscillator_ledger.py
- data/w33_z6ii_t1_full_oscillator_ledger.json

## 2. Rule 4/5/6 do not kill the local exotic cubic

For the previously found T1*T1*T4 mass channel all three external states are
unoscillated.  Hence every Rule-4 and Rule-6 oscillator-difference congruence
has left side zero.  Rule 5 also passes: all required inequalities/equalities
among oscillator counts are satisfied identically when every count is zero.

The explicit T4 singlet
\[
s={1\over6}(1,-1,-3,3,3,3,3,3)
\]
also has a physical T2 state of exactly opposite shifted gauge momentum -s.
Thus equal VEV magnitudes give an exact D-flat pair for every first-E8 Cartan
generator.

This does not close F-flatness.  The complete singlet superpotential, including
possible T2*T4*U and higher operators, must be generated before the pair can be
called a supersymmetric flat direction.

Artifacts:
- analysis/w33_z6ii_t1t1t4_rule456_dflat.py
- data/w33_z6ii_t1t1t4_rule456_dflat.json

## 3. First all-sector engine: software closure, physics quarantine

A single engine now covers U, T1/T5, T2/T4 and T3, with all massless oscillator
energies and gamma multiplicities.  During this integration a bookkeeping
error in the older T2 certificate was corrected:
\[
D_{\gamma=+1}=2,\qquad D_{\gamma=-1}=1.
\]
The targeted T2/T4 d^c no-go is unchanged.

The engine carries an anomaly sentinel.  Under the current chirality/CPT
conventions its sector contributions are

\[
\begin{array}{c|r}
\text{sector index} & A_{SU(3)^3}\\ \hline
U&+1\\
T1&+6\\
T2/T4&-1\\
T3&-8
\end{array}
\]
so the combined value is
\[
\boxed{-2\ne0}.
\]

The ledger is therefore quarantined.  It is not admitted as the physical
heterotic spectrum and no MSSM/family-count conclusion is drawn from it.
The sentinel has localized the next debugging work to the T1/T3 chirality and
CPT/projection conventions rather than allowing an inconsistent spectrum to
propagate into phenomenology.

Artifact:
- analysis/w33_z6ii_full_spectrum_engine_v1.py
- data/w33_z6ii_full_spectrum_engine_v1.json

## Evidence boundary

The finite lattice shells and the implemented projection arithmetic are
reproducible.  The anomaly failure means at least one remaining convention or
sector-index mapping still needs correction.  This packet intentionally
withdraws the earlier global "one missing anti-five" reading while preserving
the exact partial-spectrum facts that generated it.
