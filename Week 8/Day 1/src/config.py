"""Configuration module for Week 8 Capstone Project.
AI Property Valuation & Lead Scoring Platform for Real Estate.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DOCS_DATA_DIR = DATA_DIR / "docs"

EDA_DIR = BASE_DIR / "eda"
FIGURES_DIR = EDA_DIR / "figures"

# File paths
PROPERTIES_RAW_PATH = RAW_DATA_DIR / "properties_raw.csv"
LEADS_RAW_PATH = RAW_DATA_DIR / "leads_raw.csv"

PROPERTIES_CLEANED_PATH = PROCESSED_DATA_DIR / "properties_cleaned.csv"
LEADS_CLEANED_PATH = PROCESSED_DATA_DIR / "leads_cleaned.csv"

PROPERTIES_FEATURED_PATH = PROCESSED_DATA_DIR / "properties_featured.csv"
LEADS_FEATURED_PATH = PROCESSED_DATA_DIR / "leads_featured.csv"

PROPERTIES_DOC_PATH = DOCS_DATA_DIR / "data_dictionary_properties.md"
LEADS_DOC_PATH = DOCS_DATA_DIR / "data_dictionary_leads.md"
EDA_REPORT_PATH = EDA_DIR / "eda_analysis_report.md"

# Random Seed for reproducibility
RANDOM_STATE = 42

# Domain Knowledge: Society Tiers in Pakistan
SOCIETY_TIERS = {
    # Tier 1: Prime Luxury / High Capital Appreciation
    "DHA Defence": "Tier 1",
    "DHA Phase 5": "Tier 1",
    "DHA Phase 6": "Tier 1",
    "DHA Phase 7": "Tier 1",
    "DHA Phase 8": "Tier 1",
    "Gulberg": "Tier 1",
    "Gulberg III": "Tier 1",
    "F-6": "Tier 1",
    "F-7": "Tier 1",
    "F-8": "Tier 1",
    "F-10": "Tier 1",
    "F-11": "Tier 1",
    "Clifton": "Tier 1",
    "Cantt": "Tier 1",
    
    # Tier 2: Established Middle-to-Upper Class / High Liquidity
    "Bahria Town": "Tier 2",
    "Bahria Town Phase 7": "Tier 2",
    "Bahria Town Phase 8": "Tier 2",
    "Model Town": "Tier 2",
    "Johar Town": "Tier 2",
    "Faisal Town": "Tier 2",
    "E-11": "Tier 2",
    "G-11": "Tier 2",
    "G-13": "Tier 2",
    "Airport Housing Society": "Tier 2",
    "Gulshan-e-Iqbal": "Tier 2",
    
    # Tier 3: Budget / Developing Suburbs / Affordable Housing
    "Ghauri Town": "Tier 3",
    "I-10": "Tier 3",
    "G-15": "Tier 3",
    "College Road": "Tier 3",
    "Township": "Tier 3",
    "Madina Colony": "Tier 3",
    "North Nazimabad": "Tier 3",
    "Korangi": "Tier 3",
}

DEFAULT_SOCIETY_TIER = "Tier 2"

# Real Estate Unit Conversions
MARLA_TO_SQFT = 225.0  # Standard Punjab/Islamabad residential marla (approx 225-272 sq ft; standard baseline 225 sqft)
KANAL_TO_MARLA = 20.0
SQYD_TO_SQFT = 9.0
