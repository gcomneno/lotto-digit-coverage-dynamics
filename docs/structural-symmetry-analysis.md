# Structural symmetry analysis

**English** | [Italiano](it/structural-symmetry-analysis.md)


## Purpose

This document identifies the exact symmetry classes of the decimal digit-coverage process and quantifies the information lost when a state is represented only by its number of missing digits.

The analysis is mathematical and descriptive. It is not a prediction or wagering rule.

## Allowed-number counting theorem

Let `A` be a set of forbidden decimal digits and let:

\[
c = 10 - |A|.
\]

Begin with the `c²` ordered pairs made from allowed digits. Two corrections are needed:

1. remove `00` when zero is allowed, because the Lotto range starts at `01`;
2. when nine is allowed as the tens digit, remove every allowed `91–99`; `90` remains valid.

Therefore:

\[
N(A)=c^2-\mathbf 1_{0\notin A}-\mathbf 1_{9\notin A}\left(c-\mathbf 1_{0\notin A}\right).
\]

This formula was checked against direct enumeration of `01–90` for all 1,024 possible forbidden-digit sets.

## Exact symmetry classes

The transition kernel uses allowed-number counts for subsets of the current missing state. The counting theorem implies three families:

- `no-nine`: if 9 is not missing, all missing digits among 0–8 are exchangeable;
- `nine-no-zero`: if 9 is missing but 0 is not, digits 1–8 are exchangeable;
- `zero-nine`: if both 0 and 9 are missing, digits 1–8 are exchangeable.

Their class counts are `9 + 9 + 9 = 27`. Their state multiplicities sum to 1,023.

Kernel equivariance was verified over all 1,024 states and all 58,848 stored transition entries. The maximum discrepancy after canonical relabelling was exactly zero.

## Class atlas

| Class | Family | Missing | States | Canonical | P(complete in 1) | Expected draws | Q95 |
|:---|:---|---:|---:|:---|---:|---:|---:|
| `no-nine:1` | senza 9 | 1 | 9 | `{0}` | 68.164330% | 1.467042957 | 3 |
| `nine-no-zero:0` | con 9, senza 0 | 1 | 1 | `{9}` | 45.300532% | 2.207479618 | 5 |
| `no-nine:2` | senza 9 | 2 | 36 | `{0,1}` | 45.020081% | 1.838898569 | 4 |
| `nine-no-zero:1` | con 9, senza 0 | 2 | 8 | `{1,9}` | 29.457954% | 2.484144275 | 6 |
| `zero-nine:0` | con 0 e 9 | 2 | 1 | `{0,9}` | 30.813300% | 2.464624069 | 6 |
| `no-nine:3` | senza 9 | 3 | 84 | `{0,1,2}` | 28.631685% | 2.135304553 | 4 |
| `nine-no-zero:2` | con 9, senza 0 | 3 | 28 | `{1,2,9}` | 18.410705% | 2.706162000 | 6 |
| `zero-nine:1` | con 0 e 9 | 3 | 8 | `{0,1,9}` | 19.323314% | 2.691457610 | 6 |
| `no-nine:4` | senza 9 | 4 | 126 | `{0,1,2,3}` | 17.387825% | 2.372745568 | 4 |
| `nine-no-zero:3` | con 9, senza 0 | 4 | 56 | `{1,2,3,9}` | 10.961869% | 2.885829028 | 6 |
| `zero-nine:2` | con 0 e 9 | 4 | 28 | `{0,1,2,9}` | 11.550877% | 2.874729829 | 6 |
| `no-nine:5` | senza 9 | 5 | 126 | `{0,1,2,3,4}` | 9.966159% | 2.564806107 | 5 |
| `nine-no-zero:4` | con 9, senza 0 | 5 | 70 | `{1,2,3,4,9}` | 6.142068% | 3.033156586 | 6 |
| `zero-nine:3` | con 0 e 9 | 5 | 56 | `{0,1,2,3,9}` | 6.502436% | 3.024694260 | 6 |
| `no-nine:6` | senza 9 | 6 | 84 | `{0,1,2,3,4,5}` | 5.299843% | 2.722505374 | 5 |
| `nine-no-zero:5` | con 9, senza 0 | 6 | 56 | `{1,2,3,4,5,9}` | 3.181022% | 3.156155452 | 6 |
| `zero-nine:4` | con 0 e 9 | 6 | 70 | `{0,1,2,3,4,9}` | 3.386637% | 3.149572924 | 6 |
| `no-nine:7` | senza 9 | 7 | 36 | `{0,1,2,3,4,5,6}` | 2.545844% | 2.854614270 | 5 |
| `nine-no-zero:6` | con 9, senza 0 | 7 | 28 | `{1,2,3,4,5,6,9}` | 1.480776% | 3.261103775 | 6 |
| `zero-nine:5` | con 0 e 9 | 7 | 56 | `{0,1,2,3,4,5,9}` | 1.587398% | 3.255825739 | 6 |
| `no-nine:8` | senza 9 | 8 | 9 | `{0,1,2,3,4,5,6,7}` | 1.055035% | 2.967954635 | 5 |
| `nine-no-zero:7` | con 9, senza 0 | 8 | 8 | `{1,2,3,4,5,6,7,9}` | 0.590590% | 3.352798273 | 6 |
| `zero-nine:6` | con 0 e 9 | 8 | 28 | `{0,1,2,3,4,5,6,9}` | 0.638645% | 3.348403317 | 6 |
| `no-nine:9` | senza 9 | 9 | 1 | `{0,1,2,3,4,5,6,7,8}` | 0.344033% | 3.067680880 | 5 |
| `nine-no-zero:8` | con 9, senza 0 | 9 | 1 | `{1,2,3,4,5,6,7,8,9}` | 0.183484% | 3.434788969 | 6 |
| `zero-nine:7` | con 0 e 9 | 9 | 8 | `{0,1,2,3,4,5,6,7,9}` | 0.200686% | 3.430983287 | 6 |
| `zero-nine:8` | con 0 e 9 | 10 | 1 | `{0,1,2,3,4,5,6,7,8,9}` | 0.038226% | 3.506190281 | 6 |

## Information loss from cardinality only

A count-only model replaces all exact states with the same cardinality by one mean, giving each exact state equal weight. Because the rows represent symmetry classes, their metrics are weighted by `state_multiplicity`.

This is a structural average over the state space, not an average weighted by historical state frequencies.

| Missing | States | Classes | Mean expected | Expected range | Expected RMSE | P1 range |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10 | 2 | 1.541086623 | 0.740436661 | 0.222130998 | 22.863798% |
| 2 | 45 | 3 | 1.967513928 | 0.645245706 | 0.257245347 | 15.562127% |
| 3 | 120 | 3 | 2.305581494 | 0.570857447 | 0.260123875 | 10.220980% |
| 4 | 210 | 3 | 2.576499059 | 0.513083460 | 0.249567983 | 6.425957% |
| 5 | 252 | 3 | 2.797100830 | 0.468350478 | 0.232313751 | 3.824091% |
| 6 | 210 | 3 | 2.980501245 | 0.433650078 | 0.210667982 | 2.118820% |
| 7 | 120 | 3 | 3.136693840 | 0.406489505 | 0.184676159 | 1.065069% |
| 8 | 45 | 3 | 3.273094906 | 0.384843638 | 0.152578888 | 0.464445% |
| 9 | 10 | 3 | 3.395033615 | 0.367108088 | 0.109123477 | 0.160549% |
| 10 | 1 | 1 | 3.506190281 | 0.000000000 | 0.000000000 | 0.000000% |

## Main structural findings

States with the same number of missing digits are not generally equivalent.

The largest expected-time range occurs at cardinality 1: 0.740436661 draws.

The largest one-draw completion-probability range occurs at cardinality 1: 22.863798%.

Representative equality and inequality:

```text
E[{0,1}] = E[{2,3}]
E[{1,9}] = E[{8,9}]
E[{0,9}] ≠ E[{1,9}]
```

The first two equalities follow from exact symmetry. The final inequality is caused by the special boundary interaction between `0`, `9`, `01` and `90` in the range `01–90`.

Cardinality 10 is the only non-empty cardinality containing a single exact state. For cardinalities 1–9, count-only summaries discard measurable state-identity information.

## Reproduction

```bash
python3 generate_structural_analysis.py
```

Generated outputs:

- `generated/coverage-symmetry-classes.csv`;
- `generated/coverage-cardinality-loss.csv`;
- `generated/coverage-structural-analysis.json`;
- `docs/structural-symmetry-analysis.md`.

## Scope

The symmetry theorem concerns the exact finite-state model over unordered five-number draws from `01–90`.

It does not assert independence between historical wheels and does not create a predictive advantage.
