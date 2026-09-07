# Continuation-bound W33 attestation

## Problem

The existing Holotrade measured-boot layer binds a trusted verifier verdict to:

- the exact W33 execution passport;
- the GoMicroVM deployment digest;
- the runtime public-key digest;
- the machine type/logical dimension;
- the capability epoch and revocation root.

That was sufficient while "the VM" was identified by the admitted passport and
deployment.

The W33 HoloVM process kernel now makes a stricter distinction:

\[
\boxed{\text{value snapshot identity} \neq \text{process continuation identity}.}
\]

Two forks may share the same recoverable snapshot bytes and still be different logical
processes. Therefore a hardware-backed runtime verdict that binds only the passport
does not yet say which fork/generation the runtime is executing.

## Closure

`js/w33-continuation-attestation.js` extends the existing challenge, rather than
replacing it.

The new challenge commits:

\[
(\text{base measured-boot challenge},
 \text{continuation root},
 \text{process id},
 \text{generation}).
\]

The base challenge continues to commit passport, deployment, runtime key, machine
type, capability epoch and revocation state.

A signed TPM2/SEV-SNP normalized verifier verdict is accepted only when its
`challengeDigest` matches this continuation-bound challenge.

Therefore:

\[
\boxed{
\text{hardware verdict for }C_a
\not\Rightarrow
\text{hardware verdict for }C_b
}
\]

even when \(C_a\) and \(C_b\) have the same snapshot value.

The tests generate real Ed25519 verifier keys and prove that changing either the fork
or its generation changes the challenge digest and makes the old signed verdict fail
with `ATTESTATION_CHALLENGE_MISMATCH`.

## Receipt binding

The continuation identity is propagated into both:

- `w33ContinuationAttestation` receipt metadata; and
- the generic `holotrade.hardware-evidence.v1` evidence item.

The receipt therefore commits:

- passport id;
- deployment digest;
- runtime public-key digest;
- launch measurement / TCB / signer-chain verdict;
- continuation root;
- process id;
- generation.

This closes the operational gap between "approved runtime" and "approved runtime
executing this exact immutable process continuation."

## Trust boundary

This wrapper does not parse vendor attestation evidence. It reuses the existing
measured-boot contract:

1. a vendor-aware verifier checks TPM2 or SEV-SNP evidence;
2. that verifier emits a normalized verdict;
3. Holotrade verifies the Ed25519 signature on the verdict;
4. the verdict must match the continuation-bound challenge.

Synthetic tests exercise the cryptographic binding, not real AMD certificates or a
live TPM. Production hardware-backed status still requires the existing native
verifier path and policy.

## Architectural consequence

The deployment identity hierarchy is now explicit:

```text
guest image
  -> execution passport
     -> deployment/runtime measurement
        -> process id
           -> continuation root + generation
              -> signed execution receipt
```

This is the right level for a distributed HoloVM worker. A worker may be replaced or
restarted, but a receipt for a state transition is not transferable to a different
continuation simply because the code/passport is identical.
