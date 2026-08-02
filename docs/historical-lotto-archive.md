# Historical Lotto archive, 1871–2025

**English** | [Italiano](it/historical-lotto-archive.md)

## Purpose

This document describes the historical SQLite archive published by the
repository and the facts learned while constructing it.

The archive is a data resource for reproducible historical analysis. It is not
evidence that past draws can predict future draws, and it does not alter the
probability of any valid Lotto number under the ideal random model.

## Published archive

The complete historical database is:

```text
data/lotto-1871-2025.sqlite3
```

It contains:

| Property | Value |
|:---|---:|
| First draw date | 1871-01-07 |
| Last draw date | 2025-12-30 |
| Draws | 10,779 |
| `draw_numbers` rows | 518,410 |
| Wheel observations | 103,682 |
| Global draw-number range | 1–10,779 |
| Minimum wheels in one draw | 6 |
| Maximum wheels in one draw | 11 |

The global `draw_number` is a repository-defined chronological sequence. It is
not the original annual contest number.

Every original annual archive remains available separately, and every
consolidated draw preserves its original date, source URL, import timestamp,
wheels, positions and values.

## Consolidated source blocks

The overall archive is assembled from five independently verified databases:

| Database | Period | Draws |
|:---|:---|---:|
| `data/lotto-1871-1900.sqlite3` | 1871-01-07 – 1900-12-29 | 1,565 |
| `data/lotto-1901-1950.sqlite3` | 1901-01-05 – 1950-12-30 | 2,609 |
| `data/lotto-1951-2000.sqlite3` | 1951-01-06 – 2000-12-30 | 2,807 |
| `data/lotto-2001-2020.sqlite3` | 2001-01-03 – 2020-12-31 | 2,886 |
| `data/lotto-2021-2025.sqlite3` | 2021-01-02 – 2025-12-30 | 912 |

Their draw counts sum exactly to the 10,779 draws in the overall database.

## Construction and verification

The consolidated databases were built chronologically from the annual SQLite
archives.

For every source and destination database, the procedure checked:

1. `PRAGMA integrity_check`;
2. `PRAGMA foreign_key_check`;
3. uniqueness of draw dates inside the consolidated range;
4. exactly five positions for every wheel present in a draw;
5. positions exactly equal to `1, 2, 3, 4, 5`;
6. five distinct values on each wheel;
7. equality between source and destination draw counts;
8. equality between source and destination `draw_numbers` counts;
9. chronological global numbering beginning at one;
10. preservation of historically variable wheel configurations.

Each destination was first built as a temporary SQLite file, verified, and
then installed atomically.

## Historical wheel configurations

The number of operational wheels was not constant across the entire archive.

| Numbers in draw | Operational wheels | Draws |
|---:|---:|---:|
| 30 | 6 | 3 |
| 35 | 7 | 177 |
| 40 | 8 | 3,424 |
| 45 | 9 | 57 |
| 50 | 10 | 3,778 |
| 55 | 11 | 3,340 |

A draw contains five values for each wheel that was actually present.

The `wheels` reference table may list a wheel even when that wheel had no
result in a historical draw. Therefore, historical completeness must be
determined from `draw_numbers`, not merely from membership in `wheels`.

## Wheel chronology

### Original seven-wheel configuration

The first archived draw, dated 1871-01-07, contains:

- Firenze;
- Milano;
- Napoli;
- Palermo;
- Roma;
- Torino;
- Venezia.

These seven wheels form the complete observed configuration through
1874-04-25.

### Bari

Bari first appears on 1874-05-02, at global draw number 174.

From that date through 1939-07-01, the regular configuration contains eight
wheels.

### Cagliari and Genova

Cagliari and Genova first appear together on 1939-07-08, at global draw number
3,575.

The regular configuration then reaches ten wheels.

### Wartime variability, 1943–1946

Between 1943 and 1946, wheel availability varies from draw to draw.

The archive contains configurations with:

- 6 wheels;
- 7 wheels;
- 8 wheels;
- 9 wheels;
- 10 wheels.

The data show missing wheel results during this period, but the archive alone
does not prove the administrative or historical cause of each absence.
Consequently, the repository records the observed configurations without
inventing missing values or assigning unsupported explanations.

From 1946-11-30 onward, the regular ten-wheel configuration is again present
continuously in the archived data until the introduction of the Nazionale
wheel.

### Nazionale

Nazionale first appears on 2005-05-04.

The 2001–2020 consolidated block contains:

- 458 draws without Nazionale;
- 2,428 draws with Nazionale.

The overall archive contains 3,340 draws with Nazionale through 2025-12-30.

## Wheel presence counts

The number of archived draws in which each wheel appears is:

| Wheel | First archived presence | Draws present |
|:---|:---|---:|
| Bari | 1874-05-02 | 10,606 |
| Cagliari | 1939-07-08 | 7,131 |
| Firenze | 1871-01-07 | 10,772 |
| Genova | 1939-07-08 | 7,203 |
| Milano | 1871-01-07 | 10,777 |
| Napoli | 1871-01-07 | 10,774 |
| Palermo | 1871-01-07 | 10,752 |
| Roma | 1871-01-07 | 10,777 |
| Torino | 1871-01-07 | 10,775 |
| Venezia | 1871-01-07 | 10,775 |
| Nazionale | 2005-05-04 | 3,340 |

Different counts among long-running wheels are real properties of the imported
archive. They must not be silently replaced with synthetic results.

## Draw-frequency evolution

The annual number of archived draws changes substantially over time.

### Predominantly weekly period

From 1871 through 1996, almost every year contains 52 or 53 draws.

Observed exceptions include:

- 1961: 51 draws.

The 52/53 pattern is consistent with a predominantly weekly calendar, but the
database itself records dates rather than the legal or administrative rule
that established the schedule.

### Transition during 1997–2005

The annual counts then rise:

| Year | Draws |
|---:|---:|
| 1997 | 95 |
| 1998 | 104 |
| 1999 | 104 |
| 2000 | 105 |
| 2001 | 105 |
| 2002 | 109 |
| 2003 | 105 |
| 2004 | 104 |
| 2005 | 133 |

These counts demonstrate a change in observed extraction frequency. They do
not, by themselves, document the official rule changes responsible for it.

### Higher-frequency period

From 2006 through 2019, annual totals are normally 156 or 157 draws.

Later totals are:

| Year | Draws |
|---:|---:|
| 2020 | 139 |
| 2021 | 156 |
| 2022 | 157 |
| 2023 | 182 |
| 2024 | 209 |
| 2025 | 208 |

The sharp changes are historical observations from the archive. External
official sources are required before assigning causes to them.

## What was learned about historical data handling

### Annual contest numbers cannot be merged directly

Annual databases restart their contest numbering. A multi-year archive must
therefore not use the original annual number as a globally unique key.

The consolidated databases assign a new chronological sequence while retaining
the date and source provenance.

### A fixed wheel count is historically incorrect

Requiring all historical draws to contain eleven wheels would incorrectly
reject valid data before 2005.

Requiring ten wheels would also reject:

- the seven-wheel period before Bari;
- the eight-wheel period before Cagliari and Genova;
- the variable configurations observed from 1943 through 1946.

Validation must be based on five values for every wheel actually present, plus
explicitly documented historical transitions.

### Reference tables and observations serve different roles

The `wheels` table is a stable dictionary of possible wheel identifiers.

The `draw_numbers` table records which wheels actually participated in each
draw. Historical analysis must use the latter to determine operational
configuration.

### Missing wheel results are not zero values

An absent wheel has no observation for that draw. It must not be represented
as zero, an empty five-number row, or a copy from another date.

### Consolidation should preserve provenance

The overall archive keeps:

- original draw date;
- original source URL;
- original import timestamp;
- exact wheel, position and value rows;
- metadata describing the source databases and global numbering policy.

## Appropriate analytical use

The overall archive enables:

- long-run digit-coverage studies;
- cycle-duration studies across historical regimes;
- comparisons by wheel and period;
- analysis of schedule-frequency changes;
- robustness checks across independently defined historical blocks;
- explicit exclusion or separate treatment of changing wheel configurations.

Analyses that aggregate wheels must remember that all wheels in a draw share
the same draw date and are not independent calendar replications.

Analyses spanning long periods should also account for:

- changing wheel availability;
- changing extraction frequency;
- different sample sizes by wheel;
- temporary partial configurations;
- the introduction dates of Bari, Cagliari, Genova and Nazionale.

## What the archive does not establish

The database does not by itself establish:

- why a specific historical wheel result is absent;
- the legal basis for a schedule change;
- whether an apparent pattern has predictive value;
- independence between wheels observed on the same date;
- invariance of operational procedures across 155 years;
- a profitable betting strategy.

Those questions require either external primary sources or a separately
declared statistical design.

## Reproducibility boundary

The complete annual archive from 1871 through 2025 and the six consolidated
SQLite databases are tracked in the repository.

The mutable current-year database remains local:

```text
data/lotto-current.sqlite3
```

Transient reports, intermediate downloads and publication checks belong under
`_work/` and are not part of the durable historical dataset.
