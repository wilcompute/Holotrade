# Five-front recovery/attractor/RTL closure

Date: 2026-08-29

This packet executes the five continuations after the six-step migration/recovery result.  Exact finite W33 statements are separated from scheduler-policy evidence and seeded-fleet model boundaries.

## 1. High-headroom period-two attractor

The topology-aware deterministic policy sends 2,255 of the 2,880 certified near-ovoid starts into 933 distinct `19/19` period-two cycles.  Those cycles contain 1,866 distinct ten-point states and 590 distinct nine-point cores.

Every 19-free-line cycle state has the same line-occupancy profile

`0^19 1^4 2^15 3^2`,

the two triple-hit lines are disjoint, and the induced ten-point W33 graph is one isomorphism type with degree sequence

`5^4 4^4 3^2`.

Its graph automorphism group has order 16 and structure `D8 x C2`, with element-order census `1^1 2^11 4^4`, center order 4 and derived subgroup order 2.

A cycle transition fixes a nine-point core with profile `0^21 1^3 2^15 3^1` and degree sequence `5^2 4^6 2^1`, then exchanges two adjacent degree-three points.  Each toggle point has three neighbours in the core; the two neighbour triples meet exactly in the core's unique degree-two point.

Artifacts:
- `analysis/w33_near_ovoid_attractor_structure.js`
- `data/near_ovoid_attractor_structure.json`

Boundary: this classifies the attractor of the declared deterministic policy.  It does not prove 19 free lines globally optimal over all policies or all ten-point W33 states.

## 2. Exact second-step controller

After one topology-aware migration, the 2,880 provenance-labelled starts land in 2,818 distinct states, all with six free lines.  There are only three occupancy profiles:

- `0^6 1^28 2^6`: 1,980 cases;
- `0^6 1^29 2^4 3^1`: 764;
- `0^6 1^31 3^3`: 136.

The generic second-step scorer collapses exactly to:

1. choose the lexicographically first busy point incident with the maximum number of singly occupied lines;
2. release it;
3. among adjacent idle destinations, choose the lexicographically first one meeting the fewest free-after-release lines.

The chosen source has four singleton incident lines in 2,578 cases and three singleton plus one doubled line in 302.  The rule reproduces the full generic topology-aware `(from,to)` decision on all 2,880 provenance-labelled states and leaves exactly nine free lines after move two.

Artifacts:
- `scheduler/w33-near-ovoid-stage2-controller.js`
- `data/near_ovoid_stage2_controller.json`

## 3. Two simultaneous idle-node failures

The first failure is the near-ovoid defect centre, which kills all three current placements.  The second ranges over each of the other 29 idle points, for 83,520 exact cases.

Relation counts relative to the defect centre are:

- blocker centre: 2,880;
- other adjacent point: 28,800;
- nonadjacent point: 51,840.

Topology-aware recovery is universal through nine lines: every case reaches at least 3, 6 and 9 free line placements after exactly 1, 2 and 3 migrations respectively.

The relation first changes the 12-line threshold:

- blocker centre: step 4 / 5 / 6 counts `256 / 2586 / 38`;
- other adjacent: step 4 / 5 counts `12840 / 15960`;
- nonadjacent: step 4 / 5 counts `22634 / 29206`.

Legacy retains large six-step unrecovered tails even at the 3- and 6-line thresholds.

Artifacts:
- `experiments/near_ovoid_double_failure_recovery.js`
- `data/near_ovoid_double_failure_recovery.json`

Boundary: finite policy recovery on the declared level-1 failure model, not hardware MTTR or an SLA.

## 4. Actual fleet energy boundary

The earlier point-to-datacenter Voronoi experiment remains explicitly a synthetic sensitivity field.  It is not how the actual Fleet address model assigns sites.

`Fleet.build()` constructs each node address as

`[dc.prefix, cell, W33-point]`

and gives the node that same datacenter's `dcId`.  Therefore a whole level-1 W33 cell lies inside one datacenter subtree.  Within-cell point-to-point migration cannot change `baseEnergy`, PUE or site identity.  Energy is therefore constant across a level-1 point tie and becomes meaningful only when a candidate set spans cells / datacenter prefixes and the full fabric address is available.

Artifacts:
- `experiments/near_ovoid_actual_fleet_energy.js`
- `data/near_ovoid_actual_fleet_energy.json`

## 5. One-bit RTL recovery FSM

The canonical `3+3` near-ovoid block system supplies one block bit.  The hinge line contains two residual point ids; the bit selects which residual point is the certified high-release source.

The RTL datapath is one registered state bit plus a 6-bit two-input mux.  Exhaustive software regression over all 2,880 entry states verifies:

- block states split 1,440 / 1,440;
- selected source is high-release in all states;
- primary cost matches the full topology-aware scorer: 3 rays / 1 hop;
- post-move headroom matches: six free lines.

The exact generic `(from,to)` pair is the same in only 664 states.  Thus this FSM is a certified objective-equivalent first-move selector, not a bit-for-bit clone of the generic lexicographic tie-break.

Artifacts:
- `rtl/w33_near_ovoid_recovery_fsm.v`
- `rtl/verify_w33_near_ovoid_recovery_fsm.ys`
- `rtl/synth_w33_near_ovoid_recovery_fsm.ys`
- `data/near_ovoid_recovery_fsm.json`

A Yosys SAT harness proves the 6-bit block-controlled mux semantics when run.  A fresh remote Yosys/CI run is not claimed by this note.

## Reproducibility repair

Several older migration experiments expected a generated `data/w33_near_ovoid_adversarial_corpus.json` that was not committed.  `analysis/w33_near_ovoid_corpus.js` now rebuilds the 360 x 8 corpus exactly in memory and can materialize it with `--write`.  `npm test` and the experiment commands prepare it automatically where needed.

New verification entry points include:

- `npm run experiment:near-ovoid-attractor`
- `npm run experiment:near-ovoid-double-failure`
- `npm run experiment:near-ovoid-actual-fleet-energy`
- `npm run verify:w33-recovery-fsm`
- `npm run synth:w33-recovery-fsm`
- `npm run verify:migration-recovery`
