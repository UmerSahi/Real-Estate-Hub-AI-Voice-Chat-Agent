"""Pydantic validation schemas and data contracts for Day 4 API and LangGraph Assistant.
Provides strict input validation, custom error reporting, and standardized responses.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from src.config import (
    API_VERSION,
    LEGAL_DISCLAIMER,
    VALID_CITIES,
    VALID_PROPERTY_TYPES,
    VALID_LEAD_SOURCES,
    VALID_PURPOSES,
    OOD_LIMITS,
)


# ============================================================================
# Task 1: Property Valuation Schemas
# ============================================================================

class PropertyValuationRequest(BaseModel):
    """Input payload for property price estimation."""
    city: str = Field(..., description="Metropolitan city (Lahore, Islamabad, Karachi, Rawalpindi)")
    area_society: str = Field(..., description="Housing scheme or locality name (e.g. DHA Phase 6, Bahria Town, F-10)")
    property_type: str = Field(default="House", description="Structure type (House, Flat, Upper Portion, Lower Portion, Farm House, Penthouse)")
    area_marla: float = Field(..., description="Land plot area in Marlas (1 Kanal = 20 Marla)")
    bedrooms: int = Field(default=3, description="Number of dedicated bedrooms")
    bathrooms: int = Field(default=3, description="Number of attached/guest bathrooms")
    age_years: int = Field(default=2, description="Age of construction in years (0 = brand new)")
    floors: int = Field(default=2, description="Number of storeys")
    is_corner: str = Field(default="no", description="'yes' or 'no'")
    is_park_facing: str = Field(default="no", description="'yes' or 'no'")
    amenities: Optional[str] = Field(default="24/7 security, backup electricity, water", description="List or text of amenities")
    dist_main_road_km: Optional[float] = Field(default=1.0, description="Distance to main artery in km")
    dist_school_km: Optional[float] = Field(default=1.5, description="Distance to nearest school in km")
    dist_hospital_km: Optional[float] = Field(default=2.0, description="Distance to nearest hospital in km")
    covered_area: Optional[float] = Field(default=None, description="Enclosed built covered area in sq ft")
    listed_price_pkr: Optional[float] = Field(default=None, description="Current listing/asking price for commercial verdict comparison")

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        clean = v.strip().title()
        matched = [c for c in VALID_CITIES if c.lower() == clean.lower()]
        if not matched:
            raise ValueError(f"Unsupported city '{v}'. Valid cities are: {', '.join(VALID_CITIES)}")
        return matched[0]

    @field_validator("area_marla")
    @classmethod
    def validate_area_marla(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Property area_marla must be strictly positive (greater than 0).")
        if v > OOD_LIMITS["max_area_marla"]:
            raise ValueError(
                f"Out-of-Distribution: Area {v} Marla exceeds typical residential distribution bounds "
                f"(max {OOD_LIMITS['max_area_marla']} Marlas / 5 Kanals). Please request a custom commercial appraisal."
            )
        return float(v)

    @field_validator("bedrooms")
    @classmethod
    def validate_bedrooms(cls, v: int) -> int:
        if v < OOD_LIMITS["min_bedrooms"]:
            raise ValueError(f"Property must have at least {OOD_LIMITS['min_bedrooms']} bedroom.")
        if v > OOD_LIMITS["max_bedrooms"]:
            raise ValueError(f"Out-of-Distribution: Bedroom count {v} exceeds residential threshold (max {OOD_LIMITS['max_bedrooms']}).")
        return int(v)

    @field_validator("bathrooms")
    @classmethod
    def validate_bathrooms(cls, v: int) -> int:
        if v < OOD_LIMITS["min_bathrooms"]:
            raise ValueError("Property must have at least 1 bathroom.")
        if v > OOD_LIMITS["max_bathrooms"]:
            raise ValueError(f"Out-of-Distribution: Bathroom count {v} exceeds residential threshold (max {OOD_LIMITS['max_bathrooms']}).")
        return int(v)

    @field_validator("age_years")
    @classmethod
    def validate_age_years(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Property age cannot be negative.")
        if v > OOD_LIMITS["max_age_years"]:
            raise ValueError(f"Out-of-Distribution: Property age {v} exceeds model training bounds (max {OOD_LIMITS['max_age_years']} years).")
        return int(v)

    @field_validator("property_type")
    @classmethod
    def validate_prop_type(cls, v: str) -> str:
        clean = v.strip().title()
        matched = [pt for pt in VALID_PROPERTY_TYPES if pt.lower() == clean.lower()]
        if not matched:
            raise ValueError(f"Unknown property_type '{v}'. Valid types are: {', '.join(VALID_PROPERTY_TYPES)}")
        return matched[0]

    @field_validator("is_corner", "is_park_facing")
    @classmethod
    def validate_binary_flags(cls, v: str) -> str:
        clean = str(v).strip().lower()
        if clean in ["1", "true", "yes", "y"]:
            return "yes"
        return "no"


class PropertyValuationResponse(BaseModel):
    """Standardized response from the property valuation model serving engine."""
    prediction_id: str
    predicted_price_pkr: float
    predicted_price_formatted: str
    lower_range_pkr: float
    lower_range_formatted: str
    upper_range_pkr: float
    upper_range_formatted: str
    price_range_formatted: str
    listed_price_pkr: Optional[float] = None
    listed_price_formatted: Optional[str] = None
    verdict: str = Field(..., description="Commercial pricing verdict: 'Overpriced', 'Fair', or 'Underpriced'")
    price_delta_pct: float
    client_explanation: str
    disclaimer: str = LEGAL_DISCLAIMER
    model_version: str
    timestamp: str


# ============================================================================
# Task 1: Lead Scoring Schemas
# ============================================================================

class LeadScoreRequest(BaseModel):
    """Input payload for scoring an inbound real estate sales prospect."""
    lead_id: Optional[str] = Field(default="LEAD-001", description="Unique lead identifier")
    lead_source: str = Field(..., description="Channel: call, WhatsApp, Facebook, website, walk-in")
    budget_pkr: float = Field(..., description="Prospect stated investment budget in numeric PKR")
    preferred_city: str = Field(..., description="Target metropolitan area (Lahore, Islamabad, Karachi, Rawalpindi)")
    preferred_society: str = Field(..., description="Housing scheme or sector (e.g. DHA Phase 6, Bahria Town)")
    purpose: str = Field(default="buy", description="Transaction goal: buy, rent, invest")
    number_of_calls: int = Field(default=2, description="Total telephonic qualification interactions logged")
    call_duration_avg_sec: int = Field(default=180, description="Average call duration in seconds")
    response_time_min: float = Field(default=15.0, description="Speed-to-lead callback delay in minutes")
    visit_booked: str = Field(default="no", description="Whether on-site inspection visit is scheduled: yes/no")
    days_since_first_contact: int = Field(default=3, description="Elapsed days since first inquiry")
    objection_raised: Optional[str] = Field(default="None", description="Primary friction or hesitation")

    @field_validator("lead_source")
    @classmethod
    def validate_lead_source(cls, v: str) -> str:
        clean = v.strip().lower()
        matched = [s for s in VALID_LEAD_SOURCES if s.lower() == clean]
        if not matched:
            raise ValueError(f"Invalid lead_source '{v}'. Supported sources are: {', '.join(VALID_LEAD_SOURCES)}")
        return matched[0]

    @field_validator("budget_pkr")
    @classmethod
    def validate_budget(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("budget_pkr must be strictly greater than 0.")
        if v > OOD_LIMITS["max_budget_pkr"]:
            raise ValueError(f"Out-of-Distribution: Budget exceeding PKR {OOD_LIMITS['max_budget_pkr']:,.0f} requires institutional underwriting.")
        return float(v)

    @field_validator("preferred_city")
    @classmethod
    def validate_pref_city(cls, v: str) -> str:
        clean = v.strip().title()
        matched = [c for c in VALID_CITIES if c.lower() == clean.lower()]
        if not matched:
            raise ValueError(f"Unsupported city '{v}'. Valid cities are: {', '.join(VALID_CITIES)}")
        return matched[0]

    @field_validator("purpose")
    @classmethod
    def validate_purpose(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in VALID_PURPOSES:
            raise ValueError(f"Invalid purpose '{v}'. Valid options: {', '.join(VALID_PURPOSES)}")
        return clean

    @field_validator("number_of_calls")
    @classmethod
    def validate_calls(cls, v: int) -> int:
        if v < 1:
            raise ValueError("number_of_calls must be at least 1.")
        return int(v)

    @field_validator("call_duration_avg_sec", "days_since_first_contact")
    @classmethod
    def validate_non_negative_ints(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Count or duration cannot be negative.")
        return int(v)

    @field_validator("response_time_min")
    @classmethod
    def validate_response_time(cls, v: float) -> float:
        if v < 0:
            raise ValueError("response_time_min cannot be negative.")
        return float(v)

    @field_validator("visit_booked")
    @classmethod
    def validate_visit(cls, v: str) -> str:
        clean = str(v).strip().lower()
        if clean in ["1", "true", "yes", "y"]:
            return "yes"
        return "no"


class LeadScoreResponse(BaseModel):
    """Standardized response from the lead scoring engine."""
    prediction_id: str
    lead_id: str
    conversion_probability: float
    conversion_score_pct: int
    tier: str = Field(..., description="'Hot', 'Warm', or 'Cold'")
    emoji: str
    label: str
    sla: str
    assigned_role: str
    channel: str
    action_plan: str
    customer_persona: str
    recommended_sales_pitch: str
    top_positive_drivers: List[str]
    top_negative_drivers: List[str]
    urdulish_explanation: str
    english_explanation: str
    disclaimer: str = LEGAL_DISCLAIMER
    model_version: str
    timestamp: str


# ============================================================================
# Task 1: Explainability Schemas
# ============================================================================

class FeatureAttributionItem(BaseModel):
    feature_name: str
    shap_value: float
    feature_value: Any
    impact_direction: str = Field(..., description="'increases' or 'decreases'")
    description: str


class PropertyExplanationResponse(BaseModel):
    prediction_id: str
    predicted_price_pkr: float
    predicted_price_formatted: str
    base_value_pkr: float
    base_value_formatted: str
    feature_attributions: List[FeatureAttributionItem]
    top_positive_drivers: List[str]
    top_negative_drivers: List[str]
    waterfall_summary: str
    urdulish_explanation: str
    english_explanation: str
    disclaimer: str = LEGAL_DISCLAIMER
    timestamp: str


class LeadExplanationResponse(BaseModel):
    prediction_id: str
    lead_id: str
    conversion_score_pct: int
    tier: str
    feature_attributions: List[FeatureAttributionItem]
    top_positive_drivers: List[str]
    top_negative_drivers: List[str]
    urdulish_explanation: str
    english_explanation: str
    disclaimer: str = LEGAL_DISCLAIMER
    timestamp: str


# ============================================================================
# Task 1: Batch Prediction Schemas
# ============================================================================

class BatchPredictionResponse(BaseModel):
    batch_id: str
    batch_type: str = Field(..., description="'properties' or 'leads'")
    total_rows: int
    successful_rows: int
    failed_rows: int
    summary_stats: Dict[str, Any]
    predictions: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    csv_download_base64: Optional[str] = None
    disclaimer: str = LEGAL_DISCLAIMER
    timestamp: str


# ============================================================================
# Task 1: Health & Model Info Schemas
# ============================================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    models_loaded: Dict[str, bool]
    database_connected: bool


class ModelInfoResponse(BaseModel):
    api_version: str
    valuation_model: Dict[str, Any]
    lead_scoring_model: Dict[str, Any]
    system_guardrails: Dict[str, Any]
    disclaimer: str


# ============================================================================
# Task 2 & 4: Voice Agent & Assistant Schemas
# ============================================================================

class VoiceCallWebhookPayload(BaseModel):
    """Payload sent by Week 7 voice agent telephony after a call terminates."""
    call_id: Optional[str] = Field(default="CALL-VOICE-001")
    caller_id: str = Field(default="+923001234567")
    call_duration_sec: int = Field(default=240)
    budget_pkr: float = Field(default=35_000_000)
    preferred_city: str = Field(default="Lahore")
    preferred_society: str = Field(default="DHA Phase 6")
    purpose: str = Field(default="buy")
    visit_booked: str = Field(default="yes")
    number_of_calls: int = Field(default=2)
    transcript_summary: Optional[str] = Field(
        default="Client requested 1 Kanal residential plot in DHA Phase 6. Budget ~3.5 Crore. Site visit agreed for Saturday."
    )
    assigned_employee_email: Optional[str] = Field(default="sales.lead@realestatehub.pk")


class VoiceCallWebhookResponse(BaseModel):
    call_id: str
    lead_id: str
    conversion_score_pct: int
    tier: str
    hot_lead_alert_triggered: bool
    email_notification_sent: bool
    assigned_employee_email: Optional[str]
    assigned_role: str
    action_plan: str
    customer_persona: str
    recommended_pitch: str
    timestamp: str


class VoicePriceInquiryRequest(BaseModel):
    """Voice agent real-time pricing inquiry ('Mera ghar kitne ka bikega?')."""
    city: str = Field(default="Lahore")
    area_society: str = Field(default="DHA Phase 6")
    area_marla: float = Field(default=20.0, description="Plot size in Marlas (20 Marla = 1 Kanal)")
    property_type: str = Field(default="House")
    bedrooms: int = Field(default=5)
    bathrooms: int = Field(default=5)
    age_years: int = Field(default=5)
    is_corner: str = Field(default="yes")


class VoicePriceInquiryResponse(BaseModel):
    predicted_price_pkr: float
    predicted_price_formatted: str
    lower_range_formatted: str
    upper_range_formatted: str
    tts_speech_text_urdulish: str
    tts_speech_text_english: str
    timestamp: str


class AgentChatRequest(BaseModel):
    message: str = Field(..., description="Sales agent question in UrduLish or English")
    conversation_id: Optional[str] = Field(default="conv-001")
    user_role: Optional[str] = Field(default="sales_agent")


class AgentChatResponse(BaseModel):
    conversation_id: str
    user_query: str
    assistant_response: str
    intent: str
    tool_called: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None
    guardrail_passed: bool
    disclaimer: str = LEGAL_DISCLAIMER
    timestamp: str
