# Coverage-hit artifacts

This directory contains the preserved results of the historical
digit-coverage hit analysis.

The experiment measures, for each combination of TOP digits and
missing digits, how often the following Lotto draw reaches the defined
near-completion threshold:

- when one digit is missing, that digit must be observed;
- when `N > 1` digits are missing, at least `N - 1` must be observed.

## Historical partitions

The five non-overlapping historical partitions are:

- 1871–1900;
- 1901–1950;
- 1951–2000;
- 2001–2020;
- 2021–2025.

The 1871–2025 report is the canonical continuous calculation over the
whole historical archive. It is not the arithmetic sum of the five
partition reports because coverage state continues across their
boundaries.

## Files

Each interval has:

- a human-readable `.txt` report;
- a machine-readable `.csv` report.

`manifest.json` records provenance and SHA-256 checksums for the source
databases and generated artifacts.

## Reproduction

The reports were generated with commands equivalent to:

```bash
./lotto.py coverage-hits \
  --database data/lotto-INTERVAL.sqlite3 \
  --last DRAW_COUNT \
  --sort=missing,top \
  --csv coverage-hits-INTERVAL.csv
```

These artifacts are versioned because complete historical regeneration,
especially for 1871–2025, is computationally expensive.
