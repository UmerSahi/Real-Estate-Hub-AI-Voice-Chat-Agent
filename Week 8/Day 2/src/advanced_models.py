"""Task 2: Advanced Models for Property Valuation (Regression).
Trains and evaluates:
1. Random Forest Regressor
2. XGBoost Regressor
3. LightGBM Regressor
4. CatBoost Regressor
"""
from __future__ import annotations

import time
from typing import Dict, Any
import numpy as np
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from src.baseline_models import compute_metrics
from src.config import RANDOM_STATE


def train_advanced_models(
    X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray
) -> Dict[str, Any]:
    """Train and evaluate advanced ensemble and gradient boosting models."""
    models = {
        "Random Forest": RandomForestRegressor(
            n_estimators=150, max_depth=15, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=-1
        ),
        "XGBoost": XGBRegressor(
            n_estimators=200, learning_rate=0.06, max_depth=6, subsample=0.85,
            colsample_bytree=0.85, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "LightGBM": LGBMRegressor(
            n_estimators=200, learning_rate=0.06, num_leaves=31, subsample=0.85,
            colsample_bytree=0.85, random_state=RANDOM_STATE, verbose=-1, n_jobs=-1
        ),
        "CatBoost": CatBoostRegressor(
            iterations=300, learning_rate=0.07, depth=6,
            random_seed=RANDOM_STATE, verbose=0, allow_writing_files=False
        ),
    }

    results = {}
    fitted_models = {}

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0

        y_pred = model.predict(X_test)
        # Prevent any negative price artifacts
        y_pred = np.clip(y_pred, 500_000, None)

        metrics = compute_metrics(y_test, y_pred)
        metrics["training_time_sec"] = train_time
        metrics["train_time_sec"] = train_time
        metrics["train_time"] = train_time
        metrics["predictions"] = y_pred

        results[name] = metrics
        fitted_models[name] = model

    return {
        "results": results,
        "fitted_models": fitted_models,
        "models": fitted_models,
    }


if __name__ == "__main__":
    from src.data_loader import get_data_splits
    splits = get_data_splits()
    print("Training Task 2 Advanced Models...")
    out = train_advanced_models(
        splits["X_train_trans"], splits["y_train"], splits["X_test_trans"], splits["y_test"]
    )
    for model_name, res in out["results"].items():
        print(f"{model_name:20s} | MAE: {res['mae_lac']:6.2f} Lac | RMSE: {res['rmse_crore']:5.2f} Cr | R²: {res['r2']:6.4f} | MAPE: {res['mape_pct']:5.2f}% | Time: {res['training_time_sec']:4.2f}s")
