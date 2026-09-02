# The two 216s are not the same finite-group carrier

Two independently constructed objects in the W33/HoloTrade corpus have size
216:

- the 216 five-circuits of the 45 minimum words of the binary sentinel code;
- the 432 hemisystems of `W(3,3)`, modulo complementation, giving 216
  projective hemisystem lines.

The earlier comparison correctly proved only the count and complementation
mechanism.  It explicitly did not claim a fibre-level correspondence.  The new
GAP witness resolves that boundary.

## Exact no-go

Both 216-sets are transitive under `PSp(4,3)`.  A point stabilizer has order
120 in each action, and both stabilizers have the element-order histogram of
`S5`.  Nevertheless GAP proves that the two subgroups are not conjugate in
`PSp(4,3)`.  Therefore the transitive `PSp(4,3)`-sets are nonisomorphic.

Adding the outer graph automorphism does not repair the mismatch.  In the full
order-51,840 automorphism group both stabilizers grow to order 240, have the
same element-order histogram, and remain nonconjugate.  The full permutation
characters differ.  Two particularly short witnesses are:

```text
class order  class size  fixed circuits  fixed hemisystem lines
          2          45              48                       0
          2          36               6                      66
```

Thus the precise conclusion is

```text
216 circuits != 216 hemisystem lines as PSp(4,3)-sets,
and they remain unequal as Aut(W(3,3))-sets.
```

The character decomposition identifies the decisive sector.  Over
`PSp(4,3)` the circuit action contains the 81-dimensional Steinberg module
once, while the hemisystem-line action contains it zero times.  Schematically,

```text
circuits:    1 + 2*15 + 20 + 24 + 30 + 30 + 30 + 81
hemisystems: 1 + 6 + 15 + 2*20 + 30 + 60 + 64.
```

The full automorphism decomposition retains the same `81: 1 versus 0`
separation.  This links the no-go to the new obstruction-product results in
W33-Theory: the five-circuit shell is a native Steinberg-bearing carrier; the
hemisystem shell is not.

The equal cardinality is real, but it is not an equivariant dictionary.  This
also explains why the previously requested fibre-level identification never
materialized: it cannot exist under either native symmetry action.

## Replay and boundary

```bash
gap -q analysis/w33_circuit_hemisystem_gset_bridge.g
node analysis/w33_circuit_hemisystem_gset_bridge.js --write
node --test tests/w33-circuit-hemisystem-gset-bridge.test.js
```

This rules out an equivariant identification.  It does not rule out a
non-equivariant lookup table, a larger common cover, or a relation obtained
after adding new structure.  It has no physical interpretation and changes no
blocking bound.
