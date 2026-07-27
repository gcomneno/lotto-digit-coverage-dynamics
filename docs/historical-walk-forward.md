
Historical walk-forward replay
Purpose

The historical replay asks:

What would the model have reported before each historical draw if only the
earlier draws had been available?

This is stricter than calculating probabilities after loading an entire
archive.

Replay interval

The 2025 replay begins with the archive stopped at contest 100.

The first target is contest 101.

The process continues sequentially through contest 208.

state through 100 -> evaluate 101
state through 101 -> evaluate 102
...
state through 207 -> evaluate 208
Anti-leakage condition

Every recorded observation satisfies:

source_latest_draw < target_draw

The generated registry contains:

108 contests
11 wheels per contest
1,188 wheel-level forecasts

The anti-leakage verification confirms:

first path: 100 -> 101
last path:  207 -> 208
Overall results
Measure	Value
Expected closures	336.994
Observed closures	334
Predicted rate	28.37%
Observed rate	28.11%
Difference	-0.25 pp
Brier score	0.1393
Log loss	0.4112
Wheel-level results
Wheel	Expected	Observed	Predicted rate	Observed rate	Delta
Bari	34.10	30	31.57%	27.78%	-3.79 pp
Cagliari	34.08	30	31.55%	27.78%	-3.78 pp
Firenze	29.98	29	27.75%	26.85%	-0.90 pp
Genova	26.00	34	24.08%	31.48%	+7.41 pp
Milano	33.90	29	31.39%	26.85%	-4.54 pp
Napoli	30.02	30	27.79%	27.78%	-0.02 pp
Palermo	29.53	29	27.34%	26.85%	-0.49 pp
Roma	28.98	34	26.84%	31.48%	+4.65 pp
Torino	31.46	30	29.13%	27.78%	-1.35 pp
Venezia	27.72	31	25.67%	28.70%	+3.03 pp
Nazionale	31.22	28	28.91%	25.93%	-2.98 pp

These wheel-level differences are not used to create separate fitted models.

With only 108 targets per wheel, adapting probabilities to these deviations
would risk overfitting.

Reproduction
python3 analyze_prequential_replay.py \
    --database data/lotto-2025.sqlite3 \
    --start-target 101 \
    --end-target 208 \
    --output _work/prequential-replay-2025-from-0101.json

The JSON report contains the full sequence of states, probabilities, target
numbers, outcomes, and cumulative scores.

Because the output is reproducible, it is stored under _work/ rather than
committed.
