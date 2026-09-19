# Reproducibility

**English** | [Italiano](it/reproducibility.md)


Run all commands from the repository root.

Transient outputs should be written under `_work/`. Deterministic publication
artifacts are tracked under `generated/`.

## Automated suite

Install the pinned GiadaWare AI dependency, then run the Python suite:

```bash
python3 -m pip install -r requirements-ai.txt
python3 -m unittest discover -v
```

At the 19 September 2026 release-candidate checkpoint, 465 tests run; 2
integration tests are skipped when their external database fixture is not
available.

The GUI has an independent validation gate:

```bash
cd gui
npm ci --no-audit --no-fund
npm run validate
cd ..
```

## Unified dispatcher

List the 20 top-level tools, including discovery of the nested `db ask`
command, and inspect any help page:

```bash
./lotto.py list
./lotto.py help current
```

The dispatcher forwards all remaining arguments unchanged and preserves the
underlying command’s exit status. Direct invocation of every original script
remains supported.

See [Command-line reference](cli-reference.md).

## Independent kernel verification

```bash
python3 verify_transition_kernel.py \
    --output _work/reproduction/transition-kernel.json
```

Expected invariants include:

- `verified: true`;
- `draw_combinations: 43949268`;
- `observed_digit_mask_classes: 968`;
- `states_verified: 1024`;
- maximum absolute error below `1e-12`.

## State atlas

Regenerate into a temporary directory:

```bash
python3 generate_state_atlas.py \
    --csv-output _work/reproduction/coverage-state-atlas.csv \
    --json-output _work/reproduction/coverage-state-atlas.json \
    --summary-output _work/reproduction/state-atlas-summary.md
```

Compare the machine-readable artifacts:

```bash
cmp generated/coverage-state-atlas.csv \
    _work/reproduction/coverage-state-atlas.csv

cmp generated/coverage-state-atlas.json \
    _work/reproduction/coverage-state-atlas.json
```

## Structural analysis

```bash
python3 generate_structural_analysis.py \
    --classes-csv \
    _work/reproduction/coverage-symmetry-classes.csv \
    --cardinality-csv \
    _work/reproduction/coverage-cardinality-loss.csv \
    --json-output \
    _work/reproduction/coverage-structural-analysis.json \
    --summary-output \
    _work/reproduction/structural-symmetry-analysis.md
```

Compare with the tracked outputs:

```bash
cmp generated/coverage-symmetry-classes.csv \
    _work/reproduction/coverage-symmetry-classes.csv

cmp generated/coverage-cardinality-loss.csv \
    _work/reproduction/coverage-cardinality-loss.csv

cmp generated/coverage-structural-analysis.json \
    _work/reproduction/coverage-structural-analysis.json
```

At the July 2026 checkpoint, all five regenerated theoretical artifacts matched
their tracked versions byte for byte.

## Historical cycle distribution

```bash
python3 analyze_historical_cycle_distribution.py \
    --primary-databases \
    data/lotto-2023.sqlite3 \
    data/lotto-2024.sqlite3 \
    data/lotto-2025.sqlite3 \
    data/lotto-current.sqlite3 \
    --text-output \
    _work/reproduction/historical-cycle-distribution.txt \
    --json-output \
    _work/reproduction/historical-cycle-distribution.json
```

Expected archive interval:

```text
2023-01-03 -> 2026-07-28
```

Expected complete-cycle count:

```text
2253
```

The default secondary segment is empty.

## Historical structural classes

```bash
python3 analyze_historical_symmetry_classes.py \
    --database data/lotto-2023.sqlite3 \
    --database data/lotto-2024.sqlite3 \
    --database data/lotto-2025.sqlite3 \
    --database data/lotto-current.sqlite3 \
    --csv-output \
    _work/reproduction/historical-symmetry-classes.csv \
    --json-output \
    _work/reproduction/historical-symmetry-classes.json
```

Expected summary:

```text
27 structural classes
7869 one-step observations
```

## Historical anomalies

```bash
python3 analyze_coverage_anomalies.py \
    --database data/lotto-2023.sqlite3 \
    --database data/lotto-2024.sqlite3 \
    --database data/lotto-2025.sqlite3 \
    --database data/lotto-current.sqlite3 \
    --label historical-2023-2026 \
    --output-prefix \
    _work/reproduction/coverage-anomalies-2023-2026
```

At the current checkpoint, the default `1%` threshold produces:

```text
A1=21
A2=3
A3=12
A4=0
total=36
```

## Current state

```bash
./lotto.py current
./lotto.py current --to 2026-07-25
./lotto.py current --to-num 119
```

The output must state the exact database cutoff. `--to` limits the analysis by
inclusive ISO date; `--to-num` limits it by inclusive draw number. The
equivalent spelling `--to_num` is also accepted, and the date and number
cutoffs cannot be combined.

The final `TUTTE` row uses wheels with positive current-cycle age. Its
most-present set is the union across all active wheels, while its missing set
is the union only across active wheels tied for the maximum one-draw completion
probability. It then reports their intersection and the valid ordered
two-digit encodings of intersecting digits, with repeated digits allowed.
This row is descriptive
and does not define an altered probability model.

Current states and active anomalies are expected to change as new draws are
imported.

## Semantic read-query boundary

The semantic query capability is reproducible deterministically without a real
LLM because CI uses controlled backends.

For a repository-contained database:

```bash
./lotto.py db ask \
  --database data/lotto-2025.sqlite3 \
  "Cos'è uscito su Napoli nell'ultima estrazione?"
```

A real Ollama run is an optional qualification exercise, not part of the
deterministic release proof. A reachable model must not be described as
qualified unless it passes the documented semantic corpus. The currently
recorded reference evaluations for `qwen2.5:1.5b-instruct` and
`qwen3.5:2b-q4_K_M` are **NOT QUALIFIED**.

## Database integrity and update

Inspect importer and updater options:

```bash
python3 import_lotto.py --help
python3 update_lotto_database.py --help
```

Update the current annual archive:

```bash
python3 update_lotto_database.py
```

The updater requires a complete contiguous archive beginning at draw 1, builds a
temporary database, validates it and replaces the destination atomically.

## Git cleanliness

A reproduction run directed entirely to `_work/` must not modify tracked files:

```bash
git status --short
```

`docs/validation-results.md` is intentionally absent. Reproduction evidence is
generated from the live implementation rather than maintained as a manually
synchronized validation document.
