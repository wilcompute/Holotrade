# 2026-09-17 — execute-all-five continuation: T2/T4 no-go, anomaly fingerprint, and local-vectorlike mass channel

This packet continues the explicit modular-compatible Z6-II witness.

## 1. T2/T4 are not the missing third-family anti-five

Using the standard Z6-II fixed-torus GSO projection for \(g=2,4\), with
\(\gamma=\pm1\) and geometric multiplicities \(D=(1,2)\), the exact first-E8
shifted shells were rebuilt for every \(n_3=0,1,2\).

For \(T_2\), after the order-two Wilson-line condition:

- \(N_L=0\): shell sizes \(28,16,16\);
- \(N_L=1/3\): shell sizes \(1,5,5\);
- \(N_L=2/3\): empty.

The missing third-family target is
\[
\bar5=d^c+L=(\bar3,1)_{1/3}+(1,2)_{-1/2}.
\]

At \(N_L=1/3\) no \(d^c\) orbit occurs at all.  At \(N_L=0\), the only
relevant \(d^c\) candidate, at \(n_3=2\), appears with gamma-weighted count
\(3\) in each four-dimensional chirality.  The \(T_4\) sector is the
CPT-related fixed-torus partner.  Therefore the \(T_2/T_4\) branch does not
supply the required net chiral anti-five.

Artifact:
- \`analysis/w33_z6ii_t2_t4_antifive_nogo.py\`
- \`data/w33_z6ii_t2_t4_antifive_nogo.json\`

## 2. The anomaly deficit is exactly one anti-five

The certified chiral core is now:

1. two complete localized SM families from the two \(T_1\) local-\(E_6\)
   \(27\)s;
2. one split untwisted \(SU(5)\) ten
   \[
   Q+u^c+e^c.
   \]

The first two families are anomaly free.  Vectorlike pairs do not contribute
to perturbative net anomalies.  In left-chiral conventions, the remaining
partial ten has anomaly vector
\[
(A_{SU(3)^3},A_{SU(3)^2Y},A_{SU(2)^2Y},A_{Y^3},A_{\rm grav-Y})
=
\left(1,-{1\over6},{1\over4},{5\over36},0\right).
\]

Exactly one
\[
d^c+L
\]
has the negative vector
\[
\left(-1,{1\over6},-{1\over4},-{5\over36},0\right).
\]

The mod-two \(SU(2)\) Witten count says the same thing: the split ten leaves an
odd number of weak doublets once color multiplicity is included, and one
lepton doublet restores even parity.  This gives an independent fingerprint
for the eventual twisted-sector projection.

Artifacts:
- \`analysis/w33_z6ii_third_family_anomaly_fingerprint.py\`
- \`data/w33_z6ii_third_family_anomaly_fingerprint.json\`

## 3. Both local vectorlike 5+5bar packages have one explicit cubic mass channel

Each localized \(E_6\) \(27\) contains one vectorlike \(SO(10)\) ten, hence one
\(SU(5)\) \(5+\bar5\).  An exact search over the physical \(T_4\) \(N_L=0\)
singlet shell finds

\[
s={1\over6}(1,-1,-3,3,3,3,3,3).
\]

It has \(s^2=14/9\), is an SM singlet, satisfies the order-two Wilson
projection, and survives the left-chiral \(\gamma=+1\) \(T_4\) GSO condition.

More strongly, if \(q\) runs over every weight of the vectorlike \(5\), one
particular \(\bar5\) orbit in the same \(27\) satisfies
\[
\boxed{q_{\bar5}=-s-q_5}
\]
for every one of the three color-triplet weights and both weak-doublet
weights.  Thus the cubic conserves the full rank-eight first-\(E_8\) Cartan,
not merely \(SU(3)\times SU(2)\times U(1)_Y\).

The ordinary orbifold rules close too:

- point group: \(1+1+4=0\pmod 6\);
- no-oscillator H-momentum:
  \[
  2{(-1,-2,-3)\over6}+{(-2,-1,0)\over3}=(-1,-1,-1);
  \]
- \(n_3\): \(0+0+0=0\pmod3\);
- the same fixed point can be used twice, so \(n'_2+n'_2=0\pmod2\);
- gamma product: \(1\cdot1\cdot1=1\).

Because the \(T_4\) state lives on the fixed torus, the same channel is
available to both equivalent local-\(E_6\) copies.

This is not yet a proof of decoupling.  The modern worldsheet Rule 4/5/6
constraints, the actual CFT coefficient and a supersymmetric vacuum containing
the required \(T_4\) singlet VEV remain open.

Artifacts:
- \`analysis/w33_z6ii_local_vectorlike_cubic_mass_channel.py\`
- \`data/w33_z6ii_local_vectorlike_cubic_mass_channel.json\`

## Current sharp frontier

The model has:
- two complete localized families;
- a split untwisted third-family ten;
- canonical \(k_Y=5/3\);
- an exact anomaly fingerprint demanding precisely one net \(d^c+L\);
- a standard-selection-rule cubic mass channel for both localized vectorlike
  \(5+\bar5\) packages.

The shortest remaining spectrum problem is no longer “build the whole
Z6-II model.”  It is: find or rule out one net chiral anti-five in the
remaining genuinely chiral \(T_1/T_5\) oscillator content while respecting
the anomaly fingerprint.
