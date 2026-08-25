#!/usr/bin/env python3

import contextlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

import ops_policy as runtime

SCRIPT = Path(runtime.__file__).resolve()


def base_payload(now: str) -> dict:
    return {
        "strict_inputs": True,
        "brief_slot": "PM" if "T14:" in now else "AM",
        "now": now,
        "tasks_values": [["Task ID", "Tier", "Classification", "Subsystem", "Task", "Status", "Visibility", "Active From", "Active Through", "Recurrence / State Rule", "Notes", "Updated (ET)"]],
        "control_values": [["Record ID", "Type", "Item", "State", "Starts At (ET)", "Expires At (ET)", "Notes", "Status", "Updated (ET)"]],
        "routes_values": [["Route ID", "Endpoint A", "Endpoint B", "Route A → B", "Route B → A", "Avg A → B (hrs)", "Avg B → A (hrs)", "Paid Miles A → B", "Paid Miles B → A", "Miles Source A → B", "Miles Source B → A", "Operation Profile", "Status", "Notes", "Created (ET)", "Updated (ET)"]],
        "trips_values": [["Trip ID", "Route ID", "Origin", "Destination", "Departure (ET)", "ETA (ET)", "ETA Source", "Current Location", "Location Time (ET)", "Weather Watch", "Watch Expires (ET)", "Status", "Route Override", "Notes", "Updated (ET)"]],
        "travel_settings_values": [
            ["Setting ID", "Setting", "Value", "Notes", "Status", "Updated (ET)"],
            ["CONTEXT-001", "Weekly HOME transition", "Wednesday 16:30", "", "Active"],
            ["CONTEXT-002", "Weekly ROAD transition", "Friday 12:00", "", "Active"],
            ["TRAVEL-014", "Thursday mileage summary", "Enabled", "", "Active"],
        ],
        "mileage_values": [["Entry ID", "Week Ending (Thu)", "Trip ID", "Route ID", "Departure (ET)", "Arrival (ET)", "Origin", "Destination", "Company-Paid Miles", "Rate / Mile", "Gross Pay Estimate", "Miles Source", "Status", "Notes", "Updated (ET)"]],
        "mileage_settings_values": [
            ["Setting", "Value"],
            ["Rate per paid mile", 0.75],
        ],
        "appointments": [],
    }


def add_active_trip(payload: dict) -> None:
    payload["trips_values"].append(
        [
            "TRIP-001",
            "",
            "Terminal A",
            "Terminal B",
            "2026-08-21T16:30:00-04:00",
            "",
            "Unknown",
            "Checkpoint C",
            "2026-08-22T15:20:00-04:00",
            "Off",
            "",
            "Active",
            "I-40 west",
        ]
    )


class PolicyEntryRegressionTests(unittest.TestCase):
    def test_active_trip_survives_weekly_home_boundary(self):
        payload = base_payload("2026-08-26T16:31:00-04:00")
        add_active_trip(payload)
        result = runtime.resolve(payload)
        self.assertEqual(result["mode"], "ROAD")
        self.assertEqual(result["mode_source"], "active_trip")
        self.assertNotEqual(result["status"], "error")

    def test_live_home_override_beats_active_trip(self):
        payload = base_payload("2026-08-26T16:31:00-04:00")
        add_active_trip(payload)
        payload["control_values"].append(
            [
                "CTRL-HOME",
                "Mode Override",
                "Home early",
                "HOME",
                "2026-08-26T16:00:00-04:00",
                "2026-08-28T15:00:00-04:00",
                "",
                "Active",
            ]
        )
        result = runtime.resolve(payload)
        self.assertEqual(result["mode"], "HOME")
        self.assertEqual(result["mode_source"], "override")

    def test_home_early_covers_friday_pm_brief(self):
        result = runtime.home_early(runtime.parse_datetime("2026-08-26T16:00:00-04:00"))
        self.assertEqual(result["expires_at"], "2026-08-28T15:00:00-04:00")
        self.assertEqual(result["work_cycle_close_at"], "2026-08-26T16:00:00-04:00")
        self.assertEqual(result["sheet_fields"]["State"], "HOME")

    def test_home_early_after_friday_boundary_targets_next_week(self):
        result = runtime.home_early(runtime.parse_datetime("2026-08-28T15:01:00-04:00"))
        self.assertEqual(result["expires_at"], "2026-09-04T15:00:00-04:00")

    def test_directional_route_miles_are_distinct_fields(self):
        self.assertEqual(runtime.ROUTE_KEYS["paidmilesab"], "paid_miles_ab")
        self.assertEqual(runtime.ROUTE_KEYS["paidmilesba"], "paid_miles_ba")
        self.assertNotEqual(
            runtime.ROUTE_KEYS["paidmilesab"], runtime.ROUTE_KEYS["paidmilesba"]
        )

    def test_saturday_bad_mileage_range_does_not_abort(self):
        payload = base_payload("2026-08-22T14:45:00-04:00")
        add_active_trip(payload)
        payload["mileage_values"] = {"bad": "shape"}
        result = runtime.resolve(payload)
        self.assertEqual(result["mode"], "ROAD")
        self.assertNotEqual(result["status"], "error")
        self.assertFalse(
            any("mileage_values is not a readable sheet range" in error for error in result.get("errors", []))
        )

    def test_thursday_home_still_gets_mileage_summary(self):
        payload = base_payload("2026-08-27T14:45:00-04:00")
        payload["mileage_values"].append(
            [
                "MILE-001",
                "2026-08-27",
                "TRIP-001",
                "ROUTE-002",
                "2026-08-21T16:30:00-04:00",
                "",
                "Terminal A",
                "Terminal B",
                2184,
                0.75,
                "",
                "User",
                "Estimated",
                "",
                "2026-08-22T15:43:44-04:00",
            ]
        )
        result = runtime.resolve(payload)
        self.assertEqual(result["mode"], "HOME")
        self.assertTrue(result["mileage_summary_due"])
        self.assertEqual(result["mileage_summary"]["total_paid_miles"], "2,184")
        self.assertEqual(result["mileage_summary"]["gross_pay_estimate"], "1638.00")

    def test_thursday_bad_mileage_is_degraded_not_error(self):
        payload = base_payload("2026-08-27T14:45:00-04:00")
        payload["mileage_values"] = None
        result = runtime.resolve(payload)
        self.assertEqual(result["mode"], "HOME")
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["run_log_fields"]["Status"], "Degraded")
        messages = [item.get("message") for item in result["actions_required"]]
        self.assertIn("Action Required — mileage/pay Sheet unavailable", messages)

    def test_denver_summer_instant_matches_new_york_pm_slot(self):
        moment = runtime.parse_datetime("2026-08-23T12:45:00-06:00", "now")
        evidence = runtime.canonical_slot_evidence(moment)
        self.assertEqual(evidence["timezone"], "America/New_York")
        self.assertEqual(evidence["canonical_clock"], "14:45")
        self.assertTrue(evidence["slot_match"])

    def test_denver_summer_1240_does_not_match_new_york_slot(self):
        moment = runtime.parse_datetime("2026-08-23T12:40:00-06:00", "now")
        evidence = runtime.canonical_slot_evidence(moment)
        self.assertEqual(evidence["canonical_clock"], "14:40")
        self.assertFalse(evidence["slot_match"])

    def test_denver_winter_uses_iana_dst_rules_not_summer_offset(self):
        moment = runtime.parse_datetime("2026-12-15T12:45:00-07:00", "now")
        evidence = runtime.canonical_slot_evidence(moment)
        self.assertEqual(evidence["canonical_clock"], "14:45")
        self.assertTrue(evidence["canonical_now"].endswith("-05:00"))
        self.assertTrue(evidence["slot_match"])

    def test_same_instant_matches_regardless_of_input_offset(self):
        denver = runtime.parse_datetime("2026-08-23T12:45:00-06:00", "now")
        utc = runtime.parse_datetime("2026-08-23T18:45:00+00:00", "now")
        self.assertEqual(
            runtime.canonical_slot_evidence(denver)["canonical_now"],
            runtime.canonical_slot_evidence(utc)["canonical_now"],
        )

    def test_summer_us_offsets_all_resolve_to_same_eastern_pm_slot(self):
        equivalent_instants = (
            "2026-08-24T14:45:00-04:00",
            "2026-08-24T13:45:00-05:00",
            "2026-08-24T12:45:00-06:00",
            "2026-08-24T11:45:00-07:00",
            "2026-08-24T18:45:00+00:00",
        )
        evidence = [
            runtime.canonical_slot_evidence(runtime.parse_aware_instant(value))
            for value in equivalent_instants
        ]
        self.assertTrue(all(item["entry_allowed"] for item in evidence))
        self.assertEqual({"14:45"}, {item["canonical_clock"] for item in evidence})
        self.assertEqual(1, len({item["canonical_now"] for item in evidence}))

    def test_winter_us_offsets_all_resolve_to_same_eastern_pm_slot(self):
        equivalent_instants = (
            "2026-12-15T14:45:00-05:00",
            "2026-12-15T13:45:00-06:00",
            "2026-12-15T12:45:00-07:00",
            "2026-12-15T11:45:00-08:00",
            "2026-12-15T19:45:00+00:00",
        )
        evidence = [
            runtime.canonical_slot_evidence(runtime.parse_aware_instant(value))
            for value in equivalent_instants
        ]
        self.assertTrue(all(item["entry_allowed"] for item in evidence))
        self.assertEqual({"14:45"}, {item["canonical_clock"] for item in evidence})
        self.assertEqual(1, len({item["canonical_now"] for item in evidence}))

    def test_live_slot_check_owns_clock_and_waits_out_bounded_early_dispatch(self):
        moments = iter(
            (
                runtime.parse_aware_instant("2026-08-24T18:44:30+00:00"),
                runtime.parse_aware_instant("2026-08-24T18:45:00+00:00"),
            )
        )
        sleeps = []

        evidence = runtime.live_slot_evidence(
            clock=lambda: next(moments),
            sleeper=sleeps.append,
        )

        self.assertEqual("runtime_system_clock", evidence["clock_source"])
        self.assertEqual([30], sleeps)
        self.assertEqual(30, evidence["waited_seconds"])
        self.assertTrue(evidence["entry_allowed"])
        self.assertEqual("14:45", evidence["canonical_clock"])
        self.assertEqual("exact", evidence["state"])

    def test_live_slot_check_does_not_wait_out_unbounded_early_dispatch(self):
        moment = runtime.parse_aware_instant("2026-08-24T18:43:59+00:00")
        sleeps = []

        evidence = runtime.live_slot_evidence(
            clock=lambda: moment,
            sleeper=sleeps.append,
        )

        self.assertEqual([], sleeps)
        self.assertEqual(0, evidence["waited_seconds"])
        self.assertFalse(evidence["entry_allowed"])
        self.assertEqual("before_next_slot", evidence["state"])

    def test_slot_check_cli_omits_now_and_uses_live_runtime_clock_path(self):
        live_result = {
            "entry_allowed": True,
            "slot_match": True,
            "clock_source": "runtime_system_clock",
            "waited_seconds": 0,
            "state": "exact",
        }
        stdout = io.StringIO()
        with mock.patch.object(
            runtime, "live_slot_evidence", return_value=live_result
        ) as live, contextlib.redirect_stdout(stdout):
            return_code = runtime.main(["slot-check"])

        self.assertEqual(0, return_code)
        self.assertEqual(
            "runtime_system_clock",
            json.loads(stdout.getvalue())["clock_source"],
        )
        live.assert_called_once()

    def test_resolve_exposes_canonical_clock_evidence(self):
        payload = base_payload("2026-08-23T12:45:00-06:00")
        result = runtime.resolve(payload)
        self.assertEqual(result["canonical_clock_evidence"]["canonical_clock"], "14:45")
        self.assertTrue(result["canonical_clock_evidence"]["slot_match"])
        self.assertEqual(result["run_log_fields"]["Canonical Clock (ET)"], "14:45")
        self.assertTrue(result["run_log_fields"]["Canonical Slot Match"])
        self.assertEqual(result["run_log_fields"]["Logical Slot"], "14:45")
        self.assertEqual(result["run_log_fields"]["Dispatch Delay (s)"], 0)

    def test_brief_slot_cannot_contradict_canonical_slot(self):
        payload = base_payload("2026-08-24T14:45:00-04:00")
        payload["brief_slot"] = "AM"
        result = runtime.resolve(payload)
        self.assertEqual("error", result["status"])
        self.assertTrue(any("contradicts canonical" in item for item in result["errors"]))

    def test_naive_current_instant_is_rejected_for_canonical_clock(self):
        with self.assertRaisesRegex(ValueError, "explicit timezone"):
            runtime.canonical_clock(runtime.datetime(2026, 8, 23, 14, 45))

    def test_two_minute_scheduler_delay_is_allowed_and_recorded(self):
        moment = runtime.parse_aware_instant("2026-08-24T14:47:00-04:00")
        evidence = runtime.canonical_slot_evidence(moment)
        self.assertTrue(evidence["entry_allowed"])
        self.assertEqual(evidence["state"], "delayed_within_grace")
        self.assertEqual(evidence["matched_slot"], "14:45")
        self.assertEqual(evidence["delay_seconds"], 120)

    def test_nearest_slot_evidence_crosses_calendar_boundaries(self):
        before_am = runtime.canonical_slot_evidence(
            runtime.parse_aware_instant("2026-08-24T23:59:00-04:00")
        )
        self.assertEqual("2026-08-25T02:45:00-04:00", before_am["scheduled_slot"])
        self.assertEqual("before_next_slot", before_am["state"])

        after_midnight = runtime.canonical_slot_evidence(
            runtime.parse_aware_instant("2026-08-24T00:01:00-04:00")
        )
        self.assertEqual("2026-08-24T02:45:00-04:00", after_midnight["scheduled_slot"])
        self.assertEqual("before_next_slot", after_midnight["state"])

    def test_subminute_early_scheduler_jitter_is_allowed_but_bounded(self):
        within = runtime.parse_aware_instant("2026-08-24T14:44:15-04:00")
        evidence = runtime.canonical_slot_evidence(within)
        self.assertTrue(evidence["entry_allowed"])
        self.assertEqual(evidence["state"], "early_within_grace")
        self.assertEqual(evidence["delay_seconds"], -45)

        too_early = runtime.parse_aware_instant("2026-08-24T14:43:59-04:00")
        self.assertFalse(runtime.canonical_slot_evidence(too_early)["entry_allowed"])

        fractional_early = runtime.parse_aware_instant(
            "2026-08-24T14:43:59.999999-04:00"
        )
        self.assertFalse(
            runtime.canonical_slot_evidence(fractional_early)["entry_allowed"]
        )

        fractional_late = runtime.parse_aware_instant(
            "2026-08-24T15:00:00.000001-04:00"
        )
        self.assertFalse(
            runtime.canonical_slot_evidence(fractional_late)["entry_allowed"]
        )

    def test_spring_forward_gap_uses_first_valid_instant_once(self):
        first_valid = runtime.parse_aware_instant("2027-03-14T03:00:00-04:00")
        evidence = runtime.canonical_slot_evidence(first_valid)
        self.assertTrue(evidence["entry_allowed"])
        self.assertEqual(evidence["logical_scheduled_slot"], "02:45")
        self.assertEqual(evidence["scheduled_slot"], "2027-03-14T03:00:00-04:00")
        self.assertEqual(evidence["dst_adjustment"], "nonexistent_slot_to_first_valid_instant")
        self.assertEqual(evidence["state"], "dst_gap_adjusted")
        self.assertEqual(evidence["delay_seconds"], 0)

        later = runtime.parse_aware_instant("2027-03-14T03:45:00-04:00")
        self.assertFalse(runtime.canonical_slot_evidence(later)["entry_allowed"])

    def test_fall_back_repeated_custom_slot_uses_first_occurrence_only(self):
        first = runtime.parse_aware_instant("2026-11-01T01:30:00-04:00")
        second = runtime.parse_aware_instant("2026-11-01T01:30:00-05:00")
        first_evidence = runtime.canonical_slot_evidence(first, slots=((1, 30),))
        second_evidence = runtime.canonical_slot_evidence(second, slots=((1, 30),))
        self.assertTrue(first_evidence["entry_allowed"])
        self.assertEqual(first_evidence["dst_adjustment"], "first_repeated_occurrence")
        self.assertFalse(second_evidence["entry_allowed"])

    def test_noninteger_slot_grace_is_rejected(self):
        moment = runtime.parse_aware_instant("2026-08-24T14:45:00-04:00")
        for invalid in (True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "whole number"):
                    runtime.canonical_slot_evidence(moment, grace_minutes=invalid)
        for invalid in (True, 1.5):
            with self.subTest(early=invalid):
                with self.assertRaisesRegex(ValueError, "whole number"):
                    runtime.canonical_slot_evidence(moment, early_grace_seconds=invalid)
        with self.assertRaisesRegex(ValueError, "must be integers"):
            runtime.canonical_slot_evidence(moment, slots=((2.5, 45),))

    def test_outside_grace_cli_is_not_due_and_nonzero(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "slot-check", "--now", "2026-08-24T15:01:00-04:00"],
            capture_output=True,
            text=True,
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(payload["status"], "not_due")
        self.assertEqual(payload["state"], "outside_grace")
        self.assertFalse(payload["entry_allowed"])

    def test_naive_cli_timestamp_fails_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "slot-check", "--now", "2026-08-24T14:45:00"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("timezone/UTC offset", result.stdout)
        self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_resolve_cli_rejects_every_non_object_json_root_cleanly(self):
        for raw in ("null", "[]", "1", '"text"'):
            with self.subTest(raw=raw):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "resolve"],
                    input=raw,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("Input JSON root must be an object", result.stdout)
                self.assertNotIn("Traceback", result.stderr + result.stdout)

    def test_non_thursday_malformed_mileage_authority_is_isolated(self):
        payload = base_payload("2026-08-19T14:45:00-04:00")
        payload["mileage_values"] = {"bad": "shape"}
        payload["mileage_settings_values"] = {"bad": "shape"}
        result = runtime.resolve(payload)
        self.assertNotEqual(result["status"], "error")
        self.assertFalse(result["mileage_summary_due"])
        self.assertEqual(result["module_health"]["mileage"]["status"], "not_due")

    def test_off_weather_watch_ignores_stale_invalid_expiry(self):
        payload = base_payload("2026-08-22T14:45:00-04:00")
        add_active_trip(payload)
        payload["trips_values"][-1][9] = "Off"
        payload["trips_values"][-1][10] = "stale bad timestamp"
        result = runtime.resolve(payload)
        self.assertNotEqual(result["status"], "error")
        self.assertFalse(any("Watch Expires" in warning for warning in result["warnings"]))

    def test_nonfinite_route_hours_are_rejected(self):
        rows = [{
            "route_id": "ROUTE-001",
            "endpoint_a": "Alpha Depot",
            "endpoint_b": "Bravo Depot",
            "route_ab": "Route 1 → Route 2",
            "avg_ab_hours": "nan",
            "status": "Active",
        }]
        prepared, errors = runtime.prepare_routes(rows)
        self.assertEqual(prepared, [])
        self.assertTrue(any("Invalid Avg A → B" in error for error in errors))

    def test_extreme_decimal_input_is_bounded_before_pay_math(self):
        with self.assertRaisesRegex(ValueError, "exceeds the supported magnitude"):
            runtime.parse_decimal("1e100000", "miles")

    def test_malformed_appointment_row_degrades_only_appointments(self):
        payload = base_payload("2026-08-22T14:45:00-04:00")
        payload["appointments"] = [None]
        result = runtime.resolve(payload)
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["module_health"]["appointments"]["status"], "degraded")
        self.assertTrue(any("must be an object" in item for item in result["warnings"]))

    def test_invalid_strict_input_flag_fails_closed(self):
        payload = base_payload("2026-08-22T14:45:00-04:00")
        payload["strict_inputs"] = "probably"
        result = runtime.resolve(payload)
        self.assertEqual("error", result["status"])
        self.assertIn("strict_inputs must be boolean-like", result["errors"][0])


if __name__ == "__main__":
    unittest.main()
