# Twin-number statistical analysis

This analysis studies the fixed family `11`, `22`, `33`, `44`, `55`, `66`, `77`, and `88`.

Its goal is not to build a betting strategy. It tests a falsifiable question: **does coverage-state information available before a draw reproducibly change the frequency of the corresponding twin number?**

## Null model

For one fixed twin `dd` on one fixed wheel, five distinct numbers are drawn from `1..90`. Therefore:

```text
P(dd) = 5 / 90 = 1 / 18 = 5.555...%
```

Every primary comparison uses this exact null. Merely observing a twin somewhere in a draw is not an anomaly.

## Ex-ante construction

Each wheel history is synchronized at the first fully observed digit-coverage completion. For every later target draw, the state is frozen **before** reading the five target numbers.

For every digit `d` from `1` through `8`, the analyzer records predeclared conditions:

- `baseline`: every synchronized target draw;
- `missing`: `d` is still missing in the active natural cycle;
- `top`: `d` is among the digits with the maximum occurrence count in the active cycle;
- `last-missing`: `{d}` is the complete missing set;
- `missing-age>=3`: `d` is missing and the active cycle already contains at least three draws;
- `return-gap:1-4`, `5-9`, `10-19`, `20+`: fixed bins for the number of wheel draws since the same twin last appeared.

The empty state immediately after cycle completion does not generate `missing` or `top` conditions: all digits are trivially missing there and that reset state carries no selective information.

## Reported statistics

For every condition/twin pair the report includes:

- number of cases;
- observed hits;
- expected hits under `1/18`;
- observed frequency;
- absolute lift over the null;
- 95% Wilson interval;
- exact two-sided binomial p-value;
- Benjamini-Hochberg q-value for exploratory conditions.

A row is labelled `CANDIDATO`/candidate only when all of these hold:

1. at least 200 cases;
2. Benjamini-Hochberg `q < 0.05`;
3. the 95% Wilson interval excludes `1/18`.

That label is intentionally weaker than “signal” or “trigger”.

## Inferential boundary

Wheels share a draw calendar, and conditions for the same twin overlap. Pooled analysis is therefore an **exploratory screen**, not a collection of independent replications.

Any historical candidate must be frozen as a hypothesis and tested on chronologically later data not used for discovery, or through a forward test. Without that validation it remains descriptive.

If no condition passes the gate, the correct result is explicit:

```text
Nessun trigger sui numeri gemelli statisticamente supportato.
```

## CLI

```bash
./lotto.py twins
./lotto.py gemelli
```

The default database is `data/lotto-1871-2025.sqlite3`. Periods and wheels can be restricted:

```bash
./lotto.py twins --from-date 2001-01-01 --to-date 2025-12-31
./lotto.py twins --wheel Milano
```

The command also writes reproducible reports to `_work/twin-number-statistics.csv` and `_work/twin-number-statistics.json`.
