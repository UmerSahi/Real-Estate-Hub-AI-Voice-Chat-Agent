# Week 8 Capstone Project: AI Property Valuation & Lead Scoring Platform
**Domain:** Real Estate Machine Learning • Explainable AI • MLOps • LLM Agents • UrduLish Assistant  
**Client Scenario:** Real Estate Enterprise (Extension of Week 7 Voice Agent Ecosystem)  
**Duration:** 5 Days

---

## 📌 Project Architecture & Daily Breakdown

- 📁 [**Day 1: Data Understanding, EDA & Feature Engineering**](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%201/README.md)
  - Task 1: Data Collection & Documentation (Dataset A & Dataset B)
  - Task 2: Data Cleaning (Crore/Lac parser, Marla/Kanal normalizer, IQR/Z-score outlier filter, canonicalization)
  - Task 3: Exploratory Data Analysis (6 publication-grade figures with one-line business insights)
  - Task 4: Domain Feature Engineering (13 features with theoretical & domain justifications)
  - Task 5: Scikit-learn Pipelines, OHE vs Target Encoding, 70/15/15 stratified splits, data leakage audit
  - Execution: [run_day1.py](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%201/run_day1.py) & [day1_eda_and_pipeline.ipynb](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%201/notebooks/day1_eda_and_pipeline.ipynb)

- 📁 [**Day 2: Property Valuation Model (Regression)**](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%202/README.md)
  - Task 1: Baseline Models (Mean / Median dummy, Linear Regression, Ridge, Lasso)
  - Task 2: Advanced Gradient Boosted Models (Random Forest, XGBoost, LightGBM, CatBoost)
  - Task 3: Comprehensive Sliced Diagnostics (Error by City & Price Bracket, Actual vs Predicted plot)
  - Task 4: Hyperparameter Tuning with Optuna & Experiment Tracking / Registry in MLflow
  - Task 5: Price Range & Confidence Engine (10th/90th percentile Quantile Regression + Overpriced / Fair / Underpriced verdicts)
  - Execution: [run_day2.py](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%202/run_day2.py) & [day2_property_valuation.ipynb](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%202/notebooks/day2_property_valuation.ipynb)

- 📁 [**Day 3: Lead Scoring Model (Classification) & Explainability**](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%203/README.md)
  - Task 1: Classification Models (Logistic Regression, Random Forest, XGBoost, LightGBM, CatBoost)
  - Task 2: Handling Imbalanced Data (No balancing, Class weights, SMOTE, Threshold tuning, Accuracy Paradox proof)
  - Task 3: Comprehensive Evaluation (Precision, Recall, F1, ROC/PR-AUC, Precision@Top-20%, Calibration, Cost curve)
  - Task 4: Lead Segmentation (🔥 Hot / 🌤 Warm / ❄️ Cold operational SLAs) & K-Means Customer Persona Discovery
  - Task 5: Explainability with SHAP (Global beeswarm, local waterfall), UrduLish Natural Language Generator & Algorithmic Fairness Audit
  - Execution: [run_day3.py](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%203/run_day3.py) & [day3_lead_scoring.ipynb](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%203/notebooks/day3_lead_scoring.ipynb)

- 📁 [**Day 4: Model Serving, AI Assistant & Integration**](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%204/README.md)
  - Task 1: FastAPI Model Serving (Point & Quantile Price, Lead Score, SHAP Explainability, Batch CSV Processing, Health & Metadata)
  - Task 2: LangGraph AI Assistant Copilot (5 Tools, UrduLish Dialogue Engine, Strict Zero-Hallucination Price Grounding)
  - Task 3: Streamlit Interactive Luxury Dashboard (Valuation Form, Priority Lead Inbox, SHAP Lab, Market EDA, Chat Panel)
  - Task 4: Week 7 Telephony & Voice Agent Integration (Post-Call Webhook, Automated VIP Hot Lead Email Dispatcher, Real-Time TTS Price Inquiry)
  - Task 5: Production Guardrails & Governance (OOD Bounding, Prompt Injection Defense Shield, Legal Disclaimers, SQLite Audit Logging)
  - Execution: [run_day4.py](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%204/run_day4.py) & [system_architecture.md](file:///c:/Users/PMYLS/Downloads/realestate-hub%20vapi%20and%20deepgram/Week%208/Day%204/architecture/system_architecture.md)

---

## 🚀 Daily Quickstarts

### Day 1 Execution
```bash
cd "Week 8\Day 1"
python run_day1.py
python -m src.notebook_runner
python tests/test_day1_pipeline.py
```

### Day 2 Execution
```bash
cd "Week 8\Day 2"
python run_day2.py
python -m src.notebook_runner
python tests/test_day2_valuation.py
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

### Day 3 Execution
```bash
cd "Week 8\Day 3"
python run_day3.py
python -m src.notebook_runner
python tests/test_day3_lead_scoring.py
```

### Day 4 Execution
```bash
cd "Week 8\Day 4"
python run_day4.py
uvicorn src.api:app --reload --port 8000
streamlit run dashboard/app.py
```
