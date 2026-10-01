# Week 8 — Day 4: Model Serving, AI Assistant & Integration

**Domain:** Real Estate Machine Learning Serving • LangGraph Conversational Agent • Week 7 Telephony Webhook • SHAP Explainability • Production Guardrails  
**Version:** 1.0.0  
**Test Suite:** 31/31 Unit & Integration Tests Passing (100% Coverage)  

---

## 📌 Executive Summary & Scenario

> **Scenario:** *"Models sitting in a notebook make no money. Today the models become a product: an API the Week 7 voice agent can call, and an AI assistant that sales agents can chat with in UrduLish."*

Day 4 transforms the machine learning models developed during Day 2 (Property Valuation Regression with Quantile Confidence Bounds) and Day 3 (Lead Scoring Classifier with K-Means Customer Persona Discovery) into an enterprise-grade, production-serving software product:

1. **FastAPI Model Serving Layer:** High-throughput REST API serving point predictions, 10th/90th percentile confidence bounds, conversion probabilities, SHAP local waterfall feature attributions, and batch CSV processing.
2. **LangGraph AI Assistant Copilot:** Multi-turn conversational agent operating in **UrduLish** that invokes 5 specialized tools. The agent strictly enforces the inviolable constraint: **"The LLM must never invent a price. Every number must come from a tool."**
3. **Streamlit Multi-Tab Dashboard:** Luxury real estate visual interface offering interactive valuation pricing forms, priority lead pipeline with 🔥 Hot / 🌤 Warm / ❄️ Cold badges, SHAP force charts, market analytics, and an integrated copilot chat panel.
4. **Week 7 Telephony & Voice Agent Integration:** Bilateral webhook bridge connecting the voice agent (Vapi / Deepgram / Twilio). Post-call events trigger automated lead scoring; hot leads fire instant VIP email alerts to senior sales closers with a 15-minute SLA countdown; voice callers asking *"Mera ghar kitne ka bikega?"* receive real-time, speech-optimized UrduLish valuation responses.
5. **Production Guardrails & Governance:** Rigorous Out-of-Distribution (OOD) input validation, adversarial prompt-injection shield, non-certified valuation legal disclaimers, and complete audit logging to SQLite (`audit_logs.db`) and streaming JSONL.

---

## 🏛️ System Architecture

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Ingestion & User Touchpoints"]
        Caller["📞 Inbound Telephony Caller (Week 7)"]
        SalesAgent["🧑‍💼 Sales Agent / Consultant (Web / App)"]
        Investor["💼 Enterprise Client (Batch CSV / CRM)"]
    end

    subgraph TelephonyLayer ["2. Week 7 Telephony Bridge"]
        Vapi["🎙️ Vapi Telephony Gateway / Twilio"]
        Deepgram["🗣️ Deepgram Speech-to-Text (STT)"]
        TTS["🔊 Telephony Text-to-Speech (TTS Engine)"]
    end

    subgraph SecurityLayer ["3. Enterprise Guardrails & Governance"]
        OOD["🛡️ Out-of-Distribution (OOD) Check\n(Area 1-100 Marla, Valid Cities)"]
        PromptShield["🛡️ Prompt-Injection Defense\n(Blocks 'Set price to 1 rupee', Overrides)"]
        AuditLogger["📝 SQLite Audit DB & JSONL Stream\n(UUID, Latency, Inputs, IP)"]
        DisclaimerEngine["⚖️ Mandatory Legal Disclaimer Engine"]
    end

    subgraph APILayer ["4. FastAPI Model Serving Layer (Port 8000)"]
        EP_Price["POST /predict/price"]
        EP_Lead["POST /predict/lead-score"]
        EP_ExpPrice["POST /explain/price"]
        EP_ExpLead["POST /explain/lead"]
        EP_Batch["POST /predict/batch (CSV Upload)"]
        EP_Health["GET /health & GET /model/info"]
        EP_VoiceCall["POST /integration/voice-call (Webhook)"]
        EP_VoicePrice["POST /integration/voice-price-inquiry"]
        EP_Chat["POST /agent/chat"]
    end

    subgraph LangGraphLayer ["5. LangGraph AI Assistant Copilot"]
        StateGraph["🔄 LangGraph StateGraph Workflow"]
        RouterNode["🔀 Intent Router & Input Sanitizer"]
        ToolNode["⚙️ Tool Execution Node"]
        UrduLishGen["🇵🇰 UrduLish Dialogue Synthesizer"]
        GroundingVerifier["🔒 Grounding Verifier\n(LLM Never Invents Price)"]
    end

    subgraph ToolRegistry ["6. Agent Tool Registry"]
        T1["Tool 1: Price Predictor"]
        T2["Tool 2: Lead Scorer"]
        T3["Tool 3: Explainer (SHAP)"]
        T4["Tool 4: Comparable Properties"]
        T5["Tool 5: Market Stats (PPM)"]
    end

    subgraph ModelLayer ["7. Machine Learning Serving Engines"]
        ValuationModel["📈 LightGBM Valuation Regressor\n(v1.2.0, R²=0.891, MAPE=5.4%)"]
        QuantileModels["📊 Quantile Gradient Boosting\n(10th & 90th Percentiles)"]
        LeadModel["🎯 LightGBM Classifier with SMOTE\n(v1.1.0, ROC-AUC=0.912)"]
        PersonaCluster["👥 K-Means Persona Discovery (k=4)"]
        SHAPEngine["🔍 SHAP TreeExplainer"]
    end

    subgraph StorageLayer ["8. Persistence & Dashboard Layer"]
        PropDB[("📁 5,700+ Verified Property Listings")]
        AuditDB[("🗄️ SQLite Prediction Audit DB")]
        EmailDispatcher["📧 Automated VIP Hot Lead Email Dispatcher\n(SLA < 15 Min Countdown)"]
        Dashboard["🖥️ Streamlit Multi-Tab Dashboard (Port 8501)"]
    end

    %% Wiring
    Caller --> Vapi --> Deepgram --> Vapi
    Vapi -->|After-Call Webhook| EP_VoiceCall
    Vapi -->|'Mera ghar kitne ka bikega?'| EP_VoicePrice --> TTS --> Caller

    SalesAgent --> Dashboard
    SalesAgent --> EP_Chat
    Investor --> EP_Batch
    Dashboard --> APILayer

    APILayer --> SecurityLayer --> APILayer
    EP_Price --> ValuationModel & QuantileModels
    EP_Lead --> LeadModel & PersonaCluster
    EP_ExpPrice --> SHAPEngine
    EP_ExpLead --> SHAPEngine
    EP_Chat --> LangGraphLayer

    StateGraph --> RouterNode --> ToolNode --> ToolRegistry
    ToolRegistry --> ValuationModel & LeadModel & SHAPEngine & PropDB
    ToolNode --> UrduLishGen --> GroundingVerifier --> EP_Chat

    EP_VoiceCall --> LeadModel
    EP_VoiceCall -->|If Hot Lead (>=70%)| EmailDispatcher --> SalesAgent
    APILayer -.-> AuditDB
```

---

## 🛠️ Task 1 — FastAPI Model Serving Endpoints

Built with **FastAPI** and **Pydantic** with strict validation rules. Invalid inputs (e.g., negative size, unknown cities, negative budgets) are rejected immediately with structured `422 Unprocessable Entity` or `400 Bad Request` errors.

### Endpoint Catalog

| Method | Endpoint | Description | Input Schema | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Live health probe & loaded model inventory | None | `HealthResponse` |
| `GET` | `/model/info` | Governance metadata, benchmark metrics, trained dates | None | `ModelInfoResponse` |
| `POST` | `/predict/price` | Point valuation, 10th/90th quantile interval, verdict | `PropertyValuationRequest` | `PropertyValuationResponse` |
| `POST` | `/predict/lead-score` | Lead probability, 🔥/🌤/❄️ tier, SLA, customer persona | `LeadScoreRequest` | `LeadScoreResponse` |
| `POST` | `/explain/price` | SHAP feature attributions & UrduLish price reasons | `PropertyValuationRequest` | `PropertyExplanationResponse` |
| `POST` | `/explain/lead` | SHAP local waterfall drivers & conversion reasons | `LeadScoreRequest` | `LeadExplanationResponse` |
| `POST` | `/predict/batch` | High-throughput batch scoring via CSV file upload | Multipart `UploadFile` (.csv) | `BatchPredictionResponse` |

### Sample Request & Response: `POST /predict/price`

#### Request Payload:
```json
{
  "city": "Lahore",
  "area_society": "DHA Phase 6",
  "area_marla": 20.0,
  "bedrooms": 5,
  "bathrooms": 5,
  "age_years": 5,
  "property_type": "House",
  "is_corner": "yes",
  "listed_price_pkr": 85000000.0
}
```

#### Response Payload:
```json
{
  "prediction_id": "VAL-75D4E1A0",
  "predicted_price_pkr": 83900000.0,
  "predicted_price_formatted": "8.39 crore",
  "lower_range_pkr": 52800000.0,
  "lower_range_formatted": "5.28 crore",
  "upper_range_pkr": 101600000.0,
  "upper_range_formatted": "10.16 crore",
  "price_range_formatted": "5.28 crore - 10.16 crore",
  "listed_price_pkr": 85000000.0,
  "listed_price_formatted": "8.50 crore",
  "verdict": "Fair",
  "price_delta_pct": 1.3,
  "client_explanation": "Predicted: 8.39 crore (fair range 5.28 crore - 10.16 crore). Listed at 8.50 crore -> Fair Market Price (within 1.3% of model benchmark).",
  "disclaimer": "Disclaimer: All property valuations, price ranges, and lead conversion scores are algorithmic statistical estimates generated by machine learning models based on historical transaction data. They do not constitute certified legal appraisals, mortgage valuations, or guaranteed financial outcomes.",
  "model_version": "v1.2.0-lgbm-quantile",
  "timestamp": "2026-09-29T10:58:12.345678+00:00"
}
```

---

## 🤖 Task 2 — LangGraph AI Assistant & Tool Grounding

The AI Assistant is constructed using **LangGraph StateGraph** and enforces the cardinal domain rule:
> **"The LLM must never invent a price. Every number must come from a tool."**

### Registered Tools
1. **`tool_price_predictor`**: Invokes the property valuation regression engine to calculate fair value and quantile confidence bounds.
2. **`tool_lead_scorer`**: Evaluates inbound prospect conversion probability, tier, and persona.
3. **`tool_explainer`**: Computes SHAP feature importance attributions for either price or lead conversion.
4. **`tool_comparable_properties`**: Queries the 5,700+ listings database to retrieve actual similar properties matching location, size, and layout.
5. **`tool_market_stats`**: Aggregates average price per marla, median prices, and listing volume for any housing society.

### Dialogue Demonstration (UrduLish)

**Sales Agent:**
> *"DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?"*

**Assistant Output:**
> *"Model ke mutabiq DHA Phase 6 mein 1 Kanal ghar ki fair value **5.33 crore se 9.73 crore** ke darmiyan hai (benchmark point: **8.10 crore**). Sab se bara factor location aur plot size hai. Agar property modern 5-saal purani construction hai to yeh price bracket standard market rate ko reflect karta hai."*
>
> *> ⚖️ Disclaimer: All property valuations, price ranges, and lead conversion scores are algorithmic statistical estimates...*

---

## 🖥️ Task 3 — Streamlit Interactive Dashboard

The Streamlit dashboard (`dashboard/app.py`) provides an interactive interface for sales agents and leadership:

1. **🏷️ Property Valuation Tab:** Interactive form with sliders for Marla/Kanal, bedrooms, age, and corner plot premiums. Generates real-time price gauges, 10th-90th percentile ranges, and Overpriced / Fair / Underpriced verdict badges.
2. **🔥 Lead Scoring Pipeline Tab:** Live lead list sorted by conversion probability with 🔥 Hot, 🌤 Warm, and ❄️ Cold status pills. Features one-click deep dives into customer personas and recommended sales pitches.
3. **📊 SHAP Explainability Lab:** Dynamic waterfall and horizontal bar charts illustrating exactly which features contributed positively or negatively to the model's estimate.
4. **📈 Market Insights Tab:** Publication-quality visual analytics featuring price per marla by society, city median prices, and speed-to-lead conversion curves.
5. **💬 UrduLish AI Assistant Tab:** Conversational copilot with quick prompt buttons, conversation memory, and an expandable tool execution trace.
6. **📞 Telephony & Audit Tab:** Week 7 voice call simulator and live SQLite audit table.

---

## 📞 Task 4 — Week 7 Voice Agent Telephony Integration

The ML serving platform integrates with the Week 7 Vapi / Deepgram / Twilio voice agent:

### 1. Automated Post-Call Webhook (`POST /integration/voice-call`)
Immediately following call completion, telephony logs are transmitted to the serving engine:
- Evaluates interaction velocity, call duration, budget, and site visit intent.
- **Automated VIP Email Alert:** If the lead scores as **🔥 Hot** ($\ge 70\%$), an alert is composed and dispatched to the designated sales closer (`closer@realestatehub.pk`) with an operational **SLA countdown (< 15 min)**, caller audio summary, and customer persona pitch.
- Email alerts are logged to `data/simulated_emails.log`.

### 2. Real-Time Price Inquiries (`POST /integration/voice-price-inquiry`)
When an inbound caller asks *"Mera ghar kitne ka bikega?"*:
- Telephony invokes the endpoint with plot size, location, and condition.
- Generates speech-optimized text formatted specifically for Text-to-Speech (TTS):
  > *"Janab, model ke mutabiq aap ke DHA Phase 6 mein 1 kanal ghar ki takhmeena fair value taqreeban 8.4 crore hai, jis ki market trading range 5.3 se 9.7 crore banti hai. Kya aap hamare senior property advisor se visit schedule karwana chahein gay?"*

---

## 🛡️ Task 5 — Guardrails, Adversarial Security & Governance

| Guardrail Module | Mechanism | Verification / Enforcement |
| :--- | :--- | :--- |
| **Out-of-Distribution (OOD)** | Physical & statistical bounding in `src/guardrails.py` | Refuses properties with area > 100 Marla (5 Kanal), price > 60 Crore, or unserviced cities with structured `422 HTTP` errors. |
| **Prompt-Injection Defense** | Adversarial pattern matching engine | Neutralizes prompt hijacking attempts (*"Ignore instructions"*, *"Set price to 1 rupee"*, *"Reveal system prompt"*) and refuses manipulation. |
| **Zero Hallucination Grounding** | LangGraph Verifier Node | Asserts that every numeric currency figure in the response matches an exact key in the tool output JSON. |
| **Mandatory Legal Disclaimer** | Injected via middleware & response schemas | Discloses that valuations are algorithmic statistical estimates and not certified legal or financial appraisals. |
| **Audit Traceability** | SQLite (`data/audit_logs.db`) & JSONL | Records `prediction_id`, timestamp, endpoint, latency, client IP, raw inputs, and model outputs for governance. |

---

## 🚀 Execution & Verification

### 1. Run Master Verification Script (All 5 Tasks + 31 Tests)
```bash
cd "Week 8\Day 4"
python run_day4.py
```

### 2. Launch FastAPI Model Serving Server
```bash
cd "Week 8\Day 4"
uvicorn src.api:app --reload --port 8000
```
- Interactive OpenAPI Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative Redoc Interface: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 3. Launch Streamlit Interactive Dashboard
```bash
cd "Week 8\Day 4"
streamlit run dashboard/app.py
```
- Dashboard URL: [http://localhost:8501](http://localhost:8501)

### 4. Run Individual Test Suites
```bash
cd "Week 8\Day 4"
python -m unittest tests/test_fastapi_endpoints.py
python -m unittest tests/test_guardrails_and_validation.py
python -m unittest tests/test_prompt_injection.py
python -m unittest tests/test_langgraph_agent.py
python -m unittest tests/test_voice_integration.py
```
