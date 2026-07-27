
Limitations
No number prediction

The model predicts neither individual numbers nor winning combinations.

It estimates the probability that a set of missing decimal digits will all
appear within a given number of future draws.

No gambling advantage

Correct probability estimation does not create an advantage over the lottery.

The model describes a derived property of random draws.

It does not change:

prize probabilities;
expected monetary return;
independence of future number combinations;
house advantage.
Ideal random-draw assumption

The exact transition model assumes that each five-number combination from
1–90 is sampled uniformly without replacement within a wheel draw.

The historical validation checks whether real archives behave consistently with
that model at the digit-coverage level.

Dependence between observations

Successive states from the same cycle overlap and are statistically dependent.

Wheel states from the same contest may also share external timing, although
their draws are analyzed separately.

Naive significance tests that assume every state is independent would
overstate the effective sample size.

Archive censoring

The beginning of an archive can contain a partial cycle that started before the
available data.

The end can contain a cycle whose future completion is unknown.

The implementation handles these conditions explicitly, but censoring always
reduces available observations.

Small exact-state samples

Some missing sets occur rarely.

Large deviations for states with ten or twenty observations are expected and
must not be interpreted as stable anomalies.

Wheel-specific deviations

Historical wheel-level replay results differ.

The current model does not apply wheel-specific corrections because:

each wheel sample is limited;
deviations are not yet shown to persist;
fitting separate adjustments would risk overfitting.
Historical replay is not live prediction

The walk-forward replay prevents future data from entering each forecast.

However, it was executed after all historical events had already occurred.

Only committed live forecasts provide external chronological evidence that the
forecast existed before the target event.

Model versioning

Future modifications must not overwrite results from
digit-coverage-markov-v1.

A changed mathematical model should receive:

a new model identifier;
separate validation results;
separate prequential forecasts;
explicit comparison with the frozen original.
