"""Configuration and constants for Week 8 Day 2: Property Valuation Model (Regression).
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

PROPERTIES_FEATURED_PATH = DATA_DIR / "properties_featured.csv"
MODEL_BENCHMARK_REPORT_PATH = REPORTS_DIR / "model_benchmark_report.md"

# Model Artifact Paths
BEST_MODEL_PATH = MODELS_DIR / "best_valuation_model.joblib"
QUANTILE_LOWER_PATH = MODELS_DIR / "quantile_lower_model.joblib"
QUANTILE_UPPER_PATH = MODELS_DIR / "quantile_upper_model.joblib"
PREPROCESSOR_PATH = MODELS_DIR / "fitted_preprocessor.joblib"

# MLflow Experiment Configuration
MLFLOW_DB_PATH = BASE_DIR / "mlflow.db"
MLFLOW_TRACKING_URI = f"sqlite:///{MLFLOW_DB_PATH.as_posix()}"
MLFLOW_EXPERIMENT_NAME = "Property_Valuation_Regression"
MLFLOW_REGISTERED_MODEL_NAME = "PropertyValuationModel"

# Random Seed
RANDOM_STATE = 42

# Ensure required directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def format_price_pkr(price_pkr: float) -> str:
    """Format numeric PKR into conversational Pakistani Crore / Lac representation."""
    if price_pkr >= 10_000_000:
        crores = price_pkr / 10_000_000.0
        return f"{crores:.2f} crore"
    else:
        lacs = price_pkr / 100_000.0
        return f"{lacs:.1f} lac"
