"""Unit and Integration Tests for Task 5: Guardrails, OOD Checks, Disclaimers, & Audit Logging.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add Day 4 root to path
DAY4_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAY4_DIR))

import uuid
from src.guardrails import (
    validate_property_ood,
    validate_lead_ood,
    detect_prompt_injection,
    audit_logger,
)
from src.config import LEGAL_DISCLAIMER


class TestGuardrailsAndValidation(unittest.TestCase):
    """Test suite for data integrity, OOD enforcement, disclaimers, and logging."""

    def test_01_property_ood_normal_passes(self):
        """Standard residential property must pass OOD check."""
        valid_prop = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 20.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "age_years": 4,
            "listed_price_pkr": 80_000_000,
        }
        passed, reason = validate_property_ood(valid_prop)
        self.assertTrue(passed)
        self.assertIsNone(reason)

    def test_02_property_ood_extreme_area_rejected(self):
        """Property with area > 100 Marla (e.g. 500 Marla) must be rejected as OOD."""
        extreme_prop = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 500.0,
        }
        passed, reason = validate_property_ood(extreme_prop)
        self.assertFalse(passed)
        self.assertIn("OOD Rejection", reason)

    def test_03_property_ood_extreme_bedrooms_rejected(self):
        """Property with 40 bedrooms must be rejected."""
        crazy_prop = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 10.0,
            "bedrooms": 40,
        }
        passed, reason = validate_property_ood(crazy_prop)
        self.assertFalse(passed)
        self.assertIn("Bedrooms", reason)

    def test_04_lead_ood_extreme_budget_rejected(self):
        """Lead with declared budget > PKR 80 Crore must be flagged for institutional underwriting."""
        whale_lead = {
            "preferred_city": "Lahore",
            "budget_pkr": 1_000_000_000.0,  # 100 Crore
            "number_of_calls": 2,
        }
        passed, reason = validate_lead_ood(whale_lead)
        self.assertFalse(passed)
        self.assertIn("Budget", reason)

    def test_05_disclaimer_content_check(self):
        """Legal disclaimer must exist and contain non-certified valuation warning."""
        self.assertIn("Disclaimer:", LEGAL_DISCLAIMER)
        self.assertIn("algorithmic", LEGAL_DISCLAIMER)
        self.assertIn("not constitute certified legal appraisals", LEGAL_DISCLAIMER)

    def test_06_audit_logging_lifecycle(self):
        """Ensure audit logs write to SQLite and can be retrieved with correct fields."""
        test_pred_id = f"AUDIT-TEST-{uuid.uuid4().hex}"
        inputs = {"city": "Lahore", "area_marla": 10.0}
        outputs = {"predicted_price_pkr": 25_000_000}

        audit_logger.log_prediction(
            prediction_id=test_pred_id,
            endpoint="/predict/price",
            inputs=inputs,
            output=outputs,
            model_version="test-v1",
            latency_ms=12.5,
            client_ip="192.168.1.10",
            is_ood=False,
        )

        logs = audit_logger.get_recent_logs(limit=10)
        matched = [entry for entry in logs if entry["prediction_id"] == test_pred_id]
        self.assertTrue(len(matched) > 0)
        self.assertEqual(matched[0]["endpoint"], "/predict/price")
        self.assertEqual(matched[0]["model_version"], "test-v1")
        self.assertEqual(matched[0]["inputs"]["city"], "Lahore")

        summary = audit_logger.get_audit_summary()
        self.assertGreater(summary["total_predictions_logged"], 0)


if __name__ == "__main__":
    unittest.main()
