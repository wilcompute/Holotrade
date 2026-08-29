# The tau_2=111 case as a PG(3,4)-labelled partial-duality CSP

The earlier near-duality packet proved that a hypothetical 111-leaf blocker has
at least 36 clean row shadows and 36 clean column shadows, and that the number
of doubled clean-by-clean tiles satisfies

\[
D_{cc}\ge112.
\]

The new plane-ovoid identification of the W33/GQ(4,2) carrier gives a second,
more structural reduction.

## 1. Closed formula for all 360 minimum blockers

Let `O_c` be the plane ovoid of the 45-point Hermitian carrier associated with
W33 point `c`, and let

\[
C_m=\{x:m\in O_x\}.
\]

Every `C_m` has size eight and induces `K4,4` in W33.  For each incidence
`m in O_c`, define

\[
\boxed{B(c,m)=\bigl(Adj(c)\triangle C_m\bigr)\setminus\{c\}.}
\]

Exact comparison with the complete 360-blocker corpus gives:

- `|B(c,m)|=11` for every one of the `40*9=360` incidences;
- these are exactly the 360 minimum blockers, without duplication;
- the eight shell-1/removable points are `Adj(c) \\ C_m`;
- the remaining three blocker points are `C_m \\ (Adj(c) union {c})`.

Thus a minimum blocker is canonically the Hermitian label `(c,m)`, not an
opaque eleven-set.

## 2. Consequence at 111 leaves

For a row line `L`, let `B_L` be its row shadow and let `x_L` be the number of
leaves above that row line.  Define

- shadow excess `e_L=|B_L|-11`;
- fibre-overlap slack `f_L=x_L-|B_L|`.

Since every leaf belongs to four first-coordinate lines,

\[
\sum_L(e_L+f_L)=4\cdot111-40\cdot11=4.
\]

Hence at least 36 row lines satisfy `e_L=f_L=0`; call them clean.  The same is
true on the column axis.

Every clean row shadow is therefore exactly

\[
B_L=B(c_L,m_L),\qquad m_L\in O_{c_L},
\]

and every clean column shadow has an analogous label `(d_M,n_M)`.

On a clean-by-clean tile `(L,M)`, minimum-blocker geometry forces

\[
|B(c_L,m_L)\cap M|=1+[c_L\in M],
\]

and the column description forces the same occupancy, giving the already
proved center reciprocity

\[
c_L\in M\iff d_M\in L.
\]

The labels now add pointwise information that the center-only relaxation did
not contain: the one or two second-coordinate fibres in
`B(c_L,m_L) cap M` must be matched to the one or two first-coordinate fibres
in `B(d_M,n_M) cap L` by the actual leaves in that tile.

Thus the 111 problem is a finite partial-duality **matching** CSP on explicit
Hermitian labels, rather than a 1,600-leaf black-box set-cover instance.

## 3. Exact global budget retained

If `r,c >=36` are the numbers of clean row and column lines and `D_cc` is the
number of doubled clean-by-clean tiles, then

\[
16|X|=1776\ge1600+4r+4c-D_{cc},
\]

so

\[
\boxed{D_{cc}\ge4r+4c-176\ge112.}
\]

Any candidate label assignment must therefore realize a dense partial duality
and simultaneously admit the tile-by-tile fibre matchings dictated by the
`B(c,m)` formula.

## Boundary

This is an exact reduction, not an infeasibility proof.  The certified tensor
interval remains

\[
\boxed{111\le\tau_2\le115}.
\]

The next solver should operate on `(c,m)` labels plus the four units of slack,
not on 1,600 unconstrained leaf bits.