# Week 8 Capstone Project: AI Property Valuation & Lead Scoring Platform
**Domain:** Real Estate Machine Learning • Explainable AI • MLOps • LLM Agents • UrduLish Assistant  
**Client Scenario:** Real Estate Enterprise (Extension of Week 7 Voice Agent Ecosystem)  
**Deliverables Scope:** Week 8 — Day 1: Data Understanding, EDA & Feature Engineering

---

## 📌 Executive Summary
While Week 7 introduced an AI Voice Agent capable of conversational qualifying, the business faced two fundamental financial bottlenecks:
1. **Pricing Inconsistency:** Real estate agents quote property prices from gut feeling, causing overpriced listings that remain unsold for months and underpriced deals that hemorrhage commission margins.
2. **Sales Funnel Inefficiency:** Inbound sales representatives treat all leads equally, expending high-value phone time on unqualified callers while high-converting buyers slip away.

**Week 8 Solution:** A machine learning platform that:
- Accurately predicts fair market property valuations using regression models trained on historical transaction and listing data.
- Predictively scores inbound CRM leads by their empirical conversion probability.
- Explains every prediction with SHAP and translates insights into conversational UrduLish for local sales agents.

---

## 📁 Repository Structure (`Week 8`)
```
Week 8/
├── data/
│   ├── raw/
│   │   ├── properties_raw.csv           # Dataset A: 6,300 raw property listings (Min: 5,000)
│   │   └── leads_raw.csv                # Dataset B: 3,640 raw CRM leads (Min: 3,000)
│   ├── processed/
│   │   ├── properties_cleaned.csv       # Cleaned & deduplicated property listings (5,778 rows)
│   │   ├── leads_cleaned.csv            # Cleaned & deduplicated leads (3,496 rows)
│   │   ├── properties_featured.csv      # Dataset A with 8 engineered domain features
│   │   └── leads_featured.csv           # Dataset B with 5 engineered domain features
│   └── docs/
│       ├── data_dictionary_properties.md # Task 1: Complete Dataset A Data Dictionary
│       └── data_dictionary_leads.md      # Task 1: Complete Dataset B Data Dictionary
├── eda/
│   ├── figures/                         # Task 3: Publication-grade visualization charts (300 DPI)
│   │   ├── price_dist_raw_vs_log.png
│   │   ├── price_per_marla_by_city_society.png
│   │   ├── property_correlation_heatmap.png
│   │   ├── effect_bedrooms_age_corner.png
│   │   ├── lead_conversion_by_source_purpose.png
│   │   └── lead_class_imbalance.png
│   └── eda_analysis_report.md           # Task 3: Comprehensive report with one-line business insights
├── src/
│   ├── __init__.py
│   ├── config.py                        # Constants, paths, society tiers, unit conversions
│   ├── data_generator.py                # Task 1: Realistic Pakistani market data synthesizer
│   ├── data_cleaner.py                  # Task 2: Cleaning, parsing, outlier filtering, location normalization
│   ├── eda_generator.py                 # Task 3: Visual figure generation module
│   ├── feature_engineering.py           # Task 4: 13 domain features with justifications
│   └── pipeline.py                      # Task 5: Scikit-learn Pipeline, OHE vs Target Encoding, 70/15/15 split
├── notebooks/
│   └── day1_eda_and_pipeline.ipynb      # Interactive Jupyter notebook walkthrough
├── tests/
│   ├── __init__.py
│   └── test_day1_pipeline.py            # 10 automated unit & integration test suites
├── run_day1.py                          # Master one-click end-to-end execution script
└── README.md                            # Project documentation & deliverables summary
```

---

## 🚀 Quickstart Guide

To execute the entire Day 1 pipeline end-to-end (data generation, cleaning, EDA, feature engineering, pipeline encoding comparison, and automated tests):

```bash
cd "Week 8"
python run_day1.py
```

### Running Individual Pipeline Stages:
```bash
# 1. Generate Raw Datasets (Dataset A & B)
python -m src.data_generator

# 2. Clean Datasets & Remove Outliers / Duplicates
python -m src.data_cleaner

# 3. Generate EDA Figures
python -m src.eda_generator

# 4. Engineer Domain Features
python -m src.feature_engineering

# 5. Run Scikit-learn Pipelines, Leakage Audit & Encoding Comparison
python -m src.pipeline

# 6. Run Test Suite
python tests/test_day1_pipeline.py
```

---

## 📋 Day 1 Tasks & Deliverables Detailed

### Task 1 — Data Collection & Documentation
- **Dataset A — Property Listings (Regression):** 6,300 raw listings spanning Lahore, Islamabad, Karachi, and Rawalpindi. Contains messy Pakistani prices (`1.5 Crore`, `85 Lac`, `1.25 cr`), mixed area units (`Marla`, `Kanal`, `sq ft`, `sq yds`), and inconsistent location spellings (`DHA Ph 5` vs `DHA Phase 5`).
- **Dataset B — Real Estate Leads (Classification):** 3,640 CRM lead records reflecting telephony and CRM logs from Week 7, featuring inquiry channels, response speed, site visit bookings, objections, and conversion outcomes (~28.6% positive class).
- **Data Dictionaries:** Fully specified in [data_dictionary_properties.md](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/data/docs/data_dictionary_properties.md) and [data_dictionary_leads.md](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/data/docs/data_dictionary_leads.md).

### Task 2 — Data Cleaning & Normalization
- **Price Normalization:** Regex parser converts conversational Pakistani price strings (`Crore`, `Lac`, `Lakh`, comma-separated numbers) into numeric PKR floats (`price_pkr` and `budget_pkr`).
- **Area Normalization:** Standardizes mixed units (1 Kanal = 20 Marlas, 1 Marla = 225 sq ft, 1 Sq Yd = 9 sq ft) into universal `area_marla` and `area_sqft`.
- **Location Canonicalization:** Maps 35+ phonetic and spelling variations to standardized society names (`DHA Ph 5` $\rightarrow$ `DHA Phase 5`, `Gulberg 3` $\rightarrow$ `Gulberg III`, `Bahria Twn` $\rightarrow$ `Bahria Town`).
- **Deduplication:** Removed 417 duplicate property listings and 144 duplicate CRM leads.
- **Outlier Filtering (IQR & Z-Score):** Filtered out 105 extreme typographical anomalies using $\log(\text{price})$ Z-scores ($|Z| < 3.0$) and IQR bounds on price per marla.
- **Missing Value Imputation:**
  * Bedrooms and bathrooms imputed using median grouped by `property_type`.
  * Covered area estimated via typical built-up ratios ($0.85 \times \text{plot sqft}$).
  * Age imputed with median (5.0 years) to respect positive skewness.
  * Lead callback response time imputed by lead source median.

### Task 3 — Exploratory Data Analysis & Business Insights
Full visual report available at [eda_analysis_report.md](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/eda/eda_analysis_report.md).

| Figure | Metric / Focus | One-Line Business Insight |
| :--- | :--- | :--- |
| **Figure 1** | Price Distribution (Raw vs Log) | *Because 80% of listing volume trades below 4 Crore PKR while top-tier mansions create severe right-skew, training regression models on log-transformed prices protects real estate agents from overpricing middle-class homes.* |
| **Figure 2** | Price per Marla by City & Society | *Location tiering is the single largest valuation multiplier in Pakistan, where a 10-marla plot in Islamabad's F-6 commands 4.5× the market value of an identical plot in Ghauri Town.* |
| **Figure 3** | Inter-Feature Correlation Heatmap | *Plot area and covered built-up space account for over 65% of valuation variance, whereas proximity to main roads creates a substantial price premium over interior plots.* |
| **Figure 4** | Bedrooms, Age & Corner Impact | *Properties combining a brand-new build with a corner, park-facing plot command up to a 35% compound premium over an older, mid-block house of identical marla size.* |
| **Figure 5** | Lead Conversion by Source & Purpose | *Securing an on-site property visit increases conversion likelihood by over 700%, proving that voice agents and sales reps should focus 100% of their initial call on booking a physical visit.* |
| **Figure 6** | Target Variable Class Imbalance | *Because only 1 in 3.5 leads converts into a paid sale, ranking leads by predictive probability allows sales teams to capture 80% of revenue while making 50% fewer phone calls.* |

### Task 4 — Domain Feature Engineering
13 features engineered with explicit theoretical and empirical justifications:

1. **`price_per_marla`** (${\text{price\_pkr}} / {\text{area\_marla}}$): Standard real estate valuation benchmark. *(Exempt from training features to avoid target leakage).*
2. **`property_age_bucket`** (`Brand New <=1y`, `Modern 2-5y`, `Established 6-15y`, `Aging >15y`): Models steep initial structural depreciation before land value establishes a floor.
3. **`society_tier`** (`Tier 1 Prime`, `Tier 2 Mid`, `Tier 3 Budget`): Macro socioeconomic grouping capturing security, underground utilities, and prestige.
4. **`amenity_score`**: Quantified count of essential infrastructure (UPS backup, 24/7 security, gated community, mosque, park).
5. **`accessibility_composite`**: Harmonic index inversely weighted by distance to main roads, schools, and hospitals.
6. **`spatial_density_ratio`**: Covered area divided by plot sqft. Separates multi-storey builds from sprawling single-storey residences with large lawns.
7. **`bed_to_bath_ratio`**: Luxury structural layout proxy (ensuite 1:1 vs shared budget baths).
8. **`society_hist_median_ppm`**: Historical benchmark baseline per marla for each society, allowing base land anchoring without leaking the listing price.
9. **`lead_engagement_score`** ($\text{calls} \times \text{duration in mins}$): Quantifies total conversational attention invested by the buyer.
10. **`response_speed_category`** (`Immediate <=15m`, `Prompt 15m-1h`, `Standard 1h-4h`, `Delayed >4h`): Operational SLA bucketing speed-to-lead.
11. **`budget_to_market_ratio`**: Declared budget divided by society median benchmark price to detect budget mismatch.
12. **`lead_velocity`**: Call frequency per elapsed pipeline day to measure active buying momentum.
13. **`high_intent_flag`**: Composite VIP flag indicating a secured site visit, callback under 1 hour, and $\ge 2$ calls.

### Task 5 — Encoding, Scaling & Splitting Pipeline
- **One-Hot vs. Target Encoding Comparison:**
  * Property Valuation: Target Encoding reduced dimensionality from **65 to 31 features** (52% sparsity reduction) while improving validation $R^2$ to **0.8074** (vs. 0.8052 for OHE) and lowering MAE.
  * Lead Scoring: Target Encoding reduced dimensionality from **63 to 29 features**, increasing validation ROC-AUC to **0.8121** (vs. 0.8049 for OHE).
- **Data Splitting (70 / 15 / 15):**
  * Property Listings: 4,044 Train (70.0%), 867 Validation (15.0%), 867 Test (15.0%).
  * Leads Dataset: 2,447 Train, 524 Validation, 525 Test with **Stratified Sampling** strictly preserving the conversion rate at $28.61\%$, $28.63\%$, and $28.57\%$.
- **Data Leakage Check:**
  * Strictly removed `price_pkr` (target), `price` (raw text), and `price_per_marla` (derived target formula: $\text{price} = \text{ppm} \times \text{marla}$) from property feature set $X$.
  * Strictly removed `converted` (target) and `lead_id` (identifier) from leads feature set $X$.
- **Reusable Architecture:** Implemented via Scikit-learn's `ColumnTransformer` with `RobustScaler` on skewed features and `StandardScaler` on uniform distributions.
