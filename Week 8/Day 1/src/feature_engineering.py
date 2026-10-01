"""Feature Engineering Module for Week 8 Capstone Project.
Constructs at least 10 domain-specific features across Property Valuation and Lead Scoring:
Properties:
1. price_per_marla (Business Metric & Explanation Benchmark)
2. property_age_bucket (Lifecycle Phase)
3. society_tier (Tier 1 Prime, Tier 2 Mid, Tier 3 Budget)
4. amenity_score (Quantified infrastructure & utility score)
5. accessibility_composite (Harmonic distance to main road, school, hospital)
6. spatial_density_ratio (Covered Area / Plot Sqft)
7. bed_to_bath_ratio (Luxury ensuite layout indicator)
8. society_hist_median_ppm (Leakage-free location valuation baseline)

Leads:
9. lead_engagement_score (Calls × Duration in minutes)
10. response_speed_category (Operational SLA buckets)
11. budget_to_market_ratio (Stated Budget / Society Benchmark Price)
12. lead_velocity (Calls per day since first contact)
13. high_intent_flag (Composite VIP qualifier)
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from src.config import (
    DEFAULT_SOCIETY_TIER,
    SOCIETY_TIERS,
    PROPERTIES_CLEANED_PATH,
    PROPERTIES_FEATURED_PATH,
    LEADS_CLEANED_PATH,
    LEADS_FEATURED_PATH,
)

# Reference benchmark property prices for 10-marla standard units by society (PKR)
# Used to calculate budget-to-market-ratio without leaking training labels
SOCIETY_BENCHMARK_PRICE = {
    "F-6": 55_000_000,
    "F-7": 52_000_000,
    "F-8": 48_000_000,
    "F-10": 42_000_000,
    "F-11": 38_000_000,
    "E-11": 26_000_000,
    "G-11": 24_000_000,
    "G-13": 21_000_000,
    "G-15": 16_000_000,
    "I-10": 15_000_000,
    "DHA Phase 2": 28_000_000,
    "Bahria Town Islamabad": 22_000_000,
    "Ghauri Town": 11_000_000,
    "DHA Phase 5": 45_000_000,
    "DHA Phase 6": 42_000_000,
    "DHA Phase 7": 32_000_000,
    "DHA Phase 8": 36_000_000,
    "Gulberg III": 48_000_000,
    "Model Town": 44_000_000,
    "Cantt": 39_000_000,
    "Johar Town": 27_000_000,
    "Bahria Town": 23_000_000,
    "Faisal Town": 26_000_000,
    "Township": 16_000_000,
    "College Road": 15_000_000,
    "Madina Colony": 14_000_000,
    "Bahria Town Phase 7": 24_000_000,
    "Bahria Town Phase 8": 21_000_000,
    "Airport Housing Society": 18_000_000,
    "Chaklala Scheme 3": 28_000_000,
    "DHA Defence": 46_000_000,
    "Clifton": 49_000_000,
    "Gulshan-e-Iqbal": 22_000_000,
    "North Nazimabad": 17_000_000,
    "Korangi": 9_000_000,
}


def calculate_amenity_score(amenities_str: str) -> int:
    """Parse comma/semicolon-separated amenities string into a quantitative score."""
    if not isinstance(amenities_str, str) or not amenities_str.strip():
        return 2  # baseline standard
    items = [x.strip() for x in amenities_str.replace(";", ",").split(",") if x.strip()]
    return len(items)


def engineer_property_features(df_clean: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Engineer domain-informed features for Property Listings (Dataset A)."""
    df = df_clean.copy()
    justifications = {}

    # Feature 1: price_per_marla
    # NOTE: Used for business valuation and post-prediction intelligence.
    # Must NOT be an input feature in training pipeline predicting price_pkr (Leakage Protection).
    df["price_per_marla"] = df["price_pkr"] / df["area_marla"]
    justifications["price_per_marla"] = (
        "Core Pakistani real estate evaluation metric (Price / Marla). Provides standard unit value "
        "for comparisons across properties of unequal sizes."
    )

    # Feature 2: property_age_bucket
    bins = [-1, 1, 5, 15, 100]
    labels = ["Brand New (<=1y)", "Modern (2-5y)", "Established (6-15y)", "Aging (>15y)"]
    df["property_age_bucket"] = pd.cut(df["age_years"], bins=bins, labels=labels).astype(str)
    justifications["property_age_bucket"] = (
        "Captures non-linear structural depreciation. Newly constructed homes command a steep initial premium, "
        "after which depreciation flattens as land value dominates."
    )

    # Feature 3: society_tier
    df["society_tier"] = df["area_society"].map(SOCIETY_TIERS).fillna(DEFAULT_SOCIETY_TIER)
    justifications["society_tier"] = (
        "Groups high-cardinality housing societies into 3 macro tiers (Tier 1 Prime, Tier 2 Mid, Tier 3 Budget), "
        "capturing systemic differences in security, electricity reliability, and prestige."
    )

    # Feature 4: amenity_score
    df["amenity_score"] = df["amenities"].apply(calculate_amenity_score)
    justifications["amenity_score"] = (
        "Aggregates presence of essential infrastructure (UPS/Generator backup, 24/7 security, gated access, mosque). "
        "In Pakistan, utility backup and security create strong positive price elasticity."
    )

    # Feature 5: accessibility_composite
    # Harmonic-inspired composite distance score: higher means more accessible (closer to amenities)
    df["accessibility_composite"] = 1.0 / (
        1.0 + (0.50 * df["dist_main_road_km"]) + 
        (0.25 * df["dist_school_km"]) + 
        (0.25 * df["dist_hospital_km"])
    )
    justifications["accessibility_composite"] = (
        "Unified spatial index measuring overall community convenience. Penalizes isolated plots far from main roads "
        "and medical/educational infrastructure."
    )

    # Feature 6: spatial_density_ratio
    df["spatial_density_ratio"] = (df["covered_area"] / (df["area_sqft"] + 1e-5)).clip(0.1, 3.5)
    justifications["spatial_density_ratio"] = (
        "Ratio of built covered area to land area. Separates multi-storey commercial-style residential builds "
        "from sprawling open single-storey estates with large lawns."
    )

    # Feature 7: bed_to_bath_ratio
    df["bed_to_bath_ratio"] = (df["bedrooms"] / (df["bathrooms"] + 0.1)).clip(0.3, 3.0)
    justifications["bed_to_bath_ratio"] = (
        "Structural luxury proxy. Modern luxury developments offer 1:1 ensuite attached baths (~1.0 ratio), "
        "whereas dated or economy builds have multiple bedrooms sharing single bathrooms (ratio >= 1.5)."
    )

    # Feature 8: society_hist_median_ppm (Non-leaking reference rate)
    # Computed from predefined historical market tables
    def get_hist_ppm(soc: str) -> float:
        bench_10m = SOCIETY_BENCHMARK_PRICE.get(soc, 25_000_000)
        return float(bench_10m / 10.0)

    df["society_hist_median_ppm"] = df["area_society"].apply(get_hist_ppm)
    justifications["society_hist_median_ppm"] = (
        "Pre-computed historical median benchmark rate per marla for each society, allowing the regression model "
        "to anchor base land value without leaking the target listing price."
    )

    return df, justifications


def engineer_lead_features(df_clean: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Engineer domain-informed features for Leads Scoring (Dataset B)."""
    df = df_clean.copy()
    justifications = {}

    # Feature 9: lead_engagement_score
    df["lead_engagement_score"] = df["number_of_calls"] * (df["call_duration_avg_sec"] / 60.0)
    justifications["lead_engagement_score"] = (
        "Product of total calls and average call duration in minutes. Quantifies total conversational attention "
        "invested by the prospect with the voice agent or sales reps."
    )

    # Feature 10: response_speed_category
    def categorize_response(mins: float) -> str:
        if mins <= 15:
            return "Immediate (<=15m)"
        elif mins <= 60:
            return "Prompt (15m-1h)"
        elif mins <= 240:
            return "Standard (1h-4h)"
        else:
            return "Delayed (>4h)"

    df["response_speed_category"] = df["response_time_min"].apply(categorize_response)
    justifications["response_speed_category"] = (
        "Operational SLA tier for agent response latency. Speed-to-lead is mathematically the highest human-controlled "
        "lever for closing inbound inquiries."
    )

    # Feature 11: budget_to_market_ratio
    def get_market_bench(soc: str) -> float:
        return SOCIETY_BENCHMARK_PRICE.get(soc, 25_000_000)

    benchmark_prices = df["preferred_society"].apply(get_market_bench)
    df["budget_to_market_ratio"] = (df["budget_pkr"] / benchmark_prices).clip(0.1, 5.0)
    justifications["budget_to_market_ratio"] = (
        "Ratio of prospect budget to market benchmark property price in requested society. Immediately detects "
        "unrealistic buyers whose budgets are far below local market reality."
    )

    # Feature 12: lead_velocity
    df["lead_velocity"] = df["number_of_calls"] / (df["days_since_first_contact"] + 1.0)
    justifications["lead_velocity"] = (
        "Interactions per elapsed day. Prospects with high velocity (frequent calls over a short window) are in an "
        "active buying cycle, while stagnant leads have decayed interest."
    )

    # Feature 13: high_intent_flag
    df["high_intent_flag"] = (
        (df["visit_booked"] == "yes") & 
        (df["response_time_min"] <= 60) & 
        (df["number_of_calls"] >= 2)
    ).astype(int)
    justifications["high_intent_flag"] = (
        "Composite VIP flag indicating that a site visit is secured, callback speed was under 1 hour, and the prospect "
        "has completed multiple qualification calls."
    )

    return df, justifications


def main():
    print("Loading cleaned datasets for Feature Engineering...")
    df_prop = pd.read_csv(PROPERTIES_CLEANED_PATH)
    df_leads = pd.read_csv(LEADS_CLEANED_PATH)

    print("Engineering features for Property Listings...")
    df_prop_feat, prop_just = engineer_property_features(df_prop)
    df_prop_feat.to_csv(PROPERTIES_FEATURED_PATH, index=False)
    print(f"Created {len(prop_just)} features for Properties. Saved to {PROPERTIES_FEATURED_PATH}")
    for k, v in prop_just.items():
        print(f"  • {k}: {v}")

    print("\nEngineering features for Leads Scoring...")
    df_leads_feat, leads_just = engineer_lead_features(df_leads)
    df_leads_feat.to_csv(LEADS_FEATURED_PATH, index=False)
    print(f"Created {len(leads_just)} features for Leads. Saved to {LEADS_FEATURED_PATH}")
    for k, v in leads_just.items():
        print(f"  • {k}: {v}")


if __name__ == "__main__":
    main()
