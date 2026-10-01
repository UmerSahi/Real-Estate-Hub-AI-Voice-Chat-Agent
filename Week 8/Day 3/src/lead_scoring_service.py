"""Production Lead Scoring & Explainability Inference Service.
Unifies model scoring, operational segmentation, customer persona classification,
and real-time SHAP explainability into a single production-ready interface.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Dict, Any, List, Tuple
import joblib
import numpy as np
import pandas as pd
import shap

# Ensure UTF-8 console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

warnings.filterwarnings("ignore")

from src.config import (
    BEST_MODEL_PATH,
    KMEANS_PERSONAS_MODEL_PATH,
    PERSONA_SCALER_PATH,
    PREPROCESSOR_PATH,
)
from src.explainability_shap import generate_plain_language_reasons
from src.lead_segmentation import classify_lead_tier, CustomerPersonaEngine


class LeadScoringService:
    """Production Real Estate Lead Scoring and Explainability Engine."""

    def __init__(
        self,
        model_path: Path = BEST_MODEL_PATH,
        preprocessor_path: Path = PREPROCESSOR_PATH,
        persona_model_path: Path = KMEANS_PERSONAS_MODEL_PATH,
        persona_scaler_path: Path = PERSONA_SCALER_PATH,
    ):
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}. Train models first.")
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor not found at {preprocessor_path}.")

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)

        # Persona Engine
        if persona_model_path.exists():
            try:
                self.persona_engine = CustomerPersonaEngine.load(persona_model_path)
            except Exception:
                self.persona_engine = CustomerPersonaEngine()
        else:
            self.persona_engine = CustomerPersonaEngine()

        # Extract feature names
        cat_encoder = self.preprocessor.named_transformers_["cat"]
        from src.data_loader import NUMERICAL_FEATURES, CATEGORICAL_FEATURES
        cat_names = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
        self.feature_names = NUMERICAL_FEATURES + cat_names

        # SHAP Explainer
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            self.explainer = None

    def score_lead(self, lead_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Score an individual lead and return complete operational verdict, persona, and SHAP reason."""
        df_single = pd.DataFrame([lead_dict])

        # Feature transformations
        X_trans = self.preprocessor.transform(df_single)

        # Conversion Probability
        prob = float(self.model.predict_proba(X_trans)[0, 1])

        # Lead Tier & SLA
        tier_info = classify_lead_tier(prob)

        # Persona Classification
        persona_info = (
            self.persona_engine.predict_persona(lead_dict)
            if self.persona_engine.is_fitted
            else {"name": "General Real Estate Buyer", "recommended_pitch": "Standard inquiry"}
        )

        # SHAP Attributions
        top_pos = []
        top_neg = []
        if self.explainer:
            raw_shap = self.explainer.shap_values(X_trans)
            if isinstance(raw_shap, list) and len(raw_shap) == 2:
                sample_shaps = raw_shap[1][0]
            elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 3:
                sample_shaps = raw_shap[0, :, 1]
            else:
                sample_shaps = raw_shap[0]

            pos_idx = np.argsort(sample_shaps)[::-1]
            neg_idx = np.argsort(sample_shaps)

            top_pos = [(self.feature_names[i], float(sample_shaps[i])) for i in pos_idx if sample_shaps[i] > 0][:5]
            top_neg = [(self.feature_names[i], float(sample_shaps[i])) for i in neg_idx if sample_shaps[i] < 0][:5]

        # Plain Language Explanations
        reasons = generate_plain_language_reasons(lead_dict, prob, tier_info, top_pos, top_neg)

        return {
            "lead_id": lead_dict.get("lead_id", "UNKNOWN"),
            "conversion_probability": prob,
            "conversion_score_pct": int(round(prob * 100)),
            "tier": tier_info["tier"],
            "emoji": tier_info["emoji"],
            "label": tier_info["label"],
            "sla": tier_info["sla"],
            "assigned_role": tier_info["assigned_role"],
            "channel": tier_info["channel"],
            "action_plan": tier_info["action_plan"],
            "customer_persona": persona_info["name"],
            "recommended_sales_pitch": persona_info.get("recommended_pitch", ""),
            "top_positive_drivers": [f"{feat} ({val:+.3f})" for feat, val in top_pos[:3]],
            "top_negative_drivers": [f"{feat} ({val:+.3f})" for feat, val in top_neg[:2]],
            "urdulish_explanation": reasons["urdulish_explanation"],
            "english_explanation": reasons["english_explanation"],
        }


if __name__ == "__main__":
    from src.data_loader import get_lead_data_splits
    from src.classification_models import train_classification_models

    splits = get_lead_data_splits()
    clf_res = train_classification_models(
        splits["X_train_trans"], splits["y_train"].values,
        splits["X_test_trans"], splits["y_test"].values
    )
    best_clf = clf_res["models"]["LightGBM"]
    joblib.dump(best_clf, BEST_MODEL_PATH)

    service = LeadScoringService()
    sample = splits["df_test_raw"].iloc[0].to_dict()
    result = service.score_lead(sample)

    print("Lead Scoring Production Service Output:")
    print(f"  Lead ID: {result['lead_id']}")
    print(f"  Classification: {result['label']} ({result['conversion_score_pct']}%)")
    print(f"  SLA Protocol: {result['sla']}")
    print(f"  Customer Persona: {result['customer_persona']}")
    print(f"  Sales Pitch: {result['recommended_sales_pitch']}")
    print(f"\nUrduLish Reason:\n  {result['urdulish_explanation']}")
