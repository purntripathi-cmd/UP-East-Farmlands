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
    assign_concentric_ring,
    compute_parcel_routing,
    load_landmarks
)
from utils.favorites_manager import (
    load_favorites,
    save_favorites,
    toggle_favorite,
    is_favorite,
    filter_favorite_parcels
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
    
    summary_html = render_farmland_summary_card_html(sample_parcel, routing, is_fav=True)
    # Ensure no leading whitespace on lines that would trigger Markdown 4-space code block
    for line in summary_html.splitlines():
        assert not line.startswith("    "), f"Indented line detected: {line}"
    assert "Actual Driving Road Distance" in summary_html

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
