"""Data Generator for Week 8 Capstone Project.
Generates realistic, messy Pakistani real estate and CRM lead datasets:
- Dataset A: Property Listings (Regression) >= 5,000 rows.
- Dataset B: Real Estate Leads (Classification) >= 3,000 rows.
Injects real-world Pakistani real estate quirks: 'crore'/'lac' prices, marla/kanal/sqft,
inconsistent society spellings, missing values, duplicates, and outliers.
"""
from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.config import (
    KANAL_TO_MARLA,
    MARLA_TO_SQFT,
    PROPERTIES_RAW_PATH,
    LEADS_RAW_PATH,
    RANDOM_STATE,
    RAW_DATA_DIR,
)

# Seed all random engines
random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


# Pakistani Real Estate Market Configuration
CITIES_SOCIETIES = {
    "Lahore": [
        ("DHA Phase 5", "DHA Ph 5", "DHA Phase-5", "DHA Phase 5 Lahore"),
        ("DHA Phase 6", "DHA Ph 6", "DHA Phase-6"),
        ("DHA Phase 7", "DHA Ph 7"),
        ("DHA Phase 8", "DHA Ph 8"),
        ("Gulberg III", "Gulberg 3", "Gulberg-3", "Gulberg"),
        ("Model Town", "Model Town Lahore", "Model Town Ext"),
        ("Johar Town", "Johar Town Phase 1", "Johar Town Ph 2", "Johar Twn"),
        ("Bahria Town", "Bahria Town Lahore", "Bahria Twn"),
        ("Faisal Town", "Faisal Town Lahore"),
        ("Cantt", "Lahore Cantt", "Cantt Area"),
        ("Township", "Township Lahore"),
        ("College Road", "College Rd"),
        ("Madina Colony", "Madina Colony Lahore"),
    ],
    "Islamabad": [
        ("F-6", "Sector F-6", "F-6/1", "F-6/2"),
        ("F-7", "Sector F-7", "F-7/2", "F-7/4"),
        ("F-8", "Sector F-8", "F-8/3"),
        ("F-10", "Sector F-10", "F-10 Markaz", "F-10/2"),
        ("F-11", "Sector F-11", "F-11/1", "F-11/2"),
        ("E-11", "Sector E-11", "E-11/2", "E-11/3"),
        ("G-11", "Sector G-11", "G-11/3"),
        ("G-13", "Sector G-13", "G-13/1"),
        ("G-15", "Sector G-15"),
        ("I-10", "Sector I-10", "I-10/4"),
        ("DHA Phase 2", "DHA Islamabad Ph 2", "DHA Defence Ph 2"),
        ("Bahria Town", "Bahria Town Islamabad", "Bahria Twn Isb"),
        ("Ghauri Town", "Ghauri Town Phase 4", "Ghauri Twn"),
    ],
    "Rawalpindi": [
        ("Bahria Town Phase 7", "Bahria Phase 7", "Bahria Ph 7"),
        ("Bahria Town Phase 8", "Bahria Phase 8", "Bahria Ph 8"),
        ("Airport Housing Society", "Airport Society", "Airport Housing"),
        ("Cantt", "Rawalpindi Cantt", "Pindi Cantt"),
        ("Chaklala Scheme 3", "Chaklala", "Chaklala Scheme III"),
    ],
    "Karachi": [
        ("DHA Defence", "DHA Karachi", "DHA Phase 6 Karachi"),
        ("Clifton", "Clifton Block 2", "Clifton Block 5", "Clifton Karachi"),
        ("Gulshan-e-Iqbal", "Gulshan e Iqbal Block 13", "Gulshan Iqbal"),
        ("North Nazimabad", "North Nazimabad Block H"),
        ("Korangi", "Korangi Industrial", "Korangi Sector 31"),
    ]
}

# Base price per marla by canonical society in PKR
BASE_PRICE_PER_MARLA = {
    # Islamabad Elite
    "F-6": 5_500_000,
    "F-7": 5_200_000,
    "F-8": 4_800_000,
    "F-10": 4_200_000,
    "F-11": 3_800_000,
    "E-11": 2_600_000,
    "G-11": 2_400_000,
    "G-13": 2_100_000,
    "G-15": 1_600_000,
    "I-10": 1_500_000,
    "DHA Phase 2": 2_800_000,
    "Bahria Town Islamabad": 2_200_000,
    "Ghauri Town": 1_100_000,
    
    # Lahore Elite & Prime
    "DHA Phase 5": 4_500_000,
    "DHA Phase 6": 4_200_000,
    "DHA Phase 7": 3_200_000,
    "DHA Phase 8": 3_600_000,
    "Gulberg III": 4_800_000,
    "Model Town": 4_400_000,
    "Cantt": 3_900_000,
    "Johar Town": 2_700_000,
    "Bahria Town": 2_300_000,
    "Faisal Town": 2_600_000,
    "Township": 1_600_000,
    "College Road": 1_500_000,
    "Madina Colony": 1_400_000,

    # Rawalpindi
    "Bahria Town Phase 7": 2_400_000,
    "Bahria Town Phase 8": 2_100_000,
    "Airport Housing Society": 1_800_000,
    "Chaklala Scheme 3": 2_800_000,

    # Karachi
    "DHA Defence": 4_600_000,
    "Clifton": 4_900_000,
    "Gulshan-e-Iqbal": 2_200_000,
    "North Nazimabad": 1_700_000,
    "Korangi": 900_000,
}

PROPERTY_TYPES = ["House", "Flat", "Upper Portion", "Lower Portion", "Farm House", "Penthouse"]
PROPERTY_TYPE_WEIGHTS = [0.55, 0.25, 0.08, 0.07, 0.03, 0.02]

AMENITIES_POOL = [
    "Electricity Backup (UPS/Generator)",
    "24/7 Security Staff",
    "Gated Community",
    "CCTV Security",
    "Underground Electricity",
    "Nearby Mosque",
    "Nearby Park",
    "Commercial Market Access",
    "Dedicated Parking",
    "Lawn / Garden",
    "Modern Kitchen Fittings",
    "Servant Quarter",
    "Central Heating/AC"
]

LEAD_SOURCES = ["call", "WhatsApp", "Facebook", "website", "walk-in"]
LEAD_SOURCE_WEIGHTS = [0.38, 0.32, 0.16, 0.10, 0.04]

PURPOSES = ["buy", "rent", "invest"]
PURPOSE_WEIGHTS = [0.60, 0.15, 0.25]

OBJECTIONS = [
    "none",
    "price too high",
    "location too far",
    "looking for installment plan",
    "financing / bank loan unavailable",
    "legal / NOC documentation concerns",
    "property size too small",
]
OBJECTION_WEIGHTS = [0.35, 0.25, 0.15, 0.10, 0.08, 0.04, 0.03]


def format_messy_price(price_pkr: float) -> str:
    """Simulate Pakistani messy price strings (Crore, Lac, numeric, prefixes)."""
    style = random.random()
    if price_pkr >= 10_000_000:
        crores = price_pkr / 10_000_000
        if style < 0.35:
            return f"{crores:.2f} Crore"
        elif style < 0.55:
            return f"{crores:.2f} cr"
        elif style < 0.70:
            return f"PKR {crores:.2f} Crore"
        elif style < 0.85:
            return f"{int(price_pkr):,}"
        else:
            return str(int(price_pkr))
    else:
        lacs = price_pkr / 100_000
        if style < 0.40:
            return f"{lacs:.1f} Lac"
        elif style < 0.60:
            return f"{lacs:.1f} lakh"
        elif style < 0.75:
            return f"Rs {int(price_pkr):,}"
        else:
            return str(int(price_pkr))


def format_messy_area(marla: float) -> Tuple[str, str]:
    """Simulate messy area units (Marla, Kanal, Sq Ft, Sq Yds)."""
    style = random.random()
    if marla >= 20 and marla % 20 == 0 and style < 0.45:
        kanals = marla / 20.0
        return f"{kanals:.1f} Kanal", "kanal"
    elif style < 0.70:
        return f"{marla:.1f} Marla", "marla"
    elif style < 0.88:
        sqft = int(marla * MARLA_TO_SQFT)
        return f"{sqft} sq ft", "sqft"
    else:
        sqyds = int(marla * MARLA_TO_SQFT / 9.0)
        return f"{sqyds} sq yds", "sqyd"


def generate_properties_dataset(n_rows: int = 6000) -> pd.DataFrame:
    """Generate Dataset A: Property Listings with realistic market distributions & messy data."""
    records = []
    start_date = datetime(2023, 1, 1)

    for i in range(n_rows):
        prop_id = f"PROP-{10000 + i}"
        city = random.choice(list(CITIES_SOCIETIES.keys()))
        society_tuple = random.choice(CITIES_SOCIETIES[city])
        canonical_society = society_tuple[0]
        
        # 40% probability of using messy alias
        if random.random() < 0.40 and len(society_tuple) > 1:
            raw_society = random.choice(society_tuple[1:])
        else:
            raw_society = canonical_society

        prop_type = np.random.choice(PROPERTY_TYPES, p=PROPERTY_TYPE_WEIGHTS)
        
        # Plot size in Marlas
        if prop_type in ["House", "Upper Portion", "Lower Portion"]:
            marla_choices = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 40.0]
            marla_p = [0.10, 0.35, 0.15, 0.25, 0.05, 0.08, 0.02]
            marla = float(np.random.choice(marla_choices, p=marla_p))
        elif prop_type == "Flat":
            marla_choices = [2.5, 3.5, 5.0, 6.5, 8.0]
            marla_p = [0.25, 0.40, 0.20, 0.10, 0.05]
            marla = float(np.random.choice(marla_choices, p=marla_p))
        elif prop_type == "Penthouse":
            marla = float(np.random.choice([8.0, 10.0, 15.0, 20.0]))
        else: # Farm House
            marla = float(np.random.choice([40.0, 80.0, 120.0, 160.0]))

        raw_size_str, raw_unit = format_messy_area(marla)

        # Bedrooms & Bathrooms
        if prop_type == "Flat":
            beds = int(np.clip(round(marla / 1.5), 1, 4))
            baths = int(np.clip(beds, 1, 4))
            floors = 1
        elif prop_type in ["Upper Portion", "Lower Portion"]:
            beds = int(np.clip(round(marla / 2.2), 2, 4))
            baths = int(np.clip(beds, 2, 4))
            floors = 1
        elif prop_type == "Farm House":
            beds = random.choice([4, 5, 6, 7])
            baths = beds + random.choice([0, 1])
            floors = random.choice([1, 2])
        else: # House
            if marla <= 5:
                beds = random.choice([3, 4])
                floors = 2
            elif marla <= 10:
                beds = random.choice([4, 5, 6])
                floors = 2
            elif marla <= 20:
                beds = random.choice([5, 6, 7, 8])
                floors = random.choice([2, 3])
            else:
                beds = random.choice([6, 8, 10])
                floors = random.choice([2, 3])
            baths = beds + random.choice([-1, 0, 1])
            baths = max(1, baths)

        # Covered Area in Sqft
        if prop_type == "House":
            covered_sqft = int(marla * MARLA_TO_SQFT * (0.85 * floors) * random.uniform(0.9, 1.1))
        elif prop_type in ["Upper Portion", "Lower Portion"]:
            covered_sqft = int(marla * MARLA_TO_SQFT * 0.85 * random.uniform(0.9, 1.05))
        elif prop_type == "Flat":
            covered_sqft = int(marla * MARLA_TO_SQFT * random.uniform(0.85, 1.05))
        else:
            covered_sqft = int(marla * MARLA_TO_SQFT * 0.45 * random.uniform(0.85, 1.15))

        age_years = max(0, int(np.random.exponential(scale=5.0)))
        if age_years > 35:
            age_years = 35

        is_corner = "yes" if random.random() < 0.18 else "no"
        is_park_facing = "yes" if random.random() < 0.22 else "no"

        # Amenities
        k_amenities = random.randint(3, 9)
        amenities = random.sample(AMENITIES_POOL, k_amenities)
        amenities_str = "; ".join(amenities)

        # Distances (km)
        dist_main_road = round(random.uniform(0.1, 4.5), 2)
        dist_school = round(random.uniform(0.2, 5.0), 2)
        dist_hospital = round(random.uniform(0.5, 8.0), 2)

        # Base market price calculation
        base_unit_rate = BASE_PRICE_PER_MARLA.get(canonical_society, 2_200_000)
        
        # Property type multiplier
        type_mult = {
            "House": 1.0,
            "Flat": 0.82,
            "Upper Portion": 0.65,
            "Lower Portion": 0.72,
            "Farm House": 0.85,
            "Penthouse": 1.25,
        }.get(prop_type, 1.0)

        # Depreciation for age (2% per year up to 30%)
        age_depreciation = max(0.70, 1.0 - (age_years * 0.015))
        
        # Premiums
        corner_premium = 1.08 if is_corner == "yes" else 1.0
        park_premium = 1.07 if is_park_facing == "yes" else 1.0
        amenity_premium = 1.0 + (len(amenities) * 0.012)
        accessibility_mult = max(0.90, 1.05 - (dist_main_road * 0.02))

        # Intrinsic fair price
        fair_price = (
            marla * base_unit_rate * type_mult * age_depreciation * 
            corner_premium * park_premium * amenity_premium * accessibility_mult
        )
        # Market stochastic variation (+/- 8%)
        market_price = fair_price * random.gauss(1.0, 0.06)

        # Formatting messy price
        raw_price_str = format_messy_price(market_price)

        # Listing date
        date_offset = random.randint(0, 700)
        listing_date = (start_date + timedelta(days=date_offset)).strftime("%Y-%m-%d")

        # Inject realistic noise & missing values
        rec = {
            "property_id": prop_id,
            "city": city,
            "area_society": raw_society,
            "property_type": prop_type,
            "plot_size": raw_size_str,
            "covered_area": covered_sqft if random.random() > 0.03 else None,
            "bedrooms": beds if random.random() > 0.04 else None,
            "bathrooms": baths if random.random() > 0.04 else None,
            "age_years": age_years if random.random() > 0.05 else None,
            "floors": floors,
            "is_corner": is_corner if random.random() > 0.02 else None,
            "is_park_facing": is_park_facing,
            "amenities": amenities_str if random.random() > 0.03 else None,
            "dist_main_road_km": dist_main_road,
            "dist_school_km": dist_school if random.random() > 0.05 else None,
            "dist_hospital_km": dist_hospital,
            "listing_date": listing_date,
            "price": raw_price_str,
        }
        records.append(rec)

    # Inject ~5% duplicate listings (common multi-listing portal phenomenon)
    n_dupes = int(n_rows * 0.05)
    for _ in range(n_dupes):
        dupe_src = random.choice(records)
        dupe_copy = dupe_src.copy()
        # Same property listed with slightly different ID and listing date
        dupe_copy["property_id"] = f"PROP-DUP-{random.randint(1000, 9999)}"
        records.append(dupe_copy)

    # Inject 1.5% outliers (fake listings, typos)
    n_outliers = int(n_rows * 0.015)
    for _ in range(n_outliers):
        outlier_rec = random.choice(records)
        outlier_type = random.choice(["typo_low", "typo_high", "bed_outlier"])
        if outlier_type == "typo_low":
            outlier_rec["price"] = "15000"  # 15k PKR typo for house
        elif outlier_type == "typo_high":
            outlier_rec["price"] = "950 Crore"  # 950 Crore fake listing
        elif outlier_type == "bed_outlier":
            outlier_rec["bedrooms"] = 48  # 48 bedrooms typo

    df = pd.DataFrame(records)
    # Shuffle dataframe
    df = df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
    return df


def generate_leads_dataset(n_rows: int = 3500) -> pd.DataFrame:
    """Generate Dataset B: Real Estate Leads (Classification) based on Week 7 CRM logs."""
    records = []
    start_date = datetime(2024, 1, 1)

    for i in range(n_rows):
        lead_id = f"LEAD-{20000 + i}"
        lead_source = np.random.choice(LEAD_SOURCES, p=LEAD_SOURCE_WEIGHTS)
        preferred_city = random.choice(list(CITIES_SOCIETIES.keys()))
        society_tuple = random.choice(CITIES_SOCIETIES[preferred_city])
        canonical_society = society_tuple[0]
        preferred_society = canonical_society if random.random() > 0.35 else random.choice(society_tuple)

        purpose = np.random.choice(PURPOSES, p=PURPOSE_WEIGHTS)

        # Stated budget based on preferred society
        base_rate = BASE_PRICE_PER_MARLA.get(canonical_society, 2_200_000)
        expected_size = random.choice([5.0, 10.0, 20.0])
        target_property_val = base_rate * expected_size
        
        # Budget variance (some realistic, some under-budget)
        budget_ratio = random.gauss(0.95, 0.25)
        raw_budget_val = max(1_000_000, target_property_val * budget_ratio)
        budget_str = format_messy_price(raw_budget_val)

        # Lead engagement features
        number_of_calls = int(np.random.choice([1, 2, 3, 4, 5, 6, 7], p=[0.35, 0.25, 0.18, 0.11, 0.06, 0.03, 0.02]))
        call_duration_avg_sec = int(np.random.gamma(shape=3.0, scale=45.0))  # avg ~135 sec
        
        # Response time in minutes (speed to call back)
        response_time_min = int(np.random.exponential(scale=40.0) + 2)

        days_since_first_contact = random.randint(1, 90)

        objection = np.random.choice(OBJECTIONS, p=OBJECTION_WEIGHTS)

        # Visit booked logic
        # High calls, fast response, low objection -> higher visit rate
        visit_prob = 0.08
        if number_of_calls >= 3:
            visit_prob += 0.25
        if call_duration_avg_sec > 180:
            visit_prob += 0.15
        if response_time_min < 15:
            visit_prob += 0.12
        if objection == "none":
            visit_prob += 0.15
        elif objection in ["price too high", "financing / bank loan unavailable"]:
            visit_prob -= 0.10
        visit_prob = np.clip(visit_prob, 0.02, 0.85)
        visit_booked = "yes" if random.random() < visit_prob else "no"

        # Conversion Probability Model (Realistic real estate funnel ~15% conversion)
        logit = -2.8  # baseline low conversion
        if visit_booked == "yes":
            logit += 1.85
        logit += (number_of_calls - 2) * 0.35
        logit += (min(call_duration_avg_sec, 400) / 100.0) * 0.40
        if response_time_min < 20:
            logit += 0.65
        elif response_time_min > 120:
            logit -= 0.50
        
        if budget_ratio >= 0.85:
            logit += 0.50
        else:
            logit -= 0.80

        if objection == "none":
            logit += 0.70
        elif objection in ["price too high", "location too far"]:
            logit -= 0.60
        elif objection == "financing / bank loan unavailable":
            logit -= 1.10

        if lead_source in ["walk-in", "WhatsApp"]:
            logit += 0.45
        elif lead_source == "Facebook":
            logit -= 0.35

        conv_prob = 1.0 / (1.0 + math.exp(-logit))
        conv_prob = np.clip(conv_prob, 0.01, 0.92)
        converted = "yes" if random.random() < conv_prob else "no"

        rec = {
            "lead_id": lead_id,
            "lead_source": lead_source,
            "budget": budget_str,
            "preferred_city": preferred_city,
            "preferred_society": preferred_society,
            "purpose": purpose,
            "number_of_calls": number_of_calls,
            "call_duration_avg_sec": call_duration_avg_sec,
            "response_time_min": response_time_min if random.random() > 0.04 else None,
            "visit_booked": visit_booked,
            "days_since_first_contact": days_since_first_contact,
            "objection_raised": objection if random.random() > 0.03 else None,
            "converted": converted,
        }
        records.append(rec)

    # Add ~4% duplicate lead entries (e.g. repeated online form submissions)
    n_dupes = int(n_rows * 0.04)
    for _ in range(n_dupes):
        dupe_src = random.choice(records)
        dupe_copy = dupe_src.copy()
        dupe_copy["lead_id"] = f"LEAD-DUP-{random.randint(1000, 9999)}"
        records.append(dupe_copy)

    df = pd.DataFrame(records)
    df = df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
    return df


def main():
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating Dataset A: Property Listings (Regression)...")
    prop_df = generate_properties_dataset(n_rows=6000)
    prop_df.to_csv(PROPERTIES_RAW_PATH, index=False)
    print(f"Saved {len(prop_df)} raw property listings to {PROPERTIES_RAW_PATH}")

    print("Generating Dataset B: Real Estate Leads (Classification)...")
    leads_df = generate_leads_dataset(n_rows=3500)
    leads_df.to_csv(LEADS_RAW_PATH, index=False)
    print(f"Saved {len(leads_df)} raw lead records to {LEADS_RAW_PATH}")


if __name__ == "__main__":
    main()
