from __future__ import annotations

import io
import unittest
from pathlib import Path

from lotto_digit_coverage.application.current import CurrentCoverageReport
from lotto_digit_coverage.interfaces.cli.consensus import render_digit_consensus
from lotto_digit_coverage.interfaces.cli.current import render_current_report
from strategies.coverage_consensus import DigitConsensus


class CliConsensusTests(unittest.TestCase):
    def test_current_report_uses_shared_consensus_renderer(self) -> None:
        rows = (
            DigitConsensus(
                digit=9,
                missing_wheels=("Firenze", "Milano", "Roma"),
                top_wheels=(),
            ),
        )
        report = CurrentCoverageReport(
            latest_draw=129,
            latest_date="2026-08-13",
            states=(),
            markov_ranking=(),
            coverage_hit_ranking=(),
            consensus=rows,
            anomaly_history=(),
            active_anomalies=(),
            transition_count=0,
            next_draws=(),
        )
        stream = io.StringIO()

        render_current_report(
            report,
            database=Path("data/test.sqlite3"),
            summary_path=Path("artifacts/test.csv"),
            locale="it",
            stream=stream,
        )

        rendered = stream.getvalue()
        self.assertIn(render_digit_consensus(rows, locale="it"), rendered)
        self.assertIn("Ruote in deficit", rendered)
        self.assertIn("Ruote in predominanza", rendered)
        self.assertNotIn("Ruote mancanti", rendered)
        self.assertNotIn("Ruote TOP", rendered)

    def test_consensus_defaults_to_english_and_preserves_values(self) -> None:
        rows = (
            DigitConsensus(
                digit=9,
                missing_wheels=("Firenze", "Milano", "Roma"),
                top_wheels=("Bari",),
            ),
        )
        english = render_digit_consensus(rows)
        italian = render_digit_consensus(rows, locale="it")

        self.assertIn("CROSS-WHEEL DIGIT CONSENSUS", english)
        self.assertIn("CONSENSUS TRASVERSALE DELLE CIFRE", italian)
        for rendered in (english, italian):
            self.assertIn("9", rendered)
            self.assertIn("Firenze,Milano,Roma", rendered)
            self.assertIn("Bari", rendered)


if __name__ == "__main__":
    unittest.main()
