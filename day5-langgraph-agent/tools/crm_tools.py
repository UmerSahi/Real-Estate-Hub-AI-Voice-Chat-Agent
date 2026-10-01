"""Task 3: CRM Persistence & Lead Management Tool.

Provides database logging for CRM leads, appointment records, reminders,
and client interaction history.
"""
from __future__ import annotations

import datetime
import json
import random
import re
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import Boolean, Column, Float, Integer, MetaData, String, Table, Text, create_engine, select, text
from langchain_core.tools import tool

from config import get_engine

metadata = MetaData()

crm_leads = Table(
    "crm_leads",
    metadata,
    Column("lead_id", String(64), primary_key=True),
    Column("client_name", String(128)),
    Column("phone", String(64)),
    Column("email", String(128)),
    Column("city", String(64)),
    Column("budget", String(64)),
    Column("property_type", String(64)),
    Column("purpose", String(32)),
    Column("stage", String(64)),
    Column("preferences_json", Text),
    Column("created_at", String(64)),
    Column("updated_at", String(64)),
)

crm_appointments = Table(
    "crm_appointments",
    metadata,
    Column("appointment_id", String(64), primary_key=True),
    Column("lead_id", String(64)),
    Column("client_name", String(128)),
    Column("client_phone", String(64)),
    Column("property_id", String(64)),
    Column("property_title", String(256)),
    Column("agent_name", String(128)),
    Column("date_str", String(64)),
    Column("time_str", String(64)),
    Column("status", String(32)),
    Column("calendar_event_id", String(64)),
    Column("calendar_link", Text),
    Column("notes", Text),
    Column("created_at", String(64)),
    Column("updated_at", String(64)),
)

voice_lead_scores = Table(
    "voice_lead_scores",
    metadata,
    Column("call_id", String(64), primary_key=True),
    Column("caller_id", String(64)),
    Column("duration_sec", Integer),
    Column("budget_pkr", Float),
    Column("city", String(64)),
    Column("society", String(64)),
    Column("purpose", String(32)),
    Column("visit_booked", String(16)),
    Column("conversion_score_pct", Integer),
    Column("tier", String(32)),
    Column("customer_persona", String(128)),
    Column("action_plan", Text),
    Column("recommended_pitch", Text),
    Column("transcript_summary", Text),
    Column("hot_lead_alert_triggered", Boolean),
    Column("email_dispatched", Boolean),
    Column("assigned_employee_email", String(128)),
    Column("email_subject", String(256)),
    Column("email_body", Text),
    Column("created_at", String(64)),
)


def init_crm_tables():
    """Ensure CRM tables exist."""
    try:
        engine = get_engine()
        metadata.create_all(engine)
    except Exception:
        pass


init_crm_tables()


def upsert_lead(
    client_name: str = "",
    phone: str = "",
    email: str = "",
    city: str = "",
    budget: str = "",
    property_type: str = "",
    purpose: str = "For Sale",
    stage: str = "Qualified",
    preferences: Optional[Dict[str, Any]] = None,
    lead_id: Optional[str] = None,
    name: Optional[str] = None,
    requirements: Optional[str] = None,
    source: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Create or update a client lead record in CRM."""
    engine = get_engine()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    client_name = client_name or name or "Valued Client"

    prefs = dict(preferences or {})
    if requirements:
        prefs["requirements"] = requirements
    if source:
        prefs["source"] = source
    for k, v in kwargs.items():
        prefs[k] = v
    prefs_str = json.dumps(prefs, ensure_ascii=False)

    with engine.begin() as conn:
        existing = None
        if lead_id:
            res = conn.execute(select(crm_leads).where(crm_leads.c.lead_id == lead_id))
            existing = res.mappings().first()
        elif phone and phone != "Not Provided":
            res = conn.execute(select(crm_leads).where(crm_leads.c.phone == phone))
            existing = res.mappings().first()

        if existing:
            target_id = existing["lead_id"]
            conn.execute(
                crm_leads.update()
                .where(crm_leads.c.lead_id == target_id)
                .values(
                    client_name=client_name or existing["client_name"],
                    email=email or existing["email"],
                    city=city or existing["city"],
                    budget=budget or existing["budget"],
                    property_type=property_type or existing["property_type"],
                    purpose=purpose or existing["purpose"],
                    stage=stage or existing["stage"],
                    preferences_json=prefs_str if prefs else existing["preferences_json"],
                    updated_at=now_iso,
                )
            )
            return target_id
        else:
            target_id = lead_id or f"lead_{uuid.uuid4().hex[:10]}"
            conn.execute(
                crm_leads.insert().values(
                    lead_id=target_id,
                    client_name=client_name or "New Client",
                    phone=phone or "Not Provided",
                    email=email or "",
                    city=city or "",
                    budget=budget or "",
                    property_type=property_type or "",
                    purpose=purpose or "For Sale",
                    stage=stage,
                    preferences_json=prefs_str,
                    created_at=now_iso,
                    updated_at=now_iso,
                )
            )
            return target_id


def generate_appointment_id() -> str:
    """Generate a clean, memorable Appointment ID formatted as APT-XXXX (e.g. APT-1042)."""
    engine = get_engine()
    for _ in range(30):
        candidate = f"APT-{random.randint(1001, 9999)}"
        try:
            with engine.connect() as conn:
                existing = conn.execute(
                    select(crm_appointments.c.appointment_id).where(crm_appointments.c.appointment_id == candidate)
                ).first()
                if not existing:
                    return candidate
        except Exception:
            return candidate
    return f"APT-{random.randint(10000, 99999)}"


def log_appointment(
    lead_id: str,
    client_name: str,
    client_phone: str,
    property_id: str,
    property_title: str,
    agent_name: str,
    date_str: str,
    time_str: str,
    status: str = "scheduled",
    calendar_event_id: str = "",
    calendar_link: str = "",
    notes: str = "",
    appointment_id: Optional[str] = None,
) -> str:
    """Log new or updated appointment into CRM."""
    engine = get_engine()
    appt_id = appointment_id or generate_appointment_id()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with engine.begin() as conn:
        res = conn.execute(select(crm_appointments).where(crm_appointments.c.appointment_id == appt_id))
        existing = res.mappings().first()
        if existing:
            conn.execute(
                crm_appointments.update()
                .where(crm_appointments.c.appointment_id == appt_id)
                .values(
                    date_str=date_str,
                    time_str=time_str,
                    status=status,
                    calendar_event_id=calendar_event_id or existing["calendar_event_id"],
                    calendar_link=calendar_link or existing["calendar_link"],
                    notes=notes or existing["notes"],
                    updated_at=now_iso,
                )
            )
        else:
            conn.execute(
                crm_appointments.insert().values(
                    appointment_id=appt_id,
                    lead_id=lead_id,
                    client_name=client_name,
                    client_phone=client_phone,
                    property_id=property_id,
                    property_title=property_title,
                    agent_name=agent_name,
                    date_str=date_str,
                    time_str=time_str,
                    status=status,
                    calendar_event_id=calendar_event_id,
                    calendar_link=calendar_link,
                    notes=notes,
                    created_at=now_iso,
                    updated_at=now_iso,
                )
            )
    return appt_id


def words_to_number_string(text: str) -> Optional[str]:
    """Convert spoken numbers (digit-by-digit, spaced digits, or natural compound) in English/Urdu into digit string.
    e.g. 'two zero nine four' -> '2094'
         'two thousand ninety four' -> '2094'
         'two thousand ninty four' -> '2094'
         'twenty ninety four' -> '2094'
         '2 0 9 4' -> '2094'
         'do sifar nau char' -> '2094'
         'do hazaar chauranway' -> '2094'
    """
    if not text or not str(text).strip():
        return None
    t = str(text).lower().strip()
    t = re.sub(r"[-_:,.]", " ", t)

    # 1. Direct digits with spaces: e.g. "2 0 9 4", "20 94", "2 094"
    digit_blocks = re.findall(r"\b(?:\d\s*){3,6}\b", t)
    for block in digit_blocks:
        clean = re.sub(r"\s+", "", block)
        if 3 <= len(clean) <= 6:
            return clean

    # Single-digit word map
    DIGIT_MAP = {
        # 0
        "zero": "0", "o": "0", "oh": "0", "sifar": "0", "sefar": "0", "safer": "0", "zeero": "0", "صفر": "0",
        # 1
        "one": "1", "won": "1", "ek": "1", "aik": "1", "ایک": "1",
        # 2
        "two": "2", "to": "2", "too": "2", "do": "2", "doo": "2", "دو": "2",
        # 3
        "three": "3", "tree": "3", "teen": "3", "tin": "3", "تین": "3",
        # 4
        "four": "4", "for": "4", "fore": "4", "char": "4", "chaar": "4", "چار": "4",
        # 5
        "five": "5", "fiv": "5", "panch": "5", "paanch": "5", "پانچ": "5",
        # 6
        "six": "6", "che": "6", "chhe": "6", "chhey": "6", "چھ": "6",
        # 7
        "seven": "7", "sat": "7", "saat": "7", "سات": "7",
        # 8
        "eight": "8", "ate": "8", "aath": "8", "ath": "8", "آٹھ": "8",
        # 9
        "nine": "9", "nayn": "9", "nau": "9", "no": "9", "نو": "9",
    }

    # 2. Check for digit-by-digit sequence in words (e.g. "two zero nine four", "do sifar nau char")
    tokens = t.split()
    current_digits = []
    best_digit_seq = ""

    for tok in tokens:
        if tok.isdigit():
            current_digits.append(tok)
        elif tok in DIGIT_MAP:
            current_digits.append(DIGIT_MAP[tok])
        else:
            if len("".join(current_digits)) >= 3:
                seq = "".join(current_digits)
                if 3 <= len(seq) <= 6:
                    best_digit_seq = seq
                    break
            current_digits = []

    if len("".join(current_digits)) >= 3:
        seq = "".join(current_digits)
        if 3 <= len(seq) <= 6:
            best_digit_seq = seq

    if best_digit_seq:
        return best_digit_seq

    # 3. Compound numbers (e.g. "two thousand ninety four", "twenty ninety four", "do hazaar chauranway")
    ONES = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
        "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
        "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
        # Urdu ones
        "ek": 1, "aik": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "panch": 5, "paanch": 5,
        "che": 6, "chhe": 6, "sat": 7, "saat": 7, "aath": 8, "ath": 8, "nau": 9, "das": 10,
        "gyara": 11, "bara": 12, "tera": 13, "chauda": 14, "pandra": 15, "sola": 16, "satra": 17, "athara": 18, "unnees": 19,
        # Urdu script
        "ایک": 1, "دو": 2, "تین": 3, "چار": 4, "پانچ": 5, "چھ": 6, "سات": 7, "آٹھ": 8, "نو": 9, "دس": 10,
    }
    TENS = {
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "ninty": 90,
        # Urdu tens
        "bees": 20, "tees": 30, "chalis": 40, "pachas": 50, "saath": 60, "sattar": 70, "assi": 80, "nawway": 90, "nave": 90,
        # Urdu compound 2-digit numbers
        "chauranway": 94, "choranwe": 94, "chauranve": 94, "چورانوے": 94,
        "bayalees": 42, "biyalees": 42, "بیالیس": 42,
        "banoe": 92, "banway": 92, "banve": 92,
        "ikyanway": 91, "tiranway": 93, "pichanway": 95, "chhiyanway": 96, "sattanway": 97, "athhanway": 98, "ninyanway": 99,
        # Urdu script
        "بیس": 20, "تیس": 30, "چالیس": 40, "پچاس": 50, "ساٹھ": 60, "ستر": 70, "اسی": 80, "نوے": 90,
    }
    MULTIPLIERS = {
        "hundred": 100, "sau": 100, "so": 100, "سو": 100,
        "thousand": 1000, "hazaar": 1000, "hazar": 1000, "ہزار": 1000,
    }

    def _eval_cluster(cluster: list) -> Optional[int]:
        total = 0
        current = 0
        has_number = False
        for word in cluster:
            if word in ("and", "aur", "اور"):
                continue
            if word.isdigit():
                v = int(word)
                has_number = True
                if v in (100, 1000):
                    current = (current if current else 1) * v
                else:
                    current += v
            elif word in MULTIPLIERS:
                has_number = True
                mult = MULTIPLIERS[word]
                if current == 0:
                    current = 1
                if mult >= 1000:
                    total += current * mult
                    current = 0
                else:
                    current *= mult
            elif word in TENS:
                has_number = True
                if current in (10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 40, 50, 60, 70, 80, 90) and not total:
                    total += current * 100
                    current = TENS[word]
                else:
                    current += TENS[word]
            elif word in ONES:
                has_number = True
                current += ONES[word]
        total += current
        return total if has_number else None

    cluster = []
    for tok in tokens:
        if (
            tok in ONES
            or tok in TENS
            or tok in MULTIPLIERS
            or tok in ("and", "aur", "اور")
            or tok.isdigit()
        ):
            cluster.append(tok)
        else:
            if cluster:
                val = _eval_cluster(cluster)
                if val and 1000 <= val <= 99999:
                    return str(val)
                cluster = []

    if cluster:
        val = _eval_cluster(cluster)
        if val and 1000 <= val <= 99999:
            return str(val)

    return None


def lookup_appointment(query: str) -> Optional[Dict[str, Any]]:
    """Flexible cross-call lookup of appointment by ID (APT-1042, 1042, apt-1042), spoken words, phone, or digits."""
    if not query or not str(query).strip():
        return None
    raw = str(query).strip()
    clean = raw.upper().replace(" ", "").replace("_", "-")

    possible_ids = [clean, raw]
    if clean.startswith("APT") and not clean.startswith("APT-"):
        possible_ids.append(clean.replace("APT", "APT-", 1))

    # Extract digits or spoken numbers (e.g. 'two zero nine four', 'two thousand ninety four', '2094')
    num_str = words_to_number_string(raw)
    m_num = re.search(r"\b(\d{3,6})\b", clean)
    extracted_digits = num_str or (m_num.group(1) if m_num else None)

    if extracted_digits:
        possible_ids.append(f"APT-{extracted_digits}")
        possible_ids.append(f"apt-{extracted_digits}")
        possible_ids.append(extracted_digits)

    engine = get_engine()
    try:
        with engine.connect() as conn:
            # 1. Exact or case-insensitive ID match
            for pid in possible_ids:
                row = conn.execute(
                    select(crm_appointments).where(
                        (crm_appointments.c.appointment_id == pid) |
                        (crm_appointments.c.appointment_id == pid.lower()) |
                        (crm_appointments.c.appointment_id == pid.upper())
                    )
                ).mappings().first()
                if row:
                    return dict(row)

            # 2. LIKE match on appointment_id digits
            if extracted_digits:
                row = conn.execute(
                    select(crm_appointments).where(
                        crm_appointments.c.appointment_id.like(f"%{extracted_digits}%")
                    ).order_by(crm_appointments.c.created_at.desc())
                ).mappings().first()
                if row:
                    return dict(row)

            # 3. Match by client phone number if phone provided
            clean_phone = re.sub(r"\D", "", raw)
            if len(clean_phone) >= 7:
                row = conn.execute(
                    select(crm_appointments).where(
                        crm_appointments.c.client_phone.like(f"%{clean_phone[-10:]}%")
                    ).order_by(crm_appointments.c.created_at.desc())
                ).mappings().first()
                if row:
                    return dict(row)
    except Exception:
        pass

    return None


def get_appointment(appointment_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an appointment record from CRM."""
    return lookup_appointment(appointment_id)



@tool
def crm_tool(
    action: str,  # 'upsert_lead', 'log_appointment', 'get_appointment'
    client_name: Optional[str] = "",
    phone: Optional[str] = "",
    city: Optional[str] = "",
    budget: Optional[str] = "",
    property_type: Optional[str] = "",
    lead_id: Optional[str] = None,
    appointment_id: Optional[str] = None,
    property_id: Optional[str] = "",
    property_title: Optional[str] = "",
    agent_name: Optional[str] = "Ahmed Raza",
    date_str: Optional[str] = "",
    time_str: Optional[str] = "",
    status: Optional[str] = "scheduled",
    calendar_link: Optional[str] = "",
    notes: Optional[str] = "",
) -> str:
    """Manage client leads and appointments in the CRM database."""
    action_clean = action.lower().strip()
    if action_clean == "upsert_lead":
        lid = upsert_lead(
            client_name=client_name or "Valued Client",
            phone=phone or "Not Provided",
            city=city or "",
            budget=budget or "",
            property_type=property_type or "",
            lead_id=lead_id,
        )
        return json.dumps({"status": "success", "lead_id": lid})
    elif action_clean == "log_appointment":
        aid = log_appointment(
            lead_id=lead_id or f"lead_{uuid.uuid4().hex[:8]}",
            client_name=client_name or "Valued Client",
            client_phone=phone or "Not Provided",
            property_id=property_id or "PROP-General",
            property_title=property_title or "Property Visit",
            agent_name=agent_name or "Ahmed Raza",
            date_str=date_str or "Tomorrow",
            time_str=time_str or "3:00 PM",
            status=status or "scheduled",
            calendar_link=calendar_link or "",
            notes=notes or "",
            appointment_id=appointment_id,
        )
        return json.dumps({"status": "success", "appointment_id": aid})
    elif action_clean == "get_appointment":
        appt = get_appointment(appointment_id or "")
        return json.dumps({"status": "success", "appointment": appt})

    return json.dumps({"error": f"Unknown CRM action '{action}'"})


# ============================================================================
# Post-Call Voice Lead Scoring Persistence & Stats (Task 4)
# ============================================================================

def save_voice_lead_score(data: Dict[str, Any]) -> bool:
    """Persist an automated voice call lead score and alert status."""
    engine = get_engine()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    cid = data.get("call_id") or f"CALL-{uuid.uuid4().hex[:8].upper()}"

    rec = {
        "call_id": cid,
        "caller_id": str(data.get("caller_id", "+923001234567")),
        "duration_sec": int(data.get("duration_sec") or data.get("call_duration_sec") or 180),
        "budget_pkr": float(data.get("budget_pkr") or 35_000_000.0),
        "city": str(data.get("city") or data.get("preferred_city") or "Lahore"),
        "society": str(data.get("society") or data.get("preferred_society") or "DHA Phase 6"),
        "purpose": str(data.get("purpose") or "buy"),
        "visit_booked": str(data.get("visit_booked") or "no"),
        "conversion_score_pct": int(data.get("conversion_score_pct") or 50),
        "tier": str(data.get("tier") or "Warm"),
        "customer_persona": str(data.get("customer_persona") or "Standard Family Buyer"),
        "action_plan": str(data.get("action_plan") or "Nurture follow-up"),
        "recommended_pitch": str(data.get("recommended_pitch") or ""),
        "transcript_summary": str(data.get("transcript_summary") or ""),
        "hot_lead_alert_triggered": bool(data.get("hot_lead_alert_triggered", False)),
        "email_dispatched": bool(data.get("email_dispatched", False)),
        "assigned_employee_email": str(data.get("assigned_employee_email") or "closer.vip@realestatehub.pk"),
        "email_subject": str(data.get("email_subject") or ""),
        "email_body": str(data.get("email_body") or ""),
        "created_at": data.get("created_at") or now_iso,
    }

    try:
        with engine.begin() as conn:
            exists_q = text("SELECT 1 FROM voice_lead_scores WHERE call_id = :cid")
            found = conn.execute(exists_q, {"cid": cid}).scalar()
            if found:
                update_cols = ", ".join(f"{k} = :{k}" for k in rec.keys() if k != "call_id")
                conn.execute(text(f"UPDATE voice_lead_scores SET {update_cols} WHERE call_id = :call_id"), rec)
            else:
                cols = ", ".join(rec.keys())
                placeholders = ", ".join(f":{k}" for k in rec.keys())
                conn.execute(text(f"INSERT INTO voice_lead_scores ({cols}) VALUES ({placeholders})"), rec)
        return True
    except Exception as err:
        print(f"[CRM Warning] Failed to save voice lead score: {err}")
        return False


def _seed_initial_voice_lead_scores():
    """Seed sample voice lead calls so the admin portal displays active data immediately."""
    engine = get_engine()
    samples = [
        {
            "call_id": "CALL-VIP-101",
            "caller_id": "+923009998877",
            "duration_sec": 310,
            "budget_pkr": 60000000.0,
            "city": "Lahore",
            "society": "DHA Phase 6",
            "purpose": "buy",
            "visit_booked": "yes",
            "conversion_score_pct": 85,
            "tier": "Hot",
            "customer_persona": "Luxury Villa Upgrader & HNI",
            "action_plan": "Immediate 15-minute VIP sales outreach",
            "recommended_pitch": "Highlight prime sector locations, corner park-facing plots, bespoke architecture, and privacy.",
            "transcript_summary": "VIP buyer completed walkthrough inquiry, ready for token transfer after Saturday viewing.",
            "hot_lead_alert_triggered": True,
            "email_dispatched": True,
            "assigned_employee_email": "closer.vip@realestatehub.pk",
            "email_subject": "🚨 [VIP HOT LEAD] CALL-VIP-101 — 85% Conversion Intent (SLA: < 15 minutes)",
            "email_body": (
                "FROM: automated-dispatch@realestatehub.pk\n"
                "TO: closer.vip@realestatehub.pk\n"
                "SUBJECT: 🚨 [VIP HOT LEAD] CALL-VIP-101 — 85% Conversion Intent (SLA: < 15 minutes)\n"
                "PRIORITY: HIGH (Immediate Action Required)\n\n"
                "Dear Senior Closer / Sales Director,\n\n"
                "A high-value prospect has just concluded an intake call with the Voice Agent.\n"
                "The ML Lead Scoring Model has classified this lead as 🔥 HOT with 85% conversion probability.\n\n"
                "📋 LEAD DETAILS:\n"
                "  • Call ID: CALL-VIP-101\n"
                "  • Caller Phone: +923009998877\n"
                "  • Customer Persona: Luxury Villa Upgrader & HNI\n"
                "  • Required SLA: < 15 minutes\n\n"
                "🎙️ CALL TRANSCRIPT SUMMARY:\n"
                "  \"VIP buyer completed walkthrough inquiry, ready for token transfer after Saturday viewing.\"\n\n"
                "💡 RECOMMENDED SALES PLAYBOOK & PITCH:\n"
                "  \"Highlight prime sector locations, corner park-facing plots, bespoke architecture, and privacy.\"\n\n"
                "🇵🇰 URDULISH REASONING:\n"
                "  \"Yeh lead 🔥 Hot hai (Conversion Probability: 85%). Wajah: site visit already booked hai, high budget (6.00 Crore), DHA Phase 6 priority. Recommended SLA: < 15 minutes ke andar Senior Closer call kare.\"\n"
            ),
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
        {
            "call_id": "CALL-WARM-102",
            "caller_id": "+923214567890",
            "duration_sec": 195,
            "budget_pkr": 25000000.0,
            "city": "Islamabad",
            "society": "F-10",
            "purpose": "buy",
            "visit_booked": "no",
            "conversion_score_pct": 54,
            "tier": "Warm",
            "customer_persona": "Mid-Tier Residential Buyer",
            "action_plan": "24-hour nurture follow-up via WhatsApp catalog",
            "recommended_pitch": "Present comparative price trends in F-10 and neighboring sectors.",
            "transcript_summary": "Inquired about 10 Marla houses in F-10, requested brochure and pricing breakdown.",
            "hot_lead_alert_triggered": False,
            "email_dispatched": False,
            "assigned_employee_email": "closer.vip@realestatehub.pk",
            "email_subject": "",
            "email_body": "",
            "created_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)).isoformat(),
        },
        {
            "call_id": "CALL-COLD-103",
            "caller_id": "+923331122334",
            "duration_sec": 70,
            "budget_pkr": 8000000.0,
            "city": "Rawalpindi",
            "society": "Bahria Town",
            "purpose": "rent",
            "visit_booked": "no",
            "conversion_score_pct": 24,
            "tier": "Cold",
            "customer_persona": "Low Intent Browser",
            "action_plan": "Automated SMS marketing campaign enrollment",
            "recommended_pitch": "Share monthly rental listings newsletter.",
            "transcript_summary": "Caller asked general rental questions for 5 Marla flat, no immediate move date.",
            "hot_lead_alert_triggered": False,
            "email_dispatched": False,
            "assigned_employee_email": "closer.vip@realestatehub.pk",
            "email_subject": "",
            "email_body": "",
            "created_at": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5)).isoformat(),
        },
    ]

    for s in samples:
        try:
            with engine.begin() as conn:
                exists = conn.execute(text("SELECT 1 FROM voice_lead_scores WHERE call_id = :cid"), {"cid": s["call_id"]}).scalar()
                if not exists:
                    cols = ", ".join(s.keys())
                    placeholders = ", ".join(f":{k}" for k in s.keys())
                    conn.execute(text(f"INSERT INTO voice_lead_scores ({cols}) VALUES ({placeholders})"), s)
        except Exception:
            pass


def get_voice_lead_scores(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all logged post-call lead scores."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            stmt = select(voice_lead_scores).order_by(voice_lead_scores.c.created_at.desc()).limit(limit)
            rows = conn.execute(stmt).mappings().all()
            if rows:
                return [dict(r) for r in rows]
    except Exception as err:
        print(f"[CRM Warning] Failed to fetch voice lead scores: {err}")

    # Seed initial sample entries if table is newly created
    _seed_initial_voice_lead_scores()
    try:
        with engine.connect() as conn:
            stmt = select(voice_lead_scores).order_by(voice_lead_scores.c.created_at.desc()).limit(limit)
            rows = conn.execute(stmt).mappings().all()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_voice_lead_stats() -> Dict[str, Any]:
    """Calculate aggregated stats for voice call lead scores."""
    scores = get_voice_lead_scores(limit=100)
    total = len(scores)
    hot = sum(1 for s in scores if s.get("tier") == "Hot" or s.get("hot_lead_alert_triggered"))
    warm = sum(1 for s in scores if s.get("tier") == "Warm")
    cold = sum(1 for s in scores if s.get("tier") == "Cold")
    dispatched = sum(1 for s in scores if s.get("email_dispatched"))
    avg_score = round(sum(s.get("conversion_score_pct", 0) for s in scores) / total, 1) if total > 0 else 0.0

    return {
        "total_calls_scored": total,
        "hot_leads_count": hot,
        "warm_leads_count": warm,
        "cold_leads_count": cold,
        "vip_email_alerts_sent": dispatched,
        "avg_conversion_score_pct": avg_score,
    }

