"""
Unit and Integration Test Suite for UP East Farmlands
Verifies:
- Land unit conversions (Pakka Bigha, Biswa, Kattha, Dhur)
- Geo-routing & actual road distance from Kacheri Varanasi
- Google Maps turn-by-turn URL formatting
- Concentric radial ring categorizations
- Persistent favorites toggling and storage
- Weekly AI/ML scanner execution, duplicate suppression, and SQLite persistence
- Independent Critique AI risk audit, negative feedback findings, and govt portal records
- System telemetry (CPU, RAM, Uptime)
- Google Maps Folium generator
- HTML card renderers and clean_html whitespace protection
- Multi-sheet Excel workbook and CSV exports with Critique AI
- Dataset schema integrity across all parcels
"""

import os
import json
import sqlite3
import pytest
import folium

from utils.land_units import (
    LandUnitConverter,
    ACRES_PER_PAKKA_BIGHA,
    PAKKA_BIGHA_PER_ACRE
)
from utils.geo_routing import (
    DEFAULT_ORIGIN_LAT,
    DEFAULT_ORIGIN_LNG,
    DEFAULT_ORIGIN_NAME,
    haversine_distance_km,
    estimate_road_distance_km,
    estimate_driving_time_minutes,
    get_google_maps_directions_url,
    get_google_maps_satellite_search_url,
    get_google_maps_pin_url,
    assign_concentric_ring,
    compute_parcel_routing,
    load_landmarks,
    DISTRICT_CITY_CENTERS,
    get_city_center_for_district
)
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
    save_property_flags,
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
    init_state_db,
    run_weekly_scan,
    get_latest_scanner_status,
    calculate_spectral_indices,
    get_db_path
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
    render_seller_contact_card_html,
    _extract_crops_telemetry
)
from utils.excel_exporter import generate_excel_workbook, export_master_csv
from utils.farmland_repository import create_and_add_farmland, load_all_parcels, save_all_parcels


@pytest.fixture
def sample_parcel():
    return {
        "id": "test_farm_001",
        "name": "Rohania Ring Road Organic Agro Estate",
        "regional_district": "Varanasi",
        "regional_state": "Uttar Pradesh",
        "location": "Rohania Bypass, Varanasi",
        "lat": 25.2650,
        "lng": 82.9120,
        "size_acres": 3.0,
        "price_per_acre_lakhs": 45.0,
        "total_price_cr": 1.35,
        "elevation_m": 80,
        "soil_type": "Rich Gangetic Silt Loam",
        "soil_ph": 7.3,
        "organic_carbon_pct": 0.88,
        "water_source": "Dedicated Borewell",
        "water_tds_ppm": 210,
        "groundwater_depth_ft": 160,
        "drip_irrigation_installed": True,
        "power_supply": "3-Phase Dedicated Line",
        "supported_crops": {
            "high_value_crops": "Certified Sandalwood & Hass Avocado",
            "horticulture_fruits": "VNR Bihi Guava & Langra Mango",
            "cash_crops_staples": "Kala Namak Rice & Mustard",
            "soil_suitability_score": 98
        },
        "annual_agro_yield_estimate_lakhs": 14.0,
        "due_diligence_score": 96,
        "due_diligence_grade": "A+ Sovereign Grade",
        "due_diligence_verdict": "🟢 Ready to Register — Bankable",
        "due_diligence_breakdown": ["Verified on Bhulekh", "No SARFAESI debt"],
        "khasra_khatauni_number": "Khatauni #245, Khasra 89/1",
        "title_status": "Freehold Clear Title",
        "revenue_record_type": "UP Bhulekh Certified",
        "farmhouse_permission": "Allowed",
        "road_approach": "20-ft Bitumen Road",
        "fencing": "Full Chain-Link",
        "sourcing_tier": "Tier 1: Government Land Registry",
        "sourcing_tier_badge": "🏛️ Tier 1: Govt Registry",
        "published_news_title": "Dainik Jagran: Varanasi Ring Road Phase 2 Agro Zone Notification",
        "published_news_source": "Dainik Jagran Varanasi Edition",
        "published_news_date": "02 Oct 2026",
        "published_news_url": "https://epaper.jagran.com/epaper/city/varanasi",
        "notice_or_legal_type": "30-Day Public Title Caveat Cleared",
        "seller_category": "Direct Landowner / Farmer",
        "contact_person": "Raghvendra Pratap Singh",
        "contact_phone": "+91 94152 11223",
        "contact_whatsapp": "https://wa.me/919415211223",
        "spectral": {
            "ndvi": 0.76,
            "crop_classification": "High Vigour Orchard",
            "confidence_pct": 94.5
        },
        "freshness_timestamp": "03 Oct 2026, 19:30 IST"
    }


# ============================================================
# 1. LAND UNIT CONVERSIONS TESTS
# ============================================================
def test_land_unit_conversions():
    meta = LandUnitConverter.calculate_all_units(1.0)
    assert meta["acres"] == 1.0
    assert meta["pakka_bigha"] == 1.6
    assert meta["biswa"] == 32.0
    assert meta["kattha"] == 32.0
    assert meta["dhur"] == 640.0
    assert meta["sq_feet"] == 43560.0


# ============================================================
# 2. GEO-ROUTING & ROAD DISTANCE TESTS
# ============================================================
def test_kacheri_origin_default():
    landmarks = load_landmarks()
    default_lm = next((lm for lm in landmarks if lm.get("is_default")), None)
    assert default_lm is not None
    assert "Kacheri Varanasi near Varuna Pul" in default_lm["name"]


def test_haversine_and_road_routing(sample_parcel):
    routing = compute_parcel_routing(
        sample_parcel,
        DEFAULT_ORIGIN_LAT,
        DEFAULT_ORIGIN_LNG,
        DEFAULT_ORIGIN_NAME
    )
    assert routing["road_km"] >= routing["aerial_km"]
    assert "https://www.google.com/maps/dir/" in routing["google_directions_url"]


def test_concentric_ring_assignment():
    assert assign_concentric_ring(12.5) == "Within 20 km"
    assert assign_concentric_ring(34.0) == "20 to 40 km"
    assert assign_concentric_ring(52.0) == "40 to 60 km"
    assert assign_concentric_ring(75.0) == "60 to 80 km"
    assert assign_concentric_ring(95.0) == "80 to 100 km"


# ============================================================
# 3. FAVORITES PERSISTENCE TESTS
# ============================================================
def test_favorites_manager():
    test_id = "test_fav_xyz_123"
    toggle_favorite(test_id)
    assert is_favorite(test_id)
    # Verify backward compatibility when 2nd argument is a set
    fav_set = {test_id, "other_id"}
    assert is_favorite(test_id, fav_set)
    assert not is_favorite("not_in_set", fav_set)
    toggle_favorite(test_id)
    assert not is_favorite(test_id)


# ============================================================
# 4. INDEPENDENT CRITIQUE AI AUDIT TESTS
# ============================================================
def test_independent_critique_ai(sample_parcel):
    crit = evaluate_property_critique(sample_parcel)
    assert "critique_risk_score" in crit
    assert 50 <= crit["critique_risk_score"] <= 100
    assert "critique_risk_verdict" in crit
    assert "negative_feedbacks_list" in crit
    assert len(crit["negative_feedbacks_list"]) >= 1
    assert "govt_site_details" in crit
    govt = crit["govt_site_details"]
    assert "UP Bhulekh" in govt["up_bhulekh_rtc"]
    assert "IGRSUP" in govt["igrsup_barah_sala"]
    assert "CGRMS" in govt["jansunwai_status"]


# ============================================================
# 5. DUPLICATE-FREE WEEKLY SCANNER TESTS
# ============================================================
def test_duplicate_free_scanner(sample_parcel):
    init_state_db()
    # First run: inserts as new
    rep1 = run_weekly_scan([sample_parcel], force=True)
    assert rep1["status"] == "COMPLETED"

    # Second run without changes: MUST suppress duplicates!
    rep2 = run_weekly_scan([sample_parcel], force=True)
    assert rep2["status"] == "COMPLETED"
    assert rep2["duplicates_suppressed"] >= 1
    assert rep2["new_parcels_added"] == 0


# ============================================================
# 6. SYSTEM TELEMETRY TESTS
# ============================================================
def test_system_telemetry():
    tel = get_system_telemetry()
    assert "app_cpu_pct" in tel
    assert "host_cpu_pct" in tel
    assert "app_rss_mb" in tel
    assert tel["app_rss_mb"] > 0
    assert "host_total_ram_gb" in tel
    assert "python_version" in tel
    assert "process_uptime" in tel

    html = render_system_telemetry_html()
    assert "Host & App Performance" in html
    assert "App RAM" in html


# ============================================================
# 7. HTML RENDERING & CLEAN_HTML PROTECTION
# ============================================================
def test_clean_html_and_no_code_blocks(sample_parcel):
    routing = compute_parcel_routing(sample_parcel)
    
    summary_html = render_farmland_summary_card_html(sample_parcel, routing, is_fav=True, serial_no=7)
    # Ensure no leading whitespace on lines that would trigger Markdown 4-space code block
    for line in summary_html.splitlines():
        assert not line.startswith("    "), f"Indented line detected: {line}"
    assert "Actual Driving Road Distance" in summary_html
    assert "S.No. #7" in summary_html

    critique_html = render_critique_ai_card_html(sample_parcel)
    assert "Independent Critique AI Risk Audit" in critique_html
    assert "Government Portal Cross-Verification" in critique_html

    clean_test = clean_html("   <!-- comment -->\n   <div>Test</div>\n")
    assert "comment" not in clean_test
    assert clean_test == "<div>Test</div>"


# ============================================================
# 8. EXCEL AND CSV EXPORTER TESTS WITH CRITIQUE AI
# ============================================================
def test_excel_and_csv_exports(sample_parcel):
    routing = compute_parcel_routing(sample_parcel)
    routings = {sample_parcel["id"]: routing}

    excel_bytes = generate_excel_workbook([sample_parcel], routings, {"test_farm_001"})
    assert len(excel_bytes) > 2000

    csv_path = export_master_csv([sample_parcel], routings, {"test_farm_001"})
    assert os.path.exists(csv_path)
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    assert "Critique AI Risk Score" in content
    assert "Negative Feedbacks & Red Flags" in content
    assert "UP Bhulekh Section 34 Mutation" in content


# ============================================================
# 9. MASTER DATASET SCHEMA INTEGRITY
# ============================================================
def test_master_dataset_integrity():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "up_east_farmlands.json")
    with open(data_path, "r", encoding="utf-8") as f:
        parcels = json.load(f)

    assert len(parcels) >= 100
    for p in parcels:
        assert p.get("id")
        assert p.get("name")
        assert p.get("published_news_url")
        assert p.get("notice_or_legal_type")


# ============================================================
# 10. MAP DISCOVERY & DYNAMIC PROPERTY ADDITION TEST
# ============================================================
def test_map_discovery_and_add_farmland():
    initial_parcels = load_all_parcels()
    count_before = len(initial_parcels)

    test_lat, test_lng = 25.4215, 82.8874
    success, msg, new_farm = create_and_add_farmland(
        name="Automated Test Babatpur Agri Orchard",
        district="Varanasi",
        location="Babatpur Airport Road, Varanasi",
        lat=test_lat,
        lng=test_lng,
        size_acres=4.5,
        price_per_acre_lakhs=32.0,
        contact_person="Ramesh Chandra",
        contact_phone="+91 94150 99887",
        seller_category="Direct Landowner / Farmer",
        khasra_number="Khasra 219/4"
    )

    assert success is True
    assert new_farm is not None
    assert new_farm["size_acres"] == 4.5
    assert new_farm["unit_meta"]["pakka_bigha"] == 7.2
    assert "critique_ai" in new_farm
    assert new_farm["critique_ai"]["critique_risk_score"] > 0

    # Verify parcel in master dataset
    after_parcels = load_all_parcels()
    assert len(after_parcels) == count_before + 1

    # Clean up test parcel
    cleaned = [p for p in after_parcels if p.get("id") != new_farm["id"]]
    save_all_parcels(cleaned)
    assert len(load_all_parcels()) == count_before


# ============================================================
# 11. DISTRICT CITY CENTERS RESOLUTION & ROUTING TESTS
# ============================================================
def test_district_city_centers_resolution():
    """Verifies that all 11+ districts map to valid city center benchmarks."""
    expected_districts = [
        "Varanasi", "Chandauli", "Mirzapur", "Jaunpur",
        "Ghazipur", "Azamgarh", "Prayagraj", "Bhadohi",
        "Sonbhadra", "Ballia", "Mau"
    ]
    for d in expected_districts:
        assert d in DISTRICT_CITY_CENTERS
        center = DISTRICT_CITY_CENTERS[d]
        assert "lat" in center and "lng" in center and "name" in center
        assert 24.0 <= center["lat"] <= 27.0
        assert 81.0 <= center["lng"] <= 85.0

    # Test get_city_center_for_district (case-insensitive)
    chandauli_center = get_city_center_for_district("Chandauli")
    assert "Chandauli" in chandauli_center["name"]
    assert chandauli_center["lat"] == 25.2600
    assert chandauli_center["lng"] == 83.2650

    mirzapur_center = get_city_center_for_district("mirzapur")
    assert "Mirzapur" in mirzapur_center["name"]
    assert mirzapur_center["lat"] == 25.1480

    jaunpur_center = get_city_center_for_district("Jaunpur")
    assert "Jaunpur" in jaunpur_center["name"]
    assert jaunpur_center["lat"] == 25.7464

    # Default fallback for All Districts
    default_center = get_city_center_for_district("All Districts (UP East)")
    assert "Kacheri Varanasi" in default_center["name"]


def test_routing_from_respective_city_center():
    """Verifies that when a district filter is applied, distance is calculated from that district's city center."""
    chandauli_center = get_city_center_for_district("Chandauli")
    chandauli_parcel = {
        "name": "Chandauli Chakia Canal Farm",
        "lat": 25.2700,
        "lng": 83.2800,
        "size_acres": 10.0,
        "price_per_acre_lakhs": 18.0
    }

    # Route from Chandauli City Center
    chandauli_routing = compute_parcel_routing(
        chandauli_parcel,
        chandauli_center["lat"],
        chandauli_center["lng"],
        chandauli_center["name"]
    )
    # Distance from Chandauli City Center should be very close (~2-4 km)
    assert chandauli_routing["road_km"] < 5.0
    assert chandauli_routing["origin_name"] == chandauli_center["name"]
    assert "origin=25.26000,83.26500" in chandauli_routing["google_directions_url"]

    # When routed from Varanasi Kacheri, the same parcel would be ~35-40 km away
    varanasi_center = get_city_center_for_district("Varanasi")
    varanasi_routing = compute_parcel_routing(
        chandauli_parcel,
        varanasi_center["lat"],
        varanasi_center["lng"],
        varanasi_center["name"]
    )
    assert varanasi_routing["road_km"] > 30.0
    assert "origin=25.33750,82.98150" in varanasi_routing["google_directions_url"]


# ============================================================
# 15. PROPERTY FLAGS & MODERATION TESTS (FAKE / IGNORE)
# ============================================================
def test_property_flags_manager():
    """Verifies setting, retrieving, and removing fake and ignored property flags."""
    test_fake_id = "test_fake_pid_999"
    test_ignore_id = "test_ignore_pid_888"

    # Set fake listing
    set_property_flag(test_fake_id, "fake", "Reported fake seller credentials")
    flags = load_property_flags()
    assert is_fake(test_fake_id, flags)
    assert not is_ignored(test_fake_id, flags)
    assert test_fake_id in get_fake_ids(flags)

    # Set ignore listing
    set_property_flag(test_ignore_id, "ignored", "Not interested in flood basin")
    flags = load_property_flags()
    assert is_ignored(test_ignore_id, flags)
    assert not is_fake(test_ignore_id, flags)
    assert test_ignore_id in get_ignored_ids(flags)

    # Test filtering logic with flags
    mock_parcels = [
        {"id": test_fake_id, "name": "Fake Land Listing"},
        {"id": test_ignore_id, "name": "Ignored Riverbed Holding"},
        {"id": "legit_pid_111", "name": "Legitimate Agro Estate"}
    ]

    # By default, fake and ignored are excluded
    filtered_default = filter_parcels_by_flag_status(mock_parcels, show_ignored=False, show_fake=False, flags_dict=flags)
    assert len(filtered_default) == 1
    assert filtered_default[0]["id"] == "legit_pid_111"

    # When including ignored
    filtered_with_ignored = filter_parcels_by_flag_status(mock_parcels, show_ignored=True, show_fake=False, flags_dict=flags)
    assert len(filtered_with_ignored) == 2

    # When including fake
    filtered_with_fake = filter_parcels_by_flag_status(mock_parcels, show_ignored=False, show_fake=True, flags_dict=flags)
    assert len(filtered_with_fake) == 2

    # Cleanup flags
    remove_property_flag(test_fake_id)
    remove_property_flag(test_ignore_id)
    cleared_flags = load_property_flags()
    assert not is_fake(test_fake_id, cleared_flags)
    assert not is_ignored(test_ignore_id, cleared_flags)


def test_summary_card_flag_banners(sample_parcel):
    """Verifies that render_farmland_summary_card_html displays fake and ignored warnings when flagged."""
    routing = compute_parcel_routing(sample_parcel, DEFAULT_ORIGIN_LAT, DEFAULT_ORIGIN_LNG, DEFAULT_ORIGIN_NAME)

    # Normal clean rendering
    html_clean = render_farmland_summary_card_html(sample_parcel, routing, is_fav=False, serial_no=1)
    assert "ALERT: Flagged by User as Fake Listing" not in html_clean
    assert "NOTICE: Property Added to Ignore List" not in html_clean

    # Fake listing rendering
    fake_flag = {"flag": "fake", "reason": "Reported fake survey number", "timestamp": "03 Oct 2026, 21:00 IST"}
    html_fake = render_farmland_summary_card_html(sample_parcel, routing, is_fav=False, serial_no=1, flag_info=fake_flag)
    assert "ALERT: Flagged by User as Fake Listing / Fraud" in html_fake
    assert "Reported fake survey number" in html_fake
    assert "🚩 FAKE LISTING" in html_fake

    # Ignored listing rendering
    ignore_flag = {"flag": "ignored", "reason": "Dismissed by user", "timestamp": "03 Oct 2026, 21:00 IST"}
    html_ignored = render_farmland_summary_card_html(sample_parcel, routing, is_fav=False, serial_no=1, flag_info=ignore_flag)
    assert "NOTICE: Property Added to Ignore List" in html_ignored
    assert "🚫 IGNORED" in html_ignored


def test_freeze_columns_column_config():
    """Verifies that Streamlit column configuration formats pin the first 3 columns correctly."""
    import streamlit as st
    tab1_config = {
        "S.No.": st.column_config.NumberColumn("S.No.", pinned=True, width="small"),
        "Fav": st.column_config.TextColumn("Fav", pinned=True, width="small"),
        "Estate Name": st.column_config.TextColumn("Estate Name", pinned=True, width="medium"),
    }
    # Validate pinned attribute
    assert tab1_config["S.No."]["pinned"] is True
    assert tab1_config["Fav"]["pinned"] is True
    assert tab1_config["Estate Name"]["pinned"] is True


def test_sc_st_land_critique_penalty_and_flag(sample_parcel):
    """Verifies that SC/ST owned properties receive Section 98 red flag penalty, high risk verdict, and warning banners."""
    sc_parcel = dict(sample_parcel)
    sc_parcel["caste_category"] = "SC / Dalit Landholding (Sec 98 Restricted)"
    sc_parcel["is_sc_st_land"] = True
    sc_parcel["section_98_status"] = "🚨 RESTRICTED: No DM Permission (Barred for General Buyers)"
    sc_parcel["khatauni_caste_remark"] = "Khatauni Shreni 1-Ka: Restricted SC Tenure Holder u/s 98 UP Revenue Code 2006."

    critique = evaluate_property_critique(sc_parcel)
    assert critique["critique_risk_verdict"] == "🚨 HIGH RISK: SC/ST Landholding (Sec 98 Barred for General Buyers)"
    assert critique["critique_risk_score"] <= 55
    assert "Section 98 UP Revenue Code" in critique["negative_feedbacks_summary"]
    assert any("Section 98 UP Revenue Code 2006" in item for item in critique["negative_feedbacks_list"])

    # Test summary card HTML rendering
    routing = compute_parcel_routing(sc_parcel, DEFAULT_ORIGIN_LAT, DEFAULT_ORIGIN_LNG, DEFAULT_ORIGIN_NAME)
    summary_html = render_farmland_summary_card_html(sc_parcel, routing, is_fav=False, serial_no=1)
    assert "RED FLAG: SC/ST OWNED PROPERTY — SECTION 98 UP REVENUE CODE RESTRICTION" in summary_html
    assert "🚨 SC/ST RESTRICTED (Sec 98)" in summary_html

    # Test legal and news card HTML rendering
    legal_html = render_legal_and_news_card_html(sc_parcel)
    assert "Caste Category & Sec 98" in legal_html
    assert "Restricted SC Tenure Holder" in legal_html


def test_total_bigha_purvanchal_conversion():
    """Verifies that 1 Acre = 1.60 Pakka Bigha standard across Purvanchal."""
    assert round(5.0 * 1.60, 2) == 8.0
    assert round(2.5 * 1.60, 2) == 4.0
    assert round(1.25 * 1.60, 2) == 2.0
    conv = LandUnitConverter.calculate_all_units(5.0)
    assert conv["pakka_bigha"] == 8.0
    assert conv["biswa"] == 160.0


def test_google_farmland_map_sno_div_icons_and_focus(sample_parcel):
    """Verifies that create_google_farmland_map plots S.No. DivIcon badges and supports focused_sno zooming."""
    sample_parcel["_serial_no"] = 1
    sample_parcel["is_sc_st_land"] = True
    parcels = [sample_parcel]

    # Map with focused S.No.
    m = create_google_farmland_map(
        parcels=parcels,
        origin_lat=DEFAULT_ORIGIN_LAT,
        origin_lng=DEFAULT_ORIGIN_LNG,
        origin_name=DEFAULT_ORIGIN_NAME,
        focused_sno=1
    )
    assert isinstance(m, folium.Map)
    map_html = m.get_root().render()
    # Check that S.No. badge #1 and SC/ST RED FLAG warning are rendered
    assert "#1" in map_html
    assert "RED FLAG: SC/ST Owned" in map_html
    # Check that focused circle tooltip exists
    assert "Focused Farmland S.No. #1" in map_html


def test_all_dataset_parcels_have_sc_st_metadata():
    """Verifies all master parcels contain caste_category, is_sc_st_land, and section_98_status fields."""
    parcels = load_all_parcels()
    assert len(parcels) >= 110
    sc_st_count = 0
    for p in parcels:
        assert "caste_category" in p, f"Missing caste_category in parcel {p.get('id')}"
        assert "is_sc_st_land" in p, f"Missing is_sc_st_land in parcel {p.get('id')}"
        assert "section_98_status" in p, f"Missing section_98_status in parcel {p.get('id')}"
        assert "khatauni_caste_remark" in p, f"Missing khatauni_caste_remark in parcel {p.get('id')}"
        if p["is_sc_st_land"]:
            sc_st_count += 1
    assert sc_st_count >= 10, f"Expected realistic SC/ST test parcels, found {sc_st_count}"


# ============================================================
# 16. MULTI-USER FAVORITES, LIGHT BUTTONS & MAP INTEGRATION TESTS
# ============================================================
def test_multi_user_favorites_default_usernames():
    """Verifies that DEFAULT_USERNAMES contains VPT, PPT, Guest-1, guest-2."""
    assert "VPT" in DEFAULT_USERNAMES
    assert "PPT" in DEFAULT_USERNAMES
    assert "Guest-1" in DEFAULT_USERNAMES
    assert "guest-2" in DEFAULT_USERNAMES


def test_multi_user_favorites_lifecycle():
    """Verifies adding, filtering, user attribution, removing and re-adding favorites across multiple users."""
    p1 = "farm_multi_test_01"
    p2 = "farm_multi_test_02"

    # Add favorite for VPT
    add_favorite(p1, username="VPT")
    assert is_favorite(p1, username="VPT")
    assert not is_favorite(p1, username="PPT")
    assert is_favorite(p1)  # Visible to all

    # Add same property for PPT and different property for Guest-1
    add_favorite(p1, username="PPT")
    add_favorite(p2, username="Guest-1")

    users_p1 = get_users_for_parcel(p1)
    assert "VPT" in users_p1
    assert "PPT" in users_p1
    assert "Guest-1" not in users_p1

    users_p2 = get_users_for_parcel(p2)
    assert users_p2 == ["Guest-1"]

    # Active usernames list includes defaults and active users
    active_users = get_all_active_usernames()
    assert "VPT" in active_users
    assert "PPT" in active_users
    assert "Guest-1" in active_users

    # Remove favorite for VPT only; PPT must remain intact
    remove_favorite(p1, username="VPT")
    assert not is_favorite(p1, username="VPT")
    assert is_favorite(p1, username="PPT")
    assert is_favorite(p1)  # Still visible to all via PPT

    # Re-add favorite for VPT
    add_favorite(p1, username="VPT")
    assert is_favorite(p1, username="VPT")

    # Custom first name support
    add_favorite(p2, username="Ramesh")
    assert is_favorite(p2, username="Ramesh")
    assert "Ramesh" in get_users_for_parcel(p2)

    # Clean up test parcels
    remove_favorite(p1, username="VPT")
    remove_favorite(p1, username="PPT")
    remove_favorite(p2, username="Guest-1")
    remove_favorite(p2, username="Ramesh")


def test_google_map_multi_user_favorites_rendering(sample_parcel):
    """Verifies that create_google_farmland_map renders user badges and shortlist chips."""
    sample_parcel["_serial_no"] = 1
    fav_map = {str(sample_parcel["id"]): ["VPT", "PPT"]}

    m = create_google_farmland_map(
        parcels=[sample_parcel],
        origin_lat=DEFAULT_ORIGIN_LAT,
        origin_lng=DEFAULT_ORIGIN_LNG,
        origin_name=DEFAULT_ORIGIN_NAME,
        favorites_by_parcel=fav_map
    )
    assert isinstance(m, folium.Map)
    html = m.get_root().render()
    # Check that tooltip and popup display saved by VPT and PPT
    assert "Saved by VPT, PPT" in html
    assert "Shortlisted by:" in html
    assert "VPT" in html
    assert "PPT" in html


def test_white_light_button_styling_enforced_in_app():
    """Verifies that app.py CSS enforces white/light button styles and contains no black button styles."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Check button styling rules
    assert "background-color: #FFFFFF !important" in code or "background: #FFFFFF !important" in code
    assert ".stButton > button" in code
    assert "border: 1.5px solid #CBD5E1 !important" in code
    # Ensure there is no rule setting button background to black (#000 or #000000 or black)
    assert "background: #000000" not in code
    assert "background-color: #000000" not in code
    assert "background: #000" not in code
    assert "background-color: black" not in code


def test_streamlit_light_theme_and_white_header_config():
    """Verifies that .streamlit/config.toml and app.py enforce white header and light theme (no black bars)."""
    config_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "config.toml")
    with open(config_path, "r", encoding="utf-8") as f:
        toml_content = f.read()

    assert 'base = "light"' in toml_content
    assert 'backgroundColor = "#FFFFFF"' in toml_content
    assert "#0B1120" not in toml_content  # No dark black background
    assert "#1E293B" not in toml_content

    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    assert 'header[data-testid="stHeader"]' in app_code
    assert 'div[data-testid="stTabs"]' in app_code


def test_google_maps_satellite_and_pin_urls(sample_parcel):
    """Verifies that satellite URL uses &t=k to avoid errors and that direct pin URL is generated."""
    lat = float(sample_parcel["lat"])
    lng = float(sample_parcel["lng"])
    
    sat_url = get_google_maps_satellite_search_url(lat, lng)
    assert "&t=k" in sat_url
    assert f"q={lat:.6f},{lng:.6f}" in sat_url
    assert "+(" not in sat_url  # No invalid query syntax
    
    pin_url = get_google_maps_pin_url(lat, lng)
    assert f"query={lat:.6f},{lng:.6f}" in pin_url
    
    routing = compute_parcel_routing(sample_parcel)
    assert "google_satellite_url" in routing
    assert "&t=k" in routing["google_satellite_url"]
    assert "google_maps_pin_url" in routing

    summary_html = render_farmland_summary_card_html(sample_parcel, routing)
    assert "Open in Google Maps" in summary_html
    assert "Satellite Pin" in summary_html
    assert "Google Turn-by-Turn" in summary_html
    # Ensure no dark button styling #475569
    assert "background: #475569" not in summary_html


def test_critique_ai_govt_portal_source_links_and_maps_locator(sample_parcel):
    """Verifies that Critique AI renders official government portal verification links and Google Maps pin."""
    critique_html = render_critique_ai_card_html(sample_parcel)
    
    # Official portal links must be present and clickable
    assert "upbhulekh.gov.in" in critique_html
    assert "igrsup.gov.in" in critique_html
    assert "jansunwai.up.nic.in" in critique_html
    assert "upgroundwater.in" in critique_html
    assert "🔗 UP Bhulekh Source ↗" in critique_html
    assert "🔗 IGRSUP Registry Source ↗" in critique_html
    assert "🔗 Jansunwai Grievance Portal ↗" in critique_html
    assert "🔗 UPGWD NOC Registry ↗" in critique_html

    # Location launcher
    assert "Open Specific Location in Google Maps ↗" in critique_html
    assert "Satellite Pin ↗" in critique_html


def test_table_column_header_text_wrapping_and_compact_headers():
    """Verifies that app.py CSS enforces column header text wrapping and compact column names."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # CSS text wrapping rules
    assert "word-wrap: break-word" in app_code
    assert "overflow-wrap: break-word" in app_code
    assert "div[role=\"columnheader\"]" in app_code
    
    # Check that verbose headers like Road Distance from Kacheri Varanasi nea have been replaced with compact headers
    assert '"Road Dist (km)"' in app_code


def test_critique_ai_weekly_refresh_engine():
    """Verifies that Critique AI includes weekly refresh metadata and deterministic cycle cadence."""
    from utils.critic_ai import get_weekly_audit_metadata, evaluate_property_critique
    from utils.farmland_view import render_critique_ai_card_html

    meta = get_weekly_audit_metadata()
    assert "cycle_key" in meta
    assert "cycle_label" in meta
    assert "Week" in meta["cycle_label"]
    assert "Weekly" in meta["cadence"] and "7 Days" in meta["cadence"]
    assert meta["days_remaining"] >= 0
    assert "next_refresh_due" in meta

    sample_farm = {
        "id": "agri200_var_001",
        "name": "Babatpur Agro Parcel",
        "soil_ph": 7.2,
        "water_tds_ppm": 320,
        "due_diligence_score": 88
    }
    critique = evaluate_property_critique(sample_farm)
    assert "Weekly" in critique["weekly_refresh_cadence"]
    assert "audit_cycle" in critique
    assert critique["audit_cycle"] == meta["cycle_label"]
    assert "next_weekly_refresh" in critique

    html = render_critique_ai_card_html(critique)
    assert "Critique AI Weekly Cycle:" in html
    assert "Auto-refreshes Every 7 Days" in html


def test_favorites_checkbox_selective_deletion_preserves_remaining(monkeypatch):
    """Verifies that selective deletion of specific favorites preserves all other favorited items."""
    import tempfile
    from utils.favorites_manager import save_raw_favorites, load_favorites, remove_favorite, add_favorite

    # Create temporary isolated favorites file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_file = tf.name

    try:
        monkeypatch.setattr("utils.favorites_manager.get_favorites_file_path", lambda: temp_file)

        # Seed with 3 favorites
        add_favorite("p1", username="VPT")
        add_favorite("p2", username="PPT")
        add_favorite("p3", username="Guest-1")

        cur_favs = load_favorites()
        assert cur_favs == {"p1", "p2", "p3"}

        # Delete only p2 (simulating checkbox select and delete)
        remove_favorite("p2")

        remaining_favs = load_favorites()
        assert "p2" not in remaining_favs
        assert "p1" in remaining_favs  # Preserved!
        assert "p3" in remaining_favs  # Preserved!
        assert len(remaining_favs) == 2

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_top_text_visibility_and_sidebar_flex_css():
    """Verifies CSS contains institutional padding to prevent top text cut-off and margin clipping."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Block container top and side padding
    assert "padding-top: 3.5rem !important;" in app_code
    assert "padding-left: 2rem !important;" in app_code
    assert "padding-right: 2rem !important;" in app_code

    # Sidebar top padding
    assert "section[data-testid=\"stSidebar\"] > div:first-child" in app_code
    
    # Tab 5 preserved S.No. and Property ID column headers
    assert '"Tab 1 S.No."' in app_code
    assert '"Property ID"' in app_code

    # 1-click Starred Favorites toggle in KPI
    assert "btn_kpi_fav_filter_toggle" in app_code


def test_untagged_and_legacy_favorites_consolidation(monkeypatch):
    """Verifies that favorites without a username or from legacy string formats are preserved as Untagged and visible."""
    import tempfile
    import json
    from utils.favorites_manager import load_raw_favorites, save_raw_favorites, load_favorites, is_favorite, get_users_for_parcel

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_file = tf.name

    try:
        # Pre-seed isolated file with legacy string, untagged dict, and tagged dict
        seed_data = [
            "legacy_parcel_001",
            {"parcel_id": "untagged_parcel_002", "username": ""},
            {"parcel_id": "tagged_parcel_003", "username": "VPT"}
        ]
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(seed_data, f)

        monkeypatch.setattr("utils.favorites_manager.get_favorites_file_path", lambda: temp_file)

        raw = load_raw_favorites()
        assert len(raw) == 3

        # Check all are recognized as favorites
        all_favs = load_favorites()
        assert "legacy_parcel_001" in all_favs
        assert "untagged_parcel_002" in all_favs
        assert "tagged_parcel_003" in all_favs
        assert is_favorite("legacy_parcel_001") is True
        assert is_favorite("untagged_parcel_002") is True
        assert is_favorite("tagged_parcel_003") is True

        # Check user tags
        assert get_users_for_parcel("legacy_parcel_001") == ["Untagged"]
        assert get_users_for_parcel("untagged_parcel_002") == ["Untagged"]
        assert get_users_for_parcel("tagged_parcel_003") == ["VPT"]

        # Ensure saving raw preserves untagged without dropping them
        assert save_raw_favorites(raw) is True
        raw_reloaded = load_raw_favorites()
        assert len(raw_reloaded) == 3
        reloaded_ids = {r["parcel_id"] for r in raw_reloaded}
        assert reloaded_ids == {"legacy_parcel_001", "untagged_parcel_002", "tagged_parcel_003"}

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_user_specific_favorites_filtering(monkeypatch):
    """Verifies that favorites can be filtered strictly by specific user or Untagged."""
    import tempfile
    from utils.favorites_manager import save_raw_favorites, load_favorites, is_favorite, filter_favorite_parcels

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_file = tf.name

    try:
        monkeypatch.setattr("utils.favorites_manager.get_favorites_file_path", lambda: temp_file)

        sample_records = [
            {"parcel_id": "p_vpt", "username": "VPT"},
            {"parcel_id": "p_ppt", "username": "PPT"},
            {"parcel_id": "p_guest", "username": "Guest-1"},
            {"parcel_id": "p_none", "username": "Untagged"},
        ]
        save_raw_favorites(sample_records)

        # VPT favorites
        vpt_favs = load_favorites(username="VPT")
        assert vpt_favs == {"p_vpt"}
        assert is_favorite("p_vpt", username="VPT") is True
        assert is_favorite("p_ppt", username="VPT") is False

        # PPT favorites
        ppt_favs = load_favorites(username="PPT")
        assert ppt_favs == {"p_ppt"}

        # Untagged favorites
        untagged_favs = load_favorites(username="Untagged")
        assert untagged_favs == {"p_none"}

        # All favorites combined
        all_favs = load_favorites()
        assert all_favs == {"p_vpt", "p_ppt", "p_guest", "p_none"}

        mock_parcels = [{"id": "p_vpt"}, {"id": "p_ppt"}, {"id": "p_guest"}, {"id": "p_other"}]
        vpt_parcels = filter_favorite_parcels(mock_parcels, username="VPT")
        assert len(vpt_parcels) == 1
        assert vpt_parcels[0]["id"] == "p_vpt"

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_tab1_ledger_fav_column_and_telemetry_sidebar_placement():
    """Verifies that Tab 1 ledger has dedicated Fav/Shortlist column with medium width and telemetry is inside sidebar."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_code = f.read()

    # Telemetry must be rendered inside st.sidebar
    assert "render_system_telemetry_html()" in app_code
    assert "with st.sidebar:" in app_code

    # Tab 1 column config has Fav / Shortlisted By with medium width and pinned
    assert '"Fav / Shortlisted By": st.column_config.TextColumn("Fav / Investor"' in app_code
    assert 'pinned=True, width="medium"' in app_code

    # Tab 1 rows check both fav_u and is_f
    assert 'fav_cell = f"⭐ {\', \'.join(fav_u)}"' in app_code
    assert 'fav_cell = "⭐ Favorited (Untagged)"' in app_code

    # S.No. preservation in map locator
    assert 'master_sno_map.get(str(p.get("id")), idx + 1)' in app_code


def test_github_ai_agent_module_and_rule_fallback():
    """Verifies that GitHub AI agent initializes, falls back safely without a token, and answers domain queries."""
    from utils.github_ai_agent import (
        query_farmland_agent,
        probe_best_github_model,
        get_available_github_token,
        generate_local_rule_agent_response,
        CANDIDATE_GITHUB_MODELS
    )

    # 1. Candidate models are prioritized properly
    assert "gpt-4o-mini" in CANDIDATE_GITHUB_MODELS
    assert "Meta-Llama-3.1-70B-Instruct" in CANDIDATE_GITHUB_MODELS

    # 2. Probe with empty or dummy token
    m, msg = probe_best_github_model("")
    assert m is None
    assert "No token provided" in msg

    # 3. Test knowledge responses
    mock_parcels = [
        {
            "id": "p1",
            "name": "Kashi Polyhouse Farmland",
            "regional_district": "Varanasi",
            "size_acres": 5.0,
            "price_per_acre_lakhs": 45.0,
            "total_price_cr": 2.25,
            "is_sc_st_land": True,
            "caste_category": "SC (Section 98 Restricted)",
            "water_tds_ppm": 220,
            "due_diligence_score": 88,
            "critique_ai_score": 60,
            "soil_type": "Ganga Alluvial Loam",
            "road_access_width_ft": 30
        },
        {
            "id": "p2",
            "name": "Chandauli Agro Park",
            "regional_district": "Chandauli",
            "size_acres": 10.0,
            "price_per_acre_lakhs": 25.0,
            "total_price_cr": 2.5,
            "is_sc_st_land": False,
            "caste_category": "General",
            "water_tds_ppm": 280,
            "due_diligence_score": 92,
            "critique_ai_score": 90,
            "soil_type": "Alluvial Clay Loam",
            "road_access_width_ft": 40
        }
    ]

    # Query: SC/ST
    res_sc = query_farmland_agent("What are the rules for SC ST land under Section 98?", [], mock_parcels, "Varanasi Kacheri")
    assert "Section 98" in res_sc["response"]
    assert "District Collector" in res_sc["response"] or "DM" in res_sc["response"]
    assert res_sc["is_live_llm"] is False

    # Query: Bigha conversion
    res_bigha = query_farmland_agent("How many Bigha in an Acre in Purvanchal?", [], mock_parcels, "Varanasi Kacheri")
    assert "1.60" in res_bigha["response"]
    assert "Pakka Bigha" in res_bigha["response"]

    # Query: Water TDS
    res_water = query_farmland_agent("What is water TDS salinity threshold?", [], mock_parcels, "Varanasi Kacheri")
    assert "TDS" in res_water["response"]
    assert "300 ppm" in res_water["response"]


def test_help_agent_button_visibility_on_all_tabs_and_dialog():
    """Verifies that the Help / AI Agent button is wired in top header, sidebar, and Tab 2, and dialog is defined."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Help button in top header (visible across all tabs)
    assert 'btn_top_header_ai_help' in code
    assert 'Help / Ask AI Agent' in code

    # Help button in sidebar (permanently visible on all tabs)
    assert 'btn_sidebar_ai_agent_help' in code
    assert 'Open AI Agent Chat' in code

    # Dialog defined with dismiss callback and persistence flag
    assert '@st.dialog("🌾 UP East Farmlands AI Advisor & Legal Agent"' in code
    assert 'show_farmland_ai_agent_dialog' in code
    assert 'show_ai_agent_modal' in code
    assert 'on_close_ai_dialog_callback' in code
    assert 'btn_dlg_close_modal' in code

    # Distinct color card styling for User Question vs AI Response
    assert 'ai-chat-bubble-user' in code
    assert 'ai-chat-bubble-assistant' in code
    assert '#EFF6FF' in code  # Soft blue user bubble
    assert '#10B981' in code  # Emerald AI response accent border

    # Model probe action wired in dialog
    assert 'probe_best_github_model' in code
    assert 'dlg_gh_token_input' in code
    assert 'Check & Select Best Model' in code


def test_ai_agent_modal_persistence_and_distinct_color_bubbles():
    """Verifies that the dialog modal uses session_state persistence, preserves chat history, and differentiates colors."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Modal persistence logic
    assert 'st.session_state["show_ai_agent_modal"] = True' in code
    assert 'if st.session_state.get("show_ai_agent_modal", False):' in code
    assert 'show_farmland_ai_agent_dialog(all_parcels, active_lm["name"])' in code

    # Dismiss callback resets flag
    assert 'def on_close_ai_dialog_callback' in code
    assert 'st.session_state["show_ai_agent_modal"] = False' in code

    # Explicit Close button
    assert 'btn_dlg_close_modal' in code
    assert '✖ Close' in code

    # Color difference checks:
    # User Question: Soft blue background #EFF6FF, blue accent border #2563EB, Investor Query header
    assert '👤 Your Question (Investor Query)' in code
    assert '#2563EB' in code
    assert '#EFF6FF' in code

    # AI Response: Soft card with emerald accent border #10B981, AI Legal Audit badge
    assert '🌾 UP East Farmland AI Advisor & Legal Agent' in code
    assert 'AI Legal Audit' in code
    assert '#10B981' in code


def test_google_maps_terrain_default_click_zoom_and_default_location_button(sample_parcel):
    """Verifies that Google Maps Terrain is the default layer, scroll-zoom is locked until click, and default location buttons exist."""
    # 1. Test create_google_farmland_map layer configuration
    m = create_google_farmland_map(
        parcels=[sample_parcel],
        origin_lat=DEFAULT_ORIGIN_LAT,
        origin_lng=DEFAULT_ORIGIN_LNG,
        origin_name=DEFAULT_ORIGIN_NAME
    )
    map_html = m.get_root().render()

    # Terrain must be present and configured
    assert "Google Maps Terrain" in map_html
    assert "mt1.google.com/vt/lyrs=p" in map_html

    # scrollWheelZoom must be disabled on init
    assert '"scrollWheelZoom": false' in map_html

    # Click-to-zoom controller must attach click and mouseout handlers
    assert "scrollWheelZoom.enable()" in map_html
    assert "scrollWheelZoom.disable()" in map_html

    # 2. Test app.py wiring for Default Location buttons and stable zoom
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        code = f.read()

    # Default location buttons visible above map and on sidebar
    assert 'btn_reset_map_default_loc' in code
    assert 'btn_legend_default_loc' in code
    assert '📍 Default Location' in code

    # Map heading specifies Google Maps Terrain as default
    assert 'Google Maps Terrain' in code

    # Default zoom is stable at 10 (does not randomly change to 9 or 11 on search)
    assert 'map_zoom = 10' in code

    # Callbacks must be wired with on_click to prevent StreamlitWidgetAlreadyInstantiatedError
    assert 'def reset_to_default_location_callback' in code
    assert 'on_click=reset_to_default_location_callback' in code
    assert 'def clear_pinned_coord_callback' in code
    assert 'on_click=clear_pinned_coord_callback' in code







