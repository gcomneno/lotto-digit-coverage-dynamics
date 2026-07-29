# Coverage anomalies

**English** | [Italiano](it/coverage-anomalies.md)


## Purpose

`analyze_coverage_anomalies.py` identifies rare events in the natural
decimal-digit coverage process.

The detector is retrospective and descriptive. An anomaly indicates that
the observed event had low probability under the exact finite-state model.

It does not alter the probability of any subsequent draw and is not a
predictive signal.

## Observation protocol

For each wheel, observations begin only after the first complete coverage
seen in the archive. The initial left-censored segment is excluded.

For every later draw, the detector records:

- the source state: digits missing before the draw;
- the target state: digits still missing after the draw;
- the exact transition probability `K(S, T)`;
- the natural cycle and sequential transition indexes.

A completed cycle resets the next source state to all ten digits.

## Default thresholds

```text
Primary probability threshold: 1%
Recurrence window:              10 valid transitions
Recurrence threshold:           1%
```

The thresholds are fixed before inspecting the resulting events.

## A1 — Persistence anomaly

A1 identifies a natural cycle that remains open longer than expected from
an earlier state in that same cycle.

For source state `S` and horizon `h`, the event probability is:

```text
P(tau_S > h) = 1 - P(tau_S <= h)
```

An event is emitted when this probability is at most the primary
threshold.

Implementation rules:

- only non-closing transitions can trigger A1;
- only the first threshold crossing is emitted for each natural cycle;
- at most one A1 event exists per wheel and cycle;
- `right_censored` distinguishes an incomplete final cycle from a cycle
  whose later completion is present in the archive.

A1 measures persistence of the cycle. It does not require the exact state
to remain unchanged throughout the horizon.

## A2 — Immediate closure anomaly

A2 identifies an immediate transition from a non-empty source state to
the empty state:

```text
S -> {}
```

Its probability is the exact transition probability:

```text
K(S, {})
```

The event is emitted when this probability is at most the primary
threshold.

A closure from the complete ten-digit state is therefore an A2 event
because its exact probability is approximately `0.038226%`.

## A3 — Non-terminal transition anomaly

A3 identifies a rare progress transition:

```text
S -> T
```

where:

```text
{} != T != S
```

The exact cell probability `K(S, T)` is stored in
`atom_probability`.

The detector does not compare this cell probability directly with the
threshold. A large discrete state space can contain many individually
small cells whose combined behaviour is ordinary.

A3 instead uses the probability mass of all non-terminal progress
transitions from `S` whose exact probability is no greater than the
observed transition:

```text
sum K(S, U)

for every non-empty U != S
where K(S, U) <= K(S, T)
```

This discrete lower-tail mass is stored in `conditional_probability`.

A3 is emitted when that mass is at most the primary threshold.

This prevents common transitions from being classified as anomalous
merely because their exact cells are individually small.

## A4 — Recurrence anomaly

A4 identifies the recurrence of the same primary anomaly key:

- on the same wheel;
- within the configured number of valid transitions.

The recurrence key represents the same A1, A2 or A3 phenomenon. It omits
incidental details such as dates and the observed gap.

Conditioned on the first anomaly already having occurred, the detector
uses the conservative upper bound:

```text
min(1, recurrence_window * current_probability)
```

A4 is emitted when this bound is at most the recurrence threshold.

The descriptive field `pair_probability` contains:

```text
previous_probability * current_probability
```

It is not treated as the probability or p-value of recurrence within the
whole window.

An archive containing no A4 events is a valid result.

## Severity

Severity is derived from the event probability:

| Probability | Severity |
|---:|---|
| `p <= 0.1%` | `extreme` |
| `0.1% < p <= 1%` | `rare` |
| `1% < p <= 5%` | `notable` |
| `p > 5%` | `ordinary` |

With the default primary threshold, A1, A2 and A3 events are normally
classified as `rare` or `extreme`.

## Non-duplication rules

The detector validates that:

- exact event identities are unique;
- at most one A1 exists for each wheel and natural cycle;
- a transition cannot be classified simultaneously as A2 and A3;
- every A4 event references an earlier primary event;
- all reported probabilities belong to `[0, 1]`.

The report also counts primary events attached to the same transition so
that semantic overlaps remain visible.

## Outputs

The analyzer writes only local derived reports:

```text
_work/coverage-anomalies-<segment>.csv
_work/coverage-anomalies-<segment>.json
```

The CSV contains one row per event.

The JSON additionally records:

- the detector configuration;
- category definitions;
- summary counts;
- the recurrence-probability caveat.

Generated reports under `_work/` are not committed.

## Interpretation boundary

The detector answers:

> How unusual was the event that has already occurred under the exact
> coverage model?

It does not answer:

> What should happen next to compensate for that event?

After every anomaly, the next-draw probabilities are derived exclusively
from the new coverage state.
