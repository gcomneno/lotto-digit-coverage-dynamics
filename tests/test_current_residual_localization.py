from __future__ import annotations

import io
import unittest
from dataclasses import replace
from pathlib import Path

from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.application.historical_anomalies import AnomalyEvent
from lotto_digit_coverage.domain.draws import DrawSnapshot
from lotto_digit_coverage.interfaces.cli.current import render_current_report
from strategies.current_coverage_signal import HistoricalCoverageClass


class CurrentResidualLocalizationTests(unittest.TestCase):
    @staticmethod
    def _draws():
        by_wheel = {}
        for wheel, order in (("Bari", 1), ("Roma", 8)):
            by_wheel[wheel] = (
                DrawSnapshot(
                    draw_number=1,
                    draw_date="2026-01-02",
                    wheel=wheel,
                    wheel_order=order,
                    numbers=(1, 23, 45, 67, 89),
                ),
                DrawSnapshot(
                    draw_number=2,
                    draw_date="2026-01-03",
                    wheel=wheel,
                    wheel_order=order,
                    numbers=(11, 22, 33, 44, 55),
                ),
                DrawSnapshot(
                    draw_number=3,
                    draw_date="2026-01-04",
                    wheel=wheel,
                    wheel_order=order,
                    numbers=(66, 67, 68, 69, 70),
                ),
            )
        return by_wheel

    @staticmethod
    def _historical_classes():
        return {
            (5, 5): HistoricalCoverageClass(
                most_present_count=5,
                missing_count=5,
                threshold=4,
                cases=1000,
                obtained=100,
                expected_probability=0.10,
                evidence_level="3",
            )
        }

    @staticmethod
    def _anomaly() -> AnomalyEvent:
        return AnomalyEvent(
            category="A1",
            signature="A1:test",
            recurrence_key="test",
            wheel="Bari",
            wheel_order=1,
            cycle_number=1,
            event_index=1,
            target_draw=2,
            target_date="2026-01-03",
            source_state="{0,6,7,8,9}",
            target_state="{0,6,7,8,9}",
            horizon=1,
            conditional_probability=0.005,
            atom_probability=None,
            previous_conditional_probability=None,
            pair_probability=None,
            surprisal=2.30103,
            severity="rare",
            right_censored=True,
            previous_target_draw=None,
            previous_target_date=None,
            recurrence_gap=None,
        )

    def _report(self):
        report = build_current_coverage_report(
            all_draws_by_wheel=self._draws(),
            historical_classes=self._historical_classes(),
            cutoff_draw_number=2,
        )
        event = self._anomaly()
        return replace(
            report,
            anomaly_history=(event,),
            active_anomalies=(event,),
            transition_count=7,
        )

    @staticmethod
    def _render(report, locale: str) -> str:
        stream = io.StringIO()
        render_current_report(
            report,
            database=Path("fixture.sqlite3"),
            summary_path=Path("fixture.csv"),
            cutoff_draw_number=2,
            locale=locale,
            stream=stream,
        )
        return stream.getvalue()

    def test_residual_sections_are_localized_without_semantic_changes(self) -> None:
        report = self._report()
        english = self._render(report, "en")
        italian = self._render(report, "it")

        self.assertIn("COVERAGE-HITS OPERATIONAL SIGNAL", english)
        self.assertIn("SEGNALE OPERATIVO COVERAGE-HITS", italian)
        self.assertIn("NEXT DRAW IN DATABASE", english)
        self.assertIn("ESTRAZIONE SUCCESSIVA NEL DATABASE", italian)
        self.assertIn("A1-A4 ANOMALIES IN DATABASE", english)
        self.assertIn("ANOMALIE A1-A4 NEL DATABASE", italian)
        self.assertIn("ACTIVE ANOMALIES AT 2 (2026-01-03)", english)
        self.assertIn("ANOMALIE ATTIVE ALLA 2 (2026-01-03)", italian)

        semantic_tokens = (
            "Bari",
            "Roma",
            "5,5",
            "1000",
            "10.00%",
            "36.99%",
            "-1.71%",
            "6.50%",
            "35.28%",
            "66 67 68 69 70",
            "A1",
            "A1:test",
            "0.500000%",
            "2 (2026-01-03)",
            "A1=1, A2=0, A3=0, A4=0",
        )
        for token in semantic_tokens:
            self.assertIn(token, english)
            self.assertIn(token, italian)

        self.assertEqual(
            tuple(signal.wheel for signal in report.coverage_hit_ranking),
            ("Bari", "Roma"),
        )
        self.assertEqual(
            tuple(draw.draw_number for draw in report.next_draws),
            (3, 3),
        )
        self.assertEqual(report.anomaly_history, report.active_anomalies)
        self.assertEqual(report.transition_count, 7)

    def test_empty_anomaly_messages_follow_locale_only(self) -> None:
        report = build_current_coverage_report(
            all_draws_by_wheel=self._draws(),
            historical_classes=self._historical_classes(),
            cutoff_draw_number=2,
        )
        english = self._render(report, "en")
        italian = self._render(report, "it")

        self.assertIn("No historical anomaly detected.", english)
        self.assertIn("Nessuna anomalia storica rilevata.", italian)
        self.assertIn("No A1-A4 anomaly is active.", english)
        self.assertIn("Nessuna anomalia A1-A4 attiva.", italian)
        self.assertEqual(report.anomaly_history, ())
        self.assertEqual(report.active_anomalies, ())


if __name__ == "__main__":
    unittest.main()
