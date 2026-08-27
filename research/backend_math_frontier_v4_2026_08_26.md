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

# Three outside-the-box probes executed

### A. Split the 21-dimensional Seidel sector rather than stopping at the ETF

The ETF naturally exposes a rank-15 sector and its rank-21 complement. Removing the constant projector from the latter gives the exact rank-20 piece. This is the cleanest algebraic match to the spread SRG's `1+15+20` eigenspaces and gives rational/integer projectors suitable for backend certificates.

### B. Audit the optimal coloring structurally

The 8-color result was not accepted from a heuristic coloring alone. The code simultaneously proves `alpha=5`, verifies a 5-coclique, verifies the explicit 8-coloring, and records the exact color-class balance. The lower bound and upper witness therefore meet at eight.

### C. Turn the 540 count coincidence into an incidence theorem, then try to break it

The 540 chart / 540 triangle match was tested literally and closes as a bijection. The next natural strengthening—an adjacency intertwiner—was also tested literally and fails. Recording both results is more informative than preserving the attractive but false stronger conjecture.

# Evidence boundaries

- Exact: W33 carrier, 36 spreads, spread overlap graph, clique/coclique/coloring certificates, integer matrix identities, chart/triangle bijection, incidence Gram identity, tensor shadow lower bound, explicit tensor upper witness.
- Repository-certified: minimal level-one line blocker `tau_1=11` depends on the frozen SAT/UNSAT certificate already in the repository.
- Model: calling four-line overlap a compute-market conflict, pricing batches, congestion, runtime placement utility, failure correlation.
- Open: the exact depth-two product-transversal number inside `[110,115]` (narrowed from `[110,121]`; the upper bound is a construction, not a proof of optimality); representation-theoretic identification of chart-web eigenspaces; any physical or quantum realization of these scheduling coordinates.
