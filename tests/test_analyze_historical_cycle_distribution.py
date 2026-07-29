from __future__ import annotations

import unittest

from analyze_historical_cycle_distribution import (
    build_duration_comparison,
    empirical_quantile,
    render_report,
    summarize_durations,
)
from strategies.coverage_cycle_history import (
    CompletedCoverageCycle,
    WheelCoverageHistory,
)
from analyze_historical_cycle_distribution import (
    SegmentAnalysis,
)


class HistoricalCycleDistributionTests(
    unittest.TestCase
):
    def test_empirical_quantile_uses_nearest_rank(
        self,
    ) -> None:
        durations = (1, 2, 3, 4, 5)

        self.assertEqual(
            empirical_quantile(
                durations,
                0.50,
            ),
            3,
        )

        self.assertEqual(
            empirical_quantile(
                durations,
                0.90,
            ),
            5,
        )

    def test_duration_rows_are_probabilities(
        self,
    ) -> None:
        rows = build_duration_comparison(
            (2, 3, 3, 4),
            comparison_horizon=8,
        )

        self.assertEqual(
            len(rows),
            8,
        )

        self.assertAlmostEqual(
            sum(
                row.observed_probability
                for row in rows
            ),
            1.0,
        )

        self.assertAlmostEqual(
            rows[-1].observed_cdf,
            1.0,
        )

        self.assertTrue(
            all(
                0.0
                <= row.theoretical_probability
                <= 1.0
                for row in rows
            )
        )

    def test_summary_contains_exact_benchmark(
        self,
    ) -> None:
        durations = (2, 3, 3, 4, 5)
        rows = build_duration_comparison(
            durations
        )

        summary = summarize_durations(
            durations,
            rows,
        )

        self.assertEqual(
            summary.cycle_count,
            5,
        )

        self.assertAlmostEqual(
            summary.theoretical_mean,
            3.506190,
            places=5,
        )

        self.assertEqual(
            summary.theoretical_quantile_50,
            3,
        )

        self.assertEqual(
            summary.theoretical_quantile_95,
            6,
        )

        self.assertEqual(
            summary.theoretical_quantile_99,
            8,
        )

    def test_invalid_inputs_are_rejected(
        self,
    ) -> None:
        with self.assertRaises(ValueError):
            empirical_quantile(
                (),
                0.50,
            )

        with self.assertRaises(ValueError):
            empirical_quantile(
                (1, 2),
                1.0,
            )

        with self.assertRaises(ValueError):
            build_duration_comparison(())

        with self.assertRaises(ValueError):
            build_duration_comparison(
                (0, 1),
            )

    def test_report_preserves_segment_separation(
        self,
    ) -> None:
        history = WheelCoverageHistory(
            wheel="Bari",
            wheel_order=1,
            first_draw=1,
            first_date="2023-01-03",
            last_draw=2,
            last_date="2023-01-05",
            synchronized=True,
            initial_left_censored_draws=1,
            completed_cycles=(
                CompletedCoverageCycle(
                    wheel="Bari",
                    wheel_order=1,
                    cycle_number=1,
                    start_draw=2,
                    start_date="2023-01-05",
                    end_draw=2,
                    end_date="2023-01-05",
                    draws_in_cycle=1,
                ),
            ),
            right_censored_draws=0,
            right_censored_missing_digits=(
                frozenset()
            ),
        )

        rows = build_duration_comparison(
            (1,),
            comparison_horizon=8,
        )

        summary = summarize_durations(
            (1,),
            rows,
        )

        primary = SegmentAnalysis(
            label="Segmento continuo 2023–2026",
            database_paths=("primary.sqlite3",),
            first_date="2023-01-03",
            last_date="2026-07-28",
            histories=(history,),
            cycles=history.completed_cycles,
            summary=summary,
            duration_rows=rows,
        )

        secondary = SegmentAnalysis(
            label="Segmento secondario discontinuo",
            database_paths=("secondary.sqlite3",),
            first_date="2026-04-14",
            last_date="2026-07-25",
            histories=(history,),
            cycles=history.completed_cycles,
            summary=summary,
            duration_rows=rows,
        )

        single_report = render_report(primary)

        self.assertIn(
            "SEGMENTO CONTINUO 2023–2026",
            single_report,
        )

        self.assertNotIn(
            "SEGMENTO SECONDARIO DISCONTINUO",
            single_report,
        )

        report = render_report(
            primary,
            secondary,
        )

        self.assertIn(
            "SEGMENTO CONTINUO 2023–2026",
            report,
        )

        self.assertIn(
            "SEGMENTO SECONDARIO DISCONTINUO",
            report,
        )

        self.assertIn(
            "eventuali segmenti aggiuntivi restano separati",
            report,
        )

        self.assertIn(
            "non un test inferenziale",
            report,
        )


if __name__ == "__main__":
    unittest.main()
