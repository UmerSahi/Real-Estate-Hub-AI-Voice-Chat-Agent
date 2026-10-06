# 03. Data Engineering & Pakistani Feature Store
**Document Code:** REH-DOC-03  
**Project:** Week 8 Capstone Platform: AI Property Valuation & Lead Scoring  
**Target Audience:** Data Engineers, Machine Learning Engineers, Pipeline Developers  
**Status:** Feature Store Technical Specification  

---

## 1. Datasets Ingestion & Provenance

The platform ingests, standardizes, and features two primary enterprise datasets:

### Dataset A: Property Listings (`properties_featured.csv`)
- **Total Records:** 10,480 listings across 4 metropolitan regions (Islamabad, Karachi, Lahore, Rawalpindi).
- **Core Raw Features:** `property_id`, `city`, `society`, `property_type` (House, Flat, Upper Portion, Lower Portion, Farmhouse), `area_value`, `area_unit` (Marla, Kanal, Sq. Yd), `bedrooms`, `bathrooms`, `purpose` (For Sale, For Rent), `raw_price_str`, `has_corner`, `facing_park`, `main_boulevard`.

### Dataset B: CRM & Telephony Leads (`leads_featured.csv`)
- **Total Records:** 3,496 leads captured via telephony Call Detail Records (CDR) and web portal inquiries.
- **Core Raw Features:** `lead_id`, `created_at`, `inquiry_source` (Voice Call, WhatsApp, Web Form, Walk-in), `caller_city`, `target_society`, `stated_budget`, `call_duration_seconds`, `inquiry_velocity_7d`, `site_visit_booked`, `converted` (Binary Ground Truth: 0 or 1).

---

## 2. Pakistani Domain Transformations & Parsers

Standard off-the-shelf NLP and preprocessing libraries fail when exposed to colloquial Pakistani currency and land measurements. We developed dedicated, deterministic normalization engines:

### 2.1 Marla / Kanal Area Normalizer
Colloquial Pakistani real estate expresses property sizes in Marlas (approx. 225 or 250 sq. ft.) and Kanals (20 Marlas).
$$\text{Area in Marla} = \begin{cases} 
\text{area\_value} \times 20 & \text{if unit } = \text{'Kanal'} \\
\text{area\_value} \times 1.0 & \text{if unit } = \text{'Marla'} \\
\text{area\_value} \div 25 & \text{if unit } = \text{'Sq. Yd'} 
\end{cases}$$

### 2.2 Crore & Lac Currency Normalizer
Prices in Pakistan are quoted in Lacs ($10^5$) and Crores ($10^7$). Strings such as `"2.5 Crore"`, `"75 Lac"`, or `"1 Cr 20 Lac"` are parsed into exact numeric integers:
$$\text{Price (PKR)} = (\text{Crores} \times 10,000,000) + (\text{Lacs} \times 100,000)$$

### 2.3 Society Tiering Engine
Localities exhibit extreme socioeconomic price stratification. We established a 3-tier categorical system:
- **Tier 1 (Premium / Gated):** DHA (all phases), Bahria Town (all phases), Gulberg, F-6, F-7, F-8, E-7, Clifton, Naval Anchorage.
- **Tier 2 (Established Urban):** Johar Town, Model Town, G-10, G-11, I-8, Askari, PECHS, Gulshan-e-Iqbal.
- **Tier 3 (Emerging Suburban):** B-17, Faisal Town, Park View City, Bahria Enclave, Scheme 33, Surjani.

---

## 3. The 13 Engineered Domain Features

| # | Feature Name | Formula / Logic | Domain Justification |
| :--- | :--- | :--- | :--- |
| **1** | `area_marla` | Standardized to Marla ($1 \text{ Kanal} = 20 \text{ Marla}$) | Uniform metric for physical plot size across all regions. |
| **2** | `price_per_marla` | $\text{price} \div \text{area\_marla}$ | Essential target benchmark and comparative pricing signal. |
| **3** | `society_tier` | Tier 1 (1.0), Tier 2 (0.6), Tier 3 (0.3) | Captures security, underground utilities, and developer prestige. |
| **4** | `bed_bath_ratio` | $\text{bedrooms} \div \max(\text{bathrooms}, 1)$ | Architectural layout balance; indicates luxury vs budget construction. |
| **5** | `is_corner_or_park` | $\text{has\_corner} \lor \text{facing\_park}$ | Real estate premium: corner/park plots carry a 10-15% market markup. |
| **6** | `main_boulevard_flag` | Boolean (0 or 1) | Commercial flexibility markup for boulevard-facing properties. |
| **7** | `city_price_index` | City median relative to national median | Macroeconomic purchasing power differences (e.g. Islamabad > Rawalpindi). |
| **8** | `property_age_decay` | $\exp(-0.04 \times \text{age\_years})$ | Construction depreciation factor on existing house structures. |
| **9** | `call_duration_mins` | $\text{call\_duration\_seconds} \div 60$ | High telephonic talk-time strongly correlates with buyer purchase intent. |
| **10** | `inquiry_velocity` | Inquiries logged across past 7 days | Urgency indicator; active buyers make multiple inquiries in a tight window. |
| **11** | `budget_to_society_ratio`| $\text{stated\_budget} \div \text{society\_median\_price}$ | Affordability index; filters out aspirational callers with insufficient capital. |
| **12** | `site_visit_intent` | Explicit physical visit confirmed (0/1) | Highest empirical predictor of high-ticket real estate closing. |
| **13** | `source_weight` | Voice (1.0), WhatsApp (0.8), Web (0.4) | Channel commitment weighting reflecting buyer effort. |

---

## 4. Leakage Audit & Pipeline Architecture

### 4.1 Strict Partition Isolation
Data leakage is the primary cause of models failing in real-world production. We enforced strict 70 / 15 / 15 stratified partitioning:
- **Training Set (70%):** 7,336 listings / 2,447 leads. All preprocessor transformers (`TargetEncoder`, `RobustScaler`, `SimpleImputer`) are fitted **exclusively** on this fold.
- **Validation Set (15%):** 1,572 listings / 524 leads. Used strictly for Optuna hyperparameter tuning and threshold selection.
- **Test Set (15%):** 1,572 listings / 525 leads. Blind evaluation set; touched only once for final benchmark scoring.

### 4.2 Leakage Audit Checklist Passed:
- [x] Target variable (`price_pkr` and `converted`) explicitly dropped from feature matrix $X$ before pipeline entry.
- [x] Derived target metrics (e.g., `price_per_marla`, `log_price`) removed from regressors.
- [x] Out-of-fold target encoding with smoothing parameter $m=10.0$ used on high-cardinality categorical variables (`society`, `city`) to prevent target memorization.
- [x] All missing value imputations calculated strictly from training medians/modes.

```python
# Encapsulated Scikit-Learn Preprocessing Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler, OneHotEncoder
from category_encoders import TargetEncoder

numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', RobustScaler())
])

categorical_transformer = Pipeline(steps=[
    ('target_enc', TargetEncoder(smoothing=10.0)),
    ('scaler', RobustScaler())
])

preprocessor = ColumnTransformer(transformers=[
    ('num', numeric_transformer, numeric_features),
    ('cat', categorical_transformer, categorical_features)
])
```
