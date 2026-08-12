"""Optional desktop launcher for the Svelte research interface."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path

from lotto_digit_coverage.interfaces.gui.bridge import LottoGuiApi


ROOT = Path(__file__).resolve().parents[3]
GUI_ENTRYPOINT = Path("gui/dist/index.html")


def print_usage() -> None:
    print("Uso: ./lotto.py gui")
    print()
    print("Avvia la GUI locale/offline sopra il core Python condiviso.")
    print("Richiede il frontend compilato e requirements-gui.txt installato.")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        if arguments == ["--help"]:
            print_usage()
            return 0
        print(
            "ERRORE: il comando gui non accetta argomenti.",
            file=sys.stderr,
        )
        return 2

    entrypoint = ROOT / GUI_ENTRYPOINT
    if not entrypoint.is_file():
        print(
            "ERRORE: frontend GUI non compilato. "
            "Eseguire 'cd gui && npm install && npm run build'.",
            file=sys.stderr,
        )
        return 1

    try:
        import webview
    except ImportError:
        print(
            "ERRORE: pywebview non installato. "
            "Installare le dipendenze GUI da requirements-gui.txt.",
            file=sys.stderr,
        )
        return 1

    previous = Path.cwd()
    os.chdir(ROOT)
    try:
        webview.create_window(
            "Lotto Digit Coverage Dynamics",
            str(GUI_ENTRYPOINT),
            js_api=LottoGuiApi(ROOT),
            width=1440,
            height=900,
            min_size=(960, 640),
        )
        webview.start()
    finally:
        os.chdir(previous)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
