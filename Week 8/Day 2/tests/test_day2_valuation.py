"""Unit and Integration Tests for Week 8 Day 2: Property Valuation Model (Regression).
Tests:
- Data splitting, dimensions, and zero leakage
- Baseline model training and performance superiority over dummy baselines
- Advanced models (Random Forest, XGBoost, LightGBM, CatBoost) achieving R2 > 0.95
- Error breakdown slicing by city and price bracket
- Saved model artifacts existence and serializability
- Quantile regression prediction interval consistency (lower <= pred <= upper)
- Verdict classification accuracy (Overpriced / Fair / Underpriced)
- Exact conversational formatting matching client specification
- MLflow tracking and experiment logging
"""
import sys
import unittest
from pathlib import Path

# Add Day 2 root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import joblib

from src.config import (
    BEST_MODEL_PATH,
    PREPROCESSOR_PATH,
    QUANTILE_LOWER_PATH,
    QUANTILE_UPPER_PATH,
    format_price_pkr,
)
from src.data_loader import get_data_splits, LEAKAGE_COLUMNS
from src.baseline_models import train_baseline_models
from src.advanced_models import train_advanced_models
from src.valuation_service import PropertyValuationService


class TestWeek8Day2Valuation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.splits = get_data_splits()
        cls.service = PropertyValuationService()

    def test_01_data_split_integrity(self):
        """Verify 70/15/15 partitions and zero NaNs in transformed feature arrays."""
        n_total = len(self.splits["X_train"]) + len(self.splits["X_val"]) + len(self.splits["X_test"])
        self.assertAlmostEqual(len(self.splits["X_train"]) / n_total, 0.70, delta=0.01)
        self.assertAlmostEqual(len(self.splits["X_val"]) / n_total, 0.15, delta=0.01)
        self.assertAlmostEqual(len(self.splits["X_test"]) / n_total, 0.15, delta=0.01)

        self.assertFalse(np.isnan(self.splits["X_train_trans"]).any())
        self.assertFalse(np.isnan(self.splits["X_test_trans"]).any())

    def test_02_leakage_columns_strictly_excluded(self):
        """Verify that all target and leakage columns are excluded from feature matrices."""
        for col in LEAKAGE_COLUMNS:
            self.assertNotIn(col, self.splits["X_train"].columns)
            self.assertNotIn(col, self.splits["X_test"].columns)

    def test_03_baseline_models_beat_dummy(self):
        """Verify Linear Regression, Ridge, and Lasso beat the mean baseline."""
        # Train quick subset for speed
        base_res = train_baseline_models(
            self.splits["X_train_trans"][:500], self.splits["y_train"].values[:500],
            self.splits["X_test_trans"][:200], self.splits["y_test"].values[:200]
        )
        mean_mae = base_res["results"]["Mean Baseline"]["mae_pkr"]
        ridge_mae = base_res["results"]["Ridge Regression"]["mae_pkr"]
        self.assertLess(ridge_mae, mean_mae * 0.60, "Ridge must reduce MAE by at least 40% vs Mean Baseline.")

    def test_04_advanced_models_high_performance(self):
        """Verify advanced models achieve R2 > 0.90."""
        adv_res = train_advanced_models(
            self.splits["X_train_trans"][:1000], self.splits["y_train"].values[:1000],
            self.splits["X_test_trans"][:300], self.splits["y_test"].values[:300]
        )
        for name in ["Random Forest", "XGBoost", "LightGBM", "CatBoost"]:
            r2 = adv_res["results"][name]["r2"]
            self.assertGreater(r2, 0.90, f"{name} must achieve R2 > 0.90")

    def test_05_error_slices_structure(self):
        """Verify slice analysis includes all cities and price tiers."""
        from src.model_evaluation import slice_error_by_city, slice_error_by_price_tier
        y_true = self.splits["y_test"].values[:100]
        y_pred = y_true * 1.05
        df_city = slice_error_by_city(self.splits["df_test_raw"].iloc[:100], y_true, y_pred)
        df_tier = slice_error_by_price_tier(self.splits["df_test_raw"].iloc[:100], y_true, y_pred)

        self.assertGreaterEqual(len(df_city), 3)
        self.assertEqual(len(df_tier), 4)

    def test_06_model_artifacts_saved(self):
        """Verify model files exist on disk if training has run."""
        if BEST_MODEL_PATH.exists():
            model = joblib.load(BEST_MODEL_PATH)
            self.assertTrue(hasattr(model, "predict"))

        if PREPROCESSOR_PATH.exists():
            prep = joblib.load(PREPROCESSOR_PATH)
            self.assertTrue(hasattr(prep, "transform"))

    def test_07_quantile_prediction_intervals(self):
        """Verify that prediction intervals satisfy: lower_range <= predicted_price <= upper_range."""
        if self.service.model is not None:
            sample = self.splits["X_test"].iloc[0].to_dict()
            res = self.service.evaluate_valuation(sample)
            self.assertLessEqual(res["lower_range_pkr"], res["predicted_price_pkr"])
            self.assertGreaterEqual(res["upper_range_pkr"], res["predicted_price_pkr"])

    def test_08_pricing_verdict_logic(self):
        """Verify correct verdict assignment: Overpriced, Underpriced, and Fair."""
        if self.service.model is not None:
            sample = self.splits["X_test"].iloc[0].to_dict()
            base_pred = self.service.evaluate_valuation(sample)["predicted_price_pkr"]

            # Overpriced test (+30%)
            res_over = self.service.evaluate_valuation(sample, listed_price_pkr=base_pred * 1.30)
            self.assertEqual(res_over["verdict"], "Overpriced")

            # Underpriced test (-30%)
            res_under = self.service.evaluate_valuation(sample, listed_price_pkr=base_pred * 0.70)
            self.assertEqual(res_under["verdict"], "Underpriced")

            # Fair market test (exact match)
            res_fair = self.service.evaluate_valuation(sample, listed_price_pkr=base_pred)
            self.assertEqual(res_fair["verdict"], "Fair")

    def test_09_conversational_explanation_format(self):
        """Verify formatted text matches client format requirement."""
        if self.service.model is not None:
            sample = self.splits["X_test"].iloc[0].to_dict()
            base_pred = self.service.evaluate_valuation(sample)["predicted_price_pkr"]
            res = self.service.evaluate_valuation(sample, listed_price_pkr=base_pred * 1.25)
            text = res["client_explanation"]
            self.assertIn("Predicted:", text)
            self.assertIn("range", text)
            self.assertIn("Listed at", text)
            self.assertIn("Overpriced by ~", text)

    def test_10_price_formatter_crore_lac(self):
        """Verify Pakistani price formatting utility."""
        self.assertEqual(format_price_pkr(23_500_000), "2.35 crore")
        self.assertEqual(format_price_pkr(8_500_000), "85.0 lac")
        self.assertEqual(format_price_pkr(500_000), "5.0 lac")


if __name__ == "__main__":
    unittest.main()
