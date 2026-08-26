from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "appointment_identity.py"
spec = importlib.util.spec_from_file_location("appointment_identity", MODULE)
subject = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(subject)


def candidate(**overrides):
    row = {
        "source_authority": "email",
        "source_record_id": "message-123",
        "raw_title": "Appointment with Smith Clinic",
        "person_or_organization_name": "Smith Clinic",
        "start_at": "2026-09-01T10:00:00-04:00",
        "email": "synthetic-contact-token",
    }
    row.update(overrides)
    return row


def directory():
    return [{
        "entity_uuid": "2f94bd96-dbb5-4a7b-a907-08bf92578103",
        "display_name": "Smith Clinic",
        "entity_type": "medical_practice",
        "category_or_specialty": "Cardiology",
        "aliases": ["Smith Clinic"],
        "contact_identifiers": {"email": "synthetic-contact-token"},
        "source_bindings": [],
        "provenance": [{"kind": "fixture"}],
        "verification_status": "verified",
    }]


class AppointmentIdentityTests(unittest.TestCase):
    def test_cached_alias_resolves_without_research(self):
        result = subject.resolve({"candidate": candidate(), "directory": directory()})
        self.assertEqual("resolved_cached", result["status"])
        self.assertFalse(result["research_required"])
        self.assertEqual("Cardiology — Smith Clinic", result["appointment"]["canonical_title"])
        self.assertIn("email::message-123", result["entity"]["source_bindings"])

    def test_unseen_candidate_requests_research_instead_of_inventing_identity(self):
        result = subject.resolve({"candidate": candidate(person_or_organization_name="Unknown Office", email=""), "directory": []})
        self.assertEqual("needs_research_or_owner_confirmation", result["status"])
        self.assertTrue(result["research_required"])
        self.assertEqual("", result["appointment"]["provider_entity_uuid"])

    def test_supported_research_is_cached_for_reuse(self):
        result = subject.resolve({
            "candidate": candidate(person_or_organization_name="Smith Clinic"),
            "directory": [],
            "research_candidate": {
                "display_name": "Smith Clinic",
                "entity_type": "medical_practice",
                "category_or_specialty": "Cardiology",
                "source_url": "https://example.invalid/smith",
                "confidence": 0.95,
            },
        })
        self.assertEqual("resolved_research", result["status"])
        self.assertEqual(1, len(result["directory"]))
        replay = subject.resolve({"candidate": candidate(source_record_id="message-456"), "directory": result["directory"]})
        self.assertEqual("resolved_cached", replay["status"])

    def test_low_confidence_research_does_not_promote(self):
        result = subject.resolve({
            "candidate": candidate(),
            "directory": [],
            "research_candidate": {
                "display_name": "Smith Clinic",
                "source_url": "https://example.invalid/smith",
                "confidence": 0.5,
            },
        })
        self.assertTrue(result["research_required"])

    def test_owner_correction_creates_durable_binding(self):
        corrected = subject.correct({
            "candidate": candidate(person_or_organization_name="Wrong Name"),
            "directory": [],
            "correction": {
                "display_name": "Correct Name",
                "entity_type": "service_provider",
                "category_or_specialty": "Specialist",
            },
        })
        self.assertEqual("corrected", corrected["status"])
        self.assertEqual("owner_confirmed", corrected["entity"]["verification_status"])
        replay = subject.resolve({
            "candidate": candidate(person_or_organization_name="Wrong Name", source_record_id="message-123"),
            "directory": corrected["directory"],
        })
        self.assertEqual("resolved_cached", replay["status"])
        self.assertEqual("Specialist — Correct Name", replay["appointment"]["canonical_title"])

    def test_ambiguous_alias_fails_closed(self):
        rows = directory()
        second = dict(rows[0])
        second["entity_uuid"] = "02e41893-6548-4dc5-9034-764252242120"
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            subject.resolve({"candidate": candidate(), "directory": rows + [second]})


if __name__ == "__main__":
    unittest.main()
