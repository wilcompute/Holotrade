# W(3,3) optimal reservation shapes: from spectral bounds to a placeable catalogue

**Evidence status:** exact finite mathematics. Every claim below is settled by
exhaustive computation over a 40-vertex graph and independently re-checked by a
second method with no shared code path. Nothing here is a model, a simulation,
or a fitted coefficient.

**Artifacts**

| file | what it is |
|---|---|
| `analysis/w33_shape_catalogue.js` | the classification, by constrained combinatorial search |
| `analysis/w33_shape_catalogue_check.py` | independent re-derivation by eigenspace projection |
| `analysis/w33_automorphisms.js` | the symmetry group, and shape transport |
| `scheduler/w33-shapes.js` | the scheduler-facing reservation API |
| `data/w33_shape_catalogue.json` | frozen catalogue with witnesses and exact counts |
| `analysis/w33_shape_guarantees.js` | worst-case blocking numbers, by branch and bound |
| `analysis/w33_blocking_sat.py` | the same, by SAT, with UNSAT proofs below tau |
| `analysis/w33_shape_packing.js` | perfect tilings and maximum packings |
| `analysis/w33_shape_catalogue.g` | GAP/GRAPE certificate: full automorphism group |
| `analysis/w33_gap_certificate.js` | runs GAP and cross-checks every artifact |
| `analysis/w33_level2.js` | the level-2 fabric under three constructions |
| `analysis/w33_level2_shapes.js` | the lift theorem, verified |
| `analysis/w33_level2_check.py` | level-2 spectra checked numerically |
| `analysis/w33_level2_guarantees.js` | level-2 blocking numbers and the collapse |
| `analysis/w33_leveln_classification.js` | the level-n classification |
| `tests/shape-catalogue.test.js` | 56 regression tests |

---

## 1. What was missing

`research/w33_scheduler_math.md` derives, for any vertex set `T` of size `m` in
the W(3,3) point graph `SRG(40,12,2,4)` with spectrum `{12¹, 2²⁴, (−4)¹⁵}`:

```
    m(40−m)/4  ≤  b(T)  ≤  2m(40−m)/5
    m(m−10)/5  ≤  e(T)  ≤  m(m+8)/8
```

Those are **bounds**. A scheduler cannot reserve a bound — it reserves a **set**.
So the operational question is not "how dense could a shape of this size be" but
"which sizes admit a shape that actually attains the bound, and what is it".

This packet answers that exactly.

## 2. Turning each bound into a finite condition

Write `1_T` for the indicator vector and `f = 1_T − (m/40)·1`, the component
orthogonal to the all-ones vector. Then

```
    b(T) = 12m(1 − m/40) − fᵀAf,        ‖f‖² = m(1 − m/40).
```

The bounds come from `−4‖f‖² ≤ fᵀAf ≤ 2‖f‖²`, so **equality on either side
happens exactly when `f` lies entirely in one eigenspace**. Applying the strongly
regular identity `A² = 8I − 2A + 4J` converts each eigenspace condition into a
pure counting condition on neighbourhoods:

| | condition | divisibility forced |
|---|---|---|
| **upper** (densest, `f ∈ E₂`) | `\|N(v) ∩ T\| = 2 + m/4` inside, `m/4` outside | `4 \| m` |
| **lower** (most spread, `f ∈ E₋₄`) | `\|N(v) ∩ T\| = 2m/5 − 4` inside, `2m/5` outside | `5 \| m` |

These are the classical *intriguing sets* of a strongly regular graph, of
positive and negative type. Neither divisibility condition is sufficient —
existence has to be decided.

## 3. The classification

Exhaustive constrained search over all 40 vertices, with full propagation on the
counting constraints. Every search below ran to completion; none was capped.

### Densest shapes — one at every multiple of four

| m | `\|N∩T\|` in/out | e(T) bound | attained | b(T) | number of such sets |
|---:|---|---:|:---:|---:|---:|
| 4 | 3 / 1 | 6 | yes | 36 | 40 |
| 8 | 4 / 2 | 16 | yes | 64 | 585 |
| 12 | 5 / 3 | 30 | yes | 84 | 5,400 |
| 16 | 6 / 4 | 48 | yes | 96 | 21,330 |
| 20 | 7 / 5 | 70 | yes | 100 | 33,264 |
| 24 | 8 / 6 | 96 | yes | 96 | 21,330 |
| 28 | 9 / 7 | 126 | yes | 84 | 5,400 |
| 32 | 10 / 8 | 160 | yes | 64 | 585 |
| 36 | 11 / 9 | 198 | yes | 36 | 40 |

**A densest shape exists for every admissible size.** That is the useful outcome:
whenever a request is a multiple of four, there is a provably optimal shape to
serve it, and the catalogue holds a witness.

Two structural checks fall out of the table itself:

- **The counts are a palindrome.** 40, 585, 5400, 21330, 33264, 21330, 5400, 585, 40.
  That is forced: if `f ∈ E₂` then `−f ∈ E₂`, so the complement of a densest shape
  is a densest shape, and the count at `m` must equal the count at `40−m`. The
  search found this without being told, which is a real check on it.
- **`b(T)` peaks at m = 20 with the value 100** — the certified balanced bisection
  already in the repository. The densest 20-shape and the optimal balanced cut are
  the same object.

### The four-point shape is a line

There are exactly 40 densest 4-point shapes, and they are **precisely the 40
totally isotropic lines of the quadrangle**. Verified three ways: by the
constrained search, by brute force over all `C(40,4) = 91,390` subsets, and by
direct identity with the substrate's own line list. Each induces a `K₄` and so
attains the clique bound.

The geometry's own lines are the optimal four-node reservations. Nothing was
designed to make that true.

### Most-spread shapes — exactly one size

| m | `\|N∩T\|` in/out | e(T) bound | attained | count |
|---:|---|---:|:---:|---:|
| 5 | −2 / 2 | — | **no** (target negative) | 0 |
| 10 | 0 / 4 | 0 | **no** | 0 |
| 15 | 2 / 6 | 15 | **no** | 0 |
| 20 | 4 / 8 | 40 | **yes** | 432 |
| 25 | 6 / 10 | 75 | **no** | 0 |
| 30 | 8 / 12 | 120 | **no** | 0 |
| 35 | 10 / 14 | 175 | **no** | 0 |

**m = 20 is the only size admitting a perfectly spread set**, and there are
exactly 432 of them, forming a single orbit. Every other admissible size is
*impossible*, not merely unfound — the searches were exhaustive.

## 4. The strongest claim: no ovoid

| quantity | ratio bound | true value | attained |
|---|---:|---:|:---:|
| clique number ω | `1 − k/s` = 4 | **4** | yes |
| independence number α | `n(−s)/(k−s)` = 10 | **7** | **no** |

A 10-set attaining the Hoffman ratio bound would be exactly an **ovoid** of this
generalized quadrangle. The search shows none exists — reproducing Thas's
odd-`q` theorem **by exhaustive computation rather than by citing it**. That
matters for this repository's discipline: it is a check *on* the literature, not
a reference to it.

The operational reading is a hard constraint the scheduler did not previously
have:

> **No eight nodes can be placed with zero shared links.** Seven is the ceiling
> on failure-independent replica placement, at any price, on any fabric of this
> shape.

## 5. Making the catalogue placeable

A witness lives at fixed point indices, and in a live fabric those points are
usually busy. A catalogue nobody can place is a wall poster.

The fix is the symmetry group. Closing the symplectic transvections
`T_{v,a}(x) = x + a⟨x,v⟩v` over the 40 projective points gives a permutation
group of order **25,920**, verified point-transitive (orbit 40/40), edge-transitive
(orbit 480/480), with point stabiliser 648 and `648 × 40 = 25,920` confirming
orbit–stabiliser.

That is **PSp(4,3), the projective symplectic group** — deliberately *not* the
51,840 of `Sp(4,3)` or of the Weyl extension `W(E₆)`. A scalar acts trivially on
projective points. The substrate notes are emphatic that the three must not be
conflated, so the order is asserted in a test rather than assumed.

Because an automorphism preserves adjacency, it preserves induced-edge count and
boundary **exactly**. So a shape can be transported onto free nodes and carries
its optimality with it — not approximately, but as a consequence of what
"automorphism" means. `reserveShape()` walks the orbit for an image landing
entirely on free nodes, and asserts the preservation rather than trusting it.

### Shape orbits

| kind | m | orbit size | set stabiliser |
|---|---:|---:|---:|
| densest | 4 | 40 | 648 |
| densest | 8 | 45 | 576 |
| densest | 12 | 1,080 | 24 |
| densest | 16 | 270 | 96 |
| densest | 20 | 3,240 | 8 |
| densest | 24 | 6,480 | 4 |
| densest | 28 | 1,080 | 24 |
| densest | 32 | 540 | 48 |
| densest | 36 | 40 | 648 |
| spread | 20 | 432 | 60 |

Orbit × stabiliser = 25,920 in every row.

## 6. A result worth flagging: orbit size does not predict placeability

The intuitive guess is that a shape with a large orbit is easy to place. **It is
not.**

| m | orbit | always placeable up to |
|---:|---:|---:|
| 4 | 40 | ~18 busy nodes |
| 8 | 45 | ~9 |
| 12 | 1,080 | ~8 |
| 16 | 270 | ~5 |
| 20 | 3,240 | ~5 |

The m=12 shape has an orbit twenty-four times larger than the m=8 shape and
tolerates *fewer* busy nodes. Size dominates: a shape of `m` points needs `m`
free points before any image can fit at all, and rigidity does the rest.

This is the number a scheduler actually needs — the point at which it should
stop promising an optimal shape and say so. `reserveShape()` refuses with a
reason and a fallback hint rather than returning a degraded subset, because a
shape that has lost a point is no longer the shape whose optimality was proved.

*(These figures are sampled over random blocked sets, and labelled as sampled in
the API response. The exact answer would require every subset of blocked nodes.)*

## 7. Independent verification

`analysis/w33_shape_catalogue_check.py` reaches every result by a **different
method**: it rebuilds the graph from the symplectic form in Python, diagonalises
the adjacency matrix, constructs the eigenprojectors, and tests each witness by
projection — linear algebra against combinatorial search, sharing no code.

It confirms:

- the graph, the spectrum, and that the projectors resolve the identity;
- every densest witness has zero component in `E₋₄` (residual `< 1e-15`);
- every spread witness has zero component in `E₂`;
- `2e(T) + b(T) = 12m` on every witness;
- α = 7 by an independently written search, and therefore no ovoid;
- the complementation theorem on all nine densest witnesses.

All checks pass.

## 8. Worst-case placement guarantees

`placementCapacity()` reports a **sampled** figure: over random sets of busy
nodes, how often a shape can still be placed. That is honest but weak. A
scheduler wants a guarantee:

> with at most `B` nodes busy, a densest `m`-node reservation is always
> placeable — **no matter which** nodes are busy.

That is exact. A blocked set `X` defeats a shape exactly when every image of it
under the automorphism group meets `X` — that is, when `X` is a **blocking set**
for the shape's orbit. So if `τ` is the minimum blocking set,

* with `|X| ≤ τ − 1` busy nodes a placement **always** exists;
* with `|X| = τ` an adversary can make placement impossible.

`τ − 1` is the guarantee, and `τ` is exactly where the cliff is.

### A lower bound from transitivity

The orbit of a shape under a point-transitive group is balanced: every point
lies in exactly `|orbit|·m/40` images. One blocked point therefore hits at most
that many, so

```
    τ  ≥  |orbit| / (|orbit|·m/40)  =  40/m,     hence  τ ≥ ⌈40/m⌉.
```

### The results

| m | orbit | counting bound ⌈40/m⌉ | τ | **busy nodes tolerated** |
|---:|---:|---:|---:|---:|
| 4 | 40 | 10 | **11** | **10** |
| 8 | 45 | 5 | **8** | **7** |
| 12 | 1,080 | 4 | **8** | **7** |
| 16 | 270 | 3 | **6** | **5** |
| 20 | 3,240 | 2 | **6** | **5** |
| 24 | 6,480 | 2 | **4** | **3** |
| 28 | 1,080 | 2 | **4** | **3** |
| 32 | 540 | 2 | **3** | **2** |
| 36 | 40 | 2 | **2** | **1** |

and for the perfectly spread set: `m = 20`, orbit 432, τ = 3, tolerating 2.

Computed **twice, independently**: by branch and bound in
`analysis/w33_shape_guarantees.js`, and by SAT in `analysis/w33_blocking_sat.py`,
where every size below `τ` is discharged as **UNSAT** — which is what makes each
figure a proof of a lower bound rather than an unsuccessful search. The two
solvers agree on every shape.

### Why the four-node guarantee is exactly 10

This is the result worth reading twice, because it is the no-ovoid theorem
wearing different clothes.

The densest 4-point shapes are exactly the 40 lines, so defeating them means
hitting every line. Each point lies on 4 lines, so `k` points cover at most `4k`
incidences and covering all 40 needs `k ≥ 10`. **Equality would require all 40
incidences to be distinct** — no two of the ten points collinear — which is
precisely an ovoid. §4 showed this quadrangle has none. Therefore `τ ≥ 11`, and
the search finds `τ = 11` exactly.

> **A four-node densest reservation survives any ten simultaneous busy or failed
> nodes**, and eleven specific ones can defeat it. The bound is tight in both
> directions.

The abstract non-existence of an ovoid is not a curiosity here. It is the reason
the guarantee is 10 rather than 9.

### What the table says operationally

The guarantee **falls** as shapes grow: 10, 7, 7, 5, 5, 3, 3, 2, 1. And it again
has nothing to do with orbit size — `m=8` (orbit 45) and `m=12` (orbit 1,080)
have **the same** blocking number of 8, despite a twenty-four-fold difference in
how many placements exist. The counting bound is tight only at `m = 36`.

So the scheduler's admission rule is a lookup, not a simulation: past
`τ − 1` busy nodes, stop promising an optimal shape of that size and say so.

## 9. Perfect packings: the sizes that strand nothing

A tiling is the fragmentation-free schedule — every node used, every reservation
provably densest, nothing left stranded between jobs. Two arithmetic constraints
decide which sizes can even try:

* a densest shape needs `4 | m`
* a tiling needs `m | 40`

so only `m ∈ {4, 8, 20, 40}` are candidates, before any search runs.

| m | densest shapes | m divides 40 | tilings | outcome |
|---:|---:|:---:|---:|---|
| 4 | 40 | yes | **36** | **perfect tiling** |
| 8 | 585 | yes | **57,132** | **perfect tiling** |
| 12 | 5,400 | no | — | max 3 disjoint, 4 stranded |
| 16 | 21,330 | no | — | max 2 disjoint, 8 stranded |
| 20 | 33,264 | yes | **16,632** | **perfect tiling** |
| 24 | 21,330 | no | — | max 1 disjoint, 16 stranded |
| 28 | 5,400 | no | — | max 1 disjoint, 12 stranded |
| 32 | 585 | no | — | max 1 disjoint, 8 stranded |
| 36 | 40 | no | — | max 1 disjoint, 4 stranded |

**All three non-trivial candidates tile.** The `m = 4` tilings are the classical
**spreads** of the quadrangle — ten disjoint lines meeting every point-star
exactly once — and there are exactly 36, reproducing the substrate corpus's
count independently. The `m = 8` count of 57,132 is new here. And
`16,632 = 33,264 / 2` exactly, because every densest 20-set tiles with its own
complement: the complementation theorem showing up a third time, now as a factor
of two.

> **Reserve in units of 4, 8 or 20 and the cell partitions perfectly.** At any
> other size, capacity is stranded by arithmetic: 4 nodes at m=12, 8 at m=16.

### A bug this caught

The first version of the packing search looked for tilings inside the **orbit**
of a single catalogue witness. It reported *no tiling at m = 20*, which directly
contradicts the proved complementation theorem — so something had to be wrong.

The orbit of that witness has 3,240 members out of 33,264 densest 20-sets, so
the complement simply was not in the pool being searched. **Orbit is not
isomorphism class here**, and only `m = 4` has a single orbit, which is why that
case looked correct. Searching the full pool gives 16,632.

The contradiction was only visible because the theorem had already been proved.
A search with no prediction to violate would have reported the wrong answer
quietly.

## 10. GAP: the full automorphism group

The transvection closure in §5 gives 25,920 = PSp(4,3). That is the *projective*
group, and it left a real gap: placement cares about the automorphism group of
the **graph**, which could be larger. If it were, shapes would have more images
and the guarantees in §8 would be conservative.

GRAPE/nauty settles it:

| | |
|---|---:|
| \|Aut(graph)\| | **51,840** |
| \|PSp(4,3)\| | 25,920 |
| index | **2** |
| rank | 3 |
| suborbits | 1, 12, 27 |
| point stabiliser | **1,296** |

The graph's automorphism group is an index-2 extension of PSp(4,3). But **every
shape orbit is unchanged in size, and every set stabiliser exactly doubles** —
the extra involution carries each shape back into its own PSp(4,3)-orbit rather
than to new images.

So the blocking numbers and guarantees are **exact, not conservative**, and are
now certified against the true automorphism group rather than a subgroup.

Two details worth noting because they close loops elsewhere in the corpus: the
point stabiliser order **1,296** is exactly the `|N_G(P₃)|` of the UOR address
factorisation `2⁶⁴ = 40 × 1296 × payload`, and the suborbits **1 + 12 + 27 = 40**
are exactly the rank-3 shell `js/uor.js` already implements. Both were asserted
in the source papers; GAP verifies them here as facts about the graph.

## 11. Level 2: the recursion as an actual graph

Everything above is level-1: one 40-point cell. The repository's recursive layer
is a **distance formula**, not a graph -- `js/substrate.js` computes hops as
"route in the first divergent cell, then eight moves per descent on each side",
giving `16n - 14`, and the paper labels it MODELLED with the note *"no physical
product graph"*.

That label is honest, and it is also the gap: a distance formula cannot tell you
the degree, the spectrum, the bisection, or whether an optimal shape exists one
level up. Only a graph can.

### Three constructions, three different machines

A level-2 leaf is a pair `(c, p)`. How cells are wired is a real engineering
choice, and the cost differs enormously:

| construction | degree | edges | diameter | expansion | cell-split cut |
|---|---:|---:|---:|---:|---:|
| cartesian | 24 | 19,200 | **4** | 0.4167 | 4,000 |
| lexicographic | 492 | 393,600 | **2** | 0.8130 | 160,000 |
| hierarchical-gateway-4 | 12–24 | 10,560 | **5** | — | 400 |

- **Cartesian** `W [] W` -- each leaf keeps its 12 intra-cell links and gains one
  per neighbouring cell, to the same point position. Homogeneous, no gateway.
- **Lexicographic** `W[W]` -- adjacent cells fully meshed. Diameter 2 at any
  level, and a wiring bill that grows quadratically.
- **Hierarchical** -- inter-cell traffic funnels through one 4-point line per
  cell. This is the shape the software's distance model implies.

Spectra, closed-form and verified numerically in
`analysis/w33_level2_check.py`:

```
    Cartesian      24^1  14^48  8^30  4^576  (-2)^720  (-8)^225
    lexicographic  492^1  92^24  2^960  (-4)^600  (-148)^15
```

### Two findings

**Scaling up costs expansion.** A single cell has `(k - lambda2)/k = 10/12 =
0.833`. The Cartesian fabric has `10/24 = 0.417` -- half as good. The
lexicographic fabric buys back almost all of it (`0.813`) but at forty times the
wiring. There is no free scale-up.

**The `16n - 14` bound is measuring something else.** It gives 18 at level 2, but
the measured diameter of an explicit fabric is **4** (Cartesian) or 5
(hierarchical). The two are not comparable: `hopsPerDigit = 8` is a *declared
descent cost* in reversible control moves -- the corpus's "three cube moves plus
five chart-web moves per digit" -- not a graph distance. Both numbers are fine;
conflating them is not. A network sizing exercise wants 4; a reversible compiler
wants 8 per digit.

## 12. The lift theorem: shapes survive one level up

The backend question is whether a multi-cell reservation needs a fresh search
over 1,600 vertices. It does not.

On the Cartesian fabric the same spectral argument gives

```
    e(T) <= 7m + m^2/320,   equality iff f lies in the 14-eigenspace.
```

Let `T1` be a level-1 densest shape, so `f1` lies in the 2-eigenspace of `A1`.
Replicate it in every cell: `T = {(c,p) : p in T1}`, indicator `1 (x) 1_T1`, so
`f = 1 (x) f1` and

```
    (A1 (x) I + I (x) A1)(1 (x) f1) = 12(1 (x) f1) + 2(1 (x) f1) = 14(1 (x) f1).
```

It lands exactly in `E_14`. **The level-1 catalogue lifts.** The dual lift --
every point inside a densest set of *cells* -- works identically, from
`2 + 12 = 14`.

All 18 lifts (9 sizes, 2 directions) attain the level-2 bound exactly, are
two-valued intriguing sets, and match the arithmetic prediction. Natural
non-lifted constructions (the diagonal, a product of two shapes) fall well short
and are not two-valued, so the replication structure is doing the work.

> **A provably densest 160-node reservation is "the same optimal 4-shape in
> every cell."** No search over 1,600 vertices, no heuristic -- assembled from a
> catalogue that already exists.

Available level-2 sizes: 160, 320, 480, 640, 800, 960, 1120, 1280, 1440 -- the
level-1 ladder scaled by the cell size, and nothing between them.
`scheduler/w33-shapes.js` exposes this as `optimalShapeLevel2()`, refusing
anything off the ladder with the nearest attainable size.

## 13. Level-2 guarantees, and a collapse the spectral argument hides

The lift theorem gives provably densest level-2 reservations, and the API
exposed them with a `note` admitting the guarantee had never been computed
there. It can be, exactly, and the answer changes how the lifts should be used.

### The product theorem

By Sabidussi--Vizing the automorphism group of a square of a connected prime
graph is `Aut(W) wr S2`: elements act as `(c,p) -> (g(c), h(p))`, plus the swap.
Applying those to a by-points lift gives `L_P(h(T1))`, and the swap gives the
by-cells lift, so the orbit is exactly

```
    { L_P(T1') } union { L_C(T1') },   T1' ranging over the level-1 orbit.
```

For a blocked set `X` write `P(X)` for its point shadow and `C(X)` for its cell
shadow. Then `X` meets `L_P(T1')` iff `P(X)` meets `T1'`, and likewise for cells.
So `X` blocks everything iff **both shadows are level-1 blocking sets**, giving
`|X| >= |P(X)| >= tau_1`. And it is attained: put `X` on the diagonal,
`X = {(b,b) : b in B}` for a level-1 blocking set `B`, and both shadows equal `B`.

```
    tau_2 = tau_1   exactly.
```

| m1 | m2 | orbit | tau | **busy tolerated** | fraction, level 1 | fraction, level 2 |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 160 | 40 | 11 | **10** | 25.00% | 0.625% |
| 8 | 320 | 45 | 8 | **7** | 17.50% | 0.438% |
| 16 | 640 | 270 | 6 | **5** | 12.50% | 0.312% |

### The collapse

The reservation grew 40x. The fabric grew 40x. **The number of simultaneous
failures it survives did not grow at all.**

So the survivable *fraction* collapses by exactly the cell size, every time:
25% becomes 0.625%. Eleven well-chosen leaves out of sixteen hundred defeat an
optimal 160-node reservation.

Nothing in the spectral argument warns about this. Optimality and fault
tolerance are separate questions, and the bound only answers the first. It shows
up only if you refuse to extrapolate the level-1 number and compute the level-2
one instead -- where it turns out to be numerically identical and operationally
completely different.

### The trade, and why one lift wins outright

If lifting is fragile, the obvious move is to confine the reservation to fewer
cells. Measured at 160 leaves:

| cells | per cell | e(T) | bound | efficiency | cells left free | |
|---:|---:|---:|---:|---:|---:|---|
| 4 | 40 | 1200 | 1200 | 100.0% | 36 | by-cells lift: optimal AND confined |
| 5 | 32 | 928 | 1200 | 77.3% | 35 | optimal per cell |
| 8 | 20 | 880 | 1200 | 73.3% | 32 | optimal per cell |
| 10 | 16 | 720 | 1200 | 60.0% | 30 | optimal per cell |
| 20 | 8 | 880 | 1200 | 73.3% | 20 | optimal per cell |
| 40 | 4 | 1200 | 1200 | 100.0% | 0 | by-points lift: a target in every cell |

Two rows reach the bound, and they are the two lifts. Everything in between is
strictly worse: the inter-cell links given up are not repaid by the intra-cell
links gained.

> **byCells is Pareto-dominant.** Same density, same blocking number, and it
> leaves **36 of 40 cells completely untouched** for other tenants where
> byPoints leaves none. It is now the default in `optimalShapeLevel2()`.

### A bug worth recording

The first version of the confinement table took the first `k` cell indices,
which happen to be mutually non-adjacent. No inter-cell link was captured, the
4-cell row scored 80% instead of 100%, and confinement looked strictly worse
than lifting -- the opposite of the truth.

**Which cells matters as much as how many.** Choosing them as an optimal level-1
shape -- a line, for four cells -- recovers every inter-cell link the geometry
allows and lands exactly on the bound.

## 14. Every densest shape, at every level, is a lift

Section 13 found that lifted reservations do not get more robust as the fabric
grows. The obvious escape was to look for level-2 optimal shapes that are **not**
products -- something built directly on the 1,600-vertex graph that might spread
its risk differently.

**There are none.** The lift theorem is not a construction, it is a
classification, and the proof is four lines.

### The argument

At level `n` the fabric is the `n`-fold Cartesian power, with eigenvalues all
`n`-fold sums from `{12, 2, -4}`. So

```
    k = 12n,   lambda_2 = 12(n-1) + 2 = 12n - 10,   k - lambda_2 = 10
```

for **every** `n`. A set attains the densest bound exactly when
`f = 1_T - (m/N)1` lies wholly in the `lambda_2`-eigenspace, and for a Cartesian
power that eigenspace is the level-1 2-eigenspace placed in **one** coordinate:

```
    E_{12n-10}  =  (+)_i  1 (x) ... (x) E_2 (x) ... (x) 1,     dim = 24n.
```

So `1_T(x_1,...,x_n) = m/N + f_1(x_1) + ... + f_n(x_n)` -- a sum of functions of
separate coordinates. But `1_T` takes only the values 0 and 1, and for finite
sets of reals `|A_1 + ... + A_n| >= sum|A_i| - (n-1)`. The left side is at most
2, so `sum|A_i| <= n+1`, so **at most one `f_i` is non-constant** and the rest
vanish, being orthogonal to all-ones.

`T` is therefore a level-1 tight set in one coordinate and everything in the
others. That is exactly a lift. There is no third kind.

### The ladder

| n | leaves | degree | lambda_2 | gap | expansion | smallest densest shape | survivable |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 12 | 2 | **10** | 0.8333 | 4 | 25.00000% |
| 2 | 1,600 | 24 | 14 | **10** | 0.4167 | 160 | 0.62500% |
| 3 | 64,000 | 36 | 26 | **10** | 0.2778 | 6,400 | 0.01562% |
| 4 | 2,560,000 | 48 | 38 | **10** | 0.2083 | 256,000 | 0.00039% |
| 5 | 102,400,000 | 60 | 50 | **10** | 0.1667 | 10,240,000 | 0.00001% |

Three things to read off, all of them bad for large fleets:

**The spectral gap is 10 at every level.** It never grows. Expansion decays as
`10/(12n)`, so the fabric gets structurally *worse* at connecting itself the
bigger it gets.

**The ladder is 40x coarser per level.** At level 5 the smallest provably-densest
reservation holds **10,240,000 leaves**, and there is nothing at all below it.
Nine rungs, always, spaced `4 x 40^(n-1)` apart.

**Robustness never improves.** Ten failures, at every level, for every shape --
0.00001% of a level-5 fabric.

### What the backend does with this

Provably-densest reservations are a **level-1 tool**. Above that the honest move
is to compose level-1 shapes inside cells and accept a sub-optimal joint, which
is what the confinement measurements in section 13 support.
`scheduler/w33-shapes.js` exposes `levelAdvice()`, which refuses off-ladder
requests, reports the survivable fraction, and says so directly rather than
quoting a bound nobody can use.

### Prior art

None of the machinery is new. Intriguing sets and tight sets are Payne (1987)
and Bamberg--Kelly--Law--Penttila; the same objects are **equitable
2-partitions** / **perfect 2-colourings**, where the characterisation used above
-- `f` is a perfect 2-colouring iff `f - c` is an eigenfunction -- is standard,
and equitable 2-partitions of Hamming graphs (Cartesian powers of complete
graphs) with the second eigenvalue have their own literature. The separability
step is elementary and is very likely folklore.

**Nothing here is claimed as new mathematics.** What is new is that *this*
fabric is now classified, so the architectural question "is there a better
level-n shape" has a definite answer, and the answer is no.

## 15. Scope

**What this is.** Exact finite mathematics about one 40-vertex graph, plus an API
that reserves point sets in it.

**What this is not.** It reserves points of the level-1 graph. It does not do
link-state routing, congestion control, failure recovery, or placement across an
address hierarchy — those are separate and unbuilt. The placement-capacity
figures are sampled, not exhaustive, and say so. And the group computed here is
PSp(4,3); the full automorphism group of the collinearity graph is larger, so the
orbit sizes reported are PSp(4,3)-orbits and are labelled as such.
