# 05. Lead Scoring Classification & Explainability
**Document Code:** REH-DOC-05  
**Project:** Week 8 Capstone Platform: AI Property Valuation & Lead Scoring  
**Target Audience:** Machine Learning Engineers, Sales Directors, AI Ethics Officers  
**Status:** Champion Classification & XAI Specification  

---

## 1. Problem Framing & Operational Constraint

### The Business Reality
In a commercial real estate firm receiving **200 leads daily**, a 5-person sales desk has capacity to make at most **40 outbound calls per day** (Top 20% capacity).
- **Primary Goal:** Maximize the number of conversions captured within those 40 phone calls.
- **Evaluation Priority:** Precision@Top-20%, PR-AUC, and F1-Score (naive accuracy is strictly rejected).

---

## 2. Model Benchmark Evaluation (Test Set: 525 Leads)

Baseline conversion rate in the holdout partition is **28.57%** (150 converted vs 375 non-converted):

| Model Architecture | ROC-AUC | PR-AUC | F1-Score | Precision | Recall | Accuracy | Train Time | Production Role |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost Classifier** | **0.8201** | **0.6596** | 0.5906 | 72.12% | 50.00% | 80.19% | 0.24s | Benchmark |
| **LightGBM + SMOTE** | 0.8141 | 0.6451 | **0.6136** | **71.05%** | **54.00%** | **80.57%** | 0.20s | 🏆 **Champion** |
| CatBoost Classifier | 0.8155 | 0.6520 | 0.5854 | 75.00% | 48.00% | 80.57% | 0.63s | Candidate |
| Logistic Regression | 0.8185 | 0.6539 | 0.5748 | 70.19% | 48.67% | 79.43% | 0.05s | Linear Baseline |
| Random Forest | 0.8124 | 0.6469 | 0.5583 | 74.44% | 44.67% | 79.81% | 0.25s | Candidate |

---

## 3. Class Imbalance Mitigation & The Accuracy Paradox

### 3.1 The Accuracy Paradox Mathematical Proof
If a naive classifier simply outputs $\hat{y} = 0$ (Non-Converting) for all leads:
$$\text{Accuracy} = \frac{375}{525} = 71.43\%$$
$$\text{Recall} = \frac{0}{150} = 0.0\%$$
$$\text{Deals Closed} = 0 \quad \Longrightarrow \quad \text{Lost Commission} = 150 \times 300,000 = \text{PKR } 4.5 \text{ Crore}$$
Relying on accuracy would incentivize the model to never call anyone, causing catastrophic commercial failure.

### 3.2 Imbalance Strategies Benchmark

| Imbalance Mitigation Method | Decision Threshold | F1-Score | Recall | Precision | PR-AUC | ROC-AUC | Selection Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SMOTE Synthetic Oversampling** | 0.50 | **0.6136** | 54.00% | **71.05%** | 0.6444 | 0.8116 | 🏆 **Champion (Balanced)** |
| Balanced Class Weights | 0.50 | 0.6122 | 60.00% | 62.50% | 0.6328 | 0.8022 | Strong recall alternative |
| Threshold Tuning (th = 0.16) | 0.16 | 0.5962 | 82.67% | 46.62% | 0.6451 | 0.8141 | High-recall sensitivity |
| No Balancing (Default) | 0.50 | 0.5946 | 51.33% | 70.64% | 0.6451 | 0.8141 | Depressed recall |

---

## 4. Solving the Sales Capacity Bottleneck: Precision@Top-20%

When the model ranks all 200 daily leads by conversion probability and the sales desk dials the top 40:
- **Baseline Random Dialing:** 40 calls $\times 28.57\% = 11.4$ conversions.
- **AI-Ranked Dialing (Precision@Top-20%):** 40 calls $\times 71.43\% = \mathbf{28.6}$ conversions.
- **Conversion Lift:**
$$\text{Lift} = \frac{71.43\%}{28.57\%} = \mathbf{2.50x \text{ Lift}}$$
- **Total Deal Capture:** Those 40 calls capture $\mathbf{50.0\%}$ of all successful conversions occurring in the entire customer cohort.

### Operational Tiering & SLAs:
| Tier | Score Range | Action SLA | Assigned Role | Channel | Operational Playbook |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 🔥 **Hot Lead** | $P \ge 0.65$ | **< 15 Minutes** | Senior Closer | Direct Phone Call | Immediate site tour booking & token lock. |
| 🌤 **Warm Lead** | $0.35 \le P < 0.65$| **< 24 Hours** | Junior SDR | WhatsApp Video | Send video tours, layout maps, price comps. |
| ❄️ **Cold Lead** | $P < 0.35$ | Automated Drip | AI Nurture Engine | Email / WhatsApp | Weekly market rate digest; zero human labor. |

---

## 5. Explainable AI (SHAP) & UrduLish Dialogue Engine

### 5.1 SHAP TreeExplainer Attributions
Using TreeExplainer, every individual lead receives exact Shapley contribution values:
$$\phi_0 + \sum_{j=1}^M \phi_j(x) = f(x)$$
- `call_duration_seconds > 210`: $+32\%$ attribution.
- `site_visit_booked == True`: $+28\%$ attribution.
- `target_society in Tier 1`: $+19\%$ attribution.
- `inquiry_velocity > 3`: $+14\%$ attribution.
- `budget_to_society_ratio < 0.6`: $-21\%$ drag.

### 5.2 UrduLish Natural Language Generator
Sales agents reject mathematical log-odds. Our engine translates Shapley weights into conversational Roman Urdu:
> *"Yeh lead high conversion (84%) hai kyunke customer ne site visit book ki hai aur call duration 4 minute se zyada thi."*

---

## 6. Algorithmic Fairness & Bias Audit

To ensure equitable service and prevent socioeconomic or geographic discrimination:
$$\text{Disparate Impact Ratio} = \frac{P(\hat{Y}=1 \mid \text{Unprivileged})}{P(\hat{Y}=1 \mid \text{Privileged})}$$

- **Test Results Across Subgroups:**
  - Islamabad: $P(\text{Hot}) = 29.4\%$
  - Karachi: $P(\text{Hot}) = 28.1\%$
  - Lahore: $P(\text{Hot}) = 30.2\%$
  - Rawalpindi: $P(\text{Hot}) = 28.4\%$
- **Disparate Impact Ratio:** **0.94** (far exceeding the standard EEOC **0.80 Four-Fifths Rule**).
- **Audit Conclusion:** The model exhibits zero systematic geographic bias.
