# HoloTrade — live demo runbook

This is the reliable six-minute path through the prototype. It separates what is
live, what is simulated, and what is exact, while still landing the product
story: a transparent quote becomes a bounded execution contract, then a meter
and a receipt.

## Preflight

Run this once before the meeting:

```bash
npm test
npm run verify:rtl
npm run synth:rtl
npm run experiment:balancer
npm run serve
```

Open <http://127.0.0.1:8080>, reload once, and leave the speed at **1×**. The
fleet and market use a deterministic seed, so reload is the reset button.

The expected headline checks are:

- 56 software tests pass;
- the RTL miter passes over all \(2^{25}=33,554,432\) input assignments;
- iCE40 synthesis reports 49 LUT4 cells and 6 carry cells;
- the paired 64-seed simulation reports a 60.34% terminal-Gini reduction, with
  all 64 pairs improving.

If you only have three minutes, do **Exchange → Fabric → Execution**.

## 0:00 — One sentence

> “HoloTrade is a topology-aware compute broker: it shows the capacity behind a
> quote, binds a job to a named machine and policy envelope, meters node-seconds,
> and reconciles the result into a receipt.”

Point to the evidence strip at the top. The labels are part of the product:
**EXACT**, **FORMAL**, **SYNTHESIZED**, **REGRESSION**, **SIMULATION**, and
**PROTOTYPE** do not mean the same thing.

## 0:25 — Exchange: inspect before buying

On **Exchange**, start with the ticket and “Best quote, decomposed.”

> “The headline rate is an hourly-equivalent comparison quote. The actual
> execution unit is a node-second. The decomposition exposes energy,
> specialization, demand, health, declared capability, locality, and the
> operator floor instead of hiding them in one opaque price.”

Use the two interactive graphs:

1. Move across **Depth** and switch between **Liquid**, **50%**, and **Full
   book**. Change quantity from 4 to 12 and point out expected fill, VWAP, and
   slippage. The chart is cumulative executable depth, not decorative volume.
2. Hover **Value frontier**. Highlight that HoloTrade compares delivered
   throughput per dollar across unlike hardware; frontier points are offers not
   dominated on both price and capacity.

Return quantity to **4** and click **Buy**.

> “This fill creates a `SIMULATED_QUOTE_RECEIPT`. It proves what this seeded
> market quoted; it does not pretend a workload ran.”

That fill also seeds Portfolio and Fabric for the next sections.

## 1:30 — Balance: show the frozen result, then the live model

Go to **Balance**.

> “One-sided scarcity pricing makes busy capacity dearer but gives cold capacity
> no reason to attract work. This modeled policy is two-sided: premium above the
> target band and discount below it, bounded by an operating floor.”

Lead with the frozen experiment card, not a number inferred from the animation:

- same 64 seeds in both arms;
- 220 modeled nodes;
- 500 one-minute steps;
- balancer-on terminal Gini 0.06458;
- balancer-off terminal Gini 0.16110;
- paired reduction 60.34%, 95% CI [58.90%, 61.77%];
- 64/64 pairs improved.

Toggle **Balancer OFF**, let the live chart move, then restore it.

> “The chart is a deterministic live simulation. The 60.34% result comes from
> the separately reproducible paired packet, not from eyeballing this run. It is
> evidence about this model, not production telemetry or proof of longer silicon
> life.”

## 2:25 — Fabric: topology is part of the capacity

Go to **Fabric** and click a point in the W(3,3) graph. Hover points and choose a
From/To pair.

> “At level one the address space is an exact 40-vertex graph:
> SRG(40,12,2,4), 240 edges, diameter two. Direct adjacency is one symplectic
> inner-product test. The software finds a relay by a bounded scan of the forty
> points.”

Point to the bisection certificate.

> “This explicit 20|20 cut has exactly 100 crossing edges, meeting the spectral
> lower bound. That is an exact graph certificate—not a claim about a deployed
> cable plant, congestion, failures, or physical throughput.”

Then show **Portfolio** or the Fabric cell table.

> “For a partial basket we compute the graph it actually owns: induced edges,
> components, minimum degree, and diameter only when connected. A two-node
> holding cannot borrow an unowned relay and call itself diameter two.”

If the swap book has a proposal, execute one and show that both owners’
coherence improves. If it is empty, say that this seeded holding is already
locally coherent; the system refuses to manufacture a one-sided swap for the
demo.

## 3:35 — Execution: contract, refusal, delivery

Go to **Execution**.

Start by pointing at **Nodes**, which is visibly locked to one.

> “Multi-node delivery is not implemented, so the browser cannot submit that
> request and the engine rejects it if called directly. HoloTrade does not
> multiply one VM’s meter by two and call that gang execution.”

Create the successful path:

1. Set **Nodes** to 1 and **Seconds** to 120.
2. Leave egress blank to deny network access.
3. Use the supplied full example artifact digest.
4. Click **Seal demo plan**, then launch the best placement.

> “This is deliberately called a demo integrity seal. It binds owner, nonce,
> artifact, validity window, cap, workload, and anchor into a deterministic
> digest so we can exercise lifecycle semantics. It is not a digital signature,
> remote attestation, or proof that these bytes ran.”

Point to total modeled cost: boot cost and locality are explicit. Let the meter
advance, then click **Halt** if the plan has not already settled.

> “The engine rechecks the live price cap, clips the last interval so it cannot
> overbill the requested duration, includes boot overhead, and emits a delivery
> receipt. The local audit checker recomputes every body and every link; it is
> still not externally authenticated.”

## 4:55 — Assets and receipts: identity without invented liquidity

On **Assets & UOR**, show a reference moving through the exact unsigned 64-bit
codec and back.

> “The object reference is an invertible mixed-radix identifier across the full
> unsigned-64 range. Policy mobility estimates how many configured delivery
> regions still accept an asset. We do not relabel group-orbit arithmetic as
> market liquidity.”

On **Receipts**, contrast the two surfaces:

- a market fill emits a `SIMULATED_QUOTE_RECEIPT`;
- execution produces the separate metered delivery record;
- neither is presented as attestation.

## 5:35 — Close

> “What exists today is a research prototype with an unusually explicit trust
> boundary: exact topology, exhaustive RTL equivalence, reproducible simulation,
> and a complete single-node lifecycle. The next product step is to replace the
> demo seal and seeded telemetry with signed inventory, real attestation, and a
> reservation ledger—without changing the buyer-facing flow you just saw.”

## Questions you are likely to get

| Question | Answer |
|---|---|
| “Is the geometry marketing?” | No. Tests enumerate SRG(40,12,2,4), 240 edges, diameter 2, and the explicit cut of size 100. Those are graph facts; physical network performance remains unclaimed. |
| “What is formally verified?” | The complete admission/locality RTL is compared with an independently written behavioral reference across all \(2^{25}\) inputs and every output, including invalid addresses and refusal priority. |
| “Is the plan signed?” | No. `DEMO_INTEGRITY_SEAL` is an unkeyed deterministic checksum. Production needs canonical serialization, signatures, attestation, freshness, key lifecycle, and an external transparency or settlement service. |
| “Is 60.34% a customer result?” | No. It is the paired result of the checked-in deterministic simulator: 64 seeds, 220 nodes, 500 one-minute steps. It motivates a field experiment; it does not replace one. |
| “What did synthesis prove?” | Technology mapping uses 49 `SB_LUT4` and 6 `SB_CARRY` cells. There is no place-and-route timing, board test, or network benchmark yet. |
| “Why node-seconds?” | The demo’s modeled boot distribution makes fine-grained settlement useful, and the meter supports it. The specific boot values are model inputs, not measurements from a deployed HoloTrade fleet. |
| “Is this a blockchain?” | No token, mining, or consensus layer is built. The prototype has a locally checked checksum chain; production settlement architecture remains open. |
| “Can it run a distributed job?” | Not yet. Single-node execution is complete; multi-node requests are explicitly rejected until atomic reservation, launch, metering, and failure handling exist. |

## Recovery during a live demo

- **Want a clean state:** reload the page.
- **Chart looks crowded:** choose the Liquid depth zoom or narrow the ticket
  quantity.
- **No swap proposal:** explain that swaps require a live improvement for both
  owners; do not force one.
- **No admissible placement:** return to a classical workload, Nodes = 1, and a
  blank egress grant.
- **Question interrupts motion:** click Pause; it freezes the simulation without
  discarding state.
- **Need proof without the browser:** keep a terminal ready with `npm run verify`
  and `npm run experiment:balancer`.
