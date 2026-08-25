from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_repo", ROOT / "scripts/validate_repo.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader

# validate_repo imports its sibling module by name.
import sys
sys.path.insert(0, str(ROOT / "scripts"))
SPEC.loader.exec_module(VALIDATOR)


class ContractTests(unittest.TestCase):
    def test_repository_contract(self) -> None:
        self.assertEqual([], VALIDATOR.validate(ROOT))


if __name__ == "__main__":
    unittest.main()
