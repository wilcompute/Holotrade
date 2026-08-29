# Five-front migration/recovery closure

Date: 2026-08-29

This packet extends the exact 2,880-state W33 near-ovoid corpus into a declared
scheduler policy surface and several finite policy experiments.  Combinatorial
facts and engineering-policy evidence are kept separate throughout.

## 1. Opt-in scheduler policy

`scheduler/w33-migration-policy.js` exposes two policies:

- `legacy` — the default, preserving the existing rays -> hops -> lexicographic
  tie-break;
- `topology-aware` — opt-in, preserving the same rays -> hops primary objective
  while using certified near-ovoid high-release sources and line headroom as
  tie-breaks.

The selector also accepts unavailable `failed` points and an optional secondary
destination score.  Neither changes the primary movement ordering.

## 2. Long-horizon deterministic dynamics

The 32-step / cycle-detection experiment is exhaustive over all 2,880 starting
near-ovoids.  For the exact deterministic policies currently declared, both
arms eventually enter state cycles of period two.

Legacy reaches its two-cycle after transient length 0-3.  Topology-aware reaches
its two-cycle after transient length 5-14.  Its cycle-headroom classes are:

- `19/19`: 2,255 trajectories;
- `17/17`: 572;
- `16/17`: 36;
- `16/16`: 17.

Across 32 migrations, cumulative line headroom is 532,464 for legacy and
1,596,349 for topology-aware, a relative gain of about 199.8%.

This is a theorem about the two finite deterministic transition rules on this
finite corpus, not about every ray-minimising policy.

## 3. Worst single idle-node failure

For each optimal near-ovoid, its defect centre is the unique idle point whose
outage kills all three current free line placements.  Keeping that point failed,
then applying healthy size-preserving migrations gives an adversarial recovery
experiment with 2,880 starts.

Topology-aware restores at least:

- 3 free lines after exactly one migration in all 2,880 cases;
- 6 after exactly two in all cases;
- 9 after exactly three in all cases;
- 12 after four moves in 2,706 cases and after five in the remaining 174.

Legacy fails to regain even three lines within six moves in 696 cases and fails
to reach six within six moves in 2,244 cases.  Both arms pay exactly 18 rays for
six moves.

This is finite adversarial recovery evidence, not an MTTR/SLA claim.

## 4. Locality and energy as secondary objectives

At level 1 there is no residual locality tradeoff: all moves surviving the
primary selector are 3 rays / 1 hop.

Energy is not intrinsic to a W33 point.  The sensitivity experiment therefore
uses a declared catalog-anchored mapping: each W33 point is assigned to its
nearest one-digit datacenter prefix in W33 distance, with catalog order breaking
ties, and the destination score is `baseEnergy * PUE`.

Using that score only after movement and topology ties reduces the six-step
aggregate destination energy index from 1,166,342.38 to 744,090.92, a 36.20%
reduction in the declared sensitivity field, without changing the movement
floor.  This is not live telemetry or a physical energy-saving theorem.

## 5. Canonical two-state controller

The local six-state `C3 x S3` action has its unique nontrivial `3+3` block
system.  Geometrically the hinge line `ac` contains two residual points, and
exactly one is contained in a near-ovoid's four-point high-release tetrad.

Therefore the first-step source controller needs only one bit:

- state 0: use the first residual hinge point;
- state 1: use the second residual hinge point.

The two states occur 1,440/1,440.  Exhaustive regression over all 2,880
near-ovoids verifies that the selected source is always high-release, costs 3
rays / 1 hop, opens seven lines upon release, and admits a full migration with
six free lines — exactly matching the full topology-aware first-move headroom.

The two-state controller is certified only on the near-ovoid entry stratum;
after a full migration the generic topology-aware policy resumes unless a new
orbit controller is separately proved.

## Reproduction

- `npm run experiment:near-ovoid-long-horizon`
- `npm run experiment:near-ovoid-failure-recovery`
- `npm run experiment:near-ovoid-secondary-costs`
- `npm run verify:migration-recovery`

The frozen artifacts are:

- `data/near_ovoid_migration_long_horizon.json`
- `data/near_ovoid_failure_recovery.json`
- `data/near_ovoid_secondary_costs.json`
- `data/near_ovoid_block_controller.json`
