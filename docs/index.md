# Documentation index

**English** | [Italiano](it/index.md)


## Start here

- [Project overview](../README.md)
- [Methodology](methodology.md)
- [Limitations](limitations.md)
- [Reproducibility](reproducibility.md)
- [Command-line reference](cli-reference.md)
- [Glossary](glossary.md)

## Mathematical model

- [Canonical finite-state specification](finite-state-model.md)
- [Coverage state atlas summary](state-atlas-summary.md)
- [Structural symmetry analysis](structural-symmetry-analysis.md)

The formal specification defines the sample space, state space, transition
kernel, absorption metrics, natural-cycle restart semantics and verification
boundary.

## Historical comparison

- [Historical cycle distribution](historical-cycle-distribution.md)
- [Coverage anomalies](coverage-anomalies.md)
- [Rolling-frequency walk-forward backtest](rolling-frequency-backtest.md)

Historical reports compare observations with the exact-state model. They are
descriptive analyses and do not define betting rules.

## Closed research

- [Predictive research closure](predictive-research-closure.md)

The negative conclusion is retained for research accountability. Superseded
predictive implementations and frozen forecasts are not part of the publication
source of truth.

## Generated artifacts

The deterministic mathematical outputs are stored under `generated/`:

- `coverage-state-atlas.csv`;
- `coverage-state-atlas.json`;
- `coverage-symmetry-classes.csv`;
- `coverage-cardinality-loss.csv`;
- `coverage-structural-analysis.json`.

All five artifacts were regenerated at the July 2026 publication checkpoint
and matched their tracked versions byte for byte.
