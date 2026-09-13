# Exact dual witnesses at the signed-delivery boundary

The existing decoder transaction supports an explicit `dual-one-step-v1` policy.
In this mode a worker must supply actual vectors and a feasible rational dual
witness before a result can enter signed delivery. Legacy policy serialization
and its summary-cost semantics are preserved.

Add these fields when constructing a policy with `verifyDecoderPolicy`:

    proofMode: 'dual-one-step-v1'
    geometryDigest: sha256(canonicalLines)
    permittedMoveDigests: [sha256(approvedCircuitVector), ...]

The policy's existing `inputPreimageDigest` and `fiberDigest` must identify the
actual initial vector and line image. The permitted list is bounded and included
in the policy digest. It is supplied by the trusted policy creator; the verifier
does not regenerate the entire circuit library.

The receipt must include `dualWitness` containing `lines`, `start`, `end`, `move`,
`moveDigest`, `lineImage`, and forty rational strings in `dual`. Integer coordinates
must be safe JavaScript integers; arithmetic checks use BigInt, with reduced
rational arithmetic for the dual. Rational text is bounded to 128 characters per
coordinate. Retain the complete witness for later independent verification; signed
delivery carries its digest rather than copying all vectors.

The verifier checks the pinned incidence geometry, four distinct points per line,
four incident lines per point, the actual input/output/fibre identities,
`start+move=end`, both incidence images, and all forty dual inequalities. Equality
of the endpoint l1 norm and the feasible dual value proves optimality. Since the
four-regular incidence fixes the coordinate sum, negative mass is
`(l1 norm - coordinate sum)/2`; its minimum follows from the same equality.
The actual negative masses must agree with the receipt and policy.

This initial mode accepts exactly one strictly descending permitted circuit move.
It rejects missing witnesses, forged endpoints, altered starts/moves/geometries,
unapproved moves, unsafe integers, malformed rationals, nonzero duality gaps and
cross-input replay. Policies cannot silently drop the proof requirement without
changing their identity. Equivalent rational encodings remain valid.

`decoderDualVerified` and `decoderDualWitnessDigest` enter signed delivery only
after verification. The existing decoder-result digest also commits the checked
proof identity. Tests run both real pre-existing escape witnesses, eleven malformed
or substituted proof cases, a rational perturbation below floating precision,
policy downgrade and permitted-move substitution, and three original legacy cases.
All six test functions pass. Attestation verdicts are simulated test signatures;
this does not demonstrate a real measured-boot event.

Run:

    python3 -S analysis/export_octet_dual_transaction_fixture.py --check
    node --test tests/w33-certified-decoder-transaction.test.js

The exporter derives the fixture from canonical geometry and the original
`octet_dual_gap_receipts.json`; the workflow checks that provenance. This extends
that prior solver-free mathematical certificate into the transaction path. It
adds no new trap, Graver completeness theorem, arbitrary multi-step history
verification, physical evidence or quantum speedup claim.
