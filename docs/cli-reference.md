# Command-line reference

**English** | [Italiano](it/cli-reference.md)

Run commands from the repository root.

## Unified entry point

```bash
./lotto.py list
./lotto.py <command> [tool arguments]
./lotto.py help <command>
```

`lotto.py` is a thin dispatcher. It does not reimplement the mathematical or
data logic: it selects one existing executable, forwards the remaining
arguments unchanged and returns that executable’s exit status.

All original scripts remain directly executable.

## Commands

| Command | Underlying executable | Purpose |
|:---|:---|:---|
| `current` | `analyze_current_coverage.py` | Current Markov ranking, transversal row and active anomalies |
| `update` | `update_lotto_database.py` | Safe complete-archive update |
| `db` | `view_lotto_database.sh` | Terminal database browser |
| `anomalies` | `analyze_coverage_anomalies.py` | Historical A1–A4 anomaly analysis |
| `completion` | `analyze_coverage_completion.py` | Natural-cycle completion analysis |
| `residuals` | `analyze_coverage_markov_residuals.py` | Theoretical and observed residual-time comparison |
| `validation` | `analyze_coverage_markov_validation.py` | Empirical calibration of Markov probabilities |
| `digit-coverage` | `analyze_digit_coverage.py` | Digit coverage over moving windows |
| `return-times` | `analyze_digit_return_times.py` | Digit return-time analysis |
| `cycles` | `analyze_historical_cycle_distribution.py` | Historical cycle-duration comparison |
| `symmetry-history` | `analyze_historical_symmetry_classes.py` | Historical structural-class analysis |
| `atlas` | `generate_state_atlas.py` | Complete 1,023 non-empty-state atlas |
| `structure` | `generate_structural_analysis.py` | Structural classes and information-loss artifacts |
| `kernel` | `verify_transition_kernel.py` | Independent exhaustive transition-kernel verification |
| `import` | `import_lotto.py` | Annual archive import |

Aliases:

- `now` → `current`;
- `view` → `db`;
- `digits` → `digit-coverage`;
- `returns` → `return-times`;
- `cycle-distribution` → `cycles`;
- `symmetry` → `symmetry-history`.

## Current-state cutoffs

```bash
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

`--to` selects every draw whose date is not later than the given ISO date.
`--to-num` selects every draw whose annual draw number is not greater than the
given positive integer. Both limits are inclusive.

`--to_num` is accepted as an equivalent spelling. Date and draw-number cutoffs
are mutually exclusive.

When the database also contains a later aligned draw, the report displays that
next draw separately and does not use it in the historical cutoff state.

## The `TUTTE` row

The final `TUTTE` row of `current` considers only wheels whose current natural
cycle has positive age.

Let:

- `P` be the union of their most-present digit sets;
- `M` be the union of their missing-digit sets;
- `C = P ∩ M`.

The reported `Numeri` field contains every valid number `01`–`90` formed by an
ordered pair of distinct digits from `C`.

For example, `C={1,6,7}` produces:

```text
{16,17,61,67,71,76}
```

This construction is deterministic and reproducible. It is a transversal
description and an optional virtual-play convention, not a forecasting result.
Every fixed Lotto number still has the same one-draw inclusion probability
under the ideal model.

## Examples

```bash
./lotto.py current
./lotto.py current --to-num 119
./lotto.py update --year 2026
./lotto.py anomalies --help
./lotto.py kernel \
    --output _work/transition-kernel-verification.json
./lotto.py db --digit 1,6,7
```
