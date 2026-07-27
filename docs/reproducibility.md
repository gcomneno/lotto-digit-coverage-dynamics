
Reproducibility
Environment

The project uses the Python standard library.

Core components include:

sqlite3;
unittest;
dataclasses;
functools;
itertools;
math;
json;
hashlib.

No external statistical package is required for the Markov engine.

Test suite

Run:

python3 -m unittest discover -v

At the historical replay checkpoint, the suite contains 100 tests.

Datasets

Committed databases:

data/lotto-2025.sqlite3
data/lotto-2026.sqlite3

The databases should be treated as source datasets.

Temporary truncated copies belong under _work/.

Current-state analysis
python3 analyze_current_coverage.py \
    --database data/lotto-2026.sqlite3
Completion-state analysis
python3 analyze_coverage_completion.py \
    --database data/lotto-2025.sqlite3
Markov calibration
python3 analyze_coverage_markov_validation.py \
    --database data/lotto-2025.sqlite3
Residual expectation validation
python3 analyze_coverage_markov_residuals.py \
    --database data/lotto-2025.sqlite3
Digit-return analysis
python3 analyze_digit_return_times.py \
    --database data/lotto-2025.sqlite3
Walk-forward replay
python3 analyze_prequential_replay.py \
    --database data/lotto-2025.sqlite3 \
    --start-target 101 \
    --end-target 208 \
    --output _work/prequential-replay-2025-from-0101.json
Live forecast
python3 create_prequential_forecast.py \
    --database data/lotto-2026.sqlite3
Integrity checks

Before committing research changes:

git diff --check
python3 -m unittest discover -v
git status --short

Forecast integrity can be checked with:

sha256sum prequential/forecasts/draw-0120.json
Generated reports

Reports under _work/ are intentionally ignored because they can be reproduced
from committed code and data.

A committed forecast is different: it is evidence that a probability statement
was frozen before a future draw, so it belongs under prequential/forecasts/.
