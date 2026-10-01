"""Task 4: Hyperparameter Tuning with Optuna & Experiment Tracking with MLflow.
Tunes the top two models (LightGBM and CatBoost) on validation MAE.
Logs:
- Parameters
- Metrics (MAE, RMSE, R², MAPE)
- Feature set used
- Training time
- Model artifacts
Registers winning model in the MLflow Model Registry.
"""
from __future__ import annotations

import json
import time
import os
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple
import joblib

warnings.filterwarnings("ignore")
import mlflow
import mlflow.catboost
import mlflow.lightgbm
import numpy as np
import optuna
from catboost import CatBoostRegressor
from lightgbm import LGBMRegressor

from src.baseline_models import compute_metrics
from src.config import (
    BEST_MODEL_PATH,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_REGISTERED_MODEL_NAME,
    MLFLOW_TRACKING_URI,
    PREPROCESSOR_PATH,
    RANDOM_STATE,
)

# Silence Optuna info logs during tuning
optuna.logging.set_verbosity(optuna.logging.WARNING)


def tune_lightgbm(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    n_trials: int = 15
) -> Tuple[Dict[str, Any], LGBMRegressor]:
    """Tune LightGBM hyperparameters with Optuna."""
    best_score = float("inf")
    best_params = {}
    best_model = None

    def objective(trial: optuna.Trial) -> float:
        nonlocal best_score, best_params, best_model
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 300, step=50),
            "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.15, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 20, 60),
            "max_depth": trial.suggest_int("max_depth", 4, 10),
            "subsample": trial.suggest_float("subsample", 0.70, 0.95),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.70, 0.95),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            "random_state": RANDOM_STATE,
            "verbose": -1,
            "n_jobs": -1,
        }

        model = LGBMRegressor(**params)
        model.fit(X_train, y_train)
        y_val_pred = model.predict(X_val)
        mae = float(np.mean(np.abs(y_val - y_val_pred)))

        if mae < best_score:
            best_score = mae
            best_params = params
            best_model = model

        return mae

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials)

    return best_params, best_model


def tune_catboost(
    X_train: np.ndarray, y_train: np.ndarray,
    X_val: np.ndarray, y_val: np.ndarray,
    n_trials: int = 15
) -> Tuple[Dict[str, Any], CatBoostRegressor]:
    """Tune CatBoost hyperparameters with Optuna."""
    best_score = float("inf")
    best_params = {}
    best_model = None

    def objective(trial: optuna.Trial) -> float:
        nonlocal best_score, best_params, best_model
        params = {
            "iterations": trial.suggest_int("iterations", 150, 350, step=50),
            "learning_rate": trial.suggest_float("learning_rate", 0.03, 0.15, log=True),
            "depth": trial.suggest_int("depth", 4, 8),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1e-2, 10.0, log=True),
            "random_seed": RANDOM_STATE,
            "verbose": 0,
            "allow_writing_files": False,
        }

        model = CatBoostRegressor(**params)
        model.fit(X_train, y_train)
        y_val_pred = model.predict(X_val)
        mae = float(np.mean(np.abs(y_val - y_val_pred)))

        if mae < best_score:
            best_score = mae
            best_params = params
            best_model = model

        return mae

    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials)

    return best_params, best_model


def run_tuning_and_mlflow_tracking(
    splits: Dict[str, Any], n_trials: int = 15
) -> Dict[str, Any]:
    """Execute hyperparameter tuning for top 2 models, log to MLflow, and register best model."""
    X_train = splits["X_train_trans"]
    y_train = splits["y_train"]
    X_val = splits["X_val_trans"]
    y_val = splits["y_val"]
    X_test = splits["X_test_trans"]
    y_test = splits["y_test"]
    feature_names = splits["feature_names"]
    preprocessor = splits["preprocessor"]

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    print("Running Optuna tuning for Model 1: LightGBM...")
    t0_lgb = time.time()
    lgb_params, lgb_model = tune_lightgbm(X_train, y_train, X_val, y_val, n_trials=n_trials)
    lgb_time = time.time() - t0_lgb
    y_pred_lgb = lgb_model.predict(X_test)
    lgb_test_metrics = compute_metrics(y_test, y_pred_lgb)
    lgb_test_metrics["training_time_sec"] = lgb_time
    lgb_test_metrics["train_time_sec"] = lgb_time
    lgb_test_metrics["predictions"] = y_pred_lgb

    print("Running Optuna tuning for Model 2: CatBoost...")
    t0_cb = time.time()
    cb_params, cb_model = tune_catboost(X_train, y_train, X_val, y_val, n_trials=n_trials)
    cb_time = time.time() - t0_cb
    y_pred_cb = cb_model.predict(X_test)
    cb_test_metrics = compute_metrics(y_test, y_pred_cb)
    cb_test_metrics["training_time_sec"] = cb_time
    cb_test_metrics["train_time_sec"] = cb_time
    cb_test_metrics["predictions"] = y_pred_cb

    # Log LightGBM Run in MLflow
    with mlflow.start_run(run_name="Optuna_Tuned_LightGBM") as run_lgb:
        mlflow.log_params(lgb_params)
        mlflow.log_metrics({
            "test_mae_pkr": lgb_test_metrics["mae_pkr"],
            "test_mae_lac": lgb_test_metrics["mae_lac"],
            "test_rmse_cr": lgb_test_metrics["rmse_crore"],
            "test_r2": lgb_test_metrics["r2"],
            "test_mape_pct": lgb_test_metrics["mape_pct"],
            "tuning_time_sec": lgb_time,
        })
        mlflow.log_dict({"feature_names": feature_names, "feature_count": len(feature_names)}, "features_info.json")
        mlflow.lightgbm.log_model(lgb_model, artifact_path="model")
        run_lgb_id = run_lgb.info.run_id

    # Log CatBoost Run in MLflow
    with mlflow.start_run(run_name="Optuna_Tuned_CatBoost") as run_cb:
        mlflow.log_params(cb_params)
        mlflow.log_metrics({
            "test_mae_pkr": cb_test_metrics["mae_pkr"],
            "test_mae_lac": cb_test_metrics["mae_lac"],
            "test_rmse_cr": cb_test_metrics["rmse_crore"],
            "test_r2": cb_test_metrics["r2"],
            "test_mape_pct": cb_test_metrics["mape_pct"],
            "tuning_time_sec": cb_time,
        })
        mlflow.log_dict({"feature_names": feature_names, "feature_count": len(feature_names)}, "features_info.json")
        mlflow.catboost.log_model(cb_model, artifact_path="model")
        run_cb_id = run_cb.info.run_id

    # Select overall champion
    if cb_test_metrics["mae_pkr"] <= lgb_test_metrics["mae_pkr"]:
        champion_name = "Optuna Tuned CatBoost"
        champion_model = cb_model
        champion_metrics = cb_test_metrics
        champion_run_id = run_cb_id
        champion_params = cb_params
    else:
        champion_name = "Optuna Tuned LightGBM"
        champion_model = lgb_model
        champion_metrics = lgb_test_metrics
        champion_run_id = run_lgb_id
        champion_params = lgb_params

    # Register champion model in MLflow Model Registry
    print(f"\nRegistering champion model '{champion_name}' in MLflow Model Registry...")
    try:
        model_uri = f"runs:/{champion_run_id}/model"
        reg_model = mlflow.register_model(model_uri, MLFLOW_REGISTERED_MODEL_NAME)
        print(f"Registered in MLflow Registry: '{MLFLOW_REGISTERED_MODEL_NAME}', Version: {reg_model.version}")
    except Exception as e:
        print(f"MLflow model registration note: {e}")

    # Save champion model and preprocessor to local models/ directory
    joblib.dump(champion_model, BEST_MODEL_PATH)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"Saved champion model to: {BEST_MODEL_PATH}")
    print(f"Saved preprocessor to:   {PREPROCESSOR_PATH}")

    return {
        "Optuna Tuned LightGBM": {
            "metrics": lgb_test_metrics,
            "params": lgb_params,
            "run_id": run_lgb_id,
        },
        "Optuna Tuned CatBoost": {
            "metrics": cb_test_metrics,
            "params": cb_params,
            "run_id": run_cb_id,
        },
        "champion_name": champion_name,
        "champion_model": champion_model,
        "champion_metrics": champion_metrics,
        "champion_params": champion_params,
    }


if __name__ == "__main__":
    from src.data_loader import get_data_splits
    splits = get_data_splits()
    print("Testing Task 4: Optuna Tuning & MLflow Experiment Tracking...")
    res = run_tuning_and_mlflow_tracking(splits, n_trials=10)
    print("Champion:", res["champion_name"], "MAE:", res["champion_metrics"]["mae_lac"], "Lac PKR")
