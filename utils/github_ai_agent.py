"""
GitHub Models AI Agent & Farmland Due Diligence Assistant
Connects to GitHub Models (GPT-4o, GPT-4o-mini, Llama-3.1-70B, Mistral, Phi-3.5)
using a free GitHub Personal Access Token (PAT).
Automatically probes available models and selects the best available tier.
Includes an intelligent local farmland knowledge fallback if no token is configured.
"""

import os
import json
import requests
from typing import List, Dict, Any, Tuple, Optional

# Supported GitHub Models in priority order (Best reasoning & quality first)
CANDIDATE_GITHUB_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "Meta-Llama-3.1-70B-Instruct",
    "Mistral-large-2407",
    "Phi-3.5-mini-instruct"
]

# GitHub Models API Base URLs (Azure Inference and GitHub endpoints)
GITHUB_MODELS_ENDPOINTS = [
    "https://models.inference.ai.azure.com/chat/completions",
    "https://models.github.ai/inference/chat/completions"
]


def get_available_github_token() -> Optional[str]:
    """
    Retrieves GitHub token from Streamlit session state, Streamlit secrets, or environment.
    Never exposes or logs secret tokens.
    """
    # 1. Check user-supplied token in Streamlit session_state
    try:
        import streamlit as st
        token = st.session_state.get("user_github_token", "").strip()
        if token:
            return token
    except Exception:
        pass

    # 2. Check Streamlit secrets
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            if "GITHUB_TOKEN" in st.secrets:
                val = str(st.secrets["GITHUB_TOKEN"]).strip()
                if val:
                    return val
            if "GH_TOKEN" in st.secrets:
                val = str(st.secrets["GH_TOKEN"]).strip()
                if val:
                    return val
    except Exception:
        pass

    # 3. Check environment variables
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        val = os.environ.get(env_key, "").strip()
        if val:
            return val

    return None


def probe_best_github_model(token: str) -> Tuple[Optional[str], str]:
    """
    Probes candidate GitHub Models to detect the best available working model for this token.
    Returns: (best_model_name, message)
    """
    clean_token = token.strip()
    if not clean_token:
        return None, "No token provided"

    headers = {
        "Authorization": f"Bearer {clean_token}",
        "Content-Type": "application/json"
    }

    test_payload = {
        "messages": [
            {"role": "system", "content": "You are a test ping responder. Reply with 'OK'."},
            {"role": "user", "content": "ping"}
        ],
        "max_tokens": 5,
        "temperature": 0.1
    }

    for model_name in CANDIDATE_GITHUB_MODELS:
        payload = dict(test_payload)
        payload["model"] = model_name

        for endpoint in GITHUB_MODELS_ENDPOINTS:
            try:
                resp = requests.post(endpoint, headers=headers, json=payload, timeout=6)
                if resp.status_code == 200:
                    data = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else {}
                    if data.get("choices") or "choices" in resp.text:
                        return model_name, f"Connected to {model_name} via GitHub Models"
                elif resp.status_code == 401:
                    return None, "Invalid GitHub token. Please check your Personal Access Token (PAT)."
                elif resp.status_code == 429:
                    # Rate limit on this model, try next model in candidate list
                    continue
            except Exception:
                continue

    return None, "Unable to reach GitHub Models endpoint. Using Built-in Farmland Intelligence Engine."


def call_github_model(
    token: str,
    model_name: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: int = 1000
) -> Tuple[bool, str]:
    """
    Invokes GitHub Models completion endpoint.
    Returns: (success: bool, response_text: str)
    """
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "messages": messages,
        "model": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    last_error = ""
    for endpoint in GITHUB_MODELS_ENDPOINTS:
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return True, content
            elif resp.status_code == 401:
                return False, "⚠️ Authentication failed: Invalid GitHub Token."
            elif resp.status_code == 429:
                return False, "⚠️ GitHub Models rate limit reached (Free Tier limit: 15 req/min). Please try again in 1 minute."
            else:
                last_error = f"API error ({resp.status_code}): {resp.text[:120]}"
        except requests.exceptions.Timeout:
            last_error = "Connection timed out to GitHub Models."
        except Exception as e:
            last_error = f"Connection error: {str(e)}"

    return False, last_error or "GitHub Models service temporarily unavailable."


def generate_local_rule_agent_response(
    query: str,
    all_parcels: List[Dict[str, Any]],
    active_center_name: str = "Varanasi Kacheri"
) -> str:
    """
    High-accuracy, comprehensive fallback rule-engine that answers farmland queries
    using the active 112-property dataset and UP land legal regulations.
    """
    q = query.lower()

    # Query 1: SC/ST Landholding & Section 98 UP Revenue Code
    if any(k in q for k in ["sc", "st", "dalit", "section 98", "sec 98", "caste", "legal risk", "permission", "dm permission"]):
        sc_parcels = [p for p in all_parcels if p.get("is_sc_st_land") or "SC" in p.get("caste_category", "")]
        sc_names = [f"- **{p['name']}** (#{p.get('id')}, {p.get('regional_district')})" for p in sc_parcels[:4]]
        return (
            "### 🚨 Legal Advisory: SC/ST Landholding & Section 98 UP Revenue Code 2006\n\n"
            "Under **Section 98 of the UP Revenue Code, 2006**, a Bhumidhar belonging to a Scheduled Caste or Scheduled Tribe "
            "**cannot transfer (by sale, gift, or mortgage) agricultural land to any person NOT belonging to SC/ST** without "
            "prior written permission from the District Collector / District Magistrate (DM).\n\n"
            "**Key Strict Legal Conditions for DM Sanction:**\n"
            "1. The seller must retain at least **3.125 Acres (5 Bigha)** of land in UP after the sale.\n"
            "2. If the seller has less than 3.125 acres, permission is strictly rejected under state rules.\n"
            "3. Any sale deed executed without prior DM permission is declared **void ab initio** under Section 104, "
            "and title vests directly in the State of Uttar Pradesh without compensation to the buyer.\n\n"
            f"**In this Platform's Dataset:**\n"
            f"- We have flagged **{len(sc_parcels)} properties** as `SC/ST Owned (Section 98 Restricted)` with a 35-point legal penalty in Critique AI.\n"
            + "\n".join(sc_names) +
            "\n\n*Recommendation: General & OBC buyers must avoid SC/ST parcels unless a registered Collector sanction order is attached to the Khatauni.*"
        )

    # Query 2: Purvanchal Bigha Conversion
    if any(k in q for k in ["bigha", "conversion", "acre", "pakka bigha", "biswa", "area", "size"]):
        return (
            "### 📐 Purvanchal Land Measurement Standards (UP East)\n\n"
            "In UP East (Varanasi, Mirzapur, Ghazipur, Chandauli, Jaunpur, Bhadohi), land is officially measured in **Pakka Bigha**:\n\n"
            "- **1 International Acre** = `1.60 Purvanchal Pakka Bigha` (or `43,560 sq.ft` / `4,046.86 sq.m`)\n"
            "- **1 Purvanchal Pakka Bigha** = `20 Biswa` = `27,225 sq.ft` = `2,529.29 sq.m` = `0.625 Acres`\n"
            "- **1 Biswa** = `20 Biswansi` = `1,361.25 sq.ft`\n"
            "- **1 Hectare** = `2.471 Acres` = `3.954 Pakka Bigha`\n\n"
            "*Note: In Western UP (Meerut, Noida), 1 Acre is 1.75 to 2.0 Kuccha Bigha. Always use the 1.60 factor for Purvanchal transactions.*"
        )

    # Query 3: Water Quality, Salinity & TDS
    if any(k in q for k in ["water", "tds", "salinity", "groundwater", "boring", "ppm", "irrigation"]):
        low_tds = [p for p in all_parcels if p.get("water_tds_ppm", 999) < 300]
        high_tds = [p for p in all_parcels if p.get("water_tds_ppm", 0) > 450]
        return (
            "### 💧 Groundwater Quality & TDS Guidelines (UP East Farmlands)\n\n"
            "Groundwater salinity and Total Dissolved Solids (TDS) dictate crop yield, polyhouse viability, and borewell lifespan:\n\n"
            "- **< 300 ppm (Pristine Deep Aquifer)**: Ideal for drip irrigation, organic floriculture, sandalwood, and export veggies. "
            f"*{len(low_tds)} holdings in our registry qualify.*\n"
            "- **300 – 450 ppm (Standard Alluvial Yield)**: Good for traditional paddy, wheat, pulses, and mango orchards.\n"
            f"- **> 450 ppm (Saline / High Hardness)**: Found near alkaline depressions (*Usar* belt in parts of Jaunpur/Bhadohi). "
            f"*{len(high_tds)} holdings require RO or gypsum soil treatment.*\n\n"
            "**Top Holding with Lowest TDS:**\n"
            f"- **{low_tds[0]['name']}** ({low_tds[0]['regional_district']}) — TDS: `{low_tds[0].get('water_tds_ppm', 'N/A')} ppm`."
        )

    # Query 4: Highest Due Diligence / Critique Score Properties
    if any(k in q for k in ["top", "best", "highest", "cleanest", "recommended", "score", "pristine"]):
        sorted_p = sorted(all_parcels, key=lambda x: (x.get("due_diligence_score", 0) + x.get("critique_ai_score", 0)), reverse=True)
        top3 = sorted_p[:3]
        res = "### 🏆 Top Institutional Farmlands (Highest Combined DD & Critique Scores)\n\n"
        for idx, p in enumerate(top3):
            res += (
                f"**{idx+1}. {p['name']}** ({p.get('regional_district')})\n"
                f"- **Size**: `{p.get('size_acres')} Acres` (`{round(float(p.get('size_acres',0))*1.6, 2)} Bigha`)\n"
                f"- **Price**: `₹{p.get('price_per_acre_lakhs')} L/Acre` | Total: `₹{p.get('total_price_cr')} Cr`\n"
                f"- **Legal Status**: `{p.get('section_98_status', 'General/OBC Unrestricted')}`\n"
                f"- **Due Diligence**: `{p.get('due_diligence_score')}/100` | **Critique AI**: `{p.get('critique_ai_score')}/100`\n"
                f"- **Water TDS**: `{p.get('water_tds_ppm')} ppm` | Soil: `{p.get('soil_type')}`\n\n"
            )
        return res

    # Query 5: Price Comparisons / Budget
    if any(k in q for k in ["cheap", "lowest price", "budget", "rate", "cost", "crore", "lakh"]):
        sorted_p = sorted(all_parcels, key=lambda x: float(x.get("price_per_acre_lakhs", 9999)))
        cheapest = sorted_p[:3]
        res = "### 💰 Most Competitive Land Rates (UP East)\n\n"
        for idx, p in enumerate(cheapest):
            res += (
                f"**{idx+1}. {p['name']}** ({p.get('regional_district')})\n"
                f"- **Rate**: `₹{p.get('price_per_acre_lakhs')} Lakhs / Acre`\n"
                f"- **Size**: `{p.get('size_acres')} Acres` | Total: `₹{p.get('total_price_cr')} Cr`\n"
                f"- **Road Access**: `{p.get('road_access_width_ft')} ft` | Caste: `{p.get('caste_category')}`\n\n"
            )
        return res

    # Generic Farmland Advisor Summary
    return (
        f"### 🌾 UP East Farmland Due Diligence Advisor\n\n"
        f"I am actively monitoring **{len(all_parcels)} institutional farmlands** across Varanasi, Mirzapur, Ghazipur, Chandauli, Jaunpur, and Bhadohi, "
        f"anchored from **{active_center_name}**.\n\n"
        "**What I can assist you with:**\n"
        "1. **Legal & SC/ST Audits**: Verification under Section 98 UP Revenue Code, Chakbandi status, and Khatauni Shreni.\n"
        "2. **Agronomic Telemetry**: Water TDS salinity, soil classification (Ganga alluvial vs. Vindhyan red loam), and high-value crop feasibility.\n"
        "3. **Concentric Valuation**: Road distance from Varanasi Kacheri Zero-Point, price per Bigha, and expressway connectivity.\n"
        "4. **Shortlist Comparison**: Direct side-by-side analysis of any parcel ID in the portfolio.\n\n"
        "💡 *Tip: To enable live deep generative reasoning with GPT-4o or Llama 3.1, enter your free GitHub Personal Access Token (PAT) in the settings below.*"
    )


def query_farmland_agent(
    user_query: str,
    chat_history: List[Dict[str, str]],
    all_parcels: List[Dict[str, Any]],
    active_center_name: str = "Varanasi Kacheri",
    token: Optional[str] = None,
    preferred_model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for conversational agent:
    1. If a valid GitHub token is available, queries the best GitHub Model (GPT-4o / Llama 3.1).
    2. If token is absent or network fails, seamlessly falls back to the intelligent local rule engine.
    """
    effective_token = token or get_available_github_token()

    if effective_token:
        # Determine model
        model_to_use = preferred_model or "gpt-4o-mini"

        # Build institutional system prompt with farmland context
        sample_parcels_summary = []
        for p in all_parcels[:15]:
            sample_parcels_summary.append(
                f"- #{p.get('id')}: {p.get('name')} | District: {p.get('regional_district')} | Size: {p.get('size_acres')} Ac | Price: ₹{p.get('price_per_acre_lakhs')}L/Ac | Caste: {p.get('caste_category')} | TDS: {p.get('water_tds_ppm')}ppm | DD Score: {p.get('due_diligence_score')}/100"
            )

        system_instruction = (
            "You are the Senior Farmland Due Diligence & Legal Intelligence Advisor for Uttar Pradesh (UP East & Varanasi).\n"
            f"You have direct access to a curated master portfolio of {len(all_parcels)} institutional farmlands anchored from {active_center_name}.\n"
            "Key Legal & Agronomic Knowledge:\n"
            "1. UP Revenue Code 2006 Section 98: Strict prohibition on SC/ST land transfers to General/OBC buyers without prior Collector/DM permission. Violations are void ab initio under Section 104.\n"
            "2. Measurement standard in UP East: 1 Acre = 1.60 Purvanchal Pakka Bigha (1 Bigha = 20 Biswa = 27,225 sq.ft = 2,529.3 sq.m).\n"
            "3. Water TDS: <300 ppm pristine deep aquifer; >450 ppm indicates salinity requiring gypsum/RO treatment.\n"
            "4. Expressways: Varanasi Ring Road (Phase 1 & 2), Purvanchal Expressway, Ganga Expressway.\n"
            "Format your answers with professional markdown, bullet points, and actionable investor due diligence takeaways.\n\n"
            "Active Sample Farmlands:\n" + "\n".join(sample_parcels_summary)
        )

        messages = [{"role": "system", "content": system_instruction}]

        # Add recent conversation history (last 6 messages)
        for msg in chat_history[-6:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        messages.append({"role": "user", "content": user_query})

        success, response_text = call_github_model(effective_token, model_to_use, messages)
        if success:
            return {
                "response": response_text,
                "model_used": model_to_use,
                "is_live_llm": True,
                "error": None
            }

    # Fallback to rich local domain engine
    local_response = generate_local_rule_agent_response(user_query, all_parcels, active_center_name)
    return {
        "response": local_response,
        "model_used": "Built-in Farmland Intelligence Engine",
        "is_live_llm": False,
        "error": None
    }
