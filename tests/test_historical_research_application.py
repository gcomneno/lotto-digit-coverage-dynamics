from __future__ import annotations

import unittest
from unittest.mock import patch

from lotto_digit_coverage.application.historical_anomalies import (
    AnomalyEvent,
    TransitionObservation,
    build_coverage_anomaly_report,
)
from lotto_digit_coverage.application.historical_rolling import (
    RollingFrequencyResultRow,
    build_rolling_frequency_report,
)
from lotto_digit_coverage.application.historical_twins import (
    build_twin_number_report,
)
from strategies.twin_numbers import (
    NULL_TWIN_PROBABILITY,
    TwinObservation,
    TwinStatisticsRow,
)


class HistoricalResearchApplicationTests(unittest.TestCase):
    def test_anomaly_report_exposes_transitions_events_and_summary(self) -> None:
        transition = TransitionObservation(
            wheel="Bari",
            wheel_order=1,
            cycle_number=1,
            event_index=1,
            position_in_cycle=1,
            target_draw=10,
            target_date="2026-01-10",
            source_state=(1,),
            target_state=(),
            transition_probability=0.01,
        )
        event = AnomalyEvent(
            category="A2",
            signature="A2:closure:{1}->{}",
            recurrence_key="A2:closure:{1}",
            wheel="Bari",
            wheel_order=1,
            cycle_number=1,
            event_index=1,
            target_draw=10,
            target_date="2026-01-10",
            source_state="{1}",
            target_state="{}",
            horizon=1,
            conditional_probability=0.01,
            atom_probability=0.01,
            previous_conditional_probability=None,
            pair_probability=None,
            surprisal=2.0,
            severity="rare",
            right_censored=False,
            previous_target_draw=None,
            previous_target_date=None,
            recurrence_gap=None,
        )

        with patch(
            "lotto_digit_coverage.application.historical_anomalies.build_all_transitions",
            return_value=(transition,),
        ), patch(
            "lotto_digit_coverage.application.historical_anomalies.detect_anomalies",
            return_value=(event,),
        ):
            report = build_coverage_anomaly_report(
                {},
                threshold=0.01,
                recurrence_window=10,
                recurrence_threshold=0.01,
            )

        self.assertEqual(report.transitions, (transition,))
        self.assertEqual(report.events, (event,))
        self.assertEqual(report.summary["event_count"], 1)
        self.assertEqual(report.summary["category_counts"]["A2"], 1)

    def test_rolling_report_normalizes_windows_and_preserves_protocol_inputs(self) -> None:
        row = RollingFrequencyResultRow(
            window_size=6,
            period="held-out",
            start_date="2026-01-01",
            end_date="2026-12-31",
            repetitions=25,
            seed=706,
            observation_count=1,
            candidate_number_count=2,
            covered_ambo_count=1,
            observed_hit_number_count=0,
            theoretical_hit_number_count=0.1,
            random_mean_hit_number_count=0.1,
            observed_to_random_number_ratio=0.0,
            empirical_p_value_hit_number=1.0,
            observed_hit_ambo_count=0,
            theoretical_hit_ambo_count=0.01,
            random_mean_hit_ambo_count=0.01,
            observed_to_random_ambo_ratio=0.0,
            empirical_p_value_hit_ambo=1.0,
        )

        with patch(
            "lotto_digit_coverage.application.historical_rolling.build_walk_forward_experiment",
            return_value={3: (), 6: ()},
        ) as experiment, patch(
            "lotto_digit_coverage.application.historical_rolling.build_result_rows",
            return_value=(row,),
        ) as rows:
            report = build_rolling_frequency_report(
                {"Bari": ()},
                window_sizes=(6, 3, 6),
                periods=(("held-out", "2026-01-01", "2026-12-31"),),
                repetitions=25,
                base_seed=100,
            )

        experiment.assert_called_once_with(
            {"Bari": ()},
            window_sizes=(3, 6),
        )
        self.assertEqual(rows.call_args.kwargs["window_sizes"], (3, 6))
        self.assertEqual(rows.call_args.kwargs["repetitions"], 25)
        self.assertEqual(rows.call_args.kwargs["base_seed"], 100)
        self.assertEqual(report.rows, (row,))

    def test_twin_report_filters_before_statistics_and_keeps_exploratory_result(self) -> None:
        observations = (
            TwinObservation(
                wheel="Bari",
                wheel_order=1,
                target_draw=10,
                target_date="2026-01-10",
                digit=1,
                twin_number=11,
                conditions=("baseline",),
                hit=True,
            ),
            TwinObservation(
                wheel="Roma",
                wheel_order=8,
                target_draw=11,
                target_date="2026-01-11",
                digit=1,
                twin_number=11,
                conditions=("baseline",),
                hit=False,
            ),
        )
        row = TwinStatisticsRow(
            condition="baseline",
            digit=1,
            twin_number=11,
            cases=1,
            hits=1,
            expected_hits=NULL_TWIN_PROBABILITY,
            null_probability=NULL_TWIN_PROBABILITY,
            observed_probability=1.0,
            lift_probability=1.0 - NULL_TWIN_PROBABILITY,
            wilson_low=0.2,
            wilson_high=1.0,
            p_value=1.0,
            q_value=1.0,
            candidate=False,
        )

        with patch(
            "lotto_digit_coverage.application.historical_twins.build_all_twin_observations",
            return_value=observations,
        ), patch(
            "lotto_digit_coverage.application.historical_twins.build_twin_statistics",
            return_value=(row,),
        ) as statistics:
            report = build_twin_number_report(
                {"Bari": (), "Roma": ()},
                wheels=("bari",),
                from_date="2026-01-10",
                to_date="2026-01-10",
            )

        statistics.assert_called_once_with((observations[0],))
        self.assertEqual(report.observations, (observations[0],))
        self.assertEqual(report.first_target_date, "2026-01-10")
        self.assertEqual(report.last_target_date, "2026-01-10")
        self.assertEqual(report.candidate_count, 0)


if __name__ == "__main__":
    unittest.main()
