# Continuation-native HoloVM scheduling

## Result

Holotrade now schedules the immutable HoloVM process tuple

\[
(\text{continuation root},\text{process id},\text{generation})
\]

rather than treating a mutable VM/worker instance as the durable scheduling identity.

`scheduler/w33-continuation-scheduler.js` admits a worker only when four independent
conditions are satisfied:

1. its evidence level meets the request floor;
2. its runtime W33 topology binding is independently attested;
3. the required W33 points occur in that attested physical binding; and
4. the worker supplies the exact retained-union delta for the requested continuation.

Missing archive-overlap data is a hard rejection. The scheduler does not substitute a
deduplication percentage or a bit-width proxy.

## Cost object

For an eligible worker, the placement price is explicitly decomposed into

\[
C = C_{\rm compute}+C_{\rm retained}+C_{\rm transfer}+C_{\rm startup},
\]

with the retained and transfer terms using the exact continuation-specific marginal
payload bytes supplied by the archive/accounting layer.

This makes the scheduling object compatible with the W33 shared-snapshot result: two
continuations may have very different marginal storage cost despite equal apparent
state width.

## Worker migration theorem

Worker migration is deliberately weaker than process migration. The operation keeps

\[
(\text{continuation root},\text{process id},\text{generation})
\]

fixed while replacing the replay worker.

Because the continuation-attestation challenge also commits the worker runtime public
key, changing worker produces a different challenge digest. Therefore the old hardware
verdict cannot authorize the new worker:

\[
\boxed{
\text{same process continuation}
+\text{new worker}
\Longrightarrow
\text{new hardware attestation challenge}.
}
\]

This separates logical identity from deployment identity cleanly:

- **process identity** survives worker replacement;
- **runtime attestation identity** does not.

The scheduler refuses an attempted migration that substitutes a different continuation
root, process id, or generation.

## Evidence boundary

An exact W33 graph certificate is not runtime topology attestation. A cheap worker that
fails the evidence floor is not selected. A worker with abstract W33 point labels but no
attested physical binding is not dispatchable. A worker lacking exact retained-union
cost is not priced by guesswork.

The dedicated `W33 continuation-native scheduler` GitHub Actions workflow executes both
the scheduler tests and the continuation-bound hardware-attestation regression.
