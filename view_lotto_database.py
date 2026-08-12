#!/usr/bin/env python3

"""Visualizzatore del database Lotto con evidenziazioni retrospettive."""

from __future__ import annotations

import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence, TextIO


DEFAULT_DATABASE = Path("data/lotto-current.sqlite3")

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

NUMBER_PATTERN = re.compile(r"(?<!\d)\d{2}(?!\d)")


@dataclass(frozen=True)
class Options:
    database: Path
    digits: tuple[str, ...]
    numbers: tuple[int, ...]
    latest_occurrences: bool
    latest_occurrences_draw: str
    occurrence_groups: int | None


class CliError(ValueError):
    def __init__(
        self,
        message: str,
        *,
        show_usage: bool = False,
    ) -> None:
        super().__init__(message)
        self.show_usage = show_usage


def usage(stream: TextIO = sys.stdout) -> None:
    print(
        """Uso:
  ./view_lotto_database.sh [DATABASE]
  ./view_lotto_database.sh [--database PATH] [--digit CIFRE]... [--number NUMERI]...
  ./view_lotto_database.sh [--database PATH] --latest-occurrences [NUM_ESTRAZIONE]
  ./view_lotto_database.sh [--database PATH] --latest-occurrences [NUM_ESTRAZIONE] --occurrence-groups N

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
  --occurrence-groups N Raggruppa --latest-occurrences in blocchi consecutivi
                        di N estrazioni. Ogni blocco usa come riferimento
                        la propria estrazione più recente e mostra una riga
                        Tot con le presenze dei cinque numeri, mantenendo
                        l'ordine delle cinque posizioni di riferimento.
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
  ./view_lotto_database.sh --latest-occurrences --occurrence-groups 10
  ./view_lotto_database.sh --database data/lotto-2025.sqlite3 --latest-occurrences
  ./view_lotto_database.sh --database data/lotto-2025.sqlite3 --latest-occurrences 100
  ./view_lotto_database.sh --database data/lotto-2025.sqlite3 --latest-occurrences 100 --occurrence-groups 10

Questa modalità è una visualizzazione retrospettiva.
Non costituisce un segnale previsionale o una raccomandazione di gioco.""",
        file=stream,
    )


def parse_digits(values: Sequence[str]) -> tuple[str, ...]:
    digits: set[str] = set()

    for value in values:
        for part in value.split(","):
            normalized = part.strip()

            if (
                len(normalized) != 1
                or normalized not in "0123456789"
            ):
                raise CliError(
                    "--digit accetta soltanto cifre singole "
                    "comprese tra 0 e 9; "
                    f"ricevuto {part!r}."
                )

            digits.add(normalized)

    return tuple(sorted(digits, key=int))


def parse_numbers(values: Sequence[str]) -> tuple[int, ...]:
    numbers: set[int] = set()

    for value in values:
        for part in value.split(","):
            normalized = part.strip()

            if (
                not normalized.isascii()
                or not normalized.isdigit()
            ):
                raise CliError(
                    "--number accetta soltanto numeri interi "
                    "compresi tra 1 e 90; "
                    f"ricevuto {part!r}."
                )

            number = int(normalized)

            if not 1 <= number <= 90:
                raise CliError(
                    "--number accetta soltanto numeri interi "
                    "compresi tra 1 e 90; "
                    f"ricevuto {part!r}."
                )

            numbers.add(number)

    return tuple(sorted(numbers))


def _positive_integer(value: str, option: str) -> int:
    if (
        not value.isascii()
        or not value.isdigit()
        or not any(character in "123456789" for character in value)
    ):
        raise CliError(
            f"{option} accetta soltanto un intero positivo; "
            f"ricevuto {value!r}."
        )

    return int(value)


def parse_options(argv: Sequence[str]) -> Options | None:
    database = DEFAULT_DATABASE
    database_set = False
    digit_values: list[str] = []
    number_values: list[str] = []
    latest_occurrences = False
    latest_occurrences_draw = ""
    occurrence_groups: int | None = None

    arguments = list(argv)
    index = 0

    while index < len(arguments):
        argument = arguments[index]

        if argument in {"-h", "--help"}:
            usage()
            return None

        if argument == "--database":
            if index + 1 >= len(arguments):
                raise CliError("--database richiede un percorso.")

            database = Path(arguments[index + 1])
            database_set = True
            index += 2
            continue

        if argument == "--digit":
            if index + 1 >= len(arguments):
                raise CliError("--digit richiede almeno una cifra.")

            digit_values.append(arguments[index + 1])
            index += 2
            continue

        if argument == "--number":
            if index + 1 >= len(arguments):
                raise CliError("--number richiede almeno un numero.")

            number_values.append(arguments[index + 1])
            index += 2
            continue

        if argument == "--latest-occurrences":
            latest_occurrences = True
            index += 1

            if index < len(arguments):
                candidate = arguments[index]

                if (
                    not candidate.startswith("-")
                    or re.fullmatch(r"-[0-9]+", candidate) is not None
                ):
                    if (
                        "/" in candidate
                        or candidate.endswith(".db")
                        or candidate.endswith(".sqlite")
                        or candidate.endswith(".sqlite3")
                    ):
                        raise CliError(
                            "forma ambigua dopo --latest-occurrences: "
                            f"{candidate!r}. Specificare il database "
                            "con --database PATH."
                        )

                    if (
                        not candidate.isascii()
                        or not candidate.isdigit()
                        or not any(
                            character in "123456789"
                            for character in candidate
                        )
                    ):
                        raise CliError(
                            "--latest-occurrences accetta soltanto "
                            "un numero di estrazione intero positivo; "
                            f"ricevuto {candidate!r}."
                        )

                    latest_occurrences_draw = candidate
                    index += 1

            continue

        if argument == "--occurrence-groups":
            if index + 1 >= len(arguments):
                raise CliError(
                    "--occurrence-groups richiede un numero di estrazioni."
                )

            if occurrence_groups is not None:
                raise CliError(
                    "--occurrence-groups può essere specificato una sola volta."
                )

            occurrence_groups = _positive_integer(
                arguments[index + 1],
                "--occurrence-groups",
            )
            index += 2
            continue

        if argument.startswith("-"):
            raise CliError(
                f"opzione sconosciuta: {argument}",
                show_usage=True,
            )

        if database_set:
            raise CliError("database specificato più volte.")

        database = Path(argument)
        database_set = True
        index += 1

    if latest_occurrences and (digit_values or number_values):
        raise CliError(
            "--latest-occurrences non è compatibile con --digit o --number."
        )

    if occurrence_groups is not None and not latest_occurrences:
        raise CliError(
            "--occurrence-groups richiede --latest-occurrences."
        )

    digits = parse_digits(digit_values)
    numbers = parse_numbers(number_values)

    return Options(
        database=database,
        digits=digits,
        numbers=numbers,
        latest_occurrences=latest_occurrences,
        latest_occurrences_draw=latest_occurrences_draw,
        occurrence_groups=occurrence_groups,
    )


def highlight_digits(text: str, digits: set[str]) -> str:
    if not digits:
        return text

    return "".join(
        f"{HIGHLIGHT}{character}{RESET}"
        if character in digits
        else character
        for character in text
    )


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
        rendered.append(text[cursor:match.start()])
        token = match.group()

        if int(token) in numbers:
            rendered.append(f"{HIGHLIGHT}{token}{RESET}")
        else:
            rendered.append(highlight_digits(token, digits))

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
        rendered.append(text[cursor:match.start()])
        token = match.group()
        color = highlights.get(token)

        if color is None:
            rendered.append(token)
        else:
            rendered.append(f"{color}{token}{RESET}")

        cursor = match.end()

    rendered.append(text[cursor:])
    return "".join(rendered)


def chronological_key(
    draw_key: tuple[int, str],
) -> tuple[str, int]:
    draw_number, draw_date = draw_key
    return draw_date, draw_number


def is_complete_draw(wheel_results: dict[str, str]) -> bool:
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
                    f"01–90 sulla ruota {wheel}: {token!r}."
                )


def build_reference_highlights(
    reference_results: dict[str, str],
) -> dict[str, dict[str, str]]:
    return {
        wheel: {
            token: color
            for token, color in zip(
                reference_results[wheel].split(),
                OCCURRENCE_HIGHLIGHTS,
                strict=True,
            )
        }
        for wheel in EXPECTED_WHEELS
    }


def load_database(
    database: Path,
) -> tuple[
    int,
    int | None,
    int | None,
    dict[tuple[int, str], dict[str, str]],
]:
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
    except sqlite3.Error as error:
        raise ValueError(str(error)) from error

    draws: dict[tuple[int, str], dict[str, str]] = {}

    for (
        draw_number,
        draw_date,
        wheel,
        _wheel_order,
        numbers,
    ) in rows:
        key = int(draw_number), str(draw_date)
        draws.setdefault(key, {})[str(wheel)] = str(numbers)

    return int(count), first_draw, last_draw, draws


def select_reference(
    draws: dict[tuple[int, str], dict[str, str]],
    requested: str,
) -> tuple[tuple[int, str], str]:
    complete_keys = [
        key
        for key, wheel_results in draws.items()
        if is_complete_draw(wheel_results)
    ]

    if requested:
        requested_draw = int(requested)
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

        return candidates[0], "esplicito"

    if not complete_keys:
        raise ValueError(
            "nessuna estrazione completa disponibile."
        )

    return (
        max(complete_keys, key=chronological_key),
        "automatico",
    )


def _format_numbers_cell(
    value: str,
    *,
    token_width: int,
    wheel_width: int,
) -> str:
    if value == "-":
        return value.ljust(wheel_width)

    tokens = value.split()
    rendered = " ".join(
        f"{token:>{token_width}}"
        for token in tokens
    )
    return rendered.ljust(wheel_width)


def _group_occurrence_counts(
    group: Sequence[
        tuple[
            tuple[int, str],
            dict[str, str],
        ]
    ],
    reference_results: dict[str, str],
) -> dict[str, tuple[int, ...]]:
    counts: dict[str, tuple[int, ...]] = {}

    for wheel in EXPECTED_WHEELS:
        reference_tokens = reference_results[wheel].split()
        wheel_counts: list[int] = []

        for token in reference_tokens:
            occurrences = 0

            for _key, wheel_results in group:
                observed = wheel_results.get(wheel, "").split()

                if token in observed:
                    occurrences += 1

            wheel_counts.append(occurrences)

        counts[wheel] = tuple(wheel_counts)

    return counts


def _format_total_cell(
    counts: Sequence[int],
    *,
    token_width: int,
    wheel_width: int,
) -> str:
    rendered_tokens = [
        f"{color}{count:0{token_width}d}{RESET}"
        for count, color in zip(
            counts,
            OCCURRENCE_HIGHLIGHTS,
            strict=True,
        )
    ]
    visible_width = len(counts) * token_width + max(0, len(counts) - 1)
    padding = max(0, wheel_width - visible_width)
    return " ".join(rendered_tokens) + " " * padding


def _render_draw_line(
    key: tuple[int, str],
    wheel_results: dict[str, str],
    *,
    draw_width: int,
    wheel_width: int,
    token_width: int,
    digits: set[str],
    numbers: set[int],
    occurrence_highlights: dict[str, dict[str, str]] | None,
) -> str:
    draw_number, draw_date = key
    prefix = (
        f"{draw_number:>{draw_width}}  "
        f"{draw_date[5:]:<5}  "
    )
    formatted_wheels: list[str] = []

    for wheel in EXPECTED_WHEELS:
        raw_cell = wheel_results.get(wheel, "-")
        plain_cell = _format_numbers_cell(
            raw_cell,
            token_width=token_width,
            wheel_width=wheel_width,
        )

        if occurrence_highlights is not None:
            rendered_cell = highlight_occurrence_cell(
                plain_cell,
                occurrence_highlights[wheel],
            )
        else:
            rendered_cell = highlight_cell(
                plain_cell,
                digits,
                numbers,
            )

        formatted_wheels.append(rendered_cell)

    return prefix + "  ".join(formatted_wheels)


def render(options: Options) -> str:
    if not options.database.is_file():
        raise FileNotFoundError(
            f"database assente: {options.database}"
        )

    count, first_draw, last_draw, draws = load_database(options.database)

    reference_key: tuple[int, str] | None = None
    reference_kind: str | None = None

    if options.latest_occurrences:
        reference_key, reference_kind = select_reference(
            draws,
            options.latest_occurrences_draw,
        )
        validate_reference_draw(
            reference_key,
            draws[reference_key],
        )

    draw_width = max(
        len("Estr"),
        len(str(last_draw)),
    )
    token_width = (
        max(2, len(str(options.occurrence_groups)))
        if options.occurrence_groups is not None
        else 2
    )
    wheel_width = max(
        14,
        5 * token_width + 4,
    )

    lines: list[str] = []
    lines.append(f"Database:      {options.database}")
    lines.append(f"Estrazioni:    {count}")
    lines.append(f"Intervallo:    {first_draw}–{last_draw}")

    if options.digits:
        lines.append(
            "Cifre evidenziate: "
            + ", ".join(options.digits)
        )

    if options.numbers:
        lines.append(
            "Numeri evidenziati: "
            + ", ".join(str(number) for number in options.numbers)
        )

    if reference_key is not None and reference_kind is not None:
        reference_number, reference_date = reference_key
        lines.append(
            "Riferimento:  "
            f"{reference_kind} — "
            f"estrazione {reference_number} "
            f"del {reference_date}"
        )

    if options.occurrence_groups is not None:
        lines.append(
            "Gruppi:       "
            f"{options.occurrence_groups} estrazioni; "
            "ogni gruppo usa la propria estrazione più recente."
        )

    lines.append("")

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

    lines.append(header)
    lines.append(separator)

    digit_set = set(options.digits)
    number_set = set(options.numbers)

    if reference_key is None:
        rendered_draws = list(draws.items())
    else:
        rendered_draws = sorted(
            (
                (key, wheel_results)
                for key, wheel_results in draws.items()
                if chronological_key(key)
                <= chronological_key(reference_key)
            ),
            key=lambda item: chronological_key(item[0]),
            reverse=True,
        )

    if options.occurrence_groups is None:
        occurrence_highlights = None

        if reference_key is not None:
            occurrence_highlights = build_reference_highlights(
                draws[reference_key]
            )

        for key, wheel_results in rendered_draws:
            lines.append(
                _render_draw_line(
                    key,
                    wheel_results,
                    draw_width=draw_width,
                    wheel_width=wheel_width,
                    token_width=token_width,
                    digits=digit_set,
                    numbers=number_set,
                    occurrence_highlights=occurrence_highlights,
                )
            )

        return "\n".join(lines)

    group_size = options.occurrence_groups

    for start in range(0, len(rendered_draws), group_size):
        group = rendered_draws[start:start + group_size]

        if not group:
            continue

        group_reference_key, group_reference_results = group[0]
        validate_reference_draw(
            group_reference_key,
            group_reference_results,
        )
        group_highlights = build_reference_highlights(
            group_reference_results
        )
        newest_number, newest_date = group_reference_key
        oldest_number, _oldest_date = group[-1][0]

        lines.append("")
        lines.append(
            f"Gruppo {newest_number}–{oldest_number} "
            f"({len(group)} estrazioni) — "
            f"riferimento {newest_number} del {newest_date}"
        )

        for key, wheel_results in group:
            lines.append(
                _render_draw_line(
                    key,
                    wheel_results,
                    draw_width=draw_width,
                    wheel_width=wheel_width,
                    token_width=token_width,
                    digits=set(),
                    numbers=set(),
                    occurrence_highlights=group_highlights,
                )
            )

        counts = _group_occurrence_counts(
            group,
            group_reference_results,
        )
        total_prefix = (
            f"{'Tot':>{draw_width}}  "
            f"{'':<5}  "
        )
        total_cells = [
            _format_total_cell(
                counts[wheel],
                token_width=token_width,
                wheel_width=wheel_width,
            )
            for wheel in EXPECTED_WHEELS
        ]
        lines.append(total_prefix + "  ".join(total_cells))

    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else list(argv)

    try:
        options = parse_options(arguments)
    except CliError as error:
        print(f"ERRORE: {error}", file=sys.stderr)

        if error.show_usage:
            print(file=sys.stderr)
            usage(sys.stderr)

        return 2

    if options is None:
        return 0

    try:
        output = render(options)
    except FileNotFoundError as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    except (sqlite3.Error, ValueError) as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
