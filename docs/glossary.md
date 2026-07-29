# Glossary

Glossary
Absorbing state

A state that cannot be left within the current process.

For a coverage cycle, {} is absorbing because no digits remain missing.

Brier score

Mean squared error between a predicted probability and a binary outcome.

For outcome y and probability p:

(y - p)^2

Lower values are better, but scores should be interpreted relative to event
frequency and comparable evaluations.

Calibration

Agreement between predicted probabilities and observed frequencies.

A calibrated group of events predicted at approximately 60% should occur
approximately 60% of the time over a sufficiently large sample.

Completion

The event that all digits missing before a draw appear in that draw, causing
the coverage state to reach {}.

Coverage

The set of decimal digits already observed during the current cycle.

Cycle

A sequence of draws beginning with no covered digits and ending when all digits
0–9 have appeared.

Cycle age

Number of draws already processed in the current cycle.

Cycle age alone is not the Markov state.

Expected residual duration

Mean number of additional draws required for the cycle to reach completion from
a given missing state.

It is an expectation over repeated realizations, not a deterministic deadline.

Holdout

Data deliberately excluded while the model state and prediction are
constructed, then used once for evaluation.

Leakage

Use of information from the target or future observations while constructing a
forecast that is supposed to precede them.

Log loss

A proper scoring rule that strongly penalizes confident incorrect
probabilities.

Markov chain

A stochastic process whose next-state distribution depends only on the current
state.

Here the current state is the set of digits still missing.

Missing state

The set of digits not yet observed in the current cycle.

Examples:

{9}
{3,9}
{0,1,2,3,4,5,6,7,8,9}
Prequential validation

Sequential prediction and evaluation.

Each forecast is produced before its outcome, then scored when the outcome
becomes available.

Residual duration

Actual number of future draws needed to complete a cycle from an observed
state.

Right censoring

A state whose eventual completion is not visible because the archive ends
first.

Walk-forward replay

Historical reconstruction in which each target is predicted using only earlier
data, followed by sequential advancement through the archive.
