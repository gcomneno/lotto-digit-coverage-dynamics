from __future__ import annotations

import json
import unittest

from lotto_digit_coverage.application.current import build_current_coverage_report
from lotto_digit_coverage.application.occurrence_groups import (
    build_occurrence_group_report,
)
from lotto_digit_coverage.application.reporting import (
    current_report_to_dict,
    dumps_current_report,
    dumps_occurrence_group_report,
    occurrence_group_report_to_dict,
)
from lotto_digit_coverage.domain.draws import DrawSnapshot
from strategies.current_coverage_signal import HistoricalCoverageClass


class ApplicationReportingTests(unittest.TestCase):
    @staticmethod
    def current_report():
        draws = {}
        for wheel, order in (("Bari", 1), ("Roma", 8)):
            draws[wheel] = (
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

        historical = {
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
        return build_current_coverage_report(
            all_draws_by_wheel=draws,
            historical_classes=historical,
            cutoff_draw_number=2,
        )

    @staticmethod
    def occurrence_report():
        draws = {
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
        return build_occurrence_group_report(
            draws=draws,
            expected_wheels=("Bari", "Roma"),
            group_size=2,
        )

    def test_current_contract_is_explicit_versioned_and_raw(self) -> None:
        payload = current_report_to_dict(self.current_report())

        self.assertEqual(payload["schema"], "lotto.current")
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["number_representation"]["display_width"], 2)
        self.assertEqual(payload["target"], {
            "draw_number": 2,
            "draw_date": "2026-01-03",
        })
        self.assertIsInstance(
            payload["markov_ranking"][0]["expected_remaining_draws"],
            float,
        )
        self.assertIsInstance(
            payload["coverage_hit_ranking"][0]["conservative_probability"],
            float,
        )
        self.assertEqual(
            payload["next_draw_validation"][0]["numbers"][0],
            66,
        )

    def test_occurrence_contract_separates_reference_from_analysis(self) -> None:
        payload = occurrence_group_report_to_dict(self.occurrence_report())

        self.assertEqual(payload["schema"], "lotto.occurrence-groups")
        self.assertEqual(payload["schema_version"], 2)
        group = payload["groups"][0]
        self.assertEqual(group["reference"]["draw_number"], 122)
        self.assertEqual(
            [draw["draw_number"] for draw in group["draws"]],
            [121, 120],
        )
        self.assertEqual(group["actual_size"], 2)
        bari = group["wheels"][0]
        self.assertEqual(bari["reference_numbers"], [1, 12, 23, 34, 9])
        self.assertEqual(bari["occurrence_counts"], [2, 2, 2, 1, 0])
        self.assertEqual(payload["number_representation"]["display_width"], 2)

    def test_json_is_deterministic_and_contains_no_terminal_sequences(self) -> None:
        current = self.current_report()
        occurrence = self.occurrence_report()

        current_first = dumps_current_report(current)
        current_second = dumps_current_report(current)
        occurrence_first = dumps_occurrence_group_report(occurrence)
        occurrence_second = dumps_occurrence_group_report(occurrence)

        self.assertEqual(current_first, current_second)
        self.assertEqual(occurrence_first, occurrence_second)
        self.assertTrue(current_first.endswith("\n"))
        self.assertNotIn("\x1b[", current_first)
        self.assertNotIn("\x1b[", occurrence_first)
        self.assertEqual(json.loads(current_first)["schema_version"], 1)
        self.assertEqual(json.loads(occurrence_first)["schema_version"], 2)

    def test_digit_sets_are_sorted_json_arrays_not_display_strings(self) -> None:
        payload = current_report_to_dict(self.current_report())
        state = payload["states"][0]

        self.assertIsInstance(state["missing_digits"], list)
        self.assertEqual(state["missing_digits"], sorted(state["missing_digits"]))
        self.assertTrue(all(isinstance(value, int) for value in state["missing_digits"]))


if __name__ == "__main__":
    unittest.main()
