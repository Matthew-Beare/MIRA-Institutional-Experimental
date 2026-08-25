from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("import_run_sheet", ROOT / "scripts/import_run_sheet.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class RunSheetImportTests(unittest.TestCase):
    def test_opposite_directions_collapse_to_one_symmetric_pair(self) -> None:
        result = MODULE.reconcile([
            {"DATE": "5/17", "TRIP": "AAA - BBB", "MILES": "312", "source_tab": "current"},
            {"DATE": "5/17", "TRIP": "BBB - AAA", "MILES": "312", "source_tab": "current"},
        ])
        self.assertEqual(result["route_pair_count"], 1)
        route = result["route_upserts"][0]
        self.assertEqual(route["paid_miles_a_to_b"], 312)
        self.assertEqual(route["paid_miles_b_to_a"], 312)
        self.assertFalse(result["historical_occurrences_imported"])
        self.assertNotIn("occurrences", result)

    def test_source_occurrence_dedupes_without_creating_trip_rows(self) -> None:
        row = {"DATE": "5/8-10", "TRIP": "AAA - CCC", "MILES": "2,184", "source_tab": "present"}
        result = MODULE.reconcile([row, dict(row)])
        self.assertEqual(result["valid_observation_count"], 1)
        self.assertEqual(result["route_pair_count"], 1)
        self.assertEqual(result["route_upserts"][0]["paid_miles_a_to_b"], 2184)
        self.assertFalse(result["historical_occurrences_imported"])

    def test_proven_source_alias_does_not_create_duplicate_terminal(self) -> None:
        result = MODULE.reconcile([
            {"DATE": "old", "TRIP": "AAA - BBB", "MILES": "2204", "source_tab": "source"},
            {"DATE": "typo", "TRIP": "AAA - BB8", "MILES": "2204", "source_tab": "source"},
        ], {"BB8": "BBB"})
        self.assertEqual(result["route_pair_count"], 1)
        route = result["route_upserts"][0]
        self.assertEqual((route["pair_a"], route["pair_b"]), ("AAA", "BBB"))

    def test_repeated_latest_can_supersede_old_variant(self) -> None:
        result = MODULE.reconcile([
            {"DATE": "old1", "TRIP": "AAA - BBB", "MILES": "581", "source_tab": "old"},
            {"DATE": "new1", "TRIP": "AAA - BBB", "MILES": "582", "source_tab": "new"},
            {"DATE": "new2", "TRIP": "BBB - AAA", "MILES": "582", "source_tab": "new"},
        ])
        route = result["route_upserts"][0]
        self.assertEqual(route["paid_miles_a_to_b"], 582)
        self.assertEqual(route["selection_basis"], "modal")
        self.assertEqual(route["source_variants"], {581: 1, 582: 2})

    def test_malformed_rows_are_ignored_not_invented(self) -> None:
        result = MODULE.reconcile([
            {"DATE": "x", "TRIP": "NOT A TERMINAL PAIR", "MILES": "871", "source_tab": "source"},
            {"DATE": "x", "TRIP": "AAA - BBB", "MILES": "", "source_tab": "source"},
        ])
        self.assertEqual(result["valid_observation_count"], 0)
        self.assertEqual(result["route_pair_count"], 0)
        self.assertEqual(result["ignored_malformed_count"], 2)
        self.assertEqual(result["status"], "degraded")

    def test_modal_tie_requires_confirmation_instead_of_guessing(self) -> None:
        result = MODULE.reconcile([
            {"DATE": "a", "TRIP": "ABC - DEF", "MILES": "100"},
            {"DATE": "b", "TRIP": "ABC - DEF", "MILES": "101"},
        ])
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["route_upserts"], [])
        self.assertEqual(result["unresolved_route_count"], 1)
        self.assertEqual(result["unresolved_routes"][0]["reason"], "ambiguous-modal-tie")

    def test_result_is_independent_of_input_order(self) -> None:
        rows = [
            {"DATE": "c", "TRIP": "ABC - DEF", "MILES": "100", "source_tab": "x"},
            {"DATE": "a", "TRIP": "DEF - ABC", "MILES": "101", "source_tab": "x"},
            {"DATE": "b", "TRIP": "ABC - DEF", "MILES": "100", "source_tab": "x"},
        ]
        self.assertEqual(MODULE.reconcile(rows), MODULE.reconcile(list(reversed(rows))))

    def test_non_object_row_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "row 1 must be an object"):
            MODULE.reconcile([{"TRIP": "ABC - DEF", "MILES": "100"}, None])

    def test_nonfinite_miles_are_malformed_not_a_crash(self) -> None:
        result = MODULE.reconcile([{"TRIP": "ABC - DEF", "MILES": "inf"}])
        self.assertEqual(result["ignored_malformed_count"], 1)
        self.assertEqual(result["route_upserts"], [])

    def test_observed_at_must_be_offset_aware(self) -> None:
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            MODULE.reconcile([{
                "TRIP": "ABC - DEF", "MILES": "100", "observed_at": "2026-08-24T12:00:00"
            }])

    def test_alias_configuration_fails_closed_and_resolves_chains(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be an object"):
            MODULE.reconcile([], ["ABC"])
        with self.assertRaisesRegex(ValueError, "cyclic terminal aliases"):
            MODULE.reconcile([], {"ABC": "DEF", "DEF": "ABC"})
        result = MODULE.reconcile(
            [{"TRIP": "ABC - XYZ", "MILES": "100"}],
            {"ABC": "DEF", "DEF": "GHI"},
        )
        self.assertEqual(("GHI", "XYZ"), (
            result["route_upserts"][0]["pair_a"],
            result["route_upserts"][0]["pair_b"],
        ))

    def test_observed_at_is_normalized_to_one_instant_representation(self) -> None:
        utc = MODULE.normalize_row({
            "TRIP": "ABC - DEF", "MILES": "100",
            "observed_at": "2026-08-24T16:00:00Z",
        })
        eastern = MODULE.normalize_row({
            "TRIP": "ABC - DEF", "MILES": "100",
            "observed_at": "2026-08-24T12:00:00-04:00",
        })
        self.assertEqual(utc["observed_at"], eastern["observed_at"])


if __name__ == "__main__":
    unittest.main()
