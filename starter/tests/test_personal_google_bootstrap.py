from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "starter" / "life-planner" / "scripts" / "google_bootstrap.py"
SPEC = importlib.util.spec_from_file_location("google_bootstrap", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class PersonalGoogleBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.blueprint = json.loads(
            (ROOT / "starter" / "life-planner" / "assets" / "personal-google-blueprint.json").read_text(encoding="utf-8")
        )
        self.questions = json.loads((ROOT / "starter" / "questions.json").read_text(encoding="utf-8"))
        self.config = {
            "deployment_uuid": "8fdedec6-4d2c-4c5d-8590-df46fb6b4811",
            "deployment_label": "Beta",
            "owner_uuid": "327dfaa4-dd58-42d3-a875-aa211f575d85",
            "owner_display_name": "Beta User",
            "canonical_timezone": "America/New_York",
            "source_repository": "example/personal-organizer",
            "source_commit": "a" * 40,
            "enabled_modules": ["planning", "appointments"],
            "google_identity": "beta@example.com",
            "gmail_enabled": True,
            "calendar_enabled": True,
            "scheduled_dispatch_enabled": True,
            "generated_at": "2026-08-25T20:00:00-04:00",
        }

    def plan(self):
        return subject.build_plan(self.config, self.blueprint, self.questions)

    def observed(self, plan):
        workbooks = {}
        for workbook in plan["workbooks"]:
            workbooks[workbook["logical_id"]] = {
                "title": workbook["title"],
                "native_google_sheets": True,
                "spreadsheet_timezone": workbook["spreadsheet_timezone"],
                "provider_id": "sheet-" + workbook["module_id"],
                "url": "https://example.invalid/spreadsheet/" + workbook["module_id"],
                "tabs": {
                    tab["name"]: {
                        "values": [tab["headers"]] + [
                            [row.get(header, "") for header in tab["headers"]]
                            for row in tab["rows"]
                        ],
                    }
                    for tab in workbook["tabs"]
                },
            }
        return {
            "profiles": {"drive": "beta@example.com", "gmail": "beta@example.com", "calendar": "beta@example.com"},
            "source": {
                "repository": "example/personal-organizer",
                "head_commit": "a" * 40,
                "read_verified": True,
                "write_verified": True,
                "remote_readback_verified": True,
                "ci_green": True,
            },
            "workbooks": workbooks,
            "folders": {
                folder["logical_id"]: {
                    "name": folder["name"],
                    "provider_id": "id-" + folder["logical_id"],
                    "url": "https://example.invalid/folder/" + folder["logical_id"],
                }
                for folder in plan["folders"]
            },
            "gmail": {"read_verified": True},
            "calendar": {
                "read_verified": True,
                "write_verified": True,
                "readback_verified": True,
                "test_marker": plan["calendar_test"]["marker"],
                "event_id": "event-1",
            },
            "schedule": {"definition_readback": True, "canonical_clock_gate": True, "observed_firing": True},
        }

    def test_blueprint_and_plan_are_valid_and_complete(self) -> None:
        subject.validate_blueprint(self.blueprint)
        plan = self.plan()
        self.assertEqual(["core", "planning", "appointments"], plan["selected_modules"])
        self.assertEqual(3, len(plan["workbooks"]))
        core = next(item for item in plan["workbooks"] if item["module_id"] == "core")
        tabs = {tab["name"]: tab for tab in core["tabs"]}
        self.assertEqual(self.config["deployment_uuid"], tabs["Metadata"]["rows"][0]["Deployment UUID"])
        self.assertEqual(self.config["owner_uuid"], tabs["People"]["rows"][0]["Person UUID"])
        self.assertEqual(
            sum(len(section["questions"]) for section in self.questions["sections"]),
            len(tabs["Interview Ledger"]["rows"]),
        )
        self.assertRegex(plan["plan_sha256"], r"^[0-9a-f]{64}$")

    def test_optional_modules_add_only_their_declared_workbooks(self) -> None:
        self.config["enabled_modules"] = ["meal-planning", "commerce", "assets", "job-watch", "work-travel"]
        plan = self.plan()
        self.assertEqual(
            {"core", "meal-planning", "commerce", "assets", "job-watch", "work-travel"},
            {item["module_id"] for item in plan["workbooks"]},
        )
        self.assertIn("Technical Specifications", {tab["name"] for workbook in plan["workbooks"] for tab in workbook["tabs"]})

    def test_unknown_module_invalid_timezone_and_nonboolean_gate_fail_closed(self) -> None:
        for key, value in (
            ("enabled_modules", ["magic"]),
            ("canonical_timezone", "Eastern-ish"),
            ("gmail_enabled", "yes"),
        ):
            broken = deepcopy(self.config)
            broken[key] = value
            with self.subTest(key=key), self.assertRaises(subject.BootstrapError):
                subject.build_plan(broken, self.blueprint, self.questions)

    def test_exact_readback_is_ready(self) -> None:
        plan = self.plan()
        result = subject.verify(plan, self.observed(plan))
        self.assertEqual("ready", result["decision"])
        self.assertTrue(result["ready_for_manual_use"])
        self.assertTrue(result["scheduled_dispatch_selected"])
        self.assertTrue(result["ready_for_scheduled_use"])

    def test_unselected_scheduler_is_not_reported_ready(self) -> None:
        self.config["scheduled_dispatch_enabled"] = False
        plan = self.plan()
        result = subject.verify(plan, self.observed(plan))
        self.assertEqual("ready", result["decision"])
        self.assertTrue(result["ready_for_manual_use"])
        self.assertFalse(result["scheduled_dispatch_selected"])
        self.assertFalse(result["ready_for_scheduled_use"])

    def test_missing_or_drifted_core_provider_evidence_blocks(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        observed["workbooks"]["workbook:core"]["tabs"]["People"]["values"][0] = ["wrong"]
        observed["workbooks"]["workbook:core"]["spreadsheet_timezone"] = "America/Los_Angeles"
        observed["source"]["remote_readback_verified"] = False
        result = subject.verify(plan, observed)
        self.assertEqual("blocked", result["decision"])
        self.assertIn("header-mismatch-workbook:core-People", result["blocks"])
        self.assertIn("spreadsheet-timezone-mismatch-workbook:core", result["blocks"])
        self.assertIn("source-remote-readback-verified-missing", result["blocks"])

    def test_seed_drift_and_plan_tampering_fail_closed(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        people = observed["workbooks"]["workbook:core"]["tabs"]["People"]["values"]
        people[1][0] = "different-owner"
        result = subject.verify(plan, observed)
        self.assertEqual("blocked", result["decision"])
        self.assertIn("seed-mismatch-workbook:core-People", result["blocks"])

        plan["deployment"]["canonical_timezone"] = "America/Chicago"
        with self.assertRaises(subject.BootstrapError):
            subject.verify(plan, observed)

    def test_google_null_blanks_and_excel_serial_timestamp_match_seed(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        metadata = observed["workbooks"]["workbook:core"]["tabs"]["Metadata"]["values"]
        metadata[1][3] = 46260.0
        interview = observed["workbooks"]["workbook:core"]["tabs"]["Interview Ledger"]["values"]
        interview[1][5] = None
        result = subject.verify(plan, observed)
        self.assertEqual("ready", result["decision"])

    def test_optional_google_and_first_firing_failures_degrade_only(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        observed["gmail"]["read_verified"] = False
        observed["calendar"]["event_id"] = ""
        observed["schedule"]["observed_firing"] = False
        result = subject.verify(plan, observed)
        self.assertEqual("degraded", result["decision"])
        self.assertTrue(result["ready_for_manual_use"])
        self.assertFalse(result["ready_for_scheduled_use"])
        self.assertIn("schedule-awaiting-observed-firing", result["degradations"])

    def test_profile_identity_mismatch_blocks_core_and_degrades_optional_apps(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        observed["profiles"] = {"drive": "wrong@example.com", "gmail": "wrong@example.com", "calendar": "wrong@example.com"}
        result = subject.verify(plan, observed)
        self.assertEqual("blocked", result["decision"])
        self.assertIn("google-drive-identity-mismatch", result["blocks"])
        self.assertIn("gmail-identity-mismatch", result["degradations"])

    def test_cli_strict_rejects_degraded_readback(self) -> None:
        plan = self.plan()
        observed = self.observed(plan)
        observed["schedule"]["observed_firing"] = False
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "plan.json"
            observed_path = root / "observed.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            observed_path.write_text(json.dumps(observed), encoding="utf-8")
            original = sys.argv
            try:
                sys.argv = [str(SCRIPT), "verify", "--plan", str(plan_path), "--observed", str(observed_path), "--strict"]
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(3, subject.main())
            finally:
                sys.argv = original


if __name__ == "__main__":
    unittest.main()
