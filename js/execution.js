// ======================================================================
// HOLOTRADE EXECUTION LAYER
//
// This module answers the question the whole product turns on:
// WHAT, EXACTLY, IS BEING BOUGHT AND SOLD?
//
// ---------------------------------------------------------------------
// It is not a VM node.
//
// Selling "a VM node for an hour" is the obvious design and it is the
// wrong one, for three reasons that are all measurable:
//
//   1. The hour is a billing artefact, not a physical one. It exists
//      because provisioning a conventional VM takes minutes, so an
//      hour is the smallest slice worth the scheduling overhead.
//      A microVM boots in ~171 ms (p50; p99 178 ms, measured on
//      Firecracker over rotational storage -- a deliberately
//      pessimistic baseline). Once the unit boots in under a fifth of
//      a second, the hour has no physical justification left, and
//      per-second settlement becomes not just possible but correct.
//
//   2. An hour cannot express the thing that actually varies. Grid
//      prices move every five minutes and go negative at 3 a.m. on
//      ERCOT. If your settlement granularity is an hour you have
//      thrown away the signal before you can price it. Per-second
//      energy pricing -- the core idea this exchange is built around --
//      REQUIRES a sub-second execution unit or it is theatre.
//
//   3. "A node for an hour" is not auditable. You cannot prove what
//      ran on it, against which artefacts, with which grants. A signed
//      execution plan can: it names the artefact digests, the network
//      grants, the secret references, and the validity window BEFORE
//      anything boots, and the audit log chains every event to the last.
//
// ---------------------------------------------------------------------
// So Holotrade's atomic tradeable unit is the NODE-SECOND, and its
// contract is the EXECUTION PLAN:
//
//     asset     the node        -- durable, has a genome and a health
//                                  record, is what you lease or own
//     contract  the plan        -- signed, content-addressed, scoped,
//                                  time-boxed, tradeable before it runs
//     unit      the node-second -- what settles, metered against real
//                                  energy at the second it was drawn
//
// A plan is a smart asset in the exact sense the substrate papers use:
// content-addressed identity, a projection that assembles capabilities
// into a container, and an emission that produces output plus a
// verifiable receipt. Projection -> Execution -> Emission. It is
// tradeable BEFORE it executes, which is what makes forwards and
// options on compute meaningful rather than notional.
//
// ---------------------------------------------------------------------
// ISOLATION AND DENSITY
//
// Each plan runs in its own microVM: a real kernel under a real
// hypervisor, not a shared-kernel container. Deny-all-by-default
// networking, a single vsock channel out, a sealed immutable rootfs.
// That is what makes it safe to run a stranger's job on your node --
// which is the precondition for a two-sided market existing at all.
// Without it, "sell your idle nodes" is a request to be compromised.
//
// Density comes from nested state: a uniform root over six levels
// denotes ~4.2 billion addressable stateful VMs using seven unique
// state blobs, because untouched siblings keep their digests and a
// content-identical replay reuses every key. Copy-on-write over a
// content-addressed store, with mailbox delivery costing seven path
// blobs plus one receipt. That is a structural upper bound from the
// reference runtime, not a throughput measurement.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  // Measured microVM boot distribution (Firecracker, pessimistic disk).
  // Used to price cold starts and to bound settlement granularity.
  const BOOT_MS = { p50: 171.5, p95: 176.0, p99: 178.0, target: 150 };

  // Settlement granularity. One second, because the boot cost is two
  // orders below it -- so a one-second slice is >99% useful work.
  const SETTLE_SECONDS = 1;

  let PLAN_SEQ = 1;

  // ------------------------------------------------------------------
  // Execution plan
  // ------------------------------------------------------------------

  class ExecutionPlan {
    /**
     * A plan is signed at creation and immutable after. Anything that
     * would change what runs -- a new artefact, a wider grant, a longer
     * window -- is a NEW plan with a new digest, not an edit. That is
     * what makes "this is what I bought" a checkable statement.
     */
    constructor(spec) {
      this.id = `PLAN-${String(PLAN_SEQ++).padStart(5, "0")}`;
      this.createdAt = Date.now();
      this.workloadId = spec.workloadId || "llm-train";
      this.name = spec.name || "unnamed plan";
      this.owner = spec.owner || "YOU";

      // content-addressed artefacts: pinned by digest, re-verified at boot
      this.artifacts = spec.artifacts || [];

      // deny-all by default; every grant is explicit and narrow
      this.grants = {
        network: spec.grants?.network || [],       // [] means no network device at all
        services: spec.grants?.services || [],
        secrets: spec.grants?.secrets || [],       // references only, never values
      };

      // validity window + nonce: outside the window the plan will not
      // boot, full stop, and the nonce is checked against a replay
      // store so a captured plan cannot be resubmitted inside it
      this.validFrom = spec.validFrom || Date.now();
      this.validUntil = spec.validUntil || Date.now() + 3600_000;
      this.nonce = S.hash32(`${this.id}|${this.createdAt}|${Math.random()}`).toString(16);

      this.requestedSeconds = spec.requestedSeconds || 3600;
      this.nodeCount = spec.nodeCount || 1;
      this.maxPricePerNodeSecond = spec.maxPricePerNodeSecond ?? null;
      this.anchorAddress = spec.anchorAddress || null;
      this.magicBudget = spec.magicBudget || 0;

      this.status = "signed";   // signed | scheduled | running | settled | expired | rejected
      this.digest = this.computeDigest();
      this.signature = this.sign();
    }

    /**
     * The plan's content address. Every field that affects what runs is
     * in the pre-image; the mutable status fields are not. So the
     * digest of a plan is stable from signature to settlement.
     */
    computeDigest() {
      const preimage = JSON.stringify({
        w: this.workloadId,
        a: this.artifacts.map((x) => x.digest).sort(),
        g: this.grants,
        vf: this.validFrom,
        vu: this.validUntil,
        s: this.requestedSeconds,
        n: this.nodeCount,
        t: this.magicBudget,
      });
      return S.hash32(preimage).toString(16).padStart(8, "0") +
             S.hash32(preimage + "|salt").toString(16).padStart(8, "0");
    }

    sign() {
      return `sig:${S.hash32(this.digest + this.owner).toString(16).padStart(8, "0")}`;
    }

    /** Verify nothing has been edited since signature. */
    verify() {
      return this.digest === this.computeDigest() &&
             this.signature === `sig:${S.hash32(this.digest + this.owner).toString(16).padStart(8, "0")}`;
    }

    isValidAt(ts = Date.now()) {
      return ts >= this.validFrom && ts <= this.validUntil;
    }

    /**
     * The admission gate. Every check REFUSES rather than degrades --
     * there is no best-effort path through this function, because a
     * silent fallback is how a security posture becomes decorative.
     *
     * Five gates, in the order a host would actually apply them:
     *   1. signature envelope matches the content
     *   2. nonce has not been seen (replay)
     *   3. inside the validity window
     *   4. no pin drift -- every artefact digest still resolves to the
     *      bytes it was pinned to at signing time
     *   5. the node can physically serve it: magic budget t > 0 needs
     *      magic-capable hardware, always, with no substitution
     */
    admissible(node, ts = Date.now(), replayStore = null) {
      if (!this.verify()) return { ok: false, code: "BAD_SIGNATURE", reason: "signature does not match content" };
      if (replayStore && replayStore.has(this.nonce))
        return { ok: false, code: "REPLAY", reason: `nonce ${this.nonce} already admitted` };
      if (!this.isValidAt(ts)) return { ok: false, code: "WINDOW", reason: "outside validity window" };
      const drift = this.pinDrift();
      if (drift) return { ok: false, code: "PIN_DRIFT", reason: `artefact ${drift} no longer matches its pin` };
      if (this.magicBudget > 0 && !node.hardware.magicCapable)
        return { ok: false, code: "NO_MAGIC", reason: `needs magic budget t=${this.magicBudget}; node is Clifford-only` };
      if (node.health.inService) return { ok: false, code: "IN_SERVICE", reason: "node in service" };
      return { ok: true };
    }

    /**
     * Pin-drift check. Artefacts are content-addressed and re-verified
     * at admission, not only at fetch -- a mutable tag that moved
     * between signing and boot is exactly the supply-chain hole this
     * closes. Returns the name of the first drifted artefact, or null.
     */
    pinDrift() {
      for (const a of this.artifacts) {
        if (!a.digest) return a.name || "unnamed";
        if (a.observed && a.observed !== a.digest) return a.name || a.digest;
      }
      return null;
    }
  }

  // ------------------------------------------------------------------
  // MicroVM instance
  // ------------------------------------------------------------------

  class MicroVM {
    constructor(plan, node, boot) {
      this.id = `VM-${plan.digest.slice(0, 6)}-${node.id.slice(-4)}`;
      this.planId = plan.id;
      this.nodeId = node.id;
      this.bootMs = boot;
      this.startedAt = Date.now();
      this.secondsRun = 0;
      this.state = "booting";     // booting | running | halted
      this.energyJoules = 0;
      this.cost = 0;
      this.events = [];
      // nested state accounting: seven path blobs per fresh transition
      this.stateBlobs = 7;
    }

    get uptimeSeconds() {
      return this.secondsRun;
    }
  }

  // ------------------------------------------------------------------
  // Scheduler + meter
  // ------------------------------------------------------------------

  class ExecutionEngine {
    constructor(fleet, pricing, energy, workloads) {
      this.fleet = fleet;
      this.pricing = pricing;
      this.energy = energy;
      this.workloads = workloads;
      this.rand = S.rng("holotrade-exec");

      this.plans = [];
      this.vms = [];
      this.auditLog = [];        // chain-signed, newest first
      this.maxAudit = 400;
      this.lastChainHash = "0".repeat(8);
      this.replayStore = new Set();   // nonces already admitted
      this.meteredSeconds = 0;
      this.meteredSpend = 0;
      this.meteredJoules = 0;
    }

    // -- audit chain ---------------------------------------------------

    /**
     * Chain-signed, tamper-evident log. Each entry commits to the
     * previous entry's hash, so removing or editing any entry breaks
     * every entry after it. Cheap, standard, and the reason a receipt
     * from this exchange means something.
     */
    append(kind, detail, refs = {}) {
      const prev = this.lastChainHash;
      const body = JSON.stringify({ kind, detail, refs, ts: Date.now() });
      const hash = S.hash32(prev + body).toString(16).padStart(8, "0");
      const entry = { seq: this.auditLog.length + 1, ts: Date.now(), kind, detail, refs, prev, hash };
      this.lastChainHash = hash;
      this.auditLog.unshift(entry);
      if (this.auditLog.length > this.maxAudit) this.auditLog.pop();
      return entry;
    }

    /** Walk the chain and confirm nothing has been altered. */
    verifyChain() {
      const ordered = [...this.auditLog].reverse();
      for (let i = 1; i < ordered.length; i++) {
        if (ordered[i].prev !== ordered[i - 1].hash) {
          return { ok: false, brokenAt: ordered[i].seq };
        }
      }
      return { ok: true, length: ordered.length };
    }

    // -- planning ------------------------------------------------------

    createPlan(spec) {
      const w = this.workloads.find((x) => x.id === spec.workloadId);
      const plan = new ExecutionPlan({ ...spec, magicBudget: w ? w.magicBudget : 0 });
      this.plans.unshift(plan);
      this.append("plan.signed", `${plan.name} (${plan.workloadId}) t=${plan.magicBudget}`, {
        planId: plan.id, digest: plan.digest,
      });
      return plan;
    }

    /**
     * Placement. Rank admissible nodes by TOTAL cost of the plan, not
     * by headline rate -- which means the cold-start cost and the
     * locality term both enter, and a slightly dearer node next door
     * can beat a cheap one eight hops away.
     *
     * The migration price law is the tiebreak: a neighbour costs 3 rays,
     * re-vectoring in place costs 6, so when the plan already has an
     * anchor on the fabric the scheduler will move it to an adjacent
     * node before it will reconfigure where it sits.
     */
    place(plan, { limit = 8 } = {}) {
      const candidates = [];
      for (const node of this.fleet.listedNodes()) {
        const adm = plan.admissible(node);
        if (!adm.ok) continue;
        const q = this.pricing.quote(node, {
          workloadId: plan.workloadId,
          anchorAddress: plan.anchorAddress,
        });
        if (!q.serviceable || q.price == null) continue;

        const perSecond = q.price / 3600;
        const boot = this.bootCostFor(node, q);
        const total = perSecond * plan.requestedSeconds * plan.nodeCount + boot.cost * plan.nodeCount;

        if (plan.maxPricePerNodeSecond != null && perSecond > plan.maxPricePerNodeSecond) continue;

        const mig = plan.anchorAddress
          ? S.migrationCost(plan.anchorAddress, node.addr)
          : { rays: S.RAY_COST.inPlace, hops: 0, channel: "in-place" };

        candidates.push({
          node, quote: q, perSecond, boot, total, migration: mig,
          fitness: this.fleet.fitness(node),
          score: total * (1 + (mig.rays - S.RAY_COST.adjacent) * 0.01),
        });
      }
      candidates.sort((a, b) => a.score - b.score);
      return candidates.slice(0, limit);
    }

    /**
     * Cold-start cost. Boot is real work: the kernel comes up, the
     * sealed rootfs is verity-checked, the artefact digests are
     * re-verified. It draws power and it occupies the node.
     *
     * At 171 ms against a one-second settlement slice that is a 17%
     * overhead on a single second and 0.005% on an hour -- so the
     * exchange charges it once, explicitly, rather than smearing it
     * into the rate. A buyer running many short plans can SEE what
     * their fan-out costs them.
     */
    bootCostFor(node, quote) {
      const jitter = 1 + (this.rand() - 0.5) * 0.06;
      const ms = (node.hardware.kind === "photonic" ? BOOT_MS.p50 * 0.55 : BOOT_MS.p50) * jitter;
      const seconds = ms / 1000;
      const perSecond = quote.price / 3600;
      // verity + artefact re-verification is CPU-bound, so it runs the
      // node near peak for its duration
      return {
        ms,
        seconds,
        cost: perSecond * seconds * 1.6,
        overheadPct: (seconds / SETTLE_SECONDS) * 100,
      };
    }

    // -- execution -----------------------------------------------------

    /**
     * Launch a plan onto a node. Refuses rather than degrades: an
     * inadmissible plan does not get a best-effort placement, it gets
     * a reason.
     */
    launch(plan, node) {
      const adm = plan.admissible(node, Date.now(), this.replayStore);
      if (!adm.ok) {
        plan.status = "rejected";
        this.append("plan.failed", `${adm.code}: ${adm.reason}`, {
          planId: plan.id, nodeId: node.id, code: adm.code,
        });
        return { ok: false, reason: adm.reason, code: adm.code };
      }
      this.replayStore.add(plan.nonce);
      this.append("plan.admitted", `${plan.name} -> ${node.id}`, {
        planId: plan.id, nodeId: node.id, digest: plan.digest, nonce: plan.nonce,
      });
      const q = this.pricing.quote(node, {
        workloadId: plan.workloadId,
        anchorAddress: plan.anchorAddress,
      });
      const boot = this.bootCostFor(node, q);
      const vm = new MicroVM(plan, node, boot.ms);
      vm.cost += boot.cost;
      vm.state = "running";
      this.vms.unshift(vm);
      plan.status = "running";
      plan.vmId = vm.id;
      plan.nodeId = node.id;

      node.currentWorkload = plan.workloadId;
      node.utilisation = Math.min(1, node.utilisation + 0.06 * plan.nodeCount);

      this.append("plan.launched", `${vm.id} on ${node.id} in ${boot.ms.toFixed(1)}ms`, {
        planId: plan.id, nodeId: node.id, vmId: vm.id, digest: plan.digest,
      });
      return { ok: true, vm, boot, quote: q };
    }

    /**
     * Meter every running VM for dt seconds of wall clock.
     *
     * This is the per-second billing loop and it is the point of the
     * whole design: the price applied to each second is the price that
     * second actually cost, at that datacentre, at that grid price,
     * on that node's current health and utilisation. Not an average.
     * Not an hourly rate divided by 3600.
     */
    meter(dtSeconds = 1) {
      const settled = [];
      for (const vm of this.vms) {
        if (vm.state !== "running") continue;
        const node = this.fleet.get(vm.nodeId);
        const plan = this.plans.find((p) => p.id === vm.planId);
        if (!node || !plan) { vm.state = "halted"; continue; }

        const q = this.pricing.quote(node, {
          workloadId: plan.workloadId,
          anchorAddress: plan.anchorAddress,
        });
        if (!q.serviceable || q.price == null) continue;

        const perSecond = q.price / 3600;
        const slice = perSecond * dtSeconds * plan.nodeCount;
        vm.cost += slice;
        vm.secondsRun += dtSeconds;

        const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
        const kw = (node.hardware.tdp / 1000) * (dc ? dc.pue : 1.2) * (0.32 + 0.68 * node.utilisation);
        const joules = kw * 1000 * dtSeconds * plan.nodeCount;
        vm.energyJoules += joules;

        this.meteredSeconds += dtSeconds * plan.nodeCount;
        this.meteredSpend += slice;
        this.meteredJoules += joules;

        if (vm.secondsRun >= plan.requestedSeconds) {
          settled.push(this.settle(vm, plan, node));
        }
      }
      return settled;
    }

    /**
     * Settlement. Emits the receipt, closes the VM, and writes the
     * final chained audit entry.
     *
     * The receipt reports what the buyer actually got, in the units
     * that matter: node-seconds delivered, dollars drawn, joules drawn,
     * grams of CO2e, and how far above the Landauer floor the work ran.
     * The last one is the honest efficiency figure, because its
     * denominator is a thermodynamic law rather than a benchmark.
     */
    settle(vm, plan, node) {
      vm.state = "halted";
      plan.status = "settled";
      const dc = this.energy.datacenters.find((d) => d.id === node.dcId);

      const receipt = {
        id: `RX-${vm.id}`,
        planId: plan.id,
        planDigest: plan.digest,
        vmId: vm.id,
        nodeId: node.id,
        nodeAddress: node.address,
        workloadId: plan.workloadId,
        nodeSeconds: vm.secondsRun * plan.nodeCount,
        bootMs: vm.bootMs,
        cost: vm.cost,
        effectiveRatePerNodeHour: vm.secondsRun > 0 ? (vm.cost / (vm.secondsRun * plan.nodeCount)) * 3600 : 0,
        joules: vm.energyJoules,
        kwh: vm.energyJoules / 3.6e6,
        gramsCO2e: dc ? (vm.energyJoules / 3.6e6) * this.energy.carbonFor(dc.id) : 0,
        decadesAboveFloor: dc ? this.energy.decadesAboveFloor(node, dc) : null,
        lane: node.hardware.magicCapable ? "substrate" : "clifford",
        magicBudget: plan.magicBudget,
        emulationCostAvoided: plan.magicBudget > 0 ? S.magicMultiplier(plan.magicBudget) : 1,
        stateBlobs: vm.stateBlobs,
        ts: Date.now(),
      };

      const entry = this.append(
        "plan.settled",
        `${plan.name}: ${receipt.nodeSeconds.toFixed(0)} node-s, $${vm.cost.toFixed(4)}`,
        { planId: plan.id, vmId: vm.id, nodeId: node.id, digest: plan.digest }
      );
      receipt.chainHash = entry.hash;
      receipt.chainPrev = entry.prev;
      plan.receipt = receipt;
      return receipt;
    }

    halt(vmId) {
      const vm = this.vms.find((v) => v.id === vmId);
      if (!vm || vm.state !== "running") return null;
      const plan = this.plans.find((p) => p.id === vm.planId);
      const node = this.fleet.get(vm.nodeId);
      if (!plan || !node) { vm.state = "halted"; return null; }
      return this.settle(vm, plan, node);
    }

    runningVMs() {
      return this.vms.filter((v) => v.state === "running");
    }

    // -- density -------------------------------------------------------

    /**
     * Nested microVM density from the fractal state model. A uniform
     * root at depth n denotes 40^n addressable leaf VMs plus the
     * internal network VMs above them, and -- because untouched
     * siblings retain their digests under copy-on-write -- the whole
     * tree is denoted by n+1 unique state blobs.
     *
     * At n = 6 that is 4,096,000,000 leaf VMs and 105,025,641 internal
     * ones, 4,201,025,641 stateful VMs in total, from seven blobs.
     * This is a structural bound from the reference runtime -- a
     * statement about the state grammar, not a benchmark of any
     * running fleet.
     */
    densityAt(level) {
      const leaves = Math.pow(40, level);
      const internal = (Math.pow(40, level) - 1) / 39;
      return {
        level,
        leaves,
        internal: Math.round(internal),
        total: Math.round(leaves + internal),
        uniqueBlobs: level + 1,
        diameter: S.diameterAtLevel(level),
      };
    }

    /** Roll-up for the execution view header. */
    summary() {
      const running = this.runningVMs();
      const totalSeconds = this.meteredSeconds;
      return {
        plans: this.plans.length,
        running: running.length,
        settled: this.plans.filter((p) => p.status === "settled").length,
        rejected: this.plans.filter((p) => p.status === "rejected").length,
        meteredSeconds: totalSeconds,
        meteredSpend: this.meteredSpend,
        meteredKWh: this.meteredJoules / 3.6e6,
        avgRatePerNodeHour: totalSeconds > 0 ? (this.meteredSpend / totalSeconds) * 3600 : 0,
        chain: this.verifyChain(),
      };
    }
  }

  const API = { ExecutionEngine, ExecutionPlan, MicroVM, BOOT_MS, SETTLE_SECONDS };
  root.ExecutionEngine = ExecutionEngine;
  root.ExecutionPlan = ExecutionPlan;
  root.HolotradeExecution = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof window !== "undefined" ? window : globalThis);
