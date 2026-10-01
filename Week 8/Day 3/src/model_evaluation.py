"""Task 3: Comprehensive Evaluation and Cost-Optimal Decision Framework.
Computes:
- Precision, Recall, F1, ROC-AUC, PR-AUC
- Confusion Matrices (Default vs Cost-Optimal vs Top-20%)
- Precision@Top-20% & Recall@Top-20% (Business Scenario Evaluation)
- Calibration Curves (Probability Reliability)
- Cost-Benefit Decision Analysis (FN vs FP penalty tradeoffs)
- Publication-quality diagnostic figures.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
    confusion_matrix,
)

from src.config import (
    COST_FALSE_NEGATIVE_PKR,
    COST_FALSE_POSITIVE_PKR,
    FIGURES_DIR,
)

warnings.filterwarnings("ignore")


def compute_top_k_metrics(
    y_true: np.ndarray, y_prob: np.ndarray, top_k_ratio: float = 0.20
) -> Dict[str, Any]:
    """Compute Precision@Top-K and Recall@Top-K (e.g. Top 20% capacity constraint)."""
    total_leads = len(y_true)
    top_k_count = max(1, int(total_leads * top_k_ratio))

    # Rank indices by descending predicted probability
    ranked_indices = np.argsort(y_prob)[::-1]
    top_k_indices = ranked_indices[:top_k_count]

    top_k_actual = y_true[top_k_indices]
    conversions_in_top_k = int(np.sum(top_k_actual == 1))
    total_actual_conversions = int(np.sum(y_true == 1))

    precision_top_k = conversions_in_top_k / top_k_count
    recall_top_k = (
        conversions_in_top_k / total_actual_conversions
        if total_actual_conversions > 0
        else 0.0
    )
    baseline_conversion_rate = total_actual_conversions / total_leads
    lift = (
        precision_top_k / baseline_conversion_rate
        if baseline_conversion_rate > 0
        else 1.0
    )

    # Threshold corresponding to the Top-K cutoff
    cutoff_threshold = float(y_prob[top_k_indices[-1]])

    return {
        "top_k_ratio": top_k_ratio,
        "top_k_leads_called": top_k_count,
        "total_leads": total_leads,
        "total_actual_conversions": total_actual_conversions,
        "conversions_captured": conversions_in_top_k,
        "precision_at_top_k": float(precision_top_k),
        "recall_at_top_k": float(recall_top_k),
        "baseline_rate": float(baseline_conversion_rate),
        "lift": float(lift),
        "cutoff_threshold": cutoff_threshold,
    }


def compute_cost_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    cost_fn: float = COST_FALSE_NEGATIVE_PKR,
    cost_fp: float = COST_FALSE_POSITIVE_PKR,
) -> Dict[str, Any]:
    """Calculate total expected business loss across decision thresholds."""
    thresholds = np.linspace(0.05, 0.90, 86)
    costs = []
    fns = []
    fps = []
    tps = []
    tns = []

    min_cost = float("inf")
    best_th = 0.50

    for th in thresholds:
        preds = (y_prob >= th).astype(int)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()
        cost = (fn * cost_fn) + (fp * cost_fp)

        costs.append(cost)
        fns.append(fn)
        fps.append(fp)
        tps.append(tp)
        tns.append(tn)

        if cost < min_cost:
            min_cost = cost
            best_th = float(th)

    return {
        "thresholds": thresholds,
        "costs": np.array(costs),
        "fns": np.array(fns),
        "fps": np.array(fps),
        "tps": np.array(tps),
        "tns": np.array(tns),
        "optimal_cost_threshold": best_th,
        "min_cost_pkr": min_cost,
    }


def plot_roc_and_pr_curves(
    model_probs: Dict[str, np.ndarray],
    y_true: np.ndarray,
    output_dir: Path = FIGURES_DIR,
):
    """Plot dual-panel ROC and Precision-Recall Curves."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), dpi=300)

    palette = {
        "XGBoost": "#1f77b4",
        "LightGBM": "#2ca02c",
        "CatBoost": "#ff7f0e",
        "Random Forest": "#9467bd",
        "Logistic Regression": "#8c564b",
    }

    # Panel 1: ROC Curve
    for name, probs in model_probs.items():
        fpr, tpr, _ = roc_curve(y_true, probs)
        auc = roc_auc_score(y_true, probs)
        color = palette.get(name, "#333333")
        axes[0].plot(fpr, tpr, label=f"{name} (AUC = {auc:.3f})", color=color, linewidth=2)

    axes[0].plot([0, 1], [0, 1], "k--", label="Random Baseline (AUC = 0.500)", linewidth=1.2)
    axes[0].set_title("Receiver Operating Characteristic (ROC)", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    axes[0].set_ylabel("True Positive Rate (Recall)", fontsize=11)
    axes[0].set_xlim([0.0, 1.0])
    axes[0].set_ylim([0.0, 1.05])
    axes[0].legend(loc="lower right", fontsize=9.5)
    axes[0].grid(True, linestyle="--", alpha=0.3)

    # Panel 2: Precision-Recall Curve
    baseline_pr = float(np.mean(y_true))
    for name, probs in model_probs.items():
        precision, recall, _ = precision_recall_curve(y_true, probs)
        pr_auc = average_precision_score(y_true, probs)
        color = palette.get(name, "#333333")
        axes[1].plot(recall, precision, label=f"{name} (PR-AUC = {pr_auc:.3f})", color=color, linewidth=2)

    axes[1].axhline(baseline_pr, color="k", linestyle="--", label=f"Empirical Baseline ({baseline_pr:.1%})", linewidth=1.2)
    axes[1].set_title("Precision-Recall (PR) Curve", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Recall (Coverage)", fontsize=11)
    axes[1].set_ylabel("Precision (Accuracy of Call)", fontsize=11)
    axes[1].set_xlim([0.0, 1.0])
    axes[1].set_ylim([0.0, 1.05])
    axes[1].legend(loc="lower left", fontsize=9.5)
    axes[1].grid(True, linestyle="--", alpha=0.3)

    fig.suptitle("Figure 1: Model Discrimination Fidelity (ROC & PR Curves)", fontsize=15, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.94])
    output_path = output_dir / "roc_pr_curves_comparison.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def plot_confusion_matrices(
    y_true: np.ndarray,
    probs: np.ndarray,
    output_dir: Path = FIGURES_DIR,
):
    """Plot multi-panel confusion matrices: Default (0.50), Balanced (0.25), and Top-20% capacity."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), dpi=300)

    # Cutoffs to compare
    top_20_count = int(len(y_true) * 0.20)
    top_20_th = float(np.sort(probs)[::-1][top_20_count - 1])

    cutoffs = [
        ("Default Threshold (th = 0.50)", 0.50),
        ("Cost-Balanced Policy (th = 0.25)", 0.25),
        (f"Top 20% Capacity (th = {top_20_th:.2f})", top_20_th),
    ]

    for idx, (title, th) in enumerate(cutoffs):
        preds = (probs >= th).astype(int)
        cm = confusion_matrix(y_true, preds)
        tn, fp, fn, tp = cm.ravel()
        cost_pkr = (fn * COST_FALSE_NEGATIVE_PKR) + (fp * COST_FALSE_POSITIVE_PKR)

        annot = np.array([
            [f"True Neg (TN)\n{tn:,}", f"False Pos (FP)\n{fp:,}\n(Wasted Calls)"],
            [f"False Neg (FN)\n{fn:,}\n(Lost Deals!)", f"True Pos (TP)\n{tp:,}\n(Closed Deals)"],
        ])

        sns.heatmap(
            cm,
            annot=annot,
            fmt="",
            cmap="Blues" if idx == 0 else ("Greens" if idx == 1 else "Oranges"),
            cbar=False,
            ax=axes[idx],
            annot_kws={"fontsize": 10, "fontweight": "bold"},
        )
        axes[idx].set_title(f"{title}\nLoss: ~{cost_pkr/100_000:,.1f} Lac PKR", fontsize=11, fontweight="bold", pad=10)
        axes[idx].set_xlabel("Predicted Label", fontsize=10)
        axes[idx].set_ylabel("Actual Label", fontsize=10)
        axes[idx].set_xticklabels(["Did Not Convert", "Converted"])
        axes[idx].set_yticklabels(["Did Not Convert", "Converted"])

    fig.suptitle("Figure 2: Confusion Matrices Across Decision Policies", fontsize=14, fontweight="bold", y=0.99)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    output_path = output_dir / "confusion_matrix_top_models.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def plot_calibration_curves(
    model_probs: Dict[str, np.ndarray],
    y_true: np.ndarray,
    output_dir: Path = FIGURES_DIR,
):
    """Plot Calibration Reliability Curves comparing predicted probability with empirical conversion."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)

    palette = {"XGBoost": "#1f77b4", "LightGBM": "#2ca02c", "CatBoost": "#ff7f0e", "Logistic Regression": "#8c564b"}

    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration (Ideal)", linewidth=1.5)

    for name, probs in model_probs.items():
        if name not in palette:
            continue
        prob_true, prob_pred = calibration_curve(y_true, probs, n_bins=8, strategy="uniform")
        ax.plot(prob_pred, prob_true, marker="o", label=f"{name}", color=palette[name], linewidth=2)

    ax.set_title("Probability Calibration Reliability Diagram", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Mean Predicted Probability", fontsize=11)
    ax.set_ylabel("Empirical Fraction of Conversions", fontsize=11)
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.0])
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)

    plt.tight_layout()
    output_path = output_dir / "calibration_curves.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def plot_imbalance_comparison_chart(
    df_imbalance: pd.DataFrame,
    output_dir: Path = FIGURES_DIR,
):
    """Plot bar chart comparing F1, Recall, Precision, and PR-AUC across imbalance strategies."""
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=300)

    plot_df = df_imbalance.copy()
    plot_df["F1"] = plot_df["F1-Score"].astype(float)
    plot_df["Recall"] = plot_df["Recall"].str.rstrip("%").astype(float) / 100.0
    plot_df["Precision"] = plot_df["Precision"].str.rstrip("%").astype(float) / 100.0
    plot_df["PR-AUC"] = plot_df["PR-AUC"].astype(float)

    melted = plot_df.melt(
        id_vars=["Imbalance Strategy"],
        value_vars=["F1", "Recall", "Precision", "PR-AUC"],
        var_name="Metric",
        value_name="Score",
    )

    sns.barplot(
        data=melted,
        x="Imbalance Strategy",
        y="Score",
        hue="Metric",
        palette="viridis",
        ax=ax,
    )

    ax.set_title("Figure 3: Performance Across Class Imbalance Mitigation Strategies", fontsize=13, fontweight="bold", pad=14)
    ax.set_ylabel("Metric Score", fontsize=11)
    ax.set_xlabel("Imbalance Strategy", fontsize=11)
    ax.set_ylim(0, 1.15)
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.legend(loc="upper right", ncol=4, fontsize=9.5)

    for p in ax.patches:
        height = p.get_height()
        if height > 0.05:
            ax.annotate(
                f"{height:.2f}",
                (p.get_x() + p.get_width() / 2.0, height + 0.02),
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

    plt.tight_layout()
    output_path = output_dir / "imbalance_strategy_comparison.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


if __name__ == "__main__":
    from src.data_loader import get_lead_data_splits
    from src.classification_models import train_classification_models

    splits = get_lead_data_splits(save_preprocessor=False)
    clf_res = train_classification_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )

    y_test = splits["y_test"].values
    top_model_probs = {
        name: res["probabilities"] for name, res in clf_res["results"].items()
    }

    # Top-20% evaluation
    top20 = compute_top_k_metrics(y_test, clf_res["results"]["LightGBM"]["probabilities"], top_k_ratio=0.20)
    print("Precision@Top-20% Evaluation:")
    for k, v in top20.items():
        print(f"  {k}: {v}")

    # Cost curve
    cost_info = compute_cost_curve(y_test, clf_res["results"]["LightGBM"]["probabilities"])
    print(f"\nOptimal Cost Decision Threshold: {cost_info['optimal_cost_threshold']:.2f}")

    # Generate figures
    plot_roc_and_pr_curves(top_model_probs, y_test)
    plot_confusion_matrices(y_test, clf_res["results"]["LightGBM"]["probabilities"])
    plot_calibration_curves(top_model_probs, y_test)
    print("[OK] Task 3 Evaluation Figures Generated Successfully!")
