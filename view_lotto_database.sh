#!/usr/bin/env bash

DATABASE="data/lotto-2026.sqlite3"
DATABASE_SET=0
DIGITS=()
NUMBERS=()
LATEST_OCCURRENCES=0
LATEST_OCCURRENCES_DRAW=""

usage() {
    cat <<'HELP'
Uso:
  ./view_lotto_database.sh [DATABASE]
  ./view_lotto_database.sh [--database PATH] [--digit CIFRE]... [--number NUMERI]...
  ./view_lotto_database.sh [--database PATH] --latest-occurrences [NUM_ESTRAZIONE]

Visualizza le estrazioni del database in una tabella larga.

Opzioni:
  --database PATH       Database SQLite da visualizzare.
  --digit CIFRE         Evidenzia una o più cifre da 0 a 9.
                        L'opzione può essere ripetuta.
                        Sono accettate anche cifre separate da virgola.
  --number NUMERI       Evidenzia uno o più numeri da 1 a 90.
                        L'opzione può essere ripetuta.
                        Sono accettati anche numeri separati da virgola.
  --latest-occurrences [NUM_ESTRAZIONE]
                        Traccia retrospettivamente le occorrenze dei cinque
                        numeri di riferimento sulla stessa ruota.
                        Senza valore usa l'ultima estrazione completa.
                        Con un valore applica un cutoff storico inclusivo.
                        Mostra le righe in ordine cronologico discendente.
                        Non è compatibile con --digit o --number.
  -h, --help            Mostra questo messaggio.

Per un database diverso usare la forma non ambigua:
  --database PATH --latest-occurrences [NUM_ESTRAZIONE]

Esempi:
  ./view_lotto_database.sh
  ./view_lotto_database.sh --digit 7
  ./view_lotto_database.sh --digit 1,7,9
  ./view_lotto_database.sh --number 17
  ./view_lotto_database.sh --number 1,17,90
  ./view_lotto_database.sh --digit 7 --number 17,90
  ./view_lotto_database.sh --latest-occurrences
  ./view_lotto_database.sh --database data/lotto-2025.sqlite3 --latest-occurrences
  ./view_lotto_database.sh --database data/lotto-2025.sqlite3 --latest-occurrences 100

Questa modalità è una visualizzazione retrospettiva.
Non costituisce un segnale previsionale o una raccomandazione di gioco.
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

        --latest-occurrences)
            LATEST_OCCURRENCES=1
            shift

            if test "$#" -gt 0; then
                if [[ "$1" != -* ]] || [[ "$1" =~ ^-[0-9]+$ ]]; then
                    candidate="$1"

                    if [[
                        "$candidate" == */*
                        || "$candidate" == *.db
                        || "$candidate" == *.sqlite
                        || "$candidate" == *.sqlite3
                    ]]; then
                        printf '%s %s\n' \
                            "ERRORE: forma ambigua dopo --latest-occurrences:" \
                            "'$candidate'. Specificare il database con --database PATH." \
                            >&2
                        exit 2
                    fi

                    if [[ ! "$candidate" =~ ^[0-9]+$ || ! "$candidate" =~ [1-9] ]]; then
                        printf '%s %s\n' \
                            "ERRORE: --latest-occurrences accetta soltanto" \
                            "un numero di estrazione intero positivo; ricevuto '$candidate'." \
                            >&2
                        exit 2
                    fi

                    LATEST_OCCURRENCES_DRAW="$candidate"
                    shift
                fi
            fi
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


if test "$LATEST_OCCURRENCES" -eq 1 && {
    test "${#DIGITS[@]}" -gt 0 ||
    test "${#NUMBERS[@]}" -gt 0
}; then
    printf '%s\n' \
        "ERRORE: --latest-occurrences non è compatibile con --digit o --number." \
        >&2
    exit 2
fi


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


python3 - "$DATABASE" \
    --latest-occurrences "$LATEST_OCCURRENCES" \
    --latest-occurrences-draw "$LATEST_OCCURRENCES_DRAW" \
    --digits "${DIGITS[@]}" \
    --numbers "${NUMBERS[@]}" \
    > "$OUTPUT" <<'PYTHON'
from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path


HIGHLIGHT = "\033[1;30;46m"
RESET = "\033[0m"

OCCURRENCE_HIGHLIGHTS = (
    "\033[1;30;41m",
    "\033[1;30;42m",
    "\033[1;30;43m",
    "\033[1;30;44m",
    "\033[1;30;45m",
)

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


def highlight_occurrence_cell(
    text: str,
    highlights: dict[str, str],
) -> str:
    if not highlights:
        return text

    rendered: list[str] = []
    cursor = 0

    for match in NUMBER_PATTERN.finditer(text):
        rendered.append(
            text[cursor:match.start()]
        )

        token = match.group()
        color = highlights.get(token)

        if color is None:
            rendered.append(token)
        else:
            rendered.append(
                f"{color}{token}{RESET}"
            )

        cursor = match.end()

    rendered.append(text[cursor:])

    return "".join(rendered)


database = Path(sys.argv[1])

latest_marker = sys.argv.index(
    "--latest-occurrences",
    2,
)
latest_draw_marker = sys.argv.index(
    "--latest-occurrences-draw",
    latest_marker + 1,
)
digits_marker = sys.argv.index(
    "--digits",
    latest_draw_marker + 1,
)
numbers_marker = sys.argv.index(
    "--numbers",
    digits_marker + 1,
)

latest_occurrences = (
    sys.argv[latest_marker + 1] == "1"
)
latest_occurrences_draw = (
    sys.argv[latest_draw_marker + 1]
)

try:
    selected_digits = parse_digits(
        sys.argv[digits_marker + 1:numbers_marker]
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


def chronological_key(
    draw_key: tuple[int, str],
) -> tuple[str, int]:
    draw_number, draw_date = draw_key

    return (
        draw_date,
        draw_number,
    )


def is_complete_draw(
    wheel_results: dict[str, str],
) -> bool:
    return all(
        wheel in wheel_results
        and len(wheel_results[wheel].split()) == 5
        for wheel in EXPECTED_WHEELS
    )


def validate_reference_draw(
    draw_key: tuple[int, str],
    wheel_results: dict[str, str],
) -> None:
    draw_number, draw_date = draw_key

    for wheel in EXPECTED_WHEELS:
        if wheel not in wheel_results:
            raise ValueError(
                "estrazione di riferimento "
                f"{draw_number} del {draw_date}: "
                f"ruota attesa mancante: {wheel}."
            )

        tokens = wheel_results[wheel].split()

        if len(tokens) != 5:
            raise ValueError(
                "estrazione di riferimento "
                f"{draw_number} del {draw_date}: "
                f"la ruota {wheel} contiene "
                f"{len(tokens)} valori anziché 5."
            )

        for token in tokens:
            if (
                len(token) != 2
                or not token.isascii()
                or not token.isdigit()
                or not 1 <= int(token) <= 90
            ):
                raise ValueError(
                    "estrazione di riferimento "
                    f"{draw_number} del {draw_date}: "
                    "valore fuori dall'intervallo "
                    f"01–90 sulla ruota {wheel}: "
                    f"{token!r}."
                )


reference_key: tuple[int, str] | None = None
reference_kind: str | None = None

if latest_occurrences:
    try:
        complete_keys = [
            key
            for key, wheel_results in draws.items()
            if is_complete_draw(wheel_results)
        ]

        if latest_occurrences_draw:
            requested_draw = int(
                latest_occurrences_draw
            )
            candidates = [
                key
                for key in draws
                if key[0] == requested_draw
            ]

            if not candidates:
                raise ValueError(
                    "estrazione di riferimento "
                    f"{requested_draw} non trovata."
                )

            if len(candidates) > 1:
                raise ValueError(
                    "numero di estrazione ambiguo: "
                    f"{requested_draw}."
                )

            reference_key = candidates[0]
            reference_kind = "esplicito"
        else:
            if not complete_keys:
                raise ValueError(
                    "nessuna estrazione completa "
                    "disponibile."
                )

            reference_key = max(
                complete_keys,
                key=chronological_key,
            )
            reference_kind = "automatico"

    except ValueError as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)


reference_highlights: dict[
    str,
    dict[str, str],
] = {}

if reference_key is not None:
    reference_results = draws[reference_key]

    try:
        validate_reference_draw(
            reference_key,
            reference_results,
        )
    except ValueError as error:
        print(
            f"ERRORE: {error}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    for wheel in EXPECTED_WHEELS:
        tokens = reference_results[wheel].split()

        reference_highlights[wheel] = {
            token: color
            for token, color in zip(
                tokens,
                OCCURRENCE_HIGHLIGHTS,
                strict=True,
            )
        }


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

if reference_key is not None:
    reference_number, reference_date = reference_key

    print(
        "Riferimento:  "
        f"{reference_kind} — "
        f"estrazione {reference_number} "
        f"del {reference_date}"
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

if reference_key is None:
    rendered_draws = list(
        draws.items()
    )
else:
    rendered_draws = sorted(
        (
            (
                key,
                wheel_results,
            )
            for key, wheel_results in draws.items()
            if chronological_key(key)
            <= chronological_key(reference_key)
        ),
        key=lambda item: chronological_key(
            item[0]
        ),
        reverse=True,
    )

for (
    draw_number,
    draw_date,
), wheel_results in rendered_draws:
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

        if reference_key is None:
            rendered_cell = highlight_cell(
                plain_cell,
                digit_set,
                number_set,
            )
        else:
            rendered_cell = highlight_occurrence_cell(
                plain_cell,
                reference_highlights[wheel],
            )

        formatted_wheels.append(
            rendered_cell
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
