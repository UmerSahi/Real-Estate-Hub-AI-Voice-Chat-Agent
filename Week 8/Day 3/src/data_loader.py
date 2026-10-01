"""Data Loader and Preprocessing Pipeline for Week 8 Day 3: Lead Scoring.
Performs stratified 70/15/15 train/val/test split and builds leakage-free ColumnTransformer pipeline.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from src.config import (
    LEADS_FEATURED_CSV,
    PREPROCESSOR_PATH,
    RANDOM_STATE,
)

EXCLUDED_COLUMNS = ["lead_id", "budget", "converted"]

NUMERICAL_FEATURES = [
    "number_of_calls",
    "call_duration_avg_sec",
    "response_time_min",
    "days_since_first_contact",
    "budget_pkr",
    "lead_engagement_score",
    "budget_to_market_ratio",
    "lead_velocity",
    "high_intent_flag",
]

CATEGORICAL_FEATURES = [
    "lead_source",
    "preferred_city",
    "preferred_society",
    "purpose",
    "visit_booked",
    "objection_raised",
    "response_speed_category",
]


def load_raw_lead_data(data_path: Path = LEADS_FEATURED_CSV) -> pd.DataFrame:
    """Load featured real estate leads dataset."""
    if not data_path.exists():
        raise FileNotFoundError(f"Leads dataset not found at: {data_path}")
    df = pd.read_csv(data_path)
    return df


def build_preprocessor() -> ColumnTransformer:
    """Build ColumnTransformer for numerical scaling and categorical one-hot encoding."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", RobustScaler(), NUMERICAL_FEATURES),
            (
                "cat",
                OneHotEncoder(sparse_output=False, handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )
    return preprocessor


def get_lead_data_splits(
    data_path: Path = LEADS_FEATURED_CSV,
    save_preprocessor: bool = True,
) -> Dict[str, Any]:
    """Execute stratified 70/15/15 split and return raw and transformed arrays."""
    df = load_raw_lead_data(data_path)

    # Encode binary target: 'yes' -> 1, 'no' -> 0
    y = (df["converted"].astype(str).str.lower() == "yes").astype(int)
    X = df.drop(columns=[col for col in EXCLUDED_COLUMNS if col in df.columns])

    # Stratified Split: 70% Train, 30% Temp
    X_train_raw, X_temp_raw, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM_STATE
    )

    # Split Temp 50/50: 15% Validation, 15% Test
    X_val_raw, X_test_raw, y_val, y_test = train_test_split(
        X_temp_raw, y_temp, test_size=0.50, stratify=y_temp, random_state=RANDOM_STATE
    )

    # Fit preprocessor strictly on Training data (Zero Data Leakage)
    preprocessor = build_preprocessor()
    X_train_trans = preprocessor.fit_transform(X_train_raw)
    X_val_trans = preprocessor.transform(X_val_raw)
    X_test_trans = preprocessor.transform(X_test_raw)

    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    feature_names = NUMERICAL_FEATURES + cat_names

    if save_preprocessor:
        joblib.dump(preprocessor, PREPROCESSOR_PATH)

    # Corresponding full raw records for slicing and business attribution
    df_train_raw = df.loc[X_train_raw.index].copy()
    df_val_raw = df.loc[X_val_raw.index].copy()
    df_test_raw = df.loc[X_test_raw.index].copy()

    return {
        "X_train_raw": X_train_raw.reset_index(drop=True),
        "y_train": y_train.reset_index(drop=True),
        "X_val_raw": X_val_raw.reset_index(drop=True),
        "y_val": y_val.reset_index(drop=True),
        "X_test_raw": X_test_raw.reset_index(drop=True),
        "y_test": y_test.reset_index(drop=True),
        "X_train_trans": X_train_trans,
        "X_val_trans": X_val_trans,
        "X_test_trans": X_test_trans,
        "feature_names": feature_names,
        "preprocessor": preprocessor,
        "df_train_raw": df_train_raw.reset_index(drop=True),
        "df_val_raw": df_val_raw.reset_index(drop=True),
        "df_test_raw": df_test_raw.reset_index(drop=True),
    }


if __name__ == "__main__":
    splits = get_lead_data_splits()
    print("Stratified Data Partitions Created:")
    print(f"  - Train: {splits['X_train_trans'].shape[0]} samples ({splits['y_train'].mean():.2%} conversion)")
    print(f"  - Val:   {splits['X_val_trans'].shape[0]} samples ({splits['y_val'].mean():.2%} conversion)")
    print(f"  - Test:  {splits['X_test_trans'].shape[0]} samples ({splits['y_test'].mean():.2%} conversion)")
    print(f"  - Total Transformed Features: {len(splits['feature_names'])}")
