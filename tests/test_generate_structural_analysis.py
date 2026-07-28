from __future__ import annotations

import json
import math
import statistics
import tempfile
import unittest
from pathlib import Path

from generate_structural_analysis import (
    build_cardinality_loss_rows,
    build_symmetry_class_rows,
    validate_analysis,
    write_outputs,
)
from strategies.coverage_markov import (
    expected_remaining_draws,
)
from strategies.coverage_structure import (
    all_digit_states,
)


class GenerateStructuralAnalysisTests(
    unittest.TestCase
):
    def setUp(self) -> None:
        self.class_rows = (
            build_symmetry_class_rows()
        )

        self.cardinality_rows = (
            build_cardinality_loss_rows(
                self.class_rows
            )
        )

    def test_contains_twenty_seven_classes(
        self,
    ) -> None:
        self.assertEqual(
            len(self.class_rows),
            27,
        )

        self.assertEqual(
            sum(
                row.state_multiplicity
                for row in self.class_rows
            ),
            1023,
        )

    def test_family_multiplicities_are_exact(
        self,
    ) -> None:
        for row in self.class_rows:
            if row.family == "no-nine":
                expected = math.comb(
                    9,
                    row.exchangeable_count,
                )
            else:
                expected = math.comb(
                    8,
                    row.exchangeable_count,
                )

            with self.subTest(
                class_id=row.class_id
            ):
                self.assertEqual(
                    row.state_multiplicity,
                    expected,
                )

    def test_cardinality_partition_is_complete(
        self,
    ) -> None:
        self.assertEqual(
            len(self.cardinality_rows),
            10,
        )

        for row in self.cardinality_rows:
            self.assertEqual(
                row.state_count,
                math.comb(
                    10,
                    row.missing_count,
                ),
            )

    def test_count_only_summary_loses_information(
        self,
    ) -> None:
        for row in self.cardinality_rows[:-1]:
            with self.subTest(
                missing_count=(
                    row.missing_count
                )
            ):
                self.assertGreater(
                    row.expected_range,
                    0.0,
                )

        self.assertEqual(
            self.cardinality_rows[-1]
            .expected_range,
            0.0,
        )

    def test_count_only_mean_weights_exact_states_uniformly(
        self,
    ) -> None:
        states = all_digit_states(
            include_empty=False
        )

        for row in self.cardinality_rows:
            exact_mean = statistics.fmean(
                expected_remaining_draws(
                    state
                )
                for state in states
                if len(state)
                == row.missing_count
            )

            with self.subTest(
                missing_count=(
                    row.missing_count
                )
            ):
                self.assertAlmostEqual(
                    row.count_only_expected_mean,
                    exact_mean,
                    places=12,
                )

    def test_zero_nine_class_is_distinct(
        self,
    ) -> None:
        rows = {
            row.class_id: row
            for row in self.class_rows
        }

        zero_nine = rows["zero-nine:0"]
        nine_only = rows["nine-no-zero:1"]

        self.assertNotAlmostEqual(
            zero_nine
            .expected_remaining_draws,
            nine_only
            .expected_remaining_draws,
            places=12,
        )

    def test_csv_outputs_use_lf_line_endings(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            classes_path = root / "classes.csv"
            cardinality_path = root / "cardinality.csv"

            write_outputs(
                self.class_rows,
                self.cardinality_rows,
                classes_csv=classes_path,
                cardinality_csv=cardinality_path,
                json_output=root / "analysis.json",
                summary_output=root / "summary.md",
            )

            for path in (
                classes_path,
                cardinality_path,
            ):
                with self.subTest(path=path.name):
                    content = path.read_bytes()

                    self.assertIn(
                        b"\n",
                        content,
                    )

                    self.assertNotIn(
                        b"\r",
                        content,
                    )

    def test_outputs_are_deterministic(
        self,
    ) -> None:
        validate_analysis(
            self.class_rows,
            self.cardinality_rows,
        )

        with tempfile.TemporaryDirectory() as first:
            with tempfile.TemporaryDirectory() as second:
                first_root = Path(first)
                second_root = Path(second)

                first_paths = (
                    first_root / "classes.csv",
                    first_root / "cardinality.csv",
                    first_root / "analysis.json",
                    first_root / "summary.md",
                )

                second_paths = (
                    second_root / "classes.csv",
                    second_root / "cardinality.csv",
                    second_root / "analysis.json",
                    second_root / "summary.md",
                )

                write_outputs(
                    self.class_rows,
                    self.cardinality_rows,
                    classes_csv=first_paths[0],
                    cardinality_csv=first_paths[1],
                    json_output=first_paths[2],
                    summary_output=first_paths[3],
                )

                write_outputs(
                    self.class_rows,
                    self.cardinality_rows,
                    classes_csv=second_paths[0],
                    cardinality_csv=second_paths[1],
                    json_output=second_paths[2],
                    summary_output=second_paths[3],
                )

                for first_path, second_path in zip(
                    first_paths,
                    second_paths,
                ):
                    self.assertEqual(
                        first_path.read_bytes(),
                        second_path.read_bytes(),
                    )

                document = json.loads(
                    first_paths[2].read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual(
                    document["state_space"][
                        "non_empty_symmetry_classes"
                    ],
                    27,
                )

                self.assertEqual(
                    document["verification"][
                        "maximum_transition_error"
                    ],
                    0.0,
                )

                self.assertIn(
                    "uniform over exact states",
                    document[
                        "cardinality_aggregation"
                    ]["weighting"],
                )

                self.assertIn(
                    "not empirical state-frequency",
                    document[
                        "cardinality_aggregation"
                    ]["interpretation"],
                )


if __name__ == "__main__":
    unittest.main()
