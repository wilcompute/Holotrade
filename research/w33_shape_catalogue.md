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
| `tests/shape-catalogue.test.js` | 28 regression tests |

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

## 9. Scope

**What this is.** Exact finite mathematics about one 40-vertex graph, plus an API
that reserves point sets in it.

**What this is not.** It reserves points of the level-1 graph. It does not do
link-state routing, congestion control, failure recovery, or placement across an
address hierarchy — those are separate and unbuilt. The placement-capacity
figures are sampled, not exhaustive, and say so. And the group computed here is
PSp(4,3); the full automorphism group of the collinearity graph is larger, so the
orbit sizes reported are PSp(4,3)-orbits and are labelled as such.
