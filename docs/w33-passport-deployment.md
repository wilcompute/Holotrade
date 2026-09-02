# W33 execution passport and heterogeneous recovery

HoloTrade now has one immutable deployment object that can bind the W33 machine
identity to the rest of the execution proof surface.

`js/w33-passport-deployment.js` commits to:

- signed execution-plan digest;
- immutable W33 profile digest;
- carrier (`circuit216/steinberg81` or `paired-hemisystem216/steinberg64`);
- logical dimension (81 or 64);
- launched VM identity and optional GoMicroVM deployment digest;
- guest-image digest;
- Merkle memory root and memory-capability digest;
- typed component-link digest;
- packet-refinement digest;
- retained-history root and erasure policy;
- non-Clifford magic budget;
- distinct Clifford-lift and projective/Weyl namespaces.

The SHA-256 passport is an integrity commitment. It is not a signature or remote
attestation by itself. `runtime/receipt.js` signs/encodes the delivery receipt
surface, and the passport binding is placed inside that signed metadata.

## Recovery law

Recovery is intentionally split into two different operations.

### Full restore

A full checkpoint is carrier-local. Restoring an ST81 machine onto ST64, or the
reverse, is rejected. The two 216-state carriers are construction-time machine
types, not two runtime gauges of one state space.

### Neutral continuation

An application can recover on the other carrier only at a typed
`SYSCALL_BOUNDARY`. The handoff must carry a content-addressed neutral-state
digest. The target starts a new machine identity. This represents application
continuation from carrier-neutral classical state, not conversion of an ST81
quantum state into an ST64 quantum state.

This split gives HoloTrade a practical heterogeneous failover model without
invalidating the W33 carrier-fork theorem.
