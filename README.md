# HoloTrade

**Live: [wilcompute.github.io/Holotrade](https://wilcompute.github.io/Holotrade/)**  ·  [paper (PDF)](docs/holotrade.pdf)  ·  [shape catalogue](research/w33_shape_catalogue.md)

HoloTrade is a working research prototype for **topology-aware compute execution and settlement**. It connects a transparent quote to named capacity, a scoped execution plan, a hardware-checkable admission decision, per-second metering, and a receipt.

The core product idea is simple: do not sell an anonymous VM-hour. Quote the machine that will run the work, expose why it costs what it costs, reserve a bounded execution contract, and reconcile what was delivered.

```text
inventory → quote → depth/impact → plan → admit → execute → meter → receipt
                         ↘ topology-aware placement ↗
```

This repository is intentionally honest about maturity. It contains exact finite mathematics, exhaustive formal checks, deterministic simulation, and prototype software. It does **not** yet contain a production exchange, remote attestation, multi-node reservation ledger, physical Holonet, or deployed quantum hardware.

## Run the demo

```bash
npm run serve
# open http://127.0.0.1:8080
```

The site has no frontend build step and no runtime package dependencies. It starts from a deterministic seed, so reloading restores the same fleet and market. Use [DEMO.md](DEMO.md) for a short live walkthrough.

For a pre-demo check:

```bash
npm test
npm run verify:rtl
npm run synth:rtl
npm run verify:e8-backend
npm run experiment:balancer
npm run paper
```

## What is strongest today

### 1. A quote the buyer can inspect

Each node quote decomposes as

\[
P=P_0\,E\,G\,D\,H\,Q\,L,
\]

where the terms represent modeled energy, learned specialization, demand balancing, health, declared workload capability, and locality. The UI shows every factor, the operating floor, available depth, expected fill, VWAP, slippage, and the price/throughput Pareto frontier.

The quote is an **hourly-equivalent comparison rate**. Execution settles in node-seconds. Those are deliberately different concepts: the first makes heterogeneous offers comparable; the second is the delivered unit.

### 2. A complete single-node execution loop

The prototype can:

- create a content-bound plan with artifacts, grants, a nonce, validity window, price cap, locality anchor, duration, and workload class;
- rank named nodes by total modeled cost;
- refuse unsupported or invalid work with a specific reason;
- launch one simulated microVM;
- recheck the live price cap while running;
- clip the final meter interval so it never over-delivers or over-bills;
- emit a reconciled receipt and verify every body and link in the checksum chain.

The current plan envelope is explicitly `DEMO_INTEGRITY_SEAL`: an unkeyed deterministic checksum for exercising lifecycle semantics. It is **not** a digital signature or remote attestation. Multi-node requests are refused until gang reservation and delivery exist, instead of multiplying one VM's bill and pretending several nodes ran.

### 3. A topology-aware capacity model

The level-1 substrate is the collinearity graph of \(W(3,3)\):

| Exact invariant | Value |
|---|---:|
| points / totally isotropic lines | 40 / 40 |
| degree | 12 |
| edges | 240 |
| strongly regular parameters | SRG(40,12,2,4) |
| diameter | 2 |
| full automorphism-group order | 51,840 |
| exact balanced bisection | 100 |

The bisection result is not just a formula in prose. `Substrate.BISECTION_LEFT` is an explicit 20-point cut with 100 crossing edges, and the spectral lower bound is also 100. Tests verify both sides of the certificate.

For **partial** baskets, HoloTrade reports induced edges, connected components, minimum induced degree, and induced diameter. The historical 0–100 number is retained only as a clearly named normalized induced-edge coherence proxy; it is not called measured bisection bandwidth. A two-node basket cannot inherit a two-hop route through a relay it does not own.

Direct adjacency is derived from the symplectic form on the addresses. The software finds a relay by a bounded scan of the 40 points. Congestion control, failed-link routing, and physical forwarding remain unbuilt.

### 4. A reproducible balancing result

The two-sided demand policy discounts cold capacity and prices hot capacity above it. In the frozen, paired simulation packet:

| 64 paired seeds, 220 nodes, 500 one-minute steps | terminal utilization Gini |
|---|---:|
| balancer on | 0.06458, 95% CI [0.06043, 0.06874] |
| balancer off | 0.16110, 95% CI [0.15455, 0.16764] |
| paired relative reduction | **60.34%**, 95% CI [58.90%, 61.77%] |

All 64 paired seeds improved. This is evidence about this simulator and policy, not a production utilization measurement and not proof of longer hardware life. Regenerate it with:

```bash
node experiments/balancer_ab.js --summary
```

The frozen summary and row digest are in [data/balancer_ab_64.json](data/balancer_ab_64.json).

### 5. A formally checked admission circuit

`rtl/holotrade_admit.v` implements the form, adjacency predicate, migration-ray output, canonical-address validation, and seven-way admission/refusal policy.

The formal miter compares the complete implementation with an independently written behavioral reference over all \(2^{25}=33,554,432\) input assignments. It covers every output, illegal trits, the zero vector, noncanonical projective representatives, refusal priority, admission, form, adjacency, and ray cost.

Current iCE40 synthesis reports:

```text
49 × SB_LUT4
 6 × SB_CARRY
```

That is synthesis evidence only. No place-and-route timing or deployable board integration is claimed. The `sig_ok` input is a policy predicate; the RTL does not implement Ed25519 or verify a software artifact.

## Evidence labels

HoloTrade uses scope labels because “working” means different things at different layers.

| Label | What it means here |
|---|---|
| **THEOREM / EXACT** | finite statement with a reproducible certificate or exhaustive enumeration |
| **FORMAL** | equivalence or safety property checked over the complete declared input space |
| **SYNTHESIZED** | technology mapping and cell count; no timing claim |
| **REGRESSION** | executable software invariant tested in CI |
| **SIMULATION** | deterministic modeled behavior, not field telemetry |
| **PROTOTYPE** | end-to-end interaction exists but production trust/operations do not |
| **DESIGN SKETCH** | interface or market concept whose state machine is not built yet |

This distinction is load-bearing. A graph theorem is not a network SLA; a checksum is not a signature; a synthetic contextual sample is not attestation; a model coefficient is not a market measurement.

## What the website demonstrates

- **Exchange:** typed compute quotes, order-book depth, execution impact, slippage, and Pareto-efficient offers.
- **Balance:** live two-sided policy behavior with a separately reproducible paired experiment.
- **Fabric:** exact \(W(3,3)\) graph exploration, the bisection certificate, induced-basket connectivity, composition, and mutually beneficial defragmentation proposals.
- **Execution:** plan creation, named placement, explicit refusal, deterministic boot estimate, node-second metering, price-cap halt, and checksum-chain verification.
- **Fleet / Energy / Genetics:** the modeled state that feeds the quote, with seeded provenance and specialization.
- **Evidence:** a visible boundary between exact, formal, synthesized, simulated, prototype, and unbuilt claims.

Fill-time market receipts are marked `SIMULATED_QUOTE_RECEIPT`. They bind the quote and provenance shown in the demo but do not claim a workload ran. Execution receipts are the separate delivery surface.

## Recursive and research layers

An \(n\)-digit address namespace contains \(40^n\) leaves. Under the current software descent metric, equal-depth addresses have upper bound

\[
d_n=2+16(n-1)=16n-14.
\]

That bound now agrees with `fabricDistance` and has explicit witnesses in the tests. It remains a **recursive address model**, not the diameter of a constructed physical product graph.

Likewise, \(9^t\) is an illustrative declared-workload cost model. Gottesman–Knill establishes efficient classical simulation for stabilizer circuits; it does not make memory, routing, error correction, or all Clifford computation free, and it does not make \(9^t\) a universal runtime law.

### Elastic topology ladders: one complete, two partial

Ordering the ten disjoint lines of any \(W(3,3)\) spread gives a nested reservation ladder. Rung \(i\)
contains \(4i\) points, has induced degree \(i+2\), \(2i(i+2)\) internal edges, and boundary
\(4i(10-i)\). Every rung meets the spectral minimum boundary exactly. Expanding or shrinking by a whole
four-point line leaves every retained point in place, and rung 10 closes the entire 40-point carrier.

The same construction now runs on the two unitary residue geometries identified on the W33/E8 track.
GAP 4.12.1 independently rebuilds both Hermitian generalized quadrangles, exhausts their line-disjointness
graphs, and freezes these ceilings:

| carrier | maximum line atoms | ladder sizes | covered | unavoidable holes | maximum witnesses |
|---|---:|---:|---:|---:|---:|
| \(H(3,4)=GQ(4,2)\) | 6 | 5, 10, …, 30 | 30 / 45 | 15 | 72 |
| \(H(3,9)=GQ(9,3)\) | 16 | 10, 20, …, 160 | 160 / 280 | 120 | 2,268 |

These two ladders are provably **partial**: a full spread would require 9 and 28 lines, while exhaustive
search rules out even 7 and 17. The runtime therefore exposes the hole sector instead of silently treating
the final rung as full coverage. `scheduler/e8-unitary-elastic-ladder.js` verifies the frozen SHA-256 and
emits zero-migration resize plans, but its topology plans remain `dispatchable: false` until abstract point
IDs are bound to real hosts and independently topology-attested. The standard Hermitian models are
incidence-isomorphic to the certified E8 residues; a literal E8-coordinate isomorphism is not claimed here.

The maximum-rung boundary is now classified rather than merely counted. All maximum partial spreads lie
in one ambient orbit, so each carrier has one hole-graph isomorphism type. For \(q=2\), the 15 holes induce

\[
\operatorname{SRG}(15,6,1,3)\cong KG(6,2),
\]

with automorphism group \(S_6\). For \(q=3\), the 120 holes form a 20-regular diameter-two graph with
spectrum \(20^1,8^5,4^{45},0^9,(-4)^{60}\). It is not strongly regular. GAP identifies its full
automorphism group as

\[
G\cong (\mathbb F_2^6/\langle\mathbf1\rangle)\rtimes S_6
   =\operatorname{Aut}(\text{folded }Q_6),
\]

and the graph itself as the coset action \(G/H\), where \(H=\operatorname{SmallGroup}(192,1485)\), with
adjacency the union of the degree-16 and degree-4 orbitals. The obvious 120-duad folded-cube carrier was
also tested and rejected: it has stabilizer `SmallGroup(192,1472)` and its degree-20 graph is not
isomorphic to the hole graph. This is an exact finite graph/group result, not a folded-cube hardware claim
or a K3-surface construction.

### The E8 / W33 backend packet

The residual graph is now compiled, factored, and connected back to the \(q=2\) carrier rather than merely
classified. Every item below has a GAP-owned witness, a frozen SHA-256 certificate, and focused regression
tests; the hardware rows have additional Yosys SAT proofs.

| Front | Exact result | Boundary retained |
|---|---|---|
| Fano control codec | \(\mathrm{GL}(3,2)=(C_7{:}C_3)D_8\), a unique \(21\times8=168\) Zappa--Szép address chart; all 28,224 products and 4,741,632 associativity triples checked | abstract bus IDs, not machines; multiplication is matched-action, not coordinatewise |
| orientation / rollback | \(2^4{:}S_6\triangleleft 2^5{:}S_6\) gives a relative \(C_2\) character and 1,134 unlabelled pairs of maximum spreads | no canonical 0/1 label and no canonical rollback: 376 outer involutions form five classes |
| hole-graph RTL | the exact 120-state degree-20 graph is implemented both by a 1,920-bit \(GF(9)\) coordinate predicate and a 14,400-bit row ROM | Yosys proves equality on all \(2^{14}\) address pairs; synthesis is not timing or deployment evidence |
| branchwise normalizer adapter | over \(C_{13}{:}C_3\), both sides stabilize at dimension 4,200; over \(D_{26}=C_{13}{:}C_2\), \(F_2[V_2]\oplus J_2^{32}\cong H_1\oplus J_1^{64}\) at dimension 4,160 | the natural \(\mathbb F_4^3\) translation pairing is killed by \(C_{13}\)-equivariance |
| cross-prime fibre | the \(2\)-core partitions the 120 states into fifteen \(F_2^3\) fibres of size eight; each fibre is \(K_{4,4}\), while the cross-only connector over an intersecting-duad edge is exactly \(4C_4\) | the two-fibre induced union is connected and 6-regular; the old `C16` label confused component size with graph type and is retracted |
| full normalizer closure | one 64-dimensional correction pair assembles the restrictions into an abstract \(F_2[C_{13}{:}C_6]\)-module isomorphism at dimension 4,160 | no direct 4,096-dimensional bridge and no 4,160-dimensional chain map; dispatch remains refused |
| canonical fibre partition | the fifteen fibres are exactly the orbits of \(O_2(2^5{:}S_6)\), so the unlabelled \(15\times8\) partition is invariant under the full graph automorphism group | block names and within-fibre slot labels remain gauge choices; no inventory binding follows |
| affine relation compiler | sixty \(T(6)\) edges use thirteen codimension-two affine relation types; each cross relation is the union of two parallel permutation channels | 171 LUT4s versus 720 for the general predicate in the same flow; this is a multichannel relation lift, not a regular one-voltage cover |
| reversible dilation | \(U(x,y)=(x+Ay,y)\) is a 240-bit symplectic involution with 2,400 CNOTs in optimal depth 20 | exact logical circuit and exhaustive RTL identity, not a quantum-device or routing-performance claim |
| recursive control chart | \(21\times8\times15\times8=20{,}160\) bijective logical states; Goursat forces every surjective coupling of the 168- and 120-state actions to be their direct product | the equality \(20{,}160=|A_8|\) is quarantined; these are not \(A_8\) elements, hosts, or dispatchable microVMs |
| 85-state polarity / sentinel weld | one \(40\times45\) matrix satisfies \(BB^T=8I+2A_{W33}+J\) and \(B^TB=8I+2A_{\overline{GQ(4,2)}}\); restoring absolute loops gives \(H^2=16I+5J\), while the columns are exactly the 45 minima of \([40,15,8]_2\) and have 216 five-circuits | only 5 of its 35 chiral zero modes are index-protected under arbitrary off-diagonal perturbation; the design/code are classical, not physical E8 hardware, cryptographic integrity, or a qutrit-Clifford torsor |
| adjacency homology / CSS code | \(A^2=0\) over \(F_2\), with \(\operatorname{im}A=[120,40,16]_2\), \(\ker A=[120,80,8]_2\), and the exact CSS code \([[120,40,8]]_2\) | a classical stabilizer-code theorem; no decoder, noise model, physical qubits, or hardware performance is supplied |
| universal W33 shadow | every equivariant map from the 40-dimensional logical homology to a genuine 40-point W33 carrier factors through 15 coinvariants and lands in the explicit \([40,15,8]_2\) sentinel; the reverse maps land in 15 fixed dimensions | the universal image spans have dimensions 11 or 6 under the two \(S_6\) identifications; there is no isomorphic relabeling or preferred nonzero map |
| bicolour circuit split | exact rational ranks are \(216,216,372\), so the common colour space is \(60=1+15+20+24\); both colours transport the canonical circuit carrier to the same \(45=1+20+24\) subspace | this repairs a modular-rank over-read and leaves the diagonal 15 as the exact residual; no optical or hardware mode is inferred |
| router / engine Goursat closure | a connected W33 router is forced independent of the 20,160-state engine, giving \(40\times20{,}160=806{,}400\) local logical states; the full router admits exactly three additional \(C_2\) fibre products | the three parity pullbacks are exact but noncanonical, so no recursive parity policy, host identity, or dispatch authority is selected |
| the two 216s separated | the 216 five-circuits and 216 hemisystem complement-pairs are distinct transitive \(PSp(4,3)\)-sets and remain distinct under the full order-51,840 automorphism group; the circuit carrier contains Steinberg-81 once, the hemisystem carrier zero times | equal cardinality is not an equivariant dictionary; 11 permutation-character discrepancies make the no-go explicit |
| common quotient and carrier fork | both 216-state carriers fibre canonically six-to-one over the same 36 regular spreads, with the two nonconjugate \(S_5<S_6\) fibre types | the exceptional outer automorphism of abstract \(S_6\) is not realized by a substrate automorphism, so this is a fork rather than a gauge choice |
| fibre-product building bridge | the canonical \(1{,}296=36\cdot6\cdot6\) carrier has stabilizer \(F_{20}=C_5{:}C_4\) and building block \(3\cdot81+3\cdot64=435\), exactly matching the corrected 1,080 obstruction carrier; the cross-Hom dimension is 18 | semisimplicity gives an abstract isotypic isomorphism; the explicit \(1{,}296\times1{,}080\) intertwiner remains unbuilt |
| dual-carrier RTL router | both native generator actions preserve the same 36-state type quotient; cross-carrier adaptation returns only that quotient | Yosys proves all valid carrier/opcode/state inputs and rejects a fabricated-state control; this is finite combinational logic, not a processor or fabricated device |
| \(F_{20}\) protected-qutrit control | bare permutations of the cyclic \([[5,1,3]]_3\) block give only \(D_{10}\); local \(SL(2,3)\) Clifford compensation restores \(F_{20}\), with an explicit generator map satisfying \(T^5=M^4=1\) and \(MTM^{-1}=T^3\) | the faithful 40-address Pauli controller is Yosys-proved, but this is a code automorphism—not a router-state/codeword identification, local 20-to-240 embedding, threshold, or fault-tolerant recode |
| \(F_{20}\) Payne five-state atlas | the five protected sites map uniquely to the fibre \(F_{20}\)'s five-target slow circuit; separately, a ROM line has inner image \(A_5\), full \(W(E_6)\) image \(S_5\), and a line-preserving \(F_{20}\) whose inner intersection is exactly \(D_{10}\) | among 16,000 presentation-compatible address/site maps, 9,600 match zero incidences and 6,400 match exactly four of eight at every site; perfect welding never occurs, while production Payne staging repairs the frozen gauge in exactly one W33-axis hop per address |

The cross-prime quotient is especially rigid. If \(Q\) counts neighbours from one eight-state fibre into
another, then

\[
Q=4I+2A(T(6)).
\]

The off-diagonal zero relation is exactly \(KG(6,2)\), the \(q=2\) hole graph. Consequently the quotient
spectrum is \(20^1,8^5,0^9\), and the rational nine-dimensional zero eigenspace of the \(q=3\) graph is the
lift of the \(+1\) eigenspace of \(KG(6,2)\).

The 40- and 45-state carriers also close into one exact 85-state control plane. The cross-incidence matrix
has rational rank 25 and chiral kernel split \(15+20\). Adding the 45 absolute-point polarity loops produces
the symmetric \(2-(85,21,5)\) design with spectrum \(21^1,4^{45},(-4)^{39}\). Over \(F_2\), the same 45
columns generate the doubly-even self-orthogonal \([40,15,8]\) sentinel and are exactly all its minimum
words. The scheduler exposes each eight-point support, each 21-entry polarity row, and every one of the 216
five-word zero-parity circuits, all non-dispatchable. The exact operator has 35 zero modes, but rectangular
chiral index protects only 5: the witness gives an explicit off-diagonal perturbation that raises \(B\) to rank
40 and removes the other 30. This is a finite stability boundary, not evidence for a physical flat band.

There is a second, characteristic-two descent. Reducing the 120-by-120 adjacency matrix \(A\) modulo two gives

\[
A^2=0,\qquad \operatorname{rank}A=40,\qquad
\dim\ker A=80,\qquad \dim(\ker A/\operatorname{im}A)=40.
\]

Thus \(0\subset\operatorname{im}A\subset\ker A\subset F_2^{120}\) has associated graded dimensions
\(40\mid40\mid40\). `scheduler/e8-unitary-fibre-switch.js` executes this exact parity transform and verifies
that a second application vanishes. The code layer is now exact:
\(\operatorname{im}A=[120,40,16]_2\), \(\ker A=[120,80,8]_2\), and using the same image basis for the two
checks gives \([[120,40,8]]_2\). The 435 kernel words of weight eight are nontrivial logical classes because
the image distance is 16.

The tempting 40-to-40 identification is nevertheless false. GAP tests both \(S_6\) identification classes:
the logical homology is not the W33 point module. What survives universally is smaller and sharper. Every
equivariant forward map kills the \(C_2^5\)-relations, factors through a 15-dimensional coinvariant, and lands
inside the explicit \([40,15,8]_2\) sentinel. The span of all such images has dimension 11 in the inner class
and 6 in the outer class; every reverse map lands in the corresponding 15-dimensional fixed homology.

On the 216-circuit shell, the two maximal-overlap colours now have exact characteristic-zero stacked rank
372, not merely a modular lower bound. Their common 60-space splits concretely as

\[
  \operatorname{circuit}_{45}^{+}
  =\operatorname{circuit}_{45}^{-}
  =\operatorname{circuit}_{45}=1\oplus20\oplus24,
  \qquad
  \operatorname{common}_{60}
  =\operatorname{circuit}_{45}\oplus\operatorname{diagonal}_{15}.
\]

One similarly sized object must remain separate: the 216 circuit states are not the 216 projective
hemisystem lines. Their order-120 stabilizers are nonconjugate in \(PSp(4,3)\), their order-240 extensions
remain nonconjugate in \(\operatorname{Aut}(W(3,3))\), and their full permutation characters differ on eleven
classes. The most visible witnesses are involutions fixing \(48\) versus \(0\), and \(6\) versus \(66\), states.
The irreducible decomposition gives the conceptual separator: the circuit
permutation module contains the 81-dimensional Steinberg representation once,
whereas the hemisystem-line module contains it zero times.

The separation has now been turned into a usable architecture.  Both carriers
map six-to-one onto the same 36-spread base, but no automorphism of the substrate
exchanges their two \(S_5\) fibre types.  A single state therefore cannot be
retyped across the fork.  The canonical alternative is the fibre product over
the shared base: 1,296 paired states with stabilizer \(F_{20}\).  Exact GAP
character calculations show that it contains three copies of each building
homology, \(H_1(W(3,3))\) of dimension 81 and \(H_1(GQ(4,2))\) of dimension
64.  That \(435\)-dimensional sum exactly matches the true
27-completion-chart by 40-line obstruction carrier.  Using points in the
second factor gives multiplicity four rather than three and is now explicitly
quarantined as a different action.

W33-Theory already supplies the typed software IPC and neutral checkpoint
semantics over this base.  The generated RTL here implements both exact
generator pairs without inventing a
cross-carrier bijection. Same-carrier opcodes return a native 216-state
transition; an adapter request exposes only the common 36-state quotient. The
positive Yosys proof covers the complete declared input space, and a negative
control that fabricates a cross-state produces a counterexample.

The fibre stabilizer is now more than scheduler metadata. On the cyclic
five-qutrit block, bare coordinate permutations realize only the dihedral
subgroup \(D_{10}\). The missing affine multiplier is recovered by applying the
same determinant-one local qutrit Clifford on all five sites together with an
explicit stabilizer-row change. GAP then gives a presentation-matched
isomorphism from the router stabilizer to these physical Pauli-space code
automorphisms. The resulting faithful action on five sites times eight
nonidentity one-qutrit Paulis is compiled into a 40-address RTL controller;
Yosys proves closure and the full \(F_{20}\) presentation, while a controller
with the Clifford compensation removed fails. This is a native protected
control plane for a block, not a claim that the 1,296 router states are
codewords.

That control group now has an object-level address on the new Payne slow path.
Inside \(PSp(4,3)\), the fibre \(F_{20}\) has slow-target orbits
\(5+10+10+20\). Its unique five-orbit is a coclique with full \(S_5\)
set-stabilizer; its \(PSp(4,3)\)-orbit has size 216, so it is precisely one of
the existing five-target circuit states. For the fixed generator map, the five
qutrit sites have one and only one equivariant bijection to that circuit.

A five-entry ROM bank is the complementary five-state realization. Its
stabilizer maps to \(A_5\) inside \(PSp(4,3)\), but to \(S_5\) in the full
order-51,840 \(W(E_6)\) action. GAP finds one conjugacy class of line-preserving
\(F_{20}\) complements, and its intersection with the inner group is exactly
\(D_{10}\). Thus the same generator-level chain
\(D_{10}<F_{20}\) appears as bare versus Clifford-compensated code control and
as inner versus outer ROM-line symmetry. This is a group-pair isomorphism, not
an assertion that a local Clifford gate physically implements a Weyl-group
motion.

The 40 addressed one-site Paulis and the 40 W33/Payne axes each split as two
regular \(F_{20}\)-orbits. There are exactly 800 equivariant bijections; the
certificate freezes a reproducible lexicographic choice, and the fail-closed
`F20PayneCodec` thereby assigns every Pauli address a nine-target Payne cover
while retaining the gauge choice and `dispatchable: false` boundary. The tempting stronger weld is
false: after varying all 20 presentation-compatible \(F_{20}\) isomorphisms and
all 16,000 induced address/site maps, none sends each site's eight Pauli labels
onto the eight covers containing its matched circuit target. The subgroup
bridge is real, but \(F_{20}\) alone does not determine the full incidence
codec. GAP sharpens this from a zero count to a complete defect spectrum:
9,600 candidates match no address at any site, while 6,400 match exactly four
of eight at every site. Thus the best possible equivariant gauge is uniformly
half-incidence, never an uneven near miss. Composing the frozen gauge with the
separately proved production Payne staging rule repairs all 40 misses in
exactly one W33-axis hop. The repair is deterministic and certificate-checked,
but it breaks the direct equivariant weld and remains `dispatchable: false`.

### The instruction-cost exception has a geometric address

The current all-transvection Cayley metric uses all 80 nontrivial symplectic
transvections in \(Sp(4,3)\), i.e. both scalar classes. Exhaustive enumeration
shows that length exceeds \(\operatorname{rank}(g-I)\) exactly when \(g\) acts
as \(-1\) on a nonzero nondegenerate subspace and as \(+1\) on its orthogonal
complement. In dimension four this gives 90 hyperbolic-line reflections plus
the central \(-I\): all 91 anomalies from one rule. Each hyperbolic line has
15 residue-two elements, but only its distinguished reflection is expensive;
the earlier “all hyperbolic elements are expensive” reading is retracted. The
rule fails at \(q=2\), where \(-1=+1\).

This sits beside, rather than superseding, Ellers's exact classification of
\(\lambda\)-length using transvections from one fixed conjugacy class in
\(Sp(2n,3)\). Our 80-generator, two-class word metric is different, but that
paper is direct prior art and is now cited explicitly: [E. W. Ellers, *Linear
Algebra and its Applications* 202 (1994), 1–23](https://doi.org/10.1016/0024-3795(94)90181-3).

The general coordinate predicate uses 544 iCE40 LUT4s versus 1,174 for the independent row ROM. The
affine relation compiler cuts the same logical-address decision to 171 LUT4s versus 720 for that general
predicate under the same no-ABC flow. Its separate reversible lift uses 2,400 CNOTs in an exactly optimal
20-layer schedule.
Reproduce the complete packet with:

```bash
npm run verify:e8-backend
npm run verify:e8-hardware
npm run verify:w33-f20-qutrit
npm run verify:w33-f20-payne
```

The upper bound \((q^3+q+2)/2\), sharp at \(q=2,3\), is published finite-geometry prior art; the contribution
here is its executable, evidence-bounded scheduler lift. Recompute the certificate with:

```bash
npm run verify:unitary-ladders
npm run verify:unitary-holes
```

### Tensor placement robustness, and one open interval

A depth-2 tensor tile is \(L\times M\) for two W(3,3) lines: 16 leaves in the \(40\times40\) fabric. The
relevant quantity is \(\tau_2\), the fewest leaf failures that can leave **no** intact tile anywhere. Fewer
than \(\tau_2\) failures always leave some tile whole, so \(\tau_2-1\) is a hard survivability floor.

Shadow double-counting first gives \(\tau_2\ge110\), and the obvious construction \(B\times B\) from an 11-point
line blocker gives 121. The gap resisted direct search: CP-SAT over all \(2^{1600}\) subsets reproduced
exactly those endpoints and then stalled, because the problem's stabiliser \(\mathrm{Aut}(W_{33})\wr C_2\)
has order \(51840^2\cdot2\approx5.4\times10^9\) and the solver re-explores every candidate billions of times.

Searching only blockers **invariant** under a cyclic subgroup collapses the 1,600 leaf variables to one per
orbit, and CP-SAT then answers in seconds. That gives an explicit 115-leaf blocker — verified leaf-by-leaf
against all 1,600 tiles, and minimal in the sense that no single leaf can be dropped. Blocking numbers are
submultiplicative, so the improvement propagates: \(\tau_n\le115^{\lfloor n/2\rfloor}\cdot11^{n\bmod2}\),
beating \(11^n\) at every \(n\ge2\). The depth-3 witness is verified against all 64,000 depth-3 tiles.

The structural consequence matters more than the six leaves: the witness has row support 37, not 11, so
\(B\times B\) is **not** optimal and the product construction behind the 121 figure is strictly beatable.

The tight value 110 is now excluded by the exact self-duality obstruction, so **\(\tau_2\) is open in
\([111,115]\)**. The result removes one endpoint; it does not determine the remaining value. The 111 case has
an exact PG\((3,4)\)-labelled partial-duality reduction, while the surviving 112--115 interval retains the
explicit 115-leaf upper witness. `exactTau` therefore remains `null`, and the tests pin both the sharpened
lower endpoint and the unresolved boundary.

The earlier truncated external E8 JSON remains intentionally unimported. The unitary ladder above is instead
owned by a complete local GAP witness, a canonical frozen certificate, and a deterministic replay test.

## Product boundary

The most credible path is an **attested compute broker and reconciliation layer**:

1. normalize inventory, telemetry, and quotes;
2. reserve a named capacity/SLO bundle;
3. sign a canonical execution contract;
4. run and meter it;
5. bind evidence, output, invoice, and settlement into one receipt;
6. optimize placement and defragmentation using measured topology;
7. add forward/option semantics only after delivery windows, collateral, exercise, and default are implemented.

The spot interaction is a prototype. Forward, option, lease, and supply screens are research/design surfaces, not a claim that a regulated venue or complete derivatives engine already exists.

## Repository map

```text
holotrade.html              application shell and evidence labels
index.html                  redirect stub so the Pages root still works
css/styles.css              responsive visual system
data/catalog.js             deterministic demo inventory
data/balancer_ab_64.json    frozen paired simulation summary
experiments/                reproducible modeled experiments
js/substrate.js             exact level-1 geometry and address metric
js/pricing.js               quote factors, floor, balancing policy
js/market.js                depth, impact, matching simulation, quote receipts
js/fabric.js                induced topology, coherence, swaps, composition
js/execution.js             plan, admission, meter, delivery receipt, chain
js/fleet.js                 hardware, health, utilization, provenance
js/energy.js                simulated grid/carbon process
js/genetics.js              specialization and lineage model
js/uor.js                   64-bit object-reference codec and policy scores
js/app.js                   browser orchestration and chart rendering
scheduler/e8-unitary-elastic-ladder.js  fail-closed H(3,4)/H(3,9) topology plans
scheduler/e8-normalizer-stable-adapter.js branchwise stable plans plus exact full-normalizer handoff
scheduler/e8-full-normalizer-stable-closure.js abstract 4,160-state module plan, chain-level refusal
scheduler/e8-unitary-fibre-switch.js     executable 15x8 chart and square-zero parity switch
scheduler/e8_unitary_voltage_lift.js     thirteen-type affine relation compiler
scheduler/e8-unitary-reversible-dilation.js reversible 240-bit logical transform
scheduler/e8-fractal-microvm-fabric.js   bijective 20,160-state logical address chart
scheduler/e8-pg34-sentinel-control-plane.js 85-state polarity and binary parity plans
analysis/e8_fano_zappa_szep_codec.g      exact 168-state Fano matched-action codec
analysis/e8_normalizer_stable_adapter.g  C13:C3 and D26 stable module arithmetic
analysis/e8_full_normalizer_stable_closure.g full C13:C6 indecomposable closure
analysis/e8_unitary_orientation_rollback_probe.g relative orientation and rollback no-go
analysis/e8_unitary_hole_coset_rtl.g     GAP transport from 120 cosets to GF(9) coordinates
analysis/e8_unitary_crossprime_fibre_differential.g q3-to-q2 quotient and rank-40 differential
analysis/e8_unitary_canonical_fibre_partition.g intrinsic O2 orbit partition
analysis/e8_unitary_voltage_lift.g       affine channel census and 4C4 correction
analysis/e8_unitary_reversible_dilation.g symplectic involution and optimal CNOT layers
analysis/e8_fractal_microvm_fabric.g     Goursat direct-product certificate
analysis/e8_pg34_sentinel_control_plane.g polarity, sentinel, shell and PSp/S5 witness
analysis/e8_unitary_elastic_ladders.g   GAP reconstruction and exhaustive maxima
data/e8_unitary_elastic_ladders.json    canonical unitary-ladder certificate
analysis/e8_unitary_hole_sector_probe.g GAP hole graphs, spectra, groups and spread orbits
analysis/e8_unitary_kummer_duad_bridge.g exact folded-Q6 coset model and duad no-go
analysis/e8_unitary_hole_sectors.js     canonical GAP/GRAPE hole-sector freezer
data/e8_unitary_hole_sectors.json       frozen residual-geometry certificate
tests/e8-unitary-hole-sectors.test.js   digest, theorem and anti-overread guards
rtl/e8_unitary_hole_adj.v  compact GF(9) predicate plus independent 120-row ROM
rtl/verify_e8_unitary_hole_adj.ys complete compact-versus-ROM SAT miter
rtl/e8_unitary_voltage_lift.v thirteen-type affine relation predicate
rtl/e8_unitary_reversible_dilation.v 240-bit square-zero reversible dilation
rtl/verify_e8_unitary_voltage_lift.ys exhaustive affine-versus-ROM miter
rtl/verify_e8_unitary_reversible_dilation.ys exhaustive involution proof
rtl/holotrade_admit.v       admission/locality datapath + golden reference
rtl/verify.ys               complete 2^25-output formal miter
rtl/synth.ys                reproducible iCE40 synthesis
tests/core.test.js          exact facts and engine contracts
docs/holotrade.tex          paper source
docs/holotrade.pdf          compiled paper
```

## Paper

[docs/holotrade.pdf](docs/holotrade.pdf) develops the product argument, evidence taxonomy, topology certificate, pricing and execution model, paired simulation, formal hardware boundary, limitations, and primary-source bibliography.

MIT licensed.
