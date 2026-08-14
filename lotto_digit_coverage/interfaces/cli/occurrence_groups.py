"""Terminal rendering for structured occurrence-group reports."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TextIO
import sys

from lotto_digit_coverage.application.occurrence_groups import (
    OccurrenceDrawRow,
    OccurrenceGroup,
    OccurrenceGroupReport,
)


RESET = "\033[0m"
OCCURRENCE_HIGHLIGHTS = (
    "\033[1;30;41m",
    "\033[1;30;42m",
    "\033[1;30;43m",
    "\033[1;30;44m",
    "\033[1;30;45m",
)


def _format_numbers_cell(
    numbers: Sequence[int] | None,
    *,
    token_width: int,
    wheel_width: int,
    highlights: dict[int, str],
) -> str:
    if numbers is None:
        return "-".ljust(wheel_width)

    rendered: list[str] = []
    for number in numbers:
        token = f"{number:02d}"
        padded = f"{token:>{token_width}}"
        color = highlights.get(number)
        if color is None:
            rendered.append(padded)
        else:
            rendered.append(f"{color}{padded}{RESET}")

    visible_width = len(numbers) * token_width + max(0, len(numbers) - 1)
    return " ".join(rendered) + " " * max(0, wheel_width - visible_width)


def _format_total_cell(
    counts: Sequence[int],
    *,
    token_width: int,
    wheel_width: int,
) -> str:
    rendered = [
        f"{color}{count:0{token_width}d}{RESET}"
        for count, color in zip(
            counts,
            OCCURRENCE_HIGHLIGHTS,
            strict=True,
        )
    ]
    visible_width = len(counts) * token_width + max(0, len(counts) - 1)
    return " ".join(rendered) + " " * max(0, wheel_width - visible_width)


def _reference_highlights(group: OccurrenceGroup) -> dict[str, dict[int, str]]:
    return {
        row.wheel: {
            number: color
            for number, color in zip(
                row.reference_numbers,
                OCCURRENCE_HIGHLIGHTS,
                strict=True,
            )
        }
        for row in group.wheels
    }


def _render_draw_line(
    draw: OccurrenceDrawRow,
    *,
    usage: str,
    expected_wheels: Sequence[str],
    highlights: dict[str, dict[int, str]],
    draw_width: int,
    token_width: int,
    wheel_width: int,
) -> str:
    prefix = (
        f"{usage:<5}  "
        f"{draw.draw_number:>{draw_width}}  "
        f"{draw.draw_date[5:]:<5}  "
    )
    cells = []

    for wheel in expected_wheels:
        cells.append(
            _format_numbers_cell(
                draw.numbers_for(wheel),
                token_width=token_width,
                wheel_width=wheel_width,
                highlights=highlights[wheel],
            )
        )

    return prefix + "  ".join(cells)


def render_occurrence_group_report(
    report: OccurrenceGroupReport,
    *,
    database: Path,
    draw_count: int,
    first_draw: int | None,
    last_draw: int | None,
    expected_wheels: Sequence[str],
    stream: TextIO = sys.stdout,
) -> None:
    """Render the grouped report without recalculating occurrence counts."""

    draw_width = max(
        len("Estr"),
        len(str(last_draw)),
    )
    token_width = max(2, len(str(report.group_size)))
    wheel_width = max(14, 5 * token_width + 4)

    print(f"Database:      {database}", file=stream)
    print(f"Estrazioni:    {draw_count}", file=stream)
    print(f"Intervallo:    {first_draw}–{last_draw}", file=stream)
    print(
        "Riferimento:  "
        f"{report.reference_kind} — "
        f"estrazione {report.reference_draw_number} "
        f"del {report.reference_draw_date}",
        file=stream,
    )
    print(
        "Gruppi:       "
        f"{report.group_size} estrazioni analizzate per gruppo; "
        "ogni gruppo ha inoltre una propria estrazione di riferimento, "
        "esclusa dai conteggi.",
        file=stream,
    )
    print(file=stream)

    header = (
        f"{'Uso':<5}  "
        f"{'Estr':>{draw_width}}  "
        f"{'Data':<5}  "
        + "  ".join(
            f"{wheel:<{wheel_width}}"
            for wheel in expected_wheels
        )
    )
    separator = (
        f"{'-' * 5}  "
        f"{'-' * draw_width}  "
        f"{'-' * 5}  "
        + "  ".join(
            "-" * wheel_width
            for _ in expected_wheels
        )
    )
    print(header, file=stream)
    print(separator, file=stream)

    for group in report.groups:
        print(file=stream)
        print(
            f"Gruppo: riferimento {group.reference_draw_number} "
            f"del {group.reference_draw_date}; "
            f"analisi {group.newest_draw_number}–{group.oldest_draw_number} "
            f"({group.size} estrazioni conteggiate)",
            file=stream,
        )

        highlights = _reference_highlights(group)
        print(
            _render_draw_line(
                group.reference_draw,
                usage="Rif.",
                expected_wheels=expected_wheels,
                highlights=highlights,
                draw_width=draw_width,
                token_width=token_width,
                wheel_width=wheel_width,
            ),
            file=stream,
        )
        for draw in group.draws:
            print(
                _render_draw_line(
                    draw,
                    usage="Conta",
                    expected_wheels=expected_wheels,
                    highlights=highlights,
                    draw_width=draw_width,
                    token_width=token_width,
                    wheel_width=wheel_width,
                ),
                file=stream,
            )

        summaries = {row.wheel: row for row in group.wheels}
        total_prefix = f"{'Tot':<5}  {'':>{draw_width}}  {'':<5}  "
        total_cells = [
            _format_total_cell(
                summaries[wheel].occurrence_counts,
                token_width=token_width,
                wheel_width=wheel_width,
            )
            for wheel in expected_wheels
        ]
        print(total_prefix + "  ".join(total_cells), file=stream)
