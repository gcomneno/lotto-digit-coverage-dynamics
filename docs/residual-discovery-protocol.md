# Residual discovery protocol

## Objective

Use the 2023 historical prequential replay as a discovery sample to test
whether any observable feature contains information about next-draw cycle
completion beyond the exact-state Markov probability.

The 2022 archive remains sealed and must not be imported or inspected until
one final hypothesis has been selected and frozen.

## Discovery sample

- database: `data/lotto-2023.sqlite3`;
- replay: `_work/prequential-replay-2023-0020-0182.json`;
- target draws: 20–182;
- observations: 1,793;
- wheels: 11;
- leakage: none.

For each observation:

- outcome: next-draw completion, encoded as 0 or 1;
- expected probability: one-draw Markov completion probability;
- residual: outcome minus expected probability;
- variance: `p * (1 - p)`.

## Candidate feature families

The exploratory screen is limited to these predefined families:

1. wheel;
2. number of missing digits;
3. identity of the missing digit when exactly one digit is absent;
4. whether digit 9 belongs to the missing state;
5. cycle-age buckets: 0, 1, 2, 3, 4, and 5 or more;
6. exact missing state, only for states with at least 30 observations.

No additional feature family or threshold may be introduced after examining
the results without being labelled as a separate post-hoc analysis.

## Metrics

For every eligible group, report:

- number of observations;
- expected completions;
- observed completions;
- expected and observed rates;
- observed-minus-expected delta;
- standardized residual:
  `sum(y - p) / sqrt(sum(p * (1 - p)))`;
- nominal two-sided p-value;
- Benjamini–Hochberg q-value within the feature family.

## Temporal stability

Every candidate must also be evaluated separately in the first and second
chronological halves of the 2023 replay.

A candidate is considered directionally stable only when both halves have a
non-zero residual with the same sign.

## Promotion rule

A candidate may be promoted to a frozen 2022 hypothesis only when:

- it contains at least 30 observations overall;
- its Benjamini–Hochberg q-value is at most 0.05;
- its residual has the same direction in both chronological halves;
- the rule can be expressed without changing thresholds after inspection.

At most one candidate may be promoted.

If no candidate satisfies all requirements, the discovery stage ends without
a hypothesis and the 2022 archive remains sealed.

## Interpretation

This is an exploratory screen, not evidence of a predictive advantage.

Any promoted candidate must be tested exactly once on the untouched 2022
archive. Failure on 2022 rejects the candidate; parameters must not be retuned
on the holdout.
