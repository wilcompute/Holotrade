# Holotrade integration: W33 optimal near-ovoid defect dipoles

The earlier Holotrade result `analysis/w33_ovoid_deficiency.py` proved by CP-SAT that

\[
\operatorname{def}(W(3,3))=3
\]

and exhibited the optimum line profile

\[
0^3 1^{34} 2^3.
\]

W33-Theory has now upgraded that numerical optimum to a complete exact classification, using line-graph projector arithmetic and a dependency-light backtracker rather than the optimization solver.

Source-of-truth commits in `wilcompute/W33-Theory`:

- `dd770350d39b22d0a50c3586feb7283eebaac4ea` — exact executable proof;
- `7b71c98cb181b73f7fa9464f543cb0b51615af20` — frozen theorem certificate;
- `51761470746215b9d885d1507e9a25455d153d7d` — theorem note.

## Structural upgrade

Every optimal 10-set is a **defect dipole**. Its three missed lines are the punctured four-line pencil at a point `a`; its three doubled lines are the punctured pencil at a second point `b`; and `a,b` are collinear. Their common line is the hinge left out of both triples and is hit exactly once.

There are

\[
40\cdot12=480
\]

oriented collinear pairs `(a,b)`, and exactly six optimal 10-set completions over each one. Hence

\[
\boxed{480\cdot6=2880}
\]

optimal near-ovoids.

The W33 theorem further proves that `PSp(4,3)` is transitive on those 2880 states with `C3 x C3` stabilizer. For a fixed oriented dipole the order-54 edge stabilizer acts transitively on its six completions through an order-18 image `C3 x S3` with kernel `C3`.

## What Holotrade imports

`analysis/w33_ovoid_defect_dipole_integration.py` rebuilds enough of `W(3,3)` locally to verify:

- the `9720 + 40*4` triple-signature collision census;
- that the forty fourfold collision classes are exactly punctured-pencil classes;
- that a representative oriented dipole has exactly six completions;
- that every one of those six has profile `0^3 1^34 2^3`;
- that the pre-existing Holotrade CP-SAT artifact still says deficiency `3`, status `OPTIMAL`, with the same profile.

The integration certificate therefore exposes a safe test namespace:

\[
\boxed{480\text{ coarse defect channels}\times6\text{ exact completion states}.}
\]

That is useful for regression, fuzzing, evidence-path replay, and geometry-aware placement tests because it gives a complete finite family rather than a random witness.

## Firewall

This classification does **not** change any Holotrade scheduler guarantee by itself.

More importantly, the six completion states are not automatically the same six as any other six-state object in the project. The current `P^1(F9)` / Hall--Janko frontier, `G_2` Weyl packets, and various `S_3` control quotients all contain sixes with different actions. Holotrade must not identify them from cardinality. Any such bridge still needs an explicit equivariant map, module character match, or other theorem-grade intertwiner.
