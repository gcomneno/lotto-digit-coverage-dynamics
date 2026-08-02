from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from strategies.coverage_completion import (
    CurrentCoverageState,
)
from strategies.current_coverage_signal import (
    HistoricalCoverageClass,
    build_current_coverage_signals,
    load_historical_coverage_classes,
    print_coverage_hit_signal,
    wilson_lower_bound,
)


def state(
    *,
    wheel: str,
    wheel_order: int,
    draws_in_cycle: int,
    top: frozenset[int],
    missing: frozenset[int],
) -> CurrentCoverageState:
    return CurrentCoverageState(
        wheel=wheel,
        wheel_order=wheel_order,
        latest_draw=123,
        latest_date="2026-08-01",
        completed_cycles=100,
        draws_in_cycle=draws_in_cycle,
        covered_digits=(
            frozenset(range(10)) - missing
        ),
        missing_digits=missing,
        synchronized=True,
        most_present_digits=top,
    )


class CurrentCoverageSignalTests(
    unittest.TestCase
):
    def test_wilson_lower_bound_validates_counts(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            wilson_lower_bound(2, 1)

        with self.assertRaises(ValueError):
            wilson_lower_bound(0, 0)

    def test_palermo_x2_ranks_before_x1_state(
        self,
    ) -> None:
        historical = {
            (
                1,
                2,
            ): HistoricalCoverageClass(
                most_present_count=1,
                missing_count=2,
                threshold=1,
                cases=7605,
                obtained=6639,
                expected_probability=(
                    0.8764238179531166
                ),
                evidence_level="strong",
            ),
            (
                1,
                1,
            ): HistoricalCoverageClass(
                most_present_count=1,
                missing_count=1,
                threshold=1,
                cases=23019,
                obtained=13540,
                expected_probability=(
                    0.590373
                ),
                evidence_level="strong",
            ),
        }

        signals = build_current_coverage_signals(
            (
                state(
                    wheel="Firenze",
                    wheel_order=1,
                    draws_in_cycle=2,
                    top=frozenset({
                        0,
                    }),
                    missing=frozenset({
                        3,
                    }),
                ),
                state(
                    wheel="Palermo",
                    wheel_order=2,
                    draws_in_cycle=3,
                    top=frozenset({
                        5,
                    }),
                    missing=frozenset({
                        8,
                        9,
                    }),
                ),
            ),
            historical,
        )

        self.assertEqual(
            signals[0].wheel,
            "Palermo",
        )
        self.assertEqual(
            signals[0].class_label,
            "1,2",
        )
        self.assertEqual(
            signals[0].historical.cases,
            7605,
        )
        self.assertAlmostEqual(
            signals[0].conservative_probability,
            0.8290,
            places=4,
        )
        self.assertLess(
            signals[0].conservative_excess,
            0.0,
        )

    def test_loader_rejects_incoherent_threshold(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "summary.csv"

            path.write_text(
                "top,missing,threshold,cases,obtained,"
                "expected_probability,evidence_level\n"
                "1,2,2,100,80,0.75,strong\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "soglia",
            ):
                load_historical_coverage_classes(
                    path
                )

    def test_prints_operational_ranking(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "summary.csv"

            path.write_text(
                "top,missing,threshold,cases,obtained,"
                "expected_probability,evidence_level\n"
                "1,2,1,7605,6639,"
                "0.8764238179531166,strong\n",
                encoding="utf-8",
            )

            output = io.StringIO()

            with redirect_stdout(output):
                print_coverage_hit_signal(
                    (
                        state(
                            wheel="Palermo",
                            wheel_order=1,
                            draws_in_cycle=3,
                            top=frozenset({
                                5,
                            }),
                            missing=frozenset({
                                8,
                                9,
                            }),
                        ),
                    ),
                    summary_path=path,
                )

        rendered = output.getvalue()

        self.assertIn(
            "SEGNALE OPERATIVO COVERAGE-HITS",
            rendered,
        )
        self.assertIn(
            "Palermo",
            rendered,
        )
        self.assertIn(
            "1,2",
            rendered,
        )
        self.assertIn(
            "{8,9}",
            rendered,
        )
        self.assertIn(
            "82.90%",
            rendered,
        )
        self.assertIn(
            "Età è descrittiva",
            rendered,
        )
        self.assertIn(
            "non indica un vantaggio storico",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
