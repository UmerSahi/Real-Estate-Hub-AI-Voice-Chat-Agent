"""Task 1: Classification Models for Lead Conversion.
Trains and benchmarks baseline and advanced classifiers:
- Logistic Regression (Baseline)
- Random Forest
- XGBoost
- LightGBM
- CatBoost
"""
from __future__ import annotations

import time
import warnings
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
)

from src.config import RANDOM_STATE

warnings.filterwarnings("ignore")


def compute_classification_metrics(
    y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray
) -> Dict[str, float]:
    """Compute standard classification evaluation metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_true, y_prob))
    pr_auc = float(average_precision_score(y_true, y_prob))

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
    }


def train_classification_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_eval: np.ndarray,
    y_eval: np.ndarray,
    eval_name: str = "Test",
) -> Dict[str, Any]:
    """Train baseline and advanced classifiers, measure performance and training duration."""
    classifiers = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            verbose=-1,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "CatBoost": CatBoostClassifier(
            iterations=250,
            depth=5,
            learning_rate=0.08,
            verbose=0,
            random_seed=RANDOM_STATE,
            allow_writing_files=False,
        ),
    }

    results = {}
    fitted_models = {}

    for name, model in classifiers.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0

        probs = model.predict_proba(X_eval)[:, 1]
        preds = (probs >= 0.50).astype(int)

        metrics = compute_classification_metrics(y_eval, preds, probs)
        metrics["train_time_sec"] = train_time
        metrics["training_time_sec"] = train_time
        metrics["probabilities"] = probs
        metrics["predictions"] = preds

        results[name] = metrics
        fitted_models[name] = model

    return {
        "results": results,
        "models": fitted_models,
        "fitted_models": fitted_models,
        "eval_partition": eval_name,
    }


def build_comparison_dataframe(model_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Format model metrics into presentation-ready comparison DataFrame."""
    rows = []
    for name, m in model_results.items():
        rows.append({
            "Model": name,
            "ROC-AUC": f"{m['roc_auc']:.4f}",
            "PR-AUC": f"{m['pr_auc']:.4f}",
            "F1-Score": f"{m['f1']:.4f}",
            "Precision": f"{m['precision']:.2%}",
            "Recall": f"{m['recall']:.2%}",
            "Accuracy": f"{m['accuracy']:.2%}",
            "Train Time (s)": f"{m.get('train_time_sec', 0.0):.2f}s",
        })
    df_comp = pd.DataFrame(rows).sort_values("PR-AUC", ascending=False).reset_index(drop=True)
    return df_comp


if __name__ == "__main__":
    from src.data_loader import get_lead_data_splits
    splits = get_lead_data_splits(save_preprocessor=False)
    clf_res = train_classification_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )
    df_summary = build_comparison_dataframe(clf_res["results"])
    print("Task 1 Classification Models Leaderboard:")
    print(df_summary.to_string(index=False))
