# Methodology

**English** | [Italiano](it/methodology.md)


## Research objective

The project asks whether decimal digit coverage in one Italian Lotto wheel can
be represented exactly as a finite-state absorbing stochastic process and how
closely its derived properties match historical observations.

The objective is explanation and verification, not draw selection.

## Decimal representation

Every number is represented with two decimal positions:

```text
1  -> 01 -> {0,1}
9  -> 09 -> {0,9}
40 -> 40 -> {0,4}
77 -> 77 -> {7}
90 -> 90 -> {0,9}
```

The leading zero therefore contributes to digit coverage.

## State definition

Let \(D=\{0,1,\ldots,9\}\). A state \(S\subseteq D\) is the set of digits still
missing from the current cycle.

There are \(2^{10}=1,024\) states. The empty set is absorbing in the mathematical
chain. The natural historical process restarts from \(D\) after completion.

## Exact transition construction

One wheel draw is an unordered five-element subset of `01–90`, giving

\[
\binom{90}{5}=43,949,268
\]

possible draws.

Each number is mapped to a ten-bit digit mask. An integer dynamic program counts
how many five-number subsets generate each union mask. The resulting exact mask
distribution induces the transition kernel

\[
K(S,T)=P(S\setminus G(\omega)=T).
\]

A transition can only remove missing digits, so \(T\subseteq S\).

## Independent verification

The reference kernel is checked against a conceptually independent
integer-count construction over:

- all 1,024 states;
- all reachable transition cells;
- the complete five-number sample space.

At the July 2026 checkpoint:

- 968 digit-union masks were observed;
- 58,848 transition cells were compared;
- the maximum absolute discrepancy was
  `2.289401307420391 × 10⁻¹⁵`.

The tolerance used by the verifier is `1 × 10⁻¹²`.

## Derived quantities

For every non-empty state, the implementation computes:

- one-step completion probability;
- completion CDF over arbitrary horizons;
- probability mass function;
- expected remaining draws;
- variance and standard deviation;
- selected absorption-time quantiles;
- stable state-difficulty ranking.

Bellman recurrences exploit the fact that every proper successor contains fewer
missing digits.

## Structural analysis

The project verifies:

- monotonicity of the deterministic state update;
- stochastic ordering under set inclusion;
- exact decimal symmetries;
- loss of information from reducing a state to its cardinality.

The 1,023 non-empty states collapse into 27 exact structural classes:

- without digit `9`, digits `0–8` are interchangeable;
- with digit `9` missing, digit `0` becomes distinct while digits `1–8` remain
  interchangeable.

## Historical observation protocol

Annual SQLite archives are merged by date for each wheel.

At the current checkpoint the primary archive is continuous from 2023 through
draw 120 of 2026.

For natural cycles:

1. the initial left-censored cycle of each wheel is excluded;
2. completed cycles are retained;
3. the terminal incomplete cycle is recorded but excluded from complete-cycle
   duration summaries;
4. continuous year boundaries do not reset the cycle.

Wheels share the draw calendar. Pooled wheel observations are therefore
reported descriptively and are not treated as independent replicates.

## Exact-state historical comparisons

Historical analyses include:

- aggregate absorption-time distribution;
- one-step calibration by exact structural class;
- expected versus observed completion;
- residual remaining duration;
- retrospective anomaly labels A1–A4;
- current exact-state maturity.

The Markov property is interpreted conditionally: once the exact missing set is
known, cycle age and prior path do not change the theoretical transition law.

## Reproducibility boundary

Deterministic mathematical artifacts are tracked under `generated/`.
Transient reports and publication checks belong under `_work/`.

The 2022 archive remains unimported and uninspected. It is reserved for a future
question that is declared before the data are examined.
