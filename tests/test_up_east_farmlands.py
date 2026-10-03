"""
Unit and Integration Test Suite for UP East Farmlands
Verifies:
- Land unit conversions (Pakka Bigha, Biswa, Kattha, Dhur)
- Geo-routing & actual road distance from Kacheri Varanasi
- Google Maps turn-by-turn URL formatting
- Concentric radial ring categorizations
- Persistent favorites toggling and storage
- Weekly AI/ML scanner execution and SQLite persistence
- Google Maps Folium generator
- HTML card renderers and news verification links
- Multi-sheet Excel workbook and CSV exports
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
from utils.google_map_view import create_google_farmland_map
from utils.farmland_view import (
    render_farmland_summary_card_html,
    render_agronomic_telemetry_html,
    render_legal_and_news_card_html,
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

    meta_5 = LandUnitConverter.calculate_all_units(5.0)
    assert meta_5["pakka_bigha"] == 8.0
    assert "8.00 Pakka Bigha" in meta_5["pakka_bigha_display"]


# ============================================================
# 2. GEO-ROUTING & ROAD DISTANCE TESTS
# ============================================================
def test_kacheri_origin_default():
    landmarks = load_landmarks()
    default_lm = next((lm for lm in landmarks if lm.get("is_default")), None)
    assert default_lm is not None
    assert "Kacheri Varanasi near Varuna Pul" in default_lm["name"]
    assert abs(default_lm["lat"] - DEFAULT_ORIGIN_LAT) < 0.001
    assert abs(default_lm["lng"] - DEFAULT_ORIGIN_LNG) < 0.001


def test_haversine_and_road_routing(sample_parcel):
    routing = compute_parcel_routing(
        sample_parcel,
        DEFAULT_ORIGIN_LAT,
        DEFAULT_ORIGIN_LNG,
        DEFAULT_ORIGIN_NAME
    )
    assert routing["aerial_km"] > 0
    assert routing["road_km"] >= routing["aerial_km"]
    assert routing["driving_minutes"] > 0
    assert "https://www.google.com/maps/dir/" in routing["google_directions_url"]
    assert f"origin={DEFAULT_ORIGIN_LAT:.5f},{DEFAULT_ORIGIN_LNG:.5f}" in routing["google_directions_url"]


def test_concentric_ring_assignment():
    assert assign_concentric_ring(12.5) == "Within 20 km"
    assert assign_concentric_ring(34.0) == "20 to 40 km"
    assert assign_concentric_ring(52.0) == "40 to 60 km"
    assert assign_concentric_ring(75.0) == "60 to 80 km"
    assert assign_concentric_ring(95.0) == "80 to 100 km"
    assert assign_concentric_ring(145.0) == "100 to 200 km Buffer"


# ============================================================
# 3. FAVORITES PERSISTENCE TESTS
# ============================================================
def test_favorites_manager():
    initial = load_favorites()
    test_id = "test_fav_xyz_999"

    # Ensure clean starting state
    if test_id in initial:
        toggle_favorite(test_id)

    # Toggle to add
    res = toggle_favorite(test_id)
    assert res is True
    assert is_favorite(test_id)

    # Toggle to remove
    res_off = toggle_favorite(test_id)
    assert res_off is False
    assert not is_favorite(test_id)


# ============================================================
# 4. WEEKLY AI/ML SCANNER TESTS
# ============================================================
def test_weekly_ml_scanner(sample_parcel):
    init_state_db()
    report = run_weekly_scan([sample_parcel], force=True)
    assert report["status"] == "COMPLETED"
    assert report["parcels_scanned"] == 1
    assert "SCAN_" in report["scan_id"]

    status = get_latest_scanner_status()
    assert status["has_run"] is True
    assert status["parcels_scanned"] >= 1

    # Check SQLite contents
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT parcel_id, ndvi_index, crop_class FROM parcel_spectral_telemetry WHERE parcel_id = ?", ("test_farm_001",))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "test_farm_001"
    assert 0.4 <= row[1] <= 0.9


# ============================================================
# 5. GOOGLE MAP GENERATION TESTS
# ============================================================
def test_google_farmland_map_creation(sample_parcel):
    m = create_google_farmland_map(
        [sample_parcel],
        origin_lat=DEFAULT_ORIGIN_LAT,
        origin_lng=DEFAULT_ORIGIN_LNG,
        origin_name=DEFAULT_ORIGIN_NAME,
        show_concentric_rings=True
    )
    assert isinstance(m, folium.Map)
    rendered = m._repr_html_()
    assert "mt1.google.com" in rendered
    assert "Kacheri Varanasi" in rendered


# ============================================================
# 6. HTML TELEMETRY & NEWS RENDERER TESTS
# ============================================================
def test_html_cards_rendering(sample_parcel):
    routing = compute_parcel_routing(sample_parcel)
    
    # 1. Summary card
    summary_html = render_farmland_summary_card_html(sample_parcel, routing, is_fav=True)
    assert "Rohania Ring Road" in summary_html
    assert "Turn-by-Turn Directions" in summary_html
    assert "Actual Driving Distance" in summary_html

    # 2. Agronomic telemetry card
    agri_html = render_agronomic_telemetry_html(sample_parcel)
    assert "Rich Gangetic Silt Loam" in agri_html
    assert "Certified Sandalwood" in agri_html
    assert "Drip Fertigation Installed" in agri_html

    # 3. Legal and published news card
    legal_html = render_legal_and_news_card_html(sample_parcel)
    assert "96/100" in legal_html
    assert "Dainik Jagran Varanasi Edition" in legal_html
    assert "Verify Source Link" in legal_html
    assert "https://epaper.jagran.com/" in legal_html

    # 4. Seller contact card
    seller_html = render_seller_contact_card_html(sample_parcel)
    assert "Raghvendra Pratap Singh" in seller_html
    assert "WhatsApp Chat" in seller_html


def test_polymorphic_crops_extractor():
    # Dict format
    c1 = _extract_crops_telemetry({"supported_crops": {"high_value_crops": "Sandalwood", "soil_suitability_score": 95}})
    assert c1["high_value_crops"] == "Sandalwood"

    # List format (defensive against AttributeError: 'list' object has no attribute 'get')
    c2 = _extract_crops_telemetry({"supported_crops": ["Chandan & Avocado", "Guava Orchards", "Kala Namak Rice"]})
    assert c2["high_value_crops"] == "Chandan & Avocado"
    assert c2["horticulture_fruits"] == "Guava Orchards"

    # String format
    c3 = _extract_crops_telemetry({"supported_crops": "Organic Floriculture, Mango Orchards, Wheat"})
    assert c3["high_value_crops"] == "Organic Floriculture"

    # None format
    c4 = _extract_crops_telemetry({})
    assert "High-Density" in c4["high_value_crops"]


# ============================================================
# 7. EXCEL AND CSV EXPORTER TESTS
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
    assert "Rohania Ring Road" in content
    assert "Dainik Jagran Varanasi Edition" in content


# ============================================================
# 8. MASTER DATASET SCHEMA INTEGRITY TESTS
# ============================================================
def test_master_dataset_integrity():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", "up_east_farmlands.json")
    assert os.path.exists(data_path), f"Master dataset missing at {data_path}"

    with open(data_path, "r", encoding="utf-8") as f:
        parcels = json.load(f)

    assert len(parcels) >= 100, f"Expected at least 100 parcels, got {len(parcels)}"

    rings_found = set()
    for p in parcels:
        assert p.get("id"), "Missing id"
        assert p.get("name"), "Missing name"
        assert p.get("lat") and p.get("lng"), f"Missing coordinates for {p.get('id')}"
        assert p.get("size_acres") > 0, f"Invalid acreage for {p.get('id')}"
        assert p.get("price_per_acre_lakhs") > 0, f"Invalid rate for {p.get('id')}"
        assert p.get("published_news_title"), f"Missing published news title for {p.get('id')}"
        assert p.get("published_news_source"), f"Missing published news source for {p.get('id')}"
        assert p.get("published_news_url"), f"Missing published news url for {p.get('id')}"
        assert p.get("published_news_date"), f"Missing published news date for {p.get('id')}"
        assert p.get("notice_or_legal_type"), f"Missing legal notice type for {p.get('id')}"
        rings_found.add(p.get("distance_ring"))

    # Ensure all concentric distance rings exist
    assert "Within 20 km" in rings_found
    assert "20 to 40 km" in rings_found
    assert "40 to 60 km" in rings_found
    assert "60 to 80 km" in rings_found
    assert "80 to 100 km" in rings_found
