# Holotrade

**An exchange for compute.** Not a price list for VMs — a venue where the unit is the
node-second, the contract is a signed execution plan, and the price of every machine
decomposes, on screen, into six auditable terms.

```bash
npm run serve      # http://localhost:8080
npm test           # 45 regression tests
npm run verify:rtl # SAT-prove the routing primitive
```

No build step. No dependencies at runtime. Vanilla HTML, CSS and JavaScript.

**Demoing it?** [`DEMO.md`](DEMO.md) is a 6-minute walkthrough script.
**The full argument** is in [`docs/holotrade.pdf`](docs/holotrade.pdf) — 29 pages,
written to be read by an investor with no technical background and by an engineer
who wants to check the arithmetic.

---

## Why not just rent VMs by the hour?

Selling "a node for an hour" is the obvious design and it is the wrong one, for three
reasons that are all measurable.

**1. The hour is a billing artefact, not a physical one.** It exists because provisioning
a conventional VM takes minutes, so an hour is the smallest slice worth the scheduling
overhead. A microVM boots in ~171 ms (p50; p99 178 ms, measured on Firecracker over
deliberately pessimistic rotational storage). Once the unit boots in under a fifth of a
second, the hour has no physical justification left.

**2. An hour cannot express the thing that actually varies.** Grid prices move every five
minutes and go negative at 3 a.m. on ERCOT. If your settlement granularity is an hour you
have thrown the signal away before you can price it. Per-second energy pricing *requires* a
sub-second execution unit or it is theatre.

**3. "A node for an hour" is not auditable.** You cannot prove what ran on it, against
which artefacts, under which grants. A signed execution plan can: it names the artefact
digests, the egress grants, the secret references and the validity window *before* anything
boots, and the audit log chains every event to the last.

So:

| | |
|---|---|
| **asset** | the **node** — durable, has a genome and a health record, is what you lease or own |
| **contract** | the **plan** — signed, content-addressed, scoped, time-boxed, tradeable *before* it runs |
| **unit** | the **node-second** — what settles, metered against real energy at the second it was drawn |

---

## The price

```
P  =  P₀ × E × G × D × H × Q × L
```

Multiplicative, not additive — which keeps the terms independent, keeps each auditable on
its own line, and (once each is clamped) stops any single factor driving the price to zero
or infinity on its own. The buyer sees the full decomposition on every quote. There is no
opaque "market rate".

| Term | Prices | Source |
|---|---|---|
| **E** — energy | live wholesale $/MWh at that site, this second, PUE-adjusted | clamped power law, so an operator passes through most of a move and none of a tail |
| **G** — genetics | what the node's AI core has **learned** about your workload class | specialisation × realised fitness × provenance depth. Never a nameplate figure |
| **D** — demand/wear | the balancer: premium above the target band, **discount below it** | two-sided; superlinear premium because thermal cycling is |
| **H** — health | derate × Weibull reliability × correctable-error drift | a worn node should be visibly cheaper, not quietly slower |
| **Q** — quantum | exactly **1** for anything classical, and always will be | Gottesman–Knill: the Clifford layer is polynomial-time anywhere. Only non-Clifford gates are scarce, at 9ᵗ |
| **L** — locality | fabric distance from your data | one symplectic inner product per hop — not an availability-zone heuristic |

The **floor** is energy + maintenance reserve + capital recovery. All three, because a
discount that does not repay the machine is not a discount — it is a loss the operator has
not noticed yet. The exchange refuses to clear below it.

### The measured result

The naive design prices scarcity only: busy node costs more. That leaves the cold half of
the fleet idle, and an idle node still ages, still draws standby power, and still has to be
serviced on the same calendar. So `D` charges a premium above the band and pays a discount
below it.

> **Utilisation Gini ≈ 0.083 with the balancer on, ≈ 0.164 with it off — a 50% reduction in
> fleet dispersion.**

Nothing in the loop pushes utilisation toward the band directly. A node's target is set by
its *price* relative to the median of its own hardware class, and that price came from its
utilisation. The band is where the loop settles, not where it is aimed. Toggle it on the
Balance page and watch the Gini climb.

Why dispersion is the thing to minimise: **thermal cycling, not duty cycle, is what kills
silicon.** A node held flat at 70% wears slower than one swinging between idle and pinned at
the same average. An evenly loaded fleet does not merely use its capital better — it
physically lasts longer, and its service events arrive spread out instead of in a clump you
have to staff for.

---

## The network is the computer

On W(3,3) — the symplectic generalized quadrangle over 𝔽₃⁴, 40 points and 240 edges —
routing a packet *is* applying a gate *is* addressing memory. That is an algebraic identity,
not an analogy, and it is the fact every conventional compute marketplace is built to
contradict. They sell you compute, then network, then egress, because in a von Neumann
machine those are three things with three bills.

**So you do not buy nodes, you buy shapes.** Forty scattered nodes and one complete cell
have the same count and completely different value:

| | scattered 40 | one cell |
|---|---|---|
| what it is | 40 computers + a network bill | **one** computer |
| diameter | whatever the internet gives you | **2** |
| bisection | ~0 | **exactly 100** of 240 edges — the spectral bound (40/4)(12−2), met by an explicit 20\|20 cut |
| multipath | configure it | **μ = 4** internally-disjoint paths, free |

Coherence therefore enters price at the **basket** level, never the node level, because it
is not a property any single node has. And it is superlinear: the last few edges that
complete a cell are worth more than the first few, because they are what collapse the
diameter and unlock the multipath.

### The recursion closes

A network of computers is a computer, so a network of *those* is a computer too — the
fractal substitution law `Hₙ`: 40ⁿ leaves at routing diameter 8n.

A `Composite` implements exactly the interface a leaf `Node` implements — address, genome,
health, utilisation, throughput — so **there is one order book and one pricing engine, and
they apply at every level.** The engine cannot tell whether it is quoting a single GPU or a
campus, and does not need to. An operator lists their whole H₃ campus as one instrument at
level 4; a buyer at level 5 sees it as one line in the same book a single GPU appears in at
level 1. The book is self-similar because the machine is. There is a test for it.

| n | leaves | diameter | seats |
|---|---|---|---|
| 1 | 40 | 8 | a rack |
| 4 | 2,560,000 | 32 | a city pilot |
| 7 | 163,840,000,000 | **56** | everyone + every device |

"Diameter 16" is not an SLA someone promises you and pays penalties for missing. It is a
theorem about the shape you bought.

### Defragmentation

Trading fragments ownership. After a month of spot fills everyone holds confetti — a few
points in each of forty cells — and the market's aggregate bisection has collapsed even
though every individual position looks fine.

The fix is a **swap book**: I give you my orphan in your cell, you give me yours in mine.
No cash beyond a small adjustment for the difference in the two machines. It is disk
defragmentation, except the value recovered is bandwidth — and unlike a disk, both parties
can be made strictly better off. **A swap is only offered when both sides gain**, because
otherwise nobody takes the other side.

---

## Instruments

Five, because the risks a compute buyer actually carries are five different risks. Only the
first is a VM.

| | tenor | what it is for |
|---|---|---|
| **Spot node-hour** | immediate | you need it now and accept today's price |
| **Forward block** | 1–90 d | you need it in March and cannot carry an ERCOT heat dome |
| **Burst option** | 1–30 d | you *might* need 400 nodes on launch day; you want the right, not the obligation |
| **Genome lease** | 7–365 d | you want a **core that already knows your workload class** — priced on fitness, not silicon |
| **Supply offer** | open | you own idle nodes and want the exchange to sell them |

Spot node-hours are a commodity and commodities converge to marginal cost — which is
exactly the floor. **Trained cores are not a commodity.** They are heterogeneous, their
quality is observable, and their value compounds with use. That is where the spread lives.

A genome lease states its own caveat on the quote: a leased core keeps specialising toward
whatever *you* feed it. You are buying a starting point, not a frozen asset, and by the end
of a long lease you will have changed the thing you rented.

---

## Value = orbit-stabilizer co-volume

Every real-world constraint is a symmetry an asset does *not* have. A node pinned by
data-residency law cannot be moved by the automorphisms that would move it; a bare-metal
reservation is fixed harder still. Each constraint multiplies the stabiliser, and by
orbit-stabilizer that divides the orbit — the set of positions at which a counterparty could
take delivery.

So **liquidity is a computable property of the asset's own symmetry**, not a statistic
gathered from the tape. That is the honest reason a residency-pinned node should not trade
at the same price as an identical unpinned one, and it is a number you can check rather than
a discount someone asserts.

The address carries it: 2⁶⁴ = 40 (Sylow choice) × 1,296 (|N_G(P₃)|) × payload, and
40 × 1,296 = 51,840 = |Aut(W(3,3))|. **An asset's identity and its position in the fabric
are the same 64 bits** — no separate registry to go stale, no lookup to do.

---

## The RTL

The exchange's hot path is in `rtl/holotrade_admit.v`: the symplectic form, the adjacency
test that *is* the routing decision, the migration price law, and the five-condition
admission gate.

```
SAT proof finished - no model found: SUCCESS!
```

Two independently written implementations of the form — one staged 𝔽₃ operators, one plain
integer arithmetic with a single modulo — are proved equivalent **over the entire 16-bit
input space** by SAT, not sampled and not simulated. Then `tests/core.test.js` closes the
loop from the other side, checking the RTL's exact encoding against the W(3,3) graph the
software builds, over all 1,600 ordered pairs. Proving gate ≡ gold is necessary and not
sufficient: both could agree and both be wrong about the geometry.

Synthesised to iCE40 HX8K: **39 × SB_LUT4 + 6 × SB_CARRY**. The whole routing and admission
decision, in thirty-nine logic cells, with no table to build, distribute, converge or keep
fresh.

Timing is deliberately **not** reported. A cell count is a fact about a netlist; a frequency
is a fact about a specific part after place-and-route, and this design has been neither
placed nor routed.

---

## Layout

```
index.html            twelve views, no build step
css/styles.css        design system, dark-first, theme-aware
data/catalog.js       seed data — sites, hardware, workloads, instruments
js/substrate.js       W(3,3) geometry, addressing, routing, migration law, Landauer
js/energy.js          per-second grid prices, carbon, thermodynamic floor
js/fleet.js           nodes: hardware, genome, health, wear, lineage
js/pricing.js         the six multipliers, the floor, the balancer feedback loop
js/fabric.js          coherence, swap book, composition — the recursion
js/genetics.js        lineage, fitness, breeding, drift forecasting
js/uor.js             addresses, smart assets, co-volume, venue capacity
js/execution.js       signed plans, admission gate, microVMs, per-second meter, audit chain
js/market.js          order books, matching, instruments, receipts
js/app.js             orchestration and rendering only — invents no quantities
rtl/                  the routing primitive, its SAT proof, its synthesis script
tests/core.test.js    45 tests: substrate facts and engine contracts
docs/holotrade.tex    the full paper
```

---

## Honest scope

**Exact and computed here.** The W(3,3) geometry — SRG(40,12,2,4), 240 edges, 40 totally
isotropic lines of 4 points, diameter 2, bisection 100 as the spectral bound met by an
explicit cut; |Sp(4,𝔽₃)| = |W(E₆)| = 51,840; the fractal law 40ⁿ at diameter 8n; the
Landauer floor 2.64×10⁻¹⁹ J/cycle at 300 K from 58 syndrome qutrits × kT ln 3; the 9ᵗ magic
cost; the venue capacity identities (×1728 cadence, 27/80 logical rate, 1/384 coherence
blocks, h(E₈) = 30 ms floor). Run `npm test` and check every one.

**Modelled, not measured.** The fleet, the grid prices, the genomes, the wear, the order
flow. A working simulation with a seeded PRNG, so every run reproduces. Wire a real
grid-price feed, real DCIM telemetry and a real inventory in place of `data/catalog.js` and
the engines above it do not change.

**Asserted by the source programme, not by this repo.** That W(3,3) is a candidate physical
substrate, and the physics identifications that go with it. **Holotrade does not depend on
any of that being true.** Everything it prices — the geometry, the routing rule, the code
rate, the thermodynamic floor — is finite mathematics that holds regardless. The photonic
hardware that would realise the quantum layer **does not exist**; what runs here is the
classical Clifford emulation, which is polynomial-time and portable, and the quantum
advantage stays a separately priced dial rather than a capability being claimed.

---

MIT. Built on the W(3,3)–E₈ substrate programme.
