from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "policy_fingerprint.py"
SPEC = importlib.util.spec_from_file_location("policy_fingerprint_under_test", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class PolicyFingerprintTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        skill = root / "skill"
        (skill / "references").mkdir(parents=True)
        (skill / "scripts").mkdir()
        (skill / "agents").mkdir()
        (skill / "assets").mkdir()
        (skill / "SKILL.md").write_text("policy\n", encoding="utf-8")
        (skill / "references" / "rule.md").write_text("rule\n", encoding="utf-8")
        (skill / "scripts" / "engine.py").write_text("VALUE = 1\n", encoding="utf-8")
        (skill / "scripts" / "test_engine.py").write_text("ignored test\n", encoding="utf-8")
        (skill / "agents" / "openai.yaml").write_text(
            'interface:\n'
            '  display_name: "Test Skill"\n'
            '  short_description: "Test skill metadata contract"\n'
            '  icon_small: "./assets/icon.svg"\n'
            '  icon_large: "./assets/icon.svg"\n'
            '  brand_color: "#123456"\n'
            '  default_prompt: "Use $test-skill to test metadata."\n'
            'policy:\n'
            '  allow_implicit_invocation: true\n',
            encoding="utf-8",
        )
        icon = b"<svg/>\n"
        (skill / "assets" / "icon.svg").write_bytes(icon)
        (skill / "assets" / "icon.source.sha256").write_text(
            hashlib.sha256(icon).hexdigest() + "\n", encoding="utf-8"
        )
        return skill

    def test_fingerprint_changes_with_runtime_content_but_ignores_tests(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            initial = MODULE.compute(skill)
            (skill / "scripts" / "test_engine.py").write_text("changed test\n", encoding="utf-8")
            self.assertEqual(initial, MODULE.compute(skill))
            (skill / "scripts" / "engine.py").write_text("VALUE = 2\n", encoding="utf-8")
            self.assertNotEqual(initial, MODULE.compute(skill))

    def test_agent_metadata_and_assets_are_part_of_deployment_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            initial = MODULE.compute(skill)
            metadata = skill / "agents" / "openai.yaml"
            metadata.write_text(
                metadata.read_text(encoding="utf-8").replace("Test Skill", "Changed Skill"),
                encoding="utf-8",
            )
            self.assertNotEqual(initial, MODULE.compute(skill))
            changed = MODULE.compute(skill)
            changed_icon = b"<svg>changed</svg>\n"
            (skill / "assets" / "icon.svg").write_bytes(changed_icon)
            with self.assertRaisesRegex(ValueError, "source icon digest mismatch"):
                MODULE.compute(skill)
            (skill / "assets" / "icon.source.sha256").write_text(
                hashlib.sha256(changed_icon).hexdigest() + "\n", encoding="utf-8"
            )
            self.assertNotEqual(changed, MODULE.compute(skill))

    def test_materialized_agent_metadata_has_same_semantic_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            initial = MODULE.compute(skill)
            (skill / "agents" / "openai.yaml").write_text(
                "interface:\n"
                "  display_name: Test Skill\n"
                "  short_description: Test skill metadata contract\n"
                "  icon_small: assets/icon.svg\n"
                "  icon_large: assets/icon.svg\n"
                "  brand_color: '#123456'\n"
                "  default_prompt: Use $test-skill to test\n"
                "    metadata.\n"
                "policy:\n"
                "  allow_implicit_invocation: true\n"
                "  products:\n"
                "  - chatgpt\n"
                "  - codex\n",
                encoding="utf-8",
            )
            (skill / "assets" / "icon.svg").write_text(
                "<svg>provider-rendered-replacement</svg>\n", encoding="utf-8"
            )
            self.assertEqual(initial, MODULE.compute(skill))

    def test_missing_or_invalid_icon_source_digest_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            (skill / "assets" / "icon.source.sha256").unlink()
            with self.assertRaises(FileNotFoundError):
                MODULE.compute(skill)
            (skill / "assets" / "icon.source.sha256").write_text("invalid\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid source icon digest"):
                MODULE.compute(skill)

    def test_invalid_agent_metadata_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            (skill / "agents" / "openai.yaml").write_text("interface:\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lacks interface fields"):
                MODULE.compute(skill)

    def test_private_deployment_authority_map_is_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            initial = MODULE.compute(skill)
            (skill / "references" / "deployment-authorities.md").write_text(
                "private deployment values\n", encoding="utf-8"
            )
            self.assertEqual(initial, MODULE.compute(skill))

    def test_symlinked_policy_source_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, tempfile.TemporaryDirectory() as outside:
            skill = self.fixture(Path(tempdir))
            link = skill / "references" / "escape.md"
            target = Path(outside) / "private.md"
            target.write_text("private\n", encoding="utf-8")
            try:
                os.symlink(target, link)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            with self.assertRaisesRegex(ValueError, "must not be a symlink"):
                MODULE.compute(skill)

    def test_cli_missing_root_fails_without_traceback(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "/definitely/missing/skill"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("error:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_cli_accepts_relative_skill_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            skill = self.fixture(Path(tempdir))
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "skill"],
                cwd=tempdir,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), MODULE.compute(skill))


if __name__ == "__main__":
    unittest.main()
