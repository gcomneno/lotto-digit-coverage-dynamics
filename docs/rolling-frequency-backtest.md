# Rolling-frequency walk-forward backtest

**English** | [Italiano](it/rolling-frequency-backtest.md)

## Research question

This experiment tests a predefined heuristic:

1. compute the most frequent decimal digit over the previous `N` draws on one
   wheel;
2. retain every digit tied for the maximum frequency;
3. combine those digits with the digits still missing from the active natural
   coverage cycle;
4. evaluate the generated numbers on the following draw.

The primary window is `N = 6`, selected before evaluation because six draws
approximately match the exact 95th percentile of natural-cycle duration.

The comparison windows are:

- `N = 3`;
- `N = 6`;
- `N = 8`;
- `N = 12`.

The experiment is descriptive. It does not assume that historical digit
frequency changes the probability of a future draw.

## Walk-forward protocol

For every eligible wheel and target draw:

- only draws strictly earlier than the target are used;
- digit frequency is calculated over the immediately preceding `N` draws;
- every maximum-frequency tie is retained;
- the natural-cycle state must already be synchronized;
- zero-age states immediately after cycle completion are excluded;
- valid Lotto numbers `01`–`90` are generated from:
  - frequent digit followed by missing digit;
  - missing digit followed by frequent digit;
  - repeated frequent digit when valid;
- duplicate candidates are removed;
- hits are evaluated only after the candidate set has been frozen.

The implementation uses a linear incremental scan of each wheel. It produces
the same observations as the original prefix-reconstruction implementation
while reducing the real four-year backtest from `118.111` seconds to `1.407`
seconds on the development machine, an `83.95×` acceleration.

## Temporal split

The split was fixed before evaluation:

| Period | Inclusive dates | Purpose |
|:---|:---|:---|
| Development | 2023-01-01 through 2025-12-31 | Comparison and diagnosis |
| Held-out | 2026-01-01 through 2026-12-31 | Out-of-sample evaluation |

The current 2026 archive ends at draw 120 of 28 July 2026.

The primary `N = 6` hypothesis remains primary regardless of the comparative
results of the other windows.

## Equal-size random baseline

Each observation is compared with a uniformly random candidate set having the
same size as the heuristic set.

The published run uses:

- `1,000` replications for every window and period;
- deterministic base seed `20260731`;
- a distinct deterministic derived seed for each comparison.

The empirical one-sided p-value is:

```text
(number of random replications at least as large as observed + 1)
-----------------------------------------------------------------
                         replications + 1
```

Candidate identity is ignored by the baseline. Only candidate-set size and the
five target numbers affect the simulated result.

## Results

### Development period, 2023–2025

| N | Number hits | Random mean | Ratio | p-value | Ambo hits | Random mean | Ratio | p-value |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 1,815 | 1,782.25 | 1.018 | 0.2058 | 428 | 409.07 | 1.046 | 0.2488 |
| 6 | 1,607 | 1,587.09 | 1.013 | 0.2967 | 322 | 299.18 | 1.076 | 0.1588 |
| 8 | 1,553 | 1,511.99 | 1.027 | 0.1359 | 299 | 263.95 | 1.133 | 0.0380 |
| 12 | 1,411 | 1,434.98 | 0.983 | 0.7542 | 236 | 234.37 | 1.007 | 0.4875 |

`N = 8` produced the strongest development-period ambo result. Its empirical
p-value of `0.0380` would look interesting if the same data had been used both
to discover and validate the window.

That result must therefore be judged against the held-out period.

### Held-out period, 2026

| N | Number hits | Random mean | Ratio | p-value | Ambo hits | Random mean | Ratio | p-value |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 367 | 350.69 | 1.047 | 0.1728 | 79 | 75.52 | 1.046 | 0.3916 |
| 6 | 320 | 324.82 | 0.985 | 0.6154 | 49 | 63.94 | 0.766 | 0.9391 |
| 8 | 305 | 307.54 | 0.992 | 0.5854 | 42 | 52.09 | 0.806 | 0.8991 |
| 12 | 292 | 290.02 | 1.007 | 0.4535 | 45 | 45.31 | 0.993 | 0.5145 |

The apparent `N = 8` development result did not replicate. Its held-out ambo
count was below the equal-size random mean.

The predefined primary window, `N = 6`, also produced fewer held-out ambi than
the random baseline. `N = 12` was almost exactly aligned with random
expectation. `N = 3` was modestly above the random mean, but well inside normal
baseline variation.

## Conclusion

No tested rolling-frequency window demonstrated a stable advantage over random
candidate sets of equal size.

In particular:

- the strongest development result failed out of sample;
- the predefined primary hypothesis did not outperform the held-out baseline;
- candidate exposure explains much of the raw hit count;
- no window supports a predictive or exploitable interpretation.

Past frequency and natural-cycle missing digits remain valid descriptive
properties of the archive. Their combination did not establish that any
candidate number became more likely in the next draw.

## Economic accounting excluded

Virtual stake, payout and return accounting were deliberately excluded from
the implemented scope.

The report therefore makes no claim about profitability and does not translate
historical hits into financial results. Candidate counts and covered ambo counts
remain available as explicit measures of combinatorial exposure.

## Reproduction

Run the predefined experiment:

```bash
./lotto.py rolling-frequency
```

The equivalent alias is:

```bash
./lotto.py rolling
```

The default machine-readable outputs are:

```text
_work/rolling-frequency-backtest.csv
_work/rolling-frequency-backtest.json
```

Custom example:

```bash
./lotto.py rolling-frequency \
    --window-size 6 \
    --repetitions 1000 \
    --seed 20260731 \
    --csv-output _work/rolling-n6.csv \
    --json-output _work/rolling-n6.json
```

`--database` and `--window-size` may be repeated.

All SQLite archives are opened read-only. During the reference execution, the
SHA-256 digest of every annual database was identical before and after the
backtest.

## Verification

The implementation is covered by tests for:

- rolling-window boundaries;
- leading zeroes;
- maximum-frequency ties;
- mixed-wheel rejection;
- candidate generation and deduplication;
- invalid values above `90`;
- no target-draw look-ahead;
- synchronized and zero-age state handling;
- chronological archive merging;
- inclusive period boundaries;
- deterministic equal-size random baselines;
- deterministic CSV and JSON output;
- unified CLI dispatch.

At this checkpoint the complete repository suite contains `242` tests.
