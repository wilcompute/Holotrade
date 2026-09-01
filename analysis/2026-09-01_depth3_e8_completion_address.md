# Depth-3 obstruction edges now have unique E8 completion addresses

This note composes two independently certified object identifications.

Holotrade already proves that its 270 depth-three all-isotropic-regulus obstructions are exactly the 270 support-disjoint pairs among the 45 sentinel minimum words / tritangent-plane supports.  Their graph is `GQ(4,2)`: 45 vertices, degree 12, 27 maximal cliques of size five, every edge in exactly one clique.

W33-Theory independently lifts those same 45 tritangent supports through its certified six-roots-per-W33-point E8 fibration.  Each support is an orthogonal `D4+D4` packet with 48 roots, and each one of the 27 `GQ(4,2)` lines is a five-packet partition of all 240 E8 roots into ten selected `D4` subsystems.

Therefore every local obstruction edge has a deterministic cross-repository completion address:

```text
one depth-3 obstruction regulus
    = one support-disjoint packet pair
    = 2 x 48 = 96 selected E8 roots
    -> unique GQ(4,2) five-clique
    -> add the remaining 3 packets = 144 roots
    -> complete 240-root / ten-D4 E8 chart
```

The exact incidence identity is

```text
270 = 27 * C(5,2).
```

The important word is **unique**: this is not an arbitrary routing convention.  Every one of the 270 obstruction edges lies in exactly one of the 27 five-cliques, already certified locally in `data/the_depth3_obstruction_is_a_quadrangle.json`; the W33 certificate proves that the corresponding five packets partition the E8 root shell.

This gives Holotrade a finite routing primitive: an obstruction can be tagged by its canonical 27-way completion chart.  It may be useful as a feature or controller label because it is derived from exact geometry rather than fitted telemetry.

## Evidence boundary

No scheduling or blocking bound moves.  In particular, this does **not** imply that an E8 chart removes the obstruction, and it does not assign physical dynamics to E8.  `tau_2(W(3,3)^2)` remains open in `[111,115]`.

Cross-repo W33 certificates:

- verifier commit `322c5031b09287f0ff55ea9019f0441a00af7a4d`
- frozen certificate commit `3deb82ee68c2e67a186342c31bbd2da4d6ddd686`
- `data/PART_W33_20260901_REGULUS_E8_COMPLETION_BRIDGE.json`
