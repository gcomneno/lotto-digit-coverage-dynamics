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
- a complete 1,024-state absorbing Markov-chain model;
- independent verification of the transition kernel;
- absorption-time moments, distributions and quantiles;
- a machine-readable atlas of all 1,023 non-empty states;
- historical calibration and cycle-duration comparisons;
- reproducible SQLite datasets and Python analyses;
- a documented record of rejected predictive hypotheses.

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

- probability of completion within `1`, `2`, `3`, `5`, or `10` draws;
- exact expected number of draws remaining;
- variance and selected absorption-time quantiles;
- transition probabilities between missing-digit states;
- a deterministic mathematical difficulty ranking.

It does not predict winning numbers and does not establish a gambling
advantage.

## Current status

The predictive research line is closed. The maintained project direction is
exact mathematical modelling, reproducible verification and historical
description.

| Milestone | Result |
|:---|:---|
| Formal specification | Complete finite-state model over all 1,024 states |
| Independent kernel verification | 58,848 transition entries compared, zero discrepancies above tolerance |
| Maximum kernel difference | \(2.289 \times 10^{-15}\) |
| Absorption metrics | Mean, variance, probability mass and quantiles |
| Complete state atlas | 1,023 non-empty states in CSV and JSON |
| Continuous historical segment | 1,879 complete cycles from 2023–2025 |
| Historical mean | 3.480043 observed versus 3.506190 theoretical |
| Historical quantiles | Q50, Q90, Q95 and Q99 all match the theoretical values |
| Maximum historical CDF difference | 1.3760 percentage points |
| Separate partial 2026 segment | 171 complete cycles, analysed independently |

The 2026 archive begins at draw 60 on 14 April 2026. It is intentionally kept
separate from the continuous 2023–2025 segment because draws 1–59 are absent.

The complete atlas is available in:

- `generated/coverage-state-atlas.csv`;
- `generated/coverage-state-atlas.json`;
- `docs/state-atlas-summary.md`.

The detailed historical conclusion is documented in:

- `docs/historical-cycle-distribution.md`.

No historical deviation has been promoted into a prediction, wheel ranking or
wagering rule.

## A simple example

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
