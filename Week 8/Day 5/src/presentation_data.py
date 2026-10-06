"""Centralized Presentation Data, Metrics, and Strategic Model Artifacts.

Single source of truth for Week 8 Capstone Stakeholder Presentation
and Comprehensive Project Documentation.
"""
from __future__ import annotations

from typing import Any, Dict, List

# Core Executive KPIs
EXECUTIVE_METRICS = {
    "total_listings_trained": 10480,
    "total_leads_analyzed": 3496,
    "champion_valuation_model": "Optuna Tuned CatBoost Regressor",
    "valuation_r2": 0.9860,
    "valuation_mae_pkr": 1783290,
    "valuation_mae_lac": 17.83,
    "valuation_mape": 0.0729,  # 7.29%
    "baseline_mae_lac": 156.54,
    "valuation_error_reduction_pct": 88.6,
    "champion_lead_model": "LightGBM Classifier + SMOTE",
    "lead_roc_auc": 0.8201,
    "lead_pr_auc": 0.6596,
    "lead_f1_score": 0.6136,
    "precision_top_20": 0.7143,  # 71.43%
    "baseline_conversion_rate": 0.2857,  # 28.57%
    "precision_top_20_lift": 2.50,  # 2.50x lift
    "recall_top_20": 0.5000,  # 50.0% capture of all conversions
    "optimal_cost_threshold": 0.05,
    "cost_fn_pkr": 300000,
    "cost_fp_pkr": 500,
    "annual_cost_savings_pkr": 19200000,  # 1.92 Crore PKR saved
    "sales_closer_productivity_gain_pct": 150,
    "voice_agent_sla_mins": 15,
}

# Valuation Model Benchmark across 6 Candidates
VALUATION_BENCHMARK_TABLE: List[Dict[str, Any]] = [
    {
        "family": "Tuned Ensemble",
        "algorithm": "Optuna Tuned CatBoost",
        "mae_lac": 17.83,
        "rmse_cr": 0.41,
        "r2": 0.9860,
        "mape": "7.29%",
        "train_time": "7.04s",
        "status": "Champion",
    },
    {
        "family": "Gradient Boosting",
        "algorithm": "CatBoost (Default)",
        "mae_lac": 17.61,
        "rmse_cr": 0.39,
        "r2": 0.9872,
        "mape": "7.42%",
        "train_time": "0.74s",
        "status": "Candidate",
    },
    {
        "family": "Gradient Boosting",
        "algorithm": "XGBoost",
        "mae_lac": 18.29,
        "rmse_cr": 0.58,
        "r2": 0.9724,
        "mape": "6.68%",
        "train_time": "0.36s",
        "status": "Candidate",
    },
    {
        "family": "Gradient Boosting",
        "algorithm": "LightGBM",
        "mae_lac": 19.49,
        "rmse_cr": 0.57,
        "r2": 0.9727,
        "mape": "7.38%",
        "train_time": "0.20s",
        "status": "Candidate",
    },
    {
        "family": "Ensemble (Bagging)",
        "algorithm": "Random Forest",
        "mae_lac": 21.47,
        "rmse_cr": 0.55,
        "r2": 0.9749,
        "mape": "8.30%",
        "train_time": "0.49s",
        "status": "Candidate",
    },
    {
        "family": "Linear Regularized",
        "algorithm": "Ridge Regression",
        "mae_lac": 67.86,
        "rmse_cr": 1.31,
        "r2": 0.8577,
        "mape": "56.80%",
        "train_time": "0.01s",
        "status": "Baseline Linear",
    },
    {
        "family": "Heuristic Baseline",
        "algorithm": "Median Dummy",
        "mae_lac": 156.54,
        "rmse_cr": 3.59,
        "r2": -0.0649,
        "mape": "80.04%",
        "train_time": "0.00s",
        "status": "Naive Baseline",
    },
]

# Geographic Sliced Error Breakdown
GEOGRAPHIC_SLICES: List[Dict[str, Any]] = [
    {
        "city": "Islamabad",
        "listings": 224,
        "median_price_cr": 1.39,
        "mae_lac": 24.38,
        "mape": "7.62%",
        "dynamics": "High-value sectors (F-6, F-7, E-7) introduce higher absolute variance, but percentage error remains tightly bounded.",
    },
    {
        "city": "Karachi",
        "listings": 208,
        "median_price_cr": 1.45,
        "mae_lac": 15.52,
        "mape": "7.81%",
        "dynamics": "Clifton & DHA beachfront premiums captured accurately through society tier encoding.",
    },
    {
        "city": "Lahore",
        "listings": 208,
        "median_price_cr": 1.54,
        "mae_lac": 16.13,
        "mape": "6.90%",
        "dynamics": "Robust transaction volume in DHA Lahore & Bahria Town yields superior 6.90% MAPE.",
    },
    {
        "city": "Rawalpindi",
        "listings": 227,
        "median_price_cr": 1.39,
        "mae_lac": 15.06,
        "mape": "6.86%",
        "dynamics": "Lowest percentage error (6.86%) driven by high density of master-planned Bahria/DHA phases.",
    },
]

# Price Tier Slices Breakdown
PRICE_TIER_SLICES: List[Dict[str, Any]] = [
    {
        "tier": "Budget (< 1.5 Crore)",
        "count": 451,
        "mae_lac": 6.62,
        "mape": "7.67%",
        "governance": "Fully automated instant quotation.",
    },
    {
        "tier": "Mid-Market (1.5 - 3.5 Crore)",
        "count": 268,
        "mae_lac": 14.68,
        "mape": "6.69%",
        "governance": "Optimal prediction sweet-spot; instant quote + confidence range.",
    },
    {
        "tier": "Premium (3.5 - 7.0 Crore)",
        "count": 99,
        "mae_lac": 33.12,
        "mape": "7.00%",
        "governance": "Quantile upper/lower interval displayed prominently.",
    },
    {
        "tier": "Luxury (> 7.0 Crore)",
        "count": 49,
        "mae_lac": 107.36,
        "mape": "7.74%",
        "governance": "Mandatory Human Appraisal Gate triggered (flags custom fittings / architectural uniqueness).",
    },
]

# Lead Scoring Classification Benchmark
LEAD_BENCHMARK_TABLE: List[Dict[str, Any]] = [
    {
        "algorithm": "XGBoost Classifier",
        "roc_auc": 0.8201,
        "pr_auc": 0.6596,
        "f1": 0.5906,
        "precision": "72.12%",
        "recall": "50.00%",
        "accuracy": "80.19%",
        "status": "Candidate",
    },
    {
        "algorithm": "LightGBM + SMOTE",
        "roc_auc": 0.8141,
        "pr_auc": 0.6451,
        "f1": 0.6136,
        "precision": "71.05%",
        "recall": "54.00%",
        "accuracy": "80.57%",
        "status": "Champion (Balanced)",
    },
    {
        "algorithm": "CatBoost Classifier",
        "roc_auc": 0.8155,
        "pr_auc": 0.6520,
        "f1": 0.5854,
        "precision": "75.00%",
        "recall": "48.00%",
        "accuracy": "80.57%",
        "status": "Candidate",
    },
    {
        "algorithm": "Logistic Regression",
        "roc_auc": 0.8185,
        "pr_auc": 0.6539,
        "f1": 0.5748,
        "precision": "70.19%",
        "recall": "48.67%",
        "accuracy": "79.43%",
        "status": "Linear Baseline",
    },
    {
        "algorithm": "Random Forest",
        "roc_auc": 0.8124,
        "pr_auc": 0.6469,
        "f1": 0.5583,
        "precision": "74.44%",
        "recall": "44.67%",
        "accuracy": "79.81%",
        "status": "Candidate",
    },
]

# Customer Personas (K-Means k=4)
CUSTOMER_PERSONAS: List[Dict[str, Any]] = [
    {
        "name": "Overseas Capital Investor",
        "cluster_id": 0,
        "conversion_rate": "27.1%",
        "median_budget": "5.96 Crore",
        "traits": "High liquidity, commercial/file inquiry, fast response turnaround, overseas WhatsApp.",
        "sales_playbook": "Pitch 8-10% rental yields, capital gain projections, RDA/CDA verified files.",
    },
    {
        "name": "Urgent Family Homebuyer",
        "cluster_id": 1,
        "conversion_rate": "48.1%",
        "median_budget": "2.58 Crore",
        "traits": "High phone talk time, site visit booked, immediate possession requirement.",
        "sales_playbook": "Highlight 24/7 security, school/mosque proximity, park frontage, verified registry.",
    },
    {
        "name": "First-Time Budget Inquirer",
        "cluster_id": 2,
        "conversion_rate": "18.4%",
        "median_budget": "1.15 Crore",
        "traits": "Price-sensitive, asking for installment plans, 3 to 5 Marla inquiries.",
        "sales_playbook": "Offer flexible 3-year installment schedules, bank home financing partners.",
    },
    {
        "name": "Casual Market Explorer",
        "cluster_id": 3,
        "conversion_rate": "8.2%",
        "median_budget": "1.80 Crore",
        "traits": "Low interaction frequency, no site visit requested, web browsing behavior.",
        "sales_playbook": "Enroll in automated AI marketing drip; do not waste human closer phone hours.",
    },
]

# Operational Lead Routing SLAs
LEAD_TIERS: List[Dict[str, Any]] = [
    {
        "tier": "🔥 Hot Lead",
        "prob_range": "P >= 0.65",
        "sla": "Within 15 Minutes",
        "channel": "Direct Voice Call by Senior Closer",
        "action": "Immediate site tour booking & token proposal",
    },
    {
        "tier": "🌤 Warm Lead",
        "prob_range": "0.35 <= P < 0.65",
        "sla": "Within 24 Hours",
        "channel": "WhatsApp Video Tour + Consultative Call",
        "action": "Share digital brochures, layout maps & price sheets",
    },
    {
        "tier": "❄️ Cold Lead",
        "prob_range": "P < 0.35",
        "sla": "Automated Drip",
        "channel": "AI Email / WhatsApp Weekly Digest",
        "action": "Market rate trend alerts; zero human sales cost",
    },
]

# ROI Financial Model Calculations
def calculate_roi_summary(
    monthly_inbound_leads: int = 1000,
    sales_rep_count: int = 5,
    avg_property_value_pkr: float = 25000000.0,  # 2.5 Crore
    commission_rate: float = 0.015,  # 1.5% commission
) -> Dict[str, Any]:
    """Calculate projected financial ROI of the AI Valuation and Lead Scoring platform."""
    # Average deal commission
    avg_commission = avg_property_value_pkr * commission_rate  # 375,000 PKR

    # Baseline: Reps call 20% leads randomly
    called_leads = int(monthly_inbound_leads * 0.20)  # 200 leads
    baseline_conversions = called_leads * EXECUTIVE_METRICS["baseline_conversion_rate"]  # ~57 deals
    baseline_commission = baseline_conversions * avg_commission

    # With AI Scoring: Precision@Top-20% is 71.43%
    # But real conversions on the top 20% pool = called_leads * 71.43%
    ai_conversions = called_leads * EXECUTIVE_METRICS["precision_top_20"]  # ~142 deals
    ai_commission = ai_conversions * avg_commission

    incremental_deals = ai_conversions - baseline_conversions
    incremental_commission_pkr = incremental_deals * avg_commission

    # Annualized impact
    annual_incremental_commission = incremental_commission_pkr * 12
    platform_cost_annual = 1800000.0  # Hosting, APIs, Maintenance ~ 1.8 Lac/mo

    net_annual_benefit = annual_incremental_commission - platform_cost_annual
    roi_multiple = net_annual_benefit / platform_cost_annual if platform_cost_annual > 0 else 0

    return {
        "monthly_inbound_leads": monthly_inbound_leads,
        "monthly_leads_called": called_leads,
        "baseline_monthly_deals": round(baseline_conversions, 1),
        "ai_monthly_deals": round(ai_conversions, 1),
        "incremental_monthly_deals": round(incremental_deals, 1),
        "incremental_monthly_commission_pkr": round(incremental_commission_pkr, 0),
        "annual_incremental_commission_pkr": round(annual_incremental_commission, 0),
        "annual_net_benefit_pkr": round(net_annual_benefit, 0),
        "roi_multiple": round(roi_multiple, 2),
    }
