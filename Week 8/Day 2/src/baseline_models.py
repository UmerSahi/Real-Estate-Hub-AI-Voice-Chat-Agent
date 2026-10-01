"""Task 1: Baseline Models for Property Valuation (Regression).
Implements and evaluates:
1. Mean Baseline (DummyRegressor)
2. Median Baseline (DummyRegressor)
3. Standard Linear Regression
4. Regularized Ridge Regression
5. Regularized Lasso Regression

Proves mathematically that linear and regularized models beat the naive baselines.
"""
from __future__ import annotations

import time
import warnings
from typing import Dict, Any
import numpy as np
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score, root_mean_squared_error

warnings.filterwarnings("ignore")

from src.config import RANDOM_STATE


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAE (PKR), RMSE (PKR), R², and MAPE (%)."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(root_mean_squared_error(y_true, y_pred))
    r2 = float(r2_score(y_true, y_pred))
    mape = float(mean_absolute_percentage_error(y_true, y_pred) * 100.0)
    return {
        "mae_pkr": mae,
        "mae_lac": mae / 100_000.0,
        "rmse_pkr": rmse,
        "rmse_crore": rmse / 10_000_000.0,
        "rmse_cr": rmse / 10_000_000.0,
        "r2": r2,
        "R2": r2,
        "r2_score": r2,
        "mape_pct": mape,
        "mape": mape,
    }


def train_baseline_models(
    X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, y_test: np.ndarray
) -> Dict[str, Any]:
    """Train and evaluate all baseline regression models."""
    models = {
        "Mean Baseline": DummyRegressor(strategy="mean"),
        "Median Baseline": DummyRegressor(strategy="median"),
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=10.0, random_state=RANDOM_STATE),
        "Lasso Regression": Lasso(alpha=1000.0, max_iter=2000, random_state=RANDOM_STATE),
    }

    results = {}
    fitted_models = {}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, model in models.items():
            t0 = time.time()
            model.fit(X_train, y_train)
            train_time = time.time() - t0

            y_pred = model.predict(X_test)
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
    print("Training Task 1 Baseline Models...")
    out = train_baseline_models(
        splits["X_train_trans"], splits["y_train"], splits["X_test_trans"], splits["y_test"]
    )
    for model_name, res in out["results"].items():
        print(f"{model_name:20s} | MAE: {res['mae_lac']:6.2f} Lac | RMSE: {res['rmse_crore']:5.2f} Cr | R²: {res['r2']:6.4f} | MAPE: {res['mape_pct']:5.2f}%")
