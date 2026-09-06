from __future__ import annotations

import io
import unittest
from pathlib import Path

from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.domain.draws import DrawSnapshot
from lotto_digit_coverage.interfaces.cli.current import render_current_report
from strategies.current_coverage_signal import HistoricalCoverageClass


class CurrentApplicationTests(unittest.TestCase):
    @staticmethod
    def draws(next_numbers=(66, 67, 68, 69, 70)):
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
                    numbers=tuple(next_numbers),
                ),
            )
        return by_wheel

    @staticmethod
    def historical_classes():
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

    def test_report_exposes_structured_current_vertical(self) -> None:
        report = build_current_coverage_report(
            all_draws_by_wheel=self.draws(),
            historical_classes=self.historical_classes(),
            cutoff_draw_number=2,
        )

        self.assertEqual((report.latest_draw, report.latest_date), (2, "2026-01-03"))
        self.assertEqual(tuple(row.state.wheel for row in report.markov_ranking), ("Bari", "Roma"))
        self.assertEqual(len(report.coverage_hit_ranking), 2)
        self.assertTrue(report.consensus)
        self.assertEqual(tuple(draw.draw_number for draw in report.next_draws), (3, 3))
        self.assertEqual(tuple(state.draws_in_cycle for state in report.states), (1, 1))
        self.assertEqual(report.states[0].missing_digits, frozenset({0, 6, 7, 8, 9}))

    def test_later_draw_is_validation_only(self) -> None:
        first = build_current_coverage_report(
            all_draws_by_wheel=self.draws((66, 67, 68, 69, 70)),
            historical_classes=self.historical_classes(),
            cutoff_draw_number=2,
        )
        second = build_current_coverage_report(
            all_draws_by_wheel=self.draws((71, 72, 73, 74, 75)),
            historical_classes=self.historical_classes(),
            cutoff_draw_number=2,
        )

        self.assertEqual(first.states, second.states)
        self.assertEqual(first.markov_ranking, second.markov_ranking)
        self.assertEqual(first.coverage_hit_ranking, second.coverage_hit_ranking)
        self.assertNotEqual(first.next_draws, second.next_draws)

    def test_cli_renderer_defaults_to_canonical_english(self) -> None:
        report = build_current_coverage_report(
            all_draws_by_wheel=self.draws(),
            historical_classes=self.historical_classes(),
            cutoff_draw_number=2,
        )
        stream = io.StringIO()

        render_current_report(
            report,
            database=Path("fixture.sqlite3"),
            summary_path=Path("fixture.csv"),
            cutoff_draw_number=2,
            stream=stream,
        )

        rendered = stream.getvalue()
        self.assertIn("COVERAGE MARKOV METER", rendered)
        self.assertIn("CROSS-WHEEL DIGIT CONSENSUS", rendered)
        self.assertIn("Latest draw: 2 of 2026-01-03", rendered)
        self.assertNotIn("TUTTE", rendered)

    def test_english_and_italian_render_same_structured_report(self) -> None:
        report = build_current_coverage_report(
            all_draws_by_wheel=self.draws(),
            historical_classes=self.historical_classes(),
            cutoff_draw_number=2,
        )
        outputs = {}
        for locale in ("en", "it"):
            stream = io.StringIO()
            render_current_report(
                report,
                database=Path("fixture.sqlite3"),
                summary_path=Path("fixture.csv"),
                cutoff_draw_number=2,
                locale=locale,
                stream=stream,
            )
            outputs[locale] = stream.getvalue()

        self.assertIn("Wheel", outputs["en"])
        self.assertIn("Ruota", outputs["it"])
        self.assertIn("Latest draw: 2 of 2026-01-03", outputs["en"])
        self.assertIn("Ultima estrazione: 2 del 2026-01-03", outputs["it"])
        for rendered in outputs.values():
            self.assertIn("Bari", rendered)
            self.assertIn("Roma", rendered)
            self.assertIn("6.50%", rendered)
            self.assertIn("3.025", rendered)
            self.assertIn("35.28%", rendered)
            self.assertIn("2 (2026-01-03)", rendered)

        self.assertEqual(report.latest_draw, 2)
        self.assertEqual(tuple(row.state.wheel for row in report.markov_ranking), ("Bari", "Roma"))

    def test_mutually_exclusive_cutoffs_are_rejected_by_application_api(self) -> None:
        with self.assertRaises(ValueError):
            build_current_coverage_report(
                all_draws_by_wheel=self.draws(),
                historical_classes=self.historical_classes(),
                cutoff_date=__import__("datetime").date(2026, 1, 3),
                cutoff_draw_number=2,
            )


if __name__ == "__main__":
    unittest.main()
