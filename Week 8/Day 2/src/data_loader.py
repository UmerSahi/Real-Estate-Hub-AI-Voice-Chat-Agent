"""Data Loading and Preprocessing Module for Week 8 Day 2.
Isolates features from targets, performs 70/15/15 train/val/test split,
and fits a reusable Scikit-learn ColumnTransformer.
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, RobustScaler, StandardScaler, TargetEncoder

from src.config import PROPERTIES_FEATURED_PATH, RANDOM_STATE

LEAKAGE_COLUMNS = [
    "price_pkr", "price", "price_per_marla", "property_id",
    "plot_size", "listing_date", "amenities"
]


def load_property_data() -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Load featured property dataset, perform leakage audit, and return X, y, and full dataframe."""
    df = pd.read_csv(PROPERTIES_FEATURED_PATH)
    y = df["price_pkr"].copy()
    
    # Drop all target leakage and arbitrary identifiers
    cols_to_drop = [c for c in LEAKAGE_COLUMNS if c in df.columns]
    X = df.drop(columns=cols_to_drop)

    return X, y, df


def build_preprocessor(encoding_type: str = "target") -> ColumnTransformer:
    """Construct ColumnTransformer preprocessor for Property Listings."""
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
        transformers.append(
            ("cat_high_target", TargetEncoder(smooth="auto", cv=5, random_state=RANDOM_STATE), high_cardinality_cat)
        )
    else:
        transformers.append(
            ("cat_high_onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), high_cardinality_cat)
        )

    return ColumnTransformer(transformers=transformers, remainder="drop")


def get_data_splits() -> Dict[str, Any]:
    """Load, split (70/15/15), and transform property valuation data."""
    X, y, df_full = load_property_data()

    # 70% Train, 30% Temp (Val + Test)
    indices = np.arange(len(X))
    idx_train, idx_temp = train_test_split(indices, test_size=0.30, random_state=RANDOM_STATE, shuffle=True)
    idx_val, idx_test = train_test_split(idx_temp, test_size=0.50, random_state=RANDOM_STATE, shuffle=True)

    X_train, y_train = X.iloc[idx_train].copy(), y.iloc[idx_train].copy()
    X_val, y_val = X.iloc[idx_val].copy(), y.iloc[idx_val].copy()
    X_test, y_test = X.iloc[idx_test].copy(), y.iloc[idx_test].copy()

    # Raw test records for sliced error analysis (by city, price tier, etc.)
    df_test_raw = df_full.iloc[idx_test].copy().reset_index(drop=True)

    # Fit preprocessor on Train set only (strict leakage prevention)
    preprocessor = build_preprocessor(encoding_type="target")
    preprocessor.fit(X_train, y_train)

    X_train_trans = preprocessor.transform(X_train)
    X_val_trans = preprocessor.transform(X_val)
    X_test_trans = preprocessor.transform(X_test)

    # Extract transformed feature names
    feature_names = []
    for name, trans, cols in preprocessor.transformers_:
        if hasattr(trans, "get_feature_names_out"):
            feature_names.extend(trans.get_feature_names_out(cols))
        else:
            feature_names.extend(cols)

    return {
        "X_train": X_train,
        "y_train": y_train,
        "X_val": X_val,
        "y_val": y_val,
        "X_test": X_test,
        "y_test": y_test,
        "X_train_trans": X_train_trans,
        "X_val_trans": X_val_trans,
        "X_test_trans": X_test_trans,
        "df_test_raw": df_test_raw,
        "preprocessor": preprocessor,
        "feature_names": feature_names,
    }
