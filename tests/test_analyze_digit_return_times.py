from __future__ import annotations

import unittest

from analyze_digit_return_times import (
    bucket_sort_key,
    streak_bucket,
)


class AnalyzeDigitReturnTimesTests(unittest.TestCase):
    def test_explicit_streak_bucket(self) -> None:
        self.assertEqual(streak_bucket(1), "1")
        self.assertEqual(streak_bucket(8), "8")

    def test_long_streak_bucket(self) -> None:
        self.assertEqual(streak_bucket(9), "9+")
        self.assertEqual(streak_bucket(20), "9+")

    def test_bucket_order(self) -> None:
        buckets = ["9+", "2", "1", "8"]

        self.assertEqual(
            sorted(buckets, key=bucket_sort_key),
            ["1", "2", "8", "9+"],
        )


if __name__ == "__main__":
    unittest.main()
