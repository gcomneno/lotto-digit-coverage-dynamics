# Predictive research closure

## Status

**Closed on 2026-07-27.**

The project no longer pursues rules intended to predict or select a favourable
next Lotto draw.

This is a deliberate research conclusion, not a temporary lack of ideas.

## Reason for closure

The predictive programme tested several hypotheses using leakage-safe
historical replays, frozen rules, independent samples and explicit null-model
probabilities.

The tested lines included:

- completion of a state with one missing digit;
- numbers formed from the two missing digits;
- apparently favourable wheels;
- digit-9 and cycle-age interactions;
- accumulated one-shot momentum;
- calm-to-take-off momentum;
- a controlled residual-feature screen on the 2023 discovery sample.

None produced a stable and independently replicable advantage beyond the
probability already explained by the exact missing-digit state.

## Final controlled discovery result

The 2023 residual discovery screen used:

- target draws 20–182;
- 1,793 wheel-level prequential observations;
- six predefined feature families;
- exact two-sided Poisson-binomial tests;
- Benjamini–Hochberg correction within each family;
- first-half versus second-half directional stability;
- a minimum of 30 observations for promotion.

No candidate satisfied all promotion requirements.

The most visible nominal deviation was the Milano wheel:

- observations: 163;
- expected completions: 38.86;
- observed completions: 51;
- observed-minus-expected rate: +7.45 percentage points;
- nominal p-value: 0.0091;
- family-adjusted q-value: 0.0997.

It was therefore not promoted.

## Interpretation

The absence of a promoted signal does not prove that every conceivable
predictive relationship is impossible.

It does establish that:

1. the tested hypotheses did not demonstrate a robust advantage;
2. the exact-state Markov model already explains the observed completion
   probabilities well;
3. continuing to search through thresholds, wheels, digits or historical
   subgroups would materially increase the risk of multiple-testing artefacts
   and post-hoc storytelling;
4. the untouched 2022 archive must not be consumed merely to test a candidate
   that failed the discovery protocol.

## Closure rules

From this point onward:

- no `MOMENTUM-3` or threshold retuning is permitted inside the current
  research programme;
- no wheel, digit, age bucket or state may be selected because it appeared
  favourable in an already inspected sample;
- a negative result must not be inverted retroactively into a mean-reversion
  strategy;
- the 2022 archive remains unimported and uninspected;
- predictive claims must not be added to the project documentation;
- existing predictive scripts are retained as reproducible records of tested
  and rejected hypotheses.

A future predictive programme would require all of the following before any
new outcome data are inspected:

- a materially different scientific question;
- a written protocol;
- a fixed model and decision rule;
- a genuinely untouched validation sample;
- explicit correction for the planned number of tests.

Such a programme would be separate from the mathematical work defined in
`docs/mathematical-model-roadmap.md`.

## Research value of the negative results

The predictive work remains valuable because it demonstrates:

- how apparently convincing historical patterns disappear under replication;
- why exact state-dependent baselines are necessary;
- how leakage-safe prequential evaluation changes interpretation;
- why nominal significance is insufficient after multiple comparisons;
- how to preserve negative findings instead of silently discarding them.

The predictive branch is therefore closed with a useful conclusion:

> No tested rule demonstrated exploitable memory beyond the exact
> missing-digit state.
