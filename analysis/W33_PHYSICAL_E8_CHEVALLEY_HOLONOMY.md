# Physical E8 Chevalley lift of the flagship holonomy pair

The 40-vs-36 parity firewall is resolved by using the correct category of lift.
Physical theta^3 and W3 are inner SU(9) torus holonomies, so they act diagonally
on E8 root spaces; they do not need to permute E8 roots.

Using the regular maximal branching E8 -> SU(9),
`248 = 80 + 84 + 84bar = sl9 + Lambda^3(9) + Lambda^6(9)`,
and the flagship joint fundamental spectrum, the full E8 joint multiplicities are:
`(0,+),(0,-),(1,+),(1,-),(2,+),(2,-) = 44,48,38,40,38,40`.
The product C6 spectrum is `44,40,38,48,38,40`.

Exact fixed algebras:
- order-3 Wilson line: 84 neutral roots = D7, plus u1; dimension 92;
- physical order-2 theta^3: 112 neutral roots = D8; dimension 120;
- order-6 product: 36 neutral roots = D4 + A3, plus u1; dimension 44.

This is the physical Chevalley-level E8 lift. The separate Coxeter-fiber
root-permutation envelope remains mathematically valid but is a label lift, not
the physical parity operation.

Source: `wilcompute/W33-Theory:data/w33_physical_holonomy_e8_chevalley_lift.json`.