# Exact homology code and the W33 point-module obstruction

## Result

Reduce the certified symmetric 120-state adjacency matrix `A` modulo two.
The existing differential identity is `A^2=0`, with rank 40.  The new exact
packet determines the associated codes and logical quotient:

```text
im(A)  = [120,40,16]_2, doubly even and self-orthogonal
ker(A) = [120,80,8]_2 = im(A)^perp
ker(A)/im(A) has dimension 40
CSS(H_X=H_Z=im(A)) = [[120,40,8]]_2
```

There are exactly 435 weight-eight words in the kernel.  Since the image has
minimum weight 16, all 435 survive as nonzero minimum logical classes.  The
complete image and kernel weight enumerators are frozen in
`data/e8_unitary_homology_code_w33_obstruction.json`.

## Why the enumeration is exhaustive

GAP finds a 15-dimensional structured image subcode: fourteen even full-fibre
flips plus a global half-fibre word.  It extends this by a 25-dimensional
transversal.  The JavaScript freezer visits every one of the `2^25`
transversal words in Gray order.  For each, the structured-coset enumerator
factors exactly over the fifteen eight-point fibres.  Only 595 fibre-weight
profiles occur.  Their multiplicities recover all `2^40` image words; the
integer binary MacWilliams transform then recovers all `2^80` dual/kernel
words.  There is no random sampling or minimum-distance heuristic.

## The module obstruction

MeatAxe gives the following composition-factor dimensions over `F_2` for the
execution group `2^5:S6`:

```text
image   : 1^4 + 4^5 + 16
homology: 1^8 + 4^8
coimage : 1^4 + 4^5 + 16
```

Image and coimage are isomorphic; homology is not isomorphic to either.  The
normal `C2^5` acts on homology with move-rank distribution
`0:1, 12:6, 14:15, 16:10`, so it is not a quotient-only carrier.

GAP independently rebuilds the 40 points and 40 lines of `W(3,3)`, finds a
spread stabilizer `S6 < PSp(4,3)`, and pulls its genuine 40-point permutation
module through both identification classes of `S6` (ordinary and exceptional
outer).  Its composition-factor dimensions match homology, but the modules
are non-isomorphic in both cases.  The two-dimensional Hom spaces have
nonzero rank profiles `{1,6}` and `{1,11}`.  The sharp obstruction is that the
normal `C2^5` acts nontrivially on homology and trivially on every module
inflated from the `S6` quotient.

This closes a tempting but false identification: the 40 logical homology
coordinates are not secretly the 40 W33 points.  A useful bridge between them
must be a low-rank, non-invertible intertwiner, not a relabeling.

## Replay

```bash
gap -q analysis/e8_unitary_homology_code_w33_obstruction.g
node analysis/e8_unitary_homology_code_w33_obstruction.js --write
node --test tests/e8-unitary-homology-code-w33-obstruction.test.js
```

## Boundary

The packet certifies finite binary codes and representation modules.  It does
not provide physical qubits, a noise model, a decoder threshold, integral E8
coordinates, cryptographic identity, or dispatch authority.  Matching
composition factors are explicitly not promoted to module isomorphism.
