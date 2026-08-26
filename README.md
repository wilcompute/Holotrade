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

### Tensor placement robustness, and one open interval

A depth-2 tensor tile is \(L\times M\) for two W(3,3) lines: 16 leaves in the \(40\times40\) fabric. The
relevant quantity is \(\tau_2\), the fewest leaf failures that can leave **no** intact tile anywhere. Fewer
than \(\tau_2\) failures always leave some tile whole, so \(\tau_2-1\) is a hard survivability floor.

Shadow double-counting proves \(\tau_2\ge110\), and the obvious construction \(B\times B\) from an 11-point
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

**\(\tau_2\) itself is still open in \([110,115]\).** The lower bound has not moved. Two models that encode
everything tightness forces at 110 — both shadow families pinned to the exactly 360 minimum blockers, every
fibre and co-fibre an independent set capped by \(\alpha=7\), and the degree identity linking them — each
returned UNKNOWN rather than a decision. That is recorded as a negative result; `exactTau` is `null` in the
engine and the tests pin the open wording.

The E8-to-W33 refinement is a promising future topology compiler only after an explicit, complete certificate exists. The truncated external JSON previously considered for this repo is intentionally not imported.

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
