
Prequential registry

This directory stores immutable evidence for live sequential validation.

Forecasts

Pending forecasts are stored under:

prequential/forecasts/

A forecast filename identifies its target contest:

draw-0120.json

Forecast files must never be edited after their first committed publication.

Future outcome structure

Resolved outcomes should be written separately under a future directory such
as:

prequential/outcomes/

A cumulative report should be generated from forecast/outcome pairs rather
than by modifying the original forecasts.

See:

docs/live-prequential-protocol.md

