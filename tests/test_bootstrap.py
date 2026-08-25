from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("bootstrap", ROOT / "scripts/bootstrap.py")
BOOTSTRAP = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(BOOTSTRAP)


class BootstrapTests(unittest.TestCase):
    def test_example_renders_without_tokens(self) -> None:
        config = BOOTSTRAP.load_config(ROOT / "starter/config.example.json")
        self.assertEqual(set(config), BOOTSTRAP.CONFIG_KEYS)
        template = (ROOT / "starter/INSTRUCTIONS.md.tmpl").read_text(encoding="utf-8")
        rendered = BOOTSTRAP.render(template, config)
        self.assertNotIn("{{", rendered)
        self.assertIn("$my-ops-policy", rendered)
        self.assertIn("GOOGLE_SHEETS_DEFAULT_OR_SUPPORTED_DATABASE", rendered)
        self.assertIn("REQUIRED_IN_STRUCTURED_STATE_STORE", rendered)
        self.assertIn("IANA_TIMEZONE_CONVERSION_NEVER_DEVICE_TIME_OR_STATIC_OFFSET", rendered)
        self.assertIn("OBSERVED_RUNTIME_AND_DEPLOYMENT", rendered)
        self.assertIn("PERSONAL_BROWSER_ENTERPRISE_MANAGED_OR_PORTABLE_MANUAL", rendered)
        self.assertIn("SELECT_PERSONAL_ORGANIZATION_GIT_OR_MANAGED_SOURCE", rendered)

    def test_missing_key_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing configuration keys"):
            BOOTSTRAP.render("Hello {{NAME}}", {})

    def test_nested_config_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "config.json"
            path.write_text(json.dumps({"BAD": {"nested": True}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must be a scalar"):
                BOOTSTRAP.load_config(path)

    def test_unknown_config_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "config.json"
            config = json.loads((ROOT / "starter/config.example.json").read_text())
            config["TYPOO"] = "bad"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsupported keys: TYPOO"):
                BOOTSTRAP.load_config(path)

    def test_missing_schema_key_is_rejected_even_when_template_does_not_use_it(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "config.json"
            config = json.loads((ROOT / "starter/config.example.json").read_text())
            del config["ASSET_ACQUISITION"]
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing supported keys: ASSET_ACQUISITION"):
                BOOTSTRAP.load_config(path)

    def test_cli_reports_invalid_json_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "config.json"
            path.write_text("null", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/bootstrap.py"), "--config", str(path),
                 "--template", str(ROOT / "starter/INSTRUCTIONS.md.tmpl"), "--check"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("configuration must be a JSON object", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_failed_render_does_not_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            directory = Path(tempdir)
            config_path = directory / "config.json"
            config_path.write_text((ROOT / "starter/config.example.json").read_text(), encoding="utf-8")
            template_path = directory / "template.md"
            template_path.write_text("{{NOT_A_SUPPORTED_VALUE}}", encoding="utf-8")
            output_path = directory / "output.md"
            output_path.write_text("known good", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/bootstrap.py"), "--config", str(config_path),
                 "--template", str(template_path), "--output", str(output_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "known good")

    def test_human_first_boot_is_safe_bounded_and_fail_forward(self) -> None:
        guide = (ROOT / "starter/START_HERE.md").read_text(encoding="utf-8")
        lower = guide.lower()
        self.assertIn("Minimum Useful Setup", guide)
        self.assertIn("Start now by asking only the four kickoff questions", guide)
        self.assertIn("explicit approval", lower)
        self.assertIn("partial cancellation", lower)
        self.assertIn("timezone is permanently authoritative", lower)
        self.assertIn("exact local times", lower)
        self.assertIn("recipe library", lower)
        self.assertIn("job title", lower)
        self.assertIn("mark HOME/ROAD bypassed", guide)
        self.assertIn("driving/trucking", lower)
        self.assertIn("true replacement", lower)
        self.assertIn("automatically update validation, commit, and push", guide)
        self.assertIn("Google Sheets", guide)
        self.assertIn("Google Drive", guide)
        self.assertIn("Interview Ledger", guide)
        self.assertIn("do not silently abandon", lower)
        self.assertIn("Do you want help with meal planning?", guide)
        self.assertIn("ZoneInfo", guide)
        self.assertIn("public-source audit", lower)
        self.assertNotIn("https://" + "docs.google.com/spreadsheets/d/", guide)
        self.assertNotRegex(guide, r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|yahoo)\.com")
        self.assertLess(len(guide), 12000)


if __name__ == "__main__":
    unittest.main()
