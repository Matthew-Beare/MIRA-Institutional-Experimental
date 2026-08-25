from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs" / "code-inventory.json"
PRODUCTION_GLOBS = (
    "scripts/*.py",
    "starter/tools/*.py",
    "skill/ops-brief-policy/scripts/*.py",
)


def production_files() -> set[str]:
    paths: set[str] = set()
    for pattern in PRODUCTION_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.name.startswith("test_"):
                paths.add(path.relative_to(ROOT).as_posix())
    return paths


class CodeInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        self.rows = self.inventory["files"]

    def test_every_production_python_file_is_justified_exactly_once(self) -> None:
        listed = [row["path"] for row in self.rows]
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(production_files(), set(listed))
        for row in self.rows:
            self.assertGreaterEqual(len(row["responsibility"]), 20)
            self.assertGreaterEqual(len(row["why_separate"]), 20)
            self.assertTrue(row["tests"])
            for test in row["tests"]:
                self.assertTrue((ROOT / test).is_file(), f"missing test evidence: {test}")

    def test_production_python_has_docstrings_and_no_debug_or_dynamic_execution(self) -> None:
        forbidden_calls = {"eval", "exec", "breakpoint"}
        forbidden_markers = ("TODO", "FIXME", "XXX")
        for relative in sorted(production_files()):
            source = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(path=relative):
                tree = ast.parse(source, filename=relative)
                self.assertTrue(ast.get_docstring(tree), "production module lacks a docstring")
                self.assertFalse(any(marker in source for marker in forbidden_markers))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, forbidden_calls)
                    if isinstance(node, ast.ExceptHandler):
                        self.assertIsNotNone(node.type, "bare except is prohibited")
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        self.assertFalse(any(alias.name == "*" for alias in node.names))
                    if isinstance(node, ast.Call):
                        for keyword in node.keywords:
                            if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant):
                                self.assertIsNot(keyword.value.value, True, "shell=True is prohibited")


if __name__ == "__main__":
    unittest.main()
