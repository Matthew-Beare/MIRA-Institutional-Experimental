from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OrderSourceAuthorityContractTests(unittest.TestCase):
    def text(self, path: str) -> str:
        return (ROOT / path).read_text(encoding="utf-8")

    def test_live_order_status_uses_active_shipments_not_historical_rows(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        compatibility = self.text("policy/ops-brief-policy.yaml")

        self.assertIn("Live order-status queries enumerate the current Ops `Shipments` projection", skill)
        self.assertIn("must never resurrect a transaction that is absent from `Shipments`", skill)
        self.assertIn('active_status_authority: "Ops Status Register Shipments"', compatibility)
        self.assertIn("must never resurrect an order absent from the active Shipments projection", compatibility)

    def test_owner_evidence_is_first_class_when_gmail_is_missing(self) -> None:
        skill = self.text("skill/ops-brief-policy/SKILL.md")
        compatibility = self.text("policy/ops-brief-policy.yaml")
        receipt = self.text("skill/ops-brief-policy/references/receipt-ingestion.md")

        self.assertIn("Gmail is an evidence adapter, not a required purchase-ingestion gate", skill)
        self.assertIn("explicit owner screenshot/chat confirmation is first-class evidence", skill)
        self.assertIn("Never wait for Gmail and never invent missing fields", skill)
        self.assertIn("owner_evidence_fallback:", compatibility)
        self.assertIn("enabled: true", compatibility)
        self.assertIn("Never wait for Gmail or invent missing fields", compatibility)
        self.assertIn("Gmail is an evidence adapter, not a mandatory ingestion gate", receipt)
        self.assertIn("explicit owner screenshot/chat confirmation is sufficient", receipt)
        self.assertIn("Never wait for Gmail and never invent missing fields", receipt)
        self.assertNotIn("Gmail is the evidence source.", receipt)


if __name__ == "__main__":
    unittest.main()
