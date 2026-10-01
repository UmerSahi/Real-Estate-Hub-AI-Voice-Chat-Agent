"""Configuration Module for Week 8 Day 3: Lead Scoring Model & Explainability.
Defines directory paths, random seeds, business cost matrix, and lead segmentation thresholds.
"""
from __future__ import annotations

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
TESTS_DIR = BASE_DIR / "tests"

# Ensure directories exist
for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR, NOTEBOOKS_DIR, TESTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Data File Paths
LEADS_FEATURED_CSV = DATA_DIR / "leads_featured.csv"
DATA_DICTIONARY_PATH = DATA_DIR / "data_dictionary_leads.md"

# Model Artifact Paths
BEST_MODEL_PATH = MODELS_DIR / "best_lead_scoring_model.joblib"
PREPROCESSOR_PATH = MODELS_DIR / "lead_preprocessor.joblib"
KMEANS_PERSONAS_MODEL_PATH = MODELS_DIR / "kmeans_personas_model.joblib"
PERSONA_SCALER_PATH = MODELS_DIR / "persona_scaler.joblib"
BENCHMARK_REPORT_PATH = REPORTS_DIR / "lead_scoring_benchmark_report.md"

# Reproducibility
RANDOM_STATE = 42

# Business Cost Matrix (in PKR)
# Cost of False Negative: Missing a converting lead (lost commission on standard 2.5 Crore deal)
COST_FALSE_NEGATIVE_PKR = 300_000.0  # 3.0 Lac PKR
# Cost of False Positive: Wasting agent time on a non-converting lead (15-min phone call + telephony overhead)
COST_FALSE_POSITIVE_PKR = 500.0      # 500 PKR

# Lead Segmentation Thresholds
HOT_THRESHOLD = 0.65       # P >= 0.65: Hot Lead (Call within 1 hr)
WARM_THRESHOLD = 0.35      # 0.35 <= P < 0.65: Warm Lead (Call within 24 hrs)
# P < 0.35: Cold Lead (Nurture campaign)

# Decision Threshold Default
DEFAULT_DECISION_THRESHOLD = 0.50

# MLflow SQLite Tracking URI
MLFLOW_DB_PATH = BASE_DIR / "mlflow.db"
MLFLOW_TRACKING_URI = f"sqlite:///{MLFLOW_DB_PATH.as_posix()}"
MLFLOW_EXPERIMENT_NAME = "Week8_Day3_Lead_Scoring"
MLFLOW_REGISTERED_MODEL_NAME = "LeadScoringClassificationModel"


def format_price_pkr(amount: float) -> str:
    """Format PKR numeric amounts into Pakistani Lac and Crore convention."""
    if amount >= 10_000_000:
        return f"{amount / 10_000_000:.2f} crore"
    elif amount >= 100_000:
        return f"{amount / 100_000:.2f} lac"
    return f"{amount:,.0f} PKR"
