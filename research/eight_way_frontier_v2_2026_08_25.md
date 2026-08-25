# Eight-way frontier v2 — 25 August 2026

This packet records the second execution pass across HoloTrade's eight frontier modules. It is intentionally evidence-scoped: exact finite-geometry results, cryptographic verification, simulator invariants, external-contract alignment, and unbuilt production controls remain distinct.

## 1. Evidence-aware local-to-global gluing

`js/gluing.js` now separates two predicates:

1. **structural compatibility** — local sections agree on every overlap and cover required paths;
2. **current admissibility** — the evidence supporting those sections still satisfies the selected EvidenceLedger policy.

A later evidence correction can therefore make a structurally valid global section inadmissible without changing its original structural digest. This is the same history/current-validity separation used by execution certificates.

## 2. Exact capability bundle market

`js/capability-market.js` now solves the compatible minimum-price capability bundle exactly over the required capability set, breaking ties by fewer offers and then lexical offer identity. The selected offers become inputs to one atomic capability-transition Projection, so the resulting node profile advances by one immutable generation rather than a sequence of mutable flags.

The optimizer operates on modeled offer prices. It is not a deployed procurement or licensing system.

## 3. Threshold DSSE trust

`js/signing.js` retains the local self-contained Ed25519 envelope for prototype compatibility and adds a strict DSSE JSON envelope plus t-of-n verification against application-supplied trusted public keys.

Critical trust rule: DSSE `keyid` is treated only as an unauthenticated lookup hint. It never becomes authority by appearing inside the envelope. A signature counts only when it cryptographically verifies under a public key supplied by the caller's trust policy.

This is real Ed25519 + DSSE pre-authentication encoding. It is not a CA, transparency log, key-distribution system, remote attestation, or Sigstore deployment.

## 4. GoMicroVM admission reconciliation

`js/gomicrovm-adapter.js` now checks a caller-supplied runtime/admission snapshot against the compiled HoloTrade contract. It fails closed on contract/nonce mismatch, expired windows, artifact re-verification drift, authority drift, policy-ref drift, weaker seccomp posture, a reported guest network device, unsigned required audit chain, or unsealed rootfs.

The adapter still does not authenticate the source of the snapshot, invoke `mvmctl`, launch Firecracker, or infer hardware attestation. Source authentication remains a separate evidence class.

## 5. Complete W(3,3) spread scheduler census

`js/w33-scheduler.js` now computes the complete spread layer rather than a truncated catalogue. The executable certificate checks the same exact finite facts already encoded in W33-Theory's symplectic spread audit:

- exactly **36** spreads;
- every spread is **10** pairwise-disjoint isotropic lines covering all **40** points;
- every isotropic line occurs in exactly **9** spreads;
- at any anchor point there are **4** incident lines and the 36 spreads divide into four sectors of **9**.

Scheduling still uses these exact structures as a model carrier; this does not promote them to measured physical-network throughput or quantum-hardware performance.

## 6. Automatic correction-driven lineage quarantine

`js/lineage.js` can now bind emitted resources to their transition certificate and settlement-time evidence contract. `refreshEvidence()` re-evaluates certified roots against the current ledger and automatically quarantines every stale root and all descendants.

Quarantine is monotone and append-only: historical nodes/emissions are never erased.

## 7. Semantic replay challenges

The most important conceptual correction in this pass is in `js/challenge-market.js`.

A transition certificate's `element.digest` is SHA-256 of the **whole emission/provenance record**. Independent executions naturally have different plan IDs, receipt IDs, nodes, and settlement provenance, so comparing whole-emission hashes is not a valid deterministic-result test.

The challenge market now separates:

- **provenance identity** — the certificate element SHA-256;
- **semantic result identity** — a declared canonical `emission.output.metadata.resultDigest` SHA-256.

Certified independent replay verifies each replay emission against its own transition certificate, requires the same Projection digest, and then compares semantic result commitments. A quorum can contain distinct execution provenance while confirming the same semantic result. Any certified semantic disagreement makes correction-ready evidence; a legacy provenance-only mismatch is manual-review evidence only.

## 8. Auditable certified reuse

`js/certified-cache.js` now supports threshold-trusted DSSE policy and issues immutable reuse receipts. A successful cache admission commits to the source transition certificate, source element, output digest, current evidence decision, lineage status, signature verification mode, and modeled node-seconds avoided.

The receipt explicitly states that no recomputation occurred. Avoided node-seconds are accounting inside the simulator, not automatically equivalent to current-market savings.

## Regression boundary

`tests/frontier-v2.test.js` independently exercises all eight v2 invariants while the original `tests/frontier.test.js` remains active. The older replay test is intentionally retained as a legacy provenance-mode regression and now verifies that provenance disagreement alone does **not** automatically invalidate semantic evidence.

The implementation therefore supports both backwards compatibility and a stricter new semantic-replay path without conflating the two.
