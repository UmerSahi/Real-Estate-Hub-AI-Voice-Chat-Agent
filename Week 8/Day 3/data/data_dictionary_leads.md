# Data Dictionary — Dataset B: Real Estate Leads (Classification)

**Domain:** Real Estate Sales Funnel & Lead Conversion Prediction  
**Target Variable:** `converted` (Binary: `yes` / `no` -> `1` / `0`)  
**Total Raw Rows:** 3,640 lead records  
**Baseline Conversion Rate:** ~15.2% (reflects authentic high-ticket real estate conversion benchmarks)  
**Source Baseline:** Week 7 CRM persistence database (`crm_leads`, `crm_transcripts`, `crm_appointments`) extended for capstone ML training.

---

## Field Specifications

| Column Name | Raw Data Type | Cleaned Data Type | Description | Unit | Source | Known Issues & Artifacts |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `lead_id` | String | String | Unique tracking code for inbound prospective buyer/investor | Identifier | Telephony / CRM | ~4% duplicate registrations due to multi-channel inquiries |
| `lead_source` | String | Categorical | Channel through which the inquiry entered the pipeline (`call`, `WhatsApp`, `Facebook`, `website`, `walk-in`) | Channel Name | Inbound webhook | High variance in intent: walk-ins and direct calls convert significantly higher than top-of-funnel Facebook ads |
| `budget` | String | Float (`budget_pkr`) | Prospect's declared or estimated investment budget | Mixed (Crore, Lac, PKR numeric) | CRM call intake form | Formatted conversationally (e.g. `2.5 Crore`, `80 Lac`); requires regex normalization to numeric PKR |
| `preferred_city` | String | Categorical | Primary target metropolitan area for investment/residence | City Name | Customer profile | Standardized across Lahore, Islamabad, Karachi, Rawalpindi |
| `preferred_society` | String | Categorical (Standardized) | Desired housing society or sector | Scheme Name | Client preference | Minor spelling variants; must be aligned with property valuation location dictionary |
| `purpose` | String | Categorical | Client's stated transaction objective (`buy`, `rent`, `invest`) | Intent Type | Voice agent intake | `buy` and `invest` drive the primary sales commission pipeline |
| `number_of_calls` | Integer | Integer | Total customer service / voice agent calls logged | Count | Telephony CDR | Right-skewed count (1 to 7+ calls); high engagement proxy |
| `call_duration_avg_sec` | Integer | Integer | Average duration of conversation per call session | Seconds | Twilio / Vapi log | Skewed distribution; longer calls indicate deep qualifying conversations |
| `response_time_min` | Float | Float | Delay between lead arrival and sales representative callback | Minutes | Agent response timer | ~4% missing; critical business SLA metric (speed-to-lead) |
| `visit_booked` | String | Binary (`1` / `0`) | Whether an on-site physical property inspection has been scheduled | Binary (`yes` / `no`) | CRM Appointment Module | Highest single correlation with conversion; must ensure no future leakage |
| `days_since_first_contact`| Integer | Integer | Total elapsed days since lead first registered in system | Days | CRM timeline | Measure of lead aging / staleness in pipeline |
| `objection_raised` | String | Categorical | Primary friction or objection voiced during agent interactions | Reason string | Agent transcript summary | ~3% unrecorded; heavy negative impact from financial/NOC objections |
| `converted` | String | Binary Target (`1` / `0`) | Final outcome: whether the lead closed a purchase/rental contract | Binary (`yes` / `no`) | CRM Deal Won/Lost audit | **Target class imbalance:** ~15% positive, ~85% negative; requires stratified sampling and class weighting |

---

## Data Leakage Prevention Protocol

To ensure models generalize in real-time production:
1. **No Post-Event Predictors:** Columns like `contract_signing_date`, `commission_paid`, or `post_sale_feedback` are strictly excluded from dataset generation.
2. **Pre-Close Telephony Window:** All features represent signals captured *prior* to contract execution.
3. **Budget Normalization:** Raw text budget is converted to numeric PKR before modeling and compared with market prices without leaking target conversion labels.
