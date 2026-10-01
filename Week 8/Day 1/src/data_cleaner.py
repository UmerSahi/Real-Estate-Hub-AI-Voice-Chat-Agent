"""Data Cleaning Module for Week 8 Capstone Project.
Handles:
1. Missing value imputation with documented domain justifications
2. Duplicate listings & lead deduplication
3. Price normalisation ("crore", "lac", prefixes -> numeric PKR)
4. Area normalisation (marla, kanal, sq ft, sq yds -> numeric marla & sq ft)
5. Outlier detection using IQR and Z-score on log-price
6. Inconsistent location name canonicalization
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import (
    KANAL_TO_MARLA,
    MARLA_TO_SQFT,
    SQYD_TO_SQFT,
    PROPERTIES_CLEANED_PATH,
    PROPERTIES_RAW_PATH,
    LEADS_CLEANED_PATH,
    LEADS_RAW_PATH,
    PROCESSED_DATA_DIR,
)

# Canonical Location Normalization Dictionary
LOCATION_MAPPING = {
    # Lahore
    r"(?i)dha\s*(?:phase|ph)[-\s]*5.*": "DHA Phase 5",
    r"(?i)dha\s*(?:phase|ph)[-\s]*6.*": "DHA Phase 6",
    r"(?i)dha\s*(?:phase|ph)[-\s]*7.*": "DHA Phase 7",
    r"(?i)dha\s*(?:phase|ph)[-\s]*8.*": "DHA Phase 8",
    r"(?i)gulberg.*": "Gulberg III",
    r"(?i)model\s*town.*": "Model Town",
    r"(?i)johar\s*(?:town|twn).*": "Johar Town",
    r"(?i)faisal\s*town.*": "Faisal Town",
    r"(?i)township.*": "Township",
    r"(?i)college\s*(?:road|rd).*": "College Road",
    r"(?i)madina\s*colony.*": "Madina Colony",
    
    # Islamabad
    r"(?i)sector\s*f[-\s]*6.*|f[-\s]*6.*": "F-6",
    r"(?i)sector\s*f[-\s]*7.*|f[-\s]*7.*": "F-7",
    r"(?i)sector\s*f[-\s]*8.*|f[-\s]*8.*": "F-8",
    r"(?i)sector\s*f[-\s]*10.*|f[-\s]*10.*": "F-10",
    r"(?i)sector\s*f[-\s]*11.*|f[-\s]*11.*": "F-11",
    r"(?i)sector\s*e[-\s]*11.*|e[-\s]*11.*": "E-11",
    r"(?i)sector\s*g[-\s]*11.*|g[-\s]*11.*": "G-11",
    r"(?i)sector\s*g[-\s]*13.*|g[-\s]*13.*": "G-13",
    r"(?i)sector\s*g[-\s]*15.*|g[-\s]*15.*": "G-15",
    r"(?i)sector\s*i[-\s]*10.*|i[-\s]*10.*": "I-10",
    r"(?i)dha\s*(?:defence|islamabad)?\s*(?:phase|ph)[-\s]*2.*": "DHA Phase 2",
    r"(?i)ghauri\s*(?:town|twn).*": "Ghauri Town",

    # Rawalpindi
    r"(?i)bahria\s*(?:town|twn)?\s*(?:phase|ph)[-\s]*7.*": "Bahria Town Phase 7",
    r"(?i)bahria\s*(?:town|twn)?\s*(?:phase|ph)[-\s]*8.*": "Bahria Town Phase 8",
    r"(?i)airport\s*(?:housing|society).*": "Airport Housing Society",
    r"(?i)chaklala.*": "Chaklala Scheme 3",

    # Common Bahria / Cantt
    r"(?i)bahria\s*(?:town|twn)(?:\s*lahore|\s*islamabad)?$": "Bahria Town",
    r"(?i).*(?:cantt|cantonment).*": "Cantt",

    # Karachi
    r"(?i)dha(?:\s*defence|\s*karachi)?.*": "DHA Defence",
    r"(?i)clifton.*": "Clifton",
    r"(?i)gulshan.*": "Gulshan-e-Iqbal",
    r"(?i)north\s*nazimabad.*": "North Nazimabad",
    r"(?i)korangi.*": "Korangi",
}


def normalize_location_name(loc: str) -> str:
    """Standardize messy Pakistani society and sector names into canonical strings."""
    if not isinstance(loc, str) or not loc.strip():
        return "Unknown"
    cleaned = loc.strip()
    for pattern, canonical in LOCATION_MAPPING.items():
        if re.match(pattern, cleaned):
            return canonical
    return cleaned


def parse_pakistani_price(price_val: Any) -> Optional[float]:
    """Parse Pakistani price strings ('1.5 Crore', '85 Lac', commas, abbreviations) to numeric PKR."""
    if pd.isna(price_val):
        return None
    if isinstance(price_val, (int, float)):
        return float(price_val)

    s = str(price_val).lower().replace(",", "").replace("pkr", "").replace("rs", "").strip()
    
    # Check for Crore / cr
    crore_match = re.search(r"([\d\.]+)\s*(?:crore|cr)", s)
    if crore_match:
        try:
            return float(crore_match.group(1)) * 10_000_000.0
        except ValueError:
            pass

    # Check for Lac / Lakh
    lac_match = re.search(r"([\d\.]+)\s*(?:lac|lakh)", s)
    if lac_match:
        try:
            return float(lac_match.group(1)) * 100_000.0
        except ValueError:
            pass

    # Check for Million
    million_match = re.search(r"([\d\.]+)\s*million", s)
    if million_match:
        try:
            return float(million_match.group(1)) * 1_000_000.0
        except ValueError:
            pass

    # Direct numeric
    num_match = re.search(r"([\d\.]+)", s)
    if num_match:
        try:
            return float(num_match.group(1))
        except ValueError:
            return None
    return None


def parse_pakistani_area(area_val: Any) -> Tuple[Optional[float], Optional[float]]:
    """Parse messy plot area strings into both (area_marla, area_sqft).
    Conversions:
    - 1 Kanal = 20 Marlas = 4,500 sq ft (assuming standard 225 sqft/marla baseline)
    - 1 Marla = 225 sq ft
    - 1 Sq Yd = 9 sq ft = 0.04 Marla
    """
    if pd.isna(area_val):
        return None, None
    if isinstance(area_val, (int, float)):
        marla = float(area_val)
        return marla, marla * MARLA_TO_SQFT

    s = str(area_val).lower().replace(",", "").strip()

    # Kanal match
    kanal_match = re.search(r"([\d\.]+)\s*kanal", s)
    if kanal_match:
        try:
            marla = float(kanal_match.group(1)) * KANAL_TO_MARLA
            return marla, marla * MARLA_TO_SQFT
        except ValueError:
            pass

    # Marla match
    marla_match = re.search(r"([\d\.]+)\s*marla", s)
    if marla_match:
        try:
            marla = float(marla_match.group(1))
            return marla, marla * MARLA_TO_SQFT
        except ValueError:
            pass

    # Sq Ft match
    sqft_match = re.search(r"([\d\.]+)\s*sq\s*(?:ft|feet)", s)
    if sqft_match:
        try:
            sqft = float(sqft_match.group(1))
            return sqft / MARLA_TO_SQFT, sqft
        except ValueError:
            pass

    # Sq Yd match
    sqyd_match = re.search(r"([\d\.]+)\s*sq\s*(?:yd|yards)", s)
    if sqyd_match:
        try:
            sqft = float(sqyd_match.group(1)) * SQYD_TO_SQFT
            return sqft / MARLA_TO_SQFT, sqft
        except ValueError:
            pass

    # Generic number fallback (assumed marla)
    num_match = re.search(r"([\d\.]+)", s)
    if num_match:
        try:
            marla = float(num_match.group(1))
            return marla, marla * MARLA_TO_SQFT
        except ValueError:
            return None, None

    return None, None


def clean_properties_data(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean Dataset A (Properties) end-to-end:
    - Standardize prices to numeric PKR
    - Standardize areas to marla & sqft
    - Canonicalize location names
    - Deduplicate business listings
    - Impute missing values with justifiable strategies
    - Detect and remove outliers via IQR and Z-scores
    """
    df = df_raw.copy()
    stats_dict = {"initial_rows": len(df)}

    # 1. Price Normalization
    df["price_pkr"] = df["price"].apply(parse_pakistani_price)
    
    # 2. Area Normalization
    area_parsed = df["plot_size"].apply(parse_pakistani_area)
    df["area_marla"] = [p[0] for p in area_parsed]
    df["area_sqft"] = [p[1] for p in area_parsed]

    # 3. Canonicalize Location Names
    df["area_society"] = df["area_society"].apply(normalize_location_name)

    # 4. Remove Duplicates
    # In Pakistani property portals, multiple agents post the same physical unit with different IDs
    dupe_cols = ["city", "area_society", "property_type", "area_marla", "bedrooms", "price_pkr"]
    initial_dupes = df.duplicated(subset=dupe_cols).sum()
    df = df.drop_duplicates(subset=dupe_cols).reset_index(drop=True)
    stats_dict["duplicates_removed"] = int(initial_dupes)

    # 5. Missing Value Imputation
    # Justification 1: Bedrooms and Bathrooms depend directly on Property Type and Plot Size (Marla)
    df["bedrooms"] = df.groupby(["property_type"])["bedrooms"].transform(
        lambda s: s.fillna(s.median() if not pd.isna(s.median()) else 3)
    )
    df["bathrooms"] = df.groupby(["property_type"])["bathrooms"].transform(
        lambda s: s.fillna(s.median() if not pd.isna(s.median()) else 3)
    )

    # Justification 2: Covered area is strongly bound to plot area in sqft
    # If missing, estimate from typical covered area ratio (0.85 of plot sqft for houses)
    mask_cov = df["covered_area"].isna()
    df.loc[mask_cov, "covered_area"] = df.loc[mask_cov, "area_sqft"] * 0.85

    # Justification 3: Age is right-skewed; impute missing with median age
    median_age = df["age_years"].median()
    df["age_years"] = df["age_years"].fillna(median_age)

    # Justification 4: School distance depends on locality; group by society or city
    df["dist_school_km"] = df.groupby("city")["dist_school_km"].transform(
        lambda s: s.fillna(s.median() if not pd.isna(s.median()) else 2.0)
    )

    # Justification 5: Binary features (is_corner, is_park_facing) - mode is 'no'
    df["is_corner"] = df["is_corner"].fillna("no").str.lower()
    df["is_park_facing"] = df["is_park_facing"].fillna("no").str.lower()

    # Justification 6: Amenities missing text -> 'Standard Utilities'
    df["amenities"] = df["amenities"].fillna("Standard Utilities")

    # 6. Outlier Detection & Removal (IQR & Z-score)
    # Price per marla is the fundamental real estate metric in Pakistan
    valid_mask = (df["price_pkr"] > 0) & (df["area_marla"] > 0)
    df = df[valid_mask].copy()
    df["temp_price_per_marla"] = df["price_pkr"] / df["area_marla"]

    # Method A: Log-Price Z-Score filter (|z| < 3.0) to remove extreme typographical anomalies
    log_price = np.log(df["price_pkr"])
    z_scores = np.abs((log_price - log_price.mean()) / (log_price.std() + 1e-9))
    non_z_outliers = z_scores < 3.0

    # Method B: IQR Bounds on price per marla
    q1 = df["temp_price_per_marla"].quantile(0.01)
    q3 = df["temp_price_per_marla"].quantile(0.99)
    iqr = q3 - q1
    iqr_mask = (df["temp_price_per_marla"] >= (q1 - 1.5 * iqr)) & (df["temp_price_per_marla"] <= (q3 + 1.5 * iqr))

    # Domain Business Bounds:
    # Minimum valid sale price: 500,000 PKR; Max realistic standard residential price: 50 Crore (500M PKR)
    # Realistic bedrooms: 1 to 12
    domain_mask = (
        (df["price_pkr"] >= 500_000) & 
        (df["price_pkr"] <= 500_000_000) &
        (df["bedrooms"] >= 1) & 
        (df["bedrooms"] <= 12) &
        (df["area_marla"] >= 1.5) &
        (df["area_marla"] <= 160.0)
    )

    final_clean_mask = non_z_outliers & iqr_mask & domain_mask
    stats_dict["outliers_removed"] = int((~final_clean_mask).sum())

    df_cleaned = df[final_clean_mask].drop(columns=["temp_price_per_marla"]).reset_index(drop=True)
    stats_dict["final_rows"] = len(df_cleaned)

    return df_cleaned, stats_dict


def clean_leads_data(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean Dataset B (Leads) end-to-end:
    - Standardize budget to numeric PKR
    - Canonicalize preferred society names
    - Deduplicate leads
    - Impute missing values with justifiable strategies
    """
    df = df_raw.copy()
    stats_dict = {"initial_rows": len(df)}

    # 1. Budget Normalization
    df["budget_pkr"] = df["budget"].apply(parse_pakistani_price)
    # If budget missing or invalid, impute by median budget for the preferred city
    median_budget = df["budget_pkr"].median()
    df["budget_pkr"] = df.groupby("preferred_city")["budget_pkr"].transform(
        lambda s: s.fillna(s.median() if not pd.isna(s.median()) else median_budget)
    )

    # 2. Canonicalize Preferred Society
    df["preferred_society"] = df["preferred_society"].apply(normalize_location_name)

    # 3. Deduplicate Leads
    # Same client inquiring through multiple channels or resubmitting forms
    lead_dupe_cols = ["lead_source", "preferred_city", "preferred_society", "budget_pkr", "purpose", "number_of_calls"]
    initial_dupes = df.duplicated(subset=lead_dupe_cols).sum()
    df = df.drop_duplicates(subset=lead_dupe_cols).reset_index(drop=True)
    stats_dict["duplicates_removed"] = int(initial_dupes)

    # 4. Impute Missing Values
    # Response time is missing for some async leads; impute by median response time of that lead source
    df["response_time_min"] = df.groupby("lead_source")["response_time_min"].transform(
        lambda s: s.fillna(s.median() if not pd.isna(s.median()) else 30.0)
    )

    # Objection raised missing -> default to 'none'
    df["objection_raised"] = df["objection_raised"].fillna("none")

    # Target formatting: ensure binary 'yes'/'no'
    df["converted"] = df["converted"].str.lower().map({"yes": "yes", "no": "no"}).fillna("no")

    stats_dict["final_rows"] = len(df)
    stats_dict["conversion_rate"] = float((df["converted"] == "yes").mean() * 100)

    return df, stats_dict


def main():
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Cleaning Properties Dataset (Dataset A)...")
    df_prop_raw = pd.read_csv(PROPERTIES_RAW_PATH)
    df_prop_clean, prop_stats = clean_properties_data(df_prop_raw)
    df_prop_clean.to_csv(PROPERTIES_CLEANED_PATH, index=False)
    print(f"Properties Cleaning Complete: Initial {prop_stats['initial_rows']} -> "
          f"Removed {prop_stats['duplicates_removed']} duplicates, "
          f"Removed {prop_stats['outliers_removed']} outliers -> "
          f"Final {prop_stats['final_rows']} clean rows saved to {PROPERTIES_CLEANED_PATH}")

    print("\nCleaning Leads Dataset (Dataset B)...")
    df_leads_raw = pd.read_csv(LEADS_RAW_PATH)
    df_leads_clean, leads_stats = clean_leads_data(df_leads_raw)
    df_leads_clean.to_csv(LEADS_CLEANED_PATH, index=False)
    print(f"Leads Cleaning Complete: Initial {leads_stats['initial_rows']} -> "
          f"Removed {leads_stats['duplicates_removed']} duplicates -> "
          f"Final {leads_stats['final_rows']} clean rows (Conversion Rate: {leads_stats['conversion_rate']:.2f}%) "
          f"saved to {LEADS_CLEANED_PATH}")


if __name__ == "__main__":
    main()
