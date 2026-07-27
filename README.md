# Lotto Digit Coverage Dynamics

Exact combinatorial and Markov analysis of digit-coverage cycles in Italian
Lotto draws.

The project studies how the decimal digits `0–9` accumulate across consecutive
draws on each Lotto wheel.

Its central question is not:

> Which number or digit will be drawn next?

It is:

> Given the digits still missing from the current coverage cycle, how close is
> that cycle to completion?

The project provides:

- exact combinatorial probabilities;
- an absorbing Markov-chain model;
- historical calibration checks;
- leakage-safe walk-forward replay;
- immutable live prequential forecasts;
- reproducible SQLite datasets and Python analyses.

## Main conclusion

The near-complete coverage of digits after a small number of draws is a real
combinatorial phenomenon.

No replicable evidence was found that a digit becomes more likely to appear
merely because it has been absent for several consecutive draws.

The useful state variable is instead the complete set of digits still missing
from the current cycle.

> Individual digits do not accumulate probability. Coverage accumulates
> completeness.

The Markov model measures this completeness through:

- probability of completion within `1`, `2`, `3`, or `5` draws;
- exact expected number of draws remaining;
- transition probabilities between missing-digit states.

It does not predict winning numbers and does not establish a gambling
advantage.

## Current status

The model has been validated through several distinct procedures.

| Validation | Cases | Expected | Observed | Difference |
|---|---:|---:|---:|---:|
| 2025 next-draw calibration | 2,248 states | 28.63% | 28.11% | -0.52 pp |
| 2025 completion within 2 draws | 2,242 states | 57.09% | 56.38% | -0.71 pp |
| 2025 completion within 3 draws | 2,239 states | 79.53% | 78.29% | -1.23 pp |
| 2025 completion within 5 draws | 2,238 states | 95.73% | 95.76% | +0.02 pp |
| 2025 residual expectation | 2,238 states | 2.524 draws | 2.544 draws | +0.020 |
| 2025 walk-forward replay, draws 101–208 | 1,188 forecasts | 336.994 closures | 334 closures | -2.994 |
| 2026 through draw 118, next-draw calibration | 617 states | 28.11% | 27.23% | -0.89 pp |
| 2026 through draw 118, residual expectation | 595 states | 2.534 draws | 2.565 draws | +0.031 |
| Holdout draw 119 | 11 wheels | 3.607 closures | 3 closures | -0.607 |

The first live immutable prequential forecast has been frozen for draw `120`:

```text
prequential/forecasts/draw-0120.json
```

A simple example

Suppose a wheel has already covered all digits except 9.

The state is:

{9}

Its exact model metrics are approximately:

Metric	Value
Completion on next draw	45.30%
Completion within 2 draws	70.08%
Completion within 3 draws	83.63%
Completion within 5 draws	95.10%
Expected remaining draws	2.207

If the missing state is {3,9}, the next-draw completion probability falls to
about 29.46%, while the expected remaining duration rises to about 2.484
draws.

The identity of the missing digits therefore matters, not only their count.

Requirements
Python 3.11 or newer;
SQLite support in Python;
no external Python dependencies for the core analyses.

Run the complete test suite:

python3 -m unittest discover -v
Primary commands

Inspect the current coverage state:

python3 analyze_current_coverage.py \
    --database data/lotto-2026.sqlite3

Validate completion probabilities:

python3 analyze_coverage_markov_validation.py \
    --database data/lotto-2025.sqlite3

Validate expected residual duration:

python3 analyze_coverage_markov_residuals.py \
    --database data/lotto-2025.sqlite3

Run the historical walk-forward replay:

python3 analyze_prequential_replay.py \
    --database data/lotto-2025.sqlite3 \
    --start-target 101 \
    --end-target 208 \
    --output _work/prequential-replay-2025-from-0101.json

Freeze the forecast for the next available draw:

python3 create_prequential_forecast.py \
    --database data/lotto-2026.sqlite3

A forecast file is written exclusively and cannot be overwritten by the same
command.

Repository structure
.
├── analyze_*.py
├── create_prequential_forecast.py
├── data/
│   ├── lotto-2025.sqlite3
│   └── lotto-2026.sqlite3
├── docs/
├── prequential/
│   └── forecasts/
├── strategies/
├── tests/
└── _work/

_work/ contains reproducible local reports and temporary databases and is not
committed.

Documentation
Documentation index
Research question
Mathematical model
Methodology
Validation results
Historical walk-forward replay
Live prequential protocol
Reproducibility
Limitations
Glossary
Earlier research findings
Responsible interpretation

This repository is a statistical and software-engineering research project.

It does not:

forecast specific numbers;
demonstrate a profitable betting strategy;
alter the probability of any Lotto combination;
justify increasing gambling expenditure;
claim that delayed digits are due.

The model describes the natural probability of a coverage process that is
already implied by random draws.
