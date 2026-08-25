from __future__ import annotations

import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_public_source", ROOT / "scripts/audit_public_source.py")
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(AUDIT)


class PublicSourceAuditTests(unittest.TestCase):
    def test_clean_source_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "README.md").write_text("No credentials here.\n", encoding="utf-8")
            self.assertEqual([], AUDIT.audit(root))

    def test_missing_root_does_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            missing = Path(tempdir) / "missing"
            self.assertTrue(any("not a directory" in error for error in AUDIT.audit(missing)))

    def test_private_key_is_rejected(self) -> None:
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "bad.txt").write_text(marker + "\nnot-real-but-forbidden\n", encoding="utf-8")
            errors = AUDIT.audit(root)
            self.assertTrue(any("private key" in error for error in errors))

    def test_token_like_secret_is_rejected(self) -> None:
        token = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyzABCDEF1234567890"
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "bad.txt").write_text(f"token = '{token}'\n", encoding="utf-8")
            errors = AUDIT.audit(root)
            self.assertTrue(any("GitHub token" in error or "literal secret" in error for error in errors))

    def test_placeholder_assignment_is_allowed(self) -> None:
        errors = AUDIT.scan_text('client_secret = "YOUR_CLIENT_SECRET_PLACEHOLDER"', "fixture")
        self.assertEqual([], errors)

    def test_blocked_mutable_export_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            (root / "live.sqlite").write_bytes(b"sqlite")
            errors = AUDIT.audit(root)
            self.assertTrue(any("mutable-data file type" in error for error in errors))

    def test_valid_luhn_card_number_is_rejected(self) -> None:
        number = "4111" + " 1111" + " 1111" + " 1111"
        errors = AUDIT.scan_text("card " + number, "fixture")
        self.assertTrue(any("payment-card" in error for error in errors))

    def test_concrete_personal_email_is_rejected(self) -> None:
        errors = AUDIT.scan_text("forwarded by owner@personal.invalid", "fixture")
        self.assertTrue(any("personal email" in error for error in errors))
        self.assertEqual([], AUDIT.scan_text("contact@example.com", "fixture"))

    def test_concrete_google_resource_url_is_rejected(self) -> None:
        url = "https://docs.google.com/spreadsheets/d/" + "A" * 32 + "/edit"
        errors = AUDIT.scan_text(url, "fixture")
        self.assertTrue(any("Google resource URL" in error for error in errors))

    def test_concrete_authority_id_is_rejected(self) -> None:
        text = "Mileage authority sheet ID: `" + "A" * 32 + "`"
        errors = AUDIT.scan_text(text, "fixture")
        self.assertTrue(any("deployment authority ID" in error for error in errors))

    def test_deployment_override_document_is_rejected(self) -> None:
        errors = AUDIT.scan_text("# Current Deployment Overrides\n", "fixture")
        self.assertTrue(any("deployment-only" in error for error in errors))

    def test_symlink_is_rejected_in_public_source(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, tempfile.TemporaryDirectory() as outside:
            root = Path(tempdir)
            target = Path(outside) / "target.txt"
            target.write_text("ordinary text\n", encoding="utf-8")
            try:
                os.symlink(target, root / "link.txt")
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            errors = AUDIT.audit(root)
            self.assertTrue(any("forbidden symlink" in error for error in errors))

    def test_untracked_candidate_file_is_scanned_inside_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "README.md").write_text("clean\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(root), "add", "README.md"], check=True)
            marker = "-----BEGIN " + "PRIVATE KEY-----"
            (root / "candidate.txt").write_text(marker + "\n", encoding="utf-8")
            errors = AUDIT.audit(root)
            self.assertTrue(any("candidate.txt" in error and "private key" in error for error in errors))

    def test_historical_blocked_binary_path_is_rejected_without_text_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "archive.p12").write_bytes(b"\x00\x01\x02")
            subprocess.run(["git", "-C", str(root), "add", "archive.p12"], check=True)
            subprocess.run(
                [
                    "git", "-C", str(root), "-c", "user.name=Audit Test",
                    "-c", "user.email=audit@example.com", "commit", "-qm", "fixture",
                ],
                check=True,
            )
            errors = AUDIT.audit_history(root)
            self.assertTrue(any("archive.p12" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
