"""Task 5: Price Range & Confidence Engine with Quantile Regression.
Predicts:
- Fair Market Price
- Lower Range (10th percentile bound) & Upper Range (90th percentile bound)
- Commercial Verdict: Underpriced / Fair / Overpriced
- Formats conversational output for real estate clients & agents:
  'Predicted: 2.35 crore (range 2.15 – 2.55 crore). Listed at 2.9 crore → Overpriced by ~23%.'
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor

from src.config import (
    BEST_MODEL_PATH,
    PREPROCESSOR_PATH,
    QUANTILE_LOWER_PATH,
    QUANTILE_UPPER_PATH,
    RANDOM_STATE,
    format_price_pkr,
)


def train_quantile_regression_models(
    X_train: np.ndarray, y_train: np.ndarray
) -> Tuple[GradientBoostingRegressor, GradientBoostingRegressor]:
    """Train GradientBoostingRegressor quantile models for 10th and 90th percentile bounds."""
    print("Training 10th percentile quantile regressor (lower bound)...")
    model_lower = GradientBoostingRegressor(
        loss="quantile", alpha=0.10, n_estimators=100, max_depth=5,
        random_state=RANDOM_STATE
    )
    model_lower.fit(X_train, y_train)

    print("Training 90th percentile quantile regressor (upper bound)...")
    model_upper = GradientBoostingRegressor(
        loss="quantile", alpha=0.90, n_estimators=100, max_depth=5,
        random_state=RANDOM_STATE
    )
    model_upper.fit(X_train, y_train)

    # Save to disk
    joblib.dump(model_lower, QUANTILE_LOWER_PATH)
    joblib.dump(model_upper, QUANTILE_UPPER_PATH)
    print(f"Saved lower quantile model to: {QUANTILE_LOWER_PATH}")
    print(f"Saved upper quantile model to: {QUANTILE_UPPER_PATH}")

    return model_lower, model_upper


class PropertyValuationService:
    """Production Valuation Inference Service for Real Estate Sales Teams."""

    def __init__(
        self,
        model_path: Optional[Path] = None,
        preprocessor_path: Optional[Path] = None,
        lower_path: Optional[Path] = None,
        upper_path: Optional[Path] = None,
    ):
        self.model_path = model_path or BEST_MODEL_PATH
        self.preprocessor_path = preprocessor_path or PREPROCESSOR_PATH
        self.lower_path = lower_path or QUANTILE_LOWER_PATH
        self.upper_path = upper_path or QUANTILE_UPPER_PATH

        self.model = joblib.load(self.model_path) if self.model_path.exists() else None
        self.preprocessor = joblib.load(self.preprocessor_path) if self.preprocessor_path.exists() else None
        self.lower_model = joblib.load(self.lower_path) if self.lower_path.exists() else None
        self.upper_model = joblib.load(self.upper_path) if self.upper_path.exists() else None

    def evaluate_valuation(
        self,
        property_features: Dict[str, Any],
        listed_price_pkr: Optional[float] = None
    ) -> Dict[str, Any]:
        """Predict fair market price, confidence intervals, and pricing verdict."""
        if self.model is None or self.preprocessor is None:
            raise RuntimeError("Valuation models or preprocessor not loaded.")

        # Convert dictionary to DataFrame
        df_in = pd.DataFrame([property_features])

        # Preprocess features
        X_trans = self.preprocessor.transform(df_in)

        # Predict point estimate
        raw_pred = float(self.model.predict(X_trans)[0])
        pred_pkr = max(500_000.0, raw_pred)

        # Predict quantile intervals
        if self.lower_model is not None and self.upper_model is not None:
            lower_pkr = float(self.lower_model.predict(X_trans)[0])
            upper_pkr = float(self.upper_model.predict(X_trans)[0])
            # Ensure physical bounds
            lower_pkr = min(lower_pkr, pred_pkr * 0.95)
            upper_pkr = max(upper_pkr, pred_pkr * 1.05)
        else:
            # Fallback empirical 80% interval
            lower_pkr = pred_pkr * 0.92
            upper_pkr = pred_pkr * 1.08

        pred_str = format_price_pkr(pred_pkr)
        lower_str = format_price_pkr(lower_pkr)
        upper_str = format_price_pkr(upper_pkr)

        # Verdict calculation
        verdict = "Fair"
        verdict_explanation = "Fair Market Price"
        delta_pct = 0.0

        if listed_price_pkr is not None and listed_price_pkr > 0:
            delta_pct = ((listed_price_pkr - pred_pkr) / pred_pkr) * 100.0
            listed_str = format_price_pkr(listed_price_pkr)

            if listed_price_pkr > upper_pkr or delta_pct >= 10.0:
                verdict = "Overpriced"
                explanation = f"Predicted: {pred_str} (range {lower_str} - {upper_str}). Listed at {listed_str} -> Overpriced by ~{abs(round(delta_pct))}%."
            elif listed_price_pkr < lower_pkr or delta_pct <= -10.0:
                verdict = "Underpriced"
                explanation = f"Predicted: {pred_str} (range {lower_str} - {upper_str}). Listed at {listed_str} -> Underpriced by ~{abs(round(delta_pct))}%."
            else:
                verdict = "Fair"
                explanation = f"Predicted: {pred_str} (range {lower_str} - {upper_str}). Listed at {listed_str} -> Fair Market Price (Within {abs(round(delta_pct, 1))}% of fair value)."
        else:
            explanation = f"Predicted: {pred_str} (range {lower_str} - {upper_str})."

        return {
            "predicted_price_pkr": pred_pkr,
            "predicted_price_formatted": pred_str,
            "lower_range_pkr": lower_pkr,
            "lower_range_formatted": lower_str,
            "upper_range_pkr": upper_pkr,
            "upper_range_formatted": upper_str,
            "listed_price_pkr": listed_price_pkr,
            "verdict": verdict,
            "delta_percentage": delta_pct,
            "price_delta_pct": delta_pct,
            "client_explanation": explanation,
        }


if __name__ == "__main__":
    from src.data_loader import get_data_splits
    splits = get_data_splits()
    print("Testing Quantile Training...")
    train_quantile_regression_models(splits["X_train_trans"], splits["y_train"])

    print("\nTesting Valuation Service Inference...")
    service = PropertyValuationService()
    sample_prop = splits["X_test"].iloc[0].to_dict()
    res = service.evaluate_valuation(sample_prop, listed_price_pkr=29_000_000)
    print("Valuation Result:")
    print(" ", res["client_explanation"])
