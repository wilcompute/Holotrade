# Projection -> Execution -> Emission: closing the HoloTrade state transition

**Status:** implemented prototype architecture with regression tests. This note separates repository facts, supplied-source architecture, external web verification, and new design synthesis.

## 1. The gap this pass found

At the start of this pass HoloTrade already contained four strong but separate pieces:

1. an exact 64-bit UOR mixed-radix object/address codec (`js/uor.js`),
2. a scoped `ExecutionPlan` with pinned artifact digests, grants, nonce, validity window, admission, node-second metering and settlement (`js/execution.js`),
3. a correction-aware evidence ledger and fail-closed evidence policy adapter (`js/evidence.js`, `js/execution-evidence.js`), and
4. execution receipts plus an explicit non-cryptographic audit/integrity boundary.

What it did **not** contain was a first-class state transition connecting those surfaces. A resource could have a UOR, and a plan could execute, but the output of a settled plan was not itself an immutable resource that could become the input to the next plan.

`js/projection.js` closes that loop:

```text
ResourceRef[]
    |
    v
Projection --compile--> evidence-bound ExecutionPlan
    |                            |
    |                            v
    |                     admit -> execute
    |                            |
    |                            v
    +---------------------- settlement receipt
                                 |
                                 v
                         immutable Emission
                                 |
                                 v
                         output ResourceRef
                                 |
                                 +----> next Projection
```

The important product transition is therefore no longer merely:

```text
capacity -> execution -> bill
```

but:

```text
named state + bounded authority + evidence contract
    -> named execution
    -> metered transition
    -> named resulting state
```

That is a materially more composable primitive for agents, pipelines, data products and capability marketplaces.

## 2. Supplied-source architecture that motivated the shape

### HLIX / HCP material

The supplied **"HLIX-A Universal Object Reference Platform (HCP)"** document describes a model in which content-addressed resources are assembled by a projection engine into platform containers and operations follow a **Projection -> Execution -> Emission** lifecycle. Its listed base container kinds include Component, Service, Policy, View, Dataset and Receipt.

HoloTrade does **not** claim HCP conformance. The useful architectural invariant taken from the supplied document is narrower: the result of execution should be a newly emitted immutable resource/receipt, rather than an unstructured side effect.

### ArcLEAP / HLIX verified-compute material

The supplied **HLIX verified-compute collaboration** document separates object/workload identity, committed workload state and independently sealed runtime/physical evidence. The HoloTrade evidence layer translates that separation into an explicit three-digest execution evidence BOM (`identityDigest`, `stateDigest`, `runtimeDigest`). The current implementation deliberately labels these digests `DEMO_EVIDENCE_DIGEST`; they are not signatures or remote attestations.

### DTR-HLIX / VCBOM material

The supplied DTR-HLIX architecture describes a **Verified Compute Bill of Materials** spanning infrastructure identity, attestations/control evidence, measured capability, operational limits, provenance and policy eligibility. It also describes two linked marketplace surfaces: compute capacity and vendor capabilities that change a node's verified profile.

The new projection kernel is deliberately compatible with that *shape*: a future capability can be represented as an input resource to a projection, and the resulting emitted resource can carry a new capability/profile commitment. That is a design path, not a claim that DTR-HLIX is integrated today.

### Oko materials

The supplied Oko documents emphasize schema-driven execution, state/version commitments, receipts, jurisdictional boundaries and portable proofs. HoloTrade does not import the throughput/scaling claims as facts. The relevant design takeaway is that execution state transitions should be explicit, versioned and receipted.

## 3. External verification: GoMicroVM boundary

The current GoMicroVM website (`https://gomicrovm.com/`) describes agent execution under an explicit execution contract: artifact identity known before launch, scoped grants, policy references, a validity/nonce boundary, deny-by-default authority and an audit trail. Its architecture page separates build, admission, runtime and guest-control boundaries.

That is directly compatible with HoloTrade's existing `ExecutionPlan` vocabulary. `ProjectionEngine.compile()` therefore does **not** invent a second runtime contract. It compiles a projection into the plan structure HoloTrade already uses.

This repository still does **not** claim a deployed GoMicroVM integration, a Firecracker launch, cryptographic plan signatures, dm-verity verification or hardware attestation.

## 4. W33-derived design rule: history is immutable; admissibility is current

The current `W33-Theory/w33_paper.tex` manuscript explicitly preserves withdrawn claims alongside the measurements or attribution corrections that overturned them, and directs readers to the current claims ledger before relying on chronological sections. Recent W33 commits also record candidate laws that disappeared under larger samples rather than deleting the failed result.

That suggests a stronger operational rule for an execution market:

> **Never rewrite the evidence record that justified an old decision. Recompute whether that evidence is admissible now.**

The HoloTrade evidence ledger implements exactly that distinction. A record keeps its original digest; a later record may supersede or invalidate it; `evaluate()` resolves the *effective* status at admission time. Thus historical settlement remains auditable while future execution can fail closed against corrected evidence.

## 5. New synthesis implemented in `js/projection.js`

### 5.1 Immutable resource references

`ResourceRef` binds:

- resource identity,
- resource kind and semantic role,
- a declared content digest,
- a UOR address,
- metadata,
- a deterministic reference digest.

The UOR mapping remains prototype-grade because `UORAddress.from()` uses the current deterministic demo hash construction.

### 5.2 Projection identity

A `Projection` binds:

- named input resources,
- workload/service class,
- maximum authority (network/services/secrets),
- evidence references and minimum evidence policy,
- output kind,
- metadata.

Its digest is therefore a commitment to **what state is being transformed under what authority and evidence contract**, not just to executable bytes.

### 5.3 Authority monotonicity

This is the most important security invariant added in this pass:

> Runtime compilation may **narrow** grants and **strengthen** evidence policy, but it may not widen authority or weaken evidence requirements.

Concretely:

```text
projection grants = maximum authority ceiling
runtime grants    subset of that ceiling
runtime policy    >= projection evidence policy
runtime artifacts forbidden unless declared as projection inputs
```

This removes an ambient-authority escape hatch. A caller cannot compile an apparently safe projection and then smuggle in an extra network destination, secret, service or uncommitted artifact at launch time.

### 5.4 Transitive plan binding

Compilation pins both:

1. the projection digest, and
2. every input resource digest

into `ExecutionPlan.artifacts`.

Because the projection digest itself commits to roles, grants and evidence policy, the existing plan digest transitively commits to the higher-level state transition without changing the basic execution engine.

### 5.5 Emission closure

A successful settled receipt can emit an immutable output resource whose content commitment binds:

- projection digest,
- parent resource digests,
- plan digest,
- receipt/evidence commitment,
- node identity,
- delivered node-seconds,
- output metadata.

The output `ResourceRef` can be passed directly into a second `Projection`. Regression tests exercise this closure.

Failed or halted receipts do not silently become reusable output resources.

### 5.6 Idempotence and conflict detection

Repeating the exact same emission request returns the same immutable emission. Trying to emit different content for the same `(projection, plan, receipt)` transition is rejected as a conflict instead of overwriting history.

This is the state-transition analogue of the W33 correction discipline: history is append-only, not mutable.

## 6. Evidence/status table

| Statement | Current status |
|---|---|
| W(3,3) level-1 finite graph facts used by `js/substrate.js` | exact/repository-certified in this project |
| Evidence supersession changes future admission without rewriting historical records | regression-tested prototype invariant |
| Projection authority cannot widen at runtime | regression-tested prototype invariant |
| Projection evidence policy cannot weaken at runtime | regression-tested prototype invariant |
| Projection/input digests are pinned into the execution plan | regression-tested prototype invariant |
| Settled emission becomes the input to a subsequent projection | regression-tested prototype invariant |
| HCP/HLIX interoperability | **not implemented** |
| GoMicroVM deployment / Firecracker execution | **not implemented** |
| cryptographic content signatures | **not implemented** |
| remote/hardware attestation | **not implemented** |
| portable zero-knowledge/private receipt proofs | **not implemented** |
| physical Holonet execution | **not implemented** |

## 7. The deeper product consequence

This changes the natural HoloTrade instrument.

A node-second remains the metered settlement unit, but the economically useful object can now be described as a **bounded state transition**:

```text
(input resource commitments,
 projection commitment,
 authority ceiling,
 evidence policy,
 named capacity,
 delivery window)
        ->
(output resource commitment,
 receipt commitment,
 evidence envelope)
```

That opens a path to trading outcomes/capability-bound transitions while still settling the underlying compute in node-seconds. It also creates a clean place to attach future cryptographic signatures, runtime attestations, external anchors and vendor capability updates without collapsing those distinct evidence classes into one vague word like "verified."

## 8. Reproducibility

The new regression files are:

- `tests/evidence.test.js`
- `tests/projection.test.js`

`package.json` now runs every `tests/*.test.js` file so the new contract is part of CI rather than dead code.

The current browser application intentionally remains on the existing execution UI until the new lifecycle gets a dedicated projection/evidence surface; the module is implemented and testable first so product presentation cannot outrun the execution semantics.
