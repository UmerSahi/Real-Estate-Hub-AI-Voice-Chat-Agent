"""Task 1, 4 & 5: Production FastAPI Model Serving Application.
Implements:
- POST /predict/price
- POST /predict/lead-score
- POST /explain/price
- POST /explain/lead
- POST /predict/batch (CSV upload & processing)
- GET /health
- GET /model/info
- POST /integration/voice-call (Week 7 Telephony Webhook)
- POST /integration/voice-price-inquiry (Telephony real-time TTS price lookup)
- POST /agent/chat (LangGraph UrduLish Copilot)
- GET /audit/logs
"""
from __future__ import annotations

import base64
import io
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

from src.config import (
    API_VERSION,
    LEAD_METRICS,
    LEAD_MODEL_VERSION,
    LEAD_TRAINED_DATE,
    LEGAL_DISCLAIMER,
    OOD_LIMITS,
    VALUATION_METRICS,
    VALUATION_MODEL_VERSION,
    VALUATION_TRAINED_DATE,
    VALID_CITIES,
    VALID_PROPERTY_TYPES,
)
from src.database_service import db_service
from src.guardrails import (
    OutOfDistributionError,
    audit_logger,
    validate_lead_ood,
    validate_property_ood,
)
from src.langgraph_agent import ai_assistant
from src.lead_scoring_service import lead_scoring_service
from src.schemas import (
    AgentChatRequest,
    AgentChatResponse,
    BatchPredictionResponse,
    HealthResponse,
    LeadExplanationResponse,
    LeadScoreRequest,
    LeadScoreResponse,
    ModelInfoResponse,
    PropertyExplanationResponse,
    PropertyValuationRequest,
    PropertyValuationResponse,
    VoiceCallWebhookPayload,
    VoiceCallWebhookResponse,
    VoicePriceInquiryRequest,
    VoicePriceInquiryResponse,
)
from src.valuation_service import valuation_service
from src.voice_integration import voice_service

# Initialize FastAPI Application
app = FastAPI(
    title="RealEstate-Hub AI Model Serving & Voice Integration API",
    description=(
        "Production-grade ML serving API powering automated property valuation, "
        "lead conversion scoring, explainable AI (SHAP), Week 7 telephony integration, "
        "and UrduLish LangGraph agent copilot."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Custom Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation failures with clean, readable messages."""
    error_details = []
    for err in exc.errors():
        field_name = " -> ".join([str(loc) for loc in err["loc"] if loc != "body"])
        error_details.append(
            {
                "field": field_name,
                "message": err["msg"],
                "type": err["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "validation_error",
            "message": "Input data failed schema validation constraints.",
            "errors": error_details,
            "disclaimer": LEGAL_DISCLAIMER,
        },
    )


@app.exception_handler(OutOfDistributionError)
async def ood_exception_handler(request: Request, exc: OutOfDistributionError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "out_of_distribution_error",
            "message": str(exc),
            "disclaimer": LEGAL_DISCLAIMER,
        },
    )


# ============================================================================
# Core Health & Metadata Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System Health"])
def get_health_status():
    """Verify operational health and loaded model artifacts."""
    return HealthResponse(
        status="healthy",
        service="RealEstate-Hub AI Model Serving Engine",
        version=API_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        models_loaded={
            "valuation_model": valuation_service.model is not None,
            "lead_scoring_model": lead_scoring_service.model is not None,
            "quantile_lower_regressor": valuation_service.lower_model is not None,
            "quantile_upper_regressor": valuation_service.upper_model is not None,
            "valuation_shap_explainer": valuation_service.explainer is not None,
            "lead_shap_explainer": lead_scoring_service.explainer is not None,
        },
        database_connected=len(db_service.df) > 0,
    )


@app.get("/model/info", response_model=ModelInfoResponse, tags=["Model Governance"])
def get_model_info():
    """Retrieve production model versioning, benchmark metrics, and guardrail limits."""
    return ModelInfoResponse(
        api_version=API_VERSION,
        valuation_model={
            "model_name": "Property Valuation Regression Engine",
            "model_version": VALUATION_MODEL_VERSION,
            "trained_date": VALUATION_TRAINED_DATE,
            "algorithm": "Gradient Boosting / LightGBM Regressor + Quantile Estimators",
            "benchmark_metrics": VALUATION_METRICS,
            "coverage_cities": VALID_CITIES,
            "supported_property_types": VALID_PROPERTY_TYPES,
        },
        lead_scoring_model={
            "model_name": "Lead Conversion Scoring Classifier",
            "model_version": LEAD_MODEL_VERSION,
            "trained_date": LEAD_TRAINED_DATE,
            "algorithm": "LightGBM Classifier with SMOTE & Class Weighting",
            "benchmark_metrics": LEAD_METRICS,
            "operational_tiers": {
                "hot_threshold": 0.70,
                "warm_threshold": 0.35,
                "cold_threshold": 0.00,
            },
            "persona_discovery": "K-Means Clustering (k=4)",
        },
        system_guardrails={
            "out_of_distribution_limits": OOD_LIMITS,
            "adversarial_prompt_defense_enabled": True,
            "audit_logging_enabled": True,
        },
        disclaimer=LEGAL_DISCLAIMER,
    )


# ============================================================================
# Task 1: Valuation Endpoints
# ============================================================================

@app.post("/predict/price", response_model=PropertyValuationResponse, tags=["Property Valuation"])
def predict_property_price(request_data: PropertyValuationRequest, request: Request):
    """Predict fair market price, confidence intervals, and commercial verdict."""
    start_time = time.time()
    payload = request_data.model_dump()

    # OOD Guardrail
    is_valid, ood_msg = validate_property_ood(payload)
    if not is_valid:
        audit_logger.log_prediction(
            prediction_id=f"VAL-OOD-{int(start_time)}",
            endpoint="/predict/price",
            inputs=payload,
            output={"error": ood_msg},
            model_version=VALUATION_MODEL_VERSION,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            client_ip=request.client.host if request.client else "127.0.0.1",
            is_ood=True,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ood_msg,
        )

    # Inference
    result = valuation_service.predict_valuation(payload)
    latency = round((time.time() - start_time) * 1000, 2)

    # Audit Log
    audit_logger.log_prediction(
        prediction_id=result["prediction_id"],
        endpoint="/predict/price",
        inputs=payload,
        output=result,
        model_version=VALUATION_MODEL_VERSION,
        latency_ms=latency,
        client_ip=request.client.host if request.client else "127.0.0.1",
        is_ood=False,
    )

    return PropertyValuationResponse(**result)


@app.post("/explain/price", response_model=PropertyExplanationResponse, tags=["Explainability (SHAP)"])
def explain_property_price(request_data: PropertyValuationRequest):
    """Compute local SHAP feature attributions and UrduLish natural language driver reasons."""
    payload = request_data.model_dump()
    is_valid, ood_msg = validate_property_ood(payload)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ood_msg)

    result = valuation_service.explain_valuation(payload)
    return PropertyExplanationResponse(**result)


# ============================================================================
# Task 1: Lead Scoring Endpoints
# ============================================================================

@app.post("/predict/lead-score", response_model=LeadScoreResponse, tags=["Lead Scoring"])
def predict_lead_score(request_data: LeadScoreRequest, request: Request):
    """Score sales prospect conversion probability, assign SLA protocol, and discover persona."""
    start_time = time.time()
    payload = request_data.model_dump()

    # OOD Guardrail
    is_valid, ood_msg = validate_lead_ood(payload)
    if not is_valid:
        audit_logger.log_prediction(
            prediction_id=f"LEAD-OOD-{int(start_time)}",
            endpoint="/predict/lead-score",
            inputs=payload,
            output={"error": ood_msg},
            model_version=LEAD_MODEL_VERSION,
            latency_ms=round((time.time() - start_time) * 1000, 2),
            client_ip=request.client.host if request.client else "127.0.0.1",
            is_ood=True,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ood_msg,
        )

    # Inference
    result = lead_scoring_service.score_lead(payload)
    latency = round((time.time() - start_time) * 1000, 2)

    # Audit Log
    audit_logger.log_prediction(
        prediction_id=result["prediction_id"],
        endpoint="/predict/lead-score",
        inputs=payload,
        output=result,
        model_version=LEAD_MODEL_VERSION,
        latency_ms=latency,
        client_ip=request.client.host if request.client else "127.0.0.1",
        is_ood=False,
    )

    return LeadScoreResponse(**result)


@app.post("/explain/lead", response_model=LeadExplanationResponse, tags=["Explainability (SHAP)"])
def explain_lead_conversion(request_data: LeadScoreRequest):
    """Compute local SHAP attributions explaining why a lead was categorized as Hot, Warm, or Cold."""
    payload = request_data.model_dump()
    is_valid, ood_msg = validate_lead_ood(payload)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=ood_msg)

    res = lead_scoring_service.score_lead(payload)
    return LeadExplanationResponse(
        prediction_id=res["prediction_id"],
        lead_id=res["lead_id"],
        conversion_score_pct=res["conversion_score_pct"],
        tier=res["tier"],
        feature_attributions=res.get("feature_attributions", []),
        top_positive_drivers=res.get("top_positive_drivers", []),
        top_negative_drivers=res.get("top_negative_drivers", []),
        urdulish_explanation=res["urdulish_explanation"],
        english_explanation=res["english_explanation"],
        disclaimer=LEGAL_DISCLAIMER,
        timestamp=res["timestamp"],
    )


# ============================================================================
# Task 1: Batch Prediction Endpoint (CSV Upload)
# ============================================================================

@app.post("/predict/batch", response_model=BatchPredictionResponse, tags=["Batch Processing"])
async def predict_batch_csv(file: UploadFile = File(...)):
    """Upload a CSV file containing property listings or leads for high-throughput batch scoring."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Uploaded file must have a .csv extension.",
        )

    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to parse CSV: {e}")

    if df.empty:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty.")

    batch_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    # Auto-detect batch type
    cols = [c.lower() for c in df.columns]
    is_property_batch = any(c in cols for c in ["area_marla", "bedrooms", "property_type"])
    batch_type = "properties" if is_property_batch else "leads"

    predictions = []
    errors = []
    enriched_rows = []

    if batch_type == "properties":
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            try:
                # Default fallbacks
                if "city" not in row_dict or pd.isna(row_dict["city"]):
                    row_dict["city"] = "Lahore"
                if "area_society" not in row_dict or pd.isna(row_dict["area_society"]):
                    row_dict["area_society"] = "DHA Phase 6"
                if "area_marla" not in row_dict or pd.isna(row_dict["area_marla"]):
                    row_dict["area_marla"] = 10.0

                req = PropertyValuationRequest(**row_dict)
                pred_out = valuation_service.predict_valuation(req.model_dump())
                predictions.append(pred_out)

                enriched = {**row_dict, **pred_out}
                enriched_rows.append(enriched)
            except Exception as e:
                errors.append({"row_index": idx, "error": str(e), "data": row_dict})

        summary_stats = {
            "batch_type": "properties",
            "total_processed": len(predictions),
            "average_predicted_price_pkr": (
                float(pd.Series([p["predicted_price_pkr"] for p in predictions]).mean())
                if predictions
                else 0.0
            ),
            "verdict_distribution": (
                pd.Series([p["verdict"] for p in predictions]).value_counts().to_dict()
                if predictions
                else {}
            ),
        }

    else:
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            try:
                if "preferred_city" not in row_dict or pd.isna(row_dict["preferred_city"]):
                    row_dict["preferred_city"] = "Lahore"
                if "preferred_society" not in row_dict or pd.isna(row_dict["preferred_society"]):
                    row_dict["preferred_society"] = "DHA Phase 6"
                if "budget_pkr" not in row_dict or pd.isna(row_dict["budget_pkr"]):
                    row_dict["budget_pkr"] = 25_000_000.0
                if "lead_source" not in row_dict or pd.isna(row_dict["lead_source"]):
                    row_dict["lead_source"] = "call"

                req = LeadScoreRequest(**row_dict)
                score_out = lead_scoring_service.score_lead(req.model_dump())
                predictions.append(score_out)

                enriched = {**row_dict, **score_out}
                enriched_rows.append(enriched)
            except Exception as e:
                errors.append({"row_index": idx, "error": str(e), "data": row_dict})

        summary_stats = {
            "batch_type": "leads",
            "total_processed": len(predictions),
            "average_conversion_score_pct": (
                float(pd.Series([p["conversion_score_pct"] for p in predictions]).mean())
                if predictions
                else 0.0
            ),
            "tier_distribution": (
                pd.Series([p["tier"] for p in predictions]).value_counts().to_dict()
                if predictions
                else {}
            ),
        }

    # Generate enriched CSV download
    csv_b64 = None
    if enriched_rows:
        df_out = pd.DataFrame(enriched_rows)
        # Drop large nested objects for clean CSV export
        for drop_col in ["feature_attributions", "top_positive_drivers", "top_negative_drivers"]:
            if drop_col in df_out.columns:
                df_out = df_out.drop(columns=[drop_col])
        csv_buffer = io.StringIO()
        df_out.to_csv(csv_buffer, index=False)
        csv_b64 = base64.b64encode(csv_buffer.getvalue().encode("utf-8")).decode("utf-8")

    return BatchPredictionResponse(
        batch_id=batch_id,
        batch_type=batch_type,
        total_rows=len(df),
        successful_rows=len(predictions),
        failed_rows=len(errors),
        summary_stats=summary_stats,
        predictions=predictions,
        errors=errors,
        csv_download_base64=csv_b64,
        disclaimer=LEGAL_DISCLAIMER,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# Task 4: Voice Agent Integration Endpoints
# ============================================================================

@app.post(
    "/integration/voice-call",
    response_model=VoiceCallWebhookResponse,
    tags=["Week 7 Voice Integration"],
)
def handle_voice_call_webhook(payload: VoiceCallWebhookPayload):
    """Inbound webhook triggered upon call completion by Week 7 voice telephony agent."""
    result = voice_service.process_completed_voice_call(payload.model_dump())
    return VoiceCallWebhookResponse(**result)


@app.post(
    "/integration/voice-price-inquiry",
    response_model=VoicePriceInquiryResponse,
    tags=["Week 7 Voice Integration"],
)
def handle_voice_price_inquiry_endpoint(query: VoicePriceInquiryRequest):
    """Real-time voice telephony function call answering 'Mera ghar kitne ka bikega?' in UrduLish."""
    result = voice_service.handle_voice_price_inquiry(**query.model_dump())
    return VoicePriceInquiryResponse(**result)


@app.get(
    "/call",
    response_class=HTMLResponse,
    tags=["Week 7 Voice Integration"],
)
def serve_voice_call_station():
    """Interactive browser-based live voice calling station connected to Vapi."""
    call_html_path = Path(__file__).resolve().parent.parent / "dashboard" / "vapi_call.html"
    if call_html_path.exists():
        return FileResponse(call_html_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="Voice calling template not found")



# ============================================================================
# Task 2: LangGraph Assistant Endpoint
# ============================================================================

@app.post("/agent/chat", response_model=AgentChatResponse, tags=["LangGraph Assistant"])
def chat_with_assistant(request: AgentChatRequest):
    """Chat with the real estate assistant in UrduLish or English with tool-grounded prices."""
    res = ai_assistant.chat(
        message=request.message,
        conversation_id=request.conversation_id,
    )
    return AgentChatResponse(
        conversation_id=res["conversation_id"],
        user_query=res["user_query"],
        assistant_response=res["assistant_response"],
        intent=res["intent"],
        tool_called=res.get("tool_called"),
        tool_result=res.get("tool_result"),
        guardrail_passed=res["guardrail_passed"],
        disclaimer=LEGAL_DISCLAIMER,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# ============================================================================
# Task 5: Governance & Audit Log Inspection Endpoint
# ============================================================================

@app.get("/audit/logs", tags=["Model Governance"])
def get_prediction_audit_logs(limit: int = 50):
    """Retrieve verified prediction audit logs for compliance, monitoring, and debugging."""
    logs = audit_logger.get_recent_logs(limit=limit)
    summary = audit_logger.get_audit_summary()
    return {
        "status": "success",
        "total_records_returned": len(logs),
        "audit_summary": summary,
        "logs": logs,
        "disclaimer": LEGAL_DISCLAIMER,
    }
