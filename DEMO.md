# Holotrade — 6-minute demo script

```bash
npm run serve     # http://localhost:8080
```

Everything below is live. Nothing is a recording, and the simulation is seeded so
it behaves the same way every time you run it.

**Top-right controls:** `1×` cycles the clock speed (1 → 2 → 5 → 15). Push it to
**5×** before you start so the market visibly moves while you talk. `Pause`
freezes everything if someone asks a question mid-flow.

---

## 0:00 — The one-line pitch

> *"Every compute marketplace sells the same thing: a box, by the hour. The hour
> is a billing artefact — it exists because provisioning used to take minutes.
> A microVM boots in 171 milliseconds. So we sell node-seconds, and that lets us
> price four things the hour was throwing away."*

---

## 0:30 — Exchange · the price has parts

Land on **Exchange**. Point at the order book.

> *"The ask side isn't a market maker. It **is** the pricing engine — every
> listed machine posts an offer at its own clearing price."*

Point to **Best quote, decomposed** on the right.

> *"So every line in that book takes apart. Six multipliers over a hardware
> base. Energy is the live wholesale price at that site this second. Genetics is
> what that machine has **learned**. Demand is the balancer. Health is wear.
> Quantum is 1 for everything classical. Locality is distance in the fabric."*

Then the floor, underneath:

> *"And a floor: electricity plus maintenance reserve plus capital recovery. We
> refuse to clear below it. A discount that doesn't repay the machine isn't a
> discount, it's a loss the operator hasn't noticed yet."*

**Buy something** — click **Buy** with the default 4 node-hours. You'll get a
fill toast and orders appear. This seeds the Portfolio and Fabric views later.

---

## 1:30 — Balance · the result that pays for the design

Go to **Balance**. This is the strongest thing in the demo — don't rush it.

> *"The naive way to price demand is one-sided: busy machine costs more. That
> leaves half your fleet idle, still aging, still drawing power, still due for
> the same service visit. So our demand term is two-sided — premium above a
> target band, **discount** below it."*

Point at the **Utilisation Gini** tile (should read ~0.08).

> *"Gini is the standard inequality measure. Zero means every machine equally
> loaded. Watch this."*

**Flip the "Balancer ON" toggle off.** Wait ~15 seconds at 5× speed. The Gini
climbs and the line on the chart rises visibly.

> *"0.083 to 0.164. Dispersion doubles. And here's the part that matters —
> nothing in that loop pushes utilisation toward the band. A machine's target
> comes from its **price** relative to its own hardware class, and that price
> came from its utilisation. The band is where the loop settles, not where it's
> aimed."*

**Flip it back on.** Watch it fall.

Then scroll to the amber box:

> *"And this isn't just capital efficiency. Thermal cycling — not duty cycle —
> is what physically kills silicon. A machine held flat at 70% wears slower than
> one swinging between idle and pinned at the same average. Evenly loaded fleet,
> longer hardware life, service events spread across the calendar instead of
> arriving in a clump you have to staff for."*

---

## 3:00 — Fabric · you buy shapes, not counts

Go to **Fabric**. Click a node on the W(3,3) diagram — it lights its 12 neighbours.

> *"Our machines are addressed by position in a finite geometry. Forty points,
> 240 connections, diameter two — any machine reaches any other in at most two
> hops regardless of traffic. And routing is one arithmetic test on the address."*

Use the **From/To** dropdowns. Point at `⟨x,y⟩ mod 3`.

> *"That's the entire forwarding decision. No routing table. Nothing to build,
> distribute, converge, or keep fresh. Which is why locality is a **number** we
> can price per order instead of a heuristic about availability zones."*

Then the consequence:

> *"And because routing and computing are the same operation here, compute and
> bandwidth are one provisioned quantity. Forty scattered machines and forty
> wired as one cell have the same count and completely different value. So we
> price the **shape**."*

Scroll to **The recursion closes**:

> *"A network of computers is a computer. So a network of those is a computer.
> A composite implements the same interface a single machine does — so there is
> **one order book and one pricing engine at every level**. The engine can't tell
> a GPU from a campus and doesn't need to."*

Point at the level table — H1 quotes, H2 quotes, H3 quotes, same engine.

Then the **swap book** at the bottom (populated because you bought earlier):

> *"Trading fragments ownership. After a month everyone holds confetti and the
> market's total bandwidth has collapsed, even though every position looks fine.
> So: swap book. I give you my orphan in your cell, you give me yours in mine.
> No cash. It's disk defragmentation, except the value recovered is bandwidth —
> and both sides gain, which is why anyone takes the other side."*

Click a **Swap**. Coherence goes up.

---

## 4:15 — Execution · what's actually being sold

Go to **Execution**.

> *"The node is the asset. The **plan** is the contract. The node-second is the
> unit."*

Click **Sign plan**. Placements appear.

> *"Signed before anything boots — names the exact software by fingerprint, the
> only address it may contact, the window it's valid for. That's the difference
> between renting a machine and buying a guarantee about what happened on it."*

Point at the placement table.

> *"Ranked by **total** cost, not headline rate — boot cost and migration
> distance both enter. Cold start is real work, so we charge it once,
> explicitly, instead of smearing it into the rate."*

Click **Launch**. A VM appears and the meter starts ticking every second.

Now switch the workload class to **Lattice / QCD simulation** (t=12) and sign
another plan:

> *"This one needs capability ordinary hardware doesn't have. Watch."*

Try to launch it on a classical node — it refuses with `NO_MAGIC`.

> *"It refuses and says why. It doesn't quietly substitute something that won't
> work. That refusal is in software, in the tests, and in the hardware."*

Point at the **audit chain** — INTACT, every entry committing to the last.

---

## 5:15 — Genetics · where the margin actually is

Go to **Genetics**.

> *"Spot node-hours are a commodity, and commodities converge to marginal cost —
> which is exactly our floor. **There's no durable business selling
> undifferentiated node-hours.**"*

> *"Trained cores are not a commodity. A machine that's run genomics for six
> months is a strictly better genomics machine than the identical chassis next to
> it, and the gap widens. That's the spread."*

Point at the breeding console:

> *"And the prediction is stated **before** the cross, and comes in below the
> better parent on purpose — a merge is lossy and a fresh core has no track
> record. We don't credit it with its parents' completions."*

---

## 5:45 — Close on the honest scope

Go to **The Model**, scroll to the bottom three grey boxes.

> *"Last thing. Everything geometric here is proved and machine-checked — run
> `npm test`, 45 tests. The fleet and the grid prices are simulation, and we say
> so. And the physics programme this is built on top of? **Holotrade doesn't
> depend on any of it being true.** Everything we price is finite mathematics
> that holds regardless."*

---

## If someone asks a hard question

| Question | Answer |
|---|---|
| *"Is the geometry real or marketing?"* | `npm test` — 45 tests. SRG(40,12,2,4), 240 edges, diameter 2, bisection exactly 100 against the spectral bound. And `npm run verify:rtl` SAT-proves the routing primitive over all 65,536 inputs. |
| *"Have you found bugs in your own model?"* | Two, both by the test suite. A doubled bisection figure (wrong edge denominator) and a non-monotone demand curve where a machine got *cheaper by becoming busier* — directly arbitrageable. Both documented in the source beside the fix. |
| *"What's the hardware story?"* | 39 LUT4s and 6 carries on an iCE40 — the whole routing and admission decision. Formally verified. We deliberately don't quote a clock speed: that's a fact about a placed-and-routed part and we haven't placed or routed it. |
| *"What's the biggest risk?"* | The genome premium is a hypothesis with a good mechanism, not a measurement on production workloads. It's where the durable margin lives, so it's the first thing to validate. It's stated as a risk in the paper. |
| *"Why not just undercut on price?"* | Because that's the commodity trap. The floor is where undifferentiated node-hours end up, and we've made it explicit. The product is the differentiation the hourly rate was flattening. |
| *"Is this a blockchain?"* | No. Hash-chained audit logs, which is one idea from that family and the useful one. No token, no mining, no consensus overhead. |

---

## Reset between demos

Reload the page. The simulation is seeded — you get the identical starting fleet,
the same prices, the same everything.
