"""Task 3: Production Streamlit Real Estate AI Dashboard & Copilot.
Features:
1. Property Price Prediction Form with Quantile Confidence Range & Verdict
2. Lead List Sorted by Score with Hot / Warm / Cold Badges
3. SHAP Feature Attribution Waterfall & Plain-Language Explanations
4. Market Insights & Visual Analytics (Price per Marla, Conversion by Channel)
5. Interactive UrduLish AI Assistant powered by LangGraph Copilot
6. Week 7 Telephony Call Simulator & Governance Audit Logs
"""
from __future__ import annotations

import sys
from pathlib import Path
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Configure page layout and aesthetics
st.set_page_config(
    page_title="RealEstate-Hub AI | Enterprise Serving & Copilot",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add Day 4 root to path
DAY4_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAY4_DIR))

from src.config import (
    API_VERSION,
    LEGAL_DISCLAIMER,
    LEAD_MODEL_VERSION,
    VALUATION_MODEL_VERSION,
    VALID_CITIES,
    VALID_PROPERTY_TYPES,
    VALID_LEAD_SOURCES,
    VALID_PURPOSES,
    SOCIETY_TIERS,
    VAPI_ASSISTANT_ID,
    VAPI_PUBLIC_KEY,
    format_price_pkr,
)
from src.database_service import db_service
from src.guardrails import audit_logger, detect_prompt_injection
from src.langgraph_agent import ai_assistant
from src.lead_scoring_service import lead_scoring_service
from src.valuation_service import valuation_service
from src.voice_integration import voice_service

# Inject Vapi Web Calling Widget directly into main DOM (Native WebRTC, no iframe permissions block)
vapi_html_snippet = f"""
<div id="vapi-root-container" style="display:none;"></div>
<script>
  (function() {{
    if (window.__vapi_injected) return;
    window.__vapi_injected = true;
    var targetDoc = window.parent ? window.parent.document : document;
    var existing = targetDoc.getElementById("vapi-sdk-script");
    if (!existing) {{
      var script = targetDoc.createElement("script");
      script.id = "vapi-sdk-script";
      script.src = "https://cdn.jsdelivr.net/gh/VapiAI/html-script-tag@latest/dist/assets/index.js";
      script.async = true;
      script.onload = function() {{
        var win = targetDoc.defaultView || window;
        if (win.vapiSDK && !win.__vapi_btn_mounted) {{
          win.__vapi_btn_mounted = true;
          try {{
            win.vapiInstance = win.vapiSDK.run({{
              apiKey: "{VAPI_PUBLIC_KEY}",
              assistant: "{VAPI_ASSISTANT_ID}",
              config: {{
                position: "bottom-right",
                offset: "35px",
                width: "60px",
                height: "60px",
                idle: {{
                  color: "rgb(46, 160, 67)",
                  type: "pill",
                  title: "🎙️ Talk to Voice Agent",
                  subtitle: "Live UrduLish AI Call",
                  icon: "https://unpkg.com/lucide-static@0.321.0/icons/phone-call.svg"
                }},
                loading: {{
                  color: "rgb(210, 153, 34)",
                  type: "pill",
                  title: "Connecting to Vapi...",
                  subtitle: "Starting audio stream",
                  icon: "https://unpkg.com/lucide-static@0.321.0/icons/loader-2.svg"
                }},
                active: {{
                  color: "rgb(248, 81, 73)",
                  type: "pill",
                  title: "Call in Progress • Speak Now",
                  subtitle: "Click to End Call",
                  icon: "https://unpkg.com/lucide-static@0.321.0/icons/phone-off.svg"
                }}
              }}
            }});
            console.log("[Vapi Web SDK] Mounted successfully on top-level window");
          }} catch (err) {{
            console.error("[Vapi Web SDK Error]", err);
          }}
        }}
      }};
      (targetDoc.head || targetDoc.body).appendChild(script);
    }}
  }})();
</script>
"""
st.html(vapi_html_snippet, unsafe_allow_javascript=True)

# Custom Luxury Real Estate CSS Styling
st.markdown(
    """
    <style>
    /* Dark Luxury Theme Palette */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.95), rgba(33, 38, 45, 0.95));
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        margin-bottom: 15px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #58a6ff;
        margin: 5px 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .verdict-fair {
        background-color: rgba(46, 160, 67, 0.2);
        color: #3fb950;
        border: 1px solid #3fb950;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .verdict-overpriced {
        background-color: rgba(248, 81, 73, 0.2);
        color: #f85149;
        border: 1px solid #f85149;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .verdict-underpriced {
        background-color: rgba(56, 139, 253, 0.2);
        color: #58a6ff;
        border: 1px solid #58a6ff;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
    }
    .badge-hot {
        background: rgba(255, 69, 0, 0.2);
        color: #ff5722;
        border: 1px solid #ff5722;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-warm {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid #ffc107;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    .badge-cold {
        background: rgba(33, 150, 243, 0.2);
        color: #64b5f6;
        border: 1px solid #64b5f6;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: bold;
    }
    .disclaimer-banner {
        background: rgba(22, 27, 34, 0.85);
        border-left: 4px solid #d29922;
        padding: 12px 18px;
        border-radius: 6px;
        font-size: 0.82rem;
        color: #c9d1d9;
        margin-top: 25px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.title("🏢 RealEstate-Hub AI: Model Serving & Copilot")
st.caption(f"Production Serving Layer (v{API_VERSION}) • Quantile Regression • LightGBM Lead Scoring • LangGraph UrduLish Copilot")

# Sidebar Status & Navigation
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/real-estate.png", width=70)
    st.markdown("### **System Governance**")
    st.markdown(f"**Valuation Model:** `{VALUATION_MODEL_VERSION}`")
    st.markdown(f"**Lead Model:** `{LEAD_MODEL_VERSION}`")
    st.markdown(f"**Telephony Webhook:** `ACTIVE (Vapi/Week 7)`")
    st.markdown(f"**Database Size:** `{len(db_service.df):,} Verified Listings`")
    st.divider()

    st.markdown("### **Quick SLA Action Rules**")
    st.markdown("🔥 **Hot (>=70%):** Call < 15 min (Senior Closer)")
    st.markdown("🌤 **Warm (35-69%):** Callback < 2 hrs (Account Exec)")
    st.markdown("❄️ **Cold (<35%):** Automated Drip Nurture")
    st.divider()

    st.markdown("### **Legal Disclaimer**")
    st.info(LEGAL_DISCLAIMER)

# Main Navigation Tabs
tab_val, tab_leads, tab_shap, tab_eda, tab_chat, tab_telephony = st.tabs(
    [
        "🏷️ Property Valuation",
        "🔥 Lead Scoring Pipeline",
        "📊 SHAP Explainability",
        "📈 Market Insights (EDA)",
        "💬 UrduLish AI Assistant",
        "📞 Voice Integration & Audit",
    ]
)


# ============================================================================
# TAB 1: PROPERTY VALUATION
# ============================================================================
with tab_val:
    st.subheader("🏡 Automated Property Valuation Engine")
    st.write("Predict fair market price, confidence intervals (10th & 90th percentile bounds), and commercial listing verdict.")

    col_in1, col_in2, col_in3 = st.columns(3)
    with col_in1:
        city = st.selectbox("Metropolitan City", VALID_CITIES, index=0, key="val_city")
        society_list = sorted(list(SOCIETY_TIERS.keys()))
        society = st.selectbox("Housing Society / Sector", society_list, index=society_list.index("DHA Phase 6") if "DHA Phase 6" in society_list else 0)
        prop_type = st.selectbox("Property Type", VALID_PROPERTY_TYPES, index=0)

    with col_in2:
        unit = st.radio("Size Unit", ["Kanal", "Marla"], horizontal=True)
        if unit == "Kanal":
            size_val = st.number_input("Plot Size (Kanal)", min_value=0.1, max_value=5.0, value=1.0, step=0.5)
            marla_equiv = size_val * 20.0
        else:
            marla_equiv = st.number_input("Plot Size (Marla)", min_value=1.0, max_value=100.0, value=10.0, step=1.0)

        bedrooms = st.slider("Bedrooms", min_value=1, max_value=12, value=5 if marla_equiv >= 20 else 3)
        bathrooms = st.slider("Bathrooms", min_value=1, max_value=12, value=bedrooms)

    with col_in3:
        age_years = st.slider("Construction Age (Years)", min_value=0, max_value=30, value=3)
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            is_corner = st.checkbox("Corner Plot (+8% Premium)", value=True)
        with col_c2:
            is_park = st.checkbox("Park Facing", value=False)
        listed_price_cr = st.number_input("Asking / Listed Price in Crore (Optional)", min_value=0.0, max_value=50.0, value=8.5 if marla_equiv >= 20 else 3.2, step=0.1)

    if st.button("🚀 Calculate Valuation & Pricing Verdict", type="primary", use_container_width=True):
        listed_pkr = listed_price_cr * 10_000_000.0 if listed_price_cr > 0 else None
        prop_payload = {
            "city": city,
            "area_society": society,
            "area_marla": marla_equiv,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "age_years": age_years,
            "property_type": prop_type,
            "is_corner": "yes" if is_corner else "no",
            "is_park_facing": "yes" if is_park else "no",
            "listed_price_pkr": listed_pkr,
        }

        with st.spinner("Executing quantile regression models..."):
            res = valuation_service.predict_valuation(prop_payload)

        st.markdown("---")
        st.subheader("📋 Valuation Summary & Commercial Verdict")

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Fair Market Value</div>
                    <div class="metric-value">{res['predicted_price_formatted']}</div>
                    <div style="color: #8b949e; font-size: 0.8rem;">Point Estimate</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">10th - 90th% Range</div>
                    <div class="metric-value" style="font-size: 1.45rem; color: #79c0ff;">{res['price_range_formatted']}</div>
                    <div style="color: #8b949e; font-size: 0.8rem;">Confidence Interval</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m3:
            verdict_cls = "verdict-fair" if res["verdict"] == "Fair" else ("verdict-overpriced" if res["verdict"] == "Overpriced" else "verdict-underpriced")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Commercial Verdict</div>
                    <div style="margin-top: 10px;"><span class="{verdict_cls}">{res['verdict']} ({res['price_delta_pct']:+.1f}%)</span></div>
                    <div style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">vs Listed Price</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_m4:
            ppm_val = res["predicted_price_pkr"] / marla_equiv
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Unit Benchmark</div>
                    <div class="metric-value" style="font-size: 1.6rem; color: #d2a8ff;">{format_price_pkr(ppm_val)} / marla</div>
                    <div style="color: #8b949e; font-size: 0.8rem;">Standardized Rate</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.info(f"🗣 **Conversational Client Statement:** {res['client_explanation']}")


# ============================================================================
# TAB 2: LEAD SCORING PIPELINE
# ============================================================================
with tab_leads:
    st.subheader("🔥 Inbound Lead Conversion Pipeline")
    st.write("Prioritized lead inbox scored by conversion probability with operational SLA assignments.")

    # Load featured leads for display
    try:
        df_leads_raw = pd.read_csv(DAY4_DIR.parent / "Day 3" / "data" / "leads_featured.csv")
    except Exception:
        df_leads_raw = pd.DataFrame()

    if not df_leads_raw.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            city_filter = st.multiselect("Filter City", VALID_CITIES, default=VALID_CITIES)
        with col_f2:
            source_filter = st.multiselect("Filter Channel", VALID_LEAD_SOURCES, default=VALID_LEAD_SOURCES)
        with col_f3:
            visit_filter = st.selectbox("Visit Scheduled", ["All", "Yes", "No"], index=0)

        # Filter
        df_f = df_leads_raw[
            (df_leads_raw["preferred_city"].isin(city_filter))
            & (df_leads_raw["lead_source"].isin(source_filter))
        ].copy()

        if visit_filter == "Yes":
            df_f = df_f[df_f["visit_booked"] == "yes"]
        elif visit_filter == "No":
            df_f = df_f[df_f["visit_booked"] == "no"]

        # Predict scores on top 15 records
        scored_records = []
        for _, r in df_f.head(15).iterrows():
            lead_in = r.to_dict()
            lead_res = lead_scoring_service.score_lead(lead_in)
            scored_records.append(
                {
                    "Lead ID": lead_res["lead_id"],
                    "Tier": f"{lead_res['emoji']} {lead_res['tier']}",
                    "Score (%)": lead_res["conversion_score_pct"],
                    "Channel": lead_in.get("lead_source", "call"),
                    "City": lead_in.get("preferred_city", "Lahore"),
                    "Society": lead_in.get("preferred_society", "DHA Phase 6"),
                    "Budget": format_price_pkr(lead_in.get("budget_pkr", 20_000_000)),
                    "Calls": lead_in.get("number_of_calls", 1),
                    "Visit": lead_in.get("visit_booked", "no").upper(),
                    "SLA": lead_res["sla"],
                    "Persona": lead_res["customer_persona"],
                    "raw_res": lead_res,
                }
            )

        df_display = pd.DataFrame(scored_records).sort_values(by="Score (%)", ascending=False)

        # Metric cards
        hot_c = sum(1 for r in scored_records if "Hot" in r["Tier"])
        warm_c = sum(1 for r in scored_records if "Warm" in r["Tier"])
        cold_c = sum(1 for r in scored_records if "Cold" in r["Tier"])

        col_k1, col_k2, col_k3, col_k4 = st.columns(4)
        col_k1.metric("Total Inbound Queue", f"{len(scored_records)} Leads")
        col_k2.metric("🔥 Hot (VIP Closer)", f"{hot_c} Leads")
        col_k3.metric("🌤 Warm (Standard)", f"{warm_c} Leads")
        col_k4.metric("❄️ Cold (Nurture)", f"{cold_c} Leads")

        st.dataframe(
            df_display.drop(columns=["raw_res"]),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("🔍 Lead Deep Dive & Recommended Action Plan")
        selected_lead_id = st.selectbox("Inspect Lead Details", df_display["Lead ID"].tolist())
        selected_item = next(r for r in scored_records if r["Lead ID"] == selected_lead_id)
        raw_res = selected_item["raw_res"]

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Customer Persona:** `{raw_res['customer_persona']}`")
            st.markdown(f"**Assigned Closer Role:** `{raw_res['assigned_role']}`")
            st.markdown(f"**Contact Channel:** `{raw_res['channel']}`")
            st.markdown(f"**Recommended Sales Pitch:** *\"{raw_res['recommended_sales_pitch']}\"*")

        with col_d2:
            st.markdown(f"**UrduLish Business Reason:**")
            st.success(raw_res["urdulish_explanation"])
            st.markdown(f"**Action Plan:** {raw_res['action_plan']}")


# ============================================================================
# TAB 3: SHAP EXPLAINABILITY LAB
# ============================================================================
with tab_shap:
    st.subheader("📊 Local SHAP Feature Attribution Lab")
    st.write("Transparent feature contributions explaining exactly why a price or lead score was estimated.")

    shap_mode = st.radio("Explainability Target", ["Property Valuation Drivers", "Lead Conversion Drivers"], horizontal=True)

    if shap_mode == "Property Valuation Drivers":
        sample_prop = {
            "city": "Lahore",
            "area_society": "DHA Phase 6",
            "area_marla": 20.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "age_years": 5,
            "property_type": "House",
            "is_corner": "yes",
            "is_park_facing": "yes",
        }
        shap_res = valuation_service.explain_valuation(sample_prop)

        st.markdown(f"**Target Property:** 1 Kanal (20 Marla) House in DHA Phase 6 • **Fair Value:** `{shap_res['predicted_price_formatted']}`")
        st.info(f"🇵🇰 **UrduLish Natural Language Explanation:** {shap_res['urdulish_explanation']}")

        # Plot bar chart of top feature attributions
        attrs = shap_res.get("feature_attributions", [])
        if attrs:
            df_chart = pd.DataFrame(attrs).head(8)
            df_chart["value_lac"] = df_chart["shap_value"] / 100_000.0

            chart = (
                alt.Chart(df_chart)
                .mark_bar()
                .encode(
                    x=alt.X("value_lac:Q", title="Impact on Valuation (Lac PKR)"),
                    y=alt.Y("feature_name:N", sort="-x", title="Feature Name"),
                    color=alt.condition(
                        alt.datum.value_lac > 0,
                        alt.value("#2ea043"),  # Positive green
                        alt.value("#f85149"),  # Negative red
                    ),
                    tooltip=["feature_name", "value_lac", "impact_direction", "description"],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)

    else:
        sample_lead = {
            "lead_source": "call",
            "budget_pkr": 45_000_000,
            "preferred_city": "Lahore",
            "preferred_society": "DHA Phase 6",
            "purpose": "buy",
            "number_of_calls": 3,
            "call_duration_avg_sec": 240,
            "response_time_min": 10.0,
            "visit_booked": "yes",
            "days_since_first_contact": 2,
        }
        lead_shap = lead_scoring_service.score_lead(sample_lead)
        st.markdown(f"**Lead Target:** Budget 4.5 Crore, 3 Calls, Visit Booked • **Score:** `{lead_shap['conversion_score_pct']}%` ({lead_shap['tier']})")
        st.info(f"🇵🇰 **UrduLish Natural Language Explanation:** {lead_shap['urdulish_explanation']}")

        attrs = lead_shap.get("feature_attributions", [])
        if attrs:
            df_lead_chart = pd.DataFrame(attrs).head(8)
            chart = (
                alt.Chart(df_lead_chart)
                .mark_bar()
                .encode(
                    x=alt.X("shap_value:Q", title="SHAP Impact on Conversion Probability"),
                    y=alt.Y("feature_name:N", sort="-x", title="Interaction Feature"),
                    color=alt.condition(
                        alt.datum.shap_value > 0,
                        alt.value("#ff5722"),
                        alt.value("#58a6ff"),
                    ),
                    tooltip=["feature_name", "shap_value", "impact_direction"],
                )
                .properties(height=320)
            )
            st.altair_chart(chart, use_container_width=True)


# ============================================================================
# TAB 4: MARKET INSIGHTS (EDA)
# ============================================================================
with tab_eda:
    st.subheader("📈 Real Estate Marketplace Analytics & Insights")
    st.write("Aggregated trends and distributions derived from verified portal transactions.")

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("#### **Average Price per Marla by Housing Society (Lahore & Islamabad)**")
        top_socs = db_service.df.groupby("area_society")["price_per_marla"].mean().reset_index()
        top_socs = top_socs.sort_values(by="price_per_marla", ascending=False).head(12)
        top_socs["ppm_lac"] = top_socs["price_per_marla"] / 100_000.0

        chart_ppm = (
            alt.Chart(top_socs)
            .mark_bar(color="#58a6ff")
            .encode(
                x=alt.X("ppm_lac:Q", title="Price per Marla (Lac PKR)"),
                y=alt.Y("area_society:N", sort="-x", title="Society"),
                tooltip=["area_society", "ppm_lac"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_ppm, use_container_width=True)

    with col_e2:
        st.markdown("#### **Median Property Valuation Across Cities**")
        city_stats = db_service.df.groupby("city")["price_pkr"].median().reset_index()
        city_stats["price_crore"] = city_stats["price_pkr"] / 10_000_000.0

        chart_city = (
            alt.Chart(city_stats)
            .mark_bar(color="#3fb950")
            .encode(
                x=alt.X("city:N", title="City"),
                y=alt.Y("price_crore:Q", title="Median Listing Price (Crore PKR)"),
                tooltip=["city", "price_crore"],
            )
            .properties(height=350)
        )
        st.altair_chart(chart_city, use_container_width=True)


# ============================================================================
# TAB 5: AI ASSISTANT (URDULISH COPILOT)
# ============================================================================
with tab_chat:
    st.subheader("💬 RealEstate-Hub AI Assistant (UrduLish Copilot)")
    st.write("An intelligent LangGraph agent that answers questions in UrduLish and strictly binds all prices to verified ML tools.")

    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "Assalam-o-Alaikum! Main RealEstate-Hub ka AI Copilot hoon. "
                    "Aap mujh se UrduLish ya English mein kisi bhi property ki fair value, "
                    "market rate per marla, comparable listings, ya lead qualification ke baray mein pooch saktay hain.\n\n"
                    "**Sample:** *'DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?'*"
                ),
            }
        ]

    # Quick prompt buttons
    st.markdown("**Quick Prompts:**")
    qp_col1, qp_col2, qp_col3, qp_col4 = st.columns(4)
    prompt_to_send = None

    if qp_col1.button("🏷️ DHA 6 1-Kanal Price?", use_container_width=True):
        prompt_to_send = "DHA Phase 6 mein 1 kanal, 5 saal purana ghar, kitne ka jana chahiye?"
    if qp_col2.button("📈 F-10 Per Marla Rate?", use_container_width=True):
        prompt_to_send = "F-10 Islamabad mein average per marla rate kya hai?"
    if qp_col3.button("🔍 DHA 6 Similar Listings?", use_container_width=True):
        prompt_to_send = "DHA Phase 6 Lahore mein 20 marla ke similar ghar dikhao"
    if qp_col4.button("🔥 Score Inbound Lead?", use_container_width=True):
        prompt_to_send = "Yeh lead kesi hai: budget 5 crore, 3 calls, visit booked hai?"

    # Display chat history
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Ask a real estate question in UrduLish...") or prompt_to_send

    if user_input:
        st.session_state["chat_messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("LangGraph agent routing & executing tools..."):
                chat_res = ai_assistant.chat(user_input)

            st.markdown(chat_res["assistant_response"])
            st.session_state["chat_messages"].append(
                {"role": "assistant", "content": chat_res["assistant_response"]}
            )

            # Tool Execution Trace
            if chat_res.get("tool_called"):
                with st.expander(f"🛠️ Tool Execution Trace (`{chat_res['tool_called']}`)", expanded=False):
                    st.json(chat_res.get("tool_result"))


# ============================================================================
# TAB 6: VOICE INTEGRATION & AUDIT
# ============================================================================
with tab_telephony:
    st.subheader("📞 Week 7 Voice Telephony Integration & Governance Audit")
    st.write("Live WebRTC browser calls, telephony webhook simulation, automated email dispatchers, and system audit logs.")

    # Live Interactive Voice Calling Station
    st.markdown("### 🎙️ Live In-App Voice Call Console")
    st.markdown(
        "Direct WebRTC audio link with Week 7 Voice Agent (Deepgram Nova-3 + Gemini Voice Engine). "
        "Talk to the agent in UrduLish through your microphone right inside this dashboard."
    )

    c_top1, c_top2 = st.columns([3, 1])
    with c_top1:
        st.info("💡 **How to Call:** Click the green phone button below, allow microphone access when prompted, and ask in UrduLish: *'Mera DHA Phase 6 mein 1 kanal ghar kitne ka bikega?'*")
    with c_top2:
        st.link_button("🌐 Open Dedicated Call Window", "http://127.0.0.1:8000/call", use_container_width=True, type="secondary")

    # Primary: Live interactive iframe with native microphone permissions
    components.iframe("http://127.0.0.1:8000/call", height=730, scrolling=False)

    st.markdown("---")


    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.markdown("#### **Simulate Inbound Voice Call Completion**")
        sim_caller = st.text_input("Caller Phone", "+923009988776")
        sim_dur = st.number_input("Call Duration (Seconds)", value=320, step=30)
        sim_budget_cr = st.number_input("Declared Budget (Crore)", value=5.5, step=0.5)
        sim_soc = st.selectbox("Preferred Society", ["DHA Phase 6", "Bahria Town", "F-10", "Gulberg III"])
        sim_visit = st.selectbox("Site Visit Booked by Voice Agent?", ["yes", "no"])
        sim_email = st.text_input("Assigned Sales Closer Email", "closer.vip@realestatehub.pk")

        if st.button("📲 Process Call Telephony Webhook", type="primary"):
            sim_payload = {
                "call_id": f"SIM-CALL-{np.random.randint(1000, 9999)}",
                "caller_id": sim_caller,
                "call_duration_sec": int(sim_dur),
                "budget_pkr": sim_budget_cr * 10_000_000.0,
                "preferred_city": "Lahore",
                "preferred_society": sim_soc,
                "purpose": "buy",
                "visit_booked": sim_visit,
                "number_of_calls": 3,
                "transcript_summary": f"Inbound caller inquired about {sim_soc}. Declared budget {sim_budget_cr} Crore. Site visit status: {sim_visit}.",
                "assigned_employee_email": sim_email,
            }

            v_res = voice_service.process_completed_voice_call(sim_payload)
            st.success(f"Call Webhook Processed! Assigned Category: **{v_res['tier']}** ({v_res['conversion_score_pct']}%)")
            if v_res["hot_lead_alert_triggered"]:
                st.warning(f"🚨 **VIP Hot Lead Alert Sent!** Email dispatched to `{sim_email}` with SLA `{v_res['action_plan']}`.")
            else:
                st.info("Lead scored as standard priority. Enrolled in nurture pipeline.")

    with col_t2:
        st.markdown("#### **Real-Time Voice Pricing Inquiry Simulator**")
        st.caption("Answers caller inquiry: *'Mera ghar kitne ka bikega?'*")
        v_inq_soc = st.selectbox("Query Society", ["DHA Phase 6", "F-10", "Bahria Town"], key="v_inq_soc")
        v_inq_size = st.number_input("Plot Size (Marla)", value=20.0, step=5.0)

        if st.button("🎙️ Generate Voice Agent TTS Speech"):
            tts_res = voice_service.handle_voice_price_inquiry(
                city="Lahore",
                area_society=v_inq_soc,
                area_marla=v_inq_size,
            )
            st.markdown(f"**TTS Speech Text (UrduLish):**")
            st.success(tts_res["tts_speech_text_urdulish"])
            st.markdown(f"**TTS Speech Text (English):**")
            st.info(tts_res["tts_speech_text_english"])

    st.divider()
    st.subheader("📋 System Audit Logs & Prediction Traceability")
    audit_summary = audit_logger.get_audit_summary()
    st.markdown(
        f"**Total Predictions Logged:** `{audit_summary['total_predictions_logged']}` • "
        f"**Average Latency:** `{audit_summary['average_latency_ms']} ms` • "
        f"**OOD Refusals:** `{audit_summary['out_of_distribution_refusals']}`"
    )

    recent_logs = audit_logger.get_recent_logs(limit=10)
    if recent_logs:
        df_logs = pd.DataFrame(recent_logs)[["prediction_id", "timestamp", "endpoint", "model_version", "latency_ms", "client_ip", "is_ood"]]
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No audit transactions logged yet.")

# Footer Disclaimer
st.markdown(
    f"""
    <div class="disclaimer-banner">
        ⚖️ <strong>Official Legal Disclaimer:</strong> {LEGAL_DISCLAIMER}
    </div>
    """,
    unsafe_allow_html=True,
)
