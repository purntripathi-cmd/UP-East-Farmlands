"""
Comprehensive Multi-Sheet Excel & CSV Exporter Engine
Generates styled Excel workbooks (.xlsx) and master CSV with full metadata:
- Sheet 1: All Verified Farmlands (UP East)
- Sheet 2: ⭐ My Shortlisted Favorites
- Sheet 3: 🤖 Independent Critique AI Risk Audit & Negative Feedbacks
- Sheet 4: 📰 Published News & Legal Caveats
- Sheet 5: 🛰️ Weekly AI-ML Telemetry & Spectral Indices
Exports data to memory buffer for direct Streamlit download and local CSV dump.
"""

import os
import io
import pandas as pd
from typing import List, Dict, Any, Set
from utils.critic_ai import evaluate_property_critique


def build_farmland_export_row(
    sno: int,
    fm: Dict[str, Any],
    routing: Dict[str, Any],
    is_fav: bool
) -> Dict[str, Any]:
    """Flattens a farmland record into comprehensive tabular export columns including Critique AI."""
    supp = fm.get("supported_crops", {})
    if not isinstance(supp, dict):
        supp = {}
    unit = fm.get("unit_meta", {})
    if not isinstance(unit, dict):
        unit = {}
    spectral = fm.get("spectral", {})
    if not isinstance(spectral, dict):
        spectral = {}

    critique = evaluate_property_critique(fm)
    govt = critique.get("govt_site_details", {})

    return {
        "S.No.": sno,
        "Favorite": "⭐ YES" if is_fav else "NO",
        "Farmland Estate Name": fm.get("name"),
        "District": fm.get("regional_district"),
        "State": fm.get("regional_state"),
        "Location / Tehsil": fm.get("location"),
        "Distance Ring": routing.get("distance_ring", fm.get("distance_ring")),
        "Actual Road Distance (km)": routing.get("road_km", fm.get("road_distance_from_kacheri_km")),
        "Driving Time": routing.get("driving_time_display", fm.get("driving_time_from_kacheri_display")),
        "Origin Reference Landmark": routing.get("origin_name", "Kacheri Varanasi near Varuna Pul"),
        "Aerial Distance (km)": routing.get("aerial_km", fm.get("aerial_distance_from_kacheri_km")),
        "Parcel Size (Acres)": fm.get("size_acres"),
        "Pakka Bigha": unit.get("pakka_bigha"),
        "Biswa": unit.get("biswa"),
        "Kattha": unit.get("kattha"),
        "Area (sq.m)": unit.get("sq_metres"),
        "Rate / Acre (₹ Lakhs)": fm.get("price_per_acre_lakhs"),
        "Total Ticket Price (₹ Cr)": fm.get("total_price_cr"),
        "Elevation (m MSL)": fm.get("elevation_m"),
        "Soil Classification": fm.get("soil_type"),
        "Soil pH": fm.get("soil_ph"),
        "Organic Carbon (%)": fm.get("organic_carbon_pct"),
        "Water Source": fm.get("water_source"),
        "Groundwater Depth (ft)": fm.get("groundwater_depth_ft"),
        "Water Salinity TDS (ppm)": fm.get("water_tds_ppm"),
        "Drip Irrigation": "Installed ✅" if fm.get("drip_irrigation_installed") else "Not Installed",
        "Power Supply": fm.get("power_supply"),
        "High-Value & Exotic Crops": supp.get("high_value_crops"),
        "Horticulture Fruits": supp.get("horticulture_fruits"),
        "Cash Crops & Staples": supp.get("cash_crops_staples"),
        "Est Annual Agro Yield (₹ Lakhs)": fm.get("annual_agro_yield_estimate_lakhs"),
        "Due Diligence Score": fm.get("due_diligence_score"),
        "Legal Grade": fm.get("due_diligence_grade"),
        "Critique AI Risk Score": critique.get("critique_risk_score"),
        "Critique AI Risk Verdict": critique.get("critique_risk_verdict"),
        "Negative Feedbacks & Red Flags": critique.get("negative_feedbacks_summary"),
        "Govt Verification Records": critique.get("primary_govt_clearance"),
        "UP Bhulekh Section 34 Mutation": govt.get("up_bhulekh_rtc"),
        "IGRSUP 12-Year Encumbrance": govt.get("igrsup_barah_sala"),
        "CGRMS Jansunwai Status": govt.get("jansunwai_status"),
        "Khasra / Khatauni Number": fm.get("khasra_khatauni_number"),
        "Title Status": fm.get("title_status"),
        "Revenue Record Type": fm.get("revenue_record_type"),
        "Farmhouse Permission": fm.get("farmhouse_permission"),
        "Road Frontage": fm.get("road_approach"),
        "Fencing": fm.get("fencing"),
        "Sourcing Provenance": fm.get("sourcing_tier"),
        "Published News Headline": fm.get("published_news_title"),
        "Published News Platform / Source": fm.get("published_news_source"),
        "Publication Date": fm.get("published_news_date"),
        "Legal Notice Type": fm.get("notice_or_legal_type"),
        "News Verification Link": fm.get("published_news_url"),
        "Google Maps Turn-by-Turn URL": routing.get("google_directions_url", fm.get("google_maps_directions_url")),
        "Google Satellite Search URL": routing.get("google_satellite_url", fm.get("google_maps_satellite_url")),
        "Seller Category": fm.get("seller_category"),
        "Contact Person": fm.get("contact_person"),
        "Contact Phone": fm.get("contact_phone"),
        "WhatsApp Direct Link": fm.get("contact_whatsapp"),
        "Sentinel-2 NDVI": spectral.get("ndvi"),
        "Crop Classification ML": spectral.get("crop_classification"),
        "Classification Confidence (%)": spectral.get("confidence_pct"),
        "Scan Freshness Timestamp": fm.get("freshness_timestamp")
    }


def generate_excel_workbook(
    parcels: List[Dict[str, Any]],
    routings: Dict[str, Dict[str, Any]],
    favorite_ids: Set[str] = None
) -> bytes:
    """Generates a complete multi-sheet Excel workbook in memory with Critique AI."""
    fav_set = favorite_ids or set()
    buffer = io.BytesIO()

    all_rows = []
    fav_rows = []
    critique_rows = []
    news_rows = []
    ml_rows = []

    for idx, p in enumerate(parcels):
        pid = str(p.get("id"))
        is_fav = pid in fav_set
        routing = routings.get(pid, {})
        row = build_farmland_export_row(idx + 1, p, routing, is_fav)
        all_rows.append(row)

        if is_fav:
            fav_rows.append(row)

        crit = evaluate_property_critique(p)
        critique_rows.append({
            "S.No.": idx + 1,
            "Estate Name": p.get("name"),
            "District": p.get("regional_district"),
            "Critique AI Risk Score": crit["critique_risk_score"],
            "Risk Verdict": crit["critique_risk_verdict"],
            "Negative Feedbacks & Village Grievances": crit["negative_feedbacks_summary"],
            "Govt Portal Clearance": crit["primary_govt_clearance"],
            "UP Bhulekh RTC Detail": crit["govt_site_details"]["up_bhulekh_rtc"],
            "IGRSUP 12-Year Encumbrance": crit["govt_site_details"]["igrsup_barah_sala"],
            "CGRMS Jansunwai Status": crit["govt_site_details"]["jansunwai_status"],
            "Groundwater Depletion & TDS": f"{p.get('water_tds_ppm', 220)} ppm ({crit['govt_site_details']['groundwater_noc']})"
        })

        news_rows.append({
            "S.No.": idx + 1,
            "Farmland Estate Name": p.get("name"),
            "District": p.get("regional_district"),
            "Published Notice Title": p.get("published_news_title"),
            "Platform / Media Source": p.get("published_news_source"),
            "Publication Date": p.get("published_news_date"),
            "Notice Category": p.get("notice_or_legal_type"),
            "Due Diligence Score": p.get("due_diligence_score"),
            "Verification Link": p.get("published_news_url")
        })

        spectral = p.get("spectral", {}) if isinstance(p.get("spectral"), dict) else {}
        ml_rows.append({
            "S.No.": idx + 1,
            "Farmland Estate Name": p.get("name"),
            "Latitude": p.get("lat"),
            "Longitude": p.get("lng"),
            "Sentinel-2 Multispectral NDVI": spectral.get("ndvi", 0.74),
            "MESSIS / AgriFieldNet Crop Class": spectral.get("crop_classification", "High Vigour Orchard"),
            "ML Model Confidence (%)": f"{spectral.get('confidence_pct', 92.5)}%",
            "Soil Suitability Score": p.get("supported_crops", {}).get("soil_suitability_score", 95) if isinstance(p.get("supported_crops"), dict) else 95,
            "Sweet Water TDS (ppm)": p.get("water_tds_ppm", 220),
            "Salinity Risk": "Low Salinity (<300 ppm)" if p.get("water_tds_ppm", 220) < 300 else "Moderate",
            "Audit Freshness": p.get("freshness_timestamp", "Recent")
        })

    df_all = pd.DataFrame(all_rows)
    df_fav = pd.DataFrame(fav_rows) if fav_rows else pd.DataFrame([{"Message": "No farmlands shortlisted as favorite yet."}])
    df_crit = pd.DataFrame(critique_rows)
    df_news = pd.DataFrame(news_rows)
    df_ml = pd.DataFrame(ml_rows)

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_all.to_excel(writer, sheet_name="All Farmlands (UP East)", index=False)
        df_fav.to_excel(writer, sheet_name="⭐ Shortlisted Favorites", index=False)
        df_crit.to_excel(writer, sheet_name="🤖 Critique AI & Risk Audit", index=False)
        df_news.to_excel(writer, sheet_name="📰 Published Media & Legal", index=False)
        df_ml.to_excel(writer, sheet_name="🛰️ Weekly AI-ML Spectral", index=False)

    buffer.seek(0)
    return buffer.getvalue()


def export_master_csv(
    parcels: List[Dict[str, Any]],
    routings: Dict[str, Dict[str, Any]],
    favorite_ids: Set[str] = None
) -> str:
    """Exports full dataset to a master CSV file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "csv_exports", "up_east_farmlands_master.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fav_set = favorite_ids or set()
    rows = []
    for idx, p in enumerate(parcels):
        pid = str(p.get("id"))
        is_fav = pid in fav_set
        routing = routings.get(pid, {})
        rows.append(build_farmland_export_row(idx + 1, p, routing, is_fav))

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    return csv_path
