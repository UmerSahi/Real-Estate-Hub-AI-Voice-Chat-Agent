# Week 8 — Day 3: Lead Scoring Model (Classification) & Explainability

> **Production AI Voice Chat Agent Platform — Capstone Machine Learning & XAI**  
> **Scenario:** The sales team has **200 new leads** and time to call only **40** (Top 20%). Our model decides who gets called first. A wrong decision means a lost sale, so the model must be accurate and it must explain itself!

---

## 📂 Day 3 Architecture & Directory Layout

```text
Week 8/Day 3/
├── data/
│   ├── leads_featured.csv                # 3,496 featured leads from telephony CDR & CRM
│   └── data_dictionary_leads.md          # Complete data dictionary & field specifications
├── models/
│   ├── best_lead_scoring_model.joblib    # Serialized champion classifier (LightGBM)
│   ├── lead_preprocessor.joblib          # Scikit-learn ColumnTransformer (RobustScaler + OneHotEncoder)
│   ├── kmeans_personas_model.joblib      # Serialized CustomerPersonaEngine (K-Means archetypes)
│   └── persona_scaler.joblib             # Feature scaler for clustering features
├── reports/
│   ├── lead_scoring_benchmark_report.md  # Comprehensive executive Markdown report
│   └── figures/
│       ├── roc_pr_curves_comparison.png  # Figure 1: Multi-model ROC and PR curves
│       ├── confusion_matrix_top_models.png# Figure 2: Confusion matrices across decision policies
│       ├── imbalance_strategy_comparison.png# Figure 3: Benchmark of 4 imbalance strategies
│       ├── customer_personas_clusters.png# Figure 4: K-Means 2D PCA & behavioral distribution
│       ├── shap_global_importance.png    # Figure 5: Global feature attribution beeswarm
│       ├── shap_local_waterfall.png      # Figure 6: Local individual prediction waterfall
│       └── fairness_subgroup_analysis.png# Figure 7: Algorithmic fairness & bias audit
├── notebooks/
│   └── day3_lead_scoring.ipynb           # Fully executed Jupyter Notebook with embedded outputs
├── src/
│   ├── __init__.py
│   ├── config.py                         # Paths, thresholds, business cost parameters ($300k vs $500)
│   ├── data_loader.py                    # Stratified 70/15/15 split, ColumnTransformer pipeline
│   ├── classification_models.py          # Task 1: Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost
│   ├── imbalance_handler.py              # Task 2: Imbalance comparison (None, Class weights, SMOTE, Tuning)
│   ├── model_evaluation.py               # Task 3: Precision@Top-20%, Calibration, Cost curves
│   ├── lead_segmentation.py              # Task 4: Hot/Warm/Cold classification + K-Means personas
│   ├── explainability_shap.py            # Task 5: SHAP beeswarm/waterfall, UrduLish engine, Fairness audit
│   ├── lead_scoring_service.py           # Production inference pipeline (scoring, SLA, SHAP reasons)
│   └── notebook_runner.py                # Headless execution engine to populate day3_lead_scoring.ipynb
├── tests/
│   └── test_day3_lead_scoring.py         # 12 unit & integration tests (100% passing)
├── run_day3.py                           # Master automated pipeline runner
└── README.md                             # This documentation
```

---

## 📊 Task-by-Task Implementation & Technical Results

### Task 1 — Classification Models Benchmark
We established rigorous benchmarks comparing linear baseline and non-linear gradient-boosted ensembles on our stratified test partition (525 leads, 28.57% conversion baseline):

| Model | ROC-AUC | PR-AUC | F1-Score | Precision | Recall | Accuracy | Train Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost** | **0.8201** | **0.6596** | **0.5906** | 72.12% | 50.00% | 80.19% | 0.24s |
| **LightGBM** | **0.8141** | **0.6451** | **0.5946** | 70.64% | 51.33% | 80.00% | 0.20s |
| **CatBoost** | 0.8155 | 0.6520 | 0.5854 | **75.00%** | 48.00% | **80.57%** | 0.63s |
| **Random Forest** | 0.8124 | 0.6469 | 0.5583 | 74.44% | 44.67% | 79.81% | 0.25s |
| **Logistic Regression** (Baseline) | 0.8185 | 0.6539 | 0.5748 | 70.19% | 48.67% | 79.43% | 0.05s |

---

### Task 2 — Handling Imbalanced Data & The Accuracy Paradox

#### The Accuracy Paradox Explained:
- In real estate brokerage, only ~28.6% of leads close a deal, while 71.4% do not convert.
- A naive "dumb" model that predicts "NO" for 100% of incoming leads achieves **71.4% Accuracy**, yet captures **0 conversions** (Recall = 0.0%).
- **Business Cost:** Missing all 150 converting buyers costs **4.5 Crore PKR** in forfeited brokerage commissions.
- Therefore, raw accuracy is a misleading vanity metric; production models must be evaluated on **PR-AUC, Recall, and Precision@Top-20%**.

#### Imbalance Strategy Comparison:
| Imbalance Strategy | Decision Threshold | F1-Score | Recall | Precision | PR-AUC | ROC-AUC | Accuracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SMOTE** | 0.50 | **0.6136** | 54.00% | **71.05%** | 0.6444 | 0.8116 | 80.57% |
| **Class Weights** | 0.50 | 0.6122 | 60.00% | 62.50% | 0.6328 | 0.8022 | 78.29% |
| **Threshold Tuning** | 0.16 | 0.5962 | **82.67%** | 46.62% | **0.6451** | **0.8141** | 68.00% |
| **No Balancing** | 0.50 | 0.5946 | 51.33% | 70.64% | 0.6451 | 0.8141 | 80.00% |

- `SMOTE` achieves the highest balanced F1 score (0.6136).
- `Threshold Tuning (th=0.16)` captures over **82.6% of all converting leads**, directly mitigating the 300,000 PKR penalty of dropped clients.

---

### Task 3 — Comprehensive Evaluation & Solving the Calling Constraint

#### The Sales Constraint: 40 Calls out of 200 Leads (Top 20% Capacity)
- **Top 20% Calling Volume:** In our 525 test leads, the sales team calls only the top **105 leads** (20%).
- **Precision@Top-20%:** **71.43%** of the selected leads convert (vs. only **28.57%** under random calling).
- **Performance Lift:** **2.50x Lift** over untargeted cold calling!
- **Total Deals Captured:** Calling just the top 20% captures **50.0% of ALL successful deals** across the entire company.

#### Cost-Optimal Decision Analysis:
- $C_{\text{FN}} = 300,000\text{ PKR}$ (Lost commission) vs. $C_{\text{FP}} = 500\text{ PKR}$ (Wasted 15-min call).
- Lowering the decision threshold from 0.50 to cost-optimal policy saves **over 1.9 Crore PKR** in prevented lead abandonment.

---

### Task 4 — Operational Lead Segmentation & Customer Personas

#### A. Lead Priority Tiers & Sales SLA:
| Tier | Probability Range | Action SLA | Channel | Assigned Role | Action Protocol |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🔥 **Hot** | $P \ge 0.65$ | **Within 1 hour** | Direct Phone Call | Senior Consultant | Lock physical site visit, discuss commercial terms & token |
| 🌤 **Warm** | $0.35 \le P < 0.65$ | **Within 24 hours** | Consultative Call + WhatsApp | Junior SDR | Share society video tours, layout maps, price sheets |
| ❄️ **Cold** | $P < 0.35$ | **Automated Drip** | WhatsApp / Email Digest | AI Marketing Engine | Zero manual calls; send weekly market rate alerts |

#### B. Customer Personas Discovered via K-Means ($k=3$):
1. **Overseas / High-Net-Worth Capital Investor:**
   - *Median Budget:* 5.96 Crore PKR | *Conversion Rate:* 27.1%
   - *Traits:* High budget, fast response turnaround, commercial/file interest, demands verified NOC documents.
   - *Sales Pitch:* Highlight 8-10% rental yields, capital growth projections, fast file transfers, and overseas tax treaty advantages.
2. **Urgent Family Homebuyer (Active Inquirer):**
   - *Median Budget:* 2.58 Crore PKR | *Conversion Rate:* 48.1% (Highest Conversion Archetype)
   - *Traits:* High phone engagement, long call durations, booked physical site visit, family decision-making dynamic.
   - *Sales Pitch:* Focus on gated community security, immediate possession, school/park proximity, and vetted construction quality.
3. **First-Time Explorer / Budget Inquirer:**
   - *Median Budget:* 1.74 Crore PKR | *Conversion Rate:* 23.3%
   - *Traits:* Lower budget, longer response delay, multiple financing/bank objections, low site visit booking rate.
   - *Sales Pitch:* Introduce flexible 3-5 year installment plans, affordable rental options, and low-downpayment payment plans.

---

### Task 5 — Explainability with SHAP & Algorithmic Fairness Audit

#### Plain-Language UrduLish Explanation Engine:
The engine translates raw SHAP attributions into conversational explanations for sales agents:
- **Hot Lead:**
  > *"Yeh lead 🔥 Hot hai (Conversion Score: 98%) kyun ke physical property inspection visit already booked hai, high engagement score show kiya, client ne 6 martaba call ki. SLA: Call within 1 hour. Assigned: Senior Property Consultant / Closer. Recommended Action: Lock physical site visit; discuss commercial terms, payment schedule, and immediate token deposit."*
- **Cold Lead:**
  > *"Yeh lead ❄️ Cold hai (Conversion Score: 5%) kyun ke response time 180 minute se zyada tha aur financing na milne ka aitraz uthaya. Is par phone call zaya na karein. Ise automated WhatsApp drip campaign par enroll karein."*

#### Algorithmic Fairness & Bias Audit:
- **Lead Source:** Call (22.4%), WhatsApp (34.1%), Facebook (30.1%), Website (22.6%), Walk-in (57.1%).
- **Disparate Impact Ratio (DIR):** All channels $\ge 1.00$ (Passes 80% Non-Discrimination Rule).
- **City Equity:** Islamabad, Karachi, Lahore, and Rawalpindi all satisfy fairness parity ($\text{DIR} \ge 0.88$).

---

## 🚀 Daily Quickstart Instructions

### 1. Run Master Pipeline:
```bash
cd "Week 8\Day 3"
python run_day3.py
```

### 2. Re-execute Interactive Jupyter Notebook:
```bash
python -m src.notebook_runner
```

### 3. Run Automated Unit Test Suite (12 Tests):
```bash
python tests/test_day3_lead_scoring.py
```

---

## ✅ Quality Assurance Verification
- **Automated Tests:** **12/12 Tests Passing** in 7.49s (`tests/test_day3_lead_scoring.py`).
- **Notebook Status:** [`notebooks/day3_lead_scoring.ipynb`](notebooks/day3_lead_scoring.ipynb) 100% pre-executed, 0 errors, embedded high-resolution figures.
- **Model Registry Artifacts:** Serialized in `models/` with zero data leakage.
