# Mathematical model roadmap

## Project direction

The project now focuses on the part of the work that is exact, reproducible
and mathematically verifiable:

> Model decimal digit coverage in Italian Lotto draws as a finite-state
> absorbing stochastic process, derive its properties and compare those
> properties with historical observations.

The objective is understanding and verification, not draw selection.


## Completion status

| Phase | Status | Main output |
|:---|:---|:---|
| Phase 1 — Formal specification | Complete | `docs/finite-state-model.md` |
| Phase 2 — Independent transition verification | Complete | `verify_transition_kernel.py` |
| Phase 3 — Absorption metrics | Complete | `strategies/coverage_markov.py` |
| Phase 4 — Complete state atlas | Complete | `generated/coverage-state-atlas.csv` and `.json` |
| Phase 5 — Structural analysis | Next | Set-inclusion structure and identity effects |
| Phase 6 — Empirical validation | Core comparison complete | `docs/historical-cycle-distribution.md` |
| Phase 7 — Reproducibility and presentation | In progress | Documentation and final synthesis |

The transition kernel has been verified over all 1,024 states by two
conceptually independent constructions. The complete atlas contains all 1,023
non-empty states and is reproducible byte for byte.

The continuous 2023–2025 historical segment contains 1,879 complete natural
cycles. Its observed mean, variance, selected quantiles and cumulative
distribution closely match the exact absorption-time benchmark.

Predictive research remains closed.

## Core object

For one wheel, define the state as the set of decimal digits still missing
from the current coverage cycle.

The complete state space is:

\[
\mathcal{S} = \mathcal{P}(\{0,1,\ldots,9\})
\]

and contains \(2^{10} = 1024\) states.

- The initial state is the set of all ten digits.
- Each draw removes every digit observed in its five two-digit numbers.
- The empty set is the absorbing state.
- After absorption, a new coverage cycle begins.

Numbers are always represented with two digits, so values such as `01`, `06`
and `09` contribute a leading zero.

## Mathematical foundation

The model must explicitly preserve the non-uniform decimal structure of the
numbers `01–90`.

In particular:

- digits are not interchangeable;
- digit `9` has a different occurrence distribution from digits `0–8`;
- a state is determined by the identities of its missing digits, not only by
  their count;
- transition probabilities depend on the current state and the digit set
  produced by the next draw;
- cycle age and prior path do not alter the transition law once the exact
  state is known under the model.

## Phase 1 — Formal specification

Produce a mathematical specification covering:

1. the sample space for one wheel draw;
2. two-digit representation of numbers `01–90`;
3. the digit-set mapping of a draw;
4. the probability distribution over observed digit sets;
5. the transition kernel between missing-digit states;
6. the absorbing empty state;
7. restart semantics after completion;
8. assumptions and scope of the model.

Acceptance criteria:

- every symbol is defined;
- implementation terminology matches the mathematical terminology;
- transition and completion quantities have unambiguous definitions;
- assumptions are separated from empirically tested conclusions.

## Phase 2 — Independent transition verification

The transition engine must be checked by two conceptually independent
methods wherever computationally feasible.

Candidate verification methods:

- the existing combinatorial or dynamic-programming implementation;
- exhaustive enumeration of the one-draw outcome space;
- brute-force checks on selected small states;
- Monte Carlo simulation used only as an approximate diagnostic.

Required invariants:

- outgoing transition probabilities sum to one;
- transitions never add missing digits;
- the empty state transitions to itself with probability one;
- impossible transitions have probability zero;
- one-step completion probability equals the transition probability to the
  empty state;
- equivalent calculations from independent implementations agree within a
  defined numerical tolerance.

## Phase 3 — Absorption metrics

For every non-empty state, derive or compute:

- one-draw completion probability;
- completion probability within 2, 3, 5 and 10 draws;
- expected remaining draws until absorption;
- variance of the remaining absorption time;
- selected quantiles of the absorption-time distribution;
- probability mass function up to a documented truncation horizon.

Required mathematical checks:

- cumulative completion probability is non-decreasing with the horizon;
- it converges towards one;
- expected time is finite for every non-empty state;
- a single-missing-digit state agrees with the corresponding geometric
  distribution;
- Bellman equations are satisfied numerically.

## Phase 4 — Complete state atlas

Generate an atlas for all 1,023 non-empty states.

Each row should contain:

- canonical missing-state representation;
- number of missing digits;
- one-draw completion probability;
- completion probabilities at the predefined horizons;
- expected remaining draws;
- variance and selected quantiles;
- a stable difficulty ranking;
- symmetry or near-symmetry annotations where mathematically justified.

The atlas is descriptive, not a recommendation system.

Useful derived views include:

- easiest and hardest states;
- states grouped by cardinality;
- variation among states of equal cardinality;
- effect of including digit `9`;
- comparison between identity-aware and count-only summaries.

## Phase 5 — Structural analysis

Investigate properties of the transition system itself:

- partial-order structure induced by set inclusion;
- block-triangular ordering of the transition matrix;
- reachability between states;
- monotonicity under subset relations;
- dominant contributors to long absorption times;
- sensitivity to the decimal range `01–90`;
- comparison with hypothetical uniform-digit or `00–99` models.

Any claimed theorem must be either proven or explicitly labelled as a
computational conjecture.

## Phase 6 — Empirical validation

Historical archives from 2023–2026 are used only to evaluate how well the
mathematical model describes observed data.

Primary measures:

- expected versus observed completion counts;
- calibration by probability band;
- Brier score;
- log loss;
- residual distributions;
- annual stability;
- wheel-level descriptive stability;
- empirical frequencies of exact states;
- observed versus theoretical absorption-time distributions.

The main validation question is:

> Are observed deviations compatible with ordinary sampling variability
> around the exact-state model?

Historical variation must not be converted into a betting rule.

## Phase 7 — Reproducibility and presentation

The final repository should provide:

- a concise intuitive explanation;
- a complete formal model;
- tested reference implementations;
- reproducible state-atlas generation;
- machine-readable outputs;
- empirical validation reports;
- a documented limitations section;
- a record of rejected predictive hypotheses.

The intended final research deliverable is:

> **An exact finite-state model of decimal digit coverage in Italian Lotto
> draws**

## Testing policy

Every mathematical property implemented in code should have a corresponding
automated test whenever practical.

Priority tests include:

- state-space cardinality;
- canonical state encoding;
- transition normalization;
- absorbing-state behaviour;
- transition support restrictions;
- exact versus enumerated transition agreement;
- cumulative-probability monotonicity;
- single-digit geometric equivalence;
- Bellman-equation residuals;
- deterministic atlas generation.

Tests should favour exact arithmetic or tight documented tolerances over
broad approximate assertions.

## Data policy

Current roles of the archives:

- 2023: previously used as a controlled residual-discovery sample;
- 2024: previously used as an independent historical momentum test;
- 2025: development and historical replay;
- 2026: current-year validation and frozen forecasts;
- 2022: remains unimported and uninspected.

The 2022 archive is not presently required. It should remain untouched until
a specific mathematical validation question justifies an additional sample.

## Current milestone

The next mathematical milestone is structural analysis of the verified
transition system.

Primary questions:

1. characterize monotonicity under subset inclusion;
2. distinguish proved properties from computationally verified properties;
3. explain the exact symmetry of digits `0–8` and the asymmetry of digit `9`;
4. quantify the loss of information in count-only state summaries;
5. identify the states and digit identities contributing most to long
   absorption times.

Acceptance criteria:

- every structural claim is either proved or explicitly labelled as a
  computational result;
- subset-monotonicity checks cover the complete state space;
- identity-aware and count-only summaries are compared quantitatively;
- no structural observation is reinterpreted as a predictive signal;
- all new computations are deterministic and tested.
