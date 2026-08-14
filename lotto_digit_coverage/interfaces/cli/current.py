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


ANSI_RESET = "\033[0m"
ANSI_TOP = "\033[1;30;46m"
ANSI_MISSING = "\033[1;30;43m"


def _digits(digits: frozenset[int]) -> str:
    return "{" + ",".join(str(digit) for digit in sorted(digits)) + "}"


def _print_markov(report: CurrentCoverageReport, stream: TextIO) -> None:
    print("===== MISURATORE MARKOV DELLA COPERTURA =====", file=stream)
    print("Stato: cifre ancora mancanti nel ciclo naturale corrente.", file=stream)
    print(
        "Classifica: attesa residua crescente; non rappresenta un vantaggio sul gioco.",
        file=stream,
    )
    print(
        "Più presenti: cifre con il massimo numero di occorrenze nel ciclo corrente.",
        file=stream,
    )
    print(file=stream)
    print(
        f"{'Pos':<5}{'Ruota':<12}{'Ultimo':<8}{'Cicli':<7}{'Età':<5}"
        f"{'Più presenti':<23}{'Mancanti':<23}"
        "Entro 1  Entro 2  Entro 3  Entro 5  Attesa",
        file=stream,
    )
    print(
        f"{'---':<5}{'----------':<12}{'------':<8}{'-----':<7}{'---':<5}"
        f"{'-------------':<23}{'-------------':<23}"
        "-------  -------  -------  -------  ------",
        file=stream,
    )

    for position, row in enumerate(report.markov_ranking, start=1):
        state = row.state
        print(
            f"{position:<5}{state.wheel:<12}{state.latest_draw:<8}"
            f"{state.completed_cycles:<7}{state.draws_in_cycle:<5}"
            f"{_digits(state.most_present_digits):<23}"
            f"{_digits(state.missing_digits):<23}"
            f"{row.probability_within(1):>6.2%}  "
            f"{row.probability_within(2):>6.2%}  "
            f"{row.probability_within(3):>6.2%}  "
            f"{row.probability_within(5):>6.2%}  "
            f"{row.expected_remaining_draws:>6.3f}",
            file=stream,
        )


def _print_consensus(report: CurrentCoverageReport, stream: TextIO) -> None:
    print(file=stream)
    print(render_digit_consensus(report.consensus), file=stream)


def _print_coverage_hits(
    report: CurrentCoverageReport,
    *,
    summary_path: Path,
    stream: TextIO,
) -> None:
    signals = report.coverage_hit_ranking
    print(file=stream)
    print("===== SEGNALE OPERATIVO COVERAGE-HITS =====", file=stream)
    print(f"Fonte storica: {summary_path}", file=stream)
    print(
        "Evento: almeno max(1, N-1) delle N cifre mancanti alla prossima estrazione.",
        file=stream,
    )
    print(
        "Stima95-: probabilità corrente corretta con il limite inferiore Wilson "
        "dello scarto storico.",
        file=stream,
    )
    print("Età è descrittiva e non incrementa la probabilità.", file=stream)

    if not signals:
        print(file=stream)
        print("Nessuna classe corrente presente nel riepilogo storico.", file=stream)
        return

    print(file=stream)
    print(
        f"{'Pos':<5}{'Ruota':<12}{'Classe':<9}{'Età':<5}"
        f"{'Più presenti':<18}{'Mancanti':<18}{'Casi':>7}  "
        f"{'Storico':>8}  {'P evento':>8}  {'Lift95-':>8}  "
        f"{'Entro 1':>8}  {'Stima95-':>8}",
        file=stream,
    )
    print(
        f"{'---':<5}{'----------':<12}{'-------':<9}{'---':<5}"
        f"{'-------------':<18}{'-------------':<18}{'------':>7}  "
        f"{'--------':>8}  {'--------':>8}  {'--------':>8}  "
        f"{'--------':>8}  {'--------':>8}",
        file=stream,
    )

    for position, signal in enumerate(signals, start=1):
        print(
            f"{position:<5}{signal.wheel:<12}{signal.class_label:<9}"
            f"{signal.draws_in_cycle:<5}{_digits(signal.most_present_digits):<18}"
            f"{_digits(signal.missing_digits):<18}{signal.historical.cases:>7}  "
            f"{signal.historical.success_rate:>8.2%}  "
            f"{signal.current_event_probability:>8.2%}  "
            f"{signal.conservative_excess:>+8.2%}  "
            f"{signal.completion_within_one:>8.2%}  "
            f"{signal.conservative_probability:>8.2%}",
            file=stream,
        )

    winner: CurrentCoverageSignal = signals[0]
    print(file=stream)
    print(
        f"Primo segnale: {winner.wheel}, classe {winner.class_label}; "
        f"almeno {winner.historical.threshold} tra {_digits(winner.missing_digits)}; "
        f"più presenti {_digits(winner.most_present_digits)}; "
        f"Stima95- {winner.conservative_probability:.2%}.",
        file=stream,
    )
    print(
        "Nota: un lift negativo non indica un vantaggio storico; la classifica "
        "descrive il segnale operativo più robusto disponibile.",
        file=stream,
    )


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


def _print_next_draw(report: CurrentCoverageReport, stream: TextIO) -> None:
    if not report.next_draws:
        return

    states = {state.wheel: state for state in report.states}
    use_color = bool(getattr(stream, "isatty", lambda: False)())
    first = report.next_draws[0]
    print(file=stream)
    print("===== ESTRAZIONE SUCCESSIVA NEL DATABASE =====", file=stream)
    print("Non utilizzata nei calcoli del quadro storico.", file=stream)
    print(f"Estrazione: {first.draw_number} del {first.draw_date}", file=stream)
    print(file=stream)

    if use_color:
        print(
            "Legenda cifre: "
            f"{ANSI_TOP} TOP {ANSI_RESET}  {ANSI_MISSING} MANCANTI {ANSI_RESET}",
            file=stream,
        )
        print(file=stream)

    print("Ruota       Numeri", file=stream)
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


def _print_anomaly_history(report: CurrentCoverageReport, stream: TextIO) -> None:
    counts = Counter(event.category for event in report.anomaly_history)
    print(file=stream)
    print("===== ANOMALIE A1-A4 NEL DATABASE =====", file=stream)
    print(f"Transizioni valide: {report.transition_count}", file=stream)
    print(f"Eventi osservati:   {len(report.anomaly_history)}", file=stream)
    print(
        "Categorie:         "
        + ", ".join(
            f"{category}={counts.get(category, 0)}"
            for category in ALL_CATEGORIES
        ),
        file=stream,
    )

    if not report.anomaly_history:
        print(file=stream)
        print("Nessuna anomalia storica rilevata.", file=stream)
        return

    print(file=stream)
    print("Cat Data       Estr. Ruota       P(evento)  Livello   Firma", file=stream)
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


def _print_active_anomalies(report: CurrentCoverageReport, stream: TextIO) -> None:
    print(file=stream)
    print(
        f"===== ANOMALIE ATTIVE ALLA {report.latest_draw} ({report.latest_date}) =====",
        file=stream,
    )
    if not report.active_anomalies:
        print("Nessuna anomalia A1-A4 attiva.", file=stream)
        return

    print(file=stream)
    print("Cat Ruota       P(evento)  Attiva/osservata da       Firma", file=stream)
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
    stream: TextIO = sys.stdout,
) -> None:
    """Render a structured report while keeping presentation out of application."""

    print(f"Database: {database}", file=stream)
    if checkpoint_path is None:
        print("Checkpoint storico: disabilitato", file=stream)
    else:
        print(
            f"Checkpoint storico: {checkpoint_path} (fino al {checkpoint_date})",
            file=stream,
        )

    if cutoff_date is not None:
        print(f"Limite temporale: {cutoff_date} (inclusivo)", file=stream)
    if cutoff_draw_number is not None:
        print(f"Limite estrazione: {cutoff_draw_number} (inclusivo)", file=stream)

    print(
        f"Ultima estrazione: {report.latest_draw} del {report.latest_date}",
        file=stream,
    )
    print(file=stream)
    _print_markov(report, stream)
    _print_consensus(report, stream)
    _print_coverage_hits(report, summary_path=summary_path, stream=stream)
    _print_next_draw(report, stream)
    _print_anomaly_history(report, stream)
    _print_active_anomalies(report, stream)
