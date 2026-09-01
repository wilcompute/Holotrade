# Exact rational closure of the 216-by-540 bicolour circuit stack

Let `M+` and `M-` be the two `216 x 540` orbital colours in the maximal-overlap
relation between the 216 sentinel five-circuits and 540 six-circuits.  Each
colour has row/column degrees `(10,4)`.

## The proof gap

The companion W33 packet reported stacked rank 372 from elimination modulo
`1,000,003`.  That proves only

```text
rank_Q([M+;M-]) >= 372.
```

It does not by itself prove equality or the claimed 60-dimensional common row
space.  Later prose retained that premise while correcting a separate sector
assumption.

## GAP repair

The new witness independently reconstructs the 45 sentinel minima, all 216
five-circuits, all 540 six-circuits, and both 2,160-pair colour orbits.  GAP then
performs exact characteristic-zero row reduction:

```text
rank_Q(M+) = rank_Q(M-) = 216
rank_Q([M+;M-]) = 372
dim_Q(row(M+) intersection row(M-)) = 60.
```

It constructs the rational common space and intersects it with the exact seven
joint eigenspaces.  In separator order

```text
eigenvalue:       -58 -22 -18   8  14  62 170
sector dimension:  15  15  81  20  60  24   1
direct common:       0   0   0  20   0  24   1
```

The doubled 15-isotypic sum meets the common space in dimension 15.  Therefore

```text
common colour row space = 1 + 15 + 20 + 24,
```

and it has zero intersection with the symmetric 60-sector.  The 15 is a
diagonal copy across the two equivalent 15-dimensional sectors.

## Canonical circuit split

This computation now also reconstructs the established `216 x 45`
five-circuit incidence matrix `C` inside the same GAP process.  Its Gram acts
on the seven joint sectors by

```text
CC^T scalars:       0   0   0  12   0  30 120
im(C) intersection: 0   0   0  20   0  24   1.
```

Thus `im(C) = 1 + 20 + 24` exactly.  More strongly, transporting this carrier
through either colour gives the same 45-dimensional target subspace:

```text
im(im(C) M+) = im(im(C) M-) <= row(M+) intersection row(M-).
```

Both inclusions have dimension 45, so the common space has the concrete split

```text
common60 = common circuit image(1 + 20 + 24) direct-sum diagonal15.
```

The standalone circuit spectrum was already established in W33-Theory commit
`c6170fa8e`; the new result is the exact equality of its two colour transports
and its identification as the codimension-15 subcarrier of the bicolour common
space.

## Replay

```bash
gap -q analysis/e8_sentinel_bicolour_exact_stack_rank.g
node analysis/e8_sentinel_bicolour_exact_stack_rank.js --write
node --test tests/e8-sentinel-bicolour-exact-stack-rank.test.js
```

The result is an exact finite circuit-incidence/module theorem.  It does not
identify optical modes, physical qubits, hardware channels, host identities,
cryptographic authority, or dispatch bindings.
