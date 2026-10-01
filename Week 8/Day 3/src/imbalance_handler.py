"""Task 2: Handling Imbalanced Data in Lead Conversion.
Compares four strategies:
1. No balancing (empirical distribution, threshold = 0.50)
2. Class weights (balanced weighting in loss function)
3. SMOTE (Synthetic Minority Over-sampling on training set)
4. Threshold tuning (optimizing decision boundary on validation set)

Explains and quantifies why Accuracy is a misleading metric in conversion modeling.
"""
from __future__ import annotations

import warnings
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from imblearn.over_sampling import SMOTE
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from src.config import RANDOM_STATE, COST_FALSE_NEGATIVE_PKR, COST_FALSE_POSITIVE_PKR

warnings.filterwarnings("ignore")


def explain_accuracy_paradox(y_true: np.ndarray) -> Dict[str, Any]:
    """Demonstrate why raw Accuracy is a deceptive metric on imbalanced lead data."""
    total = len(y_true)
    actual_positives = int(np.sum(y_true == 1))
    actual_negatives = int(np.sum(y_true == 0))
    pos_rate = actual_positives / total
    neg_rate = actual_negatives / total

    # Naive "Dumb" Predictor: Predict "no" (0) for 100% of leads
    naive_preds = np.zeros(total, dtype=int)
    naive_acc = float(accuracy_score(y_true, naive_preds))
    naive_rec = float(recall_score(y_true, naive_preds, zero_division=0))
    naive_prec = float(precision_score(y_true, naive_preds, zero_division=0))
    naive_f1 = float(f1_score(y_true, naive_preds, zero_division=0))

    # Revenue consequence
    lost_deals = actual_positives
    lost_revenue_pkr = lost_deals * COST_FALSE_NEGATIVE_PKR

    explanation = (
        f"ACCURACY PARADOX EXPLANATION:\n"
        f"• The dataset contains {neg_rate:.1%} non-converting leads and {pos_rate:.1%} converting leads.\n"
        f"• A naive model predicting 'NO' for every single lead achieves {naive_acc:.1%} ACCURACY!\n"
        f"• However, Recall is 0.0% and Precision is 0.0% — it misses ALL {actual_positives} converting buyers.\n"
        f"• Business Cost: {lost_deals} lost transactions (~{lost_revenue_pkr/100_000:,.1f} Lac PKR in missed commissions).\n"
        f"• Conclusion: Models must be evaluated on PR-AUC, Recall, Precision@Top-20%, and Cost-Weighted F1."
    )

    return {
        "dataset_total": total,
        "conversions": actual_positives,
        "non_conversions": actual_negatives,
        "conversion_rate": pos_rate,
        "naive_accuracy": naive_acc,
        "naive_recall": naive_rec,
        "naive_precision": naive_prec,
        "naive_f1": naive_f1,
        "lost_revenue_pkr": lost_revenue_pkr,
        "explanation": explanation,
    }


def find_optimal_threshold(
    y_val: np.ndarray,
    val_probs: np.ndarray,
    criterion: str = "f1",
) -> Tuple[float, float]:
    """Find the optimal decision threshold on validation set."""
    best_th = 0.50
    best_score = -float("inf") if criterion in ["f1", "cost_utility"] else float("inf")

    thresholds = np.linspace(0.10, 0.85, 76)

    for th in thresholds:
        preds = (val_probs >= th).astype(int)

        if criterion == "f1":
            score = float(f1_score(y_val, preds, zero_division=0))
            if score > best_score:
                best_score = score
                best_th = float(th)

        elif criterion == "cost_utility":
            # Minimize total expected business penalty
            cm = confusion_matrix(y_val, preds)
            tn, fp, fn, tp = cm.ravel()
            total_cost = (fn * COST_FALSE_NEGATIVE_PKR) + (fp * COST_FALSE_POSITIVE_PKR)
            if -total_cost > best_score:
                best_score = -total_cost
                best_th = float(th)

    return best_th, best_score


def evaluate_imbalance_strategies(
    splits: Dict[str, Any],
    n_estimators: int = 200,
    max_depth: int = 5,
    learning_rate: float = 0.08,
) -> Dict[str, Any]:
    """Train and evaluate 4 imbalance handling strategies using LightGBM on Validation and Test partitions."""
    X_train = splits["X_train_trans"]
    y_train = splits["y_train"].values
    X_val = splits["X_val_trans"]
    y_val = splits["y_val"].values
    X_test = splits["X_test_trans"]
    y_test = splits["y_test"].values

    strategies_results = {}
    fitted_models = {}

    # -------------------------------------------------------------
    # 1. No Balancing (Default Empirical Distribution)
    # -------------------------------------------------------------
    m_none = LGBMClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        verbose=-1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    m_none.fit(X_train, y_train)
    p_none = m_none.predict_proba(X_test)[:, 1]
    pred_none = (p_none >= 0.50).astype(int)

    strategies_results["No Balancing"] = {
        "threshold": 0.50,
        "accuracy": float(accuracy_score(y_test, pred_none)),
        "precision": float(precision_score(y_test, pred_none, zero_division=0)),
        "recall": float(recall_score(y_test, pred_none, zero_division=0)),
        "f1": float(f1_score(y_test, pred_none, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_none)),
        "pr_auc": float(average_precision_score(y_test, p_none)),
        "probabilities": p_none,
        "predictions": pred_none,
    }
    fitted_models["No Balancing"] = m_none

    # -------------------------------------------------------------
    # 2. Class Weights (Cost-Sensitive Learning in Loss Function)
    # -------------------------------------------------------------
    m_weights = LGBMClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        class_weight="balanced",
        verbose=-1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    m_weights.fit(X_train, y_train)
    p_weights = m_weights.predict_proba(X_test)[:, 1]
    pred_weights = (p_weights >= 0.50).astype(int)

    strategies_results["Class Weights"] = {
        "threshold": 0.50,
        "accuracy": float(accuracy_score(y_test, pred_weights)),
        "precision": float(precision_score(y_test, pred_weights, zero_division=0)),
        "recall": float(recall_score(y_test, pred_weights, zero_division=0)),
        "f1": float(f1_score(y_test, pred_weights, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_weights)),
        "pr_auc": float(average_precision_score(y_test, p_weights)),
        "probabilities": p_weights,
        "predictions": pred_weights,
    }
    fitted_models["Class Weights"] = m_weights

    # -------------------------------------------------------------
    # 3. SMOTE (Synthetic Minority Over-sampling Technique)
    # -------------------------------------------------------------
    smote = SMOTE(random_state=RANDOM_STATE)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)

    m_smote = LGBMClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        verbose=-1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    m_smote.fit(X_train_sm, y_train_sm)
    p_smote = m_smote.predict_proba(X_test)[:, 1]
    pred_smote = (p_smote >= 0.50).astype(int)

    strategies_results["SMOTE"] = {
        "threshold": 0.50,
        "accuracy": float(accuracy_score(y_test, pred_smote)),
        "precision": float(precision_score(y_test, pred_smote, zero_division=0)),
        "recall": float(recall_score(y_test, pred_smote, zero_division=0)),
        "f1": float(f1_score(y_test, pred_smote, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_smote)),
        "pr_auc": float(average_precision_score(y_test, p_smote)),
        "probabilities": p_smote,
        "predictions": pred_smote,
        "resampled_train_size": len(y_train_sm),
    }
    fitted_models["SMOTE"] = m_smote

    # -------------------------------------------------------------
    # 4. Threshold Tuning (Tuned on Validation Set for Max F1)
    # -------------------------------------------------------------
    val_probs = m_none.predict_proba(X_val)[:, 1]
    best_th, val_f1 = find_optimal_threshold(y_val, val_probs, criterion="f1")

    pred_tuned = (p_none >= best_th).astype(int)

    strategies_results["Threshold Tuning"] = {
        "threshold": best_th,
        "accuracy": float(accuracy_score(y_test, pred_tuned)),
        "precision": float(precision_score(y_test, pred_tuned, zero_division=0)),
        "recall": float(recall_score(y_test, pred_tuned, zero_division=0)),
        "f1": float(f1_score(y_test, pred_tuned, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_none)),
        "pr_auc": float(average_precision_score(y_test, p_none)),
        "probabilities": p_none,
        "predictions": pred_tuned,
        "val_optimal_threshold": best_th,
        "val_f1": val_f1,
    }
    fitted_models["Threshold Tuning"] = m_none

    return {
        "strategies": strategies_results,
        "models": fitted_models,
        "accuracy_paradox": explain_accuracy_paradox(y_test),
    }


def build_imbalance_dataframe(strategy_results: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
    """Format imbalance strategy results into comparison table."""
    rows = []
    for name, s in strategy_results.items():
        rows.append({
            "Imbalance Strategy": name,
            "Decision Threshold": f"{s['threshold']:.2f}",
            "F1-Score": f"{s['f1']:.4f}",
            "Recall": f"{s['recall']:.2%}",
            "Precision": f"{s['precision']:.2%}",
            "PR-AUC": f"{s['pr_auc']:.4f}",
            "ROC-AUC": f"{s['roc_auc']:.4f}",
            "Accuracy": f"{s['accuracy']:.2%}",
        })
    df_res = pd.DataFrame(rows).sort_values("F1-Score", ascending=False).reset_index(drop=True)
    return df_res


if __name__ == "__main__":
    from src.data_loader import get_lead_data_splits
    splits = get_lead_data_splits(save_preprocessor=False)
    imb_res = evaluate_imbalance_strategies(splits)
    df_imb = build_imbalance_dataframe(imb_res["strategies"])
    print("Task 2 Imbalance Strategies Benchmark:")
    print(df_imb.to_string(index=False))
    print("\n" + imb_res["accuracy_paradox"]["explanation"])
