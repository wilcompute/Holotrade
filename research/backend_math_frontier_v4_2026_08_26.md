# Backend Math Frontier v4 — 26 August 2026

This pass executes five requested backend-math continuations and three additional probes. Every statement below is classified as exact finite combinatorics, repository-certified computation, model, or open problem. No physical or quantum claim is inferred merely from matching counts or spectra.

## 1. The 36-spread graph is anti-Latin and exactly 8-chromatic

Let the vertices be the 36 symplectic spreads of `W(3,3)` and join two spreads when they share four isotropic lines. The repository reconstructs the graph directly from the 40-point/40-line carrier.

The graph has the strongly regular parameters

`SRG(36,15,6,6)`.

That is also the parameter set of a Latin-square graph of order six, but parameter coincidence is not isomorphism. `js/spread-obstruction.js` performs exact branch-and-bound clique searches and verifies explicit witnesses:

- clique number `omega = 4`;
- independence number `alpha = 5`;
- an explicit proper 8-coloring with class sizes `[5,5,5,5,5,5,4,2]`.

Since `ceil(36/5)=8`, the coloring closes

`chi = 8`.

A Latin-square graph of order six has six-cliques from rows, columns and symbols, so `omega=4` is already a decisive obstruction to that coordinatization.

Operational model: if four-line overlap is declared a scheduling conflict, eight conflict-free venue batches are necessary and sufficient. That sentence is a HoloTrade scheduling model; `chi=8` itself is exact graph theory.

## 2. Exact integer harmonic projectors and a 36-vector ETF

For adjacency matrix `A`, direct integer multiplication verifies

`A^2 = 9 I + 6 J`.

With Seidel matrix

`S = J - I - 2 A`, 

we obtain the exact quadratic relation

`S^2 + 2 S - 35 I = 0`.

Set

`H15 = 5 I - S`,  `H21 = 7 I + S`.

Then

`H15^2 = 12 H15`,
`H21^2 = 12 H21`,
`H15 H21 = 0`,
`H15 + H21 = 12 I`.

Thus `H15/12` and `H21/12` are complementary orthogonal projectors of ranks 15 and 21.

The additional split

`P1 = J/36`,
`P15 = H15/12`,
`P20 = H21/12 - J/36`

closes an exact `1 + 15 + 20 = 36` decomposition. The implementation avoids floating eigensolvers by putting all three projectors over the common denominator 36 and checking the projector, orthogonality, trace and resolution identities with integers.

Also, `H15/5` is a Gram matrix with diagonal 1 and every off-diagonal magnitude `1/5`; its square is `(12/5)` times itself. Hence it is an exact 36-vector equiangular tight frame in `R^15`, coherence `1/5`.

External cross-check: the graph/ETF literature records the `SRG(36,15,6,6)` connection and 36 equiangular lines in `R^15` at angle `1/5`. The repository proof does not depend on those references.

## 3. Tensor-product robustness: rigorous interval, exact value still open

The frozen SAT certificate `data/w33_blocking_sat.json` proves that the minimum point set hitting all 40 W33 lines is

`tau_1 = 11`.

At level two consider all 1,600 product placements `L x M`, one for each ordered pair of W33 lines. Every tile has 16 leaves.

For a blocker `X`, fix a first-coordinate line `L`. The second-coordinate shadow of `X` on `L x W` must hit every W33 line, and therefore has at least 11 points. Summing over the 40 choices of `L` gives at least 440 shadow incidences. Each failed leaf is counted in exactly four first-coordinate line shadows, because every W33 point lies on four lines. Therefore

`4 |X| >= 440`, hence `|X| >= 110`.

If `B` is the certified 11-point level-one blocker, `B x B` hits every product tile and has 121 leaves. Therefore

`110 <= tau_tensor,2 <= 121`.

**Update (2026-08-26): the upper bound falls to 115, and the product construction is proved non-optimal.**

Direct search over all `2^1600` subsets stalls, and the reason is symmetry rather than size: the problem's
stabiliser is `Aut(W33) wr C2`, of order `51840^2 * 2 = 5.4e9`, so a solver re-explores each candidate
billions of times. Restricting to blockers *invariant* under a cyclic subgroup collapses the 1,600 leaf
variables to one per orbit. For an element `g` of `Aut(W33)` and a power `h = g^t`, the twisted action
`(p,q) -> (g(p), h(q))` leaves a few hundred orbits, and CP-SAT returns an optimum in seconds.

The classes must be keyed by **cycle type**, not by element order -- that detail cost a result. Keying on
order collapses distinct conjugacy classes onto a single representative: the order-keyed sweep bottomed out
at 116 under an order-12 element, and a *second* order-6 class, invisible to that sweep, gives **115**.
Both witnesses are verified leaf-by-leaf against all 1,600 tiles and are minimal, in the sense that no
single leaf can be dropped:

`110 <= tau_tensor,2 <= 115`.

The method is one-sided and the asymmetry matters. A hit is a genuine upper bound on `tau_2`. A miss proves
nothing about `tau_2`, only about that symmetry class; and proving optimality *within* a class -- which
CP-SAT did here -- likewise says nothing about `tau_2`.

The structural consequence outweighs the six-leaf improvement. The earlier conditional theorem read:
`tau_2 = 121` **if** an optimal blocker's row support is a minimum line blocker (11 points). The 115 witness
has row support **37**, so that hypothesis is now known **false at the optimum**. `B x B` is not optimal, and
the product construction that produced the 121 figure in the first place is strictly beatable. The recursive
upper bound `11^n` inherits the same defect at every depth.

### Why the gap exists at all: the ovoid defect controls its width

Five attacks on the tight case failed. Rather than a sixth, ask where the interval comes from -- and the
answer is a one-line derivation that explains it completely.

For a generalized quadrangle of order `(s,t)`, the same shadow double-count gives
`tau_2 >= (st+1)*tau_1`, and `B x B` gives `tau_2 <= tau_1^2`. The width of that interval is

`tau_1^2 - (st+1)*tau_1 = tau_1 * (tau_1 - (st+1)) = tau_1 * delta`,

where `delta = tau_1 - (st+1)` is the **ovoid defect** -- how far the blocking number sits above the ovoid
size. A blocking set of size `st+1` is exactly an ovoid, so `delta = 0` **iff** the quadrangle has an ovoid,
and then the two bounds coincide:

> **An ovoid is SUFFICIENT for multiplicativity: `delta = 0` collapses the two bounds onto each other, so
> `tau_2 = tau_1^2`.**

The converse does **not** follow from the bound gap, and an earlier draft of this section claimed it did.
A positive defect *opens* an interval; it does not force `tau_2` to sit below the top of it, so "no ovoid"
alone does not give non-multiplicativity. W(3,3) *is* non-multiplicative, but that is established
separately, by the certified 115-leaf blocker beating `11^2 = 121` -- not by the width of the interval.

Two instances, both computed:

| | `(s,t)` | ovoid | `tau_1` | `delta` | lower | upper | `tau_2` |
|---|---|---|---|---|---|---|---|
| GQ(2,2) = W(3,2) | (2,2) | yes | 5 | 0 | 25 | 25 | **25, OPTIMAL** |
| W(3,3) | (3,3) | no (Thas) | 11 | 1 | 110 | 121 | **open in [110,115]** |

GQ(2,2) is solved exactly over its full 225-cell grid with no symmetry assumed: `tau_2 = tau_1^2 = 25`,
multiplicative, product optimal. W(3,3) has `delta = 1`, so the interval has width `11 * 1 = 11` -- precisely
the `[110, 121]` we began with.

**So the difficulty is not an artefact of the search. It is the missing ovoid, surfacing two levels above
where it was proved missing.** That also says what would close it: an argument converting the defect into a
statement about the product, not more search inside the interval it opens.

No literature on blocking numbers of *products* of generalized quadrangles turned up, but this is a one-line
consequence of two standard bounds, so it is recorded as a derivation that explains our interval rather than
as a discovery.

### One ovoid suffices -- and the dual product is exactly 110

Ten attacks on `tau_2(W(3,3))` failed. So stop attacking that object and compute its **neighbours**.

Running the shadow count over axis *i* of a product `Q1 x Q2` gives `tau >= (s_i t_i + 1) * tau_j`, and
`B1 x B2` gives `tau <= tau_1 * tau_2`. If `Q_i` has an ovoid then `tau_i = s_i t_i + 1` and that axis's
lower bound *is* the upper bound:

> **If EITHER factor has an ovoid, `tau(Q1 x Q2) = tau_1 * tau_2`. One ovoid suffices, not two.**

| product | ovoid? | lower | upper | `tau` |
|---|---|---|---|---|
| W(3,2) x W(3,2) | both | 25 | 25 | **25** |
| W(3,2) x W(3,3) | one | 55 | 55 | **55** |
| W(3,3) x Q(4,3) | one | 110 | 110 | **110** |
| W(3,3) x W(3,3) | **neither** | 110 | 121 | **open** |

**The third row is the point.** W(3,3) has no ovoid -- Thas, for odd `q` -- but it *does* have **spreads**:
36 of them, ten disjoint lines covering all forty points. A spread of W(3,3) is exactly an ovoid of the dual
`Q(4,3)`. So `Q(4,3)` has an ovoid, `tau(Q(4,3)) = 10`, and the theorem applies.

The two products then live on the **same 40x40 grid with 1600 tiles of 16 leaves**, differing only in which
tiles: `line x line` versus `line x pencil`. The answers are `[110,115]` open versus **110 exactly**, with an
explicit witness (11-point blocker x 10-line spread) verified leaf-by-leaf against all 1600 tiles.

Swapping one factor for its dual closes the problem outright, because duality converts "no ovoid" into "has
an ovoid". That is a precise measurement of what the defect costs: not a vague obstruction, but the
difference between an interval of width five and a closed value, on two problems of identical size and shape.

### A ceiling on convex relaxations

Before an eighth combinatorial attack, it is worth asking whether the other standard tool could work at all.
It cannot, and the answer is cheap.

`Aut(W33) x Aut(W33)` has three orbitals on point pairs, so nine on leaf pairs, and the Shor (Lasserre-1)
relaxation symmetrises down to **ten variables**. The product constraints collapse too, for a reason worth
naming: in a generalized quadrangle a point off a line is collinear with *exactly one* of its points, so the
relation-count vector from a point to a line's four points is `(1,3,0)` on the line and `(0,1,3)` off it --
two cases per coordinate.

The optimum is **exactly 100** -- the plain fractional bound `1600/16` that transitivity gives for free. The
SDP does not merely fail to beat the shadow bound of 110; it fails to *reach* it.

The reason is structural. The shadow argument is about **lines** -- four-point objects that a two-point
scheme cannot express. So no relaxation built on pairwise structure can prove `tau_2 >= 111`, however much
PSD machinery is stacked on it. Strengthening the cone at the two-point level is provably a dead end.

That leaves two honest routes: a formulation whose variables live at the level of lines, or a combinatorial
argument converting the ovoid defect directly into a statement about the product.

### Where the two bounds now stand

The upper bound has been attacked by four independent methods and the lower bound by five exact models:

| attack | outcome |
|---|---|
| symmetric CP-SAT over `Aut(W33)`, all 12 cycle-type classes, all twists | **115** |
| symmetric CP-SAT including the **transpose** (the full `Aut(W33) wr C2`), 39 variants | nothing below 115 |
| LNS, 40+ rounds freeing up to 680 leaves | no improvement |
| guided annealing at size 114, 12M+ moves | plateaus at 9 unblocked tiles of 1,600 |
| one-sided tight model | UNKNOWN, 1901 s |
| two-sided + degree identity | UNKNOWN, 1901 s |
| + sound 360-fold symmetry break | UNKNOWN, 2302 s |
| + centre excess-balance and proved support >= 24 | UNKNOWN, 2101 s |
| degree-sequence split | 41,672 sequences before timeout |

Supporting census: W(3,3) has exactly **40,055** independent sets -- 1, 40, 540, 3240, 9450, 13824, 10080,
2880 by size -- and `alpha = 7` against a Hoffman ratio bound of 10. Every fibre and co-fibre of a tight
blocker is drawn from that list.

Two different deficits are in play here and must not be conflated: the **blocking** ovoid defect
`delta = tau_1 - (st+1) = 11 - 10 = 1`, which is what sets the interval width, and the **coclique** deficit
`(st+1) - alpha = 10 - 7 = 3`, which is how far the largest partial ovoid falls short of a real one. Both
are symptoms of the same missing ovoid; they are not the same number.

### The centre of a minimum blocker -- and the citation that stops this being a discovery

All 360 minimum blocking sets of W(3,3) share one rigid structure. Each has a **centre**: a point `p`
whose four lines it meets *twice*, all other 36 lines *once*, and which it never contains. Relative to the
rank-3 shell `1 + 12 + 27` around `p` the blocker has shape `(0, 8, 3)` -- none of `p`, eight of the twelve
collinear points (two on each line through `p`), three of the twenty-seven others. There are 9 blockers per
centre and 40 centres: `360 = 40 x 9`, one `Aut(W(3,3))`-orbit, stabiliser 144.

The arithmetic closes cleanly: `sum_L |b cap L| = 4|b| = 44` over 40 lines each met at least once, so the
total excess is exactly `44 - 40 = 4` -- and it sits on a pencil rather than being spread around.

**This is almost certainly not new, and is recorded as verification rather than discovery.** Dualise:
W(3,3) is the dual of Q(4,3), so a blocking set is a *cover of Q(4,3) by lines*, and the statement becomes
"a minimum cover of Q(4,3) has excess 1, its four doubly-covered points form a line, and that line is not in
the cover." Covers of classical generalized quadrangles are a studied subject, and two published facts
bracket the whole thing:

- Eisfeld, Storme, Szonyi and Sziklai, *Covers and blocking sets of classical generalised quadrangles*,
  Discrete Mathematics **238** (2001) 35-51, prove a cover of `Q(4,q)` for odd `q` needs more than
  `q^2 + 1 + (q-1)/3` lines. At `q = 3` that is `> 10.67`, i.e. at least 11 -- **exactly the value this
  repository certifies by SAT.** `tau_1 = 11` is prior art; our certificate reproduces it and shows it is
  attained.
- The companion work on covers of `PG(3,q)` and of finite generalized quadrangles states that for minimal
  covers with small excess, "the structure of the set of points lying on at least two lines of the cover is
  described" -- which is precisely the excess structure above.

The `q = 3` statement could not be retrieved verbatim from open sources, and that uncertainty resolves one
way only: **a result whose novelty cannot be established is not new.** What remains ours is the depth-2
*tensor* blocking number -- a question about a product of two quadrangles, for which no literature turned up.

### Two proved facts about the tight case, and three things that did not work

Optimising the fibre-size program directly (`f(p) = |X_p|`, line sums exactly 11, `0 <= f <= alpha = 7`)
gives two facts CP-SAT reports as OPTIMAL:

- **the support is at least 24** on each axis, against a naive counting bound of `ceil(110/7) = 16` -- the
  geometry beats the counting by eight;
- **the largest fibre is at least 4**, so no tight solution is flat.

Three approaches did not work, and are recorded as such rather than quietly dropped:

| attempt | result |
|---|---|
| two-sided tight model, degree identity | UNKNOWN, 1901 s |
| the same, sound 360-fold symmetry break | UNKNOWN, 2302 s |
| split on degree sequences | 41,672 found before timeout; not a reduction |
| LNS from the 115 witness, 40+ rounds | no improvement; bounds the method, not `tau_2` |

The centre-excess balance -- the 40 chosen centres must meet every line exactly 4 times -- is *feasible*, so
it does not obstruct on its own. It is used as a propagation constraint instead.

The exact value inside `[110, 115]` remains open. This pass does not convert an unsuccessful optimization
search into a theorem: the lower bound is untouched, and `exactTau` stays `null` in the engine.

The same shadow count recursively gives

`11 * 10^(n-1) <= tau_tensor,n <= 11^n`,

and the upper half improves at **every** depth, because blocking numbers are **submultiplicative**:
if `X` blocks every depth-`a` tile and `Y` every depth-`b` tile then `X x Y` blocks every
depth-`(a+b)` tile, since a tile splits into its first `a` and last `b` factors and each half is met
independently. Hence `tau_(a+b) <= tau_a * tau_b`, and the best product packs in as many depth-2
factors as it can:

`tau_tensor,n <= 115^floor(n/2) * 11^(n mod 2)`.

| depth | lower | new upper | naive `11^n` |
|---|---|---|---|
| 2 | 110 | **115** | 121 |
| 3 | 1,100 | **1,265** | 1,331 |
| 4 | 11,000 | **13,225** | 14,641 |
| 5 | 110,000 | **145,475** | 161,051 |
| 6 | 1,100,000 | **1,520,875** | 1,771,561 |

The saving compounds as `(115/121)^(n/2)` -- about 14% by depth 6. The depth-3 witness (1,265 leaves)
is verified in the test suite against all 64,000 depth-3 tiles rather than asserted.

## 4. Equal-capacity recursive sharding experiment

A standard depth-two line lift uses `4*40 = 160` leaves. A tensor tile uses `4*4 = 16` leaves.

Take two W33 spreads. Each is ten disjoint lines partitioning the 40 points. Pair their ten lines by a permutation and take the union of the ten products. The result is ten disjoint 16-leaf tiles, exactly 160 leaves total, with full 40-point shadows on both coordinates.

This creates a fair equal-capacity combinatorial comparator between a monolithic lift and tensor sharding. Any later congestion, correlated-failure, or runtime result must be measured/modelled separately.

At depth `n`, the standard lift/tensor-tile capacity ratio is exactly `10^(n-1)`. The proved tensor blocking lower amplification over the level-one blocker is also `10^(n-1)`. `js/tensor-sharding.js` certifies both identities without interpreting them as a physical conservation law.

## 5. The 540 Q3 charts are exactly the 540 spread triangles

A W33 Q3 chart is an unordered pair of skew isotropic lines. Direct enumeration produces 540 charts.

For every chart `{l,m}`:

- exactly three of the 36 symplectic spreads contain both `l` and `m`;
- those three spreads pairwise share four lines, so they form a triangle in the spread graph.

The spread graph itself has exactly 540 triangles, and all 540 chart-derived triples are distinct. The two sets agree exactly:

`{540 skew-line Q3 charts} <-> {540 triangles of the 36-spread graph}`.

This also explains the incidence count

`540*3 = 36*45 = 1620`.

If `M` is the 540-by-36 chart/spread incidence matrix, exact counting gives

`M^T M = 45 I + 6 A`.

The eigenvalues of this Gram operator on the `1+15+20` spread decomposition are therefore `135`, `63`, and `27`, respectively. In particular `rank(M)=36`: the spread-function space injects into chart-function space.

### Negative result that matters

The tempting stronger conjecture that the 540-chart web adjacency preserves this 36-dimensional incidence image is false. `js/chart-spread-bridge.js` constructs the 6-regular chart web and gives an exact least-squares normal-equation solution together with an integer residual witness showing `B M != M C` for any exact coefficient matrix `C` on that image. The constants are invariant by regularity; the nontrivial 15- and 20-dimensional spread sectors are not jointly an invariant chart-web subspace.

The bijection is real. An adjacency intertwiner is not.

## 6. E8's unitary residues give exact elastic ladders with unavoidable holes

The W33 repository's unitary branch identifies the two small E8 residue carriers as

**E8 / 2E8 -> H(3,4) = GQ(4,2)**,

**E8 / 3E8 -> H(3,9) = GQ(9,3)**.

Before treating those identifications as scheduler objects, this repository now rebuilds the standard
Hermitian models independently in GAP. The witness enumerates all projective isotropic points and lines,
checks the point-graph SRG parameters, forms the graph in which two lines are adjacent exactly when they are
disjoint, and exhausts cliques at the candidate maximum and one beyond it.

For a generalized quadrangle GQ(s,t), order i mutually disjoint lines and let rung i be their union. The
quadrangle axiom gives

- vertices = (s+1)i;
- induced degree = s+i-1;
- internal edges = (s+1)i(s+i-1)/2;
- boundary = (s+1)i(st+1-i).

The last quantity equals the one-sided spectral minimum, so every rung is connected, regular, and
boundary-optimal. Prefixes are nested line atoms: expansion and shrink retain every common point and migrate
zero retained work.

| carrier | point graph | max partial spread | number of maxima | covered | holes | full spread would need |
|---|---|---:|---:|---:|---:|---:|
| H(3,4) | SRG(45,12,3,3) | 6 lines | 72 | 30 | 15 | 9 lines |
| H(3,9) | SRG(280,36,8,4) | 16 lines | 2,268 | 160 | 120 | 28 lines |

The residual sectors at those two ceilings are now classified exactly. The ambient automorphism group is
transitive on the maximum partial spreads in each case, so the following are isomorphism types rather than
features of one specially chosen witness.

| carrier | hole graph | spectrum | full hole-graph automorphism group |
|---|---|---|---:|
| H(3,4) | SRG(15,6,1,3) = KG(6,2) | 6^1, 1^9, (-3)^5 | S6, order 720 |
| H(3,9) | 120 vertices, degree 20, diameter 2; not SRG | 20^1, 8^5, 4^45, 0^9, (-4)^60 | (F2^6/<1>) : S6, order 23,040 |

For q=3 the equality of group orders with W(D6) is a trap, not an identification: the hole-graph group has
trivial centre while W(D6) has centre of order two. GAP instead proves that the group is
Aut(folded Q6). More strongly, the graph is the exact coset graph G/H for
H = SmallGroup(192,1485), with a unique embedding class of H in G and adjacency equal to the union of the
degree-16 and degree-4 orbitals. The ambient maximum-spread stabilizer has order 11,520 and structure
2^4:S6; it is index two in the full hole-graph automorphism group and must not be conflated with it.

The obvious geometric guess was kept as an executable negative result. The 120 point-duads (antipodal
square faces) of folded Q6 carry another transitive G-action, but its point stabilizer is
SmallGroup(192,1472) = S4 x D8. Its unique degree-20 two-orbital graph is not isomorphic to the H(3,9)
hole graph. Thus the symmetry bridge is exact while the natural-duad carrier is wrong; the result does not
rule out every possible Kummer interpretation and constructs no K3 surface.

The maxima are not new mathematics. De Beule, Klein, Metsch and Storme proved the bound
(q^3+q+2)/2 for partial spreads of H(3,q^2) and its sharpness at q=2,3 (Designs, Codes and
Cryptography 47 (2008), DOI 10.1007/s10623-007-9047-8). W33 Passes 7255-7256 had already recorded
that prior art and the values 6 and 16. The new HoloTrade synthesis is the ordered-prefix scheduler object,
its exact resize transaction plan, and the decision to expose the residual hole sector as a first-class
contract field.

analysis/e8_unitary_elastic_ladders.g owns the geometry; the canonical freezer records GAP 4.12.1 and
SHA-256 cce62c1c16927909a83be619e353df481eb01f95c6fe8831384b5d313fc92f74.
scheduler/e8-unitary-elastic-ladder.js verifies that digest before building a plan. Its output is
deliberately dispatchable=false: the GAP point numbers are not host IDs, and an inventory binding plus
runtime topology attestation is still required. The standard Hermitian carriers are incidence-isomorphic to
the W33-certified E8 residues, but this packet does not construct a literal E8-coordinate map.

The residual classification is owned by `analysis/e8_unitary_hole_sector_probe.g` and
`analysis/e8_unitary_kummer_duad_bridge.g`. Its canonical freezer is
`analysis/e8_unitary_hole_sectors.js`; the frozen JSON digest is
`f5e3a44ee4d1c24d354de532849cb07c89f5c7836f52e24ad056f472d655190e`.

# Three outside-the-box probes executed

### A. Split the 21-dimensional Seidel sector rather than stopping at the ETF

The ETF naturally exposes a rank-15 sector and its rank-21 complement. Removing the constant projector from the latter gives the exact rank-20 piece. This is the cleanest algebraic match to the spread SRG's `1+15+20` eigenspaces and gives rational/integer projectors suitable for backend certificates.

### B. Audit the optimal coloring structurally

The 8-color result was not accepted from a heuristic coloring alone. The code simultaneously proves `alpha=5`, verifies a 5-coclique, verifies the explicit 8-coloring, and records the exact color-class balance. The lower bound and upper witness therefore meet at eight.

### C. Turn the 540 count coincidence into an incidence theorem, then try to break it

The 540 chart / 540 triangle match was tested literally and closes as a bijection. The next natural strengthening—an adjacency intertwiner—was also tested literally and fails. Recording both results is more informative than preserving the attractive but false stronger conjecture.

# Evidence boundaries

- Exact: W33 carrier, 36 spreads, spread overlap graph, clique/coclique/coloring certificates, integer matrix identities, chart/triangle bijection, incidence Gram identity, tensor shadow lower bound, explicit tensor upper witness, GAP-rebuilt H(3,4)/H(3,9) carriers, their exhaustive maximum-partial-spread ladders, both maximum-spread orbit censuses, both hole graphs, and the q=3 folded-Q6 coset classification plus natural-duad no-go.
- Repository-certified: minimal level-one line blocker `tau_1=11` depends on the frozen SAT/UNSAT certificate already in the repository.
- Model: calling four-line overlap a compute-market conflict, pricing batches, congestion, runtime placement utility, failure correlation.
- Open: the exact depth-two product-transversal number inside `[110,115]` (narrowed from `[110,121]`; the upper bound is a construction, not a proof of optimality); representation-theoretic identification of chart-web eigenspaces; any physical or quantum realization of these scheduling coordinates.
