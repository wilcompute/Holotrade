# W33 chirality becomes an operational Holotrade migration quotient

Date: 2026-08-29

**Status: PASS.** The executable audit is
`analysis/w33_near_ovoid_chirality_bridge.js`; the frozen certificate is
`data/w33_near_ovoid_chirality_bridge.json`. The production surface is
`scheduler/w33-near-ovoid-migration.js`, and
`tests/near-ovoid-migration.test.js` exhausts the 2,880-state corpus.

## 1. Two independently discovered 3+3 partitions are the same partition

Holotrade had already proved an operational fact. For a fixed oriented defect
pair `(a,c)`, its six hidden near-ovoid microstates have four-point
`highRelease` signatures. Join two states when those signatures intersect.
The result is always

`K3 disjoint union K3`.

Independently, W33-Theory reconstructed the exact oriented-edge stabilizer and
proved that its six-state action has image

`C3 x S3 = (C3 x C3) : C2`,

with a **unique nontrivial 3+3 system of imprimitivity**. The two blocks are
selected by the two residual points of the hinge line `ac`: each high-release
tetrad contains exactly one residual hinge point.

The present audit checks all 2,880 Holotrade states and proves that these are
not merely two isomorphic 3+3 structures. They are literally the same
partition in the production coordinates.

## 2. The scheduler can recover the C2 quotient directly

For a state with defect centre `a` and blocker centre `c`, let the hinge line
be

`{a,c,r0,r1}`.

The production analyzer now exposes

- `residualHingePoints = [r0,r1]`;
- `chiralityAnchor`, the unique one of `r0,r1` lying in `highRelease`;
- `chiralityBit`, the index of that anchor after sorting the two point ids.

The anchor is geometric. The numeric 0/1 encoding is only a deterministic
serialization convention; it is not claimed invariant under arbitrary point
relabeling.

For every one of the 480 oriented defect pairs:

- exactly three microstates choose the first residual hinge point;
- exactly three choose the second;
- those two triples are exactly the two connected K3 components of the
  high-release intersection graph;
- the common point of all three high-release tetrads in a component is exactly
  that component's residual hinge anchor.

Globally this gives 960 three-state chirality halves. Each of the 40 W33 points
occurs as a chirality anchor in exactly 72 states.

## 3. What Holotrade gets from the W33 `F3 x F2` normal form

The `F2` factor is now operational rather than merely representational: it is
the one-release migration quotient selected by the residual hinge anchor.
The W33 `C2` quotient swaps those two anchors and therefore swaps the two
migration halves.

The three-state factor needs more care. W33 proves a threefold cyclic structure
inside the six-state action, but Holotrade's scheduler-visible data do not pick
an origin or orientation around either three-cycle. Operationally each half is
therefore a **C3 torsor**, not a canonically numbered `F3={0,1,2}` register.
Assigning a qutrit phase label requires an extra gauge convention or additional
physical/control state.

That boundary is important: the implementation gets the theoremically forced
binary quotient without inventing a phase coordinate the data do not select.

## 4. Why this matters operationally

Current free-line placement still depends only on `(a,c)`, so the six hidden
states remain equivalent for the immediate four-node placement decision. They
are not equivalent under a release. The chirality anchor compresses the first
nontrivial part of the hidden state into a robust geometric bit:

`2880 states -> 480 placement classes -> 960 migration chirality halves`.

Within each half, all three states share the same residual hinge anchor but
retain distinct high-release tetrads. Thus a two-level controller can carry

1. the `(a,c)` placement state;
2. the chirality anchor for migration-class selection;
3. the full high-release signature only when the exact source choice is
   required.

This is a principled state-compression hierarchy derived from the finite
geometry rather than from a heuristic feature clustering.

## 5. Evidence boundary

Here `chirality` names the exact `C2` block quotient of the six-state local
group action. No particle chirality, fermion handedness, or laboratory qutrit
is inferred. The result is an exact bridge between W33 finite group theory and
Holotrade's release/migration scheduler.
