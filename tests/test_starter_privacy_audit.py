from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_starter_privacy.py"
SPEC = importlib.util.spec_from_file_location("starter_privacy_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class StarterPrivacyAuditTests(unittest.TestCase):
    def test_missing_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            blocklist = root / "blocklist.txt"
            blocklist.write_text("", encoding="utf-8")
            self.assertTrue(MODULE.audit(root / "missing", blocklist))
            starter = root / "starter"
            starter.mkdir()
            self.assertTrue(MODULE.audit(starter, root / "missing-blocklist"))

    def test_literal_blocklist_and_generic_private_markers_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            starter = root / "starter"
            starter.mkdir()
            (starter / "config.md").write_text(
                "PRIVATE_LITERAL\n" + "owner@" + "personal.invalid\n"
                + "https://" + "docs.google.com/spreadsheets/d/" + "A" * 32 + "/edit\n",
                encoding="utf-8",
            )
            blocklist = root / "blocklist.txt"
            blocklist.write_text("PRIVATE_LITERAL\n", encoding="utf-8")
            errors = MODULE.audit(starter, blocklist)
            self.assertTrue(any("blocked production marker" in error for error in errors))
            self.assertTrue(any("email address" in error for error in errors))
            self.assertTrue(any("Google resource URL" in error for error in errors))

    def test_symlink_and_authority_id_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, tempfile.TemporaryDirectory() as outside:
            root = Path(tempdir)
            starter = root / "starter"
            starter.mkdir()
            target = Path(outside) / "outside.md"
            target.write_text("clean\n", encoding="utf-8")
            try:
                os.symlink(target, starter / "linked.md")
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            (starter / "config.md").write_text(
                "Authority registry ID: `" + "A" * 32 + "`\n",
                encoding="utf-8",
            )
            blocklist = root / "blocklist.txt"
            blocklist.write_text("", encoding="utf-8")
            errors = MODULE.audit(starter, blocklist)
            self.assertTrue(any("symlinks are forbidden" in error for error in errors))
            self.assertTrue(any("deployment authority ID" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
