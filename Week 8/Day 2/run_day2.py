"""Master End-to-End Runner for Week 8 Day 2: Property Valuation Model (Regression).
Executes:
- Task 1: Baseline Models (Mean, Median, Linear Regression, Ridge, Lasso)
- Task 2: Advanced Models (Random Forest, XGBoost, LightGBM, CatBoost)
- Task 3: Sliced Evaluation & Diagnostic Visualizations (Error by City & Price Range, Actual vs Predicted)
- Task 4: Optuna Hyperparameter Tuning & MLflow Experiment Tracking + Model Registry
- Task 5: Quantile Regression Prediction Intervals & Pricing Verdict Engine
- Automated Unit Tests
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminals
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Limit OpenBLAS threads to prevent thread/memory contention on Windows
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

# Add Day 2 root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
import pandas as pd

from src.config import (
    FIGURES_DIR,
    MODEL_BENCHMARK_REPORT_PATH,
    BEST_MODEL_PATH,
    format_price_pkr,
)
from src.data_loader import get_data_splits
from src.baseline_models import train_baseline_models
from src.advanced_models import train_advanced_models
from src.hyperparameter_tuning import run_tuning_and_mlflow_tracking
from src.model_evaluation import (
    slice_error_by_city,
    slice_error_by_price_tier,
    plot_actual_vs_predicted,
    plot_error_breakdowns,
    generate_benchmark_report,
)
from src.valuation_service import (
    train_quantile_regression_models,
    PropertyValuationService,
)


def print_banner(title: str):
    width = 75
    print("\n" + "=" * width)
    print(f" {title.upper()} ".center(width, "="))
    print("=" * width)


def main():
    start_total = time.time()
    print_banner("Week 8 — Day 2: Property Valuation Model (Regression)")
    print("Scenario: 'Is plot ki sahi qeemat kya honi chahiye?'")
    print("Building production machine learning valuation platform...\n")

    # -------------------------------------------------------------
    # Step 1: Data Preparation & Leakage-Free Splitting
    # -------------------------------------------------------------
    print_banner("Step 1: Data Loading & Preprocessing")
    splits = get_data_splits()
    print(f"[OK] Training Set:   {splits['X_train_trans'].shape[0]} samples ({splits['X_train_trans'].shape[1]} features)")
    print(f"[OK] Validation Set: {splits['X_val_trans'].shape[0]} samples")
    print(f"[OK] Test Set:       {splits['X_test_trans'].shape[0]} samples")

    # -------------------------------------------------------------
    # Step 2: Baseline Models (Task 1)
    # -------------------------------------------------------------
    print_banner("Step 2: Task 1 — Baseline Regression Models")
    base_out = train_baseline_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )
    for model_name, res in base_out["results"].items():
        print(f"  • {model_name:20s} | MAE: {res['mae_lac']:6.2f} Lac | RMSE: {res['rmse_crore']:5.2f} Cr | R²: {res['r2']:6.4f} | MAPE: {res['mape_pct']:5.2f}%")

    # -------------------------------------------------------------
    # Step 3: Advanced Ensemble Models (Task 2)
    # -------------------------------------------------------------
    print_banner("Step 3: Task 2 — Advanced Gradient Boosting & Ensemble Models")
    adv_out = train_advanced_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )
    for model_name, res in adv_out["results"].items():
        print(f"  • {model_name:20s} | MAE: {res['mae_lac']:6.2f} Lac | RMSE: {res['rmse_crore']:5.2f} Cr | R²: {res['r2']:6.4f} | MAPE: {res['mape_pct']:5.2f}%")

    # -------------------------------------------------------------
    # Step 4: Optuna Tuning & MLflow Experiment Tracking (Task 4)
    # -------------------------------------------------------------
    print_banner("Step 4: Task 4 — Optuna Hyperparameter Tuning & MLflow Tracking")
    tuning_res = run_tuning_and_mlflow_tracking(splits, n_trials=12)
    champion_name = tuning_res["champion_name"]
    champion_metrics = tuning_res["champion_metrics"]
    print(f"\n[CHAMPION MODEL]: {champion_name}")
    print(f"  • Test MAE:  {champion_metrics['mae_lac']:.2f} Lac PKR")
    print(f"  • Test RMSE: {champion_metrics['rmse_crore']:.2f} Crore PKR")
    print(f"  • Test R²:   {champion_metrics['r2']:.4f}")
    print(f"  • Test MAPE: {champion_metrics['mape_pct']:.2f}%")

    # -------------------------------------------------------------
    # Step 5: Quantile Regression & Confidence Intervals (Task 5)
    # -------------------------------------------------------------
    print_banner("Step 5: Task 5 — Quantile Regression Prediction Intervals")
    train_quantile_regression_models(splits["X_train_trans"], splits["y_train"].values)
    val_service = PropertyValuationService()

    # -------------------------------------------------------------
    # Step 6: Evaluation, Slices & Benchmark Report (Task 3)
    # -------------------------------------------------------------
    print_banner("Step 6: Task 3 — Sliced Diagnostics & Visual Reports")
    y_test = splits["y_test"].values
    y_pred_champ = champion_metrics["predictions"]

    # Slices
    df_city = slice_error_by_city(splits["df_test_raw"], y_test, y_pred_champ)
    df_tier = slice_error_by_price_tier(splits["df_test_raw"], y_test, y_pred_champ)

    # Plots
    plot_actual_vs_predicted(y_test, y_pred_champ, splits["df_test_raw"]["city"], FIGURES_DIR)
    plot_error_breakdowns(df_city, df_tier, FIGURES_DIR)

    # Consolidated Metrics Dictionary
    all_metrics = {}
    for k, v in base_out["results"].items():
        all_metrics[k] = v
    for k, v in adv_out["results"].items():
        all_metrics[k] = v
    all_metrics["Optuna Tuned LightGBM"] = tuning_res["Optuna Tuned LightGBM"]["metrics"]
    all_metrics["Optuna Tuned CatBoost"] = tuning_res["Optuna Tuned CatBoost"]["metrics"]

    generate_benchmark_report(all_metrics, df_city, df_tier, champion_name, MODEL_BENCHMARK_REPORT_PATH)
    print(f"[OK] Actual vs Predicted plots saved: {FIGURES_DIR}")
    print(f"[OK] Comprehensive Benchmark Report:  {MODEL_BENCHMARK_REPORT_PATH}")

    # -------------------------------------------------------------
    # Step 7: Practical Client Valuation Inquiries
    # -------------------------------------------------------------
    print_banner("Step 7: Real-World Valuation & Verdict Demonstration")
    sample_1 = splits["X_test"].iloc[5].to_dict()
    fair_est = champion_metrics["predictions"][5]

    # Test Case A: Overpriced Listing
    res_over = val_service.evaluate_valuation(sample_1, listed_price_pkr=fair_est * 1.25)
    print("Test Case 1 (Overpriced):")
    print(f"  {res_over['client_explanation']}")

    # Test Case B: Underpriced Listing
    res_under = val_service.evaluate_valuation(sample_1, listed_price_pkr=fair_est * 0.80)
    print("\nTest Case 2 (Underpriced):")
    print(f"  {res_under['client_explanation']}")

    # Test Case C: Fair Market Listing
    res_fair = val_service.evaluate_valuation(sample_1, listed_price_pkr=fair_est * 1.01)
    print("\nTest Case 3 (Fair Market Deal):")
    print(f"  {res_fair['client_explanation']}")

    # -------------------------------------------------------------
    # Step 8: Automated Test Suite Execution
    # -------------------------------------------------------------
    print_banner("Step 8: Automated Test Suite Verification")
    from tests.test_day2_valuation import TestWeek8Day2Valuation
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWeek8Day2Valuation)
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    if test_result.wasSuccessful():
        print(f"\n[OK] All {test_result.testsRun} unit and integration tests PASSED successfully!")
    else:
        print(f"\n[ERROR] Test failures: {len(test_result.failures)}, errors: {len(test_result.errors)}")

    elapsed = time.time() - start_total
    print_banner(f"Week 8 Day 2 Complete — Total Execution Time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
