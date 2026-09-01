# The sentinel is the universal W33 shadow of the 120-state homology

Let `A` be the certified 120-state adjacency differential over `F_2`, and let

```text
H = ker(A) / im(A),             dim H = 40,
N = O_2(2^5:S6) = C2^5.
```

The full `H` is not the genuine 40-point W33 permutation module under either
identification class of `S6`.  The exact GAP/MeatAxe continuation determines
what survives after the normal translation core is removed.

## Exact reduction

Both the fixed space `H^N` and the coinvariant quotient `H_N` have dimension
15.  Reconstructing the 45 eight-supports in the same W33 coordinates gives
the sentinel `C_S=[40,15,8]_2`.  Under both inner and exceptional-outer `S6`
identifications, all of

```text
H^N, H_N, C_S(inner), C_S(outer)
```

have composition-factor dimensions `1^3 + 4^3`, but MeatAxe proves that the
four modules are pairwise non-isomorphic.  Equal dimension and equal factors therefore
do not authorize a relabeling.

The complete equivariant-map rank profiles locate the extension obstruction:

```text
H_N -> C_S(inner): {1,11}       C_S(inner) -> H_N: {4,5}
H_N -> C_S(outer): {1,6}        C_S(outer) -> H_N: {10}
H^N -> H_N:       {1,4,5,6,10} H_N -> H^N:         {1,6}
```

## Universal factorization theorem

For either genuine W33 point carrier `V`, every equivariant map `H -> V`
kills the 25-dimensional span of the `N`-differences, hence factors through
`H_N`.  GAP proves the additional object-level statement that every such image
lies inside the explicit sentinel subcode `C_S < V`.

The span of all forward images has dimension 11 for the inner `S6` class and
6 for the outer class.  Conversely, every equivariant map `V -> H` lands in
`H^N`, with the same respective universal image dimensions 11 and 6.

Thus the sentinel is not the logical homology itself.  It is the exact finite
module that receives every W33-compatible shadow of that homology.

## Replay and boundary

```bash
gap -q analysis/e8_unitary_homology_sentinel_bridge.g
node analysis/e8_unitary_homology_sentinel_bridge.js --write
node --test tests/e8-unitary-homology-sentinel-bridge.test.js
```

No preferred nonzero intertwiner is selected.  The theorem does not provide
physical qubits, decoding performance, integral E8 coordinates, host identity,
cryptographic authority, or dispatch binding.
