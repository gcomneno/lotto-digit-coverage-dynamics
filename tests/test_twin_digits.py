from __future__ import annotations

import unittest
from pathlib import Path

from strategies.lotto_repository import (
    DrawSnapshot,
    format_number,
    split_digits,
)
from strategies.twin_digits import (
    LottoRepository,
    TwinEvent,
    analyze_event_windows,
    count_digit_in_numbers,
    is_twin_number,
    rank_digit_by_presence,
)


DATABASE_PATH = Path("data/lotto-2026.sqlite3")


class NumberFormattingTests(unittest.TestCase):
    def test_format_single_digit_with_leading_zero(self) -> None:
        self.assertEqual(format_number(1), "01")

    def test_split_single_digit_includes_zero(self) -> None:
        self.assertEqual(split_digits(1), (0, 1))

    def test_recognizes_only_allowed_twins(self) -> None:
        for value in (11, 22, 33, 44, 55, 66, 77, 88):
            self.assertTrue(is_twin_number(value))

        for value in (1, 10, 12, 90, 99):
            self.assertFalse(is_twin_number(value))


class DigitCountingTests(unittest.TestCase):
    def test_counts_both_occurrences_in_66(self) -> None:
        result = count_digit_in_numbers([66], 6)

        self.assertEqual(result.digit_occurrences, 2)
        self.assertEqual(result.numbers_with_digit, 1)

    def test_counts_one_occurrence_in_06_and_60(self) -> None:
        result = count_digit_in_numbers([6, 60], 6)

        self.assertEqual(result.digit_occurrences, 2)
        self.assertEqual(result.numbers_with_digit, 2)


    def test_rank_uses_average_position_for_ties(self) -> None:
        counts = (
            0,  # cifra 0, esclusa dalla classifica
            0,
            1,
            1,
            1,
            1,
            2,
            2,
            2,
            0,  # cifra 9, esclusa dalla classifica
        )

        # 6, 7 e 8 condividono le posizioni 1, 2 e 3.
        self.assertEqual(
            rank_digit_by_presence(counts, 6),
            2.0,
        )

        # La cifra 1 è ultima da sola.
        self.assertEqual(
            rank_digit_by_presence(counts, 1),
            8.0,
        )



class WindowAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event = TwinEvent(
            draw_number=100,
            draw_date="2026-06-01",
            wheel="Bari",
            wheel_order=1,
            position=1,
            twin_number=11,
        )

        self.previous_draws = (
            DrawSnapshot(
                draw_number=99,
                draw_date="2026-05-31",
                wheel="Bari",
                wheel_order=1,
                numbers=(1, 12, 23, 34, 45),
            ),
            DrawSnapshot(
                draw_number=98,
                draw_date="2026-05-30",
                wheel="Bari",
                wheel_order=1,
                numbers=(67, 71, 81, 90, 22),
            ),
        )

    def test_windows_are_cumulative(self) -> None:
        analysis = analyze_event_windows(
            self.event,
            self.previous_draws,
            lookback=2,
        )

        first, second = analysis.windows

        self.assertEqual(first.digit_occurrences, 2)
        self.assertEqual(second.digit_occurrences, 4)
        self.assertEqual(first.available_draws, 1)
        self.assertEqual(second.available_draws, 2)

        self.assertEqual(
            first.digit_counts,
            (1, 2, 2, 2, 2, 1, 0, 0, 0, 0),
        )
        self.assertEqual(
            second.digit_counts,
            (2, 4, 4, 2, 2, 1, 1, 2, 1, 1),
        )

        self.assertEqual(sum(first.digit_counts), 10)
        self.assertEqual(sum(second.digit_counts), 20)


    def test_single_windows_use_only_the_nth_previous_draw(self) -> None:
        analysis = analyze_event_windows(
            self.event,
            self.previous_draws,
            lookback=3,
            window_mode="single",
        )

        first, second, third = analysis.windows

        self.assertEqual(
            tuple(draw.draw_number for draw in first.draws),
            (99,),
        )
        self.assertEqual(
            tuple(draw.draw_number for draw in second.draws),
            (98,),
        )
        self.assertEqual(third.draws, ())

        self.assertEqual(first.digit_slots, 10)
        self.assertEqual(second.digit_slots, 10)
        self.assertEqual(third.digit_slots, 0)

        self.assertTrue(first.is_complete)
        self.assertTrue(second.is_complete)
        self.assertFalse(third.is_complete)



@unittest.skipUnless(
    DATABASE_PATH.is_file(),
    "Database di integrazione non disponibile.",
)
class DatabaseIntegrationTests(unittest.TestCase):
    def test_latest_draw_is_120(self) -> None:
        with LottoRepository(DATABASE_PATH) as repository:
            draw_number, draw_date = repository.latest_draw()

        self.assertEqual(draw_number, 120)
        self.assertEqual(draw_date, "2026-07-28")

    def test_expected_twins_exist_in_draw_119(self) -> None:
        with LottoRepository(DATABASE_PATH) as repository:
            events = repository.twin_events_for_draw(119)

        found = {
            (event.wheel, event.twin_number)
            for event in events
        }

        self.assertIn(("Bari", 66), found)
        self.assertIn(("Genova", 11), found)
        self.assertIn(("Genova", 66), found)

    def test_previous_draws_are_same_wheel_and_exclude_current(self) -> None:
        event = TwinEvent(
            draw_number=119,
            draw_date="2026-07-25",
            wheel="Genova",
            wheel_order=4,
            position=2,
            twin_number=11,
        )

        with LottoRepository(DATABASE_PATH) as repository:
            draws = repository.previous_draws_for_event(
                event,
                limit=6,
            )

        self.assertEqual(len(draws), 6)
        self.assertTrue(
            all(draw.wheel == "Genova" for draw in draws)
        )
        self.assertTrue(
            all(draw.draw_number != 119 for draw in draws)
        )
        self.assertEqual(draws[0].draw_number, 118)

    def test_previous_draws_are_temporally_descending(self) -> None:
        event = TwinEvent(
            draw_number=119,
            draw_date="2026-07-25",
            wheel="Bari",
            wheel_order=1,
            position=4,
            twin_number=66,
        )

        with LottoRepository(DATABASE_PATH) as repository:
            draws = repository.previous_draws_for_event(
                event,
                limit=6,
            )

        ordering = [
            (draw.draw_date, draw.draw_number)
            for draw in draws
        ]

        self.assertEqual(
            ordering,
            sorted(ordering, reverse=True),
        )


if __name__ == "__main__":
    unittest.main()
