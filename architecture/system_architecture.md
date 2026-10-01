# System Architecture: Day 5 LangGraph Voice Agent with Week 8 Machine Learning Integration

**Week 7 Day 5 + Week 8 Integration Specification**  
**Integration Scope:** Deepgram Nova-3 Urdu STT + Gemini Voice + Vapi Gateway + LangGraph StateGraph (10 Nodes) + Week 8 Machine Learning Valuation & Lead Scoring Models.

---

## 🏗️ End-to-End System Architecture Diagram

```mermaid
flowchart TB
    subgraph ClientLayer ["1. Client & Inbound Touchpoints"]
        Caller["📞 Inbound Telephony Caller (WebRTC / PSTN Phone)"]
        WebUser["💻 Web Client (RealEstate Hub React Portal)"]
        SalesAgent["🧑‍💼 Real Estate Sales Consultant"]
    end

    subgraph VoiceGateway ["2. Vapi Voice Infrastructure"]
        VapiGate["🎙️ Vapi Cloud Voice Gateway"]
        DeepgramNova["🗣️ Deepgram Nova-3 (Urdu Speech-to-Text)"]
        VapiTTS["🔊 Vapi Text-to-Speech (UrduLish Voice Engine)"]
    end

    subgraph LangGraphOrchestrator ["3. Day 5 LangGraph Orchestration Layer (vapi_server.py)"]
        StateGraph["🔄 LangGraph StateGraph Engine"]
        IntentNode["🔀 Intent Detection Node\n(Entities: Marla, Society, City, Budget, Booking)"]
        
        subgraph GraphNodes ["Agent State Nodes"]
            GreetingNode["👋 Greeting Node\n('Assalam-o-Alaikum! RealEstate Hub...')"]
            RecNode["🏡 Property Recommendation Node"]
            BookNode["📅 Booking Node (Google Calendar & CRM)"]
            ReschedNode["🔄 Rescheduling Node"]
            CancelNode["❌ Cancellation Node"]
            RAGNode["📚 RAG Knowledge Node (ChromaDB)"]
            EmailNode["✉️ Email Notification Node"]
            ValuationNode["📈 ML Valuation Node\n('Mera ghar kitne ka bikega?')"]
            ClarifyNode["❓ Clarification Node (Zero Guesswork)"]
        end
    end

    subgraph MLServiceLayer ["4. Week 8 Machine Learning Serving Engines"]
        PriceValuationModel["💰 LightGBM Valuation Regressor (/predict/price)\n(R²=0.891, MAPE=5.4%)"]
        QuantileBounds["📊 Quantile Interval Models\n(10th & 90th Percentile Confidence Range)"]
        LeadScoringModel["🎯 LightGBM Lead Scoring Engine (/predict/lead-score)\n(ROC-AUC=0.912, SMOTE Balanced)"]
        PersonaClustering["👥 K-Means Customer Persona Engine (k=4)"]
        SHAPExplainers["🔍 SHAP TreeExplainer Local Attribution"]
    end

    subgraph TelephonyWebhook ["5. Post-Call Telephony Webhook & Automation"]
        PostCallWebhook["📲 Vapi Post-Call Webhook (/vapi/webhook)\n(Triggered after call completes)"]
        LeadEvaluator["⚖️ Call Feature Intake & Scoring Engine\n(Duration, Budget, Society, Visit Booked)"]
        VIPHotLeadAlert["🚨 VIP Hot Lead Email Dispatcher\n(15-Min Closer SLA Alert sent to Sales Employee)"]
    end

    subgraph StorageGovernance ["6. Persistence & Governance Layer"]
        PostgresDB[("🗄️ PostgreSQL / SQLite DB\n(Properties, CRM Leads, Appointments)")]
        ChromaKB[("📁 ChromaDB Vector Knowledge Base")]
        AuditLogs[("📝 SQLite Audit DB & JSONL Execution Traces")]
    end

    %% Voice Calling Sequence
    Caller <-->|Live Urdu Speech Audio| VapiGate
    VapiGate -->|Streaming Audio| DeepgramNova
    DeepgramNova -->|UrduLish Transcripts| VapiGate
    VapiGate <-->|OpenAI Custom LLM Protocol (/vapi/llm)| StateGraph

    %% Intent Routing
    StateGraph --> IntentNode
    IntentNode -->|Greeting| GreetingNode
    IntentNode -->|Recommendation| RecNode
    IntentNode -->|Booking| BookNode
    IntentNode -->|Rescheduling| ReschedNode
    IntentNode -->|Cancellation| CancelNode
    IntentNode -->|RAG Inquiry| RAGNode
    IntentNode -->|Email| EmailNode
    IntentNode -->|'Mera ghar kitne ka bikega?'| ValuationNode
    IntentNode -->|Missing Details| ClarifyNode

    %% Valuation Node Connection to ML
    ValuationNode -->|Inference Call| PriceValuationModel
    ValuationNode -->|Confidence Intervals| QuantileBounds
    PriceValuationModel -->|Formatted Price + Verdict| ValuationNode
    ValuationNode -->|UrduLish Speech Text| VapiTTS
    VapiTTS -->|Audio Stream| Caller

    %% Post Call Webhook Flow
    VapiGate -->|Post-Call Webhook (end-of-call-report)| PostCallWebhook
    PostCallWebhook --> LeadEvaluator
    LeadEvaluator --> LeadScoringModel
    LeadScoringModel --> PersonaClustering
    LeadScoringModel -->|Hot Lead Score >= 70%| VIPHotLeadAlert
    VIPHotLeadAlert -->|Direct High-Priority Alert| SalesAgent

    %% Storage & Governance
    RecNode <--> PostgresDB
    BookNode <--> PostgresDB
    RAGNode <--> ChromaKB
    StateGraph --> AuditLogs
```

---

## ⚡ Sequence Flow: "Mera ghar kitne ka bikega?"

```mermaid
sequenceDiagram
    autonumber
    actor Caller as 📞 Inbound Caller
    participant Vapi as 🎙️ Vapi Gateway
    participant Agent as 🔄 LangGraph Agent (vapi_server.py)
    participant ML_Val as 📈 ML Valuation Engine (/predict/price)
    
    Caller->>Vapi: "Assalam-o-Alaikum! Mera DHA Phase 6 mein 1 kanal ghar kitne ka bikega?"
    Vapi->>Agent: POST /vapi/llm/chat/completions (User Message)
    Agent->>Agent: IntentDetectionNode: Detects 'valuation', Area: 20 Marla, Society: DHA Phase 6
    Agent->>ML_Val: predict_property_price(city='Lahore', area_society='DHA Phase 6', area_marla=20.0)
    ML_Val-->>Agent: Predicted: PKR 8.39 Crore (Range: 5.28 - 10.16 Crore, Verdict: Strong Demand)
    Agent-->>Vapi: "Janab, model ke mutabiq aap ke DHA Phase 6 mein 1 Kanal ghar ki takhmeena fair value taqreeban 8.39 crore hai..."
    Vapi-->>Caller: Speaks UrduLish response via Vapi TTS
```

---

## ⚡ Sequence Flow: Post-Call Lead Scoring & Hot Lead Alert

```mermaid
sequenceDiagram
    autonumber
    participant Vapi as 🎙️ Vapi Telephony Gateway
    participant Webhook as 📲 /vapi/webhook (vapi_server.py)
    participant LeadML as 🎯 Lead Scoring Engine (/predict/lead-score)
    participant Mailer as 📧 SMTP Email Dispatcher
    actor SalesCloser as 🧑‍💼 Assigned Closer (closer.vip@realestatehub.pk)
    
    Note over Vapi,Webhook: Call concludes (Duration: 320s, Visit Booked: Yes, Budget: 6 Crore)
    Vapi->>Webhook: POST /vapi/webhook (end-of-call-report)
    Webhook->>LeadML: score_voice_call_lead(duration=320, budget=60M, visit='yes', calls=3)
    LeadML->>LeadML: LightGBM inference: Conversion Probability = 88% (Tier: HOT)
    LeadML-->>Webhook: Lead Tier: HOT, Persona: High Net-Worth Investor, SLA: 15-Minute Outreach
    Webhook->>Mailer: send_direct_contact_email(🚨 VIP Hot Lead Voice Call Alert)
    Mailer->>SalesCloser: Dispatches instant alert with caller details, SLA timer, and transcript
```
