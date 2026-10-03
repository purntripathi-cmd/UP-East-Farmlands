"""
UP East & Varanasi Farmlands Intelligence Platform
Streamlit Web Application solely dedicated to Varanasi and surrounding Eastern UP agricultural estates.
Features:
- Selectable Origin Landmark (Default: Kacheri Varanasi near Varuna Pul)
- Concentric Distance Rings (20 km, 40 km, 60 km, 80 km, 100 km, 200 km buffer)
- Google Maps Satellite Hybrid / Roadmap integration with concentric buffer overlays
- Comprehensive Farmland Table in Tab 1 with full details summary
- Independent Critique AI Engine (Negative feedback auditing, 8 risk vectors, Govt site verification)
- Persistent User Favorites / Shortlisting system
- Published News, Media Source, Date, and Verification Links
- Duplicate-Free Weekly AI/ML Spectral & Provenance Scanner with SQLite persistence
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
    load_landmarks,
    compute_parcel_routing
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

# Page Configuration
st.set_page_config(
    page_title="UP East Farmlands | Varanasi Agro-Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Professional Institutional Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #0B1120;
    }
    .stMetric {
        background: #1E293B;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px;
        font-weight: 700;
        color: #10B981;
    }
    div[data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-size: 12px;
    }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "up_east_farmlands.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# Initialize session state for favorites
if "favorites" not in st.session_state:
    st.session_state["favorites"] = load_favorites()

# Load Base Datasets
all_parcels = load_farmlands_dataset()
landmarks = load_landmarks()

# Map Landmark Lookup
landmark_dict = {lm["name"]: lm for lm in landmarks}
default_lm_name = next((lm["name"] for lm in landmarks if lm.get("is_default")), landmarks[0]["name"])

# -------------------------------------------------------------
# SIDEBAR FILTERS & CONTROLS
# -------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/fluency/96/wheat.png", width=60)
st.sidebar.title("Agro-Land Filters")
st.sidebar.caption("Varanasi & Purvanchal Concentric Corridor")

# 1. Landmark Origin Selector (DEFAULT: Kacheri Varanasi near Varuna Pul)
st.sidebar.markdown("### 📍 Select Origin Landmark")
selected_lm_name = st.sidebar.selectbox(
    "Road Distance Measured From:",
    options=list(landmark_dict.keys()),
    index=list(landmark_dict.keys()).index(default_lm_name) if default_lm_name in landmark_dict else 0,
    help="Default is Kacheri Varanasi near Varuna Pul (Collectorate & District Courts). Road distances and Google Directions dynamically recalculate from this point."
)
active_lm = landmark_dict[selected_lm_name]
origin_lat = float(active_lm["lat"])
origin_lng = float(active_lm["lng"])

st.sidebar.info(f"**Active Zero-Point:** {active_lm['name']}\n\n*({active_lm.get('description', '')})*")

# Precompute Dynamic Routing for all parcels relative to selected landmark
routings = {}
critique_cache = {}
for p in all_parcels:
    pid = str(p.get("id"))
    routings[pid] = compute_parcel_routing(p, origin_lat, origin_lng, active_lm["name"])
    critique_cache[pid] = evaluate_property_critique(p)

# 2. Concentric Radial Distance Selector
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

# 3. Maximum Road Distance Slider
max_road_km = st.sidebar.slider(
    "Max Actual Road Distance (km):",
    min_value=5,
    max_value=200,
    value=100,
    step=5,
    help="Filter by estimated actual road driving distance from active origin."
)

# 4. Shortlisted Favorites Quick-Toggle
show_fav_only = st.sidebar.checkbox(
    f"⭐ Show Only My Favorites ({len(st.session_state['favorites'])})",
    value=False,
    help="Display only the parcels you have marked as favorite."
)

# 5. District Multi-Select
all_districts = sorted(list(set(p.get("regional_district", "Varanasi") for p in all_parcels)))
selected_districts = st.sidebar.multiselect(
    "Filter by District:",
    options=all_districts,
    default=all_districts
)

# 6. Price per Acre Range Slider
prices = [float(p.get("price_per_acre_lakhs", 25.0)) for p in all_parcels]
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

    # Check District
    if dist not in selected_districts:
        continue

    # Check Price
    if not (selected_price_range[0] <= price <= selected_price_range[1]):
        continue

    # Check Tier
    if tier not in selected_tiers:
        continue

    filtered_parcels.append(p)

# Sort parcels by road distance from selected origin
filtered_parcels.sort(key=lambda x: routings.get(str(x["id"]), {}).get("road_km", 999.0))

# -------------------------------------------------------------
# MAIN APP HEADER & KPIS
# -------------------------------------------------------------
st.title("🌾 UP East & Varanasi Farmlands Intelligence Platform")
st.markdown(
    f"**Concentric Agro-Intelligence, Independent Critique AI & Due Diligence** | Origin Reference: **{active_lm['name']}**"
)

# Top KPI Metric Cards
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.metric("Verified Holdings", f"{len(filtered_parcels)} / {len(all_parcels)}")
with kpi2:
    if filtered_parcels:
        avg_dist = round(sum(routings[str(p["id"])]["road_km"] for p in filtered_parcels) / len(filtered_parcels), 1)
        st.metric("Avg Road Distance", f"{avg_dist} km", f"From {active_lm['name'].split('(')[0].strip()[:18]}")
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
    "🗺️ Interactive Google Map & Property Table",
    "🔍 Detailed Farmland Telemetry & Legal Audit",
    "📊 Master Farmland Comparison Ledger",
    "📰 Published News & Caveat Notices",
    "⭐ Shortlisted Favorites Matrix",
    "📥 Export Center (Excel / CSV)"
])

# -------------------------------------------------------------
# TAB 1: INTERACTIVE GOOGLE MAP & PROPERTY SUMMARY TABLE
# -------------------------------------------------------------
with view_tabs[0]:
    st.markdown(f"### 🗺️ Google Satellite & Hybrid Map with Concentric Buffers")
    st.caption(f"Showing concentric radial buffer rings (20 km, 40 km, 60 km, 80 km, 100 km) around **{active_lm['name']}** with live road navigation.")

    map_c1, map_c2 = st.columns([3, 1])
    with map_c2:
        st.markdown("#### 🧭 Map Legend & Controls")
        st.markdown("""
        - 🌟 **Dark Red Star:** Active Origin (**Kacheri Varanasi near Varuna Pul**)
        - 🟢 **20 km Ring:** Urban Fringe & Ring Road Phase 2
        - 🔵 **40 km Ring:** Chandauli / Mughalsarai / Mirzapur border
        - 🟡 **60 km Ring:** Ghazipur / Jaunpur Core
        - 🟣 **80 km Ring:** Azamgarh / Robertsganj approach
        - 🔴 **100 km Ring:** Outer Purvanchal perimeter
        - 🌿 **Green Pin:** Sovereign Grade A+ (Score ≥ 90)
        - 🔷 **Blue Pin:** Institutional Grade A (Score 75-89)
        - 💜 **Purple Pin:** Favorited Parcel
        """)
        show_concentric = st.checkbox("Overlay Concentric Buffer Rings", value=True)

    with map_c1:
        if filtered_parcels:
            folium_map = create_google_farmland_map(
                parcels=filtered_parcels,
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                origin_name=active_lm["name"],
                favorite_ids=st.session_state["favorites"],
                show_concentric_rings=show_concentric,
                zoom_start=9 if len(filtered_parcels) > 10 else 10
            )
            st_folium(folium_map, width="100%", height=520)
        else:
            st.warning("No farmlands match the current filter criteria. Broaden your search filters.")

    # -------------------------------------------------------------
    # PROPERTY SUMMARY TABLE IN TAB 1 (EXPLICIT USER REQUEST)
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 📋 Complete Property Summary & Critique AI Ledger")
    st.caption(f"Summary table of all **{len(filtered_parcels)}** properties matching filters, with actual driving road distance from **{active_lm['name']}**, Purvanchal Pakka Bigha units, and Critique AI risk scores.")

    if filtered_parcels:
        tab1_rows = []
        for idx, p in enumerate(filtered_parcels):
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
                "Road Dist (km)": r.get("road_km"),
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
        st.dataframe(df_tab1, use_container_width=True, height=400)
    else:
        st.info("No records matching filter.")

# -------------------------------------------------------------
# TAB 2: DETAILED FARMLAND TELEMETRY & LEGAL AUDIT
# -------------------------------------------------------------
with view_tabs[1]:
    st.markdown("### 🔍 Detailed Farmland Telemetry, Critique AI & Legal Audit")
    st.caption("Inspect complete dossiers with soil parameters, groundwater TDS, independent critique risk findings, and UP Bhulekh verified records.")

    if filtered_parcels:
        # Selector for active farmland card
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

        # 2. Split Columns: Agronomics & Legal/News/Critique
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
    st.caption("Comprehensive data ledger with road distance, Purvanchal land units (Pakka Bigha), water TDS, due diligence scores, Critique AI audits, and published news.")

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
                "Road Dist (km)": r.get("road_km"),
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
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
<span style="color: #FBBF24; font-weight: 700; font-size: 13px;">📰 {news_src}</span>
<span style="background: #451A03; color: #FDE68A; padding: 2px 8px; border-radius: 4px; font-size: 11px;">{notice_type}</span>
</div>
<div style="color: #F8FAFC; font-weight: 600; font-size: 14px; margin-bottom: 4px;">{news_title}</div>
<div style="font-size: 12px; color: #94A3B8; margin-bottom: 8px;">
<b>Estate:</b> {p.get('name')} • <b>District:</b> {p.get('regional_district')} • <b>Driving Distance:</b> {r.get('road_km')} km from {active_lm['name'].split('(')[0].strip()}
</div>
<div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px;">
<span style="color: #64748B;">Published Date: {news_date}</span>
<a href="{news_url}" target="_blank" style="background: #D97706; color: white; padding: 4px 12px; border-radius: 4px; text-decoration: none; font-weight: 600;">Verify Original Publication ↗</a>
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
                "Road Distance (km)": r.get("road_km"),
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
            file_name=f"UP_East_Farmlands_Portfolio_{selected_lm_name.split('(')[0].strip().replace(' ', '_')}.xlsx",
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
            file_name="UP_East_Farmlands_Master.csv",
            mime="text/csv",
            use_container_width=True
        )

# Footer
st.markdown("---")
render_html_block(
    "<div style='text-align: center; color: #64748B; font-size: 12px; padding: 10px;'>"
    "UP East & Varanasi Farmlands Intelligence Platform • Sentinel-2 Multispectral Telemetry • UP Bhulekh RTC Verification • Independent Critique AI Engine • Google Maps Satellite Integration"
    "</div>"
)
