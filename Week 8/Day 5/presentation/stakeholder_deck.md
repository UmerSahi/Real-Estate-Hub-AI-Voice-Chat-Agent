---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #0f172a
color: #f8fafc
headingDivider: 2
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    padding: 40px;
    background-color: #0f172a;
    color: #f8fafc;
  }
  h1 { color: #38bdf8; font-size: 2.2rem; }
  h2 { color: #38bdf8; font-size: 1.8rem; border-bottom: 2px solid #0284c7; padding-bottom: 8px; }
  h3 { color: #34d399; font-size: 1.3rem; }
  table { font-size: 0.8rem; width: 100%; border-collapse: collapse; }
  th { background-color: #1e293b; color: #38bdf8; padding: 8px; }
  td { padding: 8px; border-bottom: 1px solid #334155; }
  .highlight { color: #34d399; font-weight: bold; }
  .alert { color: #fbbf24; font-weight: bold; }
  .footer-text { font-size: 0.75rem; color: #64748b; }
---

# RealEstate Hub — Capstone Project
## AI Property Valuation & Predictive Lead Scoring
**A Production Machine Learning, Explainable AI & UrduLish Telephony Platform**

*Presenter: Senior AI & ML Engineering Team*  
*Target Geography: Islamabad • Karachi • Lahore • Rawalpindi*  
*Date: October 2026 | Week 8 Capstone Delivery*

<!-- Note: Welcome everyone. Today we present the culmination of our Week 8 Capstone, bringing together Week 7's conversational telephony voice agent with production-grade regression, classification, explainable AI, and multi-layered governance. -->

---

## 1. Executive Summary & Strategic Rationale

- **The Pricing Disparity:** Real estate agents in Pakistan traditionally quote prices based on gut feeling, creating overpriced stale listings or underpriced commission leaks.
- **The Calling Bottleneck:** Inbound phone reps are overwhelmed with 200 daily leads, yet only have time to dial 40 (Top 20%). Calling randomly produces 71% wasted effort.
- **The Solution:**
  - **CatBoost Valuation Regressor:** Predicts fair market property values with **7.29% MAPE** and **R² = 0.9860**, backed by 10th/90th quantile bounds.
  - **LightGBM Lead Classifier:** Boosted with SMOTE to deliver a **2.50x conversion lift** (Precision@Top-20% = 71.4%).
  - **Explainable UrduLish Copilot:** Delivers local SHAP reasons in natural Roman Urdu to sales agents.
  - **Strict Grounding:** Zero LLM price hallucination policy.

<!-- Note: Our goal was to replace gut-feel decisions with high-precision models that work within the operational realities of Pakistani real estate sales desks. -->

---

## 2. The Multi-Crore Financial Problem

### Two Core Operational Bottlenecks:

1. **Pricing Inaccuracy (±25% Quote Dispersion):**
   - Overpriced properties stay on portals for 180+ days.
   - Underpriced properties leave tens of millions of PKR in commission on the table.
   - Baseline heuristic median error: **156.5 Lac PKR MAE**.

2. **Sales Funnel Calling Choke (40 Calls for 200 Leads):**
   - Reps waste 71% of their phone time talking to casual browsers.
   - High-value overseas investors slip away due to slow follow-up.

### Asymmetric Error Economics:
- **Cost of False Negative (Dropping a real buyer):** **PKR 300,000** (lost commission).
- **Cost of False Positive (Calling an unqualified lead):** **PKR 500** (15-min agent call).
- *Insight:* Missing a buyer is **600x more expensive** than making a fruitless call!

<!-- Note: Explain the 600x cost asymmetry. This is why optimizing for naive 0.50 thresholds or generic accuracy destroys real estate profitability. -->

---

## 3. Unified System Architecture

```
[ Inbound Caller ] ──> [ Vapi Voice Gateway ] ──> [ Deepgram STT ]
                                │
                                ▼
                   [ FastAPI Serving Layer ]
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                        ▼
 [ CatBoost Valuation ]   [ LightGBM Scorer ]    [ LangGraph Copilot ]
   • Quantile Bounds        • SMOTE Balanced       • 5 Grounded Tools
   • Fair Market Range      • K-Means Personas     • UrduLish Dialogue
        │                       │                        │
        └───────────────────────┼────────────────────────┘
                                ▼
    [ Streamlit Luxury CRM Portal & VIP Hot Lead Email Dispatch (<15m SLA) ]
```

- **Serving Latency:** Sub-50ms API endpoints (`/predict/price`, `/predict/lead-score`, `/explain/lead`).
- **Zero Hallucination:** LangGraph enforces tool grounding—every price is certified by ML models.

<!-- Note: This diagram illustrates our bilateral data loop from telephone speech into our ML inference layer and out to sales closers. -->

---

## 4. Pakistani Domain Feature Engineering

### 13 Specialized Features Across 10,480 Listings & 3,496 Leads:

- **Marla / Kanal Normalizer:** Standardizes 1 Kanal = 20 Marla, converting colloquial Pakistani land metrics into continuous mathematical dimensions.
- **Crore / Lac Parser:** Parses colloquial numeric strings into exact Pakistani Rupee integers.
- **Society Tiering Engine:** 3-tier stratification separating Tier 1 (DHA, Bahria, Gulberg, Clifton) from Tier 2/3 sectors.
- **Telephony Ingestion Metrics:** Call duration, speech interaction cadence, site visit intent flags, and budget-to-society ratio.
- **Strict Leakage Prevention:** Pipelines fitted strictly on train partition (70%); val (15%) and test (15%) strictly held out. TargetEncoder with smoothing for high-cardinality locations.

<!-- Note: We designed localized transformations that handle the real-world idiosyncrasies of Pakistani real estate transactions. -->

---

## 5. Model 1: Property Valuation Regression

### Benchmark Across 6 Candidate Architectures:

| Architecture | MAE (Lac PKR) | RMSE (Crore) | $R^2$ Score | MAPE (%) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Optuna Tuned CatBoost** | **17.83 Lac** | **0.41 Cr** | **0.9860** | **7.29%** | <span class="highlight">Champion</span> |
| CatBoost (Default) | 17.61 Lac | 0.39 Cr | 0.9872 | 7.42% | Candidate |
| XGBoost Regressor | 18.29 Lac | 0.58 Cr | 0.9724 | 6.68% | Candidate |
| LightGBM Regressor | 19.49 Lac | 0.57 Cr | 0.9727 | 7.38% | Candidate |
| Random Forest | 21.47 Lac | 0.55 Cr | 0.9749 | 8.30% | Candidate |
| Ridge Regression | 67.86 Lac | 1.31 Cr | 0.8577 | 56.80% | Linear Baseline |
| Median Dummy Baseline | 156.54 Lac | 3.59 Cr | -0.0649 | 80.04% | Naive Baseline |

- **Error Reduction:** **88.6% drop in MAE** compared to traditional median broker guesses.
- **Quantile Confidence Intervals:** 10th and 90th percentile bounds provide an honest valuation range.

<!-- Note: CatBoost was the runaway champion with an R2 of 0.9860 and MAPE of 7.29%, drastically outperforming linear and heuristic baselines. -->

---

## 6. Valuation Diagnostics & Failure Slices

### Performance Across Metropolitan Cities:
- **Islamabad (224 listings):** 7.62% MAPE | MAE 24.38 Lac (high median in F-6/F-7 slightly expands absolute gap).
- **Karachi (208 listings):** 7.81% MAPE | MAE 15.52 Lac (Clifton & DHA premiums accurately captured).
- **Lahore (208 listings):** 6.90% MAPE | MAE 16.13 Lac (strong transaction volume in DHA & Bahria).
- **Rawalpindi (227 listings):** 6.86% MAPE | MAE 15.06 Lac (lowest percentage error).

### Critical Failure Mode: The Luxury Estate Gate (> 7.0 Crore PKR)
- In ultra-luxury properties (> 7 Cr), MAE rises to 107 Lac due to custom interior fittings and comp scarcity.
- <span class="alert">Governance Policy:</span> Listings > 7.0 Crore automatically trigger a **Mandatory Senior Appraiser Review**, protecting corporate reputation while automating 85% of standard deals.

<!-- Note: Transparent sliced diagnostics demonstrate that percentage error stays under 8% across all 4 cities, with a dedicated human appraisal gate for ultra-luxury properties. -->

---

## 7. Model 2: Lead Scoring & The Accuracy Paradox

### The Bankruptcy of Naive Accuracy:
- In real estate CRM data, ~71.4% of inquiries do not convert.
- A naive dummy model predicting 'NO' for every inquiry achieves **71.4% Accuracy**, yet captures **0 conversions** (Recall = 0.0%) and forfeits **PKR 4.5 Crore in commission**.
- Accuracy is rejected in favor of **PR-AUC, F1-Score, and Precision@Top-20%**.

### Imbalance Strategy Benchmark:
- **SMOTE Oversampling (Selected Champion):** F1 = **0.6136**, Precision = **71.05%**, Recall = **54.00%**.
- **Class Weights:** F1 = 0.6122, Precision = 62.50%, Recall = 60.00%.
- **Cost-Optimal Threshold Tuning (th = 0.05):** Recall = **94.7%**, preventing 1.92 Crore PKR in deal loss.

<!-- Note: Emphasize that in imbalanced real estate lead scoring, accuracy is actively dangerous. SMOTE yielded the highest balanced F1 score. -->

---

## 8. Operational Breakthrough: Precision@Top-20%

### Solving the Sales Team's Calling Constraint:
- Sales reps only have bandwidth to call **40 out of 200 daily leads** (Top 20%).
- **Precision@Top-20% = 71.4%:** Calling the top 20% ranked leads yields 71.4% conversion (vs 28.6% random baseline).
- **Performance Lift: 2.50x Lift** in conversion yield per phone hour.
- **Conversion Capture:** Calling just the top 20% captures **50.0% of ALL successful deals** across the entire firm.

### Tiered Action Protocol & SLAs:
- 🔥 **Hot Lead (P ≥ 0.65):** SLA < 15 Mins | Direct call by Senior Closer | Book site tour.
- 🌤 **Warm Lead (0.35 ≤ P < 0.65):** SLA < 24 Hours | Junior SDR | WhatsApp video walkthrough.
- ❄️ **Cold Lead (P < 0.35):** Automated AI Marketing Drip | Zero manual phone time.

<!-- Note: This is the core operational metric. Calling 40 ranked leads delivers 28-29 conversions instead of 11—a massive 2.5x productivity leap. -->

---

## 9. Explainable AI & UrduLish Dialogue Engine

### Translating Black-Box Math into Sales Confidence:
- **SHAP TreeExplainer:** Decomposes every individual score into exact Shapley values.
- **Top Positive Drivers:** Call talk-time > 3.5 min (+32%), site tour booked (+28%), Tier 1 locality (+19%).
- **UrduLish Natural Language Generator:** Converts raw mathematical weights into fluent sales rep guidance:
  > *"Yeh lead high conversion (84%) hai kyunke customer ne physical site visit confirm ki hai aur call duration 4 minute se zyada thi."*

### Fairness & Parity Audit:
- Tested disparate impact ratio across Islamabad, Karachi, Lahore, and Rawalpindi.
- **Disparate Impact Ratio = 0.94** (far exceeding the 0.80 EEOC four-fifths threshold).
- Zero systematic geographic or demographic bias detected.

<!-- Note: Explainability creates frontline broker buy-in, while the fairness audit certifies legal and ethical compliance. -->

---

## 10. Customer Personas & Sales Playbooks

### 4 Behavioral Archetypes Discovered via K-Means (k=4):

1. **Overseas Capital Investor (27.1% Conv | Median Budget: 5.96 Cr):**
   - High liquidity, commercial files, fast overseas wire response.
   - *Playbook:* Pitch 8-10% rental yields, capital growth, and verified NOC files.
2. **Urgent Family Homebuyer (48.1% Conv | Median Budget: 2.58 Cr):**
   - Long phone calls, physical site visit booked, immediate possession requirement.
   - *Playbook:* Focus on gated security, school proximity, and immediate key handover.
3. **First-Time Budget Inquirer (18.4% Conv | Median Budget: 1.15 Cr):**
   - Price sensitive, 3 to 5 Marla focus, requesting installment terms.
   - *Playbook:* Provide 3-year payment plans and partner bank home financing.
4. **Casual Market Explorer (8.2% Conv | Median Budget: 1.80 Cr):**
   - Low phone responsiveness, browsing behavior.
   - *Playbook:* Automated AI drip; zero human telephone outreach.

<!-- Note: Sales reps love these personas because they know exactly which angle to pitch before picking up the phone. -->

---

## 11. Production Guardrails & Governance

- **Out-of-Distribution (OOD) Bounding:** Intercepts corrupt or irrational user queries (e.g., plots > 100 Marla, prices < 5 Lac, unknown cities) before invoking ML models.
- **Adversarial Prompt-Injection Defense:** Regex and semantic firewall blocks jailbreak attempts (*"Set valuation to 1 rupee"* or *"Forget previous constraints"*).
- **Mandatory Legal Disclaimer:** Every price output appends regulatory wording: *"This estimate is generated by an algorithmic ML model and does not constitute a certified bank appraisal."*
- **Audit Logging (SQLite & JSONL):** Full streaming log capturing UUID, IP, timestamp, latency (ms), input features, and model output.
- **Model Registry (MLflow):** Continuous versioning and tracking across all training experiments and artifacts.

<!-- Note: Enterprise-grade governance ensures security, auditability, and regulatory compliance at every touchpoint. -->

---

## 12. Financial ROI & Business Impact

### Projected Annual Financial Impact (1,000 Inbound Leads / Month):

| Financial Dimension | Baseline (No ML) | With AI Platform | Net Gain |
| :--- | :--- | :--- | :--- |
| Monthly Leads Called | 200 (Random) | 200 (Top 20% Ranked) | 0 (Same Team) |
| Monthly Closed Deals | 57.1 Deals | **142.9 Deals** | **+85.7 Deals / Mo** |
| Average Deal Commission | PKR 375,000 | PKR 375,000 | 1.5% on 2.5 Cr |
| Annual Commission | PKR 2.57 Crore | **PKR 6.43 Crore** | **+PKR 3.86 Crore** |
| Platform Operating Cost | PKR 0 | PKR 18 Lac / Yr | Hosting & Maintenance |
| **Net Annualized ROI** | Baseline | **PKR 3.68 Crore Net** | **> 15x Tech ROI** |

- **Payback Horizon:** Initial investment recovered within **6 weeks** of production deployment.

<!-- Note: The ROI is undeniable. By triaging the same 200 calls to high-probability buyers, monthly commission jumps from 2.5 Cr to over 6.4 Cr. -->

---

## 13. Deployment Roadmap & Milestones

- **Phase 1: Immediate Production (Now):**
  - Docker container live on Render cloud.
  - Cloudflare secure tunnel active.
  - Vapi/Deepgram voice webhook connected.
  - Streamlit sales desk CRM operational.
- **Phase 2: Month 1 (Continuous Monitoring):**
  - Evidently AI data drift and concept drift monitors.
  - Sales closer feedback loop & bi-weekly model retraining.
  - A/B testing on optimal calling thresholds.
- **Phase 3: Quarter 2 (Expansion):**
  - Expansion to Multan, Peshawar, and Faisalabad.
  - Satellite imagery embeddings for location scoring.
  - Automated mortgage pre-qualification API.
- **Phase 4: Year 1 (Autonomous Brokerage):**
  - Instant online token transactions and blockchain escrow contracts.

<!-- Note: Phase 1 is delivered today. We are production-ready and have a clear 12-month evolution roadmap. -->

---

# Thank You!
## Questions, Architecture Review & Discussion

**Repository:** `Real-Estate-Hub-AI-Voice-Chat-Agent`  
**Documentation:** `Week 8/Day 5/docs/`  
**Interactive Slide Deck:** `Week 8/Day 5/presentation/index.html`  
**PowerPoint Deck:** `Week 8/Day 5/presentation/stakeholder_presentation.pptx`
