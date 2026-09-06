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
from lotto_digit_coverage.interfaces.cli.occurrence_localization import occurrence_text
from lotto_digit_coverage.interfaces.localization import CANONICAL_LOCALE


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
    total: int,
    token_width: int,
    sum_width: int,
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
    base = " ".join(rendered)
    suffix = f" | Σ{total:0{sum_width}d}"
    visible_width = (
        len(counts) * token_width
        + max(0, len(counts) - 1)
        + len(suffix)
    )
    return base + suffix + " " * max(0, wheel_width - visible_width)


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
    locale: str = CANONICAL_LOCALE,
    stream: TextIO = sys.stdout,
) -> None:
    """Render the grouped report without recalculating occurrence counts."""

    draw_header = occurrence_text("draw_header", locale)
    draw_width = max(
        len(draw_header),
        len(str(last_draw)),
    )
    token_width = max(2, len(str(report.group_size)))
    sum_width = max(2, len(str(report.group_size * 5)))
    base_wheel_width = 5 * token_width + 4
    wheel_width = max(14, base_wheel_width + len(f" | Σ{'0' * sum_width}"))

    print(f"{occurrence_text('database_label', locale)}:      {database}", file=stream)
    print(f"{occurrence_text('draws_label', locale)}:    {draw_count}", file=stream)
    print(f"{occurrence_text('range_label', locale)}:    {first_draw}–{last_draw}", file=stream)
    print(
        f"{occurrence_text('reference_label', locale)}:  "
        f"{report.reference_kind} — "
        f"{occurrence_text('draw', locale)} {report.reference_draw_number} "
        f"{occurrence_text('of', locale)} {report.reference_draw_date}",
        file=stream,
    )
    print(
        f"{occurrence_text('groups_label', locale)}:       "
        + occurrence_text("groups_description", locale).format(
            group_size=report.group_size
        ),
        file=stream,
    )
    limit_text = (
        occurrence_text("global_limit", locale).format(limit=report.occurrence_limit)
        if report.occurrence_limit is not None
        else occurrence_text("no_global_limit", locale)
    )
    print(
        f"{occurrence_text('limit_label', locale)}:       "
        + limit_text
        + occurrence_text("examined_draws", locale).format(
            count=report.examined_draw_count
        ),
        file=stream,
    )
    print(file=stream)

    header = (
        f"{occurrence_text('usage_header', locale):<5}  "
        f"{draw_header:>{draw_width}}  "
        f"{occurrence_text('date_header', locale):<5}  "
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
            occurrence_text("group_summary", locale).format(
                reference_draw=group.reference_draw_number,
                reference_date=group.reference_draw_date,
                newest=group.newest_draw_number,
                oldest=group.oldest_draw_number,
                size=group.size,
            ),
            file=stream,
        )

        highlights = _reference_highlights(group)
        print(
            _render_draw_line(
                group.reference_draw,
                usage=occurrence_text("reference_usage", locale),
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
                    usage=occurrence_text("count_usage", locale),
                    expected_wheels=expected_wheels,
                    highlights=highlights,
                    draw_width=draw_width,
                    token_width=token_width,
                    wheel_width=wheel_width,
                ),
                file=stream,
            )

        summaries = {row.wheel: row for row in group.wheels}
        total_prefix = (
            f"{occurrence_text('total_usage', locale):<5}  "
            f"{'':>{draw_width}}  {'':<5}  "
        )
        total_cells = [
            _format_total_cell(
                summaries[wheel].occurrence_counts,
                total=summaries[wheel].total_occurrences,
                token_width=token_width,
                sum_width=sum_width,
                wheel_width=wheel_width,
            )
            for wheel in expected_wheels
        ]
        print(total_prefix + "  ".join(total_cells), file=stream)

    print(file=stream)
    print(
        f"{occurrence_text('grand_total', locale)}: {report.grand_total_occurrences}",
        file=stream,
    )
