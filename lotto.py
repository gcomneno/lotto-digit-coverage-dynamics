#!/usr/bin/env python3

"""Porta di ingresso unica ai CLI del laboratorio Lotto."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Tool:
    command: str
    script: str
    category: str
    description: str
    aliases: tuple[str, ...] = ()


TOOLS = (
    Tool(
        "current",
        "analyze_current_coverage.py",
        "Uso corrente",
        "Classifica Markov, convergenza trasversale e anomalie attive.",
        ("now",),
    ),
    Tool(
        "update",
        "update_lotto_database.py",
        "Uso corrente",
        "Aggiorna e verifica il database annuale corrente.",
    ),
    Tool(
        "db",
        "view_lotto_database.sh",
        "Uso corrente",
        "Mostra il contenuto del database Lotto.",
        ("view",),
    ),
    Tool(
        "anomalies",
        "analyze_coverage_anomalies.py",
        "Analisi storiche",
        "Rileva e riepiloga le anomalie A1–A4.",
    ),
    Tool(
        "completion",
        "analyze_coverage_completion.py",
        "Analisi storiche",
        "Analizza le chiusure dei cicli di copertura.",
    ),
    Tool(
        "residuals",
        "analyze_coverage_markov_residuals.py",
        "Analisi storiche",
        "Confronta distribuzioni residue teoriche e osservate.",
    ),
    Tool(
        "validation",
        "analyze_coverage_markov_validation.py",
        "Analisi storiche",
        "Valida empiricamente le probabilità del modello Markov.",
    ),
    Tool(
        "digit-coverage",
        "analyze_digit_coverage.py",
        "Analisi storiche",
        "Analizza la copertura delle cifre per finestra.",
        ("digits",),
    ),
    Tool(
        "return-times",
        "analyze_digit_return_times.py",
        "Analisi storiche",
        "Analizza i tempi di ritorno delle cifre.",
        ("returns",),
    ),
    Tool(
        "cycles",
        "analyze_historical_cycle_distribution.py",
        "Analisi storiche",
        "Confronta la durata storica dei cicli con la teoria.",
        ("cycle-distribution",),
    ),
    Tool(
        "symmetry-history",
        "analyze_historical_symmetry_classes.py",
        "Analisi storiche",
        "Analizza le classi strutturali osservate storicamente.",
        ("symmetry",),
    ),
    Tool(
        "atlas",
        "generate_state_atlas.py",
        "Teoria e artefatti",
        "Genera l’atlante completo dei 1.024 stati.",
    ),
    Tool(
        "structure",
        "generate_structural_analysis.py",
        "Teoria e artefatti",
        "Genera l’analisi strutturale e delle simmetrie.",
    ),
    Tool(
        "kernel",
        "verify_transition_kernel.py",
        "Teoria e artefatti",
        "Verifica indipendentemente il kernel di transizione.",
    ),
    Tool(
        "import",
        "import_lotto.py",
        "Gestione dati",
        "Importa un archivio annuale nel database SQLite.",
    ),
)


BY_COMMAND = {
    name: tool
    for tool in TOOLS
    for name in (tool.command, *tool.aliases)
}


def print_usage() -> None:
    print("Uso:")
    print("  ./lotto.py list")
    print("  ./lotto.py <comando> [argomenti del tool]")
    print("  ./lotto.py help <comando>")
    print()
    print("Esempi:")
    print("  ./lotto.py current")
    print("  ./lotto.py current --to-num 119")
    print("  ./lotto.py update")
    print("  ./lotto.py anomalies --help")
    print()
    print("Usa './lotto.py list' per vedere tutti i comandi.")


def print_tools() -> None:
    categories: list[str] = []

    for tool in TOOLS:
        if tool.category not in categories:
            categories.append(tool.category)

    print(f"CLI disponibili: {len(TOOLS)}")

    for category in categories:
        print()
        print(category)
        print("-" * len(category))

        for tool in TOOLS:
            if tool.category != category:
                continue

            aliases = (
                f"  alias: {', '.join(tool.aliases)}"
                if tool.aliases
                else ""
            )

            print(
                f"{tool.command:<18} "
                f"{tool.description}"
            )
            print(
                f"{'':18} "
                f"→ {tool.script}{aliases}"
            )


def command_line(
    tool: Tool,
    forwarded_arguments: Sequence[str],
) -> list[str]:
    script = ROOT / tool.script

    if not script.is_file():
        raise FileNotFoundError(
            f"Tool non trovato: {script}"
        )

    if script.suffix == ".py":
        runner = [sys.executable, str(script)]
    else:
        runner = [str(script)]

    return [*runner, *forwarded_arguments]


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(
        sys.argv[1:]
        if argv is None
        else argv
    )

    if not arguments:
        print_usage()
        return 0

    first = arguments.pop(0)

    if first in {"-h", "--help"}:
        print_usage()
        return 0

    if first in {"list", "tools"}:
        print_tools()
        return 0

    if first == "help":
        if not arguments:
            print_usage()
            return 0

        first = arguments.pop(0)
        arguments.insert(0, "--help")

    tool = BY_COMMAND.get(first)

    if tool is None:
        print(
            f"ERRORE: comando sconosciuto: {first}",
            file=sys.stderr,
        )
        print(
            "Usa './lotto.py list' per vedere "
            "i comandi disponibili.",
            file=sys.stderr,
        )
        return 2

    try:
        completed = subprocess.run(
            command_line(tool, arguments),
            cwd=ROOT,
            check=False,
        )
    except FileNotFoundError as error:
        print(f"ERRORE: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
