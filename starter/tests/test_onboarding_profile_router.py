from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "onboarding_profile_router.py"
SPEC = importlib.util.spec_from_file_location("onboarding_profile_router", MODULE_PATH)
assert SPEC and SPEC.loader
router = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(router)


class OnboardingProfileRouterTests(unittest.TestCase):
    def test_retired_parent_style_profile_bypasses_work_mode_and_surfaces_appointments(self) -> None:
        result = router.resolve({
            "roles": ["retired", "parent_guardian"],
            "primary_role": "retired",
            "profile_alias": "Dad",
            "appointment_tracking": True,
            "briefs_enabled": True,
        })
        self.assertEqual("mixed", result["life_profile"])
        self.assertEqual(["retired", "parent_guardian"], result["roles"])
        self.assertEqual("retired", result["primary_role"])
        self.assertEqual("Retired", result["primary_role_label"])
        self.assertEqual("Personal Schedule & Wellbeing", result["support_template"])
        self.assertEqual("Dad", result["profile_alias"])
        self.assertEqual("private-mutable-state", result["profile_alias_storage"])
        self.assertEqual("bypassed", result["context"]["status"])
        self.assertIn("appointments", result["brief_focus"])
        self.assertIn("appointment_reminders", result["recommended_services"])
        self.assertIn("medication_reminders", result["recommended_services"])
        self.assertEqual(
            "requires_explicit_user_confirmation",
            result["reminder_templates"]["medications"]["activation"],
        )
        self.assertEqual("prohibited", result["age_or_ability_inference"])

    def test_long_haul_trucker_recommends_home_road_but_does_not_silently_select(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "long-haul truck driver",
            "works_away_from_home": True,
        })
        self.assertEqual("recommended", result["context"]["status"])
        self.assertEqual(["HOME", "ROAD"], result["context"]["primary_modes"])
        self.assertIn(["HOME", "TRUCK"], result["context"]["alternatives"])
        self.assertIn("require user confirmation", result["context"]["reason"])

    def test_office_worker_explicitly_not_away_bypasses_context_modes(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "systems administrator",
            "works_away_from_home": False,
        })
        self.assertEqual("bypassed", result["context"]["status"])
        self.assertEqual([], result["context"]["primary_modes"])

    def test_field_role_without_away_answer_requires_confirmation(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "field service technician",
        })
        self.assertEqual("needs_confirmation", result["context"]["status"])
        self.assertEqual(["HOME", "FIELD"], result["context"]["primary_modes"])

    def test_custom_context_labels_outrank_role_recommendation(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "truck driver",
            "works_away_from_home": True,
            "context_mode_names": ["house", "tractor"],
        })
        self.assertEqual("selected", result["context"]["status"])
        self.assertEqual(["HOUSE", "TRACTOR"], result["context"]["primary_modes"])

    def test_service_catalog_never_claims_unverified_implementation_or_silent_activation(self) -> None:
        result = router.resolve({"employment_status": "working"})
        self.assertEqual(set(router.SERVICE_CATALOG), set(result["service_catalog"]))
        for service in router.SERVICE_CATALOG:
            self.assertTrue(result["service_catalog"][service]["catalogued"])
            self.assertEqual(
                "requires_capability_verification",
                result["service_catalog"][service]["implementation_status"],
            )
            self.assertEqual("unresolved", result["service_catalog"][service]["activation"])

        explicit = router.resolve({
            "employment_status": "working",
            "briefs_enabled": "yes",
            "order_lifecycle_enabled": "no",
            "recipe_library_enabled": False,
        })
        self.assertEqual("enabled", explicit["service_catalog"]["briefs"]["activation"])
        self.assertEqual("disabled", explicit["service_catalog"]["orders_shipments"]["activation"])
        self.assertEqual("disabled", explicit["service_catalog"]["recipes_meals"]["activation"])

    def test_retired_and_nonworking_are_distinct_roles(self) -> None:
        retired = router.resolve({"employment_status": "retired"})
        nonworking = router.resolve({"employment_status": "not working"})
        not_employed = router.resolve({"employment_status": "not employed"})
        self.assertEqual(["retired"], retired["roles"])
        self.assertEqual("retired", retired["life_profile"])
        self.assertEqual(["nonworking"], nonworking["roles"])
        self.assertEqual("nonworking", nonworking["life_profile"])
        self.assertEqual(["nonworking"], not_employed["roles"])

    def test_retired_profile_recommends_but_never_activates_health_reminders(self) -> None:
        result = router.resolve({"roles": ["retired"]})
        self.assertEqual(4, result["schema_version"])
        for service in ("appointment_reminders", "medication_reminders"):
            self.assertIn(service, result["recommended_services"])
            self.assertEqual("unresolved", result["service_catalog"][service]["activation"])
        self.assertEqual(60, result["reminder_templates"]["appointments"]["relative_minutes_before"])
        self.assertEqual(
            "disabled_until_explicit_opt_in",
            result["reminder_templates"]["medications"]["caregiver_sharing"],
        )

    def test_household_routines_are_explicit_and_do_not_fan_out_schedulers(self) -> None:
        result = router.resolve({
            "roles": ["household_manager"],
            "household_routines_enabled": True,
        })
        self.assertIn("household_routines", result["recommended_services"])
        self.assertEqual(
            "enabled",
            result["service_catalog"]["household_routines"]["activation"],
        )
        reminder = result["reminder_templates"]["household_routines"]
        self.assertIn("washer_to_dryer", reminder["examples"])
        self.assertIn("dry_cleaning_or_repair_pickup", reminder["examples"])
        self.assertEqual(
            "consolidated_brief_or_calendar_projection_no_per_chore_automations",
            reminder["delivery"],
        )
        self.assertEqual("prohibited", reminder["ownership_inference"])

    def test_parent_is_first_class_and_composes_with_work(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "is_parent_guardian": True,
            "primary_role": "working",
            "works_away_from_home": False,
        })
        self.assertEqual(["working", "parent_guardian"], result["roles"])
        self.assertEqual("mixed", result["life_profile"])
        self.assertIn("family_school", result["brief_focus"])

    def test_dependent_minor_is_primary_not_fake_mixed_profile(self) -> None:
        result = router.resolve({"roles": ["student", "dependent_minor"]})
        self.assertEqual("dependent_minor", result["primary_role"])
        self.assertEqual("dependent_minor", result["life_profile"])
        self.assertEqual("bypassed", result["context"]["status"])

        custom_without_approval = router.resolve({
            "roles": ["dependent_minor", "student"],
            "context_mode_names": ["HOME", "CAMPUS"],
        })
        self.assertEqual("bypassed", custom_without_approval["context"]["status"])

        custom_with_approval = router.resolve({
            "roles": ["dependent_minor", "student"],
            "works_away_from_home": True,
            "context_mode_names": ["HOME", "CAMPUS"],
        })
        self.assertEqual("selected", custom_with_approval["context"]["status"])

    def test_disabled_and_not_applicable_services_are_not_recommended(self) -> None:
        result = router.resolve({
            "roles": ["retired", "parent_guardian"],
            "primary_role": "retired",
            "service_states": {
                "appointments_calendar": "not applicable",
                "household_admin": "disabled",
                "travel": "deferred",
            },
        })
        self.assertNotIn("appointments_calendar", result["recommended_services"])
        self.assertNotIn("household_admin", result["recommended_services"])
        self.assertIn("travel", result["recommended_services"])

    def test_unknown_role_and_service_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported role"):
            router.resolve({"roles": ["wizard"]})
        with self.assertRaisesRegex(ValueError, "unsupported service_states"):
            router.resolve({"service_states": {"made_up": "enabled"}})

    def test_conflicting_legacy_and_current_service_state_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "conflicting activation states"):
            router.resolve({
                "briefs_enabled": True,
                "service_states": {"briefs": "disabled"},
            })

    def test_multiple_roles_require_explicit_primary(self) -> None:
        with self.assertRaisesRegex(ValueError, "primary_role is required"):
            router.resolve({"roles": ["working", "parent_guardian"]})

    def test_duplicate_or_contradictory_roles_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicates"):
            router.resolve({"roles": ["retired", "retired"]})
        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            router.resolve({"roles": ["custom", "student"], "primary_role": "student"})
        with self.assertRaisesRegex(ValueError, "conflicts with explicit role"):
            router.resolve({"roles": ["parent_guardian"], "is_parent_guardian": False})

    def test_wrong_container_and_alias_types_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "service_states must be an object"):
            router.resolve({"service_states": []})
        with self.assertRaisesRegex(ValueError, "profile_alias must be a string"):
            router.resolve({"profile_alias": {"bad": "shape"}})
        with self.assertRaisesRegex(ValueError, "items must be strings"):
            router.resolve({"context_mode_names": ["HOME", {"bad": "shape"}]})
        with self.assertRaisesRegex(ValueError, "employment_status must be a string"):
            router.resolve({"employment_status": {"working": True}})
        with self.assertRaisesRegex(ValueError, "job_title must be a string"):
            router.resolve({"employment_status": "working", "job_title": ["driver"]})
        with self.assertRaisesRegex(ValueError, "unsupported service_states"):
            router.resolve({"service_states": {1: "enabled"}})

    def test_invalid_boolean_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid boolean"):
            router.resolve({
                "employment_status": "working",
                "works_away_from_home": "probably",
            })

    def test_invalid_custom_modes_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "two-item list"):
            router.resolve({
                "employment_status": "working",
                "context_mode_names": ["HOME"],
            })
        with self.assertRaisesRegex(ValueError, "labels must be 1-32"):
            router.resolve({
                "employment_status": "working",
                "context_mode_names": ["HOME", "BAD\nLABEL"],
            })
        with self.assertRaisesRegex(ValueError, "conflicts with works_away"):
            router.resolve({
                "employment_status": "working",
                "works_away_from_home": False,
                "context_mode_names": ["HOME", "ROAD"],
            })

    def test_job_keyword_matching_does_not_misclassify_broadway_as_road_work(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "Broadway actor",
        })
        self.assertEqual("unresolved", result["context"]["status"])

    def test_context_never_changes_canonical_timezone(self) -> None:
        result = router.resolve({
            "employment_status": "working",
            "job_title": "delivery driver",
            "works_away_from_home": True,
        })
        self.assertEqual(
            "context-never-overrides-canonical-iana-timezone",
            result["canonical_timezone_rule"],
        )


if __name__ == "__main__":
    unittest.main()
