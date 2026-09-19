# 2026-09-19 — qutrit Hamming frame interpretation of the flagship CZ packet ABI

The current W33 packet runtime and the heterotic flagship now share a sharper exact dictionary.

The nine Hesse bins are naturally the two-qutrit computational basis
\[
(x,y)\in\mathbb F_3^2.
\]
The 72-slot packet frame group is
\[
\mathbb F_3^2\rtimes D_8
\cong S_3\wr C_2
=\mathrm{Aut}\,H(2,3),
\]
the full local classical relabelling group of that \(3\times3\) basis grid.

The flagship order-three Wilson line is independently certified to lie in the
two-qutrit \(CZ_3\) conjugacy class,
\[
CZ_3|x,y\rangle=\omega^{xy}|x,y\rangle.
\]
Its zero-phase eigenspace is the five-state cross \(xy=0\), which carries the
flagship \(SU(5)\) factor. Inside the 72-element frame group, the stabiliser of
this cross is exactly the linear \(D_8\); its nine cosets are the nine
translated crosses
\[
(x-a)(y-b)=0.
\]
Thus the packet radix \(72=9\times8\) is exactly “choose one of nine translated
CZ frames, then choose one of eight internal dihedral frame symmetries.”

The punctured-Hesse compiler also has two infinity sidebands. Under the same
\(D_8\), those two points swap exactly when the qutrit phase is inverted
\(CZ_3\leftrightarrow CZ_3^{-1}\). Therefore the existing \(11=9+2\) runtime
alphabet can be read equivariantly as nine CZ-frame centers plus the two
nonzero qutrit phase sectors.

This is a finite control/frame theorem. It does not alter the new
phenomenological obstruction: through total order five the flagship \(\mu\)
couplings and \(d/\bar d\) exotic masses use the same nineteen singlets, so no
on/off VEV pattern separates them. The packet theorem supplies a symmetry
language for future coefficient-level or order-6–8 searches; it is not by
itself a solution to the \(\mu\) problem.

Primary W33 certificate:
data/w33_qutrit_hamming_cz_frame_bundle.json.
