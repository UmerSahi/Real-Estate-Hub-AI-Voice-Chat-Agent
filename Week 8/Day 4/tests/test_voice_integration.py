"""Unit and Integration Tests for Task 4: Voice Agent Integration Pipeline.
Validates:
- Telephony webhook execution
- Automatic lead scoring after calls
- Hot lead email notification triggering (SLA < 15 min alert)
- Real-time TTS speech generation for 'Mera ghar kitne ka bikega?'
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add Day 4 root to path
DAY4_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAY4_DIR))

from src.voice_integration import voice_service
from src.config import SIMULATED_EMAILS_LOG


class TestVoiceIntegration(unittest.TestCase):
    """Test suite for Week 7 voice telephony and Deepgram integration."""

    def test_01_voice_call_intake_and_scoring(self):
        """Completed voice call webhook should score lead and return operational play."""
        payload = {
            "call_id": "CALL-UNIT-001",
            "caller_id": "+923001112233",
            "call_duration_sec": 260,
            "budget_pkr": 40_000_000,
            "preferred_city": "Lahore",
            "preferred_society": "DHA Phase 6",
            "purpose": "buy",
            "visit_booked": "yes",
            "number_of_calls": 2,
            "transcript_summary": "Client seeking 10 Marla house in DHA Phase 6, budget ~4 Crore.",
            "assigned_employee_email": "agent.test@realestatehub.pk",
        }
        res = voice_service.process_completed_voice_call(payload)
        self.assertEqual(res["call_id"], "CALL-UNIT-001")
        self.assertIn("conversion_score_pct", res)
        self.assertIn("tier", res)
        self.assertIn("customer_persona", res)
        self.assertIn("recommended_pitch", res)

    def test_02_hot_lead_triggers_email_dispatch(self):
        """A high-intent call (prob >= 0.70) must trigger an automated email alert."""
        hot_payload = {
            "call_id": "CALL-HOT-VIP-777",
            "caller_id": "+923009990000",
            "call_duration_sec": 480,
            "budget_pkr": 60_000_000,
            "preferred_city": "Lahore",
            "preferred_society": "DHA Phase 6",
            "purpose": "buy",
            "visit_booked": "yes",
            "number_of_calls": 5,
            "transcript_summary": "VIP buyer completed second site walkthrough, requesting contract drafting.",
            "assigned_employee_email": "director.sales@realestatehub.pk",
        }
        res = voice_service.process_completed_voice_call(hot_payload)
        self.assertTrue(res["hot_lead_alert_triggered"])
        self.assertTrue(res["email_notification_sent"])

        # Check that email log contains this alert
        self.assertTrue(SIMULATED_EMAILS_LOG.exists())
        with open(SIMULATED_EMAILS_LOG, "r", encoding="utf-8") as f:
            log_text = f.read()
        self.assertIn("CALL-HOT-VIP-777", log_text)
        self.assertIn("director.sales@realestatehub.pk", log_text)
        self.assertIn("VIP HOT LEAD", log_text)

    def test_03_voice_price_inquiry_tts_speech(self):
        """Voice agent real-time pricing inquiry must return speech-ready UrduLish & English."""
        res = voice_service.handle_voice_price_inquiry(
            city="Lahore",
            area_society="DHA Phase 6",
            area_marla=20.0,
            bedrooms=5,
            bathrooms=5,
            age_years=5,
            property_type="House",
            is_corner="yes",
        )
        self.assertIn("predicted_price_formatted", res)
        self.assertIn("tts_speech_text_urdulish", res)
        self.assertIn("tts_speech_text_english", res)

        # Ensure UrduLish is natural for TTS telephony
        urdu_tts = res["tts_speech_text_urdulish"]
        self.assertIn("Janab", urdu_tts)
        self.assertIn("DHA Phase 6", urdu_tts)
        self.assertIn("1 Kanal", urdu_tts)
        self.assertIn("fair value", urdu_tts)


if __name__ == "__main__":
    unittest.main()
