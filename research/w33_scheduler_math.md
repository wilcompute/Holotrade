# W(3,3) shape scheduling: exact bounds, executable adapters, and paired simulation

**Evidence status:** exact finite mathematics plus a deterministic discrete-event experiment. The Kubernetes, Slurm, and Containerlab surfaces in this packet are reference adapters/exports; none was deployed in the frozen run.

## 1. What was built

This packet turns HoloTrade's existing W(3,3) point graph from a displayed topology into an executable placement primitive:

- `scheduler/w33-scheduler.js` exposes Filter, Score, NormalizeScore, Reserve, and idempotent Unreserve operations shaped like Kubernetes scheduling extension points;
- the same kernel exposes a Slurm-style `selectTopology()` gang selector;
- `scheduler/containerlab-export.js` emits all 40 Linux nodes and all 240 point-graph links as a Containerlab topology;
- `experiments/w33_scheduler_ab.js` compares W33-aware, locality-first, and seeded-random placement on identical synthetic congestion and failure states;
- `analysis/w33_scheduler_math.g` independently reconstructs W(3,3) in GAP and certifies the graph, spectrum, two optimal shapes, and vertex connectivity;
- `data/w33_scheduler_ab_24.json` freezes 288 paired scenarios; and
- `data/w33_scheduler_ab_math_gap.json` freezes the GAP-owned mathematical certificate.

The adapter vocabulary tracks the upstream systems without claiming a deployment. Kubernetes documents Filter and Score as scheduling-cycle extension points and Reserve/Unreserve as stateful notifications before binding, with Unreserve required to be idempotent. Its newer topology-aware scheduling surface evaluates whole placements for PodGroups. Slurm's topology guide likewise separates flat best-fit placement from topology-aware allocation, while its block plugin explicitly prioritizes contiguous blocks and reduced fragmentation. Containerlab defines a topology as YAML nodes plus point-to-point link endpoints. Those are the narrow interfaces mirrored here:

- [Kubernetes Scheduling Framework](https://kubernetes.io/docs/concepts/scheduling-eviction/scheduling-framework/)
- [Kubernetes Topology-Aware Workload Scheduling](https://kubernetes.io/docs/concepts/scheduling-eviction/topology-aware-scheduling/)
- [Slurm Topology Guide](https://slurm.schedmd.com/topology.html)
- [Slurm topology configuration](https://slurm.schedmd.com/topology.conf.html)
- [Containerlab topology definition](https://containerlab.dev/manual/topo-def-file/)

## 2. The scheduler theorem

Let $A$ be the adjacency matrix of the W(3,3) point graph. The GAP witness reconstructs

\[
  \operatorname{SRG}(40,12,2,4),\qquad
  \operatorname{spec}(A)=\{12^1,2^{24},(-4)^{15}\}.
\]

For any vertex set $T$ of size $m$, write

\[
  \mathbf 1_T=\frac{m}{40}\mathbf 1+f,
  \qquad f\perp\mathbf 1,
  \qquad \lVert f\rVert^2=m\left(1-\frac m{40}\right).
\]

If $b(T)$ is its edge boundary and $e(T)$ its induced-edge count, then

\[
  b(T)=12m-2e(T)
      =12m\left(1-\frac m{40}\right)-f^{\mathsf T}Af.
\]

The *one-sided* spectral bounds matter here. Since the largest eigenvalue orthogonal to the all-ones vector is $2$, not $4$ in absolute value,

\[
  \boxed{\frac{m(40-m)}4\le b(T)\le\frac{2m(40-m)}5}.
\]

Equivalently,

\[
  \frac{m(m-10)}5\le e(T)\le\frac{m(m+8)}8,
\]

with the obvious integral rounding and $e(T)\ge 0$. This is useful to a scheduler in two directions: the lower-bound equality identifies the least-exposed / most internally linked shapes of a fixed size, while boundary remaining after failures is an observable attachment-capacity input rather than a marketing proxy.

### Two equality templates already hidden in the repository

The spectrum upgrades two existing graph witnesses into optimal reservation shapes:

| shape | $m$ | induced links | boundary | consequence |
|---|---:|---:|---:|---|
| a W(3,3) line | 4 | 6 | 36 | a $K_4$, hence a densest possible 4-worker reservation |
| certified bisection side | 20 | 70 | 100 | a densest possible 20-worker reservation |

The 20-point statement is the dual reading of the existing exact bisection certificate: attaining the minimum 100-edge boundary forces $e(T)=(12\cdot20-100)/2=70$, which attains the spectral upper bound. The scheduler now explicitly injects all 40 line templates at width four and both certified halves at width twenty before generating general connected candidates.

This is a new operational use of existing repository facts, not a claim that the underlying spectral inequality or W(3,3) parameters are novel mathematics.

## 3. Exact failure threshold for the full cell

The GAP witness performs a vertex-split max-flow computation for every one of the graph's 540 nonadjacent vertex pairs. Every local vertex flow is exactly 12. Deleting the 12 open neighbours of any vertex isolates that vertex, giving the matching upper witness. Therefore

\[
  \boxed{\kappa(W(3,3))=12}.
\]

Operationally, a complete 40-node cell remains connected after *any* 11 node deletions; some 12-node deletion does disconnect it. This is an exact graph statement. It is not automatically inherited by partial reservations, and it is not a hardware availability, Byzantine, or packet-delivery SLA.

## 4. Placement policies and traffic model

Every row uses one shared topology state and then applies three policies:

1. **W33-aware:** generate connected candidates from every live seed plus exact equality templates, route the requested collective with congestion-priced shortest paths, then minimize modeled makespan with deterministic node-load and density tie-breakers.
2. **Locality-first:** start at the least-loaded available node and breadth-first fill its live neighborhood, without inspecting link congestion or collective flow.
3. **Seeded-random:** sample available nodes uniformly from a deterministic shuffle.

The traffic families are a four-worker all-reduce, eight-worker shuffle, and twelve-worker parameter-server pattern. Conditions are steady load, concentrated congestion, twenty failed links, and five failed nodes plus twelve failed links. Link capacity is one unit, link/node load is synthetic, routing is deterministic, and all policies see the same state.

This is deliberately a paired *model comparison*. The W33-aware policy sees link load and the collective objective while the baselines do not, so the packet measures the effect of that extra topology logic inside this model. It is not an unbiased systems benchmark or a claim about physical throughput.

## 5. Frozen 288-scenario result

The 24-seed packet contains $24\times4\times3=288$ paired scenarios. Its canonical row SHA-256 is:

```text
7a14efe68ac0a0664bea4bbdb93bcd75df2ea1050cb2551c861059503b002112
```

| policy | success | connected induced placements | mean modeled makespan | mean induced links |
|---|---:|---:|---:|---:|
| W33-aware | 288/288 | 100.00% | 1.351889 | 16.3090 |
| locality-first | 288/288 | 100.00% | 1.681391 | 11.6042 |
| seeded-random | 288/288 | 57.29% | 1.701758 | 9.8438 |

Paired against locality-first, W33-aware wins 264/288 rows and has a mean relative modeled-makespan reduction of **16.43%**. Against seeded-random it wins 278/288 and reduces modeled makespan by **17.35%** on average.

The effect strengthens under stress:

| condition | vs locality-first | vs seeded-random |
|---|---:|---:|
| steady | 2.30% | 4.56% |
| congested | 17.76% | 19.77% |
| 20 link failures | 22.38% | 22.93% |
| 5 node + 12 link failures | 23.27% | 22.13% |

The honest counterexample is important: on the steady twelve-worker parameter-server stratum, W33-aware has mean makespan 1.247224 versus locality-first's slightly better 1.245727 and wins only 9/24 seeds. Topology awareness is not a universal win; its value in this packet comes mainly from collectives and stressed links.

## 6. Scheduler integration boundary

### Kubernetes-shaped lifecycle

`W33SchedulerPlugin` implements:

```text
preFilter -> filter -> score -> normalizeScore -> reserve -> unreserve
```

Reservations are non-overlapping within one plugin process, retries return the same token, and Unreserve is idempotent. That protects the local gap between selection and binding. It does **not** provide distributed gang commit; the multi-node reservation transaction layer must own prepare/commit/abort across machines.

### Slurm-shaped selection

`selectTopology()` returns a deterministic list such as `w33-00`, topology class, segment size, and exact induced metrics. W(3,3) is not a tree, ring, torus, or the power-of-two hierarchy required by Slurm's stock block topology. The adapter therefore does not pretend that a `topology.conf` file can encode the graph faithfully; a production integration needs a real compiled selection plugin or a placement service called by one.

### Containerlab export

Generate the complete lab with:

```bash
node scheduler/containerlab-export.js > /tmp/holotrade-w33.clab.yml
```

Tests count 40 nodes, 240 point-to-point links, and exactly twelve data interfaces per node. Containerlab was unavailable in the producing environment, so no lab was deployed and no packet or latency result in `data/w33_scheduler_ab_24.json` came from Containerlab.

## 7. Reproduction

```bash
# Exact GAP certificate (about 540 max-flow checks)
gap -q analysis/w33_scheduler_math.g

# Focused software/GAP tests
node --test tests/scheduler.test.js

# Regenerate the full paired packet
node experiments/w33_scheduler_ab.js \
  --seeds=24 \
  --write=data/w33_scheduler_ab_24.json \
  --summary

# Generate, but do not automatically deploy, the Containerlab topology
node scheduler/containerlab-export.js > /tmp/holotrade-w33.clab.yml
```

The exact theorem is ready to constrain a real scheduler. The measured systems claim remains open until the generated topology is deployed, traffic is injected, and the same paired design is rerun on packet-level and then hardware telemetry.
