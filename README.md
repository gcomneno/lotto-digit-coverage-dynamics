# Lotto Digit Coverage Dynamics

An exact finite-state model of decimal digit coverage in Italian Lotto draws.

The project models the digits still missing from a natural coverage cycle as an
absorbing stochastic process, derives its theoretical properties and compares
them with historical observations.

The repository is a mathematical and reproducibility project. It is not a
betting system, a number-selection tool or evidence that past draws alter future
draw probabilities.

## Main result

For one wheel:

- Lotto numbers are represented as `01`–`90`;
- the leading zero is part of the representation;
- a state is the set of decimal digits still missing from the current cycle;
- there are \(2^{10}=1,024\) states;
- the empty set is absorbing in the mathematical model;
- after completion, the natural historical process restarts from all ten
  digits missing.

The exact transition kernel is computed combinatorially and independently
verified by an integer dynamic program over all unordered five-number draws.

Current verification status:

| Quantity | Result |
|:---|---:|
| Unordered five-number draws | 43,949,268 |
| Observed digit-union masks | 968 |
| States verified | 1,024 |
| Transition cells verified | 58,848 |
| Maximum absolute discrepancy | 2.2894 × 10⁻¹⁵ |
| Non-empty states in the atlas | 1,023 |
| Structural symmetry classes | 27 |

The theoretical absorption time from the full ten-digit state has:

| Metric | Exact value |
|:---|---:|
| Mean | 3.506190 draws |
| Variance | 1.924821 |
| Standard deviation | 1.387379 |
| Median | 3 draws |
| 90th percentile | 5 draws |
| 95th percentile | 6 draws |
| 99th percentile | 8 draws |
| Completion within 3 draws | 60.47% |
| Completion within 5 draws | 92.28% |

## Historical comparison

The current continuous archive covers all draws from 3 January 2023 through
28 July 2026:

| Archive | Draw range |
|:---|:---|
| 2023 | 1–182 |
| 2024 | 1–209 |
| 2025 | 1–208 |
| 2026 | 1–120 |

After applying the documented left- and right-censoring rules, the pooled
history contains 2,253 complete natural cycles.

| Metric | Observed | Exact model |
|:---|---:|---:|
| Mean duration | 3.481580 | 3.506190 |
| Variance | 1.938964 | 1.924821 |
| Standard deviation | 1.392467 | 1.387379 |
| Median | 3 | 3 |
| 90th percentile | 5 | 5 |
| 95th percentile | 6 | 6 |
| 99th percentile | 8 | 8 |

Across the duration CDF through the observed maximum of 18 draws:

- maximum absolute difference: `0.013189`;
- mean absolute difference: `0.001867`.

These are descriptive pooled comparisons. Wheels share the extraction calendar
and are not treated as independent replicates for inferential testing.

## Exact-state interpretation

Under the ideal random-draw model, the exact missing-digit set is sufficient for
the future transition law.

Cycle age, the order of previous digit appearances and the duration of an
absence do not change the next-state probabilities once the current state is
known.

Digit identity matters:

- singleton states `{0}` through `{8}` close on the next draw with probability
  `68.1643%`;
- singleton state `{9}` closes on the next draw with probability `45.3005%`.

This difference follows from the decimal structure of `01–90`. It is not a
delay effect or a compensating force.

## Historical anomalies

The anomaly detector records four retrospective descriptive categories:

- A1 — unusually persistent open state;
- A2 — unusually rare immediate completion;
- A3 — unusually rare non-terminal transition;
- A4 — recurrence of the same primary anomaly key within a fixed window.

Using a primary threshold of `1%` over the continuous 2023–2026 archive:

| Category | Events |
|:---|---:|
| A1 | 21 |
| A2 | 3 |
| A3 | 12 |
| A4 | 0 |
| Total | 36 |

These events are historical labels, not evidence of a forecasting advantage.
At draw 120 of 28 July 2026, no A1–A4 anomaly was active.

## Quick verification

Run the complete automated suite:

```bash
python3 -m unittest discover -v
```

Verify the exact transition kernel independently:

```bash
python3 verify_transition_kernel.py \
    --output _work/transition-kernel-verification.json
```

Regenerate the complete state atlas:

```bash
python3 generate_state_atlas.py
```

Regenerate the structural analysis:

```bash
python3 generate_structural_analysis.py
```

Recalculate the continuous historical cycle comparison:

```bash
python3 analyze_historical_cycle_distribution.py
```

Recalculate historical structural classes and anomalies:

```bash
python3 analyze_historical_symmetry_classes.py
python3 analyze_coverage_anomalies.py
```

Inspect the current coverage state:

```bash
python3 analyze_current_coverage.py \
    --database data/lotto-2026.sqlite3
```

Update the current annual database:

```bash
python3 update_lotto_database.py
```

Browse a database in the terminal:

```bash
./view_lotto_database.sh
./view_lotto_database.sh --digit 1,7,9
```

## Repository map

```text
.
├── data/                         annual SQLite archives
├── docs/                         model and research documentation
├── generated/                    deterministic mathematical artifacts
├── strategies/                   reference model implementations
├── tests/                        automated mathematical and data tests
├── analyze_*.py                  historical and current-state analyses
├── generate_state_atlas.py       complete 1,023-state atlas
├── generate_structural_analysis.py
├── verify_transition_kernel.py   independent exhaustive verification
├── import_lotto.py               annual archive importer
├── update_lotto_database.py      safe complete-archive updater
└── view_lotto_database.sh        terminal database browser
```

## Documentation

Start with [`docs/index.md`](docs/index.md).

The canonical formal specification is
[`docs/finite-state-model.md`](docs/finite-state-model.md).

## Research boundary

Earlier predictive experiments did not produce a stable, independently useful
advantage after exact-state conditioning. That research line is closed and its
superseded implementations have been removed.

The retained conclusion is documented in
[`docs/predictive-research-closure.md`](docs/predictive-research-closure.md).

The 2022 archive remains deliberately unimported and uninspected. Additional
data should be introduced only for a concrete, predeclared mathematical or
validation question.
