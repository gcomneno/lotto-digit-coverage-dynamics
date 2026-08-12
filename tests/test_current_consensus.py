from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import analyze_current_consensus
from strategies.coverage_completion import CurrentCoverageState


class CurrentConsensusTests(unittest.TestCase):
    def test_wrapper_removes_tutte_and_appends_consensus(self) -> None:
        state = CurrentCoverageState(
            wheel="Milano",
            wheel_order=1,
            latest_draw=128,
            latest_date="2026-08-11",
            completed_cycles=10,
            draws_in_cycle=2,
            covered_digits=frozenset({0, 1, 2, 3, 4, 5, 6, 7, 9}),
            missing_digits=frozenset({8}),
            synchronized=True,
            most_present_digits=frozenset({1}),
        )
        output = io.StringIO()

        def legacy_summary(states) -> None:
            self.assertEqual(states, (state,))
            print("===== MISURATORE MARKOV DELLA COPERTURA =====")
            print("1    Milano")
            print("*    TUTTE test Numeri={88}")
            print("* TUTTE: vecchia legenda")

        with patch.object(
            analyze_current_consensus,
            "_ORIGINAL_PRINT_MARKOV_SUMMARY",
            legacy_summary,
        ):
            with redirect_stdout(output):
                analyze_current_consensus.print_markov_summary_with_consensus(
                    (state,)
                )

        rendered = output.getvalue()

        self.assertIn("MISURATORE MARKOV", rendered)
        self.assertIn("1    Milano", rendered)
        self.assertIn("CONSENSUS TRASVERSALE", rendered)
        self.assertNotIn("TUTTE", rendered)
        self.assertNotIn("Numeri={88}", rendered)


if __name__ == "__main__":
    unittest.main()
