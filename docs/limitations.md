# Limitations

## Model assumptions

The exact kernel describes one wheel draw as an unordered selection of five
distinct numbers from `01–90`.

All theoretical probabilities are conditional on that idealized sample space.
The project does not independently audit physical drawing equipment, operating
procedures or institutional data-generation processes.

## Historical dependence

The eleven wheels share the same extraction calendar. Their observations are
pooled for descriptive summaries, but the project does not assume that they are
independent experimental replicates.

Consequently, aggregate differences from theory are not converted directly
into classical p-values or claims of formal model acceptance.

## Archive scope

The current historical window runs from 3 January 2023 through 28 July 2026.

Although it contains 2,253 complete cycles, it is still a finite observation
window. Rare states and rare transitions may have small empirical sample sizes.

The 2022 archive is deliberately excluded and has not been inspected.

## Censoring

The first observed cycle for each wheel is left-censored and excluded. The last
open cycle is right-censored and excluded from complete-duration summaries.

These rules reduce bias but also discard some observations.

## Anomaly labels

A1–A4 events are retrospective descriptive labels.

Their thresholds are not presented as a complete multiple-testing procedure,
and A4 uses a conservative Bonferroni upper bound conditional on a preceding
primary anomaly.

An anomaly does not imply:

- manipulation;
- dependence in future draws;
- compensating behaviour;
- a profitable selection rule.

## Numerical representation

The underlying combinatorial counts are integers, but reported probabilities
and Bellman metrics use floating-point arithmetic.

Independent verification currently shows a maximum absolute transition
difference of approximately `2.29 × 10⁻¹⁵`, well below the configured
`1 × 10⁻¹²` tolerance.

## Current-state outputs

Current wheel states change whenever the annual archive is updated. They are
operational snapshots, not stable research conclusions.

Documentation therefore records the archive cutoff explicitly and directs users
to regenerate the current-state report.

## External data availability

Annual database updates depend on the structure and availability of the
upstream archive page. The importer validates archive completeness and writes
databases atomically, but an upstream format change can require maintenance.

## No predictive claim

The project does not claim that:

- overdue digits become more likely;
- cycle age modifies exact-state probabilities;
- historical residuals create an exploitable edge;
- rare past transitions predict future rare transitions.

Earlier predictive experiments were closed after failing to produce a stable
result beyond the exact-state model.
