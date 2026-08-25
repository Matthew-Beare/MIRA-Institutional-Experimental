from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "starter" / "life-planner" / "scripts" / "brief_schedule.py"
SPEC = importlib.util.spec_from_file_location("brief_schedule", SCRIPT)
assert SPEC and SPEC.loader
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class BriefScheduleTests(unittest.TestCase):
    def config(self):
        return {
            "schema_version": 1,
            "canonical_timezone": "America/Denver",
            "briefs": [
                {
                    "id": "first",
                    "time": "06:17",
                    "enabled": True,
                    "notification_mode": "notify",
                },
                {
                    "id": "second",
                    "time": "21:43",
                    "enabled": True,
                    "notification_mode": "quiet",
                },
            ],
        }

    def test_arbitrary_user_times_are_preserved_exactly(self) -> None:
        desired = subject.desired_dispatch(self.config())
        self.assertEqual("America/Denver", desired["canonical_timezone"])
        self.assertEqual(["06:17", "21:43"], [row["time"] for row in desired["slots"]])

    def test_no_briefs_is_valid_and_has_no_default_time(self) -> None:
        config = {
            "schema_version": 1,
            "canonical_timezone": "Europe/London",
            "briefs": [],
        }
        desired = subject.desired_dispatch(config)
        self.assertEqual([], desired["slots"])

    def test_bad_or_duplicate_times_fail_closed(self) -> None:
        for time_value in ("6:17", "24:00", "morning"):
            config = self.config()
            config["briefs"][0]["time"] = time_value
            with self.subTest(time=time_value), self.assertRaises(subject.ScheduleError):
                subject.normalize(config)

        config = self.config()
        config["briefs"][1]["time"] = config["briefs"][0]["time"]
        with self.assertRaises(subject.ScheduleError):
            subject.normalize(config)

    def test_scheduler_readback_must_match_user_config_exactly(self) -> None:
        config = self.config()
        desired = subject.desired_dispatch(config)
        observed = {
            "definition_readback": True,
            "canonical_timezone": desired["canonical_timezone"],
            "slots": desired["slots"],
            "observed_firing": True,
        }
        self.assertEqual("ready", subject.verify(config, observed)["decision"])

        observed["slots"][0]["time"] = "06:18"
        result = subject.verify(config, observed)
        self.assertEqual("blocked", result["decision"])
        self.assertIn("schedule-slots-mismatch", result["blocks"])

    def test_first_firing_is_evidence_not_configuration(self) -> None:
        config = self.config()
        desired = subject.desired_dispatch(config)
        result = subject.verify(
            config,
            {
                "definition_readback": True,
                "canonical_timezone": desired["canonical_timezone"],
                "slots": desired["slots"],
                "observed_firing": False,
            },
        )
        self.assertEqual("degraded", result["decision"])
        self.assertEqual(["schedule-awaiting-observed-firing"], result["degradations"])

    def test_portable_policy_requires_user_choice_and_versioned_change(self) -> None:
        reference = (
            ROOT / "starter" / "life-planner" / "references" / "brief-schedule.md"
        ).read_text(encoding="utf-8")
        control = (
            ROOT / "starter" / "life-planner" / "references" / "control-cycle.md"
        ).read_text(encoding="utf-8")
        onboarding = (
            ROOT / "starter" / "life-planner" / "references" / "personal-google-onboarding.md"
        ).read_text(encoding="utf-8")
        lifecycle = (ROOT / "starter" / "PERSONAL_FORK_LIFECYCLE.md").read_text(
            encoding="utf-8"
        )
        config = json.loads((ROOT / "starter" / "config.example.json").read_text(encoding="utf-8"))

        self.assertIn("no stock brief time", reference.lower())
        self.assertIn("no product-default brief time", control.lower())
        self.assertIn("do not offer, infer, or inherit a stock time", onboarding.lower())
        self.assertIn("commit/push/read", onboarding.lower())
        self.assertIn("changed recurring brief time", lifecycle.lower())
        self.assertEqual(
            "EXPLICIT_USER_SELECTED_LOCAL_TIMES_OR_DISABLED_NO_PRODUCT_DEFAULT",
            config["BRIEF_SLOTS"],
        )
        self.assertIn("standing authorization", config["AUTO_VERSIONING"].lower())


if __name__ == "__main__":
    unittest.main()
