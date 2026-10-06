# 09. Stakeholder FAQ & Operational Troubleshooting
**Document Code:** REH-DOC-09  
**Project:** Week 8 Capstone Platform: AI Property Valuation & Lead Scoring  
**Target Audience:** Frontline Brokers, Technical Support, Operations Leads  
**Status:** Operational Runbook & Knowledge Base  

---

## 1. Frequently Asked Questions (FAQ)

### 1.1 Real Estate Broker & Sales Team FAQs

#### Q1: "Why does the valuation model give a price range instead of a single exact number?"
**A:** Real estate transactions inherently vary due to subjective factors such as interior woodwork, Italian fittings, tile quality, and seller motivation. Providing a range (10th to 90th percentile bounds, e.g. 2.15 to 2.55 Crore) gives the broker an honest negotiation envelope with 80% empirical confidence, preventing premature deal collapse.

#### Q2: "What should an agent do if a property is flagged as 'OVERPRICED'?"
**A:** The agent should use the diagnostic report to counsel the seller gently: *"Sir, hamara data-driven model indicate kar raha hai ke similar DHA properties 2.4 Crore pe close ho rahi hain jabke aap 2.8 Crore demand kar rahe hain. Is price pe listing 180 din tak stagnate ho sakti hai."* This preserves agency credibility.

#### Q3: "What happens if a lead is marked as 'HOT' but the client turns out to be unprepared?"
**A:** Even top models have a false-positive rate (~28% under Top-20% selection). The sales closer should log the call outcome in the CRM with the specific disqualifier (e.g., *"Insufficient liquidity"*). This data automatically flows into next week's retraining pipeline.

---

### 1.2 Executive & Commercial Leadership FAQs

#### Q4: "How does this platform justify its technology investment?"
**A:** For a brokerage handling 1,000 leads per month, the platform increases closed deals from 57 to 142 per month by prioritizing the highest-converting 20% of leads. This generates over **PKR 3.86 Crore in incremental annual commission**, delivering over **15x ROI** on annual infrastructure costs.

#### Q5: "How does the system ensure compliance with real estate regulatory bodies?"
**A:** Every automated quotation carries our mandatory disclaimer stating that the figure is a statistical algorithmic estimate and does not replace a certified physical bank appraisal. Furthermore, all properties over 7.0 Crore PKR trigger a mandatory human appraiser review before quotation.

---

### 1.3 Technical & Data Science FAQs

#### Q6: "Why was CatBoost chosen over Deep Neural Networks?"
**A:** Tabular real estate data with heterogeneous numerical and high-cardinality categorical features (like society names and unit types) is proven in academic benchmarks to be handled superiorly by Gradient Boosted Decision Trees compared to Neural Networks. CatBoost natively handles categorical target encoding without data leakage, trains in under 8 seconds, and achieves an R² of 0.9860.

#### Q7: "How is data leakage prevented during feature engineering?"
**A:** All transformers (encoders, scalers, imputers) are encapsulated inside scikit-learn pipelines fitted strictly on the 70% training split. Derived metrics that incorporate the target variable (such as `price_per_marla`) are strictly excluded from the regression feature matrix.

---

## 2. Operational Incident Troubleshooting Guide

| Incident Code | Symptom | Probable Cause | Immediate Remediation Action |
| :--- | :--- | :--- | :--- |
| **ERR-OOD-422** | API returns `HTTP 422: Area out of bounds` | User entered area > 100 Marla or < 0.5 Marla | Verify unit conversion (did user enter square feet as Marla?). Advise user to enter valid dimensions. |
| **ERR-LAT-504** | Inference latency exceeds 1,500ms | Heavy concurrent batch CSV upload competing for CPU | Check server thread pool; restart Uvicorn worker process: `pkill -HUP uvicorn`. |
| **ERR-GUARD-403** | Copilot rejects query: `Security policy violation` | Query triggered prompt injection defense rules | Review prompt in audit logs. If false positive, adjust regex pattern in `guardrails.py`. |
| **ERR-DB-LOCK** | SQLite `OperationalError: database is locked` | High write concurrency on `audit_logs.db` | Verify SQLite WAL mode is enabled: `PRAGMA journal_mode=WAL;`. |
| **ERR-VOICE-DISP** | VIP Email Alert failed to deliver | SMTP credentials invalid or rate limited | Check `simulated_emails.log` fallback; verify environment variables `SMTP_USER` and `SMTP_PASSWORD`. |

---

## 3. Disaster Recovery & Failover Checklist

1. **Service Degraded:** If the machine learning service fails, the API gracefully degrades to serving cached median prices by society tier.
2. **Audit DB Recovery:** The SQLite audit database is backed up hourly via automated snapshots to S3/Cloud storage.
3. **Rollback Policy:** In the event of model regression, reverting to the previous model artifact in MLflow takes under 60 seconds by updating the symlink in `models/best_valuation_model.joblib`.
