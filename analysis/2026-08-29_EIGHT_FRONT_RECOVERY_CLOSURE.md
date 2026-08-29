# Eight-front recovery closure — Holotrade side

Date: 2026-08-29

This note records the operational half of the requested five recovery/RTL fronts plus the interface to the three W33 physics attacks.

## Completed operational fronts

1. **19/19 attractor geometry.** The 933 deterministic-policy cycles are a label-selected subset of one ambient PSp(4,3) orbit of 12,960 unordered cycles; cycle/state/core stabilizers have orders 2/4/18 respectively.
2. **Healthy recovery local law.** `F_after = F + s1(source) - z(destination) - 1[shared line singleton]` exactly reproduces the topology-aware healthy decision on all 92,160 trajectory decisions through 32 steps from the 2,880 starts.
3. **Multi-failure census.** All 1,252,800 two-idle-node failure pairs are exhausted. All 11,692,800 triple initial patterns are counted and the 1,247,040 worst zero-placement triples are fully simulated through six migrations.
4. **Correct energy layer.** Inside one level-1 W33 cell, actual Fleet site energy is constant. Across datacenters, every seeded source has a minimum cross-DC tier of 7 rays / 33 hops; equal-cost energy/carbon tie-breaking changes 148/320 destinations and reduces the declared catalog energy/carbon indices without changing the movement frontier.
5. **Combined recovery RTL.** `rtl/w33_recovery_two_stage_core.v` embeds the exact W33 incidence masks. Entry mode restricts the source to the certified one-bit hinge selector; after `advance`, the same core implements the exact local healthy scorer. Software regressions lock entry objective equivalence and post-entry exact policy identity.

## Hardware evidence boundary

The current execution environment did not provide Yosys/yowasp-yosys, so this packet does not claim a new synthesized LUT/cell count. The RTL has three explicit registered bits (`valid`, `entry_q`, `block_q`); combinational cost is intentionally left as `null` in `data/w33_recovery_two_stage_core.json` until the committed Yosys harness is run.

Verification entry points:

- `npm run verify:w33-recovery-two-stage`
- `npm run synth:w33-recovery-two-stage`
- `npm run experiment:w33-crossdc-energy`
- `npm run experiment:w33-multi-failure`
- `npm run verify:migration-recovery`

## Physics interface

The companion W33-Theory packet contains three deliberately evidence-bounded physics attacks:

- 85-state chiral flat-band protection splits into five index-protected zero modes plus 30 additional PSp-symmetry-protected zero modes;
- six near-ovoid microstates admit an exact `F3 x F2` qutrit/chirality synthetic-coordinate normal form;
- the deterministic period-two recovery cycles possess a Koopman `-1` mode but fail the stronger discrete-time-crystal interpretation for the measured headroom observable and physical criteria.

Cross-repo closure: `wilcompute/W33-Theory` commit `3733d6e4b5f9441c8f281f1537245bc170e27e6d`.
