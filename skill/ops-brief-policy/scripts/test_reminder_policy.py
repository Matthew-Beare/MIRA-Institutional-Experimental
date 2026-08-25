from __future__ import annotations

import copy
import io
import json
import sys
import unittest
from unittest import mock

import reminder_policy as subject


REGIMEN = "8e3c18e8-64b3-4372-8635-e970672f6c77"


def appointment(**overrides):
    row = {
        "event_id": "calendar-event-123",
        "title": "Cardiology appointment",
        "start_at": "2026-08-26T10:00:00-04:00",
        "status": "confirmed",
        "reminder_enabled": True,
        "source_authority": "google_calendar",
        "source_record_id": "calendar-event-123:revision-7",
    }
    row.update(overrides)
    return row


def medication(**overrides):
    row = {
        "regimen_uuid": REGIMEN,
        "display_name": "Recorded medication",
        "instructions_text": "Follow the recorded label instructions.",
        "schedule_times": ["08:00", "20:00"],
        "schedule_confirmed": True,
        "status": "active",
        "reminder_enabled": True,
        "source_authority": "prescription_label",
        "source_record_id": "label-photo:fixture-1",
    }
    row.update(overrides)
    return row


def payload(**overrides):
    row = {
        "timezone": "America/New_York",
        "now": "2026-08-24T16:00:00-04:00",
        "window_start": "2026-08-24T16:00:00-04:00",
        "window_end": "2026-08-27T00:00:00-04:00",
        "appointment_reminders_enabled": True,
        "medication_reminders_enabled": False,
        "caregiver_sharing_enabled": False,
        "appointments": [appointment()],
        "medications": [],
    }
    row.update(overrides)
    return row


class ReminderPolicyTests(unittest.TestCase):
    def test_plans_day_before_morning_of_and_one_hour_before(self):
        result = subject.plan(payload())
        reminders = result["reminders"]
        self.assertEqual(3, len(reminders))
        self.assertEqual(
            ["2026-08-25T18:00:00-04:00", "2026-08-26T08:00:00-04:00", "2026-08-26T09:00:00-04:00"],
            [row["fire_at"] for row in reminders],
        )
        self.assertEqual(
            [["day_before"], ["morning_of"], ["relative"]],
            [row["triggers"] for row in reminders],
        )
        self.assertEqual("single_control_cycle_projection_no_per_event_automations", result["delivery_model"])

    def test_equal_reminder_times_are_deduplicated_with_both_triggers(self):
        data = payload(appointment_reminder_profile={
            "day_before_local_time": "18:00",
            "morning_of_local_time": "09:00",
            "relative_minutes_before": 60,
        })
        result = subject.plan(data)
        self.assertEqual(2, len(result["reminders"]))
        self.assertEqual(["morning_of", "relative"], result["reminders"][1]["triggers"])

    def test_morning_reminder_after_early_appointment_is_suppressed(self):
        data = payload(appointments=[appointment(start_at="2026-08-26T07:30:00-04:00")])
        result = subject.plan(data)
        self.assertEqual(2, len(result["reminders"]))
        self.assertTrue(any(row.get("trigger") == "morning_of" for row in result["suppressed"]))

    def test_cancelled_or_per_event_disabled_appointment_does_not_remind(self):
        for row in (appointment(status="cancelled"), appointment(reminder_enabled=False)):
            with self.subTest(row=row):
                result = subject.plan(payload(appointments=[row]))
                self.assertEqual([], result["reminders"])
                self.assertEqual("cancelled_or_disabled", result["suppressed"][0]["reason"])

    def test_disabled_service_never_silently_activates(self):
        result = subject.plan(payload(appointment_reminders_enabled=False))
        self.assertEqual([], result["reminders"])
        self.assertFalse(result["appointment_reminders_enabled"])

    def test_boolean_strings_are_explicitly_parsed_and_garbage_rejected(self):
        result = subject.plan(payload(appointment_reminders_enabled="yes"))
        self.assertTrue(result["appointment_reminders_enabled"])
        with self.assertRaisesRegex(ValueError, "explicit boolean"):
            subject.plan(payload(appointment_reminders_enabled="maybe"))

    def test_plans_only_explicit_confirmed_medication_schedule(self):
        data = payload(
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication()],
            window_start="2026-08-25T00:00:00-04:00",
            window_end="2026-08-26T00:00:00-04:00",
        )
        result = subject.plan(data)
        self.assertEqual(2, len(result["reminders"]))
        self.assertEqual(["08:00", "20:00"], [row["fire_at"][11:16] for row in result["reminders"]])
        self.assertTrue(result["safety"]["dose_or_schedule_inference_prohibited"])
        self.assertTrue(result["safety"]["missed_dose_advice_prohibited"])

    def test_active_medication_requires_confirmed_schedule(self):
        data = payload(
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication(schedule_confirmed=False)],
        )
        with self.assertRaisesRegex(ValueError, "explicitly confirmed"):
            subject.plan(data)

    def test_medication_timing_rejects_untrusted_or_inferred_source(self):
        data = payload(
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication(source_authority="assistant_inference")],
        )
        with self.assertRaisesRegex(ValueError, "not permitted"):
            subject.plan(data)

    def test_medication_schedule_requires_real_times_without_duplicates(self):
        for schedule, message in (([], "non-empty"), (["08:00", "08:00"], "duplicates")):
            data = payload(
                appointment_reminders_enabled=False,
                medication_reminders_enabled=True,
                appointments=[],
                medications=[medication(schedule_times=schedule)],
            )
            with self.subTest(schedule=schedule):
                with self.assertRaisesRegex(ValueError, message):
                    subject.plan(data)

    def test_paused_medication_is_suppressed(self):
        result = subject.plan(payload(
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication(status="paused")],
        ))
        self.assertEqual([], result["reminders"])
        self.assertEqual("inactive_or_disabled", result["suppressed"][0]["reason"])

    def test_caregiver_sharing_is_opt_in_and_requires_recipient(self):
        with self.assertRaisesRegex(ValueError, "caregiver_recipient_id"):
            subject.plan(payload(caregiver_sharing_enabled=True))
        result = subject.plan(payload(
            caregiver_sharing_enabled=True,
            caregiver_recipient_id="private-person-uuid",
        ))
        self.assertTrue(all(row["audience"] == "caregiver_and_user" for row in result["reminders"]))

    def test_canonical_timezone_controls_output_even_when_input_is_utc(self):
        result = subject.plan(payload(
            now="2026-08-24T20:00:00+00:00",
            window_start="2026-08-24T20:00:00+00:00",
            window_end="2026-08-27T04:00:00+00:00",
        ))
        self.assertEqual("America/New_York", result["timezone"])
        self.assertTrue(all(row["fire_at"].endswith("-04:00") for row in result["reminders"]))

    def test_fixed_offset_or_abbreviation_timezone_is_rejected(self):
        for zone in ("EST", "+05:00"):
            with self.subTest(zone=zone):
                with self.assertRaisesRegex(ValueError, "IANA"):
                    subject.plan(payload(timezone=zone))

    def test_utc_is_a_valid_named_iana_zone(self):
        result = subject.plan(payload(
            timezone="UTC",
            now="2026-08-24T20:00:00+00:00",
            window_start="2026-08-24T20:00:00+00:00",
            window_end="2026-08-27T04:00:00+00:00",
        ))
        self.assertEqual("UTC", result["timezone"])

    def test_nonexistent_dst_medication_time_fails_loudly(self):
        data = payload(
            now="2026-03-07T00:00:00-05:00",
            window_start="2026-03-07T00:00:00-05:00",
            window_end="2026-03-09T00:00:00-04:00",
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication(schedule_times=["02:30"])],
        )
        with self.assertRaisesRegex(ValueError, "nonexistent local time"):
            subject.plan(data)

    def test_ambiguous_dst_medication_time_fails_loudly(self):
        data = payload(
            now="2026-10-31T00:00:00-04:00",
            window_start="2026-10-31T00:00:00-04:00",
            window_end="2026-11-02T00:00:00-05:00",
            appointment_reminders_enabled=False,
            medication_reminders_enabled=True,
            appointments=[],
            medications=[medication(schedule_times=["01:30"])],
        )
        with self.assertRaisesRegex(ValueError, "ambiguous during a clock change"):
            subject.plan(data)

    def test_horizon_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "must not exceed"):
            subject.plan(payload(window_end="2026-09-30T00:00:00-04:00"))

    def test_invalid_window_and_profile_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "window_start must be before"):
            subject.plan(payload(window_end="2026-08-24T15:00:00-04:00"))
        with self.assertRaisesRegex(ValueError, "unknown fields"):
            subject.plan(payload(appointment_reminder_profile={"magic": True}))
        with self.assertRaisesRegex(ValueError, "must be 1..10080"):
            subject.plan(payload(appointment_reminder_profile={
                "day_before_local_time": "18:00",
                "morning_of_local_time": "08:00",
                "relative_minutes_before": 0,
            }))

    def test_duplicate_appointment_identity_and_bad_container_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicates an appointment identity"):
            subject.plan(payload(appointments=[appointment(), appointment()]))
        with self.assertRaisesRegex(ValueError, "appointments must be a list"):
            subject.plan(payload(appointments={}))

    def test_deterministic_replay_has_identical_ids(self):
        data = payload()
        first = subject.plan(copy.deepcopy(data))
        second = subject.plan(copy.deepcopy(data))
        self.assertEqual(
            [row["reminder_uuid"] for row in first["reminders"]],
            [row["reminder_uuid"] for row in second["reminders"]],
        )

    def test_cli_success_and_invalid_json_failure(self):
        data = payload()
        with mock.patch.object(sys, "argv", ["reminder_policy.py"]), mock.patch.object(
            sys, "stdin", io.StringIO(json.dumps(data))
        ), mock.patch.object(sys, "stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(0, subject.main())
            self.assertEqual("ok", json.loads(stdout.getvalue())["status"])

        with mock.patch.object(sys, "argv", ["reminder_policy.py"]), mock.patch.object(
            sys, "stdin", io.StringIO("{")
        ), mock.patch.object(sys, "stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(2, subject.main())
            self.assertIn("error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
