# Measured-input shadow balancing: the first host/market replay packet

**Status:** implemented and reproducible. The inputs include measured kernel counters and an official wholesale-market trace. The policy outputs are counterfactual and no host setting was changed. This is **not** a field A/B outcome.

## 1. What existed, and what this adds

The repository's existing `experiments/balancer_ab.js` packet is a strong paired **simulation**: 64 seeded fleets, one changed policy switch, and a frozen row digest. `js/energy.js` is equally explicit that its price process is synthetic. Before this packet, the repository contained no host telemetry reader, no primary-source market fixture, and no shadow-policy replay over measured inputs.

This packet adds three separately labelled layers:

1. **Measured host input:** 48 read-only, 500 ms observations of Linux `/proc` and cgroup counters over 12 logical CPU lanes.
2. **Measured market input:** 48 half-hour APXMIDP Market Index observations from Elexon for the half-open UTC interval 2026-08-01 00:00 through 2026-08-02 00:00.
3. **Counterfactual output:** one normalized 0.10 demand-response step per host observation, with the current HoloTrade demand multiplier and price elasticity. The recommendation is never applied.

The evidence label in the replay certificate is therefore deliberately:

```text
MEASURED_INPUTS_COUNTERFACTUAL_OUTPUTS
```

not `FIELD_RESULT`, `BENCHMARK`, or `MEASURED_SAVINGS`.

## 2. Primary-source wholesale trace

The source is the official [Elexon Insights Market Index Data endpoint](https://bmrs.elexon.co.uk/api-documentation/endpoint/balancing/pricing/market-index). Elexon's [developer portal](https://developer.data.elexon.co.uk/) states that the Insights APIs are public and require no API key. Its MID documentation defines the price and volume as short-term wholesale electricity trading observations in Great Britain from the appointed Market Index Data Providers. This packet selects `APXMIDP`.

The exact request is frozen in `data/telemetry_shadow_elexon_mid.json`. Elexon's endpoint filters inclusively, so the adapter preserves the provider response and then normalizes it to the declared half-open interval `[from,to)`, yielding exactly 48 rows. The fixture records the HTTP status, content type, response-byte count, raw response SHA-256, canonical response SHA-256, normalized-row SHA-256, retrieval time, query, units and full provider response.

Required attribution is included in both the fixture and this note:

> Contains BSC information licensed under the BSC Open Data Licence.

The [BSC Open Data Licence](https://www.elexon.co.uk/bsc/data/open-data-requests/bsc-open-data-licence/) permits reuse subject to attribution and its stated terms.

Frozen market summary:

| Quantity | Value |
|---|---:|
| observations | 48 half-hours |
| units | GBP/MWh and MWh |
| minimum price | 34.86 GBP/MWh |
| maximum price | 158.94 GBP/MWh |
| arithmetic mean | 114.23875 GBP/MWh |
| volume-weighted mean | 109.1946275545 GBP/MWh |
| median used as dimensionless baseline | 132.56 GBP/MWh |
| resulting common `E` range | 0.62 to 1.1049723032 |
| provider-response byte SHA-256 | `1b83b9643f5f2ef0332b29eda5ab64cd61fd3eab528001b90747a1ae69154f8e` |

No GBP/USD conversion is invented. The policy replay uses only the dimensionless ratio of each GBP price to the trace median.

## 3. Host measurement boundary

`telemetry/procfs.js` reads cumulative kernel counters and differences adjacent snapshots. The checked-in capture used a native Linux Node 24.15.0 process on WSL2 and reads:

- `/proc/stat` for aggregate and per-CPU busy fractions;
- `/proc/meminfo` for total and available memory;
- `/proc/loadavg` for runnable/total task counts and load average;
- `/proc/self/stat` for current-process CPU jiffies and resident pages;
- cgroup v2 CPU and memory counters when exposed; and
- RAPL `energy_uj` domains when exposed.

The capture is read-only. It does not set affinity, write a cgroup, change priority, migrate a process, launch a benchmark load, or call the HoloTrade execution engine.

RAPL was **not exposed** by this WSL2 kernel. The fixture records `raplEnergy: false`, the reason, and `null` rather than estimated joules in every observation. Consequently this packet establishes no energy, carbon, thermal, or hardware-lifetime outcome.

The default `node` command in this particular WSL environment routes to Windows Node and cannot see Linux `/proc`. The live fixture was captured with the SHA-verified official Linux Node v24.15.0 binary. Frozen replay and all non-live tests remain portable.

Frozen host summary:

| Quantity | Value |
|---|---:|
| observations | 48 |
| requested interval | 500 ms |
| logical CPU lanes | 12 |
| mean aggregate CPU busy fraction | 0.0098228034 |
| mean observed per-lane Gini | 0.6741738668 |
| host fixture SHA-256 | `c8e19ded8d190a57d02ddf6448217c390ffe07e7d2e3d59eb65aa0b3b8ce4ae0` |

The machine was lightly loaded. At this time scale, Linux jiffy quantization makes activity sparse across lanes and therefore makes the per-lane Gini large. The result is a faithful observation of this capture, not a population estimate for production servers.

## 4. Shadow design

For each measured vector `u = (u_1,...,u_n)`, the off arm is persistence: the observed vector is left unchanged. The on arm computes, but never applies, one recommendation:

1. evaluate the repository's exact two-sided demand multiplier `D(u_i)`;
2. form constant-elasticity weights with exponent `-1.9`;
3. allocate the observed aggregate busy fraction proportionally, with a hard lane capacity of one; and
4. move 10% toward that target.

The water-filling target and convex response preserve the sum of busy fractions to floating-point tolerance in every paired row. Because `/proc/stat` does not measure thermal swing, the replay sets `utilisationEMA = utilisation`; inventing a thermal-cycle surcharge would turn a missing measurement into fake evidence.

The 48 host intervals and 48 historical market intervals are paired by ordinal for a deterministic replay, but they are **not co-temporal and not geographically linked**. Every row carries `streamsTimeAligned: false`.

## 5. Exact common-factor cancellation

The packet exposed a structural distinction that the synthetic price process did not make obvious.

Suppose the normalized allocation weight is

\[
  a_i = \frac{P_i^{\varepsilon}}{\sum_j P_j^{\varepsilon}},
\]

where `epsilon = -1.9` in the current model. If every lane sits behind the same wholesale-price multiplier `E_t > 0` and the remaining lane-specific price is `R_i`, then

\[
  a_i(E_t R)
  = \frac{(E_tR_i)^{\varepsilon}}
           {\sum_j(E_tR_j)^{\varepsilon}}
  = \frac{E_t^{\varepsilon}R_i^{\varepsilon}}
           {E_t^{\varepsilon}\sum_jR_j^{\varepsilon}}
  = a_i(R).
\]

So a common wholesale-price feed can change absolute quotes, floors and aggregate demand, but it **cannot steer relative placement inside one price zone** under a homogeneous normalized elasticity rule. The test suite evaluates the same measured vector at the minimum and maximum allowed HoloTrade energy multipliers, 0.62 and 2.4, and obtains the same recommendation to `1e-15`.

This gives a concrete design requirement:

> Energy-aware migration needs lane/site-specific `E_i`, a cross-zone price differential, or a non-homogeneous constraint such as a binding floor/cap. A single global live feed is insufficient.

That is not a limitation of Elexon data; it is an invariance of multiplicative relative-price allocation.

## 6. Frozen paired replay result

| Quantity | Observed/off | Counterfactual/on |
|---|---:|---:|
| mean lane-utilisation Gini | 0.6741738668 | 0.6054857263 |
| mean maximum lane utilisation | 0.0529870841 | 0.0484830837 |

The mean paired Gini difference was **0.0686881405**. The recommendation lowered Gini in 41 intervals, left 7 all-idle/equivalent intervals unchanged, and worsened none. Aggregate busy fraction was conserved in every row.

These numbers measure the policy's counterfactual response to this frozen input packet. They do **not** measure what the host would have done after actuation, how applications would have performed, or whether energy/cost/wear would improve.

Commitments:

| Object | SHA-256 |
|---|---|
| host fixture | `c8e19ded8d190a57d02ddf6448217c390ffe07e7d2e3d59eb65aa0b3b8ce4ae0` |
| market fixture | `52ce161e0a4448019c08f709b8c86cbf98362b329265f155cecef9b118e88346` |
| replay rows | `4143137a2f62c5d7aaf385e1d76ff7b8cfdf7fb6c5ec14bdfdf724dbe99dc8aa` |
| replay certificate | `fc635ad40def451ab9716430f6c30304888d18ef972b6d5f4570dc6c9f6d0d60` |

The replay schema canonicalizes computed non-integer values to 12 significant
decimal digits before hashing. This removes one-to-two-ulp `Math.pow`
differences between supported V8/libm builds without changing any reported
conclusion or the input-fixture commitments.

## 7. Reproduce and recapture

Deterministic replay of the checked-in fixtures:

```bash
node experiments/balancer_shadow.js --summary
node --test tests/telemetry-shadow.test.js
```

On a native Linux Node runtime, capture a new read-only host trace and regenerate the certificate:

```bash
node experiments/balancer_shadow.js \
  --capture-host --write-certificate --samples=48 --interval-ms=500 --summary
```

Refresh the historical primary-source market response and regenerate:

```bash
node experiments/balancer_shadow.js --refresh-market --write-certificate --summary
```

A refresh is expected to change fixture commitments and must be reviewed as a new evidence packet, especially if Elexon has published a correction.

## 8. What would turn this into a field result

A field A/B requires more than a live API and `/proc`:

- telemetry from multiple independently priced physical sites;
- a pre-registered intervention horizon and workload/SLO definition;
- actual treatment actuation with a paired or randomized control;
- RAPL/BMC/PDU energy measurement and DCIM provenance;
- synchronized price, telemetry, placement and application-outcome clocks;
- workload completion/latency/error outcomes; and
- a signed operator evidence chain.

Until those exist, this packet's honest claim is narrower and useful: HoloTrade can ingest hashed measured inputs, issue a no-actuation shadow recommendation, replay it exactly, and identify a mathematical condition under which a wholesale signal cannot affect placement.
