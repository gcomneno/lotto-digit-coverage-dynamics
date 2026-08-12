# GUI usage

Related issue: #17.

The graphical interface is an optional local/offline adapter over the same Python application core used by the CLI.

## Prerequisites

- Python 3.12;
- Node.js 22 (or another version accepted by `gui/package.json`);
- the existing local SQLite archives used by the selected report;
- Linux desktop libraries required by pywebview's selected backend.

## Build the frontend

```bash
cd gui
npm install
npm run validate
cd ..
```

GIADA UI is installed from the exact reviewed Git commit recorded in `gui/package.json`. Registry publication is not required.

## Install the optional desktop host

Using a virtual environment is recommended:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-gui.txt
```

## Launch

```bash
./lotto.py gui
```

The GUI loads the compiled `gui/dist/` assets locally and communicates with Python through pywebview's in-process JavaScript API bridge. It does not start an application HTTP API and does not execute or parse CLI output.

## Screens

### Dashboard

Shows the current structured report:

- per-wheel coverage state;
- Markov ranking;
- coverage-hit ranking;
- descriptive cross-wheel consensus;
- active anomalies;
- validation against a later draw only when that draw is already present in the database.

The validation section is explicitly outside the state used for the calculation.

### Occorrenze

Explores grouped same-wheel occurrences:

- group size;
- optional historical cutoff;
- one readable wheel at a time;
- five positional reference colors;
- aligned occurrence totals;
- full group history for the selected wheel.

The wheel selector is presentation-only. Grouping and counts come from the shared application service.

### Ricerca

Historical reports are calculated only when requested. The first GUI set includes:

- coverage-cycle completion;
- Markov calibration;
- Markov residual duration;
- twin-number 11–88 exploratory screen.

The twin report requires `data/lotto-1871-2025.sqlite3`. If a required local archive is absent, the GUI reports the missing resource instead of substituting another dataset.

## Scientific boundary

The GUI is a research interface, not a betting interface.

- Consensus generates no Lotto numbers.
- Historical frequencies do not alter the exact future probability merely because they were observed historically.
- Coverage-hit success concerns missing decimal digits on the same wheel, not a winning Lotto combination.
- Twin-number results remain exploratory unless independently validated under a chronological out-of-sample or forward protocol.
- No staking, payout or automatic betting-slip workflow is provided.
