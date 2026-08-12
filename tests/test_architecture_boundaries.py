from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = ROOT / "lotto_digit_coverage"

LAYER_PATHS = {
    "domain": PACKAGE_ROOT / "domain",
    "application": PACKAGE_ROOT / "application",
    "infrastructure": PACKAGE_ROOT / "infrastructure",
    "interfaces": PACKAGE_ROOT / "interfaces",
}

FORBIDDEN_LAYER_IMPORTS = {
    "domain": (
        "lotto_digit_coverage.application",
        "lotto_digit_coverage.infrastructure",
        "lotto_digit_coverage.interfaces",
    ),
    "application": (
        "lotto_digit_coverage.infrastructure",
        "lotto_digit_coverage.interfaces",
    ),
    "infrastructure": (
        "lotto_digit_coverage.interfaces",
    ),
}

FORBIDDEN_DIRECT_DEPENDENCIES = {
    "domain": {
        "argparse",
        "sqlite3",
        "subprocess",
        "tkinter",
        "PySide2",
        "PySide6",
        "PyQt5",
        "PyQt6",
        "wx",
        "kivy",
    },
    "application": {
        "argparse",
        "sqlite3",
        "subprocess",
        "tkinter",
        "PySide2",
        "PySide6",
        "PyQt5",
        "PyQt6",
        "wx",
        "kivy",
    },
}


def imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(
                (node.lineno, alias.name)
                for alias in node.names
            )
            continue

        if not isinstance(node, ast.ImportFrom):
            continue

        module = node.module or ""

        if node.level:
            # Relative imports such as ``from ..infrastructure`` must still be
            # checked against the architectural package prefixes.
            modules.append(
                (
                    node.lineno,
                    "lotto_digit_coverage."
                    + module,
                )
            )
        elif module:
            modules.append((node.lineno, module))

    return modules


class ArchitectureBoundaryTests(unittest.TestCase):
    def test_package_skeleton_exists(self) -> None:
        expected = (
            PACKAGE_ROOT / "__init__.py",
            LAYER_PATHS["domain"] / "__init__.py",
            LAYER_PATHS["application"] / "__init__.py",
            LAYER_PATHS["infrastructure"] / "__init__.py",
            LAYER_PATHS["interfaces"] / "__init__.py",
            LAYER_PATHS["interfaces"] / "cli" / "__init__.py",
        )

        for path in expected:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertTrue(path.is_file())

    def test_layers_do_not_import_forbidden_dependencies(self) -> None:
        violations: list[str] = []

        for layer, path in LAYER_PATHS.items():
            forbidden_prefixes = FORBIDDEN_LAYER_IMPORTS.get(layer, ())
            forbidden_roots = FORBIDDEN_DIRECT_DEPENDENCIES.get(layer, set())

            for module_path in sorted(path.rglob("*.py")):
                for line, imported in imported_modules(module_path):
                    root = imported.split(".", 1)[0]

                    if root in forbidden_roots:
                        violations.append(
                            f"{module_path.relative_to(ROOT)}:{line}: "
                            f"{layer} imports forbidden dependency {imported}"
                        )
                        continue

                    if any(
                        imported == prefix
                        or imported.startswith(prefix + ".")
                        for prefix in forbidden_prefixes
                    ):
                        violations.append(
                            f"{module_path.relative_to(ROOT)}:{line}: "
                            f"{layer} imports forbidden layer {imported}"
                        )

        self.assertEqual([], violations, "\n".join(violations))

    def test_legacy_cli_table_import_is_a_compatibility_alias(self) -> None:
        from lotto_digit_coverage.interfaces.cli.table import (
            Column as CanonicalColumn,
        )
        from strategies.cli_table import Column as LegacyColumn

        self.assertIs(LegacyColumn, CanonicalColumn)


if __name__ == "__main__":
    unittest.main()
