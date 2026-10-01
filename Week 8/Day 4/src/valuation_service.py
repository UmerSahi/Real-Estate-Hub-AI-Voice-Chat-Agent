"""Task 1 & Task 5: Production Property Valuation Inference & SHAP Explainability Engine.
Serves point estimates, 10th/90th percentile confidence bounds, commercial verdict,
feature enrichment, and SHAP local feature attributions with UrduLish descriptions.
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
    BEST_VALUATION_MODEL_PATH,
    DEFAULT_SOCIETY_TIER,
    LEGAL_DISCLAIMER,
    QUANTILE_LOWER_MODEL_PATH,
    QUANTILE_UPPER_MODEL_PATH,
    SOCIETY_BENCHMARK_PRICE,
    SOCIETY_TIERS,
    VALUATION_MODEL_VERSION,
    VALUATION_PREPROCESSOR_PATH,
    format_price_pkr,
)


class PropertyValuationService:
    """Production Valuation Inference Service with Quantile Confidence Bounds and SHAP attributions."""

    def __init__(
        self,
        model_path: Path = BEST_VALUATION_MODEL_PATH,
        preprocessor_path: Path = VALUATION_PREPROCESSOR_PATH,
        lower_path: Path = QUANTILE_LOWER_MODEL_PATH,
        upper_path: Path = QUANTILE_UPPER_MODEL_PATH,
    ):
        if not model_path.exists():
            raise FileNotFoundError(f"Valuation model not found at {model_path}.")
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor not found at {preprocessor_path}.")

        self.model = joblib.load(model_path)
        self.preprocessor = joblib.load(preprocessor_path)
        self.lower_model = joblib.load(lower_path) if lower_path.exists() else None
        self.upper_model = joblib.load(upper_path) if upper_path.exists() else None

        # Build feature names list from preprocessor
        self.feature_names = []
        for name, trans, cols in self.preprocessor.transformers_:
            if hasattr(trans, "get_feature_names_out"):
                try:
                    self.feature_names.extend(trans.get_feature_names_out(cols).tolist())
                except Exception:
                    self.feature_names.extend(cols)
            else:
                self.feature_names.extend(cols)

        # Initialize SHAP TreeExplainer
        try:
            self.explainer = shap.TreeExplainer(self.model)
        except Exception:
            self.explainer = None

    def enrich_features(self, raw_dict: Dict[str, Any]) -> pd.DataFrame:
        """Enrich raw property parameters into the complete 22-column feature dataframe."""
        df = pd.DataFrame([raw_dict])

        # Ensure numeric types
        area_marla = float(df["area_marla"].iloc[0])
        bedrooms = int(df["bedrooms"].iloc[0]) if "bedrooms" in df else 3
        bathrooms = int(df["bathrooms"].iloc[0]) if "bathrooms" in df else 3
        age_years = int(df["age_years"].iloc[0]) if "age_years" in df else 2
        floors = int(df["floors"].iloc[0]) if "floors" in df else 2

        # 1. area_sqft
        if "area_sqft" not in df.columns or pd.isna(df["area_sqft"].iloc[0]):
            df["area_sqft"] = area_marla * 225.0
        area_sqft = float(df["area_sqft"].iloc[0])

        # 2. covered_area
        if "covered_area" not in df.columns or pd.isna(df["covered_area"].iloc[0]) or df["covered_area"].iloc[0] is None:
            # Typical residential covered area formula based on floors
            coverage_factor = min(2.5, 0.70 * floors)
            df["covered_area"] = area_sqft * coverage_factor
        covered_area = float(df["covered_area"].iloc[0])

        # 3. society_tier
        area_society = str(df["area_society"].iloc[0]).strip()
        if "society_tier" not in df.columns or pd.isna(df["society_tier"].iloc[0]):
            df["society_tier"] = SOCIETY_TIERS.get(area_society, DEFAULT_SOCIETY_TIER)

        # 4. property_age_bucket
        if "property_age_bucket" not in df.columns or pd.isna(df["property_age_bucket"].iloc[0]):
            if age_years <= 1:
                df["property_age_bucket"] = "Brand New (<=1y)"
            elif age_years <= 5:
                df["property_age_bucket"] = "Modern (2-5y)"
            elif age_years <= 15:
                df["property_age_bucket"] = "Established (6-15y)"
            else:
                df["property_age_bucket"] = "Aging (>15y)"

        # 5. amenity_score
        if "amenity_score" not in df.columns or pd.isna(df["amenity_score"].iloc[0]):
            amenities_val = str(df["amenities"].iloc[0]) if "amenities" in df.columns and pd.notna(df["amenities"].iloc[0]) else ""
            items = [x.strip() for x in amenities_val.replace(";", ",").split(",") if x.strip()]
            df["amenity_score"] = max(2, len(items)) if items else 3

        # 6. Distances defaults
        for col, default_val in [
            ("dist_main_road_km", 1.0),
            ("dist_school_km", 1.5),
            ("dist_hospital_km", 2.0),
        ]:
            if col not in df.columns or pd.isna(df[col].iloc[0]):
                df[col] = default_val

        # 7. accessibility_composite
        if "accessibility_composite" not in df.columns or pd.isna(df["accessibility_composite"].iloc[0]):
            df["accessibility_composite"] = 1.0 / (
                1.0
                + (0.50 * float(df["dist_main_road_km"].iloc[0]))
                + (0.25 * float(df["dist_school_km"].iloc[0]))
                + (0.25 * float(df["dist_hospital_km"].iloc[0]))
            )

        # 8. spatial_density_ratio
        if "spatial_density_ratio" not in df.columns or pd.isna(df["spatial_density_ratio"].iloc[0]):
            df["spatial_density_ratio"] = float(np.clip(covered_area / (area_sqft + 1e-5), 0.1, 3.5))

        # 9. bed_to_bath_ratio
        if "bed_to_bath_ratio" not in df.columns or pd.isna(df["bed_to_bath_ratio"].iloc[0]):
            df["bed_to_bath_ratio"] = float(np.clip(bedrooms / (bathrooms + 0.1), 0.3, 3.0))

        # 10. society_hist_median_ppm
        if "society_hist_median_ppm" not in df.columns or pd.isna(df["society_hist_median_ppm"].iloc[0]):
            bench_10m = SOCIETY_BENCHMARK_PRICE.get(area_society, 25_000_000)
            df["society_hist_median_ppm"] = float(bench_10m / 10.0)

        # Binary standardizations
        is_corn = str(df["is_corner"].iloc[0]) if "is_corner" in df.columns else "no"
        df["is_corner"] = "yes" if is_corn.lower() in ["yes", "1", "true"] else "no"

        is_park = str(df["is_park_facing"].iloc[0]) if "is_park_facing" in df.columns else "no"
        df["is_park_facing"] = "yes" if is_park.lower() in ["yes", "1", "true"] else "no"

        p_type = str(df["property_type"].iloc[0]) if "property_type" in df.columns else "House"
        df["property_type"] = p_type.title()

        c_city = str(df["city"].iloc[0]) if "city" in df.columns else "Lahore"
        df["city"] = c_city.title()

        df["floors"] = floors
        df["bedrooms"] = bedrooms
        df["bathrooms"] = bathrooms
        df["age_years"] = age_years

        return df

    def predict_valuation(
        self,
        raw_features: Dict[str, Any],
        prediction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate point prediction, confidence intervals, and commercial verdict."""
        pred_id = prediction_id or f"VAL-{uuid.uuid4().hex[:8].upper()}"
        df_enriched = self.enrich_features(raw_features)

        # Transform features
        X_trans = self.preprocessor.transform(df_enriched)

        # Point prediction
        raw_pred = float(self.model.predict(X_trans)[0])
        pred_pkr = max(500_000.0, raw_pred)

        # Quantile bounds
        if self.lower_model is not None and self.upper_model is not None:
            lower_pkr = float(self.lower_model.predict(X_trans)[0])
            upper_pkr = float(self.upper_model.predict(X_trans)[0])
            # Ensure logical bounding
            lower_pkr = min(lower_pkr, pred_pkr * 0.94)
            upper_pkr = max(upper_pkr, pred_pkr * 1.06)
        else:
            lower_pkr = pred_pkr * 0.92
            upper_pkr = pred_pkr * 1.08

        pred_fmt = format_price_pkr(pred_pkr)
        lower_fmt = format_price_pkr(lower_pkr)
        upper_fmt = format_price_pkr(upper_pkr)
        range_fmt = f"{lower_fmt} - {upper_fmt}"

        # Commercial verdict
        listed_price = raw_features.get("listed_price_pkr")
        verdict = "Fair"
        delta_pct = 0.0
        listed_fmt = None

        if listed_price is not None and float(listed_price) > 0:
            listed_price = float(listed_price)
            listed_fmt = format_price_pkr(listed_price)
            delta_pct = round(((listed_price - pred_pkr) / pred_pkr) * 100.0, 1)

            if listed_price > upper_pkr or delta_pct >= 10.0:
                verdict = "Overpriced"
                explanation = (
                    f"Predicted: {pred_fmt} (fair range {range_fmt}). "
                    f"Listed at {listed_fmt} -> Overpriced by ~{abs(delta_pct):.0f}%."
                )
            elif listed_price < lower_pkr or delta_pct <= -10.0:
                verdict = "Underpriced"
                explanation = (
                    f"Predicted: {pred_fmt} (fair range {range_fmt}). "
                    f"Listed at {listed_fmt} -> Underpriced by ~{abs(delta_pct):.0f}% (Potential high-yield deal)."
                )
            else:
                verdict = "Fair"
                explanation = (
                    f"Predicted: {pred_fmt} (fair range {range_fmt}). "
                    f"Listed at {listed_fmt} -> Fair Market Price (within {abs(delta_pct):.1f}% of model benchmark)."
                )
        else:
            explanation = f"Model calculated fair value is {pred_fmt} with confidence interval {range_fmt}."

        return {
            "prediction_id": pred_id,
            "predicted_price_pkr": pred_pkr,
            "predicted_price_formatted": pred_fmt,
            "lower_range_pkr": lower_pkr,
            "lower_range_formatted": lower_fmt,
            "upper_range_pkr": upper_pkr,
            "upper_range_formatted": upper_fmt,
            "price_range_formatted": range_fmt,
            "listed_price_pkr": listed_price,
            "listed_price_formatted": listed_fmt,
            "verdict": verdict,
            "price_delta_pct": delta_pct,
            "client_explanation": explanation,
            "disclaimer": LEGAL_DISCLAIMER,
            "model_version": VALUATION_MODEL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def explain_valuation(
        self,
        raw_features: Dict[str, Any],
        prediction_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute SHAP feature attributions and generate plain-language explanations."""
        base_pred = self.predict_valuation(raw_features, prediction_id=prediction_id)
        pred_id = base_pred["prediction_id"]

        df_enriched = self.enrich_features(raw_features)
        X_trans = self.preprocessor.transform(df_enriched)

        feature_attributions: List[Dict[str, Any]] = []
        top_pos = []
        top_neg = []
        base_val = base_pred["predicted_price_pkr"] * 0.85  # default base

        if self.explainer is not None:
            try:
                raw_shap = self.explainer.shap_values(X_trans)
                if isinstance(raw_shap, list):
                    shap_vals = raw_shap[0]
                elif isinstance(raw_shap, np.ndarray) and len(raw_shap.shape) == 2:
                    shap_vals = raw_shap[0]
                else:
                    shap_vals = np.array(raw_shap).flatten()

                if hasattr(self.explainer, "expected_value"):
                    exp_val = self.explainer.expected_value
                    base_val = float(exp_val[0] if isinstance(exp_val, (list, np.ndarray)) else exp_val)

                # Pair features
                for i in range(min(len(self.feature_names), len(shap_vals))):
                    val = float(shap_vals[i])
                    feat_name = self.feature_names[i]
                    impact_dir = "increases" if val >= 0 else "decreases"
                    desc = f"{feat_name} adds ~{format_price_pkr(abs(val))}" if val >= 0 else f"{feat_name} reduces ~{format_price_pkr(abs(val))}"

                    feature_attributions.append(
                        {
                            "feature_name": feat_name,
                            "shap_value": val,
                            "feature_value": str(df_enriched.iloc[0].get(feat_name, "N/A")),
                            "impact_direction": impact_dir,
                            "description": desc,
                        }
                    )

                # Sort by absolute magnitude
                sorted_attrs = sorted(feature_attributions, key=lambda x: abs(x["shap_value"]), reverse=True)
                top_pos = [f"{x['feature_name']} (+{format_price_pkr(x['shap_value'])})" for x in sorted_attrs if x["shap_value"] > 0][:4]
                top_neg = [f"{x['feature_name']} (-{format_price_pkr(abs(x['shap_value']))})" for x in sorted_attrs if x["shap_value"] < 0][:3]
            except Exception as e:
                print(f"[SHAP Warning] Valuation SHAP computation error: {e}")

        # Plain language UrduLish explanation
        soc = df_enriched["area_society"].iloc[0]
        size = df_enriched["area_marla"].iloc[0]
        prop_type = df_enriched["property_type"].iloc[0]
        pred_fmt = base_pred["predicted_price_formatted"]
        range_fmt = base_pred["price_range_formatted"]

        urdu_drivers = []
        if df_enriched["is_corner"].iloc[0] == "yes":
            urdu_drivers.append("corner plot premium")
        if df_enriched["is_park_facing"].iloc[0] == "yes":
            urdu_drivers.append("park facing view")
        if df_enriched["age_years"].iloc[0] <= 2:
            urdu_drivers.append("brand-new modern construction")
        if not urdu_drivers:
            urdu_drivers.append("locality demand aur covered area")

        drivers_str = " aur ".join(urdu_drivers)
        urdulish_text = (
            f"Model ke mutabiq {soc} mein {size} Marla {prop_type} ki fair value {range_fmt} "
            f"(benchmark: {pred_fmt}) ke darmiyan hai. Sab se bara asar location, plot size, aur {drivers_str} ka hai."
        )

        eng_text = (
            f"According to the valuation model, the estimated fair market price for this {size} Marla {prop_type} "
            f"in {soc} is {pred_fmt} (confidence range {range_fmt}). Key positive drivers include {', '.join(top_pos[:2]) or 'prime locality benchmark'}."
        )

        return {
            "prediction_id": pred_id,
            "predicted_price_pkr": base_pred["predicted_price_pkr"],
            "predicted_price_formatted": pred_fmt,
            "base_value_pkr": base_val,
            "base_value_formatted": format_price_pkr(base_val),
            "feature_attributions": feature_attributions[:10],
            "top_positive_drivers": top_pos,
            "top_negative_drivers": top_neg,
            "waterfall_summary": f"Base Valuation {format_price_pkr(base_val)} -> Net Property Value {pred_fmt}",
            "urdulish_explanation": urdulish_text,
            "english_explanation": eng_text,
            "disclaimer": LEGAL_DISCLAIMER,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Singleton instance
valuation_service = PropertyValuationService()
