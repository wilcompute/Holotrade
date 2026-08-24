// ======================================================================
// HOLOTRADE EXECUTION LAYER
//
// This module answers the question the whole product turns on:
// WHAT, EXACTLY, IS BEING BOUGHT AND SOLD?
//
// ---------------------------------------------------------------------
// It is not a VM node.
//
// Selling only "a VM node for an hour" hides useful execution detail.
// This module explores three reasons to expose a finer contract:
//
//   1. The hour is a billing artefact, not a physical one. It exists
//      because provisioning a conventional VM takes minutes, so an
//      hour is the smallest slice worth the scheduling overhead.
//      The simulator uses 171.5 ms as a declared cold-start assumption.
//      Firecracker benchmarks are hardware- and guest-dependent. The
//      boot charge is itemised, so the demo does not hide it inside an
//      hourly rate.
//
//   2. An hour cannot express the thing that actually varies. Grid
//      prices move every five minutes and go negative at 3 a.m. on
//      ERCOT. If your settlement granularity is an hour you have
//      thrown away the signal before you can price it. Per-second
//      energy pricing -- the core idea this exchange is built around --
//      benefits from a settlement unit finer than the quote horizon.
//
//   3. "A node for an hour" does not specify execution intent. A plan
//      can name artefact digests, network grants, secret references and
//      a validity window before boot. This prototype uses a deterministic
//      integrity seal to exercise those semantics; it is NOT a digital
//      signature or remote-attestation implementation.
//
// ---------------------------------------------------------------------
// So Holotrade's atomic tradeable unit is the NODE-SECOND, and its
// contract is the EXECUTION PLAN:
//
//     asset     the node        -- durable, has a genome and a health
//                                  record, is what you lease or own
//     contract  the plan        -- integrity-sealed, scoped,
//                                  time-boxed, tradeable before it runs
//     unit      the node-second -- what settles against the seeded
//                                  energy and node model
//
// A plan is a prototype contract object with a declared artifact digest,
// explicit grants and a metered receipt. Forward/option semantics are a
// design direction; this module does not implement those state machines.
//
// ---------------------------------------------------------------------
// ISOLATION AND DENSITY
//
// The browser simulates one isolated-microVM lifecycle per plan. A real
// deployment would still need a hypervisor, measured boot, immutable
// rootfs, deny-by-default networking, attestation and host hardening.
//
// Density comes from nested state: a uniform root over six levels
// denotes ~4.2 billion address labels using seven unique model blobs,
// state blobs, because untouched siblings keep their digests and a
// content-identical replay reuses every key. Copy-on-write over a
// content-addressed store, with mailbox delivery costing seven path
// blobs plus one receipt. That is a structural upper bound from the
// state grammar, not a built runtime or throughput measurement.
// ======================================================================

(function (root) {
  "use strict";

  const S = root.Substrate || (typeof require !== "undefined" ? require("./substrate.js") : null);

  // Declared simulator boot distribution. This is not a measurement of
  // the current host or a portable Firecracker benchmark.
  const BOOT_MS = { p50: 171.5, p95: 176.0, p99: 178.0, target: 150 };

  // Settlement granularity. A 171.5 ms fresh boot is 17.15% of a
  // one-second allocation, which is why cold start is itemised rather
  // than hidden. It falls below 1% of runtime after 17.15 seconds.
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

      // Declared artifact references. The prototype binds these strings
      // into the plan; it does not fetch or hash artifact bytes.
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

      // Security status is explicit. `signature` below is only a stable
      // prototype integrity seal; production needs a canonical encoding,
      // a real signing key, and a standard signature such as Ed25519.
      this.securityMode = "DEMO_INTEGRITY_SEAL";

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
        id: this.id,
        owner: this.owner,
        w: this.workloadId,
        a: this.artifacts.map((x) => x.digest).sort(),
        g: this.grants,
        vf: this.validFrom,
        vu: this.validUntil,
        nonce: this.nonce,
        s: this.requestedSeconds,
        n: this.nodeCount,
        max: this.maxPricePerNodeSecond,
        anchor: this.anchorAddress,
        t: this.magicBudget,
      });
      return S.hash32(preimage).toString(16).padStart(8, "0") +
             S.hash32(preimage + "|salt").toString(16).padStart(8, "0");
    }

    sign() {
      return `sig:${S.hash32(this.digest + this.owner).toString(16).padStart(8, "0")}`;
    }

    /** Verify nothing covered by the prototype integrity seal was edited. */
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
     *   4. no declared pin drift -- when the caller supplies an observed
     *      digest, it must match the declared digest
     *   5. the node declares the required capability: magic budget t > 0
     *      needs a magic-capable catalogue class, with no substitution
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
     * Prototype pin-drift hook. This compares declared and caller-supplied
     * observed digest strings; no artifact is fetched or hashed here.
     * Returns the name of the first mismatch, or null.
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
      this.auditLog = [];        // checksum-chained, newest first
      this.maxAudit = 400;
      this.lastChainHash = "0".repeat(8);
      this.replayStore = new Set();   // nonces already admitted
      this.meteredSeconds = 0;
      this.meteredSpend = 0;
      this.meteredJoules = 0;
    }

    // -- audit chain ---------------------------------------------------

    /**
     * Checksum-chained demo log. Each entry commits to its complete body
     * and the previous entry. This detects accidental/tampered edits in
     * the running prototype, but hash32 is not collision resistant and
     * this is not an externally anchored production audit log.
     */
    append(kind, detail, refs = {}) {
      const prev = this.lastChainHash;
      const ts = Date.now();
      const seq = this.auditLog.length + 1;
      const body = JSON.stringify({ seq, kind, detail, refs, ts });
      const hash = S.hash32(prev + body).toString(16).padStart(8, "0");
      const entry = { seq, ts, kind, detail, refs, prev, hash };
      this.lastChainHash = hash;
      this.auditLog.unshift(entry);
      if (this.auditLog.length > this.maxAudit) this.auditLog.pop();
      return entry;
    }

    /** Walk the chain, recompute every body checksum, and verify links. */
    verifyChain() {
      const ordered = [...this.auditLog].reverse();
      for (let i = 0; i < ordered.length; i++) {
        const entry = ordered[i];
        const expectedPrev = i === 0 ? entry.prev : ordered[i - 1].hash;
        const body = JSON.stringify({
          seq: entry.seq, kind: entry.kind, detail: entry.detail, refs: entry.refs, ts: entry.ts,
        });
        const expectedHash = S.hash32(entry.prev + body).toString(16).padStart(8, "0");
        if (entry.prev !== expectedPrev || entry.hash !== expectedHash) {
          return { ok: false, brokenAt: entry.seq };
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
        const boot = this.bootCostFor(node, q, plan.digest);
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
     * Declared cold-start cost model. A production implementation would
     * boot a kernel, verify a rootfs and rehash artifacts; this browser
     * charges modeled time and energy for those assumed operations.
     *
     * At 171 ms against a one-second settlement slice that is a 17%
     * overhead on a single second and 0.005% on an hour -- so the
     * exchange charges it once, explicitly, rather than smearing it
     * into the rate. A buyer running many short plans can SEE what
     * their fan-out costs them.
     */
    bootCostFor(node, quote, placementKey = "preview") {
      // Deterministic for a plan/node pair so preview and launch cannot
      // disagree during a demo merely because jitter was sampled twice.
      const sample = S.rng(`${placementKey}|${node.id}|boot`)();
      const jitter = 1 + (sample - 0.5) * 0.06;
      const ms = (node.hardware.kind === "photonic" ? BOOT_MS.p50 * 0.55 : BOOT_MS.p50) * jitter;
      const seconds = ms / 1000;
      const perSecond = quote.price / 3600;
      // The model assumes validation work runs the node near peak.
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
      // The current runtime starts exactly one VM on exactly one node.
      // Reject a gang request instead of billing nodeCount copies of a
      // single VM and calling that a multi-node launch.
      if (plan.nodeCount !== 1) {
        plan.status = "rejected";
        const reason = "multi-node gang placement is not implemented";
        this.append("plan.failed", `UNSUPPORTED_NODE_COUNT: ${reason}`, {
          planId: plan.id, nodeId: node.id, requestedNodes: plan.nodeCount,
        });
        return { ok: false, reason, code: "UNSUPPORTED_NODE_COUNT" };
      }
      const adm = plan.admissible(node, Date.now(), this.replayStore);
      if (!adm.ok) {
        plan.status = "rejected";
        this.append("plan.failed", `${adm.code}: ${adm.reason}`, {
          planId: plan.id, nodeId: node.id, code: adm.code,
        });
        return { ok: false, reason: adm.reason, code: adm.code };
      }
      const q = this.pricing.quote(node, {
        workloadId: plan.workloadId,
        anchorAddress: plan.anchorAddress,
      });
      if (!q.serviceable || q.price == null) {
        const reason = "node is no longer serviceable at launch";
        plan.status = "rejected";
        this.append("plan.failed", `UNSERVICEABLE: ${reason}`, { planId: plan.id, nodeId: node.id });
        return { ok: false, reason, code: "UNSERVICEABLE" };
      }
      const livePerSecond = q.price / 3600;
      if (plan.maxPricePerNodeSecond != null && livePerSecond > plan.maxPricePerNodeSecond) {
        const reason = `live rate ${livePerSecond.toFixed(8)} exceeded cap ${plan.maxPricePerNodeSecond.toFixed(8)}`;
        plan.status = "rejected";
        this.append("plan.failed", `PRICE_CAP: ${reason}`, { planId: plan.id, nodeId: node.id });
        return { ok: false, reason, code: "PRICE_CAP" };
      }
      this.replayStore.add(plan.nonce);
      this.append("plan.admitted", `${plan.name} -> ${node.id}`, {
        planId: plan.id, nodeId: node.id, digest: plan.digest, nonce: plan.nonce,
      });
      const boot = this.bootCostFor(node, q, plan.digest);
      const vm = new MicroVM(plan, node, boot.ms);
      vm.cost += boot.cost;
      this.meteredSpend += boot.cost;
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
     * Integrate every simulated run for dt seconds.
     *
     * Each integration interval uses the current modeled quote at that
     * site and node. The hourly-equivalent comparison rate is converted
     * to the delivered node-second unit for settlement.
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
        if (!q.serviceable || q.price == null) {
          settled.push(this.settle(vm, plan, node, {
            status: "service_halt",
            reason: "node became unserviceable during delivery",
          }));
          continue;
        }

        const perSecond = q.price / 3600;
        if (plan.maxPricePerNodeSecond != null && perSecond > plan.maxPricePerNodeSecond) {
          settled.push(this.settle(vm, plan, node, {
            status: "price_cap_halt",
            reason: `live rate ${perSecond.toFixed(8)} exceeded cap ${plan.maxPricePerNodeSecond.toFixed(8)}`,
          }));
          continue;
        }
        const remaining = Math.max(0, plan.requestedSeconds - vm.secondsRun);
        const deliveredSeconds = Math.min(Math.max(0, Number(dtSeconds) || 0), remaining);
        if (deliveredSeconds <= 0) {
          settled.push(this.settle(vm, plan, node));
          continue;
        }
        const slice = perSecond * deliveredSeconds * plan.nodeCount;
        vm.cost += slice;
        vm.secondsRun += deliveredSeconds;

        const dc = this.energy.datacenters.find((d) => d.id === node.dcId);
        const kw = (node.hardware.tdp / 1000) * (dc ? dc.pue : 1.2) * (0.32 + 0.68 * node.utilisation);
        const joules = kw * 1000 * deliveredSeconds * plan.nodeCount;
        vm.energyJoules += joules;

        this.meteredSeconds += deliveredSeconds * plan.nodeCount;
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
     * The receipt reports what this simulator delivered: node-seconds,
     * modeled spend, energy and carbon. A thermodynamic comparison is
     * emitted only when the energy model can supply one with compatible
     * operation boundaries; the current catalogue deliberately returns
     * null rather than compare unlike units.
     */
    settle(vm, plan, node, outcome = { status: "settled", reason: null }) {
      vm.state = "halted";
      plan.status = outcome.status === "settled" ? "settled" : "rejected";
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
        outcome: outcome.status,
        outcomeReason: outcome.reason || null,
        ts: Date.now(),
      };

      const entry = this.append(
        outcome.status === "settled" ? "plan.settled" : "plan.halted",
        `${plan.name}: ${receipt.nodeSeconds.toFixed(0)} node-s, $${vm.cost.toFixed(4)}` +
          (outcome.reason ? `; ${outcome.reason}` : ""),
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
     * Nested namespace density from the fractal state model. A uniform
     * root at depth n denotes 40^n addressable leaf labels plus the
     * internal labels above them, and -- because untouched
     * siblings retain their digests under copy-on-write -- the whole
     * tree is denoted by n+1 unique state blobs.
     *
     * At n = 6 that is 4,096,000,000 leaf labels and 105,025,641
     * internal ones, 4,201,025,641 model objects in total, from seven
     * blobs. This is an illustrative state-grammar count, not a built
     * runtime, capacity claim, or benchmark of a running fleet.
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
