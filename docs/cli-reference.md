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
| `rolling-frequency` | `analyze_rolling_frequency.py` | Walk-forward rolling-frequency backtest against equal-size random sets |
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
- `rolling` → `rolling-frequency`;
- `returns` → `return-times`;
- `cycle-distribution` → `cycles`;
- `symmetry` → `symmetry-history`.

## Rolling-frequency backtest

```bash
./lotto.py rolling-frequency
./lotto.py rolling-frequency --window-size 6
./lotto.py rolling-frequency --repetitions 1000 --seed 20260731
```

The default run:

- reads the 2023–2026 annual archives in read-only mode;
- evaluates windows `3`, `6`, `8` and `12`;
- uses 2023–2025 as the development period;
- uses 2026 as the held-out period;
- performs `1,000` equal-size random replications per comparison;
- writes deterministic CSV and JSON artifacts under `_work/`.

`--database` and `--window-size` may be repeated. Output paths can be changed
with `--csv-output` and `--json-output`.

The command reports candidate exposure, number hits, ambo hits, random means,
observed-to-random ratios and empirical one-sided p-values. It does not report
virtual stake, payout or financial return.

See the complete
[rolling-frequency research report](rolling-frequency-backtest.md).

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

- `P` be the union of the most-present digit sets across all active wheels;
- the maximum group contains every active wheel tied for the highest
  one-draw completion probability;
- `M` be the union of the missing-digit sets only across that maximum group;
- `C = P ∩ M`.

The reported `Numeri` field contains every valid number `01`–`90` formed by an
ordered pair of digits from `C`, including pairs with repeated digits.

For example, `C={1,6,7}` produces:

```text
{11,16,17,61,66,67,71,76,77}
```

This construction is deterministic and reproducible. It is a transversal
description and an optional virtual-play convention, not a forecasting result.
Every fixed Lotto number still has the same one-draw inclusion probability
under the ideal model.

## Database highlighting and historical tracing

### Manual highlighting

The `db` command supports two independent, composable selectors:

- `--digit DIGITS` highlights individual digits from `0` to `9`;
- `--number NUMBERS` highlights complete Lotto numbers from `1` to `90`.

Both options may be repeated and each value may contain a comma-separated list. Repeated selections are deduplicated. A selected number is rendered using its two-digit database form, so `--number 1` highlights `01`. When a complete number and one of its digits are both selected, complete-number highlighting takes precedence.

### Reference-draw historical occurrences

`--latest-occurrences [DRAW_NUMBER]` traces the five reference numbers
independently on every wheel.

Without `DRAW_NUMBER`, the command deterministically selects the latest complete
draw by its `(draw_date, draw_number)` tuple. With a positive integer, it
resolves exactly one reference draw with that number and treats its tuple as the
inclusive historical cutoff.

In this mode:

- the reference draw is rendered immediately below the header;
- the reference and all earlier draws are shown in descending chronological order;
- draws later than an explicit reference are excluded;
- the five numbers on each wheel receive five distinct positional colors;
- every earlier occurrence keeps the corresponding color only on that same wheel;
- identical values on other wheels are not matches;
- the palette is reused independently for every wheel.

The mode is mutually exclusive with `--digit` and `--number`. When
another database is selected, use one of these unambiguous forms:

```bash
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```

The database is never reordered or mutated. This is retrospective
visualization, not a predictive signal, probability adjustment or betting
recommendation.

## Examples

```bash
./lotto.py current
./lotto.py current --to-num 119
./lotto.py update --year 2026
./lotto.py anomalies --help
./lotto.py rolling-frequency
./lotto.py kernel \
    --output _work/transition-kernel-verification.json
./lotto.py db --digit 1,6,7
./lotto.py db --number 1,17,90
./lotto.py db --digit 7 --number 17,90
./lotto.py db --latest-occurrences
./lotto.py db --database data/lotto-2025.sqlite3 --latest-occurrences 100
```
