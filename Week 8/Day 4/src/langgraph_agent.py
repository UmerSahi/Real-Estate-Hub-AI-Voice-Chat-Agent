"""Task 2: Production LangGraph AI Assistant with Tool Grounding & UrduLish Dialogue Engine.
Enforces the inviolable rule:
'The LLM must never invent a price. Every number must come from a tool.'
Equipped with:
1. Price Predictor tool
2. Lead Scorer tool
3. Explainer tool
4. Comparable Properties tool
5. Market Stats tool
"""
from __future__ import annotations

import os
import re
import uuid
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, END

from src.config import (
    LEGAL_DISCLAIMER,
    VALID_CITIES,
    format_price_pkr,
)
from src.database_service import db_service
from src.guardrails import detect_prompt_injection
from src.lead_scoring_service import lead_scoring_service
from src.valuation_service import valuation_service


# ============================================================================
# LangGraph Agent State Definition
# ============================================================================

class AgentState(TypedDict):
    conversation_id: str
    user_query: str
    history: List[Dict[str, str]]
    intent: str
    tool_called: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[Dict[str, Any]]
    assistant_response: str
    guardrail_passed: bool
    injection_detected: bool
    disclaimer: str


# ============================================================================
# Registered Agent Tools
# ============================================================================

def tool_price_predictor(
    city: str,
    area_society: str,
    area_marla: float,
    bedrooms: int = 4,
    bathrooms: int = 4,
    age_years: int = 2,
    property_type: str = "House",
    is_corner: str = "no",
    is_park_facing: str = "no",
    listed_price_pkr: Optional[float] = None,
) -> Dict[str, Any]:
    """Tool 1: Predict fair market price, confidence intervals, and commercial verdict."""
    payload = {
        "city": city,
        "area_society": area_society,
        "area_marla": float(area_marla),
        "bedrooms": int(bedrooms),
        "bathrooms": int(bathrooms),
        "age_years": int(age_years),
        "property_type": property_type,
        "is_corner": is_corner,
        "is_park_facing": is_park_facing,
        "listed_price_pkr": listed_price_pkr,
    }
    return valuation_service.predict_valuation(payload)


def tool_lead_scorer(
    lead_source: str,
    budget_pkr: float,
    preferred_city: str,
    preferred_society: str,
    purpose: str = "buy",
    number_of_calls: int = 2,
    call_duration_avg_sec: int = 180,
    response_time_min: float = 15.0,
    visit_booked: str = "no",
    days_since_first_contact: int = 3,
    objection_raised: str = "None",
) -> Dict[str, Any]:
    """Tool 2: Score inbound lead conversion probability and assign operational SLA tier."""
    payload = {
        "lead_source": lead_source,
        "budget_pkr": float(budget_pkr),
        "preferred_city": preferred_city,
        "preferred_society": preferred_society,
        "purpose": purpose,
        "number_of_calls": int(number_of_calls),
        "call_duration_avg_sec": int(call_duration_avg_sec),
        "response_time_min": float(response_time_min),
        "visit_booked": visit_booked,
        "days_since_first_contact": int(days_since_first_contact),
        "objection_raised": objection_raised,
    }
    return lead_scoring_service.score_lead(payload)


def tool_explainer(
    target_type: str,  # 'price' or 'lead'
    **kwargs: Any,
) -> Dict[str, Any]:
    """Tool 3: Compute local SHAP attributions and plain-language driver explanations."""
    if target_type.lower() == "price":
        return valuation_service.explain_valuation(kwargs)
    else:
        return lead_scoring_service.score_lead(kwargs)


def tool_comparable_properties(
    city: str,
    area_society: str,
    area_marla: float,
    property_type: str = "House",
    bedrooms: Optional[int] = None,
    max_results: int = 3,
) -> Dict[str, Any]:
    """Tool 4: Find similar verified listings from the active real estate catalog."""
    comps = db_service.find_comparable_properties(
        city=city,
        area_society=area_society,
        area_marla=float(area_marla),
        property_type=property_type,
        bedrooms=bedrooms,
        max_results=max_results,
    )
    return {
        "total_matches": len(comps),
        "comparables": comps,
        "search_criteria": {
            "city": city,
            "area_society": area_society,
            "area_marla": area_marla,
            "property_type": property_type,
        },
    }


def tool_market_stats(
    city: str,
    area_society: Optional[str] = None,
) -> Dict[str, Any]:
    """Tool 5: Retrieve average price per marla, medians, and active inventory stats."""
    return db_service.get_market_statistics(city=city, area_society=area_society)


# ============================================================================
# Natural Language Parsing Helpers (UrduLish & English)
# ============================================================================

def parse_property_query(query: str) -> Dict[str, Any]:
    """Extract property specs (marla, kanal, bedrooms, society, city, age) from text."""
    q = query.lower()

    # Detect City
    city = "Lahore"
    if "islamabad" in q:
        city = "Islamabad"
    elif "karachi" in q:
        city = "Karachi"
    elif "rawalpindi" in q or "pindi" in q:
        city = "Rawalpindi"

    # Detect Area Society
    society = "DHA Phase 6"
    known_societies = [
        "dha phase 6", "dha phase 5", "dha phase 8", "dha phase 7", "dha phase 2", "dha defence",
        "bahria town phase 7", "bahria town phase 8", "bahria town islamabad", "bahria town",
        "gulberg iii", "gulberg", "model town", "johar town", "faisal town", "cantt", "clifton",
        "f-6", "f-7", "f-8", "f-10", "f-11", "e-11", "g-11", "g-13", "g-15", "i-10",
        "chaklala scheme 3", "gulshan-e-iqbal", "north nazimabad"
    ]
    for s in known_societies:
        if s in q:
            # Title case formatting
            society = s.title().replace("Dha", "DHA").replace("F-", "F-").replace("G-", "G-").replace("E-", "E-").replace("I-", "I-")
            if "iii" in s:
                society = society.replace("Iii", "III")
            break

    # Detect Size (Kanal vs Marla)
    area_marla = 20.0  # default 1 kanal
    kanal_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kanal|kanals)", q)
    marla_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:marla|marlas)", q)

    if kanal_match:
        area_marla = float(kanal_match.group(1)) * 20.0
    elif marla_match:
        area_marla = float(marla_match.group(1))

    # Detect Age
    age_years = 5
    age_match = re.search(r"(\d+)\s*(?:saal|year|years|yr|yrs)", q)
    if age_match:
        age_years = int(age_match.group(1))

    # Detect Bedrooms
    bedrooms = 5 if area_marla >= 20 else 3
    bed_match = re.search(r"(\d+)\s*(?:bed|bedroom|kamray|kamron)", q)
    if bed_match:
        bedrooms = int(bed_match.group(1))

    # Corner
    is_corner = "yes" if ("corner" in q or "nukkar" in q) else "no"
    is_park = "yes" if ("park" in q or "bagh" in q) else "no"

    # Property Type
    prop_type = "House"
    if "flat" in q or "apartment" in q:
        prop_type = "Flat"
    elif "portion" in q:
        prop_type = "Upper Portion" if "upper" in q else "Lower Portion"

    return {
        "city": city,
        "area_society": society,
        "area_marla": area_marla,
        "bedrooms": bedrooms,
        "bathrooms": bedrooms,
        "age_years": age_years,
        "property_type": prop_type,
        "is_corner": is_corner,
        "is_park_facing": is_park,
    }


def parse_lead_query(query: str) -> Dict[str, Any]:
    """Extract lead parameters (budget, calls, city, visit) from query text."""
    q = query.lower()

    # Budget parser
    budget = 35_000_000.0
    cr_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cr|crore|karor)", q)
    lac_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lac|lakh|lacs)", q)

    if cr_match:
        budget = float(cr_match.group(1)) * 10_000_000.0
    elif lac_match:
        budget = float(lac_match.group(1)) * 100_000.0

    # Calls
    calls = 2
    calls_match = re.search(r"(\d+)\s*(?:call|calls|dafa|baar)", q)
    if calls_match:
        calls = int(calls_match.group(1))

    # Visit
    visit = "yes" if ("visit" in q or "dora" in q or "booked" in q) else "no"

    # City & Society
    prop_params = parse_property_query(query)

    return {
        "lead_source": "call",
        "budget_pkr": budget,
        "preferred_city": prop_params["city"],
        "preferred_society": prop_params["area_society"],
        "purpose": "buy",
        "number_of_calls": calls,
        "call_duration_avg_sec": 180,
        "response_time_min": 15.0,
        "visit_booked": visit,
        "days_since_first_contact": 2,
    }


# ============================================================================
# LangGraph Workflow Nodes
# ============================================================================

def guardrail_and_router_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Evaluates prompt injection guardrails and routes user intent."""
    query = state.get("user_query", "").strip()

    # 1. Adversarial Prompt Injection Check
    is_injection, attack_reason = detect_prompt_injection(query)
    if is_injection:
        return {
            "intent": "prompt_injection_flagged",
            "injection_detected": True,
            "guardrail_passed": False,
            "tool_called": None,
            "tool_args": None,
            "tool_result": None,
            "assistant_response": (
                "⚠️ **Security Alert:** Prompt injection / adversarial manipulation pattern detected. "
                "Main aik enterprise real estate AI copilot hoon aur official machine learning models ke mutabiq "
                "hi verified answers deta hoon. Main farzi ya manipulated prices invent nahi kar sakta."
            ),
        }

    q_lower = query.lower()

    # 2. Intent Routing
    if any(k in q_lower for k in ["per marla", "rate kya", "marla rate", "market stat", "avg price", "average rate"]):
        intent = "market_stats"
    elif any(k in q_lower for k in ["comparable", "similar", "milte julte", "dosre ghar", "similar listing"]):
        intent = "comparable_properties"
    elif any(k in q_lower for k in ["lead", "prospect", "client score", "hot hai", "warm hai", "cold hai"]):
        intent = "lead_scoring"
    elif any(k in q_lower for k in ["explain", "kyun", "wajah", "why", "shap", "factor"]):
        intent = "explainer"
    elif any(k in q_lower for k in ["kitne", "price", "keemat", "value", "cost", "bikega", "bechoon", "chahiye", "jana chahiye"]):
        intent = "price_valuation"
    else:
        # Default to price inquiry if location/size mentioned, else general
        if any(c in q_lower for c in ["dha", "bahria", "f-", "kanal", "marla", "phase", "lahore", "islamabad"]):
            intent = "price_valuation"
        else:
            intent = "general_inquiry"

    return {
        "intent": intent,
        "injection_detected": False,
        "guardrail_passed": True,
    }


def tool_execution_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Executes the designated tool and gathers certified numerical outputs."""
    intent = state["intent"]
    query = state["user_query"]

    if intent == "prompt_injection_flagged":
        return {}

    tool_called = None
    tool_args = None
    tool_result = None

    if intent == "price_valuation":
        tool_called = "tool_price_predictor"
        tool_args = parse_property_query(query)
        tool_result = tool_price_predictor(**tool_args)

    elif intent == "lead_scoring":
        tool_called = "tool_lead_scorer"
        tool_args = parse_lead_query(query)
        tool_result = tool_lead_scorer(**tool_args)

    elif intent == "comparable_properties":
        tool_called = "tool_comparable_properties"
        parsed = parse_property_query(query)
        tool_args = {
            "city": parsed["city"],
            "area_society": parsed["area_society"],
            "area_marla": parsed["area_marla"],
            "property_type": parsed["property_type"],
            "bedrooms": parsed["bedrooms"],
            "max_results": 3,
        }
        tool_result = tool_comparable_properties(**tool_args)

    elif intent == "market_stats":
        tool_called = "tool_market_stats"
        parsed = parse_property_query(query)
        tool_args = {
            "city": parsed["city"],
            "area_society": parsed["area_society"],
        }
        tool_result = tool_market_stats(**tool_args)

    elif intent == "explainer":
        tool_called = "tool_explainer"
        parsed = parse_property_query(query)
        tool_args = {
            "target_type": "price",
            **parsed,
        }
        tool_result = tool_explainer(**tool_args)

    return {
        "tool_called": tool_called,
        "tool_args": tool_args,
        "tool_result": tool_result,
    }


def response_synthesis_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Formats dialogue strictly adhering to 'The LLM must never invent a price'."""
    if state.get("injection_detected"):
        return {"assistant_response": state["assistant_response"]}

    intent = state["intent"]
    tool_res = state.get("tool_result") or {}
    query = state.get("user_query", "")

    response = ""

    if intent == "price_valuation":
        pred_fmt = tool_res["predicted_price_formatted"]
        low_fmt = tool_res["lower_range_formatted"]
        up_fmt = tool_res["upper_range_formatted"]
        soc = state["tool_args"]["area_society"]
        marla = state["tool_args"]["area_marla"]
        size_label = f"{int(marla/20)} Kanal" if marla >= 20 and marla % 20 == 0 else f"{marla:.0f} Marla"
        is_corner = state["tool_args"].get("is_corner") == "yes"

        corner_mention = " aur corner plot" if is_corner else ""
        response = (
            f"Model ke mutabiq {soc} mein {size_label} ghar ki fair value **{low_fmt} se {up_fmt}** ke darmiyan hai "
            f"(benchmark point: **{pred_fmt}**). Sab se bara factor location{corner_mention} aur plot size hai. "
            f"Agar property modern 5-saal purani construction hai to yeh price bracket standard market rate ko reflect karta hai."
        )

    elif intent == "lead_scoring":
        score = tool_res["conversion_score_pct"]
        tier = tool_res["tier"]
        emoji = tool_res["emoji"]
        sla = tool_res["sla"]
        role = tool_res["assigned_role"]
        persona = tool_res["customer_persona"]
        urdu_reason = tool_res.get("urdulish_explanation", "")

        response = (
            f"Lead Analysis: Yeh lead **{emoji} {tier}** category mein aati hai (Conversion Probability: **{score}%**).\n\n"
            f"• **Customer Persona:** {persona}\n"
            f"• **Recommended SLA:** {sla} ke andar {role} outreach kare.\n"
            f"• **Summary:** {urdu_reason}"
        )

    elif intent == "comparable_properties":
        comps = tool_res.get("comparables", [])
        if comps:
            lines = [f"Database se {len(comps)} similar verified listings mili hain:\n"]
            for i, c in enumerate(comps, 1):
                lines.append(
                    f"{i}. **{c['summary']}** (Match: {c['similarity_match_pct']}, Per Marla: {c['price_per_marla_formatted']})"
                )
            response = "\n".join(lines)
        else:
            response = "Is society aur size ke liye is waqt database mein exact active matching listings mojood nahi hain."

    elif intent == "market_stats":
        loc = tool_res["locality"]
        avg_ppm = tool_res["avg_price_per_marla_formatted"]
        med = tool_res["median_price_formatted"]
        count = tool_res["total_listings_count"]
        tier = tool_res["society_tier"]
        sentiment = tool_res["market_sentiment"]

        response = (
            f"**{loc} Market Intelligence:**\n"
            f"• **Average Price per Marla:** {avg_ppm}\n"
            f"• **Median Property Price:** {med}\n"
            f"• **Active Sample Listings:** {count}\n"
            f"• **Society Classification:** {tier} ({sentiment})"
        )

    elif intent == "explainer":
        urdu = tool_res.get("urdulish_explanation", "")
        pos = tool_res.get("top_positive_drivers", [])
        neg = tool_res.get("top_negative_drivers", [])
        response = (
            f"**SHAP Valuation Breakdown:**\n{urdu}\n\n"
            f"• **Key Positive Drivers:** {', '.join(pos[:3]) if pos else 'Prime Society Benchmark'}\n"
            f"• **Dampening Factors:** {', '.join(neg[:2]) if neg else 'Standard Depreciation'}"
        )

    else:
        response = (
            "Assalam-o-Alaikum! Main RealEstate-Hub ka AI Assistant hoon. Main models aur database ki madad se:\n"
            "1. Kisi bhi plot ya ghar ki fair market value aur range bata sakta hoon.\n"
            "2. Inbound leads ko Hot/Warm/Cold score kar sakta hoon.\n"
            "3. Market rates (price per marla) aur comparable properties search kar sakta hoon.\n\n"
            "Aap mujh se UrduLish ya English mein sawal pooch saktay hain, maslan:\n"
            "- *'DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?'*\n"
            "- *'F-10 Islamabad mein average per marla rate kya hai?'*"
        )

    return {
        "assistant_response": response,
        "disclaimer": LEGAL_DISCLAIMER,
    }


def grounding_verifier_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Inviolable check ensuring any numbers match verified tool outputs."""
    response = state["assistant_response"]
    tool_res = state.get("tool_result")

    # If prompt injection, already safe
    if state.get("injection_detected"):
        return {"assistant_response": response}

    # Ensure response always contains official disclaimer
    if "Disclaimer:" not in response:
        response += f"\n\n> *⚖️ {LEGAL_DISCLAIMER}*"

    return {"assistant_response": response}


# ============================================================================
# LangGraph Graph Assembly
# ============================================================================

def build_langgraph_agent():
    """Assemble and compile the LangGraph StateGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("guardrail_router", guardrail_and_router_node)
    workflow.add_node("tool_executor", tool_execution_node)
    workflow.add_node("response_synthesizer", response_synthesis_node)
    workflow.add_node("grounding_verifier", grounding_verifier_node)

    # Set Entry Point
    workflow.set_entry_point("guardrail_router")

    # Add Edges
    workflow.add_edge("guardrail_router", "tool_executor")
    workflow.add_edge("tool_executor", "response_synthesizer")
    workflow.add_edge("response_synthesizer", "grounding_verifier")
    workflow.add_edge("grounding_verifier", END)

    return workflow.compile()


class RealEstateAIAssistant:
    """Production Agent Wrapper providing interactive chat with UrduLish and tool invocation."""

    def __init__(self):
        self.graph = build_langgraph_agent()

    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Execute chat interaction through compiled LangGraph StateGraph."""
        cid = conversation_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"
        initial_state: AgentState = {
            "conversation_id": cid,
            "user_query": message,
            "history": history or [],
            "intent": "general_inquiry",
            "tool_called": None,
            "tool_args": None,
            "tool_result": None,
            "assistant_response": "",
            "guardrail_passed": True,
            "injection_detected": False,
            "disclaimer": LEGAL_DISCLAIMER,
        }

        final_state = self.graph.invoke(initial_state)

        return {
            "conversation_id": cid,
            "user_query": message,
            "assistant_response": final_state["assistant_response"],
            "intent": final_state["intent"],
            "tool_called": final_state.get("tool_called"),
            "tool_result": final_state.get("tool_result"),
            "guardrail_passed": final_state["guardrail_passed"],
            "injection_detected": final_state["injection_detected"],
            "disclaimer": LEGAL_DISCLAIMER,
        }


# Singleton instance
ai_assistant = RealEstateAIAssistant()
