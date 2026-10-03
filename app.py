"""
UP East & Varanasi Farmlands Intelligence Platform
Streamlit Web Application solely dedicated to Varanasi and surrounding Eastern UP agricultural estates.
Features:
- Mobile-Friendly Adaptive Layout (Media queries, responsive grid, touch-friendly touch targets)
- Left Panel (Sidebar) Visible Always & Slightly Wider (375px min-width)
- Dynamic Reference City Center: Automatically anchors to respective District City Center upon district filtering
- Center Selection & Override ("center should be allowed to change"): Manual switcher in both Sidebar and Tab 1
- Tab 1 District Filter: Directly filters the Property Summary Table and Map by District
- Distance dynamically calculated from respective City Center (Varanasi Kacheri, Chandauli Collectorate, Mirzapur Kacheri, Jaunpur Collectorate, Ghazipur Collectorate, etc.)
- Integrated Google Satellite & Roadmap with Search & Micro-Market Auto-Centering
- Interactive Map Pinning: Click on map to add farmland properties to master inventory
- Comprehensive Farmland Table in Tab 1 with full details summary & Critique AI ledger
- Independent Critique AI Engine (Negative feedback auditing, 8 risk vectors, Govt site verification)
- Persistent User Favorites / Shortlisting system
- Real-time CPU, RAM, and Hosted Environment resource monitor
- Multi-Sheet Excel & Master CSV Exporters
"""

import os
import json
import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from utils.geo_routing import (
    DEFAULT_ORIGIN_LAT,
    DEFAULT_ORIGIN_LNG,
    DEFAULT_ORIGIN_NAME,
    DISTRICT_CITY_CENTERS,
    get_city_center_for_district,
    load_landmarks,
    compute_parcel_routing,
    assign_concentric_ring,
    haversine_distance_km,
    estimate_road_distance_km,
    estimate_driving_time_minutes
)
from utils.land_units import LandUnitConverter
from utils.favorites_manager import (
    DEFAULT_USERNAMES,
    load_favorites,
    load_raw_favorites,
    save_favorites,
    save_raw_favorites,
    add_favorite,
    remove_favorite,
    toggle_favorite,
    is_favorite,
    get_users_for_parcel,
    get_all_active_usernames,
    filter_favorite_parcels,
    clear_all_favorites
)
from utils.property_flags_manager import (
    load_property_flags,
    set_property_flag,
    remove_property_flag,
    get_property_flag,
    is_fake,
    is_ignored,
    get_ignored_ids,
    get_fake_ids,
    filter_parcels_by_flag_status
)
from utils.weekly_ml_scanner import (
    run_weekly_scan,
    get_latest_scanner_status
)
from utils.critic_ai import evaluate_property_critique, get_weekly_audit_metadata
from utils.system_telemetry import get_system_telemetry, render_system_telemetry_html
from utils.google_map_view import create_google_farmland_map
from utils.farmland_view import (
    clean_html,
    render_farmland_summary_card_html,
    render_agronomic_telemetry_html,
    render_legal_and_news_card_html,
    render_critique_ai_card_html,
    render_seller_contact_card_html
)
from utils.excel_exporter import generate_excel_workbook, export_master_csv
from utils.farmland_repository import create_and_add_farmland, load_all_parcels

# Page Configuration: Sidebar Visible Always
st.set_page_config(
    page_title="UP East Farmlands | Varanasi Agro-Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Professional Institutional Aesthetics, Mobile Responsiveness, Permanent Wide Sidebar & Colored Sticky Tabs
st.markdown("""
<style>
    /* Global White Background & Clean Institutional Theme */
    .stApp, .main, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }
    body {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        box-sizing: border-box !important;
    }

    /* Streamlit Top Header & Navigation Bar: Pure Seamless White (Zero Black) */
    header,
    header[data-testid="stHeader"],
    div[data-testid="stHeader"],
    [data-testid="stHeader"],
    .stAppHeader {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-bottom: 1px solid #E2E8F0 !important;
    }
    header[data-testid="stHeader"] svg,
    header[data-testid="stHeader"] button,
    header[data-testid="stHeader"] a,
    header[data-testid="stHeader"] span {
        color: #475569 !important;
        fill: #475569 !important;
    }

    /* Tab Panels & Containers: Pure White Across All Tabs */
    div[data-testid="stTabs"],
    div[data-testid="stTabs"] > div,
    div[data-baseweb="tab-panel"],
    div[data-testid="stTabContent"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }

    /* Expanders, Dataframes & Tables: Crisp Light Institutional Background */
    div[data-testid="stExpander"],
    .streamlit-expanderHeader,
    .streamlit-expanderContent,
    details {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #E2E8F0 !important;
    }
    .stDataFrame,
    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
    }

    /* Menus, Popovers, and Dropdown Lists */
    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-baseweb="menu"],
    li[data-baseweb="menu-item"] {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
    }
    
    /* Clean Dark Headings & Readable Text */
    h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    p, span, label {
        color: #334155 !important;
    }

    /* Top KPI Metric Cards */
    .stMetric {
        background: #FFFFFF !important;
        padding: 12px 14px !important;
        border-radius: 10px !important;
        border: 1.5px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #047857 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748B !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 11px !important;
        color: #059669 !important;
        font-weight: 600 !important;
    }

    /* Left Panel (Sidebar): Visible always, slightly wider (375px), clean light institutional theme */
    section[data-testid="stSidebar"] {
        min-width: 360px !important;
        max-width: 400px !important;
        width: 375px !important;
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
        color: #0F172A !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 3.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3 {
        color: #0F172A !important;
    }

    /* Flex alignment to prevent sidebar from overlapping or clipping main container */
    [data-testid="stAppViewContainer"] {
        display: flex !important;
        flex-direction: row !important;
    }
    section.main {
        flex: 1 1 auto !important;
        min-width: 0 !important;
        overflow-x: auto !important;
    }

    /* Keep left sidebar visible on desktop and tablet without auto-collapsing */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            transform: none !important;
            display: block !important;
            visibility: visible !important;
        }
        button[data-testid="baseButton-header"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarHeader"] > button {
            display: none !important;
        }
    }

    /* ============================================================
       PERMANENTLY VISIBLE TABS WITH DISTINCT COLORED TILES
       ============================================================ */
    /* Sticky Container for Tabs: stays pinned at top when scrolling, wraps comfortably without hiding behind overflow arrows */
    div[data-testid="stTabs"] > div:first-child,
    div[data-baseweb="tab-list"] {
        position: sticky !important;
        top: 0px !important;
        z-index: 9999 !important;
        background-color: #FFFFFF !important;
        padding: 10px 4px 12px 4px !important;
        border-bottom: 2px solid #E2E8F0 !important;
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 8px !important;
        overflow: visible !important;
        width: 100% !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04) !important;
    }
    /* Hide scroll arrow buttons and default active underline bar */
    button[data-baseweb="tab-scroll-backward"],
    button[data-baseweb="tab-scroll-forward"],
    div[data-baseweb="tab-border"],
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* General Tab Tile Styling */
    button[data-testid="stTab"],
    div[data-baseweb="tab-list"] > button {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        color: #0F172A !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-weight: 700 !important;
        font-size: 13.5px !important;
        border: 1.5px solid #E2E8F0 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        white-space: nowrap !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }
    button[data-testid="stTab"]:hover,
    div[data-baseweb="tab-list"] > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.1) !important;
    }
    button[data-testid="stTab"] p,
    div[data-baseweb="tab-list"] > button p {
        font-size: 13px !important;
        font-weight: 700 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.3 !important;
    }
    button[data-testid="stTab"][aria-selected="true"] p,
    button[data-testid="stTab"][aria-selected="true"] span,
    button[data-testid="stTab"][aria-selected="true"] div,
    div[data-baseweb="tab-list"] > button[aria-selected="true"] p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }

    /* Tab 1: 🗺️ Interactive Google Map & Search (Royal Blue Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(1),
    button[data-testid="stTab"]:nth-of-type(1) {
        background-color: #EFF6FF !important;
        border-color: #93C5FD !important;
        color: #1D4ED8 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(1):hover {
        background-color: #DBEAFE !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(1)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(1)[aria-selected="true"] {
        background: linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%) !important;
        border-color: #1E40AF !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35) !important;
    }

    /* Tab 2: 🔍 Detailed Farmland Telemetry & Dossier (Cyan / Teal Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(2),
    button[data-testid="stTab"]:nth-of-type(2) {
        background-color: #ECFEFF !important;
        border-color: #A5F3FC !important;
        color: #0E7490 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(2):hover {
        background-color: #CFFAFE !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(2)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(2)[aria-selected="true"] {
        background: linear-gradient(135deg, #0E7490 0%, #0891B2 100%) !important;
        border-color: #155E75 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(8, 145, 178, 0.35) !important;
    }

    /* Tab 3: 📊 Master Farmland Comparison Ledger (Purple / Violet Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(3),
    button[data-testid="stTab"]:nth-of-type(3) {
        background-color: #F5F3FF !important;
        border-color: #DDD6FE !important;
        color: #6D28D9 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(3):hover {
        background-color: #EDE9FE !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(3)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(3)[aria-selected="true"] {
        background: linear-gradient(135deg, #6D28D9 0%, #7C3AED 100%) !important;
        border-color: #5B21B6 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.35) !important;
    }

    /* Tab 4: 📰 Published News & Caveat Notices (Warm Amber / Gold Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(4),
    button[data-testid="stTab"]:nth-of-type(4) {
        background-color: #FFFBEB !important;
        border-color: #FDE68A !important;
        color: #B45309 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(4):hover {
        background-color: #FEF3C7 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(4)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(4)[aria-selected="true"] {
        background: linear-gradient(135deg, #B45309 0%, #D97706 100%) !important;
        border-color: #92400E !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(217, 119, 6, 0.35) !important;
    }

    /* Tab 5: ⭐ Shortlisted Favorites Matrix (Rose / Ruby Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(5),
    button[data-testid="stTab"]:nth-of-type(5) {
        background-color: #FFF1F2 !important;
        border-color: #FECDD3 !important;
        color: #BE123C !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(5):hover {
        background-color: #FFE4E6 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(5)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(5)[aria-selected="true"] {
        background: linear-gradient(135deg, #BE123C 0%, #E11D48 100%) !important;
        border-color: #9F1239 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(225, 29, 72, 0.35) !important;
    }

    /* Tab 6: 📥 Export Center (Excel / CSV) (Emerald / Jade Tile) */
    div[data-baseweb="tab-list"] > button:nth-of-type(6),
    button[data-testid="stTab"]:nth-of-type(6) {
        background-color: #ECFDF5 !important;
        border-color: #A7F3D0 !important;
        color: #047857 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(6):hover {
        background-color: #D1FAE5 !important;
    }
    div[data-baseweb="tab-list"] > button:nth-of-type(6)[aria-selected="true"],
    button[data-testid="stTab"]:nth-of-type(6)[aria-selected="true"] {
        background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
        border-color: #065F46 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.35) !important;
    }

    /* ============================================================
       WHITE & LIGHT BUTTON STYLING — STRICT ZERO BLACK BUTTONS
       ============================================================ */
    .stButton > button,
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #FFFFFF !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.15s ease-in-out !important;
    }
    .stButton > button:hover,
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #F8FAFC !important;
        background: #F8FAFC !important;
        color: #0F172A !important;
        border-color: #94A3B8 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08) !important;
    }
    .stButton > button:active,
    button[kind="secondary"]:active {
        background-color: #F1F5F9 !important;
        background: #F1F5F9 !important;
        color: #0F172A !important;
        border-color: #64748B !important;
    }

    /* Primary Buttons: Light Ice Blue / Emerald Tints (Never Black) */
    button[kind="primary"],
    .stButton > button[kind="primary"],
    button[data-testid="baseButton-primary"] {
        background-color: #EFF6FF !important;
        background: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1.5px solid #60A5FA !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(37, 99, 235, 0.12) !important;
    }
    button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:hover,
    button[data-testid="baseButton-primary"]:hover {
        background-color: #DBEAFE !important;
        background: #DBEAFE !important;
        color: #1E40AF !important;
        border-color: #2563EB !important;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2) !important;
    }

    /* Download Buttons: Crisp Light Emerald (Never Black) */
    .stDownloadButton > button {
        background-color: #ECFDF5 !important;
        background: #ECFDF5 !important;
        color: #047857 !important;
        border: 1.5px solid #6EE7B7 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(4, 120, 87, 0.12) !important;
    }
    .stDownloadButton > button:hover {
        background-color: #D1FAE5 !important;
        background: #D1FAE5 !important;
        color: #065F46 !important;
        border-color: #059669 !important;
    }

    /* Inputs, Selectboxes, Multiselects: Clean White Fields */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }

    /* Modern Mobile Responsive Layout */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: 3.75rem !important;
        }
        /* Wrap KPI metrics row into 2 neat columns on phone screens */
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 6px !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            flex: 1 1 calc(50% - 6px) !important;
            min-width: calc(50% - 6px) !important;
        }
        h1 {
            font-size: 1.35rem !important;
            line-height: 1.2 !important;
        }
        h2 {
            font-size: 1.15rem !important;
        }
        h3 {
            font-size: 1.05rem !important;
        }
        button[kind="primary"], button[kind="secondary"], .stButton > button {
            min-height: 44px !important;
            font-size: 13px !important;
            border-radius: 8px !important;
        }
        div[data-testid="stDataFrame"] {
            width: 100% !important;
            overflow-x: auto !important;
        }
    }

    /* Table Column Header: Shrink text, wrap words, compact padding, eliminate excessive column width */
    [data-testid="stDataFrame"] th,
    [data-testid="stTable"] th,
    div[data-testid="stDataFrame"] div[role="columnheader"],
    div[data-testid="stDataFrame"] div[role="columnheader"] span,
    div[data-testid="stDataFrame"] div[role="columnheader"] p {
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        line-height: 1.15 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        text-align: left !important;
        padding: 3px 5px !important;
    }
</style>
""", unsafe_allow_html=True)


def render_html_block(html_content: str):
    """Safely renders HTML without triggering markdown code block parsing."""
    cleaned = clean_html(html_content)
    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)


@st.cache_data
def load_farmlands_dataset():
    """Loads master JSON dataset of Varanasi and UP East Farmlands."""
    return load_all_parcels()


# Load Base Datasets
all_parcels = load_farmlands_dataset()
# Master Tab 1 Serial Number lookup mapping (preserved across all tabs, maps, and favorites)
master_sno_map = {str(p["id"]): idx + 1 for idx, p in enumerate(all_parcels)}
landmarks = load_landmarks()
landmark_dict = {lm["name"]: lm for lm in landmarks}
default_lm_name = next((lm["name"] for lm in landmarks if lm.get("is_default")), landmarks[0]["name"])

# Distinct Districts in Dataset
all_districts = sorted(list(set(p.get("regional_district", "Varanasi") for p in all_parcels if p.get("regional_district"))))
district_choices = ["All Districts (UP East)"] + all_districts

# -------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------
if "active_user_name" not in st.session_state:
    st.session_state["active_user_name"] = "VPT"

if "fav_user_filter" not in st.session_state:
    st.session_state["fav_user_filter"] = "All Properties (Inventory & Favorites)"

if "favorites" not in st.session_state:
    st.session_state["favorites"] = load_favorites()

raw_fav_records = load_raw_favorites()
all_active_usernames = get_all_active_usernames(raw_fav_records)
fav_users_by_parcel = {str(p["id"]): get_users_for_parcel(str(p["id"]), raw_fav_records) for p in all_parcels}

if "property_flags" not in st.session_state:
    st.session_state["property_flags"] = load_property_flags()

if "show_ignored" not in st.session_state:
    st.session_state["show_ignored"] = False

if "show_fake" not in st.session_state:
    st.session_state["show_fake"] = False

if "map_clicked_coord" not in st.session_state:
    st.session_state["map_clicked_coord"] = None

if "map_search_term" not in st.session_state:
    st.session_state["map_search_term"] = ""

if "filter_district" not in st.session_state:
    st.session_state["filter_district"] = "All Districts (UP East)"

if "active_center_name" not in st.session_state:
    st.session_state["active_center_name"] = default_lm_name

if "manual_center_override" not in st.session_state:
    st.session_state["manual_center_override"] = False

# -------------------------------------------------------------
# DISTRICT FILTER CALLBACKS & CITY CENTER AUTO-ANCHORING
# -------------------------------------------------------------
def sync_district_from_sidebar():
    st.session_state["filter_district"] = st.session_state["sb_dist_choice"]
    if not st.session_state.get("manual_center_override", False):
        center_obj = get_city_center_for_district(st.session_state["filter_district"])
        st.session_state["active_center_name"] = center_obj["name"]

def sync_district_from_tab1():
    st.session_state["filter_district"] = st.session_state["t1_dist_choice"]
    if not st.session_state.get("manual_center_override", False):
        center_obj = get_city_center_for_district(st.session_state["filter_district"])
        st.session_state["active_center_name"] = center_obj["name"]

def sync_center_from_sidebar():
    st.session_state["active_center_name"] = st.session_state["sb_center_choice"]
    st.session_state["manual_center_override"] = True

# -------------------------------------------------------------
# SIDEBAR FILTERS & CONTROLS (Always Visible, 375px Wide)
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/wheat.png", width=60)
st.sidebar.title("Agro-Land Filters")
st.sidebar.caption("Varanasi & Purvanchal Concentric Corridor")

# Manual Data Refresh Button in Sidebar
if st.sidebar.button("🔄 Refresh Farmland Data Now", type="primary", use_container_width=True, key="btn_sb_refresh_top"):
    with st.spinner("Refreshing farmland inventory, satellite telemetry, and road routing..."):
        st.cache_data.clear()
        scan_report = run_weekly_scan(all_parcels, force=True)
        st.session_state["favorites"] = load_favorites()
        st.session_state["property_flags"] = load_property_flags()
        st.sidebar.success(f"✅ Data refreshed! Scanned {scan_report['parcels_scanned']} parcels ({scan_report['duplicates_suppressed']} duplicates suppressed).")
        time.sleep(0.3)
        st.rerun()

# 1. District Filter in Sidebar (Synchronized with Tab 1)
st.sidebar.markdown("### 📍 Filter by District")
current_dist_idx = district_choices.index(st.session_state["filter_district"]) if st.session_state["filter_district"] in district_choices else 0
sidebar_dist = st.sidebar.selectbox(
    "Active District Filter:",
    options=district_choices,
    index=current_dist_idx,
    key="sb_dist_choice",
    on_change=sync_district_from_sidebar,
    help="When a specific district is chosen, distance is automatically calculated from that district's city center."
)

# 2. Reference Zero-Point (Center) Selector ("center should be allowed to change")
st.sidebar.markdown("### 🏛️ Distance Zero-Point (Center)")
center_options = list(landmark_dict.keys())
current_center_idx = center_options.index(st.session_state["active_center_name"]) if st.session_state["active_center_name"] in center_options else 0

selected_center_name = st.sidebar.selectbox(
    "Road Distance Measured From:",
    options=center_options,
    index=current_center_idx,
    key="sb_center_choice",
    on_change=sync_center_from_sidebar,
    help="Default anchors to respective District City Center. You can change this to any landmark or custom point anytime."
)

active_lm = landmark_dict.get(st.session_state["active_center_name"], landmark_dict[default_lm_name])
origin_lat = float(active_lm["lat"])
origin_lng = float(active_lm["lng"])
center_short = active_lm["name"].split("(")[0].strip()

if st.session_state.get("manual_center_override", False):
    st.sidebar.warning(f"⚠️ Custom Center Active: **{center_short}**")
    if st.sidebar.button("🔄 Auto-Reset to District City Center", use_container_width=True):
        st.session_state["manual_center_override"] = False
        center_obj = get_city_center_for_district(st.session_state["filter_district"])
        st.session_state["active_center_name"] = center_obj["name"]
        st.rerun()
else:
    st.sidebar.info(f"**Auto Zero-Point:** {active_lm['name']}\n\n*({active_lm.get('description', '')})*")

# Precompute Dynamic Routing for all parcels relative to active zero-point
routings = {}
critique_cache = {}
for p in all_parcels:
    pid = str(p.get("id"))
    routings[pid] = compute_parcel_routing(p, origin_lat, origin_lng, active_lm["name"])
    base_crit = evaluate_property_critique(p)
    if is_fake(pid, st.session_state["property_flags"]):
        f_info = get_property_flag(pid, st.session_state["property_flags"])
        base_crit["critique_risk_score"] = 0
        base_crit["critique_risk_verdict"] = "🚨 CRITICAL: Fake Listing"
        base_crit["critique_verdict_badge"] = "🚩 FAKE LISTING"
        base_crit["negative_feedbacks_summary"] = f"CRITICAL FRAUD ALERT: {f_info.get('reason', 'Reported as fake listing')}."
    critique_cache[pid] = base_crit

# 3. Concentric Radial Distance Selector
st.sidebar.markdown("### ⭕ Concentric Radial Buffer")
ring_options = [
    "All Radii (Full UP East Region)",
    "🟢 Within 20 km (Urban Fringe / Ring Road)",
    "🟡 20 to 40 km (Chandauli / Mughalsarai / Mirzapur Border)",
    "🔵 40 to 60 km (Jaunpur / Mirzapur / Gyanpur Core)",
    "🟣 60 to 80 km (Ghazipur / Robertsganj / Azamgarh Border)",
    "🟤 80 to 100 km (Azamgarh / Prayagraj Fringe / Mau / Buxar)",
    "🌐 Extended 200 km Regional Buffer"
]
selected_ring = st.sidebar.selectbox("Filter by Radial Distance Ring:", options=ring_options, index=0)

# 4. Maximum Road Distance Slider
max_road_km = st.sidebar.slider(
    f"Max Road Distance from {center_short[:16]} (km):",
    min_value=5,
    max_value=200,
    value=120,
    step=5,
    help="Filter by estimated actual road driving distance from active origin."
)

# 5. User Profiles & Multi-User Favorites Filters (Visible to All)
st.sidebar.markdown("### ⭐ Investor Profiles & Favorites")

sidebar_user_list = list(DEFAULT_USERNAMES)
for u in all_active_usernames:
    if u not in sidebar_user_list:
        sidebar_user_list.append(u)
sidebar_user_list.append("➕ Custom First Name...")

current_user_idx = sidebar_user_list.index(st.session_state["active_user_name"]) if st.session_state["active_user_name"] in sidebar_user_list else 0
chosen_sidebar_user = st.sidebar.selectbox(
    "👤 Active User Profile / First Name:",
    options=sidebar_user_list,
    index=current_user_idx,
    key="sb_active_user_select",
    help="Defaults: VPT, PPT, Guest-1, guest-2. Any property you star will be saved under this name and visible to everyone."
)
if chosen_sidebar_user == "➕ Custom First Name...":
    custom_u = st.sidebar.text_input("Enter First Name:", value="", placeholder="e.g. Ramesh", key="sb_custom_user_input")
    if custom_u.strip():
        st.session_state["active_user_name"] = custom_u.strip()
else:
    st.session_state["active_user_name"] = chosen_sidebar_user

fav_filter_choices = [
    "All Properties (Inventory & Favorites)",
    f"⭐ All Favorites (Combined — {len(st.session_state['favorites'])})"
] + [
    f"👤 {u}'s Favorites ({len(load_favorites(username=u))})"
    for u in (all_active_usernames or DEFAULT_USERNAMES)
]

sel_fav_filter = st.sidebar.selectbox(
    "⭐ Filter by Favorites:",
    options=fav_filter_choices,
    index=0,
    key="sb_fav_filter_select",
    help="Filter by all favorites (visible to all) or by specific investor."
)

# 6. Listing Moderation & Ignore/Fake Filters
st.sidebar.markdown("### 🛡️ Moderation & Quality Filters")
ignored_count = len(get_ignored_ids(st.session_state["property_flags"]))
fake_count = len(get_fake_ids(st.session_state["property_flags"]))

chk_ignored = st.sidebar.checkbox(
    f"👁️ Show Ignored Properties ({ignored_count})",
    value=st.session_state["show_ignored"],
    key="sb_chk_show_ignored",
    help="Check to reveal properties you placed on the ignore list (hidden by default)."
)
chk_fake = st.sidebar.checkbox(
    f"🚩 Show Fake Listings ({fake_count})",
    value=st.session_state["show_fake"],
    key="sb_chk_show_fake",
    help="Check to reveal listings that have been flagged as fake or fraudulent."
)
st.session_state["show_ignored"] = chk_ignored
st.session_state["show_fake"] = chk_fake

# 6. Caste Category & Section 98 UP Revenue Code Filter
caste_filter = st.sidebar.selectbox(
    "⚖️ Landowner Caste & Sec 98 Filter:",
    options=[
        "All Properties (Unrestricted & Flagged)",
        "General / OBC Only (Unrestricted for All)",
        "SC / ST Owned Only (🚨 Section 98 Flagged)"
    ],
    index=0,
    help="Under Section 98 UP Revenue Code 2006, General category buyers cannot purchase SC/ST land without prior written Collector/DM sanction. Use this filter to exclude restricted lands."
)

# 7. Price per Acre Range Slider
prices = [float(p.get("price_per_acre_lakhs", 25.0)) for p in all_parcels] if all_parcels else [25.0]
min_price, max_price = min(prices), max(prices)
selected_price_range = st.sidebar.slider(
    "Price per Acre (₹ Lakhs):",
    min_value=int(min_price),
    max_value=int(max_price) + 2,
    value=(int(min_price), int(max_price) + 2)
)

# 8. Sourcing Tier Filter
all_tiers = sorted(list(set(p.get("sourcing_tier", "Tier 1: Government Land Registry") for p in all_parcels)))
selected_tiers = st.sidebar.multiselect(
    "Sourcing Tier / Provenance:",
    options=all_tiers,
    default=all_tiers
)

# 9. Weekly AI/ML Scanner Control in Sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Weekly Duplicate-Free AI Engine")
scanner_status = get_latest_scanner_status()
st.sidebar.caption(f"**Last Scanned:** {scanner_status.get('completed_at', 'Scheduled')[:16]}")
st.sidebar.caption(f"**Next Refresh Due:** {scanner_status.get('next_refresh_due', 'In 7 Days')[:10]}")
st.sidebar.caption(f"**Duplicates Suppressed:** {scanner_status.get('duplicates_suppressed', 0)} (Zero Duplicate Policy)")

if st.sidebar.button("⚡ Run Weekly AI/ML Scan Now", use_container_width=True):
    with st.spinner("Executing Sentinel-2 NDVI calculation & duplicate-free audit..."):
        report = run_weekly_scan(all_parcels, force=True)
        st.sidebar.success(
            f"✅ Scan Complete! {report['parcels_scanned']} audited, {report['duplicates_suppressed']} duplicates suppressed, {report['in_place_updated']} updated in-place."
        )
        scanner_status = get_latest_scanner_status()

# 10. CPU, RAM & Hosted Environment Telemetry Widget
st.sidebar.markdown("---")
st.sidebar.markdown("### 🖥️ Hosted System Telemetry")
with st.sidebar:
    render_html_block(render_system_telemetry_html())


# -------------------------------------------------------------
# FILTERING LOGIC
# -------------------------------------------------------------
filtered_parcels = []
for p in all_parcels:
    pid = str(p.get("id"))
    routing = routings.get(pid, {})
    road_km = routing.get("road_km", 999.0)
    aerial_km = routing.get("aerial_km", 999.0)
    price = float(p.get("price_per_acre_lakhs", 0.0))
    dist = p.get("regional_district", "")
    tier = p.get("sourcing_tier", "")

    # Check Moderation Flags: Ignore List & Fake Listings
    flag_info = get_property_flag(pid, st.session_state["property_flags"])
    if flag_info:
        flag_type = flag_info.get("flag")
        if flag_type == "ignored" and not st.session_state["show_ignored"]:
            continue
        if flag_type == "fake" and not st.session_state["show_fake"]:
            continue

    # Check Multi-User Favorite Filter or 1-Click Starred KPI Toggle
    if st.session_state.get("show_only_favorites_in_tab1", False) or "⭐ All Favorites" in sel_fav_filter:
        if not is_favorite(pid, cached_set=st.session_state["favorites"]):
            continue
    elif sel_fav_filter.startswith("👤 ") and "'s Favorites" in sel_fav_filter:
        target_uname = sel_fav_filter.split("👤 ")[1].split("'s Favorites")[0].strip()
        if not is_favorite(pid, username=target_uname):
            continue

    # Check Caste Category & Section 98 UP Revenue Code Filter
    is_sc_st_parcel = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
    if caste_filter == "General / OBC Only (Unrestricted for All)" and is_sc_st_parcel:
        continue
    if caste_filter == "SC / ST Owned Only (🚨 Section 98 Flagged)" and not is_sc_st_parcel:
        continue

    # Check District Filter (Single selection / All Districts)
    if st.session_state["filter_district"] != "All Districts (UP East)":
        if dist.lower() != st.session_state["filter_district"].lower():
            continue

    # Check Radial Ring Filter
    if "Within 20 km" in selected_ring and aerial_km > 20.0:
        continue
    elif "20 to 40 km" in selected_ring and (aerial_km <= 20.0 or aerial_km > 40.0):
        continue
    elif "40 to 60 km" in selected_ring and (aerial_km <= 40.0 or aerial_km > 60.0):
        continue
    elif "60 to 80 km" in selected_ring and (aerial_km <= 60.0 or aerial_km > 80.0):
        continue
    elif "80 to 100 km" in selected_ring and (aerial_km <= 80.0 or aerial_km > 100.0):
        continue
    elif "Extended 200 km" in selected_ring and (aerial_km <= 100.0 or aerial_km > 200.0):
        continue

    # Check Road Distance
    if road_km > max_road_km:
        continue

    # Check Price
    if not (selected_price_range[0] <= price <= selected_price_range[1]):
        continue

    # Check Tier
    if tier not in selected_tiers:
        continue

    filtered_parcels.append(p)

# Sort parcels by road distance from active origin
filtered_parcels.sort(key=lambda x: routings.get(str(x["id"]), {}).get("road_km", 999.0))

# -------------------------------------------------------------
# MAIN APP HEADER & KPIS
# -------------------------------------------------------------
st.title("🌾 UP East & Varanasi Farmlands Intelligence Platform")
st.markdown(
    f"**Concentric Agro-Intelligence & Due Diligence** | Active Zero-Point: **{active_lm['name']}**"
)

# Top KPI Metric Cards (Responsive on Mobile)
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Verified Holdings", f"{len(filtered_parcels)} / {len(all_parcels)}")
with kpi2:
    if filtered_parcels:
        avg_dist = round(sum(routings[str(p["id"])]["road_km"] for p in filtered_parcels) / len(filtered_parcels), 1)
        st.metric("Avg Road Distance", f"{avg_dist} km", f"From {center_short[:16]}")
    else:
        st.metric("Avg Road Distance", "N/A")
with kpi3:
    if filtered_parcels:
        avg_price = round(sum(float(p.get("price_per_acre_lakhs", 0)) for p in filtered_parcels) / len(filtered_parcels), 1)
        st.metric("Avg Rate / Acre", f"₹{avg_price} Lakhs")
    else:
        st.metric("Avg Rate / Acre", "N/A")
with kpi4:
    fav_count = len(st.session_state["favorites"])
    is_fav_filter_on = st.session_state.get("show_only_favorites_in_tab1", False)
    st.metric(
        "Starred Favorites",
        f"{fav_count} Parcels",
        "Filtered Active" if is_fav_filter_on else "Shortlist"
    )
    if is_fav_filter_on:
        if st.button("🌐 Show All Holdings", key="btn_kpi_fav_filter_toggle", use_container_width=True, help="Reset filter to show all properties"):
            st.session_state["show_only_favorites_in_tab1"] = False
            st.session_state["fav_user_filter"] = "All Properties (Inventory & Favorites)"
            st.rerun()
    else:
        if st.button(f"⭐ View {fav_count} Favorites", key="btn_kpi_fav_filter_toggle", use_container_width=True, help="Filter app to display only your starred favorites"):
            st.session_state["show_only_favorites_in_tab1"] = True
            st.session_state["fav_user_filter"] = "⭐ All Favorites"
            st.rerun()
with kpi5:
    sys_tel = get_system_telemetry()
    st.metric("Host CPU / RAM", f"{sys_tel['app_cpu_pct']}% CPU", f"{sys_tel['app_rss_mb']}MB RSS ({sys_tel['host_ram_used_pct']}% Host)")

st.markdown("---")

if st.session_state.get("show_only_favorites_in_tab1", False):
    fb_c1, fb_c2 = st.columns([3.8, 1.2])
    with fb_c1:
        st.info(f"⭐ **Viewing {len(filtered_parcels)} Starred Favorites Only** across Google Map, Dossier Telemetry, and Tables. [Click 'Show All Holdings' to restore full inventory].")
    with fb_c2:
        if st.button("✖️ Show All Holdings", key="btn_clear_fav_filter_banner", use_container_width=True):
            st.session_state["show_only_favorites_in_tab1"] = False
            st.session_state["fav_user_filter"] = "All Properties (Inventory & Favorites)"
            st.rerun()

# -------------------------------------------------------------
# TAB NAVIGATION (Clean, focused strictly on Farmlands)
# -------------------------------------------------------------
view_tabs = st.tabs([
    "🗺️ Interactive Google Map & Search",
    "🔍 Detailed Farmland Telemetry & Dossier",
    "📊 Master Farmland Comparison Ledger",
    "📰 Published News & Caveat Notices",
    "⭐ Shortlisted Favorites Matrix",
    "📥 Export Center (Excel / CSV)"
])

# -------------------------------------------------------------
# TAB 1: INTERACTIVE GOOGLE MAP, SEARCH & PROPERTY CREATOR
# -------------------------------------------------------------
with view_tabs[0]:
    # Tab 1 District Filter, Center Switcher & Quick Search
    t1_c1, t1_c2, t1_c3, t1_c4 = st.columns([1.6, 1.8, 1.8, 1.2])

    with t1_c1:
        t1_dist_idx = district_choices.index(st.session_state["filter_district"]) if st.session_state["filter_district"] in district_choices else 0
        st.selectbox(
            "📍 Filter Table & Map by District:",
            options=district_choices,
            index=t1_dist_idx,
            key="t1_dist_choice",
            on_change=sync_district_from_tab1,
            help="Select a district to filter the table and map. Distance will be calculated from that District's City Center."
        )

    with t1_c2:
        st.markdown(f"**🏛️ Distance Zero-Point:**")
        st.caption(f"Currently: **{center_short[:30]}**")
        with st.popover("⚙️ Change Center Zero-Point", use_container_width=True):
            st.markdown("##### 🏛️ Change Reference Zero-Point")
            st.caption("Change the origin landmark or city center from which all road distances and concentric rings are computed.")
            new_t1_center = st.selectbox(
                "Select Center Reference:",
                options=center_options,
                index=center_options.index(st.session_state["active_center_name"]) if st.session_state["active_center_name"] in center_options else 0,
                key="popover_center_choice"
            )
            p_btn1, p_btn2 = st.columns(2)
            with p_btn1:
                if st.button("Apply Selected Center", type="primary", use_container_width=True):
                    st.session_state["active_center_name"] = new_t1_center
                    st.session_state["manual_center_override"] = True
                    st.rerun()
            with p_btn2:
                if st.button("Auto-Anchor to City Center", use_container_width=True):
                    st.session_state["manual_center_override"] = False
                    center_obj = get_city_center_for_district(st.session_state["filter_district"])
                    st.session_state["active_center_name"] = center_obj["name"]
                    st.rerun()

    with t1_c3:
        map_search_input = st.text_input(
            "🔍 Search Properties (Table & Map):",
            value=st.session_state.get("map_search_term", ""),
            placeholder="Type name, village, khasra, highway...",
            key="tab1_search_bar"
        )

    with t1_c4:
        micro_market_jump = st.selectbox(
            "📍 Jump to Micro-Market:",
            options=[
                "All Regions",
                "Rohania / Ring Road Ph-2",
                "Babatpur Airport Agro-Belt",
                "Chandauli / Mughalsarai",
                "Mirzapur / Vindhya Slopes",
                "Jaunpur Gomti Basin",
                "Ghazipur Ganga Alluvium"
            ],
            key="micro_market_select"
        )

    st.markdown(f"### 🗺️ Google Satellite & Hybrid Map with Concentric Buffers")
    st.caption(f"Concentric buffer rings (20 km, 40 km, 60 km, 80 km, 100 km) radiating from **{active_lm['name']}**. Search any area, or click anywhere on the map to add a new farmland property!")

    # Micro-market coordinate lookup
    micro_market_coords = {
        "Rohania / Ring Road Ph-2": (25.2650, 82.9050, 11),
        "Babatpur Airport Agro-Belt": (25.4520, 82.8590, 11),
        "Chandauli / Mughalsarai": (25.2600, 83.1600, 11),
        "Mirzapur / Vindhya Slopes": (25.1450, 82.5650, 11),
        "Jaunpur Gomti Basin": (25.7464, 82.6837, 10),
        "Ghazipur Ganga Alluvium": (25.5840, 83.5770, 10),
    }

    # Apply search filter to map display
    display_parcels = list(filtered_parcels)
    search_q = map_search_input.strip().lower()

    center_lat = origin_lat
    center_lng = origin_lng
    map_zoom = 9 if len(display_parcels) > 10 else 10

    if micro_market_jump in micro_market_coords:
        mm_lat, mm_lng, mm_zoom = micro_market_coords[micro_market_jump]
        center_lat, center_lng, map_zoom = mm_lat, mm_lng, mm_zoom

    if search_q:
        display_parcels = [
            p for p in display_parcels
            if search_q in p.get("name", "").lower()
            or search_q in p.get("location", "").lower()
            or search_q in p.get("regional_district", "").lower()
            or search_q in p.get("khasra_khatauni_number", "").lower()
            or search_q in p.get("published_news_title", "").lower()
        ]
        st.info(f"🔍 **Search Filter Active:** Found **{len(display_parcels)}** properties matching '{map_search_input}'.")
        if display_parcels:
            center_lat = float(display_parcels[0].get("lat", origin_lat))
            center_lng = float(display_parcels[0].get("lng", origin_lng))
            map_zoom = 11

    # Assign persistent serial numbers matching Tab 1 table row order
    for idx, p in enumerate(display_parcels):
        p["_serial_no"] = master_sno_map.get(str(p.get("id")), idx + 1)

    active_map_fav_filter = st.session_state.get("sb_map_fav_quick_select", "🌐 Show All on Map")

    # Filter display parcels for map if map fav quick filter is active
    map_parcels = list(display_parcels)
    if active_map_fav_filter == "⭐ Show All Favorites on Map":
        map_parcels = [p for p in map_parcels if is_favorite(str(p.get("id")), cached_set=st.session_state["favorites"])]
    elif active_map_fav_filter.startswith("👤 ") and "'s Favs on Map" in active_map_fav_filter:
        u_target = active_map_fav_filter.split("👤 ")[1].split("'s Favs on Map")[0].strip()
        map_parcels = [p for p in map_parcels if is_favorite(str(p.get("id")), username=u_target)]

    # S.No. & Multi-User Favorites Google Map Locator Bar
    loc_c1, loc_c2, loc_c3 = st.columns([2.5, 1.3, 1.0])
    with loc_c1:
        sno_options = ["🗺️ Overview (All Farmland Parcels)"]
        for p in map_parcels:
            pid = str(p.get("id"))
            master_sno = master_sno_map.get(pid, 1)
            fav_u = fav_users_by_parcel.get(pid, [])
            if fav_u:
                fav_tag = f" • ⭐ {', '.join(fav_u)}"
            elif is_favorite(pid, cached_set=st.session_state["favorites"]):
                fav_tag = " • ⭐ Favorited"
            else:
                fav_tag = ""
            sc_tag = " • 🚨 SC/ST" if (p.get("is_sc_st_land") or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")) else ""
            bigha_txt = f"{round(float(p.get('size_acres', 0))*1.6, 2)} Bigha"
            sno_options.append(f"#{master_sno}. {p.get('name')} ({p.get('regional_district', '')} • {bigha_txt}{fav_tag}{sc_tag})")

        selected_sno_label = st.selectbox(
            "🎯 Locate Farmland / Favorite by S.No. on Google Map:",
            options=sno_options,
            index=0,
            key="sb_map_sno_locator",
            help="Select any property or favorite by its exact Serial Number (#S.No.) to zoom directly into its parcel pin."
        )

    with loc_c2:
        map_fav_quick_choices = ["🌐 Show All on Map", "⭐ Show All Favorites on Map"] + [f"👤 {u}'s Favs on Map" for u in all_active_usernames]
        map_filter_idx = map_fav_quick_choices.index(active_map_fav_filter) if active_map_fav_filter in map_fav_quick_choices else 0
        sel_map_fav_quick = st.selectbox(
            "⭐ Filter Map Pins:",
            options=map_fav_quick_choices,
            index=map_filter_idx,
            key="sb_map_fav_quick_select",
            help="Focus the Google Map pins on only shortlisted favorites (visible to all or by specific investor)."
        )
        if sel_map_fav_quick != active_map_fav_filter:
            st.rerun()

    with loc_c3:
        st.write("")
        if selected_sno_label != "🗺️ Overview (All Farmland Parcels)" or sel_map_fav_quick != "🌐 Show All on Map":
            if st.button("❌ Reset Map", key="btn_reset_map_sno", use_container_width=True):
                st.session_state["sb_map_sno_locator"] = "🗺️ Overview (All Farmland Parcels)"
                st.session_state["sb_map_fav_quick_select"] = "🌐 Show All on Map"
                st.rerun()

    if sel_map_fav_quick != "🌐 Show All on Map":
        if map_parcels:
            center_lat = float(map_parcels[0]["lat"])
            center_lng = float(map_parcels[0]["lng"])
            map_zoom = 11
        else:
            st.warning(f"⚠️ No properties found for '{sel_map_fav_quick}' with current district/search filters.")

    focused_sno = None
    if selected_sno_label != "🗺️ Overview (All Farmland Parcels)":
        try:
            focused_sno = int(selected_sno_label.split(".")[0].replace("#", "").strip())
            target_p = next((p for p in map_parcels if master_sno_map.get(str(p.get("id"))) == focused_sno), None)
            if target_p is None:
                target_p = next((p for p in all_parcels if master_sno_map.get(str(p.get("id"))) == focused_sno), None)
            if target_p:
                center_lat = float(target_p["lat"])
                center_lng = float(target_p["lng"])
                map_zoom = 15
        except Exception:
            focused_sno = None

    # Map Layout & Legend Controls
    map_c1, map_c2 = st.columns([3, 1])
    with map_c2:
        st.markdown("#### 🧭 Map Legend")
        st.markdown(f"""
        - 🌟 **Dark Red Star:** Active Origin (**{center_short}**)
        - 🏷️ **Numbered Badges (#1, #2...):** Exact S.No. from Table Below
        - 🚨 **Red Badge (#S.No. 🚨):** SC/ST Owned (Section 98 Barred for General)
        - 💜 **Purple Badge (#S.No. ★):** Starred Favorite (Saved by Investor)
        - 🌿 **Green Badge (#S.No.):** Sovereign Grade A+ (Score ≥ 90)
        - 🔷 **Blue Badge (#S.No.):** Institutional Grade A (Score 75-89)
        - 🟡 **Amber Badge (#S.No.):** Operational Advisory (Score 60-74)
        - 🎯 **Golden Ring:** Focused Property (Selected by S.No.)
        - 📍 **Red Target:** Pinned / Clicked Location
        """)
        show_concentric = st.checkbox("Overlay Concentric Buffer Rings", value=True)
        if st.session_state.get("map_clicked_coord"):
            if st.button("❌ Clear Pinned Map Coordinate", use_container_width=True):
                st.session_state["map_clicked_coord"] = None
                st.rerun()

    with map_c1:
        selected_pin_obj = None
        if st.session_state.get("map_clicked_coord"):
            c_lat, c_lng = st.session_state["map_clicked_coord"]
            selected_pin_obj = {
                "lat": c_lat,
                "lng": c_lng,
                "title": "Selected Map Coordinate",
                "description": "Complete the form below to add this farmland property to the master inventory."
            }

        folium_map = create_google_farmland_map(
            parcels=map_parcels,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            origin_name=active_lm["name"],
            favorite_ids=st.session_state["favorites"],
            show_concentric_rings=show_concentric,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=map_zoom,
            selected_pin=selected_pin_obj,
            focused_sno=focused_sno,
            favorites_by_parcel=fav_users_by_parcel
        )

        st.caption("💡 **Tip:** Tap or click anywhere on the Google Map to pin coordinates and instantly add a new property!")
        map_output = st_folium(
            folium_map,
            width="100%",
            height=440,
            key="up_east_interactive_folium_map",
            returned_objects=["last_clicked"]
        )

        # Check for map clicks
        if map_output and map_output.get("last_clicked"):
            click_dict = map_output["last_clicked"]
            click_lat = round(float(click_dict["lat"]), 5)
            click_lng = round(float(click_dict["lng"]), 5)
            curr_coord = st.session_state.get("map_clicked_coord")
            if curr_coord is None or (abs(curr_coord[0] - click_lat) > 0.0001 or abs(curr_coord[1] - click_lng) > 0.0001):
                st.session_state["map_clicked_coord"] = (click_lat, click_lng)
                st.rerun()

    # -------------------------------------------------------------
    # INTERACTIVE ADD PROPERTY FORM (FROM MAP CLICK OR MANUAL PIN)
    # -------------------------------------------------------------
    is_coord_pinned = st.session_state.get("map_clicked_coord") is not None
    pinned_lat = st.session_state["map_clicked_coord"][0] if is_coord_pinned else origin_lat
    pinned_lng = st.session_state["map_clicked_coord"][1] if is_coord_pinned else origin_lng

    # Calculate real-time routing for pinned coordinates
    pinned_aerial = haversine_distance_km(origin_lat, origin_lng, pinned_lat, pinned_lng)
    pinned_road = estimate_road_distance_km(pinned_aerial)
    pinned_mins = estimate_driving_time_minutes(pinned_road)
    pinned_ring = assign_concentric_ring(pinned_aerial)

    expander_title = f"📍 ➕ Add Farmland Property from Map {'[📍 PINNED: ' + str(pinned_lat) + ', ' + str(pinned_lng) + ']' if is_coord_pinned else '(Click Map or Enter Coordinates)'}"
    with st.expander(expander_title, expanded=is_coord_pinned):
        st.markdown("#### 🌾 Discover & Register New Farmland Property")
        st.caption(f"Pre-populated with coordinates from your Google Map interaction. Actual road distance is automatically calculated from **{active_lm['name']}**.")

        # Real-time Telemetry Preview
        p_card1, p_card2, p_card3 = st.columns(3)
        with p_card1:
            st.info(f"🚗 **Actual Road Distance:** `{pinned_road} km` (~`{pinned_mins} mins` driving)")
        with p_card2:
            st.info(f"⭕ **Concentric Ring:** `{pinned_ring}`")
        with p_card3:
            st.info(f"📍 **Zero-Point:** `{center_short}`")

        with st.form("add_farmland_from_map_form", clear_on_submit=False):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                prop_name = st.text_input("Farmland Estate Name *", placeholder="e.g. Rohania Ring Road Organic Agro Estate")
                prop_district = st.selectbox(
                    "District *",
                    options=all_districts,
                    index=all_districts.index(st.session_state["filter_district"]) if st.session_state["filter_district"] in all_districts else 0
                )
                prop_location = st.text_input("Specific Village / Tehsil / Corridor *", placeholder="e.g. Village Kanchanpur, Sevapuri")
            with f_col2:
                prop_khasra = st.text_input("Khasra / Khatauni Number *", placeholder="e.g. Khasra 142/1, Khatauni 288")
                prop_approach = st.selectbox("Road Approach *", ["Direct National Highway (NH)", "Paved Bitumen Link (18-24 ft)", "Paved Rural Road (12-14 ft)", "Chak Road / Canal Service Lane"])
                prop_water = st.selectbox("Primary Water Source *", ["Dedicated Tubewell / Deep Borewell", "Canal Irrigated + Submersible", "River Lift + Open Well", "Submersible Borewell"])

            f_coord1, f_coord2 = st.columns(2)
            with f_coord1:
                prop_lat = st.number_input("Latitude (from Map Click or Manual)", value=float(pinned_lat), format="%.5f")
            with f_coord2:
                prop_lng = st.number_input("Longitude (from Map Click or Manual)", value=float(pinned_lng), format="%.5f")

            f_size1, f_size2 = st.columns(2)
            with f_size1:
                prop_acres = st.number_input("Parcel Size (Acres) *", min_value=0.5, max_value=500.0, value=5.0, step=0.5)
            with f_size2:
                prop_rate_lakhs = st.number_input("Price per Acre (₹ Lakhs) *", min_value=1.0, max_value=500.0, value=25.0, step=1.0)

            # Live unit and price calculation preview
            est_pakka_bigha = prop_acres * 1.60
            est_biswa = est_pakka_bigha * 20
            est_cr = round((prop_acres * prop_rate_lakhs) / 100.0, 2)
            st.markdown(
                f"📐 **Purvanchal Land Units:** `{est_pakka_bigha:.2f}` Pakka Bigha (`{est_biswa:.1f}` Biswa / `{est_biswa:.1f}` Kattha) • **Total Deal Ticket:** `₹{est_cr:.2f} Cr`"
            )

            f_seller1, f_seller2 = st.columns(2)
            with f_seller1:
                prop_seller_name = st.text_input("Landowner / Rep Name *", value="Landowner Representative")
            with f_seller2:
                prop_seller_phone = st.text_input("Contact Mobile Phone *", value="+91 94150 12345")

            f_caste1, f_caste2 = st.columns(2)
            with f_caste1:
                prop_seller_cat = st.selectbox(
                    "Seller Category",
                    options=["Direct Landowner / Farmer", "Broker / Mandi Aggregator", "Bank Distress Recovery Rep", "Govt Land Board"],
                    index=0
                )
            with f_caste2:
                prop_caste_cat = st.selectbox(
                    "Landowner Caste Category (UP Revenue Code Sec 98) *",
                    options=[
                        "General / OBC (Unrestricted)",
                        "SC / Dalit Landholding (Sec 98 Restricted)",
                        "ST Landholding (Sec 98 Restricted)"
                    ],
                    index=0,
                    help="Under Section 98 UP Revenue Code 2006, land held by an SC/ST Bhumidhar cannot be transferred to a non-SC/ST person without prior written sanction from the District Magistrate / Collector."
                )

            # Optional published news notice
            f_news1, f_news2 = st.columns(2)
            with f_news1:
                prop_news_title = st.text_input("Published News Headline / Gazette Notice (Optional)", placeholder="e.g. UP Bhulekh Section 34 Clean Title Gazette Notification")
            with f_news2:
                prop_news_source = st.text_input("Publication Source / E-Paper (Optional)", placeholder="e.g. Dainik Jagran Varanasi Edition")

            submit_prop = st.form_submit_button("➕ Save & Register Farmland to Master Inventory", type="primary", use_container_width=True)

            if submit_prop:
                success, msg, new_item = create_and_add_farmland(
                    name=prop_name,
                    district=prop_district,
                    location=prop_location,
                    lat=prop_lat,
                    lng=prop_lng,
                    size_acres=prop_acres,
                    price_per_acre_lakhs=prop_rate_lakhs,
                    contact_person=prop_seller_name,
                    contact_phone=prop_seller_phone,
                    seller_category=prop_seller_cat,
                    khasra_number=prop_khasra,
                    caste_category=prop_caste_cat,
                    news_title=prop_news_title,
                    news_source=prop_news_source
                )
                if success:
                    st.success(f"🎉 {msg}")
                    st.session_state["map_clicked_coord"] = None
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Error: {msg}")

    # -------------------------------------------------------------
    # PROPERTY SUMMARY TABLE IN TAB 1 (FILTERABLE BY DISTRICT)
    # -------------------------------------------------------------
    st.markdown("---")
    col_tab1_h1, col_tab1_h2 = st.columns([3.5, 1.2])
    with col_tab1_h1:
        st.markdown(f"### 📋 Property Summary & Critique AI Ledger: {st.session_state['filter_district']}")
    with col_tab1_h2:
        if st.button("🔄 Refresh Data", key="btn_tab1_refresh_data", use_container_width=True):
            with st.spinner("Refreshing farmland inventory, satellite telemetry, and road routing..."):
                st.cache_data.clear()
                scan_res = run_weekly_scan(all_parcels, force=True)
                st.session_state["favorites"] = load_favorites()
                st.session_state["property_flags"] = load_property_flags()
                st.success(f"✅ Data refreshed! Scanned {scan_res['parcels_scanned']} parcels.")
                time.sleep(0.3)
                st.rerun()

    st.caption(
        f"Showing **{len(display_parcels)}** properties matching filters. All road driving distances and driving times are calculated from **{active_lm['name']}**.\n\n"
        f"💡 **Correlation Guide:** Each property's **S.No. (#1, #2, #3...)** corresponds directly to the property dropdown in **Tab 2 (🔍 Detailed Farmland Telemetry & Dossier)** for effortless cross-referencing."
    )

    if display_parcels:
        tab1_rows = []
        for idx, p in enumerate(display_parcels):
            pid = str(p.get("id"))
            r = routings.get(pid, {})
            crit = critique_cache.get(pid, {})
            is_f = is_favorite(pid, cached_set=st.session_state["favorites"])
            f_info = get_property_flag(pid, st.session_state["property_flags"])
            status_text = "🚩 Fake" if is_fake(pid, st.session_state["property_flags"]) else ("🚫 Ignored" if is_ignored(pid, st.session_state["property_flags"]) else "Active")

            acres_val = float(p.get("size_acres", 0.0))
            total_bigha_val = round(acres_val * 1.60, 2)

            is_sc = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
            sec_stat = p.get("section_98_status", "")
            if is_sc and ("Approved" in sec_stat or "CONDITIONAL" in sec_stat):
                caste_badge = "⚠️ SC/ST (DM Sanctioned)"
            elif is_sc:
                caste_badge = "🚨 SC/ST: Barred (Sec 98)"
            else:
                caste_badge = "✅ General / OBC"

            fav_u = fav_users_by_parcel.get(pid, [])
            if fav_u:
                fav_cell = f"⭐ {', '.join(fav_u)}"
            elif is_f:
                fav_cell = "⭐ Favorited (Untagged)"
            else:
                fav_cell = "—"

            tab1_rows.append({
                "S.No.": master_sno_map.get(pid, idx + 1),
                "Fav / Shortlisted By": fav_cell,
                "Estate Name": p.get("name"),
                "Status": status_text,
                "District": p.get("regional_district"),
                "Road Dist (km)": r.get("road_km"),
                "Drive Time": r.get("driving_time_display"),
                "Radial Ring": r.get("distance_ring"),
                "Acres": acres_val,
                "Total Bigha": total_bigha_val,
                "Caste / Sec 98 Flag": caste_badge,
                "Price/Acre (₹L)": p.get("price_per_acre_lakhs"),
                "Total (₹Cr)": p.get("total_price_cr"),
                "Elevation (m)": p.get("elevation_m"),
                "Water TDS (ppm)": p.get("water_tds_ppm"),
                "DD Score": p.get("due_diligence_score"),
                "Legal Grade": p.get("due_diligence_grade"),
                "Critique AI Score": crit.get("critique_risk_score", 90),
                "Critique Risk Verdict": crit.get("critique_verdict_badge", "Pristine"),
                "Top Negative Flag / Advisory": crit.get("negative_feedbacks_summary", "Clean Audit"),
                "Govt Clearance": crit.get("primary_govt_clearance", "UP Bhulekh / IGRSUP Clear"),
                "Khatauni Caste Remark": p.get("khatauni_caste_remark", "Shreni 1-Ka General Freehold"),
                "Published News Platform": p.get("published_news_source"),
                "Notice Date": p.get("published_news_date"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })

        df_tab1 = pd.DataFrame(tab1_rows)
        # Freeze first 3 columns (S.No., Fav / Shortlisted By, Estate Name)
        tab1_col_config = {
            "S.No.": st.column_config.NumberColumn("S.No.", help="Master Serial Number matching Google Map pins and audit ledgers", pinned=True, width="small"),
            "Fav / Shortlisted By": st.column_config.TextColumn("Fav / Investor", help="Shortlisted Favorite status and investor tagging (e.g. ⭐ VPT, PPT, Guest)", pinned=True, width="medium"),
            "Estate Name": st.column_config.TextColumn("Estate Name", pinned=True, width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "District": st.column_config.TextColumn("District", width="small"),
            "Road Dist (km)": st.column_config.NumberColumn("Road Dist (km)", help=f"Driving distance from {center_short}", format="%.1f km", width="small"),
            "Drive Time": st.column_config.TextColumn("Drive Time", width="small"),
            "Radial Ring": st.column_config.TextColumn("Ring", width="small"),
            "Acres": st.column_config.NumberColumn("Acres", format="%.2f", width="small"),
            "Total Bigha": st.column_config.NumberColumn("Bigha (UP)", help="Purvanchal Pakka Bigha (1 Acre = 1.60 Pakka Bigha = 32 Biswa)", format="%.2f", width="small"),
            "Caste / Sec 98 Flag": st.column_config.TextColumn("Caste / Sec 98", help="Section 98 UP Revenue Code 2006 compliance flag.", width="medium"),
            "Price/Acre (₹L)": st.column_config.NumberColumn("Price/Ac (₹L)", format="₹%.1f L", width="small"),
            "Total (₹Cr)": st.column_config.NumberColumn("Total (₹Cr)", format="₹%.2f Cr", width="small"),
            "Elevation (m)": st.column_config.NumberColumn("Elev (m)", format="%d m", width="small"),
            "Water TDS (ppm)": st.column_config.NumberColumn("TDS (ppm)", format="%d", width="small"),
            "DD Score": st.column_config.NumberColumn("DD Score", format="%d", width="small"),
            "Critique AI Score": st.column_config.NumberColumn("Critique", help="Critique AI Score (0-100)", format="%d/100", width="small"),
            "Critique Risk Verdict": st.column_config.TextColumn("Critique Verdict", width="small"),
        }
        st.dataframe(df_tab1, use_container_width=True, height=450, column_config=tab1_col_config, hide_index=True)

        # Quick Star / Shortlist by User Expander
        with st.expander("⭐ 👤 Quick Star / Shortlist Farmland by User Profile", expanded=False):
            st.markdown("#### Save Farmland as Favorite by First Name")
            st.caption("Favorites saved under your first name are visible to all users. Each user can save multiple favorites, or remove and re-add them anytime.")
            qs_c1, qs_c2, qs_c3, qs_c4 = st.columns([2.2, 1.4, 1.2, 1.2])
            with qs_c1:
                qs_parcels_map = {f"#{master_sno_map.get(str(p.get('id')), idx+1)}. {p['name']} ({p.get('regional_district')})": str(p['id']) for idx, p in enumerate(display_parcels)}
                sel_qs_label = st.selectbox("Select Farmland Property:", options=list(qs_parcels_map.keys()), key="sel_qs_prop")
                sel_qs_pid = qs_parcels_map[sel_qs_label]
            with qs_c2:
                qs_users = list(DEFAULT_USERNAMES)
                for u in all_active_usernames:
                    if u not in qs_users:
                        qs_users.append(u)
                qs_users.append("➕ Custom Name...")
                user_def_idx = qs_users.index(st.session_state["active_user_name"]) if st.session_state["active_user_name"] in qs_users else 0
                sel_qs_user = st.selectbox("Shortlist as User:", options=qs_users, index=user_def_idx, key="sel_qs_user")
                if sel_qs_user == "➕ Custom Name...":
                    qs_custom_name = st.text_input("Enter First Name:", value="", placeholder="e.g. Ramesh", key="qs_custom_input")
                    target_user = qs_custom_name.strip() if qs_custom_name.strip() else "Guest-1"
                else:
                    target_user = sel_qs_user
                st.session_state["active_user_name"] = target_user
            with qs_c3:
                st.write("")
                if is_favorite(sel_qs_pid, username=target_user):
                    if st.button(f"★ Remove ({target_user})", key="btn_qs_rem", use_container_width=True):
                        remove_favorite(sel_qs_pid, username=target_user)
                        st.session_state["favorites"] = load_favorites()
                        st.success(f"Removed from {target_user}'s favorites.")
                        st.rerun()
                else:
                    if st.button(f"☆ Add ({target_user})", key="btn_qs_add", use_container_width=True):
                        add_favorite(sel_qs_pid, username=target_user)
                        st.session_state["favorites"] = load_favorites()
                        st.success(f"Saved to {target_user}'s favorites!")
                        st.rerun()
            with qs_c4:
                st.write("")
                already_favs = get_users_for_parcel(sel_qs_pid, raw_fav_records)
                if already_favs:
                    st.caption(f"**Favorited by:** {', '.join(already_favs)}")
                else:
                    st.caption("No favorites yet.")

        # Quick Flag & Ignore Moderation Center Expander
        with st.expander(f"🛡️ 🚫 Flagged & Ignored Listings Center ({len(get_ignored_ids(st.session_state['property_flags']))} Ignored, {len(get_fake_ids(st.session_state['property_flags']))} Fake)", expanded=False):
            st.markdown("#### Moderation Registry: Manage Ignored Holdings & Fake Listings")
            st.caption("Properties added to the Ignore List or flagged as Fake Listings are excluded from main inventory views by default to maintain a clean discovery pipeline.")

            q_col1, q_col2, q_col3 = st.columns([2.5, 1.2, 1.2])
            with q_col1:
                mod_parcels_map = {f"#{idx+1}. {p['name']} ({p.get('regional_district')})": str(p['id']) for idx, p in enumerate(all_parcels)}
                selected_mod_label = st.selectbox("Select Property to Moderate:", options=list(mod_parcels_map.keys()), key="sel_quick_mod")
                selected_mod_pid = mod_parcels_map[selected_mod_label]
            with q_col2:
                if st.button("🚫 Add to Ignore List", key="btn_quick_add_ignore", use_container_width=True):
                    set_property_flag(selected_mod_pid, "ignored", "Dismissed from active inventory by user")
                    st.session_state["property_flags"] = load_property_flags()
                    st.warning("🚫 Property moved to Ignore List!")
                    st.rerun()
            with q_col3:
                if st.button("🚩 Mark as Fake Listing", key="btn_quick_add_fake", use_container_width=True):
                    set_property_flag(selected_mod_pid, "fake", "Reported as fraudulent or deceptive listing")
                    st.session_state["property_flags"] = load_property_flags()
                    st.error("🚩 Marked as Fake Listing! Risk score downgraded to 0.")
                    st.rerun()

            current_flags = st.session_state["property_flags"]
            if current_flags:
                st.markdown("##### Currently Flagged Properties:")
                for flagged_pid, f_data in list(current_flags.items()):
                    m_parcel = next((p for p in all_parcels if str(p.get("id")) == flagged_pid), None)
                    m_title = m_parcel.get("name", f"ID: {flagged_pid}") if m_parcel else f"ID: {flagged_pid}"
                    f_badge = "🚩 Fake Listing" if f_data.get("flag") == "fake" else "🚫 Ignored"
                    fc1, fc2, fc3 = st.columns([3, 2, 1])
                    with fc1:
                        st.markdown(f"**{m_title}** — `{f_badge}`")
                    with fc2:
                        st.caption(f"{f_data.get('reason')} ({f_data.get('timestamp')})")
                    with fc3:
                        if st.button("↩️ Restore", key=f"restore_btn_{flagged_pid}", use_container_width=True):
                            remove_property_flag(flagged_pid)
                            st.session_state["property_flags"] = load_property_flags()
                            st.success("✅ Restored to active inventory!")
                            st.rerun()
    else:
        st.info("No records matching filter or search query.")

# -------------------------------------------------------------
# TAB 2: DETAILED FARMLAND TELEMETRY & LEGAL AUDIT
# -------------------------------------------------------------
with view_tabs[1]:
    st.markdown("### 🔍 Detailed Farmland Telemetry, Critique AI & Legal Audit")
    st.caption("Inspect complete dossiers with soil parameters, groundwater TDS, independent critique risk findings, and UP Bhulekh verified records.")

    # Weekly Critique AI Audit Telemetry Banner
    crit_meta = get_weekly_audit_metadata()
    cr_b1, cr_b2 = st.columns([3.5, 1.5])
    with cr_b1:
        st.info(f"📅 **Independent Critique AI Weekly Audit Engine:** Active Cycle **{crit_meta['cycle_label']}** • Cadence: {crit_meta['cadence']} • Next cycle re-audit in **{crit_meta['days_remaining']} days** ({crit_meta['next_refresh_due'][:11]}).")
    with cr_b2:
        if st.button("🔄 Force Weekly Re-audit Now", key="btn_force_critique_reaudit_t2", use_container_width=True):
            st.cache_data.clear()
            st.session_state["favorites"] = load_favorites()
            st.success(f"✅ Re-audited all holdings under weekly cycle {crit_meta['cycle_key']}!")
            st.rerun()

    # Align target parcels with Tab 1 display parcels
    target_parcels = display_parcels if display_parcels else filtered_parcels

    if target_parcels:
        farm_names = []
        for idx, p in enumerate(target_parcels):
            pid_cur = str(p["id"])
            sno_cur = master_sno_map.get(pid_cur, idx + 1)
            bigha_v = round(float(p.get("size_acres", 0.0)) * 1.60, 2)
            is_sc = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
            sc_badge = " • 🚨 SC/ST" if is_sc else ""
            farm_names.append(
                f"#{sno_cur}. {p['name']} — {p.get('regional_district', '')} ({routings.get(pid_cur, {}).get('road_km', 0.0)} km | {bigha_v} Bigha | ₹{p.get('price_per_acre_lakhs')}L/Ac{sc_badge})"
            )
        
        saved_idx = st.session_state.get("tab2_selected_idx", 0)
        if saved_idx >= len(target_parcels):
            saved_idx = 0
            
        selected_farm_idx = st.selectbox(
            "📌 Select Farmland by Serial Number (S.No. matches Tab 1 Table exactly):",
            options=range(len(target_parcels)),
            index=saved_idx,
            format_func=lambda i: farm_names[i],
            key="tab2_farm_selector"
        )
        st.session_state["tab2_selected_idx"] = selected_farm_idx

        active_farm = target_parcels[selected_farm_idx]
        active_pid = str(active_farm["id"])
        active_routing = routings[active_pid]
        active_sno = master_sno_map.get(active_pid, selected_farm_idx + 1)
        cur_fav_users = get_users_for_parcel(active_pid, raw_fav_records)
        is_fav = bool(cur_fav_users)

        st.markdown(f"#### 🏷️ Property Dossier: #{active_sno}. {active_farm.get('name')} ({active_farm.get('regional_district')})")

        # Action Controls: Multi-User Favorites, Ignore List, Fake Listing Flag
        active_flag_info = get_property_flag(active_pid, st.session_state["property_flags"])
        active_flag_type = active_flag_info.get("flag") if active_flag_info else None

        if cur_fav_users:
            badges_html = " ".join([f'<span style="background: #F3E8FF; color: #6B21A8; border: 1.5px solid #DDD6FE; border-radius: 6px; padding: 3px 8px; font-size: 12px; font-weight: 700; display: inline-block; margin-right: 4px;">👤 {u}</span>' for u in cur_fav_users])
            st.markdown(f"**⭐ Shortlisted by ({len(cur_fav_users)} Investors — Visible to All):** {badges_html}", unsafe_allow_html=True)
        else:
            st.caption("⭐ Not yet shortlisted by any investor. Use the controls below to save under your first name.")

        fav_ctl_col1, fav_ctl_col2, fav_ctl_col3, fav_ctl_col4 = st.columns([1.5, 1.3, 1.1, 1.1])
        with fav_ctl_col1:
            t2_user_list = list(DEFAULT_USERNAMES)
            for u in all_active_usernames:
                if u not in t2_user_list:
                    t2_user_list.append(u)
            t2_user_list.append("➕ Custom First Name...")

            t2_user_def_idx = t2_user_list.index(st.session_state["active_user_name"]) if st.session_state["active_user_name"] in t2_user_list else 0
            sel_t2_user = st.selectbox(
                "👤 Star / Unstar as User:",
                options=t2_user_list,
                index=t2_user_def_idx,
                key=f"tab2_fav_user_sel_{active_pid}",
                help="Select or enter your name. Defaults: VPT, PPT, Guest-1, guest-2."
            )
            if sel_t2_user == "➕ Custom First Name...":
                custom_t2_name = st.text_input("Enter First Name:", value="", placeholder="e.g. Ramesh", key=f"t2_custom_name_{active_pid}")
                effective_t2_user = custom_t2_name.strip() if custom_t2_name.strip() else "Guest-1"
            else:
                effective_t2_user = sel_t2_user
            st.session_state["active_user_name"] = effective_t2_user

        with fav_ctl_col2:
            st.write("")
            user_already_fav = is_favorite(active_pid, username=effective_t2_user)
            if user_already_fav:
                if st.button(f"★ Remove Favorite ({effective_t2_user})", key=f"fav_btn_rem_{active_pid}", use_container_width=True):
                    remove_favorite(active_pid, username=effective_t2_user)
                    st.session_state["favorites"] = load_favorites()
                    st.success(f"Removed from {effective_t2_user}'s favorites.")
                    st.rerun()
            else:
                if st.button(f"☆ Add to Favorites ({effective_t2_user})", key=f"fav_btn_add_{active_pid}", use_container_width=True):
                    add_favorite(active_pid, username=effective_t2_user)
                    st.session_state["favorites"] = load_favorites()
                    st.success(f"Saved to {effective_t2_user}'s favorites!")
                    st.rerun()

        with fav_ctl_col3:
            st.write("")
            if active_flag_type == "ignored":
                if st.button("↩️ Un-ignore", key=f"unignore_btn_{active_pid}", use_container_width=True):
                    remove_property_flag(active_pid)
                    st.session_state["property_flags"] = load_property_flags()
                    st.success("✅ Property restored to active inventory!")
                    st.rerun()
            else:
                if st.button("🚫 Add Ignore", key=f"ignore_btn_{active_pid}", use_container_width=True):
                    set_property_flag(active_pid, "ignored", "Dismissed from active discovery by user")
                    st.session_state["property_flags"] = load_property_flags()
                    st.warning("🚫 Property added to Ignore List!")
                    st.rerun()

        with fav_ctl_col4:
            st.write("")
            if active_flag_type == "fake":
                if st.button("✅ Clear Fake", key=f"unfake_btn_{active_pid}", use_container_width=True):
                    remove_property_flag(active_pid)
                    st.session_state["property_flags"] = load_property_flags()
                    st.success("✅ Fake listing flag removed!")
                    st.rerun()
            else:
                if st.button("🚩 Mark Fake", key=f"fake_btn_{active_pid}", use_container_width=True):
                    set_property_flag(active_pid, "fake", "Reported by user as fraudulent or deceptive listing")
                    st.session_state["property_flags"] = load_property_flags()
                    st.error("🚩 Marked as Fake Listing! Risk score downgraded to 0.")
                    st.rerun()

        # 1. Top Summary Card (Clean HTML rendering with matching Serial Number & Moderation Banners)
        render_html_block(render_farmland_summary_card_html(
            active_farm,
            active_routing,
            is_fav,
            serial_no=master_sno_map.get(active_pid, selected_farm_idx + 1),
            flag_info=active_flag_info,
            fav_users=cur_fav_users
        ))

        # 2. Split Columns: Agronomics & Legal/News
        col_agri, col_legal = st.columns([1.5, 1.5])
        with col_agri:
            render_html_block(render_agronomic_telemetry_html(active_farm))
        with col_legal:
            render_html_block(render_legal_and_news_card_html(active_farm))

        # 3. Independent Critique AI Risk Audit & Negative Feedbacks Dossier
        render_html_block(render_critique_ai_card_html(active_farm))

        # 4. Direct Seller Contact Card
        render_html_block(render_seller_contact_card_html(active_farm))

    else:
        st.info("No farmlands to display with current filter criteria.")

# -------------------------------------------------------------
# TAB 3: MASTER FARMLAND COMPARISON LEDGER
# -------------------------------------------------------------
with view_tabs[2]:
    col_tab3_h1, col_tab3_h2 = st.columns([3.5, 1.2])
    with col_tab3_h1:
        st.markdown("### 📊 Master Farmland Comparison Ledger")
    with col_tab3_h2:
        if st.button("🔄 Refresh Ledger Data", key="btn_tab3_refresh_data", use_container_width=True):
            with st.spinner("Refreshing farmland inventory, satellite telemetry, and road routing..."):
                st.cache_data.clear()
                scan_res = run_weekly_scan(all_parcels, force=True)
                st.session_state["favorites"] = load_favorites()
                st.session_state["property_flags"] = load_property_flags()
                st.success(f"✅ Data refreshed! Scanned {scan_res['parcels_scanned']} parcels.")
                time.sleep(0.3)
                st.rerun()

    st.caption(f"Comprehensive data ledger with road distance from **{active_lm['name']}**, Purvanchal land units (Pakka Bigha), water TDS, due diligence scores, Critique AI audits, and published news.")

    if filtered_parcels:
        table_rows = []
        for idx, p in enumerate(filtered_parcels):
            pid = str(p.get("id"))
            r = routings[pid]
            crit = critique_cache[pid]
            is_f = is_favorite(pid, cached_set=st.session_state["favorites"])
            unit = p.get("unit_meta", {})
            f_info = get_property_flag(pid, st.session_state["property_flags"])
            status_text = "🚩 Fake" if is_fake(pid, st.session_state["property_flags"]) else ("🚫 Ignored" if is_ignored(pid, st.session_state["property_flags"]) else "Active")

            acres_val = float(p.get("size_acres", 0.0))
            total_bigha_val = round(acres_val * 1.60, 2)

            is_sc = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
            sec_stat = p.get("section_98_status", "")
            if is_sc and ("Approved" in sec_stat or "CONDITIONAL" in sec_stat):
                caste_badge = "⚠️ SC/ST (DM Sanctioned)"
            elif is_sc:
                caste_badge = "🚨 SC/ST: Barred (Sec 98)"
            else:
                caste_badge = "✅ General / OBC"

            fav_u = fav_users_by_parcel.get(pid, [])
            if fav_u:
                fav_cell = f"⭐ {', '.join(fav_u)}"
            elif is_f:
                fav_cell = "⭐ Favorited (Untagged)"
            else:
                fav_cell = "—"

            table_rows.append({
                "S.No.": master_sno_map.get(pid, idx + 1),
                "Fav / Shortlisted By": fav_cell,
                "Estate Name": p.get("name"),
                "Status": status_text,
                "District": p.get("regional_district"),
                "Road Dist (km)": r.get("road_km"),
                "Drive Time": r.get("driving_time_display"),
                "Radial Ring": r.get("distance_ring"),
                "Acres": acres_val,
                "Total Bigha": total_bigha_val,
                "Biswa": round(total_bigha_val * 20, 1),
                "Caste / Sec 98 Flag": caste_badge,
                "Price/Acre (₹L)": p.get("price_per_acre_lakhs"),
                "Total (₹Cr)": p.get("total_price_cr"),
                "Elevation (m)": p.get("elevation_m"),
                "Water TDS (ppm)": p.get("water_tds_ppm"),
                "Due Diligence Score": p.get("due_diligence_score"),
                "Legal Grade": p.get("due_diligence_grade"),
                "Critique Risk Score": crit.get("critique_risk_score"),
                "Critique Verdict": crit.get("critique_risk_verdict"),
                "Negative Caveats & Grievances": crit.get("negative_feedbacks_summary"),
                "Govt Clearance": crit.get("primary_govt_clearance"),
                "Khatauni Caste Remark": p.get("khatauni_caste_remark", "UP Bhulekh Shreni 1-Ka Freehold"),
                "News Platform": p.get("published_news_source"),
                "Notice Type": p.get("notice_or_legal_type"),
                "Khasra No": p.get("khasra_khatauni_number"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })

        df_table = pd.DataFrame(table_rows)
        # Freeze first 3 columns (S.No., Fav / Shortlisted By, Estate Name)
        tab3_col_config = {
            "S.No.": st.column_config.NumberColumn("S.No.", help="Master Serial Number matching Tab 1 and Google Map pins", pinned=True, width="small"),
            "Fav / Shortlisted By": st.column_config.TextColumn("Fav / Investor", help="Shortlisted Favorite status and investor tagging", pinned=True, width="medium"),
            "Estate Name": st.column_config.TextColumn("Estate Name", pinned=True, width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "District": st.column_config.TextColumn("District", width="small"),
            "Road Dist (km)": st.column_config.NumberColumn("Road Dist (km)", help=f"Road distance from {center_short}", format="%.1f km", width="small"),
            "Drive Time": st.column_config.TextColumn("Drive Time", width="small"),
            "Radial Ring": st.column_config.TextColumn("Ring", width="small"),
            "Acres": st.column_config.NumberColumn("Acres", format="%.2f", width="small"),
            "Total Bigha": st.column_config.NumberColumn("Bigha (UP)", help="Purvanchal Pakka Bigha (1 Acre = 1.60 Pakka Bigha = 32 Biswa)", format="%.2f", width="small"),
            "Biswa": st.column_config.NumberColumn("Biswa", format="%.1f", width="small"),
            "Caste / Sec 98 Flag": st.column_config.TextColumn("Caste / Sec 98", help="Section 98 UP Revenue Code 2006 compliance flag.", width="medium"),
            "Price/Acre (₹L)": st.column_config.NumberColumn("Price/Ac (₹L)", format="₹%.1f L", width="small"),
            "Total (₹Cr)": st.column_config.NumberColumn("Total (₹Cr)", format="₹%.2f Cr", width="small"),
            "Elevation (m)": st.column_config.NumberColumn("Elev (m)", format="%d m", width="small"),
            "Water TDS (ppm)": st.column_config.NumberColumn("TDS (ppm)", format="%d", width="small"),
            "Due Diligence Score": st.column_config.NumberColumn("DD Score", format="%d", width="small"),
            "Critique Risk Score": st.column_config.NumberColumn("Critique", format="%d/100", width="small"),
        }
        st.dataframe(df_table, use_container_width=True, height=500, column_config=tab3_col_config, hide_index=True)
    else:
        st.info("No records matching filter.")

# -------------------------------------------------------------
# TAB 4: PUBLISHED NEWS & CAVEAT NOTICES
# -------------------------------------------------------------
with view_tabs[3]:
    st.markdown("### 📰 Published News, E-Auctions & Legal Caveats")
    st.caption("Verified public notices published in leading newspapers, SARFAESI bank recovery bulletins, and UP Bhulekh revenue gazettes.")

    if filtered_parcels:
        for p in filtered_parcels[:25]:
            pid = str(p.get("id"))
            r = routings[pid]
            news_title = p.get("published_news_title")
            news_src = p.get("published_news_source")
            news_date = p.get("published_news_date")
            news_url = p.get("published_news_url")
            notice_type = p.get("notice_or_legal_type")

            news_card_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 4px;">
<span style="color: #B45309; font-weight: 800; font-size: 13px;">📰 {news_src}</span>
<span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #FCD34D;">{notice_type}</span>
</div>
<div style="color: #0F172A; font-weight: 700; font-size: 15px; margin-bottom: 4px; line-height: 1.3;">{news_title}</div>
<div style="font-size: 12.5px; color: #475569; margin-bottom: 10px;">
<b>Estate:</b> {p.get('name')} • <b>District:</b> {p.get('regional_district')} • <b>Driving Distance:</b> {r.get('road_km')} km from {center_short}
</div>
<div style="display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; flex-wrap: wrap; gap: 6px;">
<span style="color: #64748B;">Published Date: {news_date}</span>
<a href="{news_url}" target="_blank" style="background: #D97706; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; min-height: 36px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(217,119,6,0.3);">Verify Original Publication ↗</a>
</div>
</div>
"""
            render_html_block(news_card_html)
    else:
        st.info("No published notices available.")

# -------------------------------------------------------------
# TAB 5: SHORTLISTED FAVORITES MATRIX
# -------------------------------------------------------------
with view_tabs[4]:
    st.markdown("### ⭐ Multi-User Shortlisted Favorites Matrix")
    st.caption("All favorites shortlisted by any investor are visible to everyone. Filter by investor profile or manage selections below.")

    t5_c1, t5_c2 = st.columns([2.5, 1.5])
    with t5_c1:
        t5_user_filter_opts = ["🌐 All Users (Combined Favorites)"] + [f"👤 {u}'s Favorites" for u in (all_active_usernames or DEFAULT_USERNAMES)]
        sel_t5_user_filter = st.selectbox(
            "👤 Filter Matrix by Investor / Username (Visible to All):",
            options=t5_user_filter_opts,
            index=0,
            key="tab5_user_filter_select",
            help="View all favorites across the team or filter by specific username."
        )

    # Determine filtered favorites for Tab 5
    if sel_t5_user_filter == "🌐 All Users (Combined Favorites)":
        fav_ids_t5 = load_favorites()
        target_u_name = None
    else:
        target_u_name = sel_t5_user_filter.split("👤 ")[1].split("'s Favorites")[0].strip()
        fav_ids_t5 = load_favorites(username=target_u_name)

    fav_parcels = [p for p in all_parcels if str(p.get("id")) in fav_ids_t5]

    if fav_parcels:
        st.success(f"Displaying **{len(fav_parcels)}** shortlisted agricultural holdings ({sel_t5_user_filter}).")
        
        fav_matrix_rows = []
        for idx, p in enumerate(fav_parcels):
            pid = str(p.get("id"))
            r = routings.get(pid, {})
            crit = critique_cache.get(pid, {})
            acres_val = float(p.get("size_acres", 0.0))
            total_bigha_val = round(acres_val * 1.60, 2)
            cur_u_list = get_users_for_parcel(pid, raw_fav_records)

            is_sc = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
            sec_stat = p.get("section_98_status", "")
            if is_sc and ("Approved" in sec_stat or "CONDITIONAL" in sec_stat):
                caste_badge = "⚠️ SC/ST (DM Sanctioned)"
            elif is_sc:
                caste_badge = "🚨 SC/ST: Barred (Sec 98)"
            else:
                caste_badge = "✅ General / OBC"

            fav_matrix_rows.append({
                "Tab 1 S.No.": master_sno_map.get(pid, idx + 1),
                "Property ID": pid,
                "Favorited By": ", ".join(cur_u_list) if cur_u_list else "Saved (Untagged)",
                "Estate Name": p.get("name"),
                "District": p.get("regional_district"),
                "Road Dist (km)": r.get("road_km"),
                "Drive Time": r.get("driving_time_display"),
                "Acres": acres_val,
                "Total Bigha": total_bigha_val,
                "Caste / Sec 98 Flag": caste_badge,
                "Price/Acre (₹L)": p.get("price_per_acre_lakhs"),
                "Total (₹Cr)": p.get("total_price_cr"),
                "Soil pH": p.get("soil_ph"),
                "Water TDS (ppm)": p.get("water_tds_ppm"),
                "Due Diligence Score": p.get("due_diligence_score"),
                "Legal Grade": p.get("due_diligence_grade"),
                "Critique Risk Score": crit.get("critique_risk_score"),
                "Top Negative Flag": crit.get("negative_feedbacks_summary"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })
        df_fav = pd.DataFrame(fav_matrix_rows)
        # Freeze first 4 columns (Tab 1 S.No., Property ID, Favorited By, Estate Name)
        fav_col_config = {
            "Tab 1 S.No.": st.column_config.NumberColumn("Tab 1 S.No.", help="Serial Number identical to Tab 1 inventory and Google Map pins", pinned=True, width="small"),
            "Property ID": st.column_config.TextColumn("Property ID", help="Unique Master Property ID", pinned=True, width="small"),
            "Favorited By": st.column_config.TextColumn("Favorited By", pinned=True, width="medium"),
            "Estate Name": st.column_config.TextColumn("Estate Name", pinned=True, width="medium"),
            "District": st.column_config.TextColumn("District", width="small"),
            "Road Dist (km)": st.column_config.NumberColumn("Road Dist (km)", help=f"Road distance from {center_short}", format="%.1f km", width="small"),
            "Drive Time": st.column_config.TextColumn("Drive Time", width="small"),
            "Acres": st.column_config.NumberColumn("Acres", format="%.2f", width="small"),
            "Total Bigha": st.column_config.NumberColumn("Bigha (UP)", help="Purvanchal Pakka Bigha (1 Acre = 1.60 Pakka Bigha)", format="%.2f", width="small"),
            "Caste / Sec 98 Flag": st.column_config.TextColumn("Caste / Sec 98", width="medium"),
            "Price/Acre (₹L)": st.column_config.NumberColumn("Price/Ac (₹L)", format="₹%.1f L", width="small"),
            "Total (₹Cr)": st.column_config.NumberColumn("Total (₹Cr)", format="₹%.2f Cr", width="small"),
            "Water TDS (ppm)": st.column_config.NumberColumn("TDS (ppm)", format="%d", width="small"),
            "Due Diligence Score": st.column_config.NumberColumn("DD Score", format="%d", width="small"),
            "Critique Risk Score": st.column_config.NumberColumn("Critique", format="%d/100", width="small"),
        }
        st.dataframe(df_fav, use_container_width=True, height=450, column_config=fav_col_config, hide_index=True)

        # Direct CSV Download for Favorites
        csv_fav_bytes = df_fav.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Shortlisted Favorites (.csv)",
            data=csv_fav_bytes,
            file_name=f"UP_East_Favorites_{sel_t5_user_filter.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=False,
            help="Download the displayed shortlisted favorites directly as a CSV spreadsheet."
        )

        st.markdown("#### 🗑️ Select & Delete Shortlisted Favorites")
        st.caption("Check the boxes next to the properties you want to remove, then click 'Delete Selected Favorites'. Unselected favorites are preserved in permanent storage.")

        del_sel_pids = []
        c_chk1, c_chk2 = st.columns(2)
        for i, p in enumerate(fav_parcels):
            pid = str(p.get("id"))
            t1_sno = master_sno_map.get(pid, i + 1)
            col_target = c_chk1 if i % 2 == 0 else c_chk2
            cur_u = get_users_for_parcel(pid, raw_fav_records)
            u_lbl = f" [Starred by: {', '.join(cur_u)}]" if cur_u else " [Starred: Untagged]"
            with col_target:
                if st.checkbox(
                    f"**#{t1_sno}**. {p.get('name')} (`{pid}`) — *{p.get('regional_district')}*{u_lbl}",
                    key=f"chk_fav_del_{pid}"
                ):
                    del_sel_pids.append(pid)

        btn_c1, btn_c2, btn_c3 = st.columns([1.6, 1.4, 1.8])
        with btn_c1:
            has_sel = len(del_sel_pids) > 0
            del_lbl = f"🗑️ Delete Selected ({len(del_sel_pids)}) Favorites" if has_sel else "🗑️ Delete Selected Favorites"
            if st.button(del_lbl, disabled=not has_sel, key="btn_del_selected_favs", use_container_width=True):
                for pid_to_del in del_sel_pids:
                    remove_favorite(pid_to_del, username=target_u_name if target_u_name else None)
                st.session_state["favorites"] = load_favorites()
                st.success(f"✅ Deleted {len(del_sel_pids)} selected favorite(s). Remaining saved favorites are safely preserved.")
                st.rerun()
        with btn_c2:
            if target_u_name:
                if st.button(f"🗑️ Clear All {target_u_name}'s", key="btn_clear_user_favs", use_container_width=True):
                    clear_all_favorites(username=target_u_name)
                    st.session_state["favorites"] = load_favorites()
                    st.success(f"Cleared all favorites for {target_u_name}.")
                    st.rerun()
            else:
                st.caption("Filter by investor above to clear individual shortlist.")
        with btn_c3:
            if st.button("🗑️ Clear All Favorites (All Users)", key="btn_clear_all_favs", use_container_width=True):
                clear_all_favorites()
                st.session_state["favorites"] = load_favorites()
                st.success("All favorites across all users cleared.")
                st.rerun()
    else:
        st.info(f"No shortlisted farmlands found for {sel_t5_user_filter}. You can add favorites in Tab 1 or Tab 2 under any username!")

# -------------------------------------------------------------
# TAB 6: EXPORT CENTER (EXCEL & CSV)
# -------------------------------------------------------------
with view_tabs[5]:
    st.markdown("### 📥 Farmland Portfolio Export Center")
    st.caption("Generate institutional-grade multi-sheet Excel workbooks and CSV files containing all spatial, financial, agronomic, Critique AI, and legal provenance columns.")

    exp_c1, exp_c2 = st.columns(2)
    with exp_c1:
        st.markdown("#### 📗 Multi-Sheet Excel Workbook (.xlsx)")
        st.markdown("""
        Includes 5 distinct worksheets:
        - **Sheet 1:** All Verified Farmlands (UP East) with all 48 columns
        - **Sheet 2:** ⭐ My Shortlisted Favorites
        - **Sheet 3:** 🤖 Independent Critique AI & Risk Audit
        - **Sheet 4:** 📰 Published News & Legal Notices
        - **Sheet 5:** 🛰️ Weekly AI-ML Spectral & Remote Sensing Telemetry
        """)

        excel_bytes = generate_excel_workbook(filtered_parcels, routings, st.session_state["favorites"])
        st.download_button(
            label="⬇️ Download UP East Farmlands Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"UP_East_Farmlands_Portfolio_{center_short.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with exp_c2:
        st.markdown("#### 📄 Master CSV Export (.csv)")
        st.markdown("""
        Standard comma-separated format compatible with Python Pandas, GIS software (QGIS, ArcGIS), and Google Sheets with Critique AI metrics.
        """)

        csv_file_path = export_master_csv(filtered_parcels, routings, st.session_state["favorites"])
        with open(csv_file_path, "rb") as f:
            csv_bytes = f.read()

        st.download_button(
            label="⬇️ Download Farmlands Master CSV (.csv)",
            data=csv_bytes,
            file_name=f"UP_East_Farmlands_Master_{center_short.replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
render_html_block(
    "<div style='text-align: center; color: #64748B; font-size: 11px; padding: 10px; line-height: 1.5;'>"
    "UP East & Varanasi Farmlands Intelligence Platform • Sentinel-2 Multispectral Telemetry • UP Bhulekh RTC Verification • Independent Critique AI Engine • Google Maps Satellite Integration"
    "</div>"
)
