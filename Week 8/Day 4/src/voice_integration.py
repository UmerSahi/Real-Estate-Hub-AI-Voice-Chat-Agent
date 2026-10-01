"""Task 4: Voice Agent Integration Pipeline (Extension of Week 7 Telephony & Deepgram Ecosystem).
Provides:
1. Post-call webhook handling with automatic lead scoring.
2. Hot lead immediate email dispatcher to assigned sales employee with SLA countdown.
3. Real-time conversational TTS price query handler for 'Mera ghar kitne ka bikega?'.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import (
    SIMULATED_EMAILS_LOG,
    HOT_THRESHOLD,
    format_price_pkr,
)
from src.lead_scoring_service import lead_scoring_service
from src.valuation_service import valuation_service


class VoiceAgentIntegrationService:
    """Manages bilateral integration between Week 7 voice telephony and Week 8 ML engines."""

    def __init__(self, email_log_path: Path = SIMULATED_EMAILS_LOG):
        self.email_log_path = email_log_path
        self.email_log_path.parent.mkdir(parents=True, exist_ok=True)

    def process_completed_voice_call(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Triggered automatically via telephony webhook when inbound caller hangs up."""
        call_id = payload.get("call_id", f"CALL-{datetime.now(timezone.utc).strftime('%H%M%S')}")
        caller_id = payload.get("caller_id", "+923001234567")
        budget = float(payload.get("budget_pkr", 35_000_000))
        city = payload.get("preferred_city", "Lahore")
        society = payload.get("preferred_society", "DHA Phase 6")
        duration = int(payload.get("call_duration_sec", 180))
        visit = payload.get("visit_booked", "no")
        calls = int(payload.get("number_of_calls", 1))
        notes = payload.get("transcript_summary", "Client inquired about residential options.")
        employee_email = payload.get("assigned_employee_email", "closer.team@realestatehub.pk")

        # 1. Evaluate Lead Score
        lead_input = {
            "lead_id": call_id,
            "lead_source": "call",
            "budget_pkr": budget,
            "preferred_city": city,
            "preferred_society": society,
            "purpose": payload.get("purpose", "buy"),
            "number_of_calls": calls,
            "call_duration_avg_sec": duration,
            "response_time_min": 5.0,  # Telephony live interaction
            "visit_booked": visit,
            "days_since_first_contact": 1,
            "objection_raised": "None",
        }
        score_res = lead_scoring_service.score_lead(lead_input)

        is_hot = score_res["conversion_probability"] >= HOT_THRESHOLD
        email_sent = False

        # 2. Trigger Hot Lead Alert if conversion probability >= 70%
        if is_hot:
            email_sent = self.dispatch_hot_lead_alert_email(
                call_id=call_id,
                caller_id=caller_id,
                recipient_email=employee_email,
                score_data=score_res,
                transcript_summary=notes,
            )

        return {
            "call_id": call_id,
            "lead_id": score_res["lead_id"],
            "conversion_score_pct": score_res["conversion_score_pct"],
            "tier": score_res["tier"],
            "hot_lead_alert_triggered": is_hot,
            "email_notification_sent": email_sent,
            "assigned_employee_email": employee_email if is_hot else None,
            "assigned_role": score_res["assigned_role"],
            "action_plan": score_res["action_plan"],
            "customer_persona": score_res["customer_persona"],
            "recommended_pitch": score_res["recommended_sales_pitch"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def dispatch_hot_lead_alert_email(
        self,
        call_id: str,
        caller_id: str,
        recipient_email: str,
        score_data: Dict[str, Any],
        transcript_summary: str,
    ) -> bool:
        """Compose and dispatch high-priority email alert to assigned sales closer."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        prob_pct = score_data["conversion_score_pct"]
        persona = score_data["customer_persona"]
        role = score_data["assigned_role"]
        sla = score_data["sla"]
        pitch = score_data["recommended_sales_pitch"]
        urdu_reason = score_data.get("urdulish_explanation", "")

        subject = f"🚨 [VIP HOT LEAD] {call_id} — {prob_pct}% Conversion Intent (SLA: {sla})"
        body = (
            f"======================================================================\n"
            f"FROM: automated-dispatch@realestatehub.pk\n"
            f"TO: {recipient_email}\n"
            f"DATE: {now_str}\n"
            f"SUBJECT: {subject}\n"
            f"PRIORITY: HIGH (Immediate Action Required)\n"
            f"======================================================================\n\n"
            f"Dear {role},\n\n"
            f"A high-value prospect has just concluded an intake call with the Week 7 Voice Agent.\n"
            f"The ML Lead Scoring Model has classified this lead as 🔥 HOT with a {prob_pct}% conversion probability.\n\n"
            f"📋 LEAD DETAILS:\n"
            f"  • Call ID: {call_id}\n"
            f"  • Caller Phone: {caller_id}\n"
            f"  • Customer Persona: {persona}\n"
            f"  • Required SLA: {sla}\n\n"
            f"🎙️ CALL TRANSCRIPT SUMMARY:\n"
            f"  \"{transcript_summary}\"\n\n"
            f"💡 RECOMMENDED SALES PLAYBOOK & PITCH:\n"
            f"  \"{pitch}\"\n\n"
            f"🇵🇰 URDULISH REASONING:\n"
            f"  \"{urdu_reason}\"\n\n"
            f"Please initiate direct contact with the client immediately.\n"
            f"RealEstate-Hub CRM Automated Lead Dispatcher\n"
            f"----------------------------------------------------------------------\n\n"
        )

        try:
            with open(self.email_log_path, "a", encoding="utf-8") as f:
                f.write(body)
            print(f"[Email Dispatcher] Alert successfully delivered to {recipient_email} for {call_id}")
            return True
        except Exception as e:
            print(f"[Email Dispatcher Error] Failed to write alert log: {e}")
            return False

    def handle_voice_price_inquiry(
        self,
        city: str,
        area_society: str,
        area_marla: float,
        bedrooms: int = 5,
        bathrooms: int = 5,
        age_years: int = 5,
        property_type: str = "House",
        is_corner: str = "yes",
    ) -> Dict[str, Any]:
        """Real-time voice telephony function call for 'Mera ghar kitne ka bikega?'."""
        pred = valuation_service.predict_valuation(
            {
                "city": city,
                "area_society": area_society,
                "area_marla": float(area_marla),
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "age_years": age_years,
                "property_type": property_type,
                "is_corner": is_corner,
            }
        )

        pred_fmt = pred["predicted_price_formatted"]
        low_fmt = pred["lower_range_formatted"]
        up_fmt = pred["upper_range_formatted"]

        size_label = f"{int(area_marla/20)} Kanal" if area_marla >= 20 and area_marla % 20 == 0 else f"{area_marla:.0f} Marla"

        # Formulate concise, speech-optimized text for TTS engine
        urdulish_tts = (
            f"Janab, model ke mutabiq aap ke {area_society} mein {size_label} ghar ki takhmeena fair value "
            f"taqreeban {pred_fmt} hai, jis ki market trading range {low_fmt} se {up_fmt} banti hai. "
            f"Kya aap hamare senior property consultant se visit schedule karwana chahein gay?"
        )

        english_tts = (
            f"Sir, based on our real-time valuation model, the estimated fair market value for your {size_label} home "
            f"in {area_society} is approximately {pred_fmt}, with an expected trading range between {low_fmt} and {up_fmt}. "
            f"Would you like to schedule an inspection visit with our senior agent?"
        )

        return {
            "predicted_price_pkr": pred["predicted_price_pkr"],
            "predicted_price_formatted": pred_fmt,
            "lower_range_formatted": low_fmt,
            "upper_range_formatted": up_fmt,
            "tts_speech_text_urdulish": urdulish_tts,
            "tts_speech_text_english": english_tts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
voice_service = VoiceAgentIntegrationService()
