"""Exploratory Data Analysis (EDA) Module for Week 8 Capstone Project.
Generates publication-quality charts for:
1. Price distribution (raw vs log-transformed)
2. Price per marla by city and top societies
3. Correlation heatmap for property features
4. Multi-panel effect of bedrooms, age, and corner plots on price
5. Lead conversion rate by source and purpose
6. Class imbalance in the leads dataset

Saves all figures to `eda/figures/`.
"""
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import (
    FIGURES_DIR,
    PROPERTIES_CLEANED_PATH,
    LEADS_CLEANED_PATH,
    RANDOM_STATE,
)

# Professional visual palette configuration
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
PRIMARY_COLOR = "#1f4e79"
SECONDARY_COLOR = "#d9534f"
ACCENT_COLOR = "#2e7d32"
PALETTE = ["#1f4e79", "#2e7d32", "#f39c12", "#d9534f", "#8e44ad", "#16a085"]


def setup_figure_style():
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.edgecolor"] = "#cccccc"
    plt.rcParams["axes.linewidth"] = 0.8


def plot_price_distribution(df_prop: pd.DataFrame, output_dir: Path):
    """Figure 1: Price distribution (raw in Crore vs log-transformed)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=300)
    
    # Raw price in Crore PKR (1 Crore = 10 Million PKR)
    price_crore = df_prop["price_pkr"] / 10_000_000.0
    
    sns.histplot(price_crore, bins=40, kde=True, ax=axes[0], color="#1f4e79", edgecolor="white")
    axes[0].set_title("Raw Price Distribution (Severe Positive Skew)", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("Listing Price (Crore PKR)", fontsize=11)
    axes[0].set_ylabel("Listing Count", fontsize=11)
    
    # Add median line
    median_val = price_crore.median()
    axes[0].axvline(median_val, color="#d9534f", linestyle="--", linewidth=1.5, label=f"Median: {median_val:.2f} Cr")
    axes[0].legend(frameon=True)

    # Log-transformed price
    log_price = np.log10(df_prop["price_pkr"])
    sns.histplot(log_price, bins=40, kde=True, ax=axes[1], color="#2e7d32", edgecolor="white")
    axes[1].set_title("Log10-Transformed Price Distribution (Near Normal)", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Log10(Price in PKR)", fontsize=11)
    axes[1].set_ylabel("Listing Count", fontsize=11)
    
    # Add mean line
    mean_log = log_price.mean()
    axes[1].axvline(mean_log, color="#f39c12", linestyle="--", linewidth=1.5, label=f"Mean Log10: {mean_log:.2f}")
    axes[1].legend(frameon=True)

    plt.suptitle("Figure 1: Property Valuation Distribution Analysis", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    file_path = output_dir / "price_dist_raw_vs_log.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def plot_price_per_marla_by_city_society(df_prop: pd.DataFrame, output_dir: Path):
    """Figure 2: Price per Marla comparison across Cities and Top Societies."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), dpi=300)
    
    df = df_prop.copy()
    df["price_per_marla_lac"] = (df["price_pkr"] / df["area_marla"]) / 100_000.0

    # Panel A: Price per marla by City
    city_order = df.groupby("city")["price_per_marla_lac"].median().sort_values(ascending=False).index
    sns.boxplot(
        data=df, x="city", y="price_per_marla_lac", order=city_order,
        ax=axes[0], palette="Blues_r", showfliers=False
    )
    axes[0].set_title("Median Price per Marla by Metropolitan City", fontsize=13, fontweight="bold", pad=12)
    axes[0].set_xlabel("City", fontsize=11)
    axes[0].set_ylabel("Price per Marla (Lacs PKR)", fontsize=11)

    # Panel B: Top 10 Societies across Pakistan
    top_societies = (
        df.groupby("area_society")["price_per_marla_lac"]
        .median()
        .sort_values(ascending=False)
        .head(10)
    )
    sns.barplot(
        x=top_societies.values, y=top_societies.index,
        ax=axes[1], palette="crest"
    )
    axes[1].set_title("Top 10 High-Valuation Housing Societies in Pakistan", fontsize=13, fontweight="bold", pad=12)
    axes[1].set_xlabel("Median Price per Marla (Lacs PKR)", fontsize=11)
    axes[1].set_ylabel("Society / Sector", fontsize=11)
    for i, val in enumerate(top_societies.values):
        axes[1].text(val + 0.5, i, f"{val:.1f} Lac", va="center", fontsize=9, fontweight="bold")

    plt.suptitle("Figure 2: Geographic Valuation Gradient Across Pakistan", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    file_path = output_dir / "price_per_marla_by_city_society.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def plot_correlation_heatmap(df_prop: pd.DataFrame, output_dir: Path):
    """Figure 3: Feature Correlation Heatmap."""
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    
    numeric_cols = [
        "price_pkr", "area_marla", "covered_area", "bedrooms", 
        "bathrooms", "age_years", "floors", "dist_main_road_km", 
        "dist_school_km", "dist_hospital_km"
    ]
    df_num = df_prop[numeric_cols].copy()
    df_num.rename(columns={
        "price_pkr": "Price",
        "area_marla": "Plot Area",
        "covered_area": "Covered Area",
        "bedrooms": "Bedrooms",
        "bathrooms": "Bathrooms",
        "age_years": "Age (Yrs)",
        "floors": "Floors",
        "dist_main_road_km": "Dist Main Rd",
        "dist_school_km": "Dist School",
        "dist_hospital_km": "Dist Hospital",
    }, inplace=True)

    corr = df_num.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    
    sns.heatmap(
        corr, mask=mask, annot=True, fmt=".2f", cmap="vlag", 
        vmin=-0.8, vmax=0.8, square=True, linewidths=0.5, cbar_kws={"shrink": 0.8},
        ax=ax
    )
    ax.set_title("Figure 3: Inter-Feature Correlation Heatmap for Property Listings", fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    file_path = output_dir / "property_correlation_heatmap.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def plot_effect_bedrooms_age_corner(df_prop: pd.DataFrame, output_dir: Path):
    """Figure 4: Effect of Bedrooms, Age, and Corner Plots on Property Price."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    df = df_prop.copy()
    df["price_crore"] = df["price_pkr"] / 10_000_000.0

    # Panel 1: Bedrooms vs Price
    bed_filtered = df[df["bedrooms"] <= 8]
    sns.boxplot(
        data=bed_filtered, x="bedrooms", y="price_crore", 
        ax=axes[0], palette="Blues", showfliers=False
    )
    axes[0].set_title("Price Scaling by Bedroom Count", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Bedrooms", fontsize=11)
    axes[0].set_ylabel("Price (Crore PKR)", fontsize=11)

    # Panel 2: Age vs Price (Binned Age)
    df["age_bucket"] = pd.cut(
        df["age_years"], 
        bins=[-1, 1, 5, 10, 20, 50], 
        labels=["Brand New (<=1y)", "1-5y", "6-10y", "11-20y", "20y+"]
    )
    sns.barplot(
        data=df, x="age_bucket", y="price_crore",
        ax=axes[1], palette="Reds_r", errorbar=None
    )
    axes[1].set_title("Price Depreciation Across Age Buckets", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Property Age", fontsize=11)
    axes[1].set_ylabel("Average Price (Crore PKR)", fontsize=11)
    axes[1].tick_params(axis="x", rotation=20)

    # Panel 3: Corner & Park-Facing Premium
    df["plot_feature"] = "Standard Plot"
    df.loc[(df["is_corner"] == "yes") & (df["is_park_facing"] == "no"), "plot_feature"] = "Corner Only"
    df.loc[(df["is_corner"] == "no") & (df["is_park_facing"] == "yes"), "plot_feature"] = "Park-Facing Only"
    df.loc[(df["is_corner"] == "yes") & (df["is_park_facing"] == "yes"), "plot_feature"] = "Corner + Park Facing"
    
    order = ["Standard Plot", "Corner Only", "Park-Facing Only", "Corner + Park Facing"]
    sns.barplot(
        data=df, x="plot_feature", y="price_crore", order=order,
        ax=axes[2], palette="Greens", errorbar=None
    )
    axes[2].set_title("Premium for Corner & Park-Facing Plots", fontsize=12, fontweight="bold")
    axes[2].set_xlabel("Plot Location Attributes", fontsize=11)
    axes[2].set_ylabel("Average Price (Crore PKR)", fontsize=11)
    axes[2].tick_params(axis="x", rotation=25)

    plt.suptitle("Figure 4: Impact of Key Architectural & Positional Drivers on Price", fontsize=15, fontweight="bold", y=1.03)
    plt.tight_layout()
    file_path = output_dir / "effect_bedrooms_age_corner.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def plot_lead_conversion_by_source_purpose(df_leads: pd.DataFrame, output_dir: Path):
    """Figure 5: Lead Conversion Rate by Source Channel and Transaction Purpose."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), dpi=300)
    df = df_leads.copy()
    df["converted_int"] = (df["converted"] == "yes").astype(int)

    # Panel 1: Conversion Rate by Lead Source
    source_conv = (
        df.groupby("lead_source")["converted_int"].mean() * 100.0
    ).sort_values(ascending=False)
    
    sns.barplot(x=source_conv.index, y=source_conv.values, ax=axes[0], palette="mako")
    axes[0].set_title("Conversion Rate (%) by Acquisition Channel", fontsize=12, fontweight="bold", pad=12)
    axes[0].set_xlabel("Lead Source", fontsize=11)
    axes[0].set_ylabel("Conversion Rate (%)", fontsize=11)
    axes[0].set_ylim(0, max(source_conv.values) * 1.25)
    for i, val in enumerate(source_conv.values):
        axes[0].text(i, val + 1.0, f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold")

    # Panel 2: Conversion Rate by Purpose & Visit Booked Status
    purpose_visit = (
        df.groupby(["purpose", "visit_booked"])["converted_int"].mean() * 100.0
    ).reset_index()
    
    sns.barplot(
        data=purpose_visit, x="purpose", y="converted_int", hue="visit_booked",
        ax=axes[1], palette=["#d9534f", "#2e7d32"]
    )
    axes[1].set_title("Conversion Rate by Purpose & Site Visit Booking", fontsize=12, fontweight="bold", pad=12)
    axes[1].set_xlabel("Client Purpose", fontsize=11)
    axes[1].set_ylabel("Conversion Rate (%)", fontsize=11)
    axes[1].legend(title="Visit Booked", loc="upper left")

    plt.suptitle("Figure 5: Lead Conversion Dynamics Across Funnel Dimensions", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    file_path = output_dir / "lead_conversion_by_source_purpose.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def plot_lead_class_imbalance(df_leads: pd.DataFrame, output_dir: Path):
    """Figure 6: Class Imbalance visualization in Leads Dataset."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), dpi=300)
    
    counts = df_leads["converted"].value_counts()
    labels = ["Lost / Not Converted (no)", "Converted Deal (yes)"]
    vals = [counts.get("no", 0), counts.get("yes", 0)]
    pcts = [vals[0] / sum(vals) * 100, vals[1] / sum(vals) * 100]

    # Panel 1: Bar chart with raw count
    sns.barplot(x=labels, y=vals, ax=axes[0], palette=["#7f8c8d", "#27ae60"])
    axes[0].set_title("Lead Class Counts (Raw Scale)", fontsize=12, fontweight="bold", pad=12)
    axes[0].set_ylabel("Lead Count", fontsize=11)
    for i, count in enumerate(vals):
        axes[0].text(i, count + 40, f"{count:,} ({pcts[i]:.1f}%)", ha="center", fontsize=10, fontweight="bold")
    axes[0].set_ylim(0, max(vals) * 1.15)

    # Panel 2: Pie chart with proportion
    axes[1].pie(
        vals, labels=labels, autopct="%1.1f%%", startangle=140,
        colors=["#95a5a6", "#2ecc71"], explode=(0, 0.1),
        textprops={"fontsize": 11, "fontweight": "bold"}
    )
    axes[1].set_title("Lead Conversion Target Proportions", fontsize=12, fontweight="bold", pad=12)

    plt.suptitle("Figure 6: Target Variable Class Imbalance in Lead Scoring", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    file_path = output_dir / "lead_class_imbalance.png"
    plt.savefig(file_path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {file_path}")


def main():
    setup_figure_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Loading cleaned datasets for EDA...")
    df_prop = pd.read_csv(PROPERTIES_CLEANED_PATH)
    df_leads = pd.read_csv(LEADS_CLEANED_PATH)

    print("Generating Figure 1: Price Distribution (Raw vs Log)...")
    plot_price_distribution(df_prop, FIGURES_DIR)

    print("Generating Figure 2: Price per Marla by City and Society...")
    plot_price_per_marla_by_city_society(df_prop, FIGURES_DIR)

    print("Generating Figure 3: Property Feature Correlation Heatmap...")
    plot_correlation_heatmap(df_prop, FIGURES_DIR)

    print("Generating Figure 4: Effect of Bedrooms, Age, and Corner Plots...")
    plot_effect_bedrooms_age_corner(df_prop, FIGURES_DIR)

    print("Generating Figure 5: Lead Conversion by Source & Purpose...")
    plot_lead_conversion_by_source_purpose(df_leads, FIGURES_DIR)

    print("Generating Figure 6: Lead Class Imbalance...")
    plot_lead_class_imbalance(df_leads, FIGURES_DIR)

    print("All 6 EDA figures successfully generated and saved!")


if __name__ == "__main__":
    main()
