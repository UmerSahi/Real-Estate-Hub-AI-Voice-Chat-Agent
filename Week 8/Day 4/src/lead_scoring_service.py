"""Task 1 & Task 5: Production Lead Scoring, Customer Persona & SHAP Explainability Engine.
Scores inbound prospects, derives operational SLAs, classifies customer personas,
and generates plain-language UrduLish & English conversion attributions.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import shap

from src.config import (
    BEST_LEAD_MODEL_PATH,
    HOT_THRESHOLD,
    KMEANS_PERSONAS_MODEL_PATH,
    LEAD_MODEL_VERSION,
    LEAD_PREPROCESSOR_PATH,
    LEGAL_DISCLAIMER,
    PERSONA_SCALER_PATH,
    SOCIETY_BENCHMARK_PRICE,
    WARM_THRESHOLD,
    format_price_pkr,
)


class LeadScoringService:
    """Production Real Estate Lead Scoring, Persona Engine, and Explainability Service."""

    def __init__(
        self,
        model_path: Path = BEST_LEAD_MODEL_PATH,
        preprocessor_path: Path = LEAD_PREPROCESSOR_PATH,
        persona_model_path: Path = KMEANS_PERSONAS_MODEL_PATH,
        persona_scaler_path: Path = PERSONA_SCALER_PATH,
    ):
        if not model_path.exists():
            raise FileNotFoundError(f"Lead model not found at {model_path}.")
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Lead preprocessor not found at {preprocessor_path}.")

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)

        # Persona cluster models
        self.persona_model = joblib.load(persona_model_path) if persona_model_path.exists() else None
        self.persona_scaler = joblib.load(persona_scaler_path) if persona_scaler_path.exists() else None

        # Build feature names
        num_cols = [
            "number_of_calls", "call_duration_avg_sec", "response_time_min",
            "days_since_first_contact", "budget_pkr", "lead_engagement_score",
            "budget_to_market_ratio", "lead_velocity", "high_intent_flag"
        ]
        cat_names = []
        try:
            cat_encoder = self.preprocessor.named_transformers_["cat"]
            from src.config import VALID_CITIES
            cat_names = cat_encoder.get_feature_names_out().tolist()
        except Exception:
            pass
        self.feature_names = num_cols + cat_names

        # SHAP Explainer
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            self.explainer = None

    def enrich_features(self, raw_dict: Dict[str, Any]) -> pd.DataFrame:
        """Enrich raw lead attributes with composite interaction metrics."""
        df = pd.DataFrame([raw_dict])

        # Normalize types
        calls = int(df["number_of_calls"].iloc[0]) if "number_of_calls" in df.columns else 1
        duration = float(df["call_duration_avg_sec"].iloc[0]) if "call_duration_avg_sec" in df.columns else 120.0
        resp_time = float(df["response_time_min"].iloc[0]) if "response_time_min" in df.columns else 30.0
        days = float(df["days_since_first_contact"].iloc[0]) if "days_since_first_contact" in df.columns else 1.0
        budget = float(df["budget_pkr"].iloc[0]) if "budget_pkr" in df.columns else 20_000_000.0
        soc = str(df["preferred_society"].iloc[0]) if "preferred_society" in df.columns else "DHA Phase 6"

        visit_raw = str(df.get("visit_booked", pd.Series(["no"])).iloc[0]).lower()
        visit_booked = "yes" if visit_raw in ["yes", "1", "true"] else "no"

        # 1. lead_engagement_score
        if "lead_engagement_score" not in df.columns or pd.isna(df["lead_engagement_score"].iloc[0]):
            df["lead_engagement_score"] = calls * (duration / 60.0)

        # 2. response_speed_category
        if "response_speed_category" not in df.columns or pd.isna(df["response_speed_category"].iloc[0]):
            if resp_time <= 15:
                cat = "Immediate (<=15m)"
            elif resp_time <= 60:
                cat = "Prompt (15m-1h)"
            elif resp_time <= 240:
                cat = "Standard (1h-4h)"
            else:
                cat = "Delayed (>4h)"
            df["response_speed_category"] = cat

        # 3. budget_to_market_ratio
        if "budget_to_market_ratio" not in df.columns or pd.isna(df["budget_to_market_ratio"].iloc[0]):
            bench = SOCIETY_BENCHMARK_PRICE.get(soc, 25_000_000)
            df["budget_to_market_ratio"] = float(np.clip(budget / bench, 0.1, 5.0))

        # 4. lead_velocity
        if "lead_velocity" not in df.columns or pd.isna(df["lead_velocity"].iloc[0]):
            df["lead_velocity"] = calls / (days + 1.0)

        # 5. high_intent_flag
        if "high_intent_flag" not in df.columns or pd.isna(df["high_intent_flag"].iloc[0]):
            is_high = 1 if (visit_booked == "yes" and resp_time <= 60 and calls >= 2) else 0
            df["high_intent_flag"] = is_high

        # Format categorical values
        df["visit_booked"] = visit_booked
        df["preferred_city"] = str(df.get("preferred_city", pd.Series(["Lahore"])).iloc[0]).title()
        df["preferred_society"] = soc
        df["lead_source"] = str(df.get("lead_source", pd.Series(["call"])).iloc[0]).lower()
        df["purpose"] = str(df.get("purpose", pd.Series(["buy"])).iloc[0]).lower()
        df["objection_raised"] = str(df.get("objection_raised", pd.Series(["None"])).iloc[0])
        df["budget_pkr"] = budget
        df["number_of_calls"] = calls
        df["call_duration_avg_sec"] = int(duration)
        df["response_time_min"] = resp_time
        df["days_since_first_contact"] = int(days)

        return df

    def determine_persona(self, enriched_dict: Dict[str, Any]) -> Tuple[str, str]:
        """Classify customer persona with cluster model or domain heuristics."""
        budget = enriched_dict.get("budget_pkr", 20_000_000)
        purpose = enriched_dict.get("purpose", "buy")
        calls = enriched_dict.get("number_of_calls", 1)
        visit = enriched_dict.get("visit_booked", "no")

        if purpose == "rent":
            return (
                "Urban Rental Inquirer",
                "Present high-mobility rental apartments with immediate possession and verified utility connections.",
            )
        elif budget >= 50_000_000:
            return (
                "Luxury Villa Upgrader & HNI",
                "Highlight prime sector locations, corner park-facing plots, bespoke architecture, and privacy.",
            )
        elif purpose == "invest" or budget >= 30_000_000:
            return (
                "High-Yield Capital Investor",
                "Pitch annualized rental yields, upcoming commercial road expansions, and projected 3-year capital appreciation.",
            )
        else:
            return (
                "Family First-Time Homebuyer",
                "Emphasize community safety, nearby accredited schools, 24/7 electricity backup, and clear transfer documentation.",
            )

    def score_lead(
        self,
        raw_lead: Dict[str, Any],
        prediction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate conversion probability, operational SLA tier, and plain-language reasoning."""
        pred_id = prediction_id or f"LEAD-{uuid.uuid4().hex[:8].upper()}"
        lead_id = str(raw_lead.get("lead_id", pred_id))

        df_enriched = self.enrich_features(raw_lead)

        # Feature transformations
        X_trans = self.preprocessor.transform(df_enriched)

        # Predict probability
        prob = float(self.model.predict_proba(X_trans)[0, 1])
        score_pct = int(round(prob * 100))

        # Operational tier & SLA assignment
        if prob >= HOT_THRESHOLD:
            tier = "Hot"
            emoji = "🔥"
            label = "🔥 Hot Lead (Immediate VIP Closer)"
            sla = "< 15 minutes"
            role = "Senior Closer / Sales Director"
            channel = "Direct Phone Call & WhatsApp VIP"
            plan = "Immediate VIP outreach; schedule executive private site walkthrough and present term sheet."
        elif prob >= WARM_THRESHOLD:
            tier = "Warm"
            emoji = "🌤"
            label = "🌤 Warm Lead (Priority Consultation)"
            sla = "< 2 hours"
            role = "Account Executive"
            channel = "WhatsApp Portfolio & Callback"
            plan = "Share 3 tailored property dossiers matching declared budget; follow up to secure physical inspection."
        else:
            tier = "Cold"
            emoji = "❄️"
            label = "❄️ Cold Lead (Nurture Campaign)"
            sla = "< 24 hours"
            role = "Automated AI Lead Nurturer"
            channel = "Automated WhatsApp / Email Drip"
            plan = "Enroll in market intelligence drip campaign; trigger re-scoring when portal activity recurs."

        # Persona discovery
        persona, pitch = self.determine_persona(df_enriched.iloc[0].to_dict())

        # SHAP local drivers
        top_pos = []
        top_neg = []
        feature_attributions: List[Dict[str, Any]] = []

        if self.explainer is not None:
            try:
                raw_shap = self.explainer.shap_values(X_trans)
                if isinstance(raw_shap, list) and len(raw_shap) == 2:
                    sample_shaps = raw_shap[1][0]
                elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
                    sample_shaps = raw_shap[0, :, 1]
                elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 2:
                    sample_shaps = raw_shap[0]
                else:
                    sample_shaps = np.array(raw_shap).flatten()

                for i in range(min(len(self.feature_names), len(sample_shaps))):
                    val = float(sample_shaps[i])
                    feat = self.feature_names[i]
                    impact_dir = "increases" if val >= 0 else "decreases"
                    desc = f"{feat} increases conversion probability (+{val*100:.1f}%)" if val >= 0 else f"{feat} reduces conversion probability ({val*100:.1f}%)"

                    feature_attributions.append(
                        {
                            "feature_name": feat,
                            "shap_value": val,
                            "feature_value": str(df_enriched.iloc[0].get(feat, "N/A")),
                            "impact_direction": impact_dir,
                            "description": desc,
                        }
                    )

                pos_idx = np.argsort(sample_shaps)[::-1]
                neg_idx = np.argsort(sample_shaps)

                top_pos = [f"{self.feature_names[i]} ({sample_shaps[i]:+.3f})" for i in pos_idx if sample_shaps[i] > 0][:4]
                top_neg = [f"{self.feature_names[i]} ({sample_shaps[i]:+.3f})" for i in neg_idx if sample_shaps[i] < 0][:3]
            except Exception as e:
                print(f"[SHAP Warning] Lead SHAP calculation: {e}")

        # Plain-language UrduLish & English reasons
        calls_count = df_enriched["number_of_calls"].iloc[0]
        visit_booked = df_enriched["visit_booked"].iloc[0]
        budget_fmt = format_price_pkr(df_enriched["budget_pkr"].iloc[0])
        city = df_enriched["preferred_city"].iloc[0]
        soc = df_enriched["preferred_society"].iloc[0]

        urdu_reasons = []
        if visit_booked == "yes":
            urdu_reasons.append("site visit already booked hai")
        if calls_count >= 2:
            urdu_reasons.append(f"client ne {calls_count} baar follow-up call ki")
        if df_enriched["response_time_min"].iloc[0] <= 15:
            urdu_reasons.append("team ne 15 minute ke andar respond kiya")
        if not urdu_reasons:
            urdu_reasons.append(f"client ka budget {budget_fmt} market benchmark se match karta hai")

        reasons_summary = ", ".join(urdu_reasons)
        urdulish_text = (
            f"Yeh lead {emoji} {tier} hai (Conversion Probability: {score_pct}%). "
            f"Wajah: {reasons_summary}. Target: {soc}, {city}. "
            f"Recommended SLA: {sla} ke andar {role} call kare."
        )

        eng_text = (
            f"Lead {lead_id} is evaluated as {tier} with a {score_pct}% probability of closing. "
            f"Primary positive factors: {', '.join(top_pos[:2]) or 'high interaction velocity'}. "
            f"SLA Protocol: {sla} handled by {role}."
        )

        return {
            "prediction_id": pred_id,
            "lead_id": lead_id,
            "conversion_probability": prob,
            "conversion_score_pct": score_pct,
            "tier": tier,
            "emoji": emoji,
            "label": label,
            "sla": sla,
            "assigned_role": role,
            "channel": channel,
            "action_plan": plan,
            "customer_persona": persona,
            "recommended_sales_pitch": pitch,
            "feature_attributions": feature_attributions[:10],
            "top_positive_drivers": top_pos,
            "top_negative_drivers": top_neg,
            "urdulish_explanation": urdulish_text,
            "english_explanation": eng_text,
            "disclaimer": LEGAL_DISCLAIMER,
            "model_version": LEAD_MODEL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
lead_scoring_service = LeadScoringService()
