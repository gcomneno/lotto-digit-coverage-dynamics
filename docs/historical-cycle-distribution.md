# Historical coverage-cycle distribution

## Purpose

This document compares the observed durations of complete decimal digit-coverage cycles with the exact absorption-time distribution of the finite-state model.

The comparison is descriptive. It is not a test of a betting strategy, does not select draws or wheels, and does not imply that historical deviations alter future probabilities.

## Theoretical object

A natural cycle begins immediately after a previous cycle has completed. Its initial missing-digit state is:

\[
\{0,1,2,3,4,5,6,7,8,9\}.
\]

The cycle ends when all ten decimal digits have appeared among the five two-digit numbers drawn on the wheel.

The exact theoretical absorption metrics are:

| Metric | Exact value |
|:---|---:|
| Expected duration | 3.506190 draws |
| Variance | 1.924821 |
| Standard deviation | 1.387379 draws |
| Median, Q50 | 3 draws |
| Q90 | 5 draws |
| Q95 | 6 draws |
| Q99 | 8 draws |

## Historical archives

| Archive | Observed interval | National draws | SHA-256 |
|:---|:---|---:|:---|
| 2023 | 2023-01-03 → 2023-12-30 | 182 | `9b0495a52e827493cd554efe378810adddca7fe6972cf5ed676123c11fc469ad` |
| 2024 | 2024-01-02 → 2024-12-31 | 209 | `4deafe1fd27bd8aadd7a50d492009cc347c11d2602e47fde9de31e7338daebee` |
| 2025 | 2025-01-02 → 2025-12-30 | 208 | `23ed4f6b83fcb479d80ea9c54ea69c2654e0a5639c117b1fb7f49c4b90d488f2` |
| 2026 | 2026-04-14 → 2026-07-25 | 60 | `75f9f1c7f9f4a1aca6691d644ae8b7834e6084b339c8fa23c131ba4d16786e9e` |

All four archives contain eleven wheels, five numbers per wheel and draw, no incomplete wheel draws and no duplicated positions.

## Continuity and censoring rules

The archives from 2023 through 2025 form one continuous historical segment containing 599 national draws.

The 2026 archive begins at draw 60 on 14 April 2026. Draws 1–59 are absent, so the 2025 and 2026 archives must not be joined across that gap.

For each wheel and each continuous segment:

- the initial cycle is excluded because it is censored on the left and may have begun before the archive;
- every subsequently completed cycle is included;
- the final incomplete cycle is recorded as right-censored but excluded from the complete-duration distribution;
- a cycle ending on the final available draw has no right-censored successor in the observed data.

The eleven wheels share the same draw calendar. Their cycle durations must therefore not automatically be treated as mutually independent observations.

## Main continuous segment: 2023–2025

| Metric | Observed | Theoretical | Difference |
|:---|---:|---:|---:|
| Complete cycles | 1,879 | — | — |
| Mean duration | 3.480043 | 3.506190 | -0.026148 |
| Variance | 1.935605 | 1.924821 | +0.010783 |
| Q50 | 3 | 3 | 0 |
| Q90 | 5 | 5 | 0 |
| Q95 | 6 | 6 | 0 |
| Q99 | 8 | 8 | 0 |

CDF comparison:

- mean absolute CDF error: 0.2156%;
- maximum absolute CDF error: 1.3760%.

Across this segment, the empirical mean, variance, selected quantiles and cumulative distribution are all close to the exact finite-state benchmark.

## Separate partial segment: 2026

| Metric | Observed | Theoretical | Difference |
|:---|---:|---:|---:|
| Complete cycles | 171 | — | — |
| Mean duration | 3.555556 | 3.506190 | +0.049365 |
| Variance | 2.106563 | 1.924821 | +0.181741 |
| Q50 | 3 | 3 | 0 |
| Q90 | 5 | 5 | 0 |
| Q95 | 6 | 6 | 0 |
| Q99 | 9 | 8 | +1 |

CDF comparison:

- mean absolute CDF error: 0.5871%;
- maximum absolute CDF error: 1.9859%.

This shorter segment exhibits more sampling variation, as expected from its much smaller number of complete cycles. It remains descriptively close to the theoretical model but must not be merged through the missing January–April data.

## Interpretation

The continuous 2023–2025 segment provides strong descriptive agreement with the exact absorption-time distribution:

- the observed mean differs by about 0.026 draws;
- the observed variance differs by about 0.011;
- all four selected empirical quantiles match exactly;
- the maximum CDF difference is below 1.4 percentage points.

These findings support the finite-state model as an accurate description of historical coverage-cycle duration.

They do not, by themselves, constitute an inferential proof that every deviation is independent sampling noise. Such a claim would require an explicitly defined dependence model for wheels sharing the same draw calendar.

No observed deviation in this report is converted into a prediction, wheel ranking or wagering rule.

## Reproduction

Run the complete comparison with:

```bash
python3 analyze_historical_cycle_distribution.py
```

The command writes the detailed local reports to:

```text
_work/historical-cycle-comparison.txt
_work/historical-cycle-comparison.json
```

The `_work/` outputs are reproducible local artifacts and are intentionally not committed.

## Implementation map

```text
strategies/coverage_cycle_history.py
analyze_historical_cycle_distribution.py
tests/test_coverage_cycle_history.py
tests/test_analyze_historical_cycle_distribution.py
```

## Status

Historical absorption-time comparison completed at commit `47a8562`.

The mathematical model, independent transition verification, absorption metrics, complete state atlas and historical cycle comparison are now all reproducible from repository code.
