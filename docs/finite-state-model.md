# Finite-state model of decimal digit coverage

## Purpose

This document defines the exact finite-state stochastic model used to study
decimal digit coverage in one Italian Lotto wheel.

The model answers mathematical questions such as:

- which digits are still missing from the current coverage cycle;
- how the missing-digit state can change after one draw;
- the probability of completing coverage in one or more draws;
- the expected number of draws remaining before completion;
- how the theoretical process compares with historical observations.

It is not a draw-selection or betting model.

## 1. Decimal universe

Let

\[
D = \{0,1,2,\ldots,9\}
\]

be the set of decimal digits.

One wheel draw contains five distinct numbers selected from

\[
N = \{1,2,\ldots,90\}.
\]

Every number is represented with exactly two decimal characters.

Examples:

\[
1 \mapsto 01,
\qquad
6 \mapsto 06,
\qquad
90 \mapsto 90.
\]

Therefore leading zeroes contribute to digit coverage.

Define the digit-set function

\[
\delta : N \rightarrow \mathcal{P}(D)
\]

so that \(\delta(n)\) is the set of digits appearing in the two-character
representation of \(n\).

Examples:

\[
\delta(1) = \{0,1\},
\]

\[
\delta(11) = \{1\},
\]

\[
\delta(90) = \{0,9\}.
\]

Repeated occurrences of the same digit do not change the set.

## 2. Draw sample space

A draw is an unordered set of five distinct numbers:

\[
\omega \in \Omega
=
\left\{
A \subseteq N : |A| = 5
\right\}.
\]

The number of possible draws is

\[
|\Omega|
=
\binom{90}{5}
=
43\,949\,268.
\]

The model assumes that every element of \(\Omega\) has equal probability:

\[
P(\omega)
=
\frac{1}{\binom{90}{5}}.
\]

For a draw \(\omega\), define its observed digit set as

\[
G(\omega)
=
\bigcup_{n \in \omega} \delta(n).
\]

Only the union of observed digits is relevant to the coverage-state
transition.

## 3. Coverage cycles

A coverage cycle begins with none of the ten digits observed.

During the cycle, every new draw adds its observed digits to the set already
covered.

The cycle completes when all digits in \(D\) have appeared at least once.

For historical reconstruction, a new natural cycle begins immediately after
the draw that completes the previous cycle.

An archive may begin in the middle of an already active cycle. Historical
state reconstruction is therefore considered synchronized only after the
first complete cycle has been observed within the available archive.

## 4. State representation

The model represents a state by the set of digits still missing from the
current cycle.

Let

\[
S \subseteq D
\]

be the current missing-digit state.

Examples:

- \(S = D\): no digit has yet been covered in the cycle;
- \(S = \{2,5,9\}\): digits 2, 5 and 9 are still missing;
- \(S = \{9\}\): only digit 9 is still missing;
- \(S = \varnothing\): coverage is complete.

The state space is the power set

\[
\mathcal{S}
=
\mathcal{P}(D).
\]

Its cardinality is

\[
|\mathcal{S}|
=
2^{10}
=
1024.
\]

There are 1,023 non-empty transient states and one empty absorbing state in
the absorption model.

The identities of the missing digits are part of the state. Two states with
the same cardinality need not have the same transition probabilities.

For example,

\[
\{3\}
\quad\text{and}\quad
\{9\}
\]

both contain one missing digit, but their completion probabilities differ
because decimal digits do not occur symmetrically in the numbers `01–90`.

## 5. Deterministic state update

Given a current state \(S\) and a draw \(\omega\), the next state is

\[
F(S,\omega)
=
S \setminus G(\omega).
\]

A transition can only remove missing digits.

Therefore, for every valid transition from \(S\) to \(T\),

\[
T \subseteq S.
\]

A draw can:

- leave the state unchanged;
- remove one missing digit;
- remove several missing digits;
- remove every missing digit and complete the cycle.

It can never add a digit to the missing set.

## 6. Exact transition kernel

The one-step Markov transition probability is

\[
K(S,T)
=
P(F(S,\omega)=T).
\]

Because all five-number draws are equiprobable,

\[
K(S,T)
=
\frac{
\left|
\left\{
\omega \in \Omega :
S \setminus G(\omega)=T
\right\}
\right|
}{
\binom{90}{5}
}.
\]

If

\[
T \nsubseteq S,
\]

then

\[
K(S,T)=0.
\]

For every state \(S\),

\[
\sum_{T \subseteq S} K(S,T)=1.
\]

The transition law depends only on the current exact missing-digit set.

Under the model, it does not additionally depend on:

- the age of the current cycle;
- the order in which already covered digits appeared;
- previous residuals;
- previous wins or failures;
- the wheel name;
- calendar time.

This is the Markov property of the model.

## 7. Inclusion–exclusion construction

The primary implementation computes transition probabilities through
inclusion–exclusion.

For a candidate transition \(S \rightarrow T\), define

\[
R = S \setminus T.
\]

The digits in \(T\) must be absent from the next draw, while every digit in
\(R\) must appear at least once.

For any set of forbidden digits \(F \subseteq D\), define

\[
a(F)
=
\left|
\left\{
n \in N :
\delta(n) \cap F = \varnothing
\right\}
\right|.
\]

This is the number of Lotto numbers containing none of the forbidden digits.

The probability that all five drawn numbers avoid \(F\) is

\[
A(F)
=
\frac{
\binom{a(F)}{5}
}{
\binom{90}{5}
},
\]

with value zero when \(a(F)<5\).

Inclusion–exclusion then gives

\[
K(S,T)
=
\sum_{U \subseteq R}
(-1)^{|U|}
A(T \cup U).
\]

This formula enforces:

- absence of every digit still missing in \(T\);
- presence of every digit removed from the state.

The one-draw completion probability from \(S\) is the special case

\[
K(S,\varnothing).
\]

## 8. Independent integer-count construction

A second implementation verifies the kernel without using
inclusion–exclusion.

Each digit set is represented by a ten-bit mask.

For every number \(n \in N\), let

\[
m(n)
\]

be the bit mask corresponding to \(\delta(n)\).

A dynamic programme processes the numbers `1–90` one at a time.

Let

\[
C_{k,m}
\]

be the number of ways to choose \(k\) processed numbers whose combined digit
mask is \(m\).

The initial condition is

\[
C_{0,0}=1.
\]

When processing a number with mask \(b\), every existing count contributes
to two cases:

1. the number is not selected;
2. the number is selected, producing union mask \(m \lor b\).

Only layers up to \(k=5\) are retained.

After all 90 numbers have been processed,

\[
C_{5,m}
\]

is the exact number of five-number draws producing observed digit mask \(m\).

The counts satisfy

\[
\sum_m C_{5,m}
=
\binom{90}{5}
=
43\,949\,268.
\]

For a current missing-state mask \(s\), the next-state mask is

\[
t
=
s \land \neg m.
\]

Therefore the exact integer transition count is obtained by aggregating all
draw-mask counts that produce the same \(t\).

This method:

- uses integer arithmetic for combination counts;
- does not use inclusion–exclusion;
- does not call the primary transition implementation;
- does not enumerate all 43,949,268 draws individually.

## 9. Exhaustive kernel verification

The two independent constructions were compared over the complete state
space.

Verification results:

- possible five-number draws: 43,949,268;
- observed digit-union mask classes: 968;
- current states verified: 1,024;
- transition entries compared: 58,848;
- comparison tolerance: \(10^{-12}\);
- maximum absolute probability difference:
  \(2.289 \times 10^{-15}\);
- maximum normalization error:
  \(5.995 \times 10^{-15}\);
- discrepancies above tolerance: 0.

The remaining numerical differences are consistent with floating-point
rounding in the inclusion–exclusion implementation.

The transition kernel is therefore computationally verified across the
entire state space by two conceptually independent methods.

## 10. Absorbing-chain interpretation

For completion analysis, the empty state is treated as absorbing:

\[
K(\varnothing,\varnothing)=1.
\]

This convention allows standard absorption quantities to be calculated
without mixing completion with the beginning of a new cycle.

It is important to distinguish two processes.

### Absorption model

Used for mathematical quantities such as:

- probability of completing within \(h\) draws;
- expected remaining draws;
- absorption-time distributions.

In this model, once \(\varnothing\) is reached, the process remains there.

### Natural historical process

Used to reconstruct repeated coverage cycles in actual archives.

After a draw completes the cycle, the tracking state is reset for the next
cycle to

\[
D.
\]

The absorbing state is therefore a mathematical boundary for one cycle, not
a claim that historical coverage permanently stops.

## 11. Completion probability within a horizon

Let

\[
H_S
\]

be the number of additional draws needed to reach the empty state when the
current state is \(S\).

Define

\[
q_h(S)
=
P(H_S \le h).
\]

Boundary conditions are

\[
q_h(\varnothing)=1
\]

for every \(h \ge 0\), and

\[
q_0(S)=0
\]

for every non-empty \(S\).

For \(h \ge 1\),

\[
q_h(S)
=
\sum_{T \subseteq S}
K(S,T)q_{h-1}(T).
\]

Consequently,

\[
q_1(S)
=
K(S,\varnothing).
\]

For every state \(S\), the sequence

\[
q_1(S),q_2(S),q_3(S),\ldots
\]

is non-decreasing.

For every non-empty state in this model,

\[
\lim_{h\to\infty} q_h(S)=1.
\]

## 12. Expected remaining draws

Define

\[
E(S)
=
\mathbb{E}[H_S].
\]

For the absorbing state,

\[
E(\varnothing)=0.
\]

For a non-empty state,

\[
E(S)
=
1+
\sum_{T \subseteq S}
K(S,T)E(T).
\]

Because the transition distribution may include a self-transition, isolate
the \(T=S\) term:

\[
E(S)
=
\frac{
1+
\sum_{T \subsetneq S}K(S,T)E(T)
}{
1-K(S,S)
}.
\]

This recursive equation is well-defined because every non-empty state has a
positive probability of eventually losing at least one missing digit.

## 13. Single-digit states

For a state containing one missing digit,

\[
S=\{d\},
\]

each draw either:

- contains digit \(d\), completing the cycle;
- avoids digit \(d\), leaving the state unchanged.

The absorption time is therefore geometric with parameter

\[
p_d
=
K(\{d\},\varnothing).
\]

Thus

\[
P(H_{\{d\}}=h)
=
(1-p_d)^{h-1}p_d
\]

for \(h=1,2,\ldots\), and

\[
E(\{d\})
=
\frac{1}{p_d}.
\]

This provides a closed-form reference check for the general recursive
implementation.

## 14. Partial-order structure

The state graph follows set inclusion.

Every transition satisfies

\[
T \subseteq S.
\]

If states are ordered by decreasing cardinality, transitions can only remain
within the same state or move towards states with fewer missing digits.

The transition matrix therefore admits an ordering with a triangular
structure apart from self-transitions.

This structure supports recursive computation of absorption metrics without
requiring a generic dense matrix inversion.

## 15. What the model establishes

The model establishes exact probabilities conditional on the current
missing-digit state and its stated assumptions.

It supports claims such as:

- the precise probability of a given state transition;
- the precise probability of completing within a fixed horizon;
- the expected remaining time to completion;
- differences between states containing different digit identities;
- theoretical benchmarks for historical calibration.

## 16. What the model does not establish

The model does not establish:

- that a particular future draw will complete a cycle;
- that one wheel is predictively favourable;
- that recent deviations alter the next transition probability;
- that cycle age creates additional predictive information;
- that a historical residual pattern is exploitable;
- that any wagering strategy has positive expected value.

Historical results may be compared with the model, but unexplained sample
variation must not automatically be converted into a predictive rule.

## 17. Implementation map

Primary inclusion–exclusion kernel:

```text
strategies/coverage_markov.py
```

Independent digit-mask enumerator:

```text
strategies/coverage_transition_enumerator.py
```

Exhaustive verification command:

```text
verify_transition_kernel.py
```

Kernel tests:

```text
tests/test_coverage_markov.py
tests/test_coverage_transition_enumerator.py
```

Mathematical roadmap:

```text
docs/mathematical-model-roadmap.md
```

Predictive-research closure:

```text
docs/predictive-research-closure.md
```

## 18. Current verification status

As of commit `be3f81e`:

- the complete 1,024-state transition kernel has been independently verified;
- all 153 automated tests pass;
- no transition discrepancy exceeds \(10^{-12}\);
- predictive research is closed;
- the next mathematical milestone is the complete absorption-state atlas.

The kernel should be treated as verified subject to the assumptions and
limitations documented above.
