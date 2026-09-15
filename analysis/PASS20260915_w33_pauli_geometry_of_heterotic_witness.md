# Pass 2026-09-15 — Pauli geometry of the frozen heterotic net-three witness

## Question

The E8 order-three sector is now explicitly graded by the two-qutrit phase space
`V = F_3^4`, with W(3,3) lines equal to Lagrangian 2-spaces / Pauli Cartans. Does
the already-certified three-family Wilson-line witness from
`data/w33_vacuum_wilson_line_families.json` put all three Wilson lines in one such
Cartan?

## Exact answer: no

The parent witness is frozen and re-verified there: it is anomaly-free, has gauge
semisimple part `A2 + A1^3`, and has a quark-doublet pair with untwisted per-plane
index 1 and net index 3.

Using the same Coxeter twist `g=c^10`, the same quotient `E8/(1-g)E8`, and the same
deterministic Pauli coordinates `(x1,z1,x2,z2)` as the W33 E8/Pauli certificate,
the **first-E8 components** of its three Wilson lines map to

```
v1 = (1,1,0,2)
v2 = (0,0,1,2)
v3 = (2,0,2,1).
```

Their symplectic Gram matrix is

```
0 2 0
1 0 0
0 0 0
```

and the three labels have rank 3 over F3. Thus `v1` and `v2` do not commute,
while `v3` commutes with each. A single W33 line would require a rank-at-most-2
totally isotropic span, so no one W33 line / Pauli Cartan contains all three.

Instead the witness forms a **two-Cartan hinge**: `span(v1,v3)` and `span(v2,v3)`
are two W33 lines sharing the projective point `[v3]`.

## Consequence

This is a useful null result. Membership of all Wilson lines in one W33
isotropic line/Pauli Cartan is **not necessary** for the already-certified net-three
quark-doublet chirality. Any genuine W33 selection effect on a Standard-Model
vacuum must therefore be subtler — for example a condition involving several
Cartans, a spread, or the hypercharge/exotic constraints themselves.

The result does **not** close hypercharge. The parent Wilson-line certificate does
not yet assign `U(1)_Y`, determine `k_Y`, or prove removal of vector-like exotics,
and this pass does not invent those missing data.

## Reproducibility

Run:

```bash
python analysis/w33_pauli_geometry_of_heterotic_witness.py
```

Certificate:

`data/w33_pauli_geometry_of_heterotic_witness.json`
