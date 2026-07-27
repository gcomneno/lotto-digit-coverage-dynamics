# Coverage state atlas summary

## Status

Generated from the exact 1,024-state finite-state model.

The atlas is descriptive mathematical material, not a betting recommendation.

## Scope

- total states: 1,024;
- absorbing empty state: 1;
- non-empty states in the atlas: 1,023;
- difficulty metric: expected remaining draws;
- rank 1: smallest expected remaining time;
- deterministic tie-breakers: missing-digit count and lexicographic state.

## Summary by missing-digit count

| Missing digits | States | Minimum mean | Average mean | Maximum mean |
|---:|---:|---:|---:|---:|
| 1 | 10 | 1.467043 | 1.541087 | 2.207480 |
| 2 | 45 | 1.838899 | 1.967514 | 2.484144 |
| 3 | 120 | 2.135305 | 2.305581 | 2.706162 |
| 4 | 210 | 2.372746 | 2.576499 | 2.885829 |
| 5 | 252 | 2.564806 | 2.797101 | 3.033157 |
| 6 | 210 | 2.722505 | 2.980501 | 3.156155 |
| 7 | 120 | 2.854614 | 3.136694 | 3.261104 |
| 8 | 45 | 2.967955 | 3.273095 | 3.352798 |
| 9 | 10 | 3.067681 | 3.395034 | 3.434789 |
| 10 | 1 | 3.506190 | 3.506190 | 3.506190 |

## Ten easiest states

| Rank | State | Missing | Mean | Std. dev. | P(within 1) | Q50 | Q95 | Q99 |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `{0}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 2 | `{1}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 3 | `{2}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 4 | `{3}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 5 | `{4}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 6 | `{5}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 7 | `{6}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 8 | `{7}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 9 | `{8}` | 1 | 1.467043 | 0.827751 | 68.16% | 1 | 3 | 5 |
| 10 | `{0,1}` | 2 | 1.838899 | 0.994758 | 45.02% | 2 | 4 | 5 |

## Ten hardest states

| Rank | State | Missing | Mean | Std. dev. | P(within 1) | Q50 | Q95 | Q99 |
|---:|:---|---:|---:|---:|---:|---:|---:|---:|
| 1023 | `{0,1,2,3,4,5,6,7,8,9}` | 10 | 3.506190 | 1.387379 | 0.04% | 3 | 6 | 8 |
| 1022 | `{1,2,3,4,5,6,7,8,9}` | 9 | 3.434789 | 1.397678 | 0.18% | 3 | 6 | 8 |
| 1021 | `{0,2,3,4,5,6,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1020 | `{0,1,3,4,5,6,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1019 | `{0,1,2,4,5,6,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1018 | `{0,1,2,3,5,6,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1017 | `{0,1,2,3,4,6,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1016 | `{0,1,2,3,4,5,7,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1015 | `{0,1,2,3,4,5,6,8,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |
| 1014 | `{0,1,2,3,4,5,6,7,9}` | 9 | 3.430983 | 1.399142 | 0.20% | 3 | 6 | 8 |

## Full initial state

For the state with all ten digits still missing:

- expected remaining draws: 3.506190;
- variance: 1.924821;
- standard deviation: 1.387379;
- completion within 3 draws: 60.47%;
- completion within 5 draws: 92.28%;
- median completion horizon: 3;
- 95% completion horizon: 6;
- 99% completion horizon: 8.

## Machine-readable outputs

- `generated/coverage-state-atlas.csv`
- `generated/coverage-state-atlas.json`

## Interpretation

States with the same number of missing digits may have different metrics because digit identities are not symmetric in the range `01–90`.

The ranking describes mathematical absorption difficulty only. It does not identify favourable draws, wheels or wagering opportunities.
