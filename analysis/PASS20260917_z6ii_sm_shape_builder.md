# Z6-II even-order breakthrough: an honest modular-compatible SU(5) to SM gauge embedding

This packet replaces the previous requirements-only even-order frontier with an actual
order-six heterotic gauge embedding. It deliberately does **not** reuse the old
\`T^6/Z3\` spectrum engine.

## Witness

Use the standard Z6-II compact twist

\[
v_6=(1/6,1/3,-1/2),
\]

and, in the first E8,

\[
V_6=(1/6,1/3,-1/2,0,0,0,0,0),
\]

\[
W_2=(-1,1/2,0,-1,-1,-1/2,-1/2,-1/2),
\]

\[
W_3=(-2/3,-2/3,2/3,0,2/3,-1/3,-1/3,0).
\]

The second E8 is untouched in this witness. Exact E8-lattice tests give orders
6, 2 and 3 respectively.

The Abelian modular-invariance residues are

\[
6(V_6^2-v_6^2)=0,\quad
2V_6\!\cdot W_2=0,\quad
3V_6\!\cdot W_3=-2,
\]

\[
2W_2^2=8,\quad
3W_3^2=6,\quad
W_2\!\cdot W_3=0,
\]

so every required residue is an even integer.

## Exact root-system chain

Direct enumeration of all 240 E8 roots gives

\[
E_6
 \xrightarrow{W_2} A_5+A_1,\qquad
E_6 \xrightarrow{W_3} A_4+A_1,
\]

and with both Wilson lines

\[
\boxed{A_2+A_1}.
\]

The local subtwist checks are

\[
2V_6:E_7,\quad 2V_6+W_3:A_5+A_2,
\]

\[
3V_6:E_7+A_1,\quad 3V_6+W_2:D_6+A_1+A_1.
\]

The final A2+A1 roots lie entirely inside the A4 parent from \(V_6+W_3\); the
spectator A1 is broken. Thus this is literally an SU(5) to SU(3)xSU(2)
breaking inside the E8 root system.

## Hypercharge

The unique A4-Cartan direction orthogonal to the surviving A2+A1 roots can be
normalized as

\[
Y={1\over 12}(-1,-1,-1,5,-7,3,3,-5).
\]

It satisfies

\[
Y^2={5\over 6},\qquad
\boxed{k_Y=2Y^2={5\over3}}.
\]

On every SU(5) root the W2 character is exactly the character of \((3/5)Y\).
Consequently the surviving-root phase is 0 and the broken-root phase is 1/2:
this is precisely the even-order pairing mechanism isolated by the preceding
GUT no-go work.

## Sector kinematics

For k=1,...,5 the Z6-II vacuum-energy shifts are

\[
11/36,\ 2/9,\ 1/4,\ 2/9,\ 11/36.
\]

The k=2,3,4 subtwists leave one complex plane invariant and therefore require
fixed-torus treatment; k=1,5 are fixed-point sectors. This is exactly why the
old Z3 fixed-point routine cannot be reused.

## Boundary

This closes the **gauge embedding**, not the heterotic MSSM. The next engine
must enumerate shifted E8xE8 momenta, oscillators, fixed-point/fixed-torus
degeneracies and centralizer projections sector by sector, then test net
chirality, hypercharge anomalies, vectorlike exotics, flatness and Yukawas.

Executable source:
\`analysis/w33_z6ii_sm_shape_builder.py\`

Frozen certificate:
\`data/w33_z6ii_sm_shape_builder.json\`
