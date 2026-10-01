"""Comprehensive Unit and Integration Test Suite for Week 8 Day 3: Lead Scoring & Explainability.
Tests all 5 core tasks:
1. Data Loading, Leakage Prevention, & Stratified Splitting
2. Classification Models (Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost)
3. Handling Imbalanced Data & Accuracy Paradox Proof
4. Model Evaluation (Precision@Top-20%, Calibration, Cost Threshold Curve)
5. Lead Segmentation & K-Means Customer Persona Engine
6. SHAP Explainability & UrduLish Natural Language Generator
7. Subgroup Algorithmic Fairness & Bias Audit
8. Production LeadScoringService End-to-End Inference
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Add Day 3 root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.config import (
    BEST_MODEL_PATH,
    FIGURES_DIR,
    HOT_THRESHOLD,
    KMEANS_PERSONAS_MODEL_PATH,
    PERSONA_SCALER_PATH,
    PREPROCESSOR_PATH,
    WARM_THRESHOLD,
)
from src.data_loader import get_lead_data_splits, load_raw_lead_data, EXCLUDED_COLUMNS
from src.classification_models import train_classification_models, build_comparison_dataframe
from src.imbalance_handler import evaluate_imbalance_strategies, explain_accuracy_paradox
from src.model_evaluation import compute_top_k_metrics, compute_cost_curve
from src.lead_segmentation import classify_lead_tier, CustomerPersonaEngine
from src.explainability_shap import (
    compute_shap_explanations,
    generate_plain_language_reasons,
    audit_model_fairness_and_bias,
)
from src.lead_scoring_service import LeadScoringService


class TestDay3LeadScoring(unittest.TestCase):
    """Test suite for Day 3 lead scoring classification and explainability pipeline."""

    @classmethod
    def setUpClass(cls):
        """Prepare common splits and fast model for tests."""
        cls.splits = get_lead_data_splits(save_preprocessor=True)
        cls.X_train = cls.splits["X_train_trans"]
        cls.y_train = cls.splits["y_train"].values
        cls.X_val = cls.splits["X_val_trans"]
        cls.y_val = cls.splits["y_val"].values
        cls.X_test = cls.splits["X_test_trans"]
        cls.y_test = cls.splits["y_test"].values
        cls.feat_names = cls.splits["feature_names"]

    def test_01_data_loading_and_leakage_audit(self):
        """Task 1: Verify data partition proportions, target distribution, and zero leakage."""
        self.assertGreater(len(self.X_train), 2000)
        self.assertGreater(len(self.X_val), 400)
        self.assertGreater(len(self.X_test), 400)

        # Stratified balance check (~28.6% positive conversion across sets)
        self.assertAlmostEqual(float(self.y_train.mean()), 0.286, delta=0.03)
        self.assertAlmostEqual(float(self.y_val.mean()), 0.286, delta=0.03)
        self.assertAlmostEqual(float(self.y_test.mean()), 0.286, delta=0.03)

        # Leakage audit: target and raw id excluded from feature space
        for col in EXCLUDED_COLUMNS:
            self.assertNotIn(col, self.feat_names)

    def test_02_classification_models_training(self):
        """Task 1: Verify all 5 classifiers train and achieve superior discrimination over random chance."""
        clf_res = train_classification_models(self.X_train, self.y_train, self.X_test, self.y_test)
        self.assertEqual(len(clf_res["results"]), 5)
        for name in ["Logistic Regression", "Random Forest", "XGBoost", "LightGBM", "CatBoost"]:
            self.assertIn(name, clf_res["results"])
            metrics = clf_res["results"][name]
            self.assertGreater(metrics["roc_auc"], 0.75)
            self.assertGreater(metrics["pr_auc"], 0.55)
            self.assertGreater(metrics["f1"], 0.45)

        df_summary = build_comparison_dataframe(clf_res["results"])
        self.assertEqual(len(df_summary), 5)

    def test_03_accuracy_paradox_demonstration(self):
        """Task 2: Mathematically verify the accuracy paradox on imbalanced lead conversion."""
        paradox = explain_accuracy_paradox(self.y_test)
        self.assertGreater(paradox["naive_accuracy"], 0.65)
        self.assertEqual(paradox["naive_recall"], 0.0)
        self.assertEqual(paradox["naive_f1"], 0.0)
        self.assertGreater(paradox["lost_revenue_pkr"], 10_000_000.0)

    def test_04_imbalance_strategies_comparison(self):
        """Task 2: Verify all 4 imbalance mitigation strategies."""
        imb_res = evaluate_imbalance_strategies(self.splits, n_estimators=50)
        self.assertEqual(len(imb_res["strategies"]), 4)
        for strat in ["No Balancing", "Class Weights", "SMOTE", "Threshold Tuning"]:
            self.assertIn(strat, imb_res["strategies"])
            self.assertGreater(imb_res["strategies"][strat]["f1"], 0.45)

    def test_05_precision_at_top_20_percent(self):
        """Task 3: Test Precision@Top-20% directly reflecting the 40-out-of-200 calling capacity constraint."""
        clf_res = train_classification_models(self.X_train, self.y_train, self.X_test, self.y_test)
        probs = clf_res["results"]["LightGBM"]["probabilities"]
        top20 = compute_top_k_metrics(self.y_test, probs, top_k_ratio=0.20)

        self.assertEqual(top20["top_k_leads_called"], int(len(self.y_test) * 0.20))
        self.assertGreater(top20["precision_at_top_k"], 0.60)  # >60% precision
        self.assertGreater(top20["lift"], 2.0)  # >2.0x lift over random baseline

    def test_06_cost_benefit_threshold_curve(self):
        """Task 3: Verify business loss calculation and cost-optimal decision threshold."""
        clf_res = train_classification_models(self.X_train, self.y_train, self.X_test, self.y_test)
        probs = clf_res["results"]["LightGBM"]["probabilities"]
        cost_info = compute_cost_curve(self.y_test, probs)

        self.assertLess(cost_info["optimal_cost_threshold"], 0.50)
        self.assertGreater(cost_info["min_cost_pkr"], 0.0)

    def test_07_lead_segmentation_tiers(self):
        """Task 4: Verify operational lead categorization into Hot, Warm, and Cold."""
        hot = classify_lead_tier(0.85)
        self.assertEqual(hot["tier"], "Hot")
        self.assertIn("1 hour", hot["sla"])

        warm = classify_lead_tier(0.50)
        self.assertEqual(warm["tier"], "Warm")
        self.assertIn("24 hours", warm["sla"])

        cold = classify_lead_tier(0.15)
        self.assertEqual(cold["tier"], "Cold")
        self.assertIn("Automated", cold["sla"])

    def test_08_customer_persona_clustering(self):
        """Task 4: Verify unsupervised K-Means customer persona clustering."""
        df_raw = load_raw_lead_data()
        engine = CustomerPersonaEngine(n_clusters=3).fit(df_raw)
        self.assertEqual(len(engine.persona_profiles), 3)

        sample = df_raw.iloc[0].to_dict()
        persona = engine.predict_persona(sample)
        self.assertIn("name", persona)
        self.assertIn("recommended_pitch", persona)

    def test_09_shap_explainability_and_plots(self):
        """Task 5: Verify SHAP TreeExplainer calculation and array shapes."""
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(n_estimators=30, max_depth=4, verbose=-1, random_state=42)
        model.fit(self.X_train, self.y_train)

        explainer, shaps, X_sample = compute_shap_explanations(
            model, self.X_train, self.X_test, self.feat_names, max_eval_samples=50
        )
        self.assertEqual(shaps.shape[0], 50)
        self.assertEqual(shaps.shape[1], len(self.feat_names))

    def test_10_urdulish_and_english_reason_generator(self):
        """Task 5: Verify conversational UrduLish and English natural language explanations."""
        sample = self.splits["df_test_raw"].iloc[0].to_dict()
        tier_hot = classify_lead_tier(0.88)
        pos_drivers = [("visit_booked_yes", 0.45), ("number_of_calls", 0.25)]
        neg_drivers = [("response_time_min", -0.10)]

        reasons = generate_plain_language_reasons(sample, 0.88, tier_hot, pos_drivers, neg_drivers)
        self.assertIn("Hot", reasons["urdulish_explanation"])
        self.assertIn("88%", reasons["urdulish_explanation"])
        self.assertIn("Hot", reasons["english_explanation"])

    def test_11_fairness_and_bias_audit(self):
        """Task 5: Verify subgroup fairness audit across acquisition sources and cities."""
        clf_res = train_classification_models(self.X_train, self.y_train, self.X_test, self.y_test)
        probs = clf_res["results"]["LightGBM"]["probabilities"]
        audit = audit_model_fairness_and_bias(self.splits["df_test_raw"], self.y_test, probs)

        self.assertIn("lead_source", audit["lead_source_audit"].columns)
        self.assertIn("Disparate Impact (DIR)", audit["lead_source_audit"].columns)
        self.assertIn("preferred_city", audit["city_audit"].columns)

    def test_12_production_lead_scoring_service(self):
        """End-to-End: Test LeadScoringService real-time scoring and payload generation."""
        service = LeadScoringService()
        sample = self.splits["df_test_raw"].iloc[0].to_dict()
        result = service.score_lead(sample)

        self.assertIn("conversion_probability", result)
        self.assertIn("tier", result)
        self.assertIn("customer_persona", result)
        self.assertIn("urdulish_explanation", result)
        self.assertIn("english_explanation", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
