#!/usr/bin/env bash

ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")"
    pwd
)"

PYTHON_SCRIPT="$ROOT/view_lotto_database.py"

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRORE: comando python3 non disponibile." >&2
    exit 1
fi

if ! command -v less >/dev/null 2>&1; then
    echo "ERRORE: comando less non disponibile." >&2
    exit 1
fi

OUTPUT="$(
    mktemp \
        "${TMPDIR:-/tmp}/view-lotto-database.XXXXXX"
)"

cleanup() {
    rm -f "$OUTPUT"
}

trap cleanup EXIT HUP INT TERM

python3 "$PYTHON_SCRIPT" "$@" > "$OUTPUT"
PYTHON_EXIT="$?"

if test "$PYTHON_EXIT" -ne 0; then
    exit "$PYTHON_EXIT"
fi

less -RS "$OUTPUT"
