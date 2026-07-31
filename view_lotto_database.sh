#!/usr/bin/env bash

DATABASE="data/lotto-2026.sqlite3"
DATABASE_SET=0
DIGITS=()
NUMBERS=()

usage() {
    cat <<'HELP'
Uso:
  ./view_lotto_database.sh [DATABASE]
  ./view_lotto_database.sh [--database PATH] [--digit CIFRE]... [--number NUMERI]...

Visualizza tutte le estrazioni del database in una tabella larga.

Opzioni:
  --database PATH       Database SQLite da visualizzare.
  --digit CIFRE         Evidenzia una o più cifre da 0 a 9.
                        L'opzione può essere ripetuta.
                        Sono accettate anche cifre separate da virgola.
  --number NUMERI       Evidenzia uno o più numeri da 1 a 90.
                        L'opzione può essere ripetuta.
                        Sono accettati anche numeri separati da virgola.
  -h, --help            Mostra questo messaggio.

Esempi:
  ./view_lotto_database.sh
  ./view_lotto_database.sh --digit 7
  ./view_lotto_database.sh --digit 1,7,9
  ./view_lotto_database.sh --number 17
  ./view_lotto_database.sh --number 17 --number 90
  ./view_lotto_database.sh --number 1,17,90
  ./view_lotto_database.sh --digit 7 --number 17,90
  ./view_lotto_database.sh data/lotto-2025.sqlite3 --number 1,90
HELP
}


while test "$#" -gt 0; do
    case "$1" in
        --database)
            if test "$#" -lt 2; then
                echo "ERRORE: --database richiede un percorso." >&2
                exit 2
            fi

            DATABASE="$2"
            DATABASE_SET=1
            shift 2
            ;;

        --digit)
            if test "$#" -lt 2; then
                echo "ERRORE: --digit richiede almeno una cifra." >&2
                exit 2
            fi

            DIGITS+=("$2")
            shift 2
            ;;

        --number)
            if test "$#" -lt 2; then
                echo "ERRORE: --number richiede almeno un numero." >&2
                exit 2
            fi

            NUMBERS+=("$2")
            shift 2
            ;;

        -h|--help)
            usage
            exit 0
            ;;

        -*)
            echo "ERRORE: opzione sconosciuta: $1" >&2
            echo >&2
            usage >&2
            exit 2
            ;;

        *)
            if test "$DATABASE_SET" -eq 1; then
                echo "ERRORE: database specificato più volte." >&2
                exit 2
            fi

            DATABASE="$1"
            DATABASE_SET=1
            shift
            ;;
    esac
done


if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRORE: comando python3 non disponibile." >&2
    exit 1
fi

if ! command -v less >/dev/null 2>&1; then
    echo "ERRORE: comando less non disponibile." >&2
    exit 1
fi

if ! test -f "$DATABASE"; then
    echo "ERRORE: database assente: $DATABASE" >&2
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


python3 - "$DATABASE" --digits "${DIGITS[@]}" --numbers "${NUMBERS[@]}" > "$OUTPUT" <<'PYTHON'
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path


HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"

EXPECTED_WHEELS = (
    "Bari",
    "Cagliari",
    "Firenze",
    "Genova",
    "Milano",
    "Napoli",
    "Palermo",
    "Roma",
    "Torino",
    "Venezia",
    "Nazionale",
)


def parse_digits(values: list[str]) -> tuple[str, ...]:
    digits: set[str] = set()

    for value in values:
        parts = value.split(",")

        for part in parts:
            normalized = part.strip()

            if (
                len(normalized) != 1
                or normalized not in "0123456789"
            ):
                raise ValueError(
                    "--digit accetta soltanto cifre "
                    "singole comprese tra 0 e 9; "
                    f"ricevuto {part!r}."
                )

            digits.add(normalized)

    return tuple(
        sorted(
            digits,
            key=int,
        )
    )


def parse_numbers(values: list[str]) -> tuple[int, ...]:
    numbers: set[int] = set()

    for value in values:
        parts = value.split(",")

        for part in parts:
            normalized = part.strip()

            if (
                not normalized.isascii()
                or not normalized.isdigit()
            ):
                raise ValueError(
                    "--number accetta soltanto numeri "
                    "interi compresi tra 1 e 90; "
                    f"ricevuto {part!r}."
                )

            number = int(normalized)

            if not 1 <= number <= 90:
                raise ValueError(
                    "--number accetta soltanto numeri "
                    "interi compresi tra 1 e 90; "
                    f"ricevuto {part!r}."
                )

            numbers.add(number)

    return tuple(sorted(numbers))


def highlight_digits(
    text: str,
    digits: set[str],
) -> str:
    if not digits:
        return text

    return "".join(
        (
            f"{HIGHLIGHT}{character}{RESET}"
            if character in digits
            else character
        )
        for character in text
    )


NUMBER_PATTERN = re.compile(r"(?<!\d)\d{2}(?!\d)")


def highlight_cell(
    text: str,
    digits: set[str],
    numbers: set[int],
) -> str:
    if not digits and not numbers:
        return text

    rendered: list[str] = []
    cursor = 0

    for match in NUMBER_PATTERN.finditer(text):
        rendered.append(
            text[cursor:match.start()]
        )

        token = match.group()

        if int(token) in numbers:
            rendered.append(
                f"{HIGHLIGHT}{token}{RESET}"
            )
        else:
            rendered.append(
                highlight_digits(
                    token,
                    digits,
                )
            )

        cursor = match.end()

    rendered.append(text[cursor:])

    return "".join(rendered)


database = Path(sys.argv[1])
numbers_marker = sys.argv.index(
    "--numbers",
    3,
)

try:
    selected_digits = parse_digits(
        sys.argv[3:numbers_marker]
    )
    selected_numbers = parse_numbers(
        sys.argv[numbers_marker + 1:]
    )
except ValueError as error:
    print(
        f"ERRORE: {error}",
        file=sys.stderr,
    )
    raise SystemExit(2)

try:
    with sqlite3.connect(database) as connection:
        integrity = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

        if integrity != "ok":
            raise ValueError(
                "Integrità SQLite non valida: "
                f"{integrity}."
            )

        count, first_draw, last_draw = connection.execute(
            """
            SELECT
                COUNT(*),
                MIN(draw_number),
                MAX(draw_number)
            FROM draws
            """
        ).fetchone()

        rows = connection.execute(
            """
            SELECT
                draw_number,
                draw_date,
                wheel,
                wheel_order,
                GROUP_CONCAT(value_padded, ' ') AS numbers
            FROM (
                SELECT
                    draw_number,
                    draw_date,
                    wheel,
                    wheel_order,
                    position,
                    value_padded
                FROM v_draw_numbers
                ORDER BY
                    draw_number,
                    wheel_order,
                    position
            )
            GROUP BY
                draw_number,
                draw_date,
                wheel,
                wheel_order
            ORDER BY
                draw_number,
                wheel_order
            """
        ).fetchall()

except (
    sqlite3.Error,
    ValueError,
) as error:
    print(
        f"ERRORE: {error}",
        file=sys.stderr,
    )
    raise SystemExit(1)


draws: dict[
    tuple[int, str],
    dict[str, str],
] = {}

for (
    draw_number,
    draw_date,
    wheel,
    wheel_order,
    numbers,
) in rows:
    key = (
        draw_number,
        draw_date,
    )

    draws.setdefault(
        key,
        {},
    )[wheel] = numbers


draw_width = max(
    len("Estr"),
    len(str(last_draw)),
)

wheel_width = 14

print(f"Database:      {database}")
print(f"Estrazioni:    {count}")
print(
    f"Intervallo:    "
    f"{first_draw}–{last_draw}"
)

if selected_digits:
    print(
        "Cifre evidenziate: "
        + ", ".join(selected_digits)
    )

if selected_numbers:
    print(
        "Numeri evidenziati: "
        + ", ".join(
            str(number)
            for number in selected_numbers
        )
    )

print()

header = (
    f"{'Estr':>{draw_width}}  "
    f"{'Data':<5}  "
    + "  ".join(
        f"{wheel:<{wheel_width}}"
        for wheel in EXPECTED_WHEELS
    )
)

separator = (
    f"{'-' * draw_width}  "
    f"{'-' * 5}  "
    + "  ".join(
        "-" * wheel_width
        for _ in EXPECTED_WHEELS
    )
)

print(header)
print(separator)

digit_set = set(selected_digits)
number_set = set(selected_numbers)

for (
    draw_number,
    draw_date,
), wheel_results in draws.items():
    prefix = (
        f"{draw_number:>{draw_width}}  "
        f"{draw_date[5:]:<5}  "
    )

    formatted_wheels: list[str] = []

    for wheel in EXPECTED_WHEELS:
        plain_cell = wheel_results.get(
            wheel,
            "-",
        ).ljust(wheel_width)

        formatted_wheels.append(
            highlight_cell(
                plain_cell,
                digit_set,
                number_set,
            )
        )

    print(
        prefix
        + "  ".join(formatted_wheels)
    )
PYTHON

PYTHON_EXIT="$?"

if test "$PYTHON_EXIT" -ne 0; then
    exit "$PYTHON_EXIT"
fi

less -RS "$OUTPUT"
