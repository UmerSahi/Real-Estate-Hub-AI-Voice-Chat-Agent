"""Task 5: Explainability with SHAP, Plain-Language UrduLish Generator, and Fairness Audit.
- Global SHAP Summary / Beeswarm Plots
- Local SHAP Waterfall Explanations for Individual Leads
- UrduLish & English Natural Language Reason Generator:
  "Yeh lead Hot hai kyun ke client ne 3 dafa call ki, budget market price se match karta hai, aur visit already book hai."
- Algorithmic Fairness & Unfair Bias Audit across Lead Source and Metropolitan City.
"""
from __future__ import annotations

import os
import sys
import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure UTF-8 console encoding on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import shap

from src.config import (
    FIGURES_DIR,
    HOT_THRESHOLD,
    WARM_THRESHOLD,
    format_price_pkr,
)

warnings.filterwarnings("ignore")


def compute_shap_explanations(
    model: Any,
    X_train: np.ndarray,
    X_eval: np.ndarray,
    feature_names: List[str],
    max_eval_samples: int = 300,
) -> Tuple[Any, np.ndarray, np.ndarray]:
    """Compute TreeExplainer or LinearExplainer SHAP values for test samples."""
    sample_indices = np.arange(min(len(X_eval), max_eval_samples))
    X_sample = X_eval[sample_indices]

    try:
        explainer = shap.TreeExplainer(model)
        raw_shap = explainer.shap_values(X_sample)
    except Exception:
        explainer = shap.Explainer(model, X_train[:100])
        raw_shap = explainer(X_sample).values

    # Normalize to positive conversion class (class 1)
    if isinstance(raw_shap, list) and len(raw_shap) == 2:
        shap_values_pos = raw_shap[1]
    elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
        shap_values_pos = raw_shap[:, :, 1]
    else:
        shap_values_pos = raw_shap

    return explainer, shap_values_pos, X_sample


def plot_shap_global_summary(
    shap_values_pos: np.ndarray,
    X_sample: np.ndarray,
    feature_names: List[str],
    output_dir: Path = FIGURES_DIR,
    max_display: int = 15,
) -> Path:
    """Generate and save publication-quality global SHAP beeswarm summary plot."""
    plt.figure(figsize=(11, 7), dpi=300)
    shap.summary_plot(
        shap_values_pos,
        X_sample,
        feature_names=feature_names,
        max_display=max_display,
        show=False,
    )
    plt.title("Figure 5: Global Feature Attribution (SHAP Summary Beeswarm)", fontsize=13, fontweight="bold", pad=16)
    plt.tight_layout()
    output_path = output_dir / "shap_global_importance.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def plot_shap_local_waterfall(
    explainer: Any,
    shap_values_pos: np.ndarray,
    X_sample: np.ndarray,
    feature_names: List[str],
    lead_index: int = 0,
    output_dir: Path = FIGURES_DIR,
    lead_label: str = "Lead #1041 (Hot Lead)",
) -> Path:
    """Generate and save local SHAP feature contribution bar plot for an individual prediction."""
    sample_shap = shap_values_pos[lead_index]
    top_indices = np.argsort(np.abs(sample_shap))[::-1][:10]

    top_features = [feature_names[i] for i in top_indices]
    top_shaps = [sample_shap[i] for i in top_indices]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    colors = ["#2ca02c" if val > 0 else "#d62728" for val in top_shaps]

    y_pos = np.arange(len(top_features))
    ax.barh(y_pos, top_shaps, color=colors, align="center")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(top_features, fontsize=9.5)
    ax.invert_yaxis()
    ax.axvline(0, color="black", linestyle="--", linewidth=1.0)

    ax.set_title(f"Figure 6: Local Prediction Explanation for {lead_label}", fontsize=12, fontweight="bold", pad=14)
    ax.set_xlabel("SHAP Impact on Predicted Conversion Probability (Log-Odds / P-Shift)", fontsize=10)
    ax.grid(axis="x", linestyle="--", alpha=0.3)

    for i, val in enumerate(top_shaps):
        offset = 0.01 if val >= 0 else -0.01
        ha = "left" if val >= 0 else "right"
        ax.text(val + offset, i, f"{val:+.3f}", va="center", ha=ha, fontsize=8.5, fontweight="bold")

    plt.tight_layout()
    output_path = output_dir / "shap_local_waterfall.png"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
    return output_path


def generate_plain_language_reasons(
    lead_dict: Dict[str, Any],
    probability: float,
    tier_info: Dict[str, Any],
    top_pos_features: List[Tuple[str, float]],
    top_neg_features: List[Tuple[str, float]],
) -> Dict[str, str]:
    """Translate raw SHAP attribution values into natural language UrduLish and English explanations."""
    tier = tier_info["tier"]
    prob_pct = int(round(probability * 100))

    # Human-friendly feature mapping
    friendly_names = {
        "visit_booked_yes": "site physical visit book karwai hai",
        "visit_booked": "physical property inspection",
        "number_of_calls": f"client ne {lead_dict.get('number_of_calls', 1)} martaba call ki",
        "call_duration_avg_sec": f"lambay arsay baat ki ({lead_dict.get('call_duration_avg_sec', 0)}s avg call duration)",
        "lead_engagement_score": "high engagement score show kiya",
        "lead_velocity": "inquiry turnaround velocity buhat taiz hai",
        "budget_to_market_ratio": f"budget market rate se {lead_dict.get('budget_to_market_ratio', 1.0):.1f}x match karta hai",
        "high_intent_flag": "immediate purchase intent flag active hai",
        "lead_source_walk-in": "direct office walk-in lead hai",
        "lead_source_call": "inbound direct call inquiry hai",
        "lead_source_Facebook": "Facebook digital ad se lead aayi",
        "objection_raised_none": "koi objection ya issue raise nahi kiya",
        "objection_raised_price too high": "qeemat zyada honay ka aitraz uthaya",
        "objection_raised_financing / bank loan unavailable": "bank loan ya installment na milne ki shikayat ki",
        "response_time_min": f"response time {lead_dict.get('response_time_min', 0):.0f} minute tha",
    }

    # Extract top positive drivers
    pos_reasons = []
    for feat, _ in top_pos_features[:3]:
        matched = False
        for k, v in friendly_names.items():
            if k in feat:
                pos_reasons.append(v)
                matched = True
                break
        if not matched:
            pos_reasons.append(feat.replace("_", " "))

    # Extract top negative drivers
    neg_reasons = []
    for feat, _ in top_neg_features[:2]:
        matched = False
        for k, v in friendly_names.items():
            if k in feat:
                neg_reasons.append(v)
                matched = True
                break
        if not matched:
            neg_reasons.append(feat.replace("_", " "))

    pos_str_urdu = ", ".join(pos_reasons) if pos_reasons else "standard interaction record"
    neg_str_urdu = ", ".join(neg_reasons) if neg_reasons else "koi bara negative factor nahi hai"

    # Construct UrduLish Explanation
    if tier == "Hot":
        urdulish = (
            f"Yeh lead 🔥 Hot hai (Conversion Score: {prob_pct}%) kyun ke {pos_str_urdu}. "
            f"SLA: {tier_info['sla']}. Assigned: {tier_info['assigned_role']}. "
            f"Recommended Action: {tier_info['action_plan']}"
        )
        english = (
            f"Lead classified as High Priority (🔥 Hot, {prob_pct}% Conversion Probability). "
            f"Primary conversion drivers include {', '.join(pos_reasons)}. "
            f"Protocol: Dispatch to senior consultant within 1 hour."
        )
    elif tier == "Warm":
        urdulish = (
            f"Yeh lead 🌤 Warm hai (Conversion Score: {prob_pct}%) kyun ke client ka interest darmiyana hai ({pos_str_urdu}), "
            f"lekin {neg_str_urdu}. "
            f"SLA: {tier_info['sla']}. Recommended Action: {tier_info['action_plan']}"
        )
        english = (
            f"Lead classified as Moderate Intent (🌤 Warm, {prob_pct}% Conversion Probability). "
            f"Positive signals ({', '.join(pos_reasons)}) are moderated by ({', '.join(neg_reasons)}). "
            f"Protocol: Follow up via SDR within 24 hours with society layout plans."
        )
    else:
        urdulish = (
            f"Yeh lead ❄️ Cold hai (Conversion Score: {prob_pct}%) kyun ke {neg_str_urdu}. "
            f"Is par phone call zaya na karein. Ise automated WhatsApp drip campaign par enroll karein."
        )
        english = (
            f"Lead classified as Low Intent (❄️ Cold, {prob_pct}% Conversion Probability). "
            f"Depressed conversion indicators: {', '.join(neg_reasons)}. "
            f"Protocol: Automated drip marketing only; do not allocate manual sales bandwidth."
        )

    return {
        "urdulish_explanation": urdulish,
        "english_explanation": english,
    }


def audit_model_fairness_and_bias(
    df_raw: pd.DataFrame,
    y_true: np.ndarray,
    probs: np.ndarray,
    decision_threshold: float = 0.35,
    output_dir: Path = FIGURES_DIR,
) -> Dict[str, Any]:
    """Audit algorithmic fairness across lead sources and metropolitan cities."""
    preds = (probs >= decision_threshold).astype(int)
    eval_df = df_raw.copy()
    eval_df["y_true"] = y_true
    eval_df["y_pred"] = preds
    eval_df["prob"] = probs

    audit_tables = {}

    for attr in ["lead_source", "preferred_city"]:
        sub_rows = []
        # Benchmark group is the highest volume group
        benchmark_group = eval_df[attr].value_counts().index[0]
        benchmark_sub = eval_df[eval_df[attr] == benchmark_group]
        benchmark_selection_rate = benchmark_sub["y_pred"].mean()

        for group_val, grp in eval_df.groupby(attr):
            total_grp = len(grp)
            actual_conv_rate = grp["y_true"].mean()
            selection_rate = grp["y_pred"].mean()  # % predicted positive
            disparate_impact = selection_rate / benchmark_selection_rate if benchmark_selection_rate > 0 else 1.0

            # True Positives & False Negatives
            tp = int(((grp["y_true"] == 1) & (grp["y_pred"] == 1)).sum())
            fp = int(((grp["y_true"] == 0) & (grp["y_pred"] == 1)).sum())
            fn = int(((grp["y_true"] == 1) & (grp["y_pred"] == 0)).sum())
            tn = int(((grp["y_true"] == 0) & (grp["y_pred"] == 0)).sum())

            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

            # 4/5ths rule of fairness (Disparate Impact >= 0.80)
            fairness_verdict = "Fair (Passed 80% Rule)" if disparate_impact >= 0.80 else "Disparity Flagged (<0.80)"

            sub_rows.append({
                attr: group_val,
                "Count": total_grp,
                "Actual Conversion (%)": actual_conv_rate * 100.0,
                "Selection Rate (%)": selection_rate * 100.0,
                "Disparate Impact (DIR)": disparate_impact,
                "Recall (%)": recall * 100.0,
                "Precision (%)": precision * 100.0,
                "FPR (%)": fpr * 100.0,
                "Fairness Verdict": fairness_verdict,
            })

        audit_tables[attr] = pd.DataFrame(sub_rows).sort_values("Count", ascending=False).reset_index(drop=True)

    # Plot Multi-Panel Fairness Figure
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), dpi=300)

    # Panel 1: Lead Source Selection & Conversion
    df_src = audit_tables["lead_source"]
    sns.barplot(data=df_src, x="lead_source", y="Selection Rate (%)", palette="Blues_d", ax=axes[0], hue="lead_source", legend=False)
    axes[0].axhline(80, color="gray", linestyle="--", alpha=0.5, label="Parity Reference")
    axes[0].set_title("Lead Source Selection Rate & Fairness", fontsize=12, fontweight="bold", pad=12)
    axes[0].set_ylabel("Positive Selection Rate (%)", fontsize=10)
    axes[0].set_xlabel("Acquisition Channel", fontsize=10)
    axes[0].grid(axis="y", linestyle="--", alpha=0.3)
    for p in axes[0].patches:
        h = p.get_height()
        axes[0].annotate(f"{h:.1f}%", (p.get_x() + p.get_width() / 2.0, h + 1.0), ha="center", fontsize=8.5, fontweight="bold")

    # Panel 2: Metropolitan City Selection Rate
    df_city = audit_tables["preferred_city"]
    sns.barplot(data=df_city, x="preferred_city", y="Selection Rate (%)", palette="Greens_d", ax=axes[1], hue="preferred_city", legend=False)
    axes[1].set_title("Metropolitan City Selection Rate & Equity", fontsize=12, fontweight="bold", pad=12)
    axes[1].set_ylabel("Positive Selection Rate (%)", fontsize=10)
    axes[1].set_xlabel("Preferred City", fontsize=10)
    axes[1].grid(axis="y", linestyle="--", alpha=0.3)
    for p in axes[1].patches:
        h = p.get_height()
        axes[1].annotate(f"{h:.1f}%", (p.get_x() + p.get_width() / 2.0, h + 1.0), ha="center", fontsize=8.5, fontweight="bold")

    fig.suptitle("Figure 7: Subgroup Algorithmic Fairness & Bias Audit", fontsize=14, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.93])
    file_path = output_dir / "fairness_subgroup_analysis.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()

    return {
        "lead_source_audit": audit_tables["lead_source"],
        "city_audit": audit_tables["preferred_city"],
        "figure_path": file_path,
    }


if __name__ == "__main__":
    from src.data_loader import get_lead_data_splits
    from src.classification_models import train_classification_models

    splits = get_lead_data_splits(save_preprocessor=False)
    clf_res = train_classification_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )
    best_model = clf_res["models"]["LightGBM"]
    X_test_trans = splits["X_test_trans"]
    feat_names = splits["feature_names"]

    explainer, shaps, X_sample = compute_shap_explanations(best_model, splits["X_train_trans"], X_test_trans, feat_names)
    plot_shap_global_summary(shaps, X_sample, feat_names)
    plot_shap_local_waterfall(explainer, shaps, X_sample, feat_names, lead_index=0)

    # Test Plain Language Generator
    test_lead = splits["df_test_raw"].iloc[0].to_dict()
    prob = float(clf_res["results"]["LightGBM"]["probabilities"][0])
    from src.lead_segmentation import classify_lead_tier
    tier = classify_lead_tier(prob)
    top_pos = [(feat_names[i], shaps[0][i]) for i in np.argsort(shaps[0])[::-1] if shaps[0][i] > 0]
    top_neg = [(feat_names[i], shaps[0][i]) for i in np.argsort(shaps[0]) if shaps[0][i] < 0]
    reasons = generate_plain_language_reasons(test_lead, prob, tier, top_pos, top_neg)

    print("Sample UrduLish Explanation:\n", reasons["urdulish_explanation"])
    print("\nSample English Explanation:\n", reasons["english_explanation"])

    # Fairness Audit
    fairness = audit_model_fairness_and_bias(splits["df_test_raw"], splits["y_test"].values, clf_res["results"]["LightGBM"]["probabilities"])
    print("\nLead Source Fairness Audit Table:")
    print(fairness["lead_source_audit"][["lead_source", "Count", "Selection Rate (%)", "Disparate Impact (DIR)", "Fairness Verdict"]].to_string(index=False))
