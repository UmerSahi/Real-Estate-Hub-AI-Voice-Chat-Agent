"""Master End-to-End Runner for Week 8 Day 1.
AI Property Valuation & Lead Scoring Platform for Real Estate.

Executes all Day 1 tasks sequentially:
1. Task 1: Data Collection & Data Dictionary Generation (6,300 Properties, 3,640 Leads)
2. Task 2: Data Cleaning (Crore/Lac parser, Marla/Kanal normalizer, IQR/Z-score outlier filter, Location standardization)
3. Task 3: Exploratory Data Analysis (6 figures generated with one-line business insights)
4. Task 4: Feature Engineering (13 domain features created with justifications)
5. Task 5: Encoding, Scaling & Splitting Pipeline (OHE vs Target Encoding, 70/15/15 stratified split, leakage isolation)
6. Automated Unit Tests (10 test suites validating complete pipeline)
"""
import os
import sys
import time
import unittest
from pathlib import Path

# Limit OpenBLAS threads to prevent Windows thread/memory contention
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import (
    PROPERTIES_RAW_PATH,
    LEADS_RAW_PATH,
    PROPERTIES_CLEANED_PATH,
    LEADS_CLEANED_PATH,
    PROPERTIES_FEATURED_PATH,
    LEADS_FEATURED_PATH,
    FIGURES_DIR,
    PROPERTIES_DOC_PATH,
    LEADS_DOC_PATH,
    EDA_REPORT_PATH,
)
from src import data_generator, data_cleaner, eda_generator, feature_engineering, pipeline


def print_banner(title: str):
    width = 75
    print("\n" + "=" * width)
    print(f" {title.upper()} ".center(width, "="))
    print("=" * width)


def main():
    start_total = time.time()
    print_banner("Week 8 — Day 1: Data Understanding, EDA & Feature Engineering")
    print("Scenario: AI Property Valuation & Lead Scoring Platform for Real Estate")
    print("Initializing reproducible pipeline run...\n")

    # -------------------------------------------------------------
    # Step 1: Data Collection & Documentation (Task 1)
    # -------------------------------------------------------------
    print_banner("Step 1: Task 1 — Data Collection & Documentation")
    data_generator.main()
    print(f"\n[OK] Property listings raw dataset generated: {PROPERTIES_RAW_PATH}")
    print(f"[OK] CRM leads raw dataset generated:       {LEADS_RAW_PATH}")
    print(f"[OK] Property data dictionary:              {PROPERTIES_DOC_PATH}")
    print(f"[OK] Leads data dictionary:                 {LEADS_DOC_PATH}")

    # -------------------------------------------------------------
    # Step 2: Data Cleaning (Task 2)
    # -------------------------------------------------------------
    print_banner("Step 2: Task 2 — Data Cleaning & Normalization")
    data_cleaner.main()
    print(f"\n[OK] Cleaned property dataset saved: {PROPERTIES_CLEANED_PATH}")
    print(f"[OK] Cleaned leads dataset saved:    {LEADS_CLEANED_PATH}")

    # -------------------------------------------------------------
    # Step 3: Exploratory Data Analysis (Task 3)
    # -------------------------------------------------------------
    print_banner("Step 3: Task 3 — Exploratory Data Analysis & Visual Insights")
    eda_generator.main()
    print(f"\n[OK] All 6 high-resolution figures saved in: {FIGURES_DIR}")
    print(f"[OK] Comprehensive EDA report with insights: {EDA_REPORT_PATH}")

    # -------------------------------------------------------------
    # Step 4: Feature Engineering (Task 4)
    # -------------------------------------------------------------
    print_banner("Step 4: Task 4 — Domain Feature Engineering")
    feature_engineering.main()
    print(f"\n[OK] Featured property dataset saved: {PROPERTIES_FEATURED_PATH}")
    print(f"[OK] Featured leads dataset saved:    {LEADS_FEATURED_PATH}")

    # -------------------------------------------------------------
    # Step 5: Encoding, Scaling & Splitting Pipeline (Task 5)
    # -------------------------------------------------------------
    print_banner("Step 5: Task 5 — Scikit-learn Pipeline & Leakage Audit")
    pipeline.main()

    # -------------------------------------------------------------
    # Step 6: Test Suite Execution (In-Process)
    # -------------------------------------------------------------
    print_banner("Step 6: Automated Test Suite Verification")
    from tests.test_day1_pipeline import TestWeek8Day1Pipeline
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWeek8Day1Pipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print(f"\n[OK] All {result.testsRun} unit and integration tests PASSED successfully!")
    else:
        print(f"\n[ERROR] Test failures: {len(result.failures)}, errors: {len(result.errors)}")

    elapsed = time.time() - start_total
    print_banner(f"Week 8 Day 1 Complete — Elapsed Time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
