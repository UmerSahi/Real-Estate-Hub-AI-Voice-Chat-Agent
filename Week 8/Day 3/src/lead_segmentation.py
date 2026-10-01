"""Task 4: Lead Segmentation & Customer Persona Discovery.
- Segments leads into Hot (🔥), Warm (🌤), and Cold (❄️) operational tiers.
- Discovers distinct Customer Personas using K-Means clustering.
- Defines sales playbooks and SLA action plans for each persona and tier.
"""
from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from src.config import (
    FIGURES_DIR,
    HOT_THRESHOLD,
    KMEANS_PERSONAS_MODEL_PATH,
    PERSONA_SCALER_PATH,
    RANDOM_STATE,
    WARM_THRESHOLD,
    format_price_pkr,
)

warnings.filterwarnings("ignore")

PERSONA_FEATURE_COLS = [
    "budget_pkr",
    "number_of_calls",
    "call_duration_avg_sec",
    "response_time_min",
    "days_since_first_contact",
    "lead_engagement_score",
    "budget_to_market_ratio",
    "lead_velocity",
]


def classify_lead_tier(probability: float) -> Dict[str, Any]:
    """Assign operational business category and sales SLA based on predicted conversion probability."""
    if probability >= HOT_THRESHOLD:
        return {
            "tier": "Hot",
            "emoji": "🔥",
            "label": "🔥 Hot Lead",
            "sla": "Call within 1 hour",
            "assigned_role": "Senior Property Consultant / Closer",
            "channel": "Direct Priority Phone Call",
            "action_plan": "Lock physical site visit; discuss commercial terms, payment schedule, and immediate token deposit.",
            "probability": float(probability),
        }
    elif probability >= WARM_THRESHOLD:
        return {
            "tier": "Warm",
            "emoji": "🌤",
            "label": "🌤 Warm Lead",
            "sla": "Call within 24 hours",
            "assigned_role": "Sales Development Representative (SDR)",
            "channel": "Consultative Phone Call & WhatsApp Brochure",
            "action_plan": "Share curated society walkthrough video, layout plans, and price comparison sheet.",
            "probability": float(probability),
        }
    else:
        return {
            "tier": "Cold",
            "emoji": "❄️",
            "label": "❄️ Cold Lead",
            "sla": "Automated Nurture (No manual call)",
            "assigned_role": "Marketing Automation Engine",
            "channel": "WhatsApp Drip Campaign & Weekly Email Digest",
            "action_plan": "Enroll in automated market trends drip; send notifications for flexible installment plot launches.",
            "probability": float(probability),
        }


class CustomerPersonaEngine:
    """Discovers and profiles real estate customer personas using unsupervised K-Means clustering."""

    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=RANDOM_STATE, n_init=10)
        self.pca = PCA(n_components=2, random_state=RANDOM_STATE)
        self.is_fitted = False
        self.persona_profiles: Dict[int, Dict[str, Any]] = {}

    def fit(self, df_raw: pd.DataFrame) -> CustomerPersonaEngine:
        """Fit scaler and K-Means clustering on lead behavioral features."""
        X_sub = df_raw[PERSONA_FEATURE_COLS].copy()
        X_scaled = self.scaler.fit_transform(X_sub)
        clusters = self.kmeans.fit_predict(X_scaled)
        self.pca.fit(X_scaled)

        df_clustered = df_raw.copy()
        df_clustered["cluster"] = clusters

        # Build archetype profiles for each cluster
        cluster_summaries = {}
        for c in range(self.n_clusters):
            c_df = df_clustered[df_clustered["cluster"] == c]
            cluster_summaries[c] = {
                "median_budget": float(c_df["budget_pkr"].median()),
                "avg_calls": float(c_df["number_of_calls"].mean()),
                "avg_duration_sec": float(c_df["call_duration_avg_sec"].mean()),
                "avg_response_min": float(c_df["response_time_min"].mean()),
                "conversion_rate": float((c_df["converted"] == "yes").mean()),
                "visit_rate": float((c_df["visit_booked"] == "yes").mean()),
                "count": len(c_df),
                "pct": len(c_df) / len(df_raw),
            }

        # Map cluster IDs to realistic real estate personas based on budget & engagement
        sorted_by_budget = sorted(cluster_summaries.items(), key=lambda kv: kv[1]["median_budget"])
        sorted_by_calls = sorted(cluster_summaries.items(), key=lambda kv: kv[1]["avg_calls"])

        # Determine which cluster is high-ticket investor, active family buyer, and budget renter/browser
        investor_c = max(cluster_summaries.items(), key=lambda kv: kv[1]["median_budget"])[0]
        active_buyer_c = max(
            [c for c in range(self.n_clusters) if c != investor_c],
            key=lambda c: cluster_summaries[c]["avg_calls"],
        )
        remaining = [c for c in range(self.n_clusters) if c not in [investor_c, active_buyer_c]][0]

        self.persona_profiles[investor_c] = {
            "name": "Overseas / High-Net-Worth Capital Investor",
            "archetype": "Investor",
            "description": "High liquidity prospect seeking capital appreciation or commercial rental yield; inquiries focused on prime sectors.",
            "median_budget_formatted": format_price_pkr(cluster_summaries[investor_c]["median_budget"]),
            "key_traits": "High budget, fast response turnaround, commercial/file interest, demands verified NOC documents.",
            "recommended_pitch": "Highlight 8-10% rental yields, capital growth projections, fast file transfers, and overseas tax treaty advantages.",
            **cluster_summaries[investor_c],
        }

        self.persona_profiles[active_buyer_c] = {
            "name": "Urgent Family Homebuyer (Active Inquirer)",
            "archetype": "Homebuyer",
            "description": "Family-oriented end-user looking to relocate into ready-to-move housing or secure residential plots.",
            "median_budget_formatted": format_price_pkr(cluster_summaries[active_buyer_c]["median_budget"]),
            "key_traits": "High phone engagement, long call durations, booked physical site visit, family decision-making dynamic.",
            "recommended_pitch": "Focus on gated community security, immediate possession, school/park proximity, and vetted construction quality.",
            **cluster_summaries[active_buyer_c],
        }

        self.persona_profiles[remaining] = {
            "name": "First-Time Explorer / Budget Inquirer",
            "archetype": "Explorer/Renter",
            "description": "Price-sensitive early-stage researcher exploring rental apartments or affordable installment plots.",
            "median_budget_formatted": format_price_pkr(cluster_summaries[remaining]["median_budget"]),
            "key_traits": "Lower budget, longer response delay, multiple financing/bank objections, low site visit booking rate.",
            "recommended_pitch": "Introduce flexible 3-5 year installment plans, affordable rental options, and low-downpayment payment plans.",
            **cluster_summaries[remaining],
        }

        self.is_fitted = True
        return self

    def predict_persona(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single lead dictionary into a customer persona."""
        if not self.is_fitted:
            raise ValueError("CustomerPersonaEngine must be fitted first.")

        row_vals = [float(lead_dict.get(col, 0.0)) for col in PERSONA_FEATURE_COLS]
        row_scaled = self.scaler.transform([row_vals])
        cluster_id = int(self.kmeans.predict(row_scaled)[0])
        return self.persona_profiles[cluster_id]
    def save(self, model_path: Path = KMEANS_PERSONAS_MODEL_PATH):
        """Serialize full CustomerPersonaEngine instance."""
        joblib.dump(self, model_path)

    @classmethod
    def load(cls, model_path: Path = KMEANS_PERSONAS_MODEL_PATH) -> CustomerPersonaEngine:
        """Deserialize full CustomerPersonaEngine instance."""
        return joblib.load(model_path)

    def plot_persona_clusters(self, df_raw: pd.DataFrame, output_dir: Path = FIGURES_DIR) -> Path:
        """Generate high-resolution cluster distribution and radar/bar comparisons."""
        X_sub = df_raw[PERSONA_FEATURE_COLS].copy()
        X_scaled = self.scaler.transform(X_sub)
        coords = self.pca.transform(X_scaled)
        clusters = self.kmeans.predict(X_scaled)

        plot_df = pd.DataFrame({
            "PCA1": coords[:, 0],
            "PCA2": coords[:, 1],
            "Cluster": [self.persona_profiles[c]["name"] for c in clusters],
            "Conversion": df_raw["converted"].values,
        })

        fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=300)

        # Panel 1: 2D PCA Space of Customer Personas
        palette = {
            self.persona_profiles[c]["name"]: color
            for c, color in zip(self.persona_profiles.keys(), ["#1f77b4", "#2ca02c", "#d62728"])
        }
        sns.scatterplot(
            data=plot_df,
            x="PCA1",
            y="PCA2",
            hue="Cluster",
            palette=palette,
            style="Conversion",
            alpha=0.65,
            s=45,
            ax=axes[0],
        )
        axes[0].set_title("Customer Personas in Latent Behavioral Space (PCA)", fontsize=12, fontweight="bold", pad=12)
        axes[0].set_xlabel("Principal Component 1 (Engagement & Volume)", fontsize=10)
        axes[0].set_ylabel("Principal Component 2 (Budget & Value)", fontsize=10)
        axes[0].legend(loc="upper right", fontsize=8.5)
        axes[0].grid(True, linestyle="--", alpha=0.3)

        # Panel 2: Conversion Rate & Budget by Persona
        summary_rows = []
        for c, p in self.persona_profiles.items():
            summary_rows.append({
                "Persona": p["name"].split("(")[0].strip(),
                "Conversion Rate (%)": p["conversion_rate"] * 100.0,
                "Site Visit Rate (%)": p["visit_rate"] * 100.0,
                "Avg Calls": p["avg_calls"] * 10.0,  # Scaled for visual comparison
            })
        df_summary = pd.DataFrame(summary_rows)
        df_melt = df_summary.melt(id_vars=["Persona"], var_name="Behavioral Metric", value_name="Score")

        sns.barplot(data=df_melt, x="Persona", y="Score", hue="Behavioral Metric", palette="Blues_r", ax=axes[1])
        axes[1].set_title("Persona Behavioral & Conversion Benchmarks", fontsize=12, fontweight="bold", pad=12)
        axes[1].set_ylabel("Percentage / Scaled Score", fontsize=10)
        axes[1].set_xlabel("Customer Persona", fontsize=10)
        axes[1].tick_params(axis="x", rotation=15)
        axes[1].legend(loc="upper right", fontsize=8.5)
        axes[1].grid(axis="y", linestyle="--", alpha=0.3)

        fig.suptitle("Figure 4: Unsupervised Customer Persona Clustering (K-Means)", fontsize=14, fontweight="bold", y=0.98)
        plt.tight_layout(rect=[0, 0.02, 1, 0.93])
        file_path = output_dir / "customer_personas_clusters.png"
        plt.savefig(file_path, bbox_inches="tight")
        plt.close()
        return file_path


if __name__ == "__main__":
    from src.data_loader import load_raw_lead_data
    df = load_raw_lead_data()
    engine = CustomerPersonaEngine(n_clusters=3).fit(df)
    engine.save()
    engine.plot_persona_clusters(df)
    print("Discovered Personas:")
    for c, p in engine.persona_profiles.items():
        print(f"\n[Persona {c}]: {p['name']}")
        print(f"  Median Budget: {p['median_budget_formatted']}")
        print(f"  Conversion Rate: {p['conversion_rate']:.1%}")
        print(f"  Pitch: {p['recommended_pitch']}")
