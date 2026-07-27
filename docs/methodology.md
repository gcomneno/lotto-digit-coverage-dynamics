
Methodology
Unit of analysis

Each Lotto wheel is analyzed independently.

A draw is atomic: all five numbers from the same wheel and contest are processed
together.

Digits are accumulated only within the same wheel.

Natural coverage cycles

A natural cycle follows these rules:

begin with no covered digits;
add every digit appearing in each new draw;
close the cycle when all digits 0–9 have appeared;
start a new cycle after that completion.

The state recorded after a completion is therefore the fresh state containing
all ten missing digits.

Left censoring

An archive may begin in the middle of an already active cycle.

The first observed partial cycle is not treated as a complete natural cycle.
It is used only to synchronize the process once the first complete coverage is
observed.

Right censoring

At the end of an archive, the current cycle may still be open.

For probability-within-horizon validation:

a successful completion can be recorded as soon as it occurs;
a failure is recorded only when the full requested horizon is available.

For residual-duration validation:

only states whose subsequent completion is observable are included;
right-censored final states are excluded.
Exact theoretical baseline

No empirical frequency is used to define the Markov transition probabilities.

They are calculated from the exact combinatorics of selecting five distinct
numbers from 1 to 90.

Historical data is used only for validation.

Calibration validation

For every observed state, the model assigns a probability of cycle completion
within a chosen horizon.

Predictions are compared with observed binary outcomes.

Reported measures include:

observed completion rate;
mean predicted probability;
observed-minus-predicted difference;
Brier score;
calibration by probability bands;
exact-state summaries where enough observations exist.

Historical states overlap and states within the same cycle are dependent.
Results are therefore treated as descriptive calibration, not as independent
Bernoulli trials for naive significance testing.

Residual-duration validation

For each state with a known later completion:

predicted value: exact Markov expected remaining draws;
observed value: actual number of draws before cycle completion.

Reported measures include:

mean observed duration;
mean predicted duration;
bias;
mean absolute error;
root mean squared error.

The expected value is not intended to predict the exact duration of an
individual cycle.

Historical walk-forward replay

For target contest T:

use only contests strictly earlier than T;
reconstruct the current state for every wheel;
calculate and freeze the model probabilities;
inspect contest T;
record the completion outcome;
advance to T + 1.

The 2025 replay covers:

100 -> 101
101 -> 102
...
207 -> 208

It contains 108 × 11 = 1,188 wheel-level forecasts.

The replay is leakage-safe but reconstructed after the events. It is therefore
not equivalent to a forecast publicly committed before an unknown draw.

Live prequential validation

The live protocol adds a time-ordering proof:

generate an immutable forecast file;
record source database hash and model commit;
commit and push the forecast before the target draw;
never modify the forecast;
record the outcome in a separate file;
update cumulative scoring.

The first live target is contest 120.
