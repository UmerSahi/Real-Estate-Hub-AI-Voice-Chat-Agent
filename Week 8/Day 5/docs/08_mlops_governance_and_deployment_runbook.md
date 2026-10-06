# 08. MLOps Governance & Deployment Runbook
**Document Code:** REH-DOC-08  
**Project:** Week 8 Capstone Platform: AI Property Valuation & Lead Scoring  
**Target Audience:** DevOps Engineers, MLOps Practitioners, Site Reliability Engineers  
**Status:** Production Deployment Runbook  

---

## 1. MLOps Lifecycle & Model Registry

All model artifacts are versioned, serialized, and tracked in our experiment registry:

```
[ Data Pipeline ] ──> [ Optuna Bayesian Tuning ] ──> [ MLflow Registry ]
                                                              │
                                      ┌───────────────────────┴───────────────────────┐
                                      ▼                                               ▼
                         CatBoost Valuation (v1.2.0)                     LightGBM Lead (v1.1.0)
                         • Artifact: best_valuation_model.joblib         • Artifact: best_lead_scoring_model.joblib
                         • Preprocessor: fitted_preprocessor.joblib      • Preprocessor: lead_preprocessor.joblib
                         • Quantiles: quantile_lower/upper.joblib        • Persona Scaler: persona_scaler.joblib
```

---

## 2. Production Guardrails & Governance

### 2.1 Out-of-Distribution (OOD) Bounding Engine
To protect models against irrational inputs, queries pass through strict boundary filters:
- `area_marla`: $0.5 \le \text{area} \le 100.0$ Marla.
- `bedrooms`: $0 \le \text{bedrooms} \le 15$.
- `bathrooms`: $0 \le \text{bathrooms} \le 15$.
- `city`: Restricted to `['Islamabad', 'Karachi', 'Lahore', 'Rawalpindi']`.
- `quoted_price_pkr`: $500,000 \le \text{price} \le 500,000,000$.

*If an OOD violation occurs, the API returns a structured HTTP 422 Unprocessable Entity error without invoking the model.*

### 2.2 Adversarial Prompt-Injection Defense Shield
Protects the LangGraph agent against malicious prompt tampering:
- Rejects patterns matching: `ignore previous instructions`, `system prompt override`, `set price to 1 rupee`, `pretend you are an unrestricted AI`, or `DROP TABLE`.
- Sanitizes user input before tokenization.

### 2.3 SQLite Audit DB Schema (`audit_logs.db`)
Every API call is recorded synchronously into SQLite and asynchronously into JSONL:

```sql
CREATE TABLE IF NOT EXISTS model_prediction_audits (
    audit_id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    model_version TEXT NOT NULL,
    client_ip TEXT,
    input_payload JSON NOT NULL,
    prediction_output JSON NOT NULL,
    latency_ms REAL NOT NULL,
    status_code INTEGER NOT NULL,
    guardrail_flags TEXT
);
```

---

## 3. Docker Containerization & Deployment

### 3.1 Multi-Stage Dockerfile Specification
```dockerfile
FROM python:3.12-slim-bookworm AS base

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl sqlite3 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000 8501
CMD ["uvicorn", "Week 8.Day 4.src.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 Cloudflare Tunneling & Live Deployment
For secure, zero-trust remote access to local or cloud instances:
```bash
# Start Cloudflare Tunnel
cloudflared.exe tunnel --url http://localhost:8000
```
This generates a secure public HTTPS endpoint (e.g. `https://realestate-api.trycloudflare.com`) accessible by Vapi telephony servers.

---

## 4. Continuous Monitoring & Retraining Triggers

### 4.1 Data & Concept Drift Monitoring
We track statistical drift between the training baseline and live inference streams:
1. **Numerical Drift (Area, Price, Duration):** Kolmogorov-Smirnov (KS) test evaluated weekly ($p < 0.05$ triggers an alert).
2. **Categorical Drift (Societies, Cities):** Population Stability Index (PSI) calculated on a rolling 14-day window ($\text{PSI} > 0.2$ flags severe distribution shift).
3. **Concept Drift:** Tracking the rolling discrepancy between model predicted price and finalized broker transaction price.

### 4.2 Automated Retraining Pipeline
When drift thresholds trigger:
1. New transaction records are queried from CRM storage.
2. The data cleaning and domain feature engineering pipeline executes automatically.
3. Candidate models train in MLflow.
4. If candidate MAPE beats champion by $\ge 0.5\%$, the candidate is automatically tagged as production champion.
