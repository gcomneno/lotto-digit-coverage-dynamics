# Application report contracts

Related issues: #9, #12, #13, #14, #17.

The migrated interactive use cases expose presentation-neutral Python reports. `lotto_digit_coverage.application.reporting` defines the stable machine-readable boundary for those reports without turning internal dataclasses into a permanent public API.

## Versioning

The initial contract version is `1`.

Each payload contains:

- a stable `schema` name;
- `schema_version`;
- explicit primitive fields rather than ANSI/preformatted terminal text;
- a `number_representation` declaration: Lotto numbers are integers in `1..90` and interfaces display them with width 2 (`01`–`90`).

A breaking field/meaning change requires a schema-version change. Additive fields may be introduced conservatively when consumers can ignore unknown fields.

## Current status

`current_report_to_dict()` produces schema `lotto.current` and includes:

- analyzed target draw/date;
- per-wheel coverage states;
- raw Markov probabilities and expected remaining draws;
- coverage-hit ranking and historical evidence values;
- descriptive consensus;
- anomaly history and active anomalies;
- next-draw validation kept explicitly separate from the analyzed target.

Probabilities remain raw numeric values. Percent formatting belongs to an interface.

## Occurrence groups

`occurrence_group_report_to_dict()` produces schema `lotto.occurrence-groups` and includes:

- resolved reference draw and kind;
- configured group size;
- actual group sizes and date/draw ranges;
- ordered historical draw rows;
- per-wheel ordered reference numbers;
- occurrence counts aligned to those reference-number positions.

## Deterministic JSON

`dumps_current_report()` and `dumps_occurrence_group_report()` produce deterministic, UTF-8-friendly JSON with sorted object keys, indentation and a trailing newline. NaN/Infinity values are rejected.

These functions are application-level serialization helpers, not an HTTP API. A CLI `--json` surface may consume them later without changing the contracts.

## GUI boundary

A future GUI, built with GIADA UI as the canonical reusable design-system/component foundation, must consume the same application reports/contract semantics as the CLI. It must not parse CLI output or recreate research calculations.
