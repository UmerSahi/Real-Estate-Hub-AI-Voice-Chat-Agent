"""Scikit-learn Pipeline Module for Week 8 Capstone Project.
Handles:
1. Rigorous Data Leakage Checks & Feature Isolation
2. 70/15/15 Train / Validation / Test Splitting (Stratified for Leads)
3. One-Hot vs Target Encoding Comparison for High-Cardinality Location Features
4. Robust & Standard Scaling
5. Reusable, Production-Grade Scikit-learn Pipelines (Pipeline & ColumnTransformer)
"""
from __future__ import annotations

from typing import Dict, List, Literal, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler, TargetEncoder

from src.config import (
    PROPERTIES_FEATURED_PATH,
    LEADS_FEATURED_PATH,
    RANDOM_STATE,
)

# ==========================================
# 1. DATA LEAKAGE AUDIT & COLUMN REMOVALS
# ==========================================
PROPERTY_LEAKAGE_REMOVALS = {
    "price_pkr": "TARGET VARIABLE (Must be isolated as y, never present in X).",
    "price": "Raw target string containing unparsed price labels (severe direct target leakage).",
    "price_per_marla": (
        "Calculated directly from price_pkr / area_marla. Including this creates artificial R2 = 1.0 "
        "because price = price_per_marla * area_marla. Must only be used for EDA / post-inference explanation."
    ),
    "property_id": "Arbitrary unique identifier; leaks portal row ordering and causes index memorization.",
    "plot_size": "Redundant unparsed string; already normalized to area_marla and area_sqft.",
    "listing_date": "Temporal publishing metadata; does not represent an intrinsic physical property characteristic.",
    "amenities": "Raw unstructured text string; already transformed into quantitative amenity_score."
}

LEAD_LEAKAGE_REMOVALS = {
    "converted": "TARGET VARIABLE (Must be isolated as y, never present in X).",
    "lead_id": "Arbitrary CRM identifier; non-generalizable tracking token.",
    "budget": "Raw unstructured string; already normalized into budget_pkr and budget_to_market_ratio."
}


def audit_and_prepare_properties(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict[str, str]]:
    """Audit property dataset for data leakage and separate features from target."""
    df_clean = df.copy()
    y = df_clean["price_pkr"].copy()

    # Drop all leakage and redundant columns
    cols_to_drop = [c for c in PROPERTY_LEAKAGE_REMOVALS.keys() if c in df_clean.columns]
    X = df_clean.drop(columns=cols_to_drop)

    return X, y, PROPERTY_LEAKAGE_REMOVALS


def audit_and_prepare_leads(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, Dict[str, str]]:
    """Audit leads dataset for data leakage and separate features from binary target."""
    df_clean = df.copy()
    # Map target binary 'yes'/'no' to 1 / 0
    y = (df_clean["converted"].str.lower() == "yes").astype(int)

    # Drop all leakage and redundant columns
    cols_to_drop = [c for c in LEAD_LEAKAGE_REMOVALS.keys() if c in df_clean.columns]
    X = df_clean.drop(columns=cols_to_drop)

    return X, y, LEAD_LEAKAGE_REMOVALS


# ==========================================
# 2. 70 / 15 / 15 TRAIN-VAL-TEST SPLITTING
# ==========================================
def split_property_data(
    X: pd.DataFrame, y: pd.Series, random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Split property data into Train (70%), Validation (15%), and Test (15%)."""
    # 70% Train, 30% Temp (Val + Test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=random_state, shuffle=True
    )
    # Split Temp 50/50 -> 15% Val, 15% Test
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, shuffle=True
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def split_lead_data(
    X: pd.DataFrame, y: pd.Series, random_state: int = RANDOM_STATE
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Split leads data into Train (70%), Validation (15%), and Test (15%) using Stratification."""
    # 70% Train, 30% Temp (Val + Test) with stratification on binary converted outcome
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=random_state, stratify=y
    )
    # Split Temp 50/50 -> 15% Val, 15% Test with stratification
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=random_state, stratify=y_temp
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


# ==========================================
# 3. REUSABLE SCIKIT-LEARN PIPELINES
# ==========================================
def build_property_preprocessor(
    encoding_type: Literal["target", "onehot"] = "target"
) -> ColumnTransformer:
    """Build a Scikit-learn ColumnTransformer for Property Valuation.
    - Low-cardinality categorical: OneHotEncoder
    - High-cardinality society: TargetEncoder vs OneHotEncoder
    - Continuous numerical: RobustScaler (handles real estate right-tail variance)
    """
    numeric_robust = [
        "area_marla", "area_sqft", "covered_area", "society_hist_median_ppm"
    ]
    numeric_standard = [
        "bedrooms", "bathrooms", "age_years", "floors", "amenity_score",
        "dist_main_road_km", "dist_school_km", "dist_hospital_km",
        "accessibility_composite", "spatial_density_ratio", "bed_to_bath_ratio"
    ]
    low_cardinality_cat = [
        "city", "property_type", "is_corner", "is_park_facing", 
        "property_age_bucket", "society_tier"
    ]
    high_cardinality_cat = ["area_society"]

    transformers = [
        ("num_robust", RobustScaler(), numeric_robust),
        ("num_standard", StandardScaler(), numeric_standard),
        ("cat_low", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), low_cardinality_cat),
    ]

    if encoding_type == "target":
        # TargetEncoder uses smoothed empirical Bayes shrinkage to prevent overfitting
        transformers.append(
            ("cat_high_target", TargetEncoder(smooth="auto", cv=5, random_state=RANDOM_STATE), high_cardinality_cat)
        )
    else:
        transformers.append(
            ("cat_high_onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), high_cardinality_cat)
        )

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return preprocessor


def build_lead_preprocessor(
    encoding_type: Literal["target", "onehot"] = "target"
) -> ColumnTransformer:
    """Build a Scikit-learn ColumnTransformer for Lead Scoring.
    - Low-cardinality categorical: OneHotEncoder
    - High-cardinality preferred society: TargetEncoder vs OneHotEncoder
    - Continuous numerical: RobustScaler & StandardScaler
    """
    numeric_robust = [
        "budget_pkr", "call_duration_avg_sec", "lead_engagement_score"
    ]
    numeric_standard = [
        "number_of_calls", "response_time_min", "days_since_first_contact",
        "budget_to_market_ratio", "lead_velocity", "high_intent_flag"
    ]
    low_cardinality_cat = [
        "lead_source", "preferred_city", "purpose", "visit_booked",
        "objection_raised", "response_speed_category"
    ]
    high_cardinality_cat = ["preferred_society"]

    transformers = [
        ("num_robust", RobustScaler(), numeric_robust),
        ("num_standard", StandardScaler(), numeric_standard),
        ("cat_low", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False), low_cardinality_cat),
    ]

    if encoding_type == "target":
        transformers.append(
            ("cat_high_target", TargetEncoder(smooth="auto", cv=5, random_state=RANDOM_STATE), high_cardinality_cat)
        )
    else:
        transformers.append(
            ("cat_high_onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), high_cardinality_cat)
        )

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")
    return preprocessor


# ==========================================
# 4. ENCODING STRATEGY COMPARISON
# ==========================================
def compare_property_encoding_strategies(
    X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series
) -> Dict[str, Any]:
    """Scientifically compare One-Hot vs Target Encoding on high-cardinality location features."""
    results = {}

    for enc in ["target", "onehot"]:
        prep = build_property_preprocessor(encoding_type=enc)
        # Wrap in Pipeline with a Ridge regularizer
        pipeline = Pipeline([
            ("preprocessor", prep),
            ("regressor", Ridge(alpha=1.0))
        ])

        # Fit on training data
        pipeline.fit(X_train, y_train)

        # Measure feature dimensions
        X_train_trans = prep.transform(X_train)
        dim = X_train_trans.shape[1]

        # Evaluate on validation data
        y_pred_val = pipeline.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred_val)
        r2 = r2_score(y_val, y_pred_val)

        results[enc] = {
            "feature_dimension": dim,
            "validation_mae_pkr": float(mae),
            "validation_r2": float(r2),
            "mae_lac": float(mae / 100_000.0),
        }

    return results


def compare_lead_encoding_strategies(
    X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series
) -> Dict[str, Any]:
    """Scientifically compare One-Hot vs Target Encoding on Lead conversion."""
    results = {}

    for enc in ["target", "onehot"]:
        prep = build_lead_preprocessor(encoding_type=enc)
        pipeline = Pipeline([
            ("preprocessor", prep),
            ("classifier", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE))
        ])

        pipeline.fit(X_train, y_train)

        X_train_trans = prep.transform(X_train)
        dim = X_train_trans.shape[1]

        y_prob_val = pipeline.predict_proba(X_val)[:, 1]
        y_pred_val = (y_prob_val >= 0.5).astype(int)

        auc = roc_auc_score(y_val, y_prob_val)
        f1 = f1_score(y_val, y_pred_val)

        results[enc] = {
            "feature_dimension": dim,
            "validation_roc_auc": float(auc),
            "validation_f1": float(f1),
        }

    return results


def main():
    print("=" * 70)
    print("TASK 5: ENCODING, SCALING & SPLITTING PIPELINE AUDIT")
    print("=" * 70)

    # 1. Properties Pipeline
    print("\n--- DATASET A: PROPERTY VALUATION (REGRESSION) ---")
    df_prop = pd.read_csv(PROPERTIES_FEATURED_PATH)
    X_prop, y_prop, prop_leaks = audit_and_prepare_properties(df_prop)
    print(f"Total Features Isolated: {X_prop.shape[1]} features, Target: y ({y_prop.name})")
    print("Data Leakage Removals Documented:")
    for col, reason in prop_leaks.items():
        print(f"  [REMOVED] {col}: {reason}")

    X_train_p, X_val_p, X_test_p, y_train_p, y_val_p, y_test_p = split_property_data(X_prop, y_prop)
    print(f"\n70/15/15 Data Split Sizes:")
    print(f"  Train:      {len(X_train_p)} rows ({len(X_train_p)/len(X_prop)*100:.1f}%)")
    print(f"  Validation: {len(X_val_p)} rows ({len(X_val_p)/len(X_prop)*100:.1f}%)")
    print(f"  Test:       {len(X_test_p)} rows ({len(X_test_p)/len(X_prop)*100:.1f}%)")

    print("\nComparing Encoding Strategies for High-Cardinality 'area_society':")
    prop_comp = compare_property_encoding_strategies(X_train_p, y_train_p, X_val_p, y_val_p)
    for enc, met in prop_comp.items():
        print(f"  [{enc.upper()} ENCODING] Features: {met['feature_dimension']} | "
              f"Val MAE: {met['mae_lac']:.2f} Lac PKR | Val R²: {met['validation_r2']:.4f}")

    # 2. Leads Pipeline
    print("\n--- DATASET B: LEAD SCORING (CLASSIFICATION) ---")
    df_leads = pd.read_csv(LEADS_FEATURED_PATH)
    X_lead, y_lead, lead_leaks = audit_and_prepare_leads(df_leads)
    print(f"Total Features Isolated: {X_lead.shape[1]} features, Target: y ({y_lead.name})")
    print("Data Leakage Removals Documented:")
    for col, reason in lead_leaks.items():
        print(f"  [REMOVED] {col}: {reason}")

    X_train_l, X_val_l, X_test_l, y_train_l, y_val_l, y_test_l = split_lead_data(X_lead, y_lead)
    print(f"\nStratified 70/15/15 Split & Target Balance Verification:")
    for name, split_y in [("Train", y_train_l), ("Validation", y_val_l), ("Test", y_test_l)]:
        conv_rate = split_y.mean() * 100
        print(f"  {name:11s}: {len(split_y)} rows | Converted Rate: {conv_rate:.2f}% (Strictly Preserved)")

    print("\nComparing Encoding Strategies for High-Cardinality 'preferred_society':")
    lead_comp = compare_lead_encoding_strategies(X_train_l, y_train_l, X_val_l, y_val_l)
    for enc, met in lead_comp.items():
        print(f"  [{enc.upper()} ENCODING] Features: {met['feature_dimension']} | "
              f"Val ROC-AUC: {met['validation_roc_auc']:.4f} | Val F1: {met['validation_f1']:.4f}")

    print("\nPipeline definitions verified. Ready for model training in Day 2!")


if __name__ == "__main__":
    main()
