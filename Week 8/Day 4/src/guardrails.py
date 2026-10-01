"""Task 5: Guardrails, Out-of-Distribution (OOD) Checks, Prompt-Injection Defense, & Audit Logging.
Enforces rigorous runtime safety, compliance disclaimers, and full traceability.
"""
from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from src.config import (
    AUDIT_DB_PATH,
    AUDIT_LOG_JSONL,
    LEGAL_DISCLAIMER,
    OOD_LIMITS,
    VALID_CITIES,
    VALID_LEAD_SOURCES,
    VALID_PROPERTY_TYPES,
)


class OutOfDistributionError(ValueError):
    """Raised when request features fall outside the validated historical model distribution."""
    pass


class PromptInjectionError(ValueError):
    """Raised when an adversarial prompt attempt is detected."""
    pass


# ============================================================================
# Out-of-Distribution (OOD) Validation
# ============================================================================

def validate_property_ood(features: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate property parameters against empirical distribution bounds."""
    # City check
    city = str(features.get("city", "")).strip().title()
    if city not in VALID_CITIES:
        return False, f"OOD Rejection: City '{city}' is outside trained coverage {VALID_CITIES}."

    # Area marla check
    try:
        area_marla = float(features.get("area_marla", 0))
    except (ValueError, TypeError):
        return False, "OOD Rejection: area_marla must be a valid numeric quantity."

    if area_marla < OOD_LIMITS["min_area_marla"]:
        return False, f"OOD Rejection: area_marla ({area_marla}) must be >= {OOD_LIMITS['min_area_marla']} Marla."
    if area_marla > OOD_LIMITS["max_area_marla"]:
        return False, (
            f"OOD Rejection: Property area ({area_marla} Marla) exceeds model domain threshold "
            f"({OOD_LIMITS['max_area_marla']} Marla / 5 Kanal). Outliers require certified human appraisal."
        )

    # Bedrooms check
    bedrooms = features.get("bedrooms")
    if bedrooms is not None:
        try:
            b = int(bedrooms)
            if b < OOD_LIMITS["min_bedrooms"] or b > OOD_LIMITS["max_bedrooms"]:
                return False, f"OOD Rejection: Bedrooms ({b}) outside residential bounds [{OOD_LIMITS['min_bedrooms']}-{OOD_LIMITS['max_bedrooms']}]."
        except (ValueError, TypeError):
            return False, "OOD Rejection: bedrooms must be a valid integer."

    # Bathrooms check
    bathrooms = features.get("bathrooms")
    if bathrooms is not None:
        try:
            b = int(bathrooms)
            if b < OOD_LIMITS["min_bathrooms"] or b > OOD_LIMITS["max_bathrooms"]:
                return False, f"OOD Rejection: Bathrooms ({b}) outside bounds [{OOD_LIMITS['min_bathrooms']}-{OOD_LIMITS['max_bathrooms']}]."
        except (ValueError, TypeError):
            return False, "OOD Rejection: bathrooms must be a valid integer."

    # Age check
    age_years = features.get("age_years")
    if age_years is not None:
        try:
            a = int(age_years)
            if a < OOD_LIMITS["min_age_years"] or a > OOD_LIMITS["max_age_years"]:
                return False, f"OOD Rejection: age_years ({a}) outside valid span [{OOD_LIMITS['min_age_years']}-{OOD_LIMITS['max_age_years']}]."
        except (ValueError, TypeError):
            return False, "OOD Rejection: age_years must be a valid integer."

    # Listed price check (if present)
    listed = features.get("listed_price_pkr")
    if listed is not None:
        try:
            lp = float(listed)
            if lp < OOD_LIMITS["min_price_pkr"] or lp > OOD_LIMITS["max_price_pkr"]:
                return False, (
                    f"OOD Rejection: Listed price PKR {lp:,.0f} outside operational limits "
                    f"[PKR {OOD_LIMITS['min_price_pkr']:,.0f} - PKR {OOD_LIMITS['max_price_pkr']:,.0f}]."
                )
        except (ValueError, TypeError):
            return False, "OOD Rejection: listed_price_pkr must be a valid numeric amount."

    return True, None


def validate_lead_ood(features: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate sales lead parameters against funnel bounds."""
    # City check
    city = str(features.get("preferred_city", "")).strip().title()
    if city not in VALID_CITIES:
        return False, f"OOD Rejection: Preferred city '{city}' outside trained coverage {VALID_CITIES}."

    # Budget check
    try:
        budget = float(features.get("budget_pkr", 0))
    except (ValueError, TypeError):
        return False, "OOD Rejection: budget_pkr must be a valid numeric amount."

    if budget < OOD_LIMITS["min_budget_pkr"]:
        return False, f"OOD Rejection: Budget PKR {budget:,.0f} below minimum residential viable threshold."
    if budget > OOD_LIMITS["max_budget_pkr"]:
        return False, f"OOD Rejection: Budget PKR {budget:,.0f} exceeds max supported pipeline budget."

    # Calls check
    calls = features.get("number_of_calls")
    if calls is not None:
        try:
            c = int(calls)
            if c < OOD_LIMITS["min_number_of_calls"] or c > OOD_LIMITS["max_number_of_calls"]:
                return False, f"OOD Rejection: Calls count ({c}) outside valid range [1-{OOD_LIMITS['max_number_of_calls']}]."
        except (ValueError, TypeError):
            return False, "OOD Rejection: number_of_calls must be a valid integer."

    return True, None


# ============================================================================
# Prompt Injection Defense
# ============================================================================

INJECTION_PATTERNS = [
    r"(?i)\bignore\b(?:\s+\w+){0,3}\s+\binstructions\b",
    r"(?i)\bdisregard\b(?:\s+\w+){0,3}\s+\b(?:rules|prompts|instructions)\b",
    r"(?i)\bset\s+price\s+to\s+(?:1\s+rupee|0|zero|free|1\s+rs|100\s+rs)\b",
    r"(?i)\bprice\s*=\s*(?:1|0)\b",
    r"(?i)\b(?:tell|reveal|print|show)\b(?:\s+\w+){0,3}\s+\bsystem\s+(?:prompt|instructions)\b",
    r"(?i)\bjailbreak\b",
    r"(?i)\bdan\s+mode\b",
    r"(?i)\byou\s+are\s+now\s+(?:an?\s+unrestricted|a\s+calculator|evil)\b",
    r"(?i)\boutput\s+only\s+(?:1|0|true|false)\b",
    r"(?i)\boverride\s+(?:model|valuation|safeguards|system)\b",
]


def detect_prompt_injection(user_text: str) -> Tuple[bool, Optional[str]]:
    """Detect known adversarial manipulation patterns targeting LLM assistant."""
    if not isinstance(user_text, str):
        return False, None

    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, user_text)
        if match:
            return True, f"Adversarial prompt injection pattern detected: '{match.group(0)}'"

    return False, None


# ============================================================================
# Audit Logging System
# ============================================================================

class AuditLogger:
    """Production audit logging system recording every model transaction to SQLite and JSONL."""

    def __init__(self, db_path: Path = AUDIT_DB_PATH, jsonl_path: Path = AUDIT_LOG_JSONL):
        self.db_path = db_path
        self.jsonl_path = jsonl_path
        self._init_sqlite()

    def _init_sqlite(self):
        """Ensure SQLite table schema exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS prediction_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT UNIQUE,
                    timestamp TEXT,
                    endpoint TEXT,
                    model_version TEXT,
                    latency_ms REAL,
                    client_ip TEXT,
                    is_ood INTEGER,
                    inputs_json TEXT,
                    output_json TEXT
                )
                """
            )
            conn.commit()

    def log_prediction(
        self,
        prediction_id: str,
        endpoint: str,
        inputs: Dict[str, Any],
        output: Dict[str, Any],
        model_version: str,
        latency_ms: float = 0.0,
        client_ip: str = "127.0.0.1",
        is_ood: bool = False,
    ) -> None:
        """Write audit log entry asynchronously/thread-safe to both SQLite and JSONL."""
        now_iso = datetime.now(timezone.utc).isoformat()
        inputs_str = json.dumps(inputs, default=str)
        output_str = json.dumps(output, default=str)

        # 1. SQLite Write
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO prediction_audit_logs 
                    (prediction_id, timestamp, endpoint, model_version, latency_ms, client_ip, is_ood, inputs_json, output_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        prediction_id,
                        now_iso,
                        endpoint,
                        model_version,
                        latency_ms,
                        client_ip,
                        1 if is_ood else 0,
                        inputs_str,
                        output_str,
                    ),
                )
                conn.commit()
        except Exception as e:
            # Fallback warning
            print(f"[AuditLogger Warning] SQLite write failed: {e}")

        # 2. JSONL Write
        try:
            entry = {
                "prediction_id": prediction_id,
                "timestamp": now_iso,
                "endpoint": endpoint,
                "model_version": model_version,
                "latency_ms": latency_ms,
                "client_ip": client_ip,
                "is_ood": is_ood,
                "inputs": inputs,
                "output": output,
            }
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, default=str) + "\n")
        except Exception as e:
            print(f"[AuditLogger Warning] JSONL write failed: {e}")

    def get_recent_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent predictions for audit dashboard and compliance checks."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT prediction_id, timestamp, endpoint, model_version, latency_ms, client_ip, is_ood, inputs_json, output_json
                FROM prediction_audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            logs = []
            for r in rows:
                logs.append(
                    {
                        "prediction_id": r["prediction_id"],
                        "timestamp": r["timestamp"],
                        "endpoint": r["endpoint"],
                        "model_version": r["model_version"],
                        "latency_ms": r["latency_ms"],
                        "client_ip": r["client_ip"],
                        "is_ood": bool(r["is_ood"]),
                        "inputs": json.loads(r["inputs_json"]) if r["inputs_json"] else {},
                        "output": json.loads(r["output_json"]) if r["output_json"] else {},
                    }
                )
            return logs

    def get_audit_summary(self) -> Dict[str, Any]:
        """Return total counts and latency statistics across served endpoints."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), AVG(latency_ms) FROM prediction_audit_logs")
            total, avg_lat = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM prediction_audit_logs WHERE is_ood = 1")
            ood_count = cursor.fetchone()[0]
            return {
                "total_predictions_logged": total or 0,
                "average_latency_ms": round(avg_lat or 0.0, 2),
                "out_of_distribution_refusals": ood_count or 0,
            }


# Singleton instance
audit_logger = AuditLogger()
