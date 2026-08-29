# Six-step near-ovoid migration/recovery trajectories

This packet extends the earlier one-release A/B from an instantaneous source
choice to **full, size-preserving migrations over six consecutive steps**.
It deliberately keeps engineering-policy evidence separate from W33 blocking
theorems.

## Experiment

Every trajectory starts from one of the complete 2,880 optimal ten-point
near-ovoids.  At every step one busy point is released and one idle point is
occupied, so busy cardinality remains ten.

Both policies first minimise exactly the same movement objective:

1. level-1 migration rays;
2. hop count.

On this corpus both arms remain at the floor of **3 rays / 1 hop per step**, so
a six-step trajectory costs exactly 18 rays and six hops in both arms.

The only difference is the equal-cost tie-break.

### Legacy arm

Use the existing deterministic lexicographic `(source,destination)` tie-break
among cheapest moves.

### Topology-aware arm

On a certified near-ovoid, restrict the source to the exact four high-release
points supplied by `scheduler/w33-near-ovoid-migration.js`.  After a trajectory
leaves the near-ovoid stratum, all busy sources are eligible.  Among cheapest
moves, choose the move that

1. maximises the number of free W33 lines **after the complete migration**;
2. then maximises release-only headroom;
3. then applies the same lexicographic tie-break.

No anti-cycle rule is imposed.  Repeated states are allowed and measured.

## Exact corpus result

Across all 2,880 paired trajectories, mean free-line headroom after each full
migration is

| step | legacy | topology-aware |
|---:|---:|---:|
| 1 | 5.2854167 | 6.0000000 |
| 2 | 5.6083333 | 9.0000000 |
| 3 | 5.9604167 | 11.7621528 |
| 4 | 5.6388889 | 14.1795139 |
| 5 | 5.9604167 | 15.7621528 |
| 6 | 5.6388889 | 16.9229167 |

The topology-aware arm is strictly better in respectively

`1566, 2620, 2819, 2875, 2880, 2880`

of the 2,880 paired states at steps 1 through 6.

Cumulative six-step headroom is

- legacy: `98,186`, mean `34.0923611`;
- topology-aware: `212,045`, mean `73.6267361`;
- gain: `113,859`, mean `39.534375`;
- relative cumulative gain: `1.1596256085` (about 115.96%).

The topology-aware trajectory never drops below six free lines:

`minimum-headroom histogram = {6:2880}`.

The legacy minimum-headroom histogram is

`{3:810, 4:528, 5:789, 6:753}`.

## Migration cycling

Count the initial state plus the six post-migration states.  The topology-aware
arm visits seven distinct states in **all 2,880** trajectories.

The legacy deterministic tie-break visits only

`{2:732, 3:1098, 4:858, 5:192}`

distinct states.  Thus this particular deterministic ray-only tie-break enters
short migration cycles on the entire adversarial corpus.

This statement is intentionally narrow: it is **not** a theorem that every
possible ray-only policy cycles.  It diagnoses the currently declared
lexicographic tie-break.

## Why this is stronger than the one-release benchmark

The preceding A/B measured free lines after the migration source was released
but before accounting for destination occupancy.  The present experiment scores
the complete move.  At the first full migration the topology-aware policy still
achieves exactly six free lines on all 2,880 states, while the legacy full-move
histogram is

`3^30 4^432 5^1104 6^1314`.

So the improvement is not an artifact of temporarily deleting a source; it
survives destination placement and then compounds over the trajectory.

## Evidence boundary

This result is exact for the two declared deterministic policies on the finite
2,880-state level-1 adversarial corpus.  It is an engineering-policy benchmark,
not a new blocking-number theorem.  It does not establish production
throughput, latency, energy savings, market performance, or physical-fabric
behavior.

Artifacts:

- `experiments/near_ovoid_migration_trajectory_ab.js`
- `data/near_ovoid_migration_trajectory_ab.json`
- `tests/near-ovoid-migration-trajectory.test.js`
- `npm run experiment:near-ovoid-trajectory`
