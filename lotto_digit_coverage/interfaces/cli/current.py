"""Terminal adapter for the structured current coverage report."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TextIO
import sys

from analyze_coverage_anomalies import ALL_CATEGORIES, AnomalyEvent
from strategies.current_coverage_signal import CurrentCoverageSignal

from lotto_digit_coverage.application.current import CurrentCoverageReport
from lotto_digit_coverage.interfaces.cli.consensus import render_digit_consensus
from lotto_digit_coverage.interfaces.localization import (
    CANONICAL_LOCALE,
    DEFAULT_PRESENTATION_CATALOG,
)


ANSI_RESET = "\033[0m"
ANSI_TOP = "\033[1;30;46m"
ANSI_MISSING = "\033[1;30;43m"


def _text(key: str, locale: str) -> str:
    return DEFAULT_PRESENTATION_CATALOG.resolve(key, locale).text


def _digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(str(digit) for digit in sorted(digits)) + "}"


def _print_markov(
    report: CurrentCoverageReport,
    stream: TextIO,
    *,
    locale: str,
) -> None:
    print(_text("cli.current.markov_title", locale), file=stream)
    print(_text("cli.current.markov_state", locale), file=stream)
    print(_text("cli.current.markov_ranking", locale), file=stream)
    print(_text("cli.current.markov_top", locale), file=stream)
    print(file=stream)
    print(
        f"{_text('cli.current.pos', locale):<5}"
        f"{_text('cli.current.wheel', locale):<12}"
        f"{_text('cli.current.last', locale):<8}"
        f"{_text('cli.current.cycles', locale):<7}"
        f"{_text('cli.current.age', locale):<5}"
        f"{_text('cli.current.most_present', locale):<23}"
        f"{_text('cli.current.missing', locale):<23}"
        f"{_text('cli.current.within1', locale)}  "
        f"{_text('cli.current.within2', locale)}  "
        f"{_text('cli.current.within3', locale)}  "
        f"{_text('cli.current.within5', locale)}  "
        f"{_text('cli.current.expected', locale)}",
        file=stream,
    )
    print(
        f"{'---':<5}{'----------':<12}{'------':<8}{'-----':<7}{'---':<5}"
        f"{'-------------':<23}{'-------------':<23}"
        "--------  --------  --------  --------  --------",
        file=stream,
    )

    for position, row in enumerate(report.markov_ranking, start=1):
        state = row.state
        print(
            f"{position:<5}{state.wheel:<12}{state.latest_draw:<8}"
            f"{state.completed_cycles:<7}{state.draws_in_cycle:<5}"
            f"{_digits(state.most_present_digits):<23}"
            f"{_digits(state.missing_digits):<23}"
            f"{row.probability_within(1):>8.2%}  "
            f"{row.probability_within(2):>8.2%}  "
            f"{row.probability_within(3):>8.2%}  "
            f"{row.probability_within(5):>8.2%}  "
            f"{row.expected_remaining_draws:>8.3f}",
            file=stream,
        )


def _print_consensus(
    report: CurrentCoverageReport,
    stream: TextIO,
    *,
    locale: str,
) -> None:
    print(file=stream)
    print(render_digit_consensus(report.consensus, locale=locale), file=stream)


def _print_coverage_hits(
    report: CurrentCoverageReport,
    *,
    summary_path: Path,
    stream: TextIO,
    locale: str,
) -> None:
    signals = report.coverage_hit_ranking
    print(file=stream)
    print(_text("cli.current.coverage_hits_title", locale), file=stream)
    print(
        f"{_text('cli.current.historical_source', locale)}: {summary_path}",
        file=stream,
    )
    print(_text("cli.current.coverage_hits_event", locale), file=stream)
    print(_text("cli.current.coverage_hits_estimate", locale), file=stream)
    print(_text("cli.current.coverage_hits_age_note", locale), file=stream)

    if not signals:
        print(file=stream)
        print(_text("cli.current.coverage_hits_empty", locale), file=stream)
        return

    print(file=stream)
    print(
        f"{_text('cli.current.pos', locale):<5}"
        f"{_text('cli.current.wheel', locale):<12}"
        f"{_text('cli.current.class', locale):<9}"
        f"{_text('cli.current.age', locale):<5}"
        f"{_text('cli.current.most_present', locale):<18}"
        f"{_text('cli.current.missing', locale):<18}"
        f"{_text('cli.current.cases', locale):>7}  "
        f"{_text('cli.current.historical', locale):>10}  "
        f"{_text('cli.current.event_probability', locale):>8}  "
        f"{'Lift95-':>8}  "
        f"{_text('cli.current.within1', locale):>8}  "
        f"{_text('cli.current.estimate95', locale):>11}",
        file=stream,
    )
    print(
        f"{'---':<5}{'----------':<12}{'-------':<9}{'---':<5}"
        f"{'-------------':<18}{'-------------':<18}{'------':>7}  "
        f"{'----------':>10}  {'--------':>8}  {'--------':>8}  "
        f"{'--------':>8}  {'-----------':>11}",
        file=stream,
    )

    for position, signal in enumerate(signals, start=1):
        print(
            f"{position:<5}{signal.wheel:<12}{signal.class_label:<9}"
            f"{signal.draws_in_cycle:<5}{_digits(signal.most_present_digits):<18}"
            f"{_digits(signal.missing_digits):<18}{signal.historical.cases:>7}  "
            f"{signal.historical.success_rate:>10.2%}  "
            f"{signal.current_event_probability:>8.2%}  "
            f"{signal.conservative_excess:>+8.2%}  "
            f"{signal.completion_within_one:>8.2%}  "
            f"{signal.conservative_probability:>11.2%}",
            file=stream,
        )

    winner: CurrentCoverageSignal = signals[0]
    print(file=stream)
    print(
        f"{_text('cli.current.first_signal', locale)}: {winner.wheel}, "
        f"{_text('cli.current.class', locale).lower()} {winner.class_label}; "
        f"{_text('cli.current.at_least', locale)} {winner.historical.threshold} "
        f"{_text('cli.current.among', locale)} {_digits(winner.missing_digits)}; "
        f"{_text('cli.current.most_present', locale).lower()} "
        f"{_digits(winner.most_present_digits)}; "
        f"{_text('cli.current.estimate95', locale)} "
        f"{winner.conservative_probability:.2%}.",
        file=stream,
    )
    print(_text("cli.current.coverage_hits_note", locale), file=stream)


def _format_next_number(
    number: int,
    *,
    top_digits: frozenset[int],
    missing_digits: frozenset[int],
    use_color: bool,
) -> str:
    formatted = f"{number:02d}"
    if not use_color:
        return formatted

    rendered: list[str] = []
    for character in formatted:
        digit = int(character)
        if digit in missing_digits:
            rendered.append(f"{ANSI_MISSING}{character}{ANSI_RESET}")
        elif digit in top_digits:
            rendered.append(f"{ANSI_TOP}{character}{ANSI_RESET}")
        else:
            rendered.append(character)
    return "".join(rendered)


def _print_next_draw(
    report: CurrentCoverageReport,
    stream: TextIO,
    *,
    locale: str,
) -> None:
    if not report.next_draws:
        return

    states = {state.wheel: state for state in report.states}
    use_color = bool(getattr(stream, "isatty", lambda: False)())
    first = report.next_draws[0]
    print(file=stream)
    print(_text("cli.current.next_draw_title", locale), file=stream)
    print(_text("cli.current.next_draw_note", locale), file=stream)
    print(
        f"{_text('cli.current.draw', locale)}: {first.draw_number} "
        f"{_text('cli.current.of', locale)} {first.draw_date}",
        file=stream,
    )
    print(file=stream)

    if use_color:
        print(
            f"{_text('cli.current.digit_legend', locale)}: "
            f"{ANSI_TOP} {_text('cli.current.top', locale)} {ANSI_RESET}  "
            f"{ANSI_MISSING} {_text('cli.current.missing', locale).upper()} {ANSI_RESET}",
            file=stream,
        )
        print(file=stream)

    print(
        f"{_text('cli.current.wheel', locale):<12}"
        f"{_text('cli.current.numbers', locale)}",
        file=stream,
    )
    print("----------  --------------", file=stream)
    for draw in report.next_draws:
        state = states[draw.wheel]
        numbers = " ".join(
            _format_next_number(
                number,
                top_digits=state.most_present_digits,
                missing_digits=state.missing_digits,
                use_color=use_color,
            )
            for number in draw.numbers
        )
        print(f"{draw.wheel:<12}{numbers}", file=stream)


def _print_anomaly_history(
    report: CurrentCoverageReport,
    stream: TextIO,
    *,
    locale: str,
) -> None:
    counts = Counter(event.category for event in report.anomaly_history)
    print(file=stream)
    print(_text("cli.current.anomaly_history_title", locale), file=stream)
    print(
        f"{_text('cli.current.valid_transitions', locale)}: {report.transition_count}",
        file=stream,
    )
    print(
        f"{_text('cli.current.observed_events', locale)}:   {len(report.anomaly_history)}",
        file=stream,
    )
    print(
        f"{_text('cli.current.categories', locale)}:         "
        + ", ".join(
            f"{category}={counts.get(category, 0)}"
            for category in ALL_CATEGORIES
        ),
        file=stream,
    )

    if not report.anomaly_history:
        print(file=stream)
        print(_text("cli.current.no_historical_anomalies", locale), file=stream)
        return

    print(file=stream)
    print(
        f"Cat {_text('cli.current.date', locale):<10} "
        f"{_text('cli.current.draw', locale):<5} "
        f"{_text('cli.current.wheel', locale):<11} "
        f"{_text('cli.current.event_probability_header', locale):>10} "
        f"{_text('cli.current.level', locale):<8}  "
        f"{_text('cli.current.signature', locale)}",
        file=stream,
    )
    print("--- ---------- ----- ----------- ---------- --------  ----------------", file=stream)
    for event in report.anomaly_history:
        print(
            f"{event.category:<3} {event.target_date:<10} {event.target_draw:<5} "
            f"{event.wheel:<11} {event.conditional_probability:>10.6%} "
            f"{event.severity:<8}  {event.signature}",
            file=stream,
        )


def _anomaly_timing(event: AnomalyEvent, report: CurrentCoverageReport) -> str:
    if event.category == "A1":
        return f"{event.target_draw} ({event.target_date})"
    return f"{report.latest_draw} ({report.latest_date})"


def _print_active_anomalies(
    report: CurrentCoverageReport,
    stream: TextIO,
    *,
    locale: str,
) -> None:
    print(file=stream)
    print(
        _text("cli.current.active_anomalies_title", locale).format(
            draw=report.latest_draw,
            date=report.latest_date,
        ),
        file=stream,
    )
    if not report.active_anomalies:
        print(_text("cli.current.no_active_anomalies", locale), file=stream)
        return

    print(file=stream)
    print(
        f"Cat {_text('cli.current.wheel', locale):<11} "
        f"{_text('cli.current.event_probability_header', locale):>10} "
        f"{_text('cli.current.active_since', locale):<25}  "
        f"{_text('cli.current.signature', locale)}",
        file=stream,
    )
    print("--- ----------- ---------- -------------------------  ----------------", file=stream)
    for event in report.active_anomalies:
        print(
            f"{event.category:<3} {event.wheel:<11} "
            f"{event.conditional_probability:>10.6%} "
            f"{_anomaly_timing(event, report):<25}  {event.signature}",
            file=stream,
        )


def render_current_report(
    report: CurrentCoverageReport,
    *,
    database: Path,
    summary_path: Path,
    checkpoint_path: Path | None = None,
    checkpoint_date: str | None = None,
    cutoff_date: str | None = None,
    cutoff_draw_number: int | None = None,
    locale: str = CANONICAL_LOCALE,
    stream: TextIO = sys.stdout,
) -> None:
    """Render a structured report while keeping presentation out of application."""

    print(f"Database: {database}", file=stream)
    checkpoint_label = _text("cli.current.checkpoint_label", locale)
    if checkpoint_path is None:
        print(
            f"{checkpoint_label}: {_text('cli.current.disabled', locale)}",
            file=stream,
        )
    else:
        print(
            f"{checkpoint_label}: {checkpoint_path} "
            f"({_text('cli.current.until', locale)} {checkpoint_date})",
            file=stream,
        )

    if cutoff_date is not None:
        print(
            f"{_text('cli.current.time_limit', locale)}: {cutoff_date} "
            f"({_text('cli.current.inclusive', locale)})",
            file=stream,
        )
    if cutoff_draw_number is not None:
        print(
            f"{_text('cli.current.draw_limit', locale)}: {cutoff_draw_number} "
            f"({_text('cli.current.inclusive', locale)})",
            file=stream,
        )

    print(
        f"{_text('cli.current.latest_draw', locale)}: {report.latest_draw} "
        f"{_text('cli.current.of', locale)} {report.latest_date}",
        file=stream,
    )
    print(file=stream)
    _print_markov(report, stream, locale=locale)
    _print_consensus(report, stream, locale=locale)
    _print_coverage_hits(
        report,
        summary_path=summary_path,
        stream=stream,
        locale=locale,
    )
    _print_next_draw(report, stream, locale=locale)
    _print_anomaly_history(report, stream, locale=locale)
    _print_active_anomalies(report, stream, locale=locale)
