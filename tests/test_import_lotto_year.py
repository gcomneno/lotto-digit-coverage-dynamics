from __future__ import annotations

import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from import_lotto import (
    Draw,
    archive_database_path,
    archive_source_path,
    archive_url,
    build_parser,
    current_system_year,
    destination_database_path,
    download_archive,
    parse_import_limit,
    parse_year,
    validate_archive_year,
)


class FakeResponse:
    status = 200

    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        return None

    def read(self) -> bytes:
        return self.content


class ImportLottoYearTests(unittest.TestCase):
    def test_default_year_is_current_system_year(
        self,
    ) -> None:
        args = build_parser().parse_args([])

        self.assertEqual(
            args.year,
            current_system_year(),
        )
        self.assertIsNone(args.limit)
        self.assertIsNone(args.source)
        self.assertIsNone(args.database)
        self.assertIsNone(args.source_url)

    def test_year_derives_url_and_paths(
        self,
    ) -> None:
        self.assertEqual(
            archive_url(2024),
            (
                "https://www.estrazionedellotto.it/"
                "risultati/archivio-lotto-2024"
            ),
        )
        self.assertEqual(
            archive_source_path(2024),
            Path("_work/archive-2024.html"),
        )
        self.assertEqual(
            archive_database_path(2024),
            Path("data/lotto-2024.sqlite3"),
        )

    @patch(
        "import_lotto.current_system_year",
        return_value=2026,
    )
    def test_destination_database_path_distinguishes_current_year(
        self,
        _current_year: object,
    ) -> None:
        self.assertEqual(
            destination_database_path(2026),
            Path("data/lotto-current.sqlite3"),
        )
        self.assertEqual(
            destination_database_path(2025),
            Path("data/lotto-2025.sqlite3"),
        )

    def test_parse_year_requires_four_digits(
        self,
    ) -> None:
        self.assertEqual(parse_year("2024"), 2024)

        for invalid in (
            "24",
            "20245",
            "abcd",
            "1899",
            str(current_system_year() + 1),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(
                    argparse.ArgumentTypeError
                ):
                    parse_year(invalid)

    def test_limit_defaults_to_all_semantics(
        self,
    ) -> None:
        self.assertIsNone(
            parse_import_limit("all")
        )
        self.assertEqual(
            parse_import_limit("12"),
            12,
        )

    def test_validate_archive_year(
        self,
    ) -> None:
        valid = [
            Draw(
                number=1,
                date="2024-01-02",
                wheels=(),
            ),
            Draw(
                number=2,
                date="2024-12-31",
                wheels=(),
            ),
        ]

        validate_archive_year(
            valid,
            expected_year=2024,
        )

        invalid = [
            Draw(
                number=3,
                date="2025-01-02",
                wheels=(),
            )
        ]

        with self.assertRaisesRegex(
            ValueError,
            "contiene estrazioni di un altro anno",
        ):
            validate_archive_year(
                invalid,
                expected_year=2024,
            )

    def test_download_archive_writes_atomically(
        self,
    ) -> None:
        content = b"<html>archivio lotto</html>"

        with tempfile.TemporaryDirectory() as directory:
            destination = (
                Path(directory)
                / "nested"
                / "archive-2024.html"
            )

            with patch(
                "import_lotto.urlopen",
                return_value=FakeResponse(content),
            ):
                result = download_archive(
                    "https://example.test/archive",
                    destination,
                )

            self.assertEqual(result, content)
            self.assertEqual(
                destination.read_bytes(),
                content,
            )
            self.assertFalse(
                destination.with_suffix(
                    ".html.tmp"
                ).exists()
            )


if __name__ == "__main__":
    unittest.main()
