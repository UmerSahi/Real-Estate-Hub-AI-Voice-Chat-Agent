"""Unit and Integration Tests for Task 1: FastAPI Model Serving Endpoints.
Validates:
- GET /health
- GET /model/info
- POST /predict/price
- POST /predict/lead-score
- POST /explain/price
- POST /explain/lead
- POST /predict/batch (CSV file upload)
- Input validation: reject negative size, unknown city, negative budget, etc.
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Add Day 4 root to path
DAY4_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAY4_DIR))

from src.api import app
from src.config import LEGAL_DISCLAIMER


class TestFastAPIEndpoints(unittest.TestCase):
    """Test suite for FastAPI serving layer."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """GET /health must return 200 with operational model statuses."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["models_loaded"]["valuation_model"])
        self.assertTrue(data["models_loaded"]["lead_scoring_model"])
        self.assertTrue(data["database_connected"])

    def test_02_model_info_endpoint(self):
        """GET /model/info must expose versioning, metrics, and trained dates."""
        res = self.client.get("/model/info")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("valuation_model", data)
        self.assertIn("lead_scoring_model", data)
        self.assertIn("system_guardrails", data)
        self.assertIn("r2_score", data["valuation_model"]["benchmark_metrics"])
        self.assertIn("precision_at_top20", data["lead_scoring_model"]["benchmark_metrics"])

    def test_03_predict_price_valid(self):
        """POST /predict/price should return point estimate, range, and verdict."""
        payload = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 20.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "age_years": 5,
            "property_type": "House",
            "is_corner": "yes",
            "listed_price_pkr": 85_000_000,
        }
        res = self.client.post("/predict/price", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("predicted_price_pkr", data)
        self.assertIn("predicted_price_formatted", data)
        self.assertIn("price_range_formatted", data)
        self.assertIn(data["verdict"], ["Fair", "Overpriced", "Underpriced"])
        self.assertIn("Disclaimer:", data["disclaimer"])

    def test_04_predict_price_reject_negative_size(self):
        """POST /predict/price must reject negative or zero plot size with 422."""
        payload = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": -5.0,
            "bedrooms": 3,
        }
        res = self.client.post("/predict/price", json=payload)
        self.assertEqual(res.status_code, 422)
        err = res.json()
        self.assertEqual(err["status"], "validation_error")

    def test_05_predict_price_reject_unknown_city(self):
        """POST /predict/price must reject unknown city with actionable 422 error."""
        payload = {
            "city": "Peshawar",
            "area_society": "Hayatabad",
            "area_marla": 10.0,
        }
        res = self.client.post("/predict/price", json=payload)
        self.assertEqual(res.status_code, 422)
        err = res.json()
        self.assertEqual(err["status"], "validation_error")
        self.assertTrue(any("Unsupported city" in e["message"] for e in err["errors"]))

    def test_06_predict_lead_score_valid(self):
        """POST /predict/lead-score should return conversion probability and tier."""
        payload = {
            "lead_id": "LEAD-TEST-API",
            "lead_source": "call",
            "budget_pkr": 45_000_000,
            "preferred_city": "Lahore",
            "preferred_society": "DHA Phase 6",
            "purpose": "buy",
            "number_of_calls": 3,
            "call_duration_avg_sec": 240,
            "response_time_min": 10.0,
            "visit_booked": "yes",
            "days_since_first_contact": 2,
            "objection_raised": "None",
        }
        res = self.client.post("/predict/lead-score", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("conversion_probability", data)
        self.assertIn("conversion_score_pct", data)
        self.assertIn(data["tier"], ["Hot", "Warm", "Cold"])
        self.assertIn("sla", data)
        self.assertIn("customer_persona", data)
        self.assertIn("urdulish_explanation", data)

    def test_07_predict_lead_score_reject_invalid_source(self):
        """POST /predict/lead-score must reject unknown lead channel."""
        payload = {
            "lead_source": "newspaper_classifieds",
            "budget_pkr": 20_000_000,
            "preferred_city": "Lahore",
            "preferred_society": "DHA Phase 6",
        }
        res = self.client.post("/predict/lead-score", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_08_explain_price(self):
        """POST /explain/price should return SHAP waterfall feature attributions."""
        payload = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 20.0,
            "bedrooms": 5,
        }
        res = self.client.post("/explain/price", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("feature_attributions", data)
        self.assertIn("urdulish_explanation", data)
        self.assertIn("waterfall_summary", data)

    def test_09_explain_lead(self):
        """POST /explain/lead should return feature drivers and plain language reason."""
        payload = {
            "lead_source": "call",
            "budget_pkr": 35_000_000,
            "preferred_city": "Islamabad",
            "preferred_society": "F-10",
            "number_of_calls": 3,
            "visit_booked": "yes",
        }
        res = self.client.post("/explain/lead", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("feature_attributions", data)
        self.assertIn("urdulish_explanation", data)

    def test_10_predict_batch_csv(self):
        """POST /predict/batch should accept CSV file upload and process rows."""
        csv_text = (
            "city,area_society,area_marla,bedrooms,bathrooms,age_years,property_type\n"
            "Lahore,DHA Phase 6,10.0,3,3,2,House\n"
            "Islamabad,F-10,20.0,5,5,1,House\n"
        )
        file_obj = io.BytesIO(csv_text.encode("utf-8"))
        files = {"file": ("test_batch.csv", file_obj, "text/csv")}
        res = self.client.post("/predict/batch", files=files)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["batch_type"], "properties")
        self.assertEqual(data["successful_rows"], 2)
        self.assertEqual(data["failed_rows"], 0)
        self.assertIsNotNone(data["csv_download_base64"])

    def test_11_serve_voice_call_station(self):
        """GET /call should return 200 HTML content for live voice agent station."""
        res = self.client.get("/call")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("RealEstate-Hub", res.text)
        self.assertIn("vapiSDK", res.text)


if __name__ == "__main__":
    unittest.main()
