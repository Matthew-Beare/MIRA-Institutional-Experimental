from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "reminder_delivery.py"
spec = importlib.util.spec_from_file_location("reminder_delivery", MODULE)
subject = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(subject)


def reminder(**overrides):
    row = {
        "reminder_uuid": "4d7c6dd7-875b-4285-892c-0b0191f99b30",
        "kind": "appointment",
        "title": "Cardiology appointment",
        "fire_at": "2026-08-26T09:00:00-04:00",
        "triggers": ["relative"],
    }
    row.update(overrides)
    return row


class ReminderDeliveryTests(unittest.TestCase):
    def test_visual_delivery_exists_without_spoken_opt_in(self):
        result = subject.project({"reminders": [reminder()], "verified_capabilities": [], "spoken_enabled": False})
        self.assertEqual("ready", result["status"])
        self.assertEqual(["visual_notification"], [row["channel"] for row in result["delivery_intents"]])

    def test_spoken_delivery_requires_verified_capability(self):
        result = subject.project({"reminders": [reminder()], "verified_capabilities": [], "spoken_enabled": True})
        self.assertEqual("degraded", result["status"])
        self.assertEqual(1, len(result["warnings"]))
        self.assertEqual("spoken_notification", result["warnings"][0]["missing_capability"])

    def test_title_mode_generates_requested_one_hour_phrase(self):
        result = subject.project({
            "reminders": [reminder()],
            "verified_capabilities": ["spoken_notification"],
            "spoken_enabled": True,
            "spoken_detail_mode": "title",
        })
        spoken = [row for row in result["delivery_intents"] if row["channel"] == "spoken_notification"]
        self.assertEqual("Cardiology appointment in one hour.", spoken[0]["speech_text"])

    def test_generic_is_privacy_default(self):
        result = subject.project({
            "reminders": [reminder(triggers=["day_before"])],
            "verified_capabilities": ["spoken_notification"],
            "spoken_enabled": True,
        })
        spoken = [row for row in result["delivery_intents"] if row["channel"] == "spoken_notification"]
        self.assertEqual("You have an appointment tomorrow.", spoken[0]["speech_text"])

    def test_invalid_detail_mode_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "generic or title"):
            subject.project({
                "reminders": [reminder()],
                "verified_capabilities": ["spoken_notification"],
                "spoken_enabled": True,
                "spoken_detail_mode": "leak_everything",
            })


if __name__ == "__main__":
    unittest.main()
