
Live prequential protocol
Objective

Historical replay can prevent computational leakage, but it cannot prove that a
forecast existed before the event.

The live protocol creates that proof.

Forecast lifecycle

A forecast passes through the following conceptual states:

pending -> resolved

The pending forecast file itself remains unchanged.

Resolution data must be stored separately.

Forecast generation

Before the target contest:

update the source database only through the latest known contest;
run the full test suite;
generate the forecast;
verify the generated target number;
commit and push the forecast;
do not modify it after publication.

Command:

python3 create_prequential_forecast.py \
    --database data/lotto-2026.sqlite3

Default path:

prequential/forecasts/draw-NNNN.json
Immutability

The forecast writer uses exclusive file creation.

If the target file already exists, generation fails rather than overwriting the
previous content.

Each forecast records:

format version;
model identifier;
generation timestamp in UTC;
repository commit;
source database path;
source database SHA-256;
latest source contest;
target contest;
state of every wheel;
completion probabilities;
expected residual duration.
Current live forecast

The first true live forecast is:

prequential/forecasts/draw-0120.json

It was generated from data through contest 119.

Its creation was committed in:

00fc434b2fdf5aaeb10e0e9697eb67bf6e801901

The forecast file SHA-256 is:

6386764076d12e5469d31f8c5b3fa2c2493c1be19cae825f174273a936ff3a63
Outcome recording

When the target contest becomes available, the future outcome recorder should:

verify the pending forecast hash;
verify that the database contains the target contest;
read the target draw for every wheel;
compare target digits with frozen missing digits;
calculate wheel outcomes;
calculate expected and observed closures;
calculate Brier score and log loss;
write a separate immutable outcome document;
update a cumulative summary generated from forecast/outcome pairs.

The forecast must not be edited to change status.

Interpretation

A single target contest provides only eleven wheel observations.

The cumulative sequence is the primary object of interest.

No parameter should be changed in response to a small number of favorable or
unfavorable outcomes unless a separate model version and explicit research
protocol are created.
