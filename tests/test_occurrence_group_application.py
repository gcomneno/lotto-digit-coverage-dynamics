from __future__ import annotations

import io
import unittest
from pathlib import Path

from lotto_digit_coverage.application.occurrence_groups import (
    build_occurrence_group_report,
)
from lotto_digit_coverage.interfaces.cli.occurrence_groups import (
    render_occurrence_group_report,
)


WHEELS = ("Bari", "Roma")


class OccurrenceGroupApplicationTests(unittest.TestCase):
    @staticmethod
    def draws():
        return {
            (120, "2026-07-31"): {
                "Bari": (1, 12, 23, 34, 46),
                "Roma": (1, 12, 23, 34, 9),
            },
            (121, "2026-08-02"): {
                "Bari": (1, 12, 23, 56, 67),
                "Roma": (50, 60, 70, 80, 90),
            },
            (122, "2026-08-04"): {
                "Bari": (1, 12, 23, 34, 9),
                "Roma": (50, 60, 70, 80, 90),
            },
        }

    def test_reference_is_separate_and_counts_use_only_analysis_draws(self) -> None:
        report = build_occurrence_group_report(
            draws=self.draws(),
            expected_wheels=WHEELS,
            group_size=2,
        )

        self.assertEqual(
            (report.reference_draw_number, report.reference_draw_date),
            (122, "2026-08-04"),
        )
        self.assertEqual(tuple(group.size for group in report.groups), (2,))

        group = report.groups[0]
        self.assertEqual(group.reference_draw.draw_number, 122)
        self.assertEqual(
            tuple(draw.draw_number for draw in group.draws),
            (121, 120),
        )

        bari = group.wheels[0]
        self.assertEqual(bari.reference_numbers, (1, 12, 23, 34, 9))
        self.assertEqual(bari.occurrence_counts, (2, 2, 2, 1, 0))

    def test_explicit_cutoff_is_reference_and_not_counted(self) -> None:
        report = build_occurrence_group_report(
            draws=self.draws(),
            expected_wheels=WHEELS,
            group_size=2,
            requested_draw_number=121,
        )

        self.assertEqual(report.reference_kind, "esplicito")
        self.assertEqual(report.reference_draw_number, 121)
        self.assertEqual(
            tuple(group.reference_draw_number for group in report.groups),
            (121,),
        )
        self.assertEqual(
            tuple(draw.draw_number for draw in report.groups[0].draws),
            (120,),
        )
        self.assertEqual(
            report.groups[0].wheels[0].occurrence_counts,
            (1, 1, 1, 0, 0),
        )

    def test_same_number_on_other_wheel_does_not_count(self) -> None:
        draws = self.draws()
        draws[(121, "2026-08-02")]["Bari"] = (56, 57, 58, 59, 60)
        draws[(121, "2026-08-02")]["Roma"] = (1, 12, 23, 34, 9)

        report = build_occurrence_group_report(
            draws=draws,
            expected_wheels=WHEELS,
            group_size=2,
        )

        bari = report.groups[0].wheels[0]
        self.assertEqual(bari.occurrence_counts, (1, 1, 1, 1, 0))

    def test_ambiguous_draw_number_is_rejected(self) -> None:
        draws = self.draws()
        draws[(122, "2025-08-04")] = draws[(122, "2026-08-04")]

        with self.assertRaisesRegex(ValueError, "ambiguo"):
            build_occurrence_group_report(
                draws=draws,
                expected_wheels=WHEELS,
                group_size=2,
                requested_draw_number=122,
            )

    def test_renderer_marks_reference_and_counted_draws(self) -> None:
        report = build_occurrence_group_report(
            draws=self.draws(),
            expected_wheels=WHEELS,
            group_size=2,
        )
        stream = io.StringIO()

        render_occurrence_group_report(
            report,
            database=Path("fixture.sqlite3"),
            draw_count=3,
            first_draw=120,
            last_draw=122,
            expected_wheels=WHEELS,
            stream=stream,
        )

        output = stream.getvalue()
        self.assertEqual(report.groups[0].wheels[0].reference_numbers[0], 1)
        self.assertIn("01", output)
        self.assertIn("analisi 121–120 (2 estrazioni conteggiate)", output)
        self.assertIn("Rif.", output)
        self.assertIn("Conta", output)
        self.assertIn("esclusa dai conteggi", output)


if __name__ == "__main__":
    unittest.main()
