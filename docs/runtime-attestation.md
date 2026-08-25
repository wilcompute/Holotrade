# Runtime execution and attestation boundary

This packet is the first HoloTrade runtime path that uses standard
cryptography and host observations rather than the browser prototype's demo
checksum. It does four concrete things:

1. hashes the exact kernel, root filesystem, drive, output, quote, TPM-log, or
   SEV-SNP-report bytes with SHA-256;
2. probes Firecracker/KVM, TPM measured-boot, IMA, SEV-SNP, RAPL, and Kepler as
   separate capabilities with typed failure states;
3. configures and starts Firecracker through its Unix HTTP API only after the
   mandatory host and artifact checks pass;
4. signs the delivery payload as a tagged COSE_Sign1 object with Ed25519 and
   verifies it against a caller-supplied trust key.

The implementation is under `runtime/`; the regression certificate is
`tests/runtime-attestation.test.js`.

## The key honesty boundary

A signed receipt is not automatically hardware-attested. These are distinct:

| Observation | What HoloTrade records | What it does **not** claim |
|---|---|---|
| Firecracker binary answers `--version` | executable is present | a guest booted |
| Unix API answers and accepts machine config | control plane works | KVM is accessible |
| `/dev/kvm` exists | kernel exposed a KVM device | caller can open it read/write |
| TPM event log is readable | exact log bytes and SHA-256 digest | PCR quote is fresh or valid |
| `/dev/sev-guest` exists | guest report ioctl surface is present | any report was requested or verified |
| TPM quote / SNP report file is supplied | exact bytes and SHA-256 digest | signature/TCB is valid without a configured verifier |
| Ed25519 COSE_Sign1 verifies | named software key signed the bound payload | that key is a TPM/TEE key |
| RAPL counter changes | top-level host/package energy delta | per-VM causal attribution |
| Kepler series changes | configured Prometheus counter delta | correctness beyond Kepler's own collector/model boundary |

`hardwareAttested` becomes true only when a configured quote/report verifier
returns `valid: true` and identifies itself. The embedded public key in a COSE
envelope is transport metadata and is never accepted as its own trust root.

## Reproduce the probe

On a Linux host:

```bash
FIRECRACKER_BIN=/absolute/path/to/firecracker \
FIRECRACKER_KERNEL=/absolute/path/to/vmlinux \
FIRECRACKER_ROOTFS=/absolute/path/to/rootfs.ext4 \
KEPLER_METRICS_URL=http://127.0.0.1:9103/metrics \
node runtime/probe.js
```

Kernel/rootfs and Kepler variables are optional. Omitting them returns typed
`UNAVAILABLE` blockers; it does not substitute fixtures or modeled evidence.
The control-plane probe starts Firecracker, performs `GET /version`,
`PUT /machine-config`, and `GET /machine-config`, then terminates it. It does
not call `InstanceStart` and therefore cannot be mistaken for a guest boot.

The real launch adapter is `FirecrackerRuntime.launch` in
`runtime/firecracker.js`. Given a ready host and actual kernel/rootfs paths, it:

- hashes every launch input;
- starts the Firecracker process and waits for its Unix socket;
- configures vCPU/memory, boot source, root drive, optional read-only drives,
  and optional explicitly named TAP interfaces;
- sends `InstanceStart`;
- returns a live handle only after the start action succeeds.

If preflight fails, `launch` returns `executed: false` and never spawns the
VMM. If an API step fails after spawn, it terminates the VMM and returns the
actual Firecracker error body and bounded logs.

For a production deployment, use Firecracker's `jailer`; this adapter is an
unjailer development path and makes no production isolation claim.

## Host observation: 2026-08-25

An official Firecracker v1.16.1 x86-64 release was downloaded to `/tmp` for a
non-committed host probe.

| Item | Observation |
|---|---|
| Release archive SHA-256 | `382a02a869e4d6d5cb14c40577f9545e8458021ea8b0b2d3fc10ec14d9c242e6` |
| Firecracker binary SHA-256 | `2fd0171309af7e24cf8dafc8a6f921c1434c49b5f9349bb996b7ed0a4deb8aa7` |
| Release manifest | binary digest exactly matched the bundled `SHA256SUMS` |
| Binary/API | `Firecracker v1.16.1`; version and machine-config API calls succeeded |
| KVM | `/dev/kvm` is a character device, but this user has neither read nor write access (`EACCES`) |
| Start attempt | `InstanceStart` returned `Error creating KVM object: Permission denied (os error 13)` |
| TPM | neither `/dev/tpmrm0` nor `/dev/tpm0`; no TPM boot-event or IMA log |
| SEV-SNP | `sev_guest` module directory exists, but CPU is Intel and `/dev/sev-guest` is absent; no report exists |
| RAPL | powercap directory exists but exposes no readable `energy_uj` counter |
| Kepler | no metrics endpoint was configured |

The successful API probe and failed `InstanceStart` are both useful: together
they locate the blocker at KVM authorization instead of incorrectly reporting
that Firecracker itself is absent. No TPM quote, SNP report, RAPL sample, or
Kepler sample was manufactured to fill the missing fields.

The downloaded binary remains outside the repository. The runtime code accepts
an absolute pinned binary path, so a deployment can manage it through its own
verified supply-chain policy.

## COSE receipt profile

`runtime/cose.js` emits the RFC 9052 tagged structure:

```text
#6.18([
  protected:   bstr({ 1: -8, 4: key-id }),
  unprotected: {},
  payload:     bstr(deterministic-CBOR delivery payload),
  signature:   bstr(Ed25519 signature)
])
```

The signed structure is:

```text
["Signature1", protected, external_aad, payload]
```

The delivery payload binds execution/node identity, nonce, ordered integer
timestamps, actual artifact SHA-256 digests and sizes, capability statuses,
energy-counter deltas, and any measured-boot/TPM/SNP evidence digests. The
encoder intentionally rejects floating point and indefinite-length CBOR so the
signed bytes are deterministic. Node's built-in `crypto.sign` and
`crypto.verify` perform pure Ed25519 signing.

## Energy scope

`RaplMeter` discovers `energy_uj` counters and selects only top-level powercap
zones. Package counters and their core/uncore descendants overlap; summing both
would double count. Counter wrap is reconciled with
`max_energy_range_uj` when it is available.

The default `KeplerMeter` series is `kepler_node_cpu_joules_total`. A deployment
may provide a narrower VM/container metric pattern, but the selected series is
always carried in the receipt. Neither meter silently turns a modeled wattage
into a measured joule value.

## Tests

```bash
node --test tests/runtime-attestation.test.js
```

The focused suite checks actual SHA-256 file measurement, deterministic CBOR,
real Ed25519 COSE signing and tamper rejection, external trust-key enforcement,
typed absent-capability states, RAPL wraparound, Kepler Prometheus deltas,
quote/report binding versus verification, signed receipt closure, and
fail-before-spawn Firecracker admission.

## Primary specifications and implementation references

- Firecracker getting started and KVM requirements:
  <https://github.com/firecracker-microvm/firecracker/blob/main/docs/getting-started.md>
- Firecracker production host/jailer guidance:
  <https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md>
- Firecracker v1.16.1 release:
  <https://github.com/firecracker-microvm/firecracker/releases/tag/v1.16.1>
- COSE structures and COSE_Sign1, RFC 9052:
  <https://www.rfc-editor.org/rfc/rfc9052.html>
- COSE EdDSA algorithm, RFC 9053:
  <https://www.rfc-editor.org/rfc/rfc9053.html>
- Linux TPM event-log semantics:
  <https://docs.kernel.org/security/tpm/tpm_event_log.html>
- Linux SEV guest report ioctl:
  <https://docs.kernel.org/virt/coco/sev-guest.html>
- Linux powercap/RAPL `energy_uj` interface:
  <https://docs.kernel.org/power/powercap/powercap.html>
- Kepler metric definitions:
  <https://sustainable-computing.io/kepler/design/metrics/>
