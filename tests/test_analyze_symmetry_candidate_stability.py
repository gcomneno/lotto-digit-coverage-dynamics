from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analyze_historical_symmetry_classes import (
    ClassObservation,
)
from analyze_symmetry_candidate_stability import (
    CANDIDATE_CLASS_IDS,
    build_breakdown_rows,
    build_stability_rows,
    validate_breakdown_rows,
    write_csv,
    write_json,
)


PROBABILITIES = {
    "nine-no-zero:1": (
        0.29457953656930075
    ),
    "nine-no-zero:3": (
        0.10961868579927198
    ),
    "no-nine:1": (
        0.68164329835937199
    ),
}


def observation(
    *,
    class_id: str,
    date: str,
    wheel: str,
    wheel_order: int,
    completed: bool,
) -> ClassObservation:
    missing_by_class = {
        "nine-no-zero:1": (1, 9),
        "nine-no-zero:3": (1, 2, 3, 9),
        "no-nine:1": (1,),
    }

    return ClassObservation(
        wheel=wheel,
        wheel_order=wheel_order,
        target_draw=1,
        target_date=date,
        missing_digits=(
            missing_by_class[class_id]
        ),
        class_id=class_id,
        theoretical_probability=(
            PROBABILITIES[class_id]
        ),
        completed_next=completed,
    )


class CandidateStabilityTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.observations = (
            observation(
                class_id="nine-no-zero:1",
                date="2023-01-01",
                wheel="Bari",
                wheel_order=1,
                completed=True,
            ),
            observation(
                class_id="nine-no-zero:1",
                date="2023-01-02",
                wheel="Bari",
                wheel_order=1,
                completed=False,
            ),
            observation(
                class_id="nine-no-zero:1",
                date="2024-01-01",
                wheel="Torino",
                wheel_order=10,
                completed=False,
            ),
            observation(
                class_id="nine-no-zero:3",
                date="2023-01-03",
                wheel="Torino",
                wheel_order=10,
                completed=True,
            ),
            observation(
                class_id="nine-no-zero:3",
                date="2024-01-02",
                wheel="Bari",
                wheel_order=1,
                completed=False,
            ),
            observation(
                class_id="no-nine:1",
                date="2025-01-01",
                wheel="Bari",
                wheel_order=1,
                completed=True,
            ),
        )

    def test_year_breakdown_preserves_totals(
        self,
    ) -> None:
        rows = build_breakdown_rows(
            self.observations,
            dimension="year",
        )

        validate_breakdown_rows(
            rows,
            self.observations,
            dimension="year",
        )

        self.assertEqual(
            len(rows),
            len(CANDIDATE_CLASS_IDS) * 3,
        )

        candidate = [
            row
            for row in rows
            if row.class_id
            == "nine-no-zero:1"
        ]

        self.assertEqual(
            sum(
                row.observations
                for row in candidate
            ),
            3,
        )

        row_2023 = next(
            row
            for row in candidate
            if row.segment == "2023"
        )

        self.assertEqual(
            row_2023.observations,
            2,
        )

        self.assertEqual(
            row_2023.observed_completions,
            1,
        )

        row_2025 = next(
            row
            for row in candidate
            if row.segment == "2025"
        )

        self.assertEqual(
            row_2025.direction,
            "no-data",
        )

    def test_wheel_breakdown_is_separate(
        self,
    ) -> None:
        rows = build_breakdown_rows(
            self.observations,
            dimension="wheel",
        )

        validate_breakdown_rows(
            rows,
            self.observations,
            dimension="wheel",
        )

        self.assertEqual(
            len(rows),
            len(CANDIDATE_CLASS_IDS) * 2,
        )

        bari = next(
            row
            for row in rows
            if (
                row.class_id
                == "nine-no-zero:1"
                and row.segment == "Bari"
            )
        )

        torino = next(
            row
            for row in rows
            if (
                row.class_id
                == "nine-no-zero:1"
                and row.segment == "Torino"
            )
        )

        self.assertEqual(
            bari.observations,
            2,
        )

        self.assertEqual(
            torino.observations,
            1,
        )

    def test_stability_reports_mixed_year_signs(
        self,
    ) -> None:
        year_rows = build_breakdown_rows(
            self.observations,
            dimension="year",
        )

        wheel_rows = build_breakdown_rows(
            self.observations,
            dimension="wheel",
        )

        summaries = build_stability_rows(
            year_rows,
            wheel_rows,
        )

        candidate = next(
            row
            for row in summaries
            if row.class_id
            == "nine-no-zero:1"
        )

        self.assertEqual(
            candidate.positive_years,
            ("2023",),
        )

        self.assertEqual(
            candidate.negative_years,
            ("2024",),
        )

        self.assertFalse(
            candidate.yearly_direction_consistent
        )

        self.assertEqual(
            candidate.largest_wheel,
            "Bari",
        )

        self.assertAlmostEqual(
            candidate
            .largest_wheel_observation_share,
            2 / 3,
        )

    def test_rejects_unknown_dimension(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            build_breakdown_rows(
                self.observations,
                dimension="month",
            )

    def test_outputs_are_lf_and_valid_json(
        self,
    ) -> None:
        year_rows = build_breakdown_rows(
            self.observations,
            dimension="year",
        )

        wheel_rows = build_breakdown_rows(
            self.observations,
            dimension="wheel",
        )

        stability_rows = build_stability_rows(
            year_rows,
            wheel_rows,
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            year_csv = root / "year.csv"
            wheel_csv = root / "wheel.csv"
            json_path = root / "stability.json"

            write_csv(
                year_rows,
                year_csv,
            )

            write_csv(
                wheel_rows,
                wheel_csv,
            )

            write_json(
                year_rows,
                wheel_rows,
                stability_rows,
                json_path,
            )

            self.assertNotIn(
                b"\r",
                year_csv.read_bytes(),
            )

            self.assertNotIn(
                b"\r",
                wheel_csv.read_bytes(),
            )

            document = json.loads(
                json_path.read_text(
                    encoding="utf-8"
                )
            )

            self.assertEqual(
                document[
                    "candidate_class_ids"
                ],
                list(CANDIDATE_CLASS_IDS),
            )

            self.assertEqual(
                len(document["stability"]),
                2,
            )


if __name__ == "__main__":
    unittest.main()
