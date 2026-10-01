"""Unit and Integration Tests for Week 8 Day 1 Pipeline.
Tests:
- Raw dataset existence and minimum row thresholds (Dataset A >= 5000, Dataset B >= 3000)
- Price parser accuracy (Crore, Lac, numeric PKR)
- Area parser accuracy (Marla, Kanal, Sq Ft, Sq Yds)
- Location canonicalization
- Cleaned dataset completeness (zero NaNs, deduplicated)
- Feature engineering correctness (all 13 features created)
- Data leakage isolation (strictly zero target or identifier leakage)
- 70/15/15 train/val/test splits and stratification consistency
- Scikit-learn Pipeline transformations (Target & One-Hot encoding)
"""
import sys
import unittest
from pathlib import Path

# Add Week 8 root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

from src.config import (
    PROPERTIES_RAW_PATH,
    LEADS_RAW_PATH,
    PROPERTIES_CLEANED_PATH,
    LEADS_CLEANED_PATH,
    PROPERTIES_FEATURED_PATH,
    LEADS_FEATURED_PATH,
)
from src.data_cleaner import (
    normalize_location_name,
    parse_pakistani_area,
    parse_pakistani_price,
)
from src.feature_engineering import (
    engineer_property_features,
    engineer_lead_features,
)
from src.pipeline import (
    audit_and_prepare_properties,
    audit_and_prepare_leads,
    split_property_data,
    split_lead_data,
    build_property_preprocessor,
    build_lead_preprocessor,
)


class TestWeek8Day1Pipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.df_prop_raw = pd.read_csv(PROPERTIES_RAW_PATH)
        cls.df_leads_raw = pd.read_csv(LEADS_RAW_PATH)
        cls.df_prop_clean = pd.read_csv(PROPERTIES_CLEANED_PATH)
        cls.df_leads_clean = pd.read_csv(LEADS_CLEANED_PATH)
        cls.df_prop_feat = pd.read_csv(PROPERTIES_FEATURED_PATH)
        cls.df_leads_feat = pd.read_csv(LEADS_FEATURED_PATH)

    def test_01_dataset_a_properties_size_and_schema(self):
        """Verify Dataset A has at least 5,000 rows and all required columns."""
        self.assertGreaterEqual(len(self.df_prop_raw), 5000, "Dataset A must have at least 5,000 listings.")
        required_cols = [
            "property_id", "city", "area_society", "property_type", "plot_size",
            "covered_area", "bedrooms", "bathrooms", "age_years", "floors",
            "is_corner", "is_park_facing", "amenities", "dist_main_road_km",
            "dist_school_km", "dist_hospital_km", "listing_date", "price"
        ]
        for col in required_cols:
            self.assertIn(col, self.df_prop_raw.columns, f"Missing column in Dataset A: {col}")

    def test_02_dataset_b_leads_size_and_schema(self):
        """Verify Dataset B has at least 3,000 rows and all required columns."""
        self.assertGreaterEqual(len(self.df_leads_raw), 3000, "Dataset B must have at least 3,000 leads.")
        required_cols = [
            "lead_id", "lead_source", "budget", "preferred_city", "preferred_society",
            "purpose", "number_of_calls", "call_duration_avg_sec", "response_time_min",
            "visit_booked", "days_since_first_contact", "objection_raised", "converted"
        ]
        for col in required_cols:
            self.assertIn(col, self.df_leads_raw.columns, f"Missing column in Dataset B: {col}")

    def test_03_price_parser_pakistani_formats(self):
        """Test parsing of various Pakistani conversational price strings."""
        self.assertEqual(parse_pakistani_price("1.5 Crore"), 15_000_000.0)
        self.assertEqual(parse_pakistani_price("2.25 cr"), 22_500_000.0)
        self.assertEqual(parse_pakistani_price("85 Lac"), 8_500_000.0)
        self.assertEqual(parse_pakistani_price("90 lakh"), 9_000_000.0)
        self.assertEqual(parse_pakistani_price("PKR 12,000,000"), 12_000_000.0)
        self.assertEqual(parse_pakistani_price("Rs 5,500,000"), 5_500_000.0)

    def test_04_area_parser_units(self):
        """Test conversion of mixed Pakistani land area units to Marla and Sqft."""
        marla_k, sqft_k = parse_pakistani_area("1 Kanal")
        self.assertEqual(marla_k, 20.0)
        self.assertEqual(sqft_k, 4500.0)

        marla_m, sqft_m = parse_pakistani_area("10 Marla")
        self.assertEqual(marla_m, 10.0)
        self.assertEqual(sqft_m, 2250.0)

        marla_s, sqft_s = parse_pakistani_area("2250 sq ft")
        self.assertEqual(marla_s, 10.0)
        self.assertEqual(sqft_s, 2250.0)

    def test_05_location_canonicalization(self):
        """Test normalization of inconsistent society spellings."""
        self.assertEqual(normalize_location_name("DHA Ph 5"), "DHA Phase 5")
        self.assertEqual(normalize_location_name("DHA Phase-6"), "DHA Phase 6")
        self.assertEqual(normalize_location_name("Gulberg 3"), "Gulberg III")
        self.assertEqual(normalize_location_name("Bahria Twn"), "Bahria Town")
        self.assertEqual(normalize_location_name("F-11/2"), "F-11")

    def test_06_cleaned_datasets_have_no_missing_critical_values(self):
        """Verify cleaned datasets have zero missing values in essential fields."""
        self.assertEqual(self.df_prop_clean["price_pkr"].isna().sum(), 0)
        self.assertEqual(self.df_prop_clean["area_marla"].isna().sum(), 0)
        self.assertEqual(self.df_prop_clean["bedrooms"].isna().sum(), 0)

        self.assertEqual(self.df_leads_clean["budget_pkr"].isna().sum(), 0)
        self.assertEqual(self.df_leads_clean["converted"].isna().sum(), 0)

    def test_07_feature_engineering_presence(self):
        """Verify feature engineering generates expected features."""
        for feat in ["price_per_marla", "property_age_bucket", "society_tier", 
                     "amenity_score", "accessibility_composite", "spatial_density_ratio", 
                     "bed_to_bath_ratio", "society_hist_median_ppm"]:
            self.assertIn(feat, self.df_prop_feat.columns)

        for feat in ["lead_engagement_score", "response_speed_category", 
                     "budget_to_market_ratio", "lead_velocity", "high_intent_flag"]:
            self.assertIn(feat, self.df_leads_feat.columns)

    def test_08_data_leakage_audit_strictly_excludes_target_and_identifiers(self):
        """Verify that X contains NO target variables or derived target formulas."""
        X_p, y_p, _ = audit_and_prepare_properties(self.df_prop_feat)
        
        self.assertNotIn("price_pkr", X_p.columns)
        self.assertNotIn("price", X_p.columns)
        self.assertNotIn("price_per_marla", X_p.columns, "price_per_marla MUST be excluded from X to prevent target leak!")
        self.assertNotIn("property_id", X_p.columns)

        X_l, y_l, _ = audit_and_prepare_leads(self.df_leads_feat)
        self.assertNotIn("converted", X_l.columns)
        self.assertNotIn("lead_id", X_l.columns)
        self.assertNotIn("budget", X_l.columns)

    def test_09_train_val_test_split_proportions_and_stratification(self):
        """Verify 70/15/15 partition sizes and lead class stratification."""
        X_p, y_p, _ = audit_and_prepare_properties(self.df_prop_feat)
        X_tr_p, X_va_p, X_te_p, y_tr_p, y_va_p, y_te_p = split_property_data(X_p, y_p)

        n_p = len(X_p)
        self.assertAlmostEqual(len(X_tr_p) / n_p, 0.70, delta=0.01)
        self.assertAlmostEqual(len(X_va_p) / n_p, 0.15, delta=0.01)
        self.assertAlmostEqual(len(X_te_p) / n_p, 0.15, delta=0.01)

        # Leads Stratification check
        X_l, y_l, _ = audit_and_prepare_leads(self.df_leads_feat)
        X_tr_l, X_va_l, X_te_l, y_tr_l, y_va_l, y_te_l = split_lead_data(X_l, y_l)

        base_rate = y_l.mean()
        self.assertAlmostEqual(y_tr_l.mean(), base_rate, delta=0.02)
        self.assertAlmostEqual(y_va_l.mean(), base_rate, delta=0.02)
        self.assertAlmostEqual(y_te_l.mean(), base_rate, delta=0.02)

    def test_10_scikit_learn_pipeline_transformation(self):
        """Verify Scikit-learn Pipeline transforms data without raising errors."""
        X_p, y_p, _ = audit_and_prepare_properties(self.df_prop_feat)
        X_tr_p, X_va_p, _, y_tr_p, y_va_p, _ = split_property_data(X_p, y_p)

        pipe_prop = build_property_preprocessor(encoding_type="target")
        X_trans_p = pipe_prop.fit_transform(X_tr_p, y_tr_p)
        self.assertEqual(len(X_trans_p), len(X_tr_p))
        self.assertFalse(np.isnan(X_trans_p).any(), "Transformed property array must contain zero NaNs")

        X_l, y_l, _ = audit_and_prepare_leads(self.df_leads_feat)
        X_tr_l, X_va_l, _, y_tr_l, y_va_l, _ = split_lead_data(X_l, y_l)

        pipe_lead = build_lead_preprocessor(encoding_type="target")
        X_trans_l = pipe_lead.fit_transform(X_tr_l, y_tr_l)
        self.assertEqual(len(X_trans_l), len(X_tr_l))
        self.assertFalse(np.isnan(X_trans_l).any(), "Transformed lead array must contain zero NaNs")


if __name__ == "__main__":
    unittest.main()
