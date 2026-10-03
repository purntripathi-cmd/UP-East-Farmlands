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
    load_favorites,
    toggle_favorite,
    is_favorite,
    filter_favorite_parcels
)
from utils.weekly_ml_scanner import (
    run_weekly_scan,
    get_latest_scanner_status
)
from utils.critic_ai import evaluate_property_critique
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

# Custom Styling for Professional Institutional Aesthetics, Mobile Responsiveness, and Permanent Wide Sidebar
st.markdown("""
<style>
    .main {
        background-color: #0B1120;
    }
    .stMetric {
        background: #1E293B;
        padding: 10px 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    div[data-testid="stMetricValue"] {
        font-size: 19px;
        font-weight: 700;
        color: #10B981;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 11px;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    /* Left Panel (Sidebar): Visible always, slightly wider (375px) */
    section[data-testid="stSidebar"] {
        min-width: 360px !important;
        max-width: 400px !important;
        width: 375px !important;
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem !important;
        padding-left: 1.1rem !important;
        padding-right: 1.1rem !important;
    }

    /* Keep left sidebar visible on desktop and tablet without auto-collapsing */
    @media (min-width: 768px) {
        section[data-testid="stSidebar"] {
            transform: none !important;
            display: block !important;
            visibility: visible !important;
            position: relative !important;
        }
        button[data-testid="baseButton-header"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarHeader"] > button {
            display: none !important;
        }
    }

    /* Modern Mobile Responsive Layout */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0.6rem !important;
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
        /* Mobile touch targets with min 44px ergonomics */
        button[kind="primary"], button[kind="secondary"], .stButton > button {
            min-height: 44px !important;
            font-size: 13px !important;
            border-radius: 6px !important;
        }
        /* Horizontal scroll for wide dataframes */
        div[data-testid="stDataFrame"] {
            width: 100% !important;
            overflow-x: auto !important;
        }
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
landmarks = load_landmarks()
landmark_dict = {lm["name"]: lm for lm in landmarks}
default_lm_name = next((lm["name"] for lm in landmarks if lm.get("is_default")), landmarks[0]["name"])

# Distinct Districts in Dataset
all_districts = sorted(list(set(p.get("regional_district", "Varanasi") for p in all_parcels if p.get("regional_district"))))
district_choices = ["All Districts (UP East)"] + all_districts

# -------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -------------------------------------------------------------
if "favorites" not in st.session_state:
    st.session_state["favorites"] = load_favorites()

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
    critique_cache[pid] = evaluate_property_critique(p)

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

# 5. Shortlisted Favorites Quick-Toggle
show_fav_only = st.sidebar.checkbox(
    f"⭐ Show Only My Favorites ({len(st.session_state['favorites'])})",
    value=False,
    help="Display only the parcels you have marked as favorite."
)

# 6. Price per Acre Range Slider
prices = [float(p.get("price_per_acre_lakhs", 25.0)) for p in all_parcels] if all_parcels else [25.0]
min_price, max_price = min(prices), max(prices)
selected_price_range = st.sidebar.slider(
    "Price per Acre (₹ Lakhs):",
    min_value=int(min_price),
    max_value=int(max_price) + 2,
    value=(int(min_price), int(max_price) + 2)
)

# 7. Sourcing Tier Filter
all_tiers = sorted(list(set(p.get("sourcing_tier", "Tier 1: Government Land Registry") for p in all_parcels)))
selected_tiers = st.sidebar.multiselect(
    "Sourcing Tier / Provenance:",
    options=all_tiers,
    default=all_tiers
)

# 8. Weekly AI/ML Scanner Control in Sidebar
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

# 9. CPU, RAM & Hosted Environment Telemetry Widget
st.sidebar.markdown("---")
st.sidebar.markdown("### 🖥️ Hosted System Telemetry")
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

    # Check Favorite Filter
    if show_fav_only and not is_favorite(pid, st.session_state["favorites"]):
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
    st.metric("Starred Favorites", f"{fav_count} Parcels", "Shortlist")
with kpi5:
    sys_tel = get_system_telemetry()
    st.metric("Host CPU / RAM", f"{sys_tel['app_cpu_pct']}% CPU", f"{sys_tel['app_rss_mb']}MB RSS ({sys_tel['host_ram_used_pct']}% Host)")

st.markdown("---")

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

    # Map Layout & Legend Controls
    map_c1, map_c2 = st.columns([3, 1])
    with map_c2:
        st.markdown("#### 🧭 Map Legend")
        st.markdown(f"""
        - 🌟 **Dark Red Star:** Active Origin (**{center_short}**)
        - 🟢 **20 km Ring:** Urban Fringe / Ring Road
        - 🔵 **40 km Ring:** Intermediate Ring
        - 🟡 **60 km Ring:** Regional Buffer
        - 🟣 **80 km Ring:** Outer Perimeter
        - 🔴 **100 km Ring:** Regional Boundary
        - 🌿 **Green Pin:** Sovereign Grade A+ (Score ≥ 90)
        - 🔷 **Blue Pin:** Institutional Grade A (Score 75-89)
        - 💜 **Purple Pin:** Starred Favorite
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
            parcels=display_parcels,
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            origin_name=active_lm["name"],
            favorite_ids=st.session_state["favorites"],
            show_concentric_rings=show_concentric,
            center_lat=center_lat,
            center_lng=center_lng,
            zoom_start=map_zoom,
            selected_pin=selected_pin_obj
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

            f_seller1, f_seller2, f_seller3 = st.columns(3)
            with f_seller1:
                prop_seller_name = st.text_input("Landowner / Rep Name *", value="Landowner Representative")
            with f_seller2:
                prop_seller_phone = st.text_input("Contact Mobile Phone *", value="+91 94150 12345")
            with f_seller3:
                prop_seller_cat = st.selectbox(
                    "Seller Category",
                    options=["Direct Landowner / Farmer", "Broker / Mandi Aggregator", "Bank Distress Recovery Rep", "Govt Land Board"],
                    index=0
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
    st.markdown(f"### 📋 Property Summary & Critique AI Ledger: {st.session_state['filter_district']}")
    st.caption(f"Showing **{len(display_parcels)}** properties matching filters. All road driving distances and driving times are calculated from **{active_lm['name']}**.")

    if display_parcels:
        tab1_rows = []
        for idx, p in enumerate(display_parcels):
            pid = str(p.get("id"))
            r = routings.get(pid, {})
            crit = critique_cache.get(pid, {})
            is_f = is_favorite(pid, st.session_state["favorites"])
            unit = p.get("unit_meta", {})

            tab1_rows.append({
                "S.No.": idx + 1,
                "Fav": "⭐" if is_f else "—",
                "Estate Name": p.get("name"),
                "District": p.get("regional_district"),
                f"Road Dist from {center_short[:20]} (km)": r.get("road_km"),
                "Drive Time": r.get("driving_time_display"),
                "Radial Ring": r.get("distance_ring"),
                "Acres": p.get("size_acres"),
                "Pakka Bigha": unit.get("pakka_bigha"),
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
                "Published News Platform": p.get("published_news_source"),
                "Notice Date": p.get("published_news_date"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })

        df_tab1 = pd.DataFrame(tab1_rows)
        st.dataframe(df_tab1, use_container_width=True, height=450)
    else:
        st.info("No records matching filter or search query.")

# -------------------------------------------------------------
# TAB 2: DETAILED FARMLAND TELEMETRY & LEGAL AUDIT
# -------------------------------------------------------------
with view_tabs[1]:
    st.markdown("### 🔍 Detailed Farmland Telemetry, Critique AI & Legal Audit")
    st.caption("Inspect complete dossiers with soil parameters, groundwater TDS, independent critique risk findings, and UP Bhulekh verified records.")

    if filtered_parcels:
        farm_names = [f"{p['name']} ({routings[str(p['id'])]['road_km']} km | ₹{p['price_per_acre_lakhs']}L/Acre)" for p in filtered_parcels]
        selected_farm_idx = st.selectbox(
            "Select Farmland to Inspect Full Dossier:",
            options=range(len(filtered_parcels)),
            format_func=lambda i: farm_names[i],
            key="tab2_farm_selector"
        )
        active_farm = filtered_parcels[selected_farm_idx]
        active_pid = str(active_farm["id"])
        active_routing = routings[active_pid]
        is_fav = is_favorite(active_pid, st.session_state["favorites"])

        # Favorite Toggle Button
        fav_col1, fav_col2 = st.columns([1, 4])
        with fav_col1:
            fav_btn_label = "★ Remove from Favorites" if is_fav else "☆ Add to Favorites"
            if st.button(fav_btn_label, key=f"fav_btn_tab2_{active_pid}", use_container_width=True):
                new_state = toggle_favorite(active_pid)
                st.session_state["favorites"] = load_favorites()
                st.rerun()

        with fav_col2:
            if is_fav:
                st.success("⭐ This farmland is in your Shortlisted Favorites!")

        # 1. Top Summary Card (Clean HTML rendering)
        render_html_block(render_farmland_summary_card_html(active_farm, active_routing, is_fav))

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
    st.markdown("### 📊 Master Farmland Comparison Ledger")
    st.caption(f"Comprehensive data ledger with road distance from **{active_lm['name']}**, Purvanchal land units (Pakka Bigha), water TDS, due diligence scores, Critique AI audits, and published news.")

    if filtered_parcels:
        table_rows = []
        for idx, p in enumerate(filtered_parcels):
            pid = str(p.get("id"))
            r = routings[pid]
            crit = critique_cache[pid]
            is_f = is_favorite(pid, st.session_state["favorites"])
            unit = p.get("unit_meta", {})

            table_rows.append({
                "S.No.": idx + 1,
                "Fav": "⭐" if is_f else "—",
                "Estate Name": p.get("name"),
                "District": p.get("regional_district"),
                f"Road Dist from {center_short[:20]} (km)": r.get("road_km"),
                "Drive Time": r.get("driving_time_display"),
                "Radial Ring": r.get("distance_ring"),
                "Acres": p.get("size_acres"),
                "Pakka Bigha": unit.get("pakka_bigha"),
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
                "News Platform": p.get("published_news_source"),
                "Notice Type": p.get("notice_or_legal_type"),
                "Khasra No": p.get("khasra_khatauni_number"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })

        df_table = pd.DataFrame(table_rows)
        st.dataframe(df_table, use_container_width=True, height=500)
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
<div style="background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 14px; margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 4px;">
<span style="color: #FBBF24; font-weight: 700; font-size: 13px;">📰 {news_src}</span>
<span style="background: #451A03; color: #FDE68A; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{notice_type}</span>
</div>
<div style="color: #F8FAFC; font-weight: 600; font-size: 14px; margin-bottom: 4px;">{news_title}</div>
<div style="font-size: 12px; color: #94A3B8; margin-bottom: 8px;">
<b>Estate:</b> {p.get('name')} • <b>District:</b> {p.get('regional_district')} • <b>Driving Distance:</b> {r.get('road_km')} km from {center_short}
</div>
<div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; flex-wrap: wrap; gap: 6px;">
<span style="color: #64748B;">Published Date: {news_date}</span>
<a href="{news_url}" target="_blank" style="background: #D97706; color: white; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-weight: 600; min-height: 40px; display: inline-flex; align-items: center;">Verify Original Publication ↗</a>
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
    st.markdown("### ⭐ My Shortlisted Favorites Matrix")
    fav_parcels = filter_favorite_parcels(all_parcels, st.session_state["favorites"])

    if fav_parcels:
        st.success(f"You have shortlisted **{len(fav_parcels)}** preferred agricultural holdings.")
        
        fav_matrix_rows = []
        for idx, p in enumerate(fav_parcels):
            pid = str(p.get("id"))
            r = routings.get(pid, {})
            crit = critique_cache.get(pid, {})
            unit = p.get("unit_meta", {})
            fav_matrix_rows.append({
                "S.No.": idx + 1,
                "Estate Name": p.get("name"),
                "District": p.get("regional_district"),
                f"Road Distance from {center_short[:20]} (km)": r.get("road_km"),
                "Driving Time": r.get("driving_time_display"),
                "Acres": p.get("size_acres"),
                "Pakka Bigha": unit.get("pakka_bigha"),
                "Price / Acre (₹ Lakhs)": p.get("price_per_acre_lakhs"),
                "Total Price (₹ Cr)": p.get("total_price_cr"),
                "Soil pH": p.get("soil_ph"),
                "Water TDS (ppm)": p.get("water_tds_ppm"),
                "Due Diligence Score": p.get("due_diligence_score"),
                "Legal Grade": p.get("due_diligence_grade"),
                "Critique Risk Score": crit.get("critique_risk_score"),
                "Top Negative Flag": crit.get("negative_feedbacks_summary"),
                "Contact": f"{p.get('contact_person')} ({p.get('contact_phone')})"
            })
        st.dataframe(pd.DataFrame(fav_matrix_rows), use_container_width=True)

        if st.button("🗑️ Clear All Favorites", type="secondary"):
            st.session_state["favorites"] = set()
            from utils.favorites_manager import save_favorites
            save_favorites(set())
            st.rerun()
    else:
        st.info("You haven't shortlisted any farmlands as favorites yet. Click the ⭐ button on any farmland card to add it here.")

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
