# HoloTrade eight-way execution frontier — 2026-08-25

This note records the implementation pass that followed the first correction-aware `Projection -> Execution -> Emission` closure. The rule throughout is evidence separation: an exact finite W(3,3) fact, a deterministic simulator invariant, a cryptographic signature, an external signed receipt, a runtime attestation, and a physical-network claim are different evidence classes.

## Baseline entering this pass

The repository already had:

- exact level-1 `W(3,3) = SRG(40,12,2,4)` substrate logic;
- node-second pricing and deterministic fleet simulation;
- immutable `ExecutionPlan` semantics with artifact pins, explicit grants, validity windows and replay nonces;
- correction-aware evidence records and fail-closed evidence policies;
- `Projection -> Execution -> Emission` closure;
- real SHA-256 transition certificates with exact W(3,3) route witnesses;
- explicit separation between historical settlement validity and current evidence admissibility.

The checkpoint `908c575` was green before this pass began.

---

## 1. Local-to-global certificate/policy gluing

**Implementation:** `js/gluing.js`

W33-Theory's strongest UOR-style bridge is a genuine local-to-global result: exact local sections overlap compatibly and glue to one unique global section. HoloTrade now uses that pattern generically.

A local section contains a nested patch such as:

```text
policy:       execution.region=US, execution.network=deny
capability:   execution.region=US, node.accelerator=gpu
residency:    execution.network=deny, node.accelerator=gpu
```

The gluing kernel recursively flattens paths, compares canonical values on every overlap, verifies required coverage, and emits one deterministic global section only if every overlap agrees.

There is intentionally no last-writer-wins rule. `US` versus `EU` on the same path is a hard conflict.

**Status:** regression-tested prototype invariant.

---

## 2. Capability-transition market

**Implementation:** `js/capability-market.js`

A vendor capability is now represented as an immutable resource rather than a mutable registry flag. A node capability profile is also an immutable resource.

Applying a capability becomes:

```text
old node profile + vendor capability resource
        -> capability Projection
        -> evidence-gated ExecutionPlan
        -> settled receipt
        -> emitted next-generation node profile
```

The old profile remains unchanged. The emitted profile records the union of capabilities, evidence references, generation, vendor, offer identity/digest and modeled transition price.

`CapabilityExchange` can rank compatible offers against a required capability set. `CapabilityTransitionEngine` converts the selected offer into the existing Projection machinery instead of creating a second execution path.

**Boundary:** this does not install firmware, reconfigure silicon, enforce licensing, or attest hardware state.

**Status:** end-to-end simulator regression-tested prototype state machine.

---

## 3. Real Ed25519 signature boundary

**Implementation:** `js/signing.js`

Transition certificates can now be wrapped in a real asymmetric Ed25519 signature using Node's `crypto` implementation. The signed payload is the canonical certificate byte string.

The envelope uses:

```text
payloadType
base64 canonical payload
Ed25519 signature
SHA-256 key id
SPKI public key
```

and signs DSSE-style pre-authentication bytes.

The module intentionally calls the wire object `holotrade.dsse-shaped.v1`, not DSSE/Sigstore conformance, because HoloTrade has not yet been tested against a reference DSSE implementation or transparency service.

This matches the general in-toto model that supply-chain steps, materials and products should be explicit and signed by authorized functionaries, but no in-toto interoperability claim is made yet.

**Boundary:** a valid Ed25519 signature authenticates the signed bytes/key. It does not prove where computation ran, establish hardware state, or provide key transparency/timestamping.

**Status:** real cryptography, local-key prototype integration; regression tested for valid signatures and tampering.

External reference checked during implementation:

- https://in-toto.io/docs/specs/
- https://in-toto.io/docs/getting-started/

---

## 4. GoMicroVM execution-contract adapter

**Implementation:** `js/gomicrovm-adapter.js`

The adapter maps a HoloTrade plan into the current documented mvm/GoMicroVM security vocabulary:

- pinned artifact digests;
- deny-by-default network/service/secret authority;
- policy references;
- nonce and validity window;
- seccomp posture (`minimal` absent network authority, `network` when network is requested);
- required audit-chain signing flag;
- redacted invocation metadata;
- resource/time/price constraints.

It also emits a payload-ready `mvmctl run --dry-run --json` descriptor and parses supplied signed receipts into HoloTrade evidence.

Current GoMicroVM documentation states that `mvmctl run --receipt` writes a signed receipt with invocation hashes, output hashes and exit status; raw argv, env values, stdout and stderr are not stored. It separately describes signed execution plans, policy references, seccomp posture and audit-chain signing.

The HoloTrade adapter therefore separates:

```text
receipt signature verified
contract binding verified
successful exit reported
runtime/hardware attestation separately verified
```

A signed receipt alone is **not** labeled remote or hardware attestation.

**Boundary:** this repository does not invoke `mvmctl`, Firecracker, Nix, the guest agent or the hosted control plane in CI.

**Status:** payload-ready offline adapter with tested evidence semantics; deployment not implemented.

External reference checked during implementation:

- https://gomicrovm.com/reference/cli-commands/
- https://gomicrovm.com/guides/networking/

---

## 5. Exact W33 spread scheduling and topology shadow pricing

**Implementation:** `js/w33-scheduler.js`

The scheduler reconstructs W(3,3) spreads directly from the exact 40 four-point lines. One spread is ten pairwise-disjoint lines covering all 40 points.

For projection inputs and a candidate execution node it now derives:

```text
resource UOR point
    -> exact W33 route
    -> unique line for every route edge
    -> line-operation demands
    -> conflict-free spread frames
```

A frame only schedules line operations drawn from one spread, so selected lines are site-disjoint by construction.

`LineCongestionLedger` adds an experimental convex marginal shadow cost to already-loaded line contexts. `rankPlacement()` starts from the existing economic placement candidates, generates the exact W33 frame witness for each candidate, and reranks using the modeled line congestion cost.

This makes topology participate as a concrete schedule/certificate instead of only a scalar coherence score.

**Boundary:** the shadow price is a scheduling heuristic over exact combinatorics. It is not measured link congestion, network throughput or a physical tariff.

**Status:** exact finite carrier + regression-tested scheduling/market heuristic.

---

# Three additional outside-the-box integrations

## 6. Transitive lineage quarantine

**Implementation:** `js/lineage.js`

A correction to an ancestor resource should affect downstream reuse even when descendant receipts were historically valid.

`ResourceLineage` builds the immutable emission DAG and supports:

- ancestors;
- descendants;
- cycle refusal;
- append-only provenance;
- quarantine propagation.

If resource `A` becomes epistemically unsafe and `B` consumed `A`, then both `A` and `B` remain in history but can be marked non-reusable. The correction propagates through every descendant without deleting or editing settled transitions.

This is the operational form of the project's research correction discipline:

> preserve history; change current admissibility.

**Status:** regression-tested prototype invariant.

---

## 7. Deterministic re-execution challenge market

**Implementation:** `js/challenge-market.js`

For a transition explicitly declared deterministic, a buyer/challenger can compare an independent replay emission against the certificate's real SHA-256 canonical emission digest.

A match confirms the content identity. A mismatch produces a correction-ready evidence record that can invalidate the evidence references which admitted the original computation.

The original certificate is not edited.

The challenge object also contains a modeled bounty ledger to expose the future economic mechanism: verification can itself become a purchased service.

**Boundary:** no money moves in this prototype, and exact-output challenges are refused unless the transition is declared deterministic.

**Status:** regression-tested prototype market/evidence state machine.

---

## 8. Correction-aware certified-result cache

**Implementation:** `js/certified-cache.js`

Because a Projection digest commits to its input resources, transformation, authority ceiling and evidence policy, it can serve as an exact cache key for deterministic work.

A cached result is reusable only when all of the following remain true:

1. the transition certificate still validates;
2. any attached Ed25519 envelope still verifies;
3. current evidence re-evaluation succeeds;
4. the output resource is not quarantined by lineage.

If all pass, HoloTrade can return the immutable previously emitted resource and record the node-seconds avoided instead of scheduling duplicate compute.

A later evidence correction turns the same entry into `EVIDENCE_STALE`; a lineage quarantine turns it into `LINEAGE_QUARANTINED`.

This is a potentially important market feedback loop: stronger proof and deterministic content addressing can reduce future compute demand rather than merely adding audit overhead.

**Status:** regression-tested in-memory prototype cache.

---

# Integration test

`tests/frontier.test.js` exercises all eight ideas together with the existing HoloTrade simulator.

The suite covers:

- compatible and incompatible local-section gluing;
- a real capability-profile transition through placement, launch, metering and settlement;
- Ed25519 signing and tamper rejection;
- GoMicroVM contract/redaction/receipt evidence boundaries;
- W33 spread enumeration, full 40-site cover, conflict-free scheduling and shadow-priced placement;
- two-stage lineage and transitive quarantine;
- successful and mismatching deterministic replay challenges;
- certified cache hits followed by evidence-staleness and lineage-quarantine refusal.

The first full frontier integration commit (`76ed263`) passed GitHub Actions, including Node tests and RTL formal/synthesis. Subsequent evidence-boundary cleanup keeps the same suite as the gate.

---

# What changed conceptually

Before these passes the core economic object was approximately:

```text
named capacity -> metered execution -> receipt
```

It is now closer to:

```text
compatible local claims
       |
       v
committed input resources + capability state + bounded authority + evidence floor
       |
       v
Projection
       |
       +--> exact W33 scheduling witness / congestion shadow price
       |
       +--> GoMicroVM-shaped execution contract
       v
metered execution
       v
immutable emission + SHA-256 transition certificate
       |
       +--> optional Ed25519 signature
       +--> re-execution challenge
       +--> lineage propagation
       +--> certified deterministic reuse
       v
next Projection
```

The important separation remains:

| Claim | Current evidence level |
|---|---|
| W(3,3) 40 points/40 lines, adjacency, diameter 2, `mu=4` | exact finite computation/repository certificate |
| spread-frame scheduling over those lines | exact carrier + deterministic algorithm |
| fleet placement / congestion shadow price | simulator/model |
| capability market | prototype state machine |
| Projection -> Execution -> Emission | prototype execution semantics + regression tests |
| SHA-256 certificate content address | real cryptographic digest |
| Ed25519 certificate signature | real local asymmetric signature |
| GoMicroVM contract | offline adapter based on current public docs |
| GoMicroVM execution in HoloTrade CI | not implemented |
| Firecracker execution in HoloTrade CI | not implemented |
| remote/hardware attestation | not implemented unless supplied and separately verified by a future adapter |
| physical W33 network | not implemented |
| challenge bounty settlement | accounting model only |
| distributed certified cache | not implemented |

This boundary is intentional: the architecture can become more capable without allowing stronger words than the evidence supports.
