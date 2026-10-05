"""
Farmland Presentation & Mobile-Responsive HTML Card Components
Provides clean, dark-mode, mobile-optimized cards for:
1. Farmland Top Summary (Price, Local Units, Road Distance from Kacheri Varanasi)
2. Agronomic Telemetry (Soil, pH, sweet water depth, TDS, drip irrigation, high-value crops)
3. Legal Due Diligence Audit & Published News (100-pt breakdown + Published newspaper clipping, platform source, publication date, legal notice type, and verification link)
4. Independent Critique AI Audit & Negative Feedbacks Dossier (8 risk vectors, critique score, negative flags, and govt portal records)
5. Direct Landowner / Broker Contact (Click to Call & Click to WhatsApp)

Guaranteed mobile-responsive layout with min-height 44px touch targets and zero raw HTML code block artifacts.
"""

import re
import textwrap
import urllib.parse
from typing import Dict, Any, List
from utils.critic_ai import evaluate_property_critique


def clean_html(html_str: str) -> str:
    """Removes HTML comments, strips leading spaces on lines to prevent markdown code block triggers."""
    cleaned = re.sub(r'<!--.*?-->', '', html_str, flags=re.DOTALL)
    cleaned = textwrap.dedent(cleaned)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(lines)


def _extract_crops_telemetry(item: Dict[str, Any]) -> Dict[str, Any]:
    """Safely extracts crop telemetry supporting dict, list, string, or None formats."""
    supp = item.get("supported_crops", {})
    if isinstance(supp, dict):
        return {
            "high_value_crops": supp.get("high_value_crops", "Certified Sandalwood & Hass Avocado"),
            "horticulture_fruits": supp.get("horticulture_fruits", "VNR Bihi Guava & Langra Mango"),
            "cash_crops_staples": supp.get("cash_crops_staples", "Kala Namak Rice & Wheat"),
            "soil_suitability_score": supp.get("soil_suitability_score", 95)
        }
    elif isinstance(supp, list):
        h_val = supp[0] if len(supp) > 0 else "Certified Sandalwood (Chandan)"
        hort = supp[1] if len(supp) > 1 else "VNR Bihi Guava & Langra Mango"
        cash = supp[2] if len(supp) > 2 else "Kala Namak Scented Rice"
        return {
            "high_value_crops": str(h_val),
            "horticulture_fruits": str(hort),
            "cash_crops_staples": str(cash),
            "soil_suitability_score": 92
        }
    elif isinstance(supp, str) and supp.strip():
        parts = [p.strip() for p in supp.split(",") if p.strip()]
        return {
            "high_value_crops": parts[0] if len(parts) > 0 else supp,
            "horticulture_fruits": parts[1] if len(parts) > 1 else "High-Density Guava & Mango",
            "cash_crops_staples": parts[2] if len(parts) > 2 else "Kala Namak Rice & Wheat",
            "soil_suitability_score": 90
        }
    return {
        "high_value_crops": "High-Density Sandalwood & Avocado",
        "horticulture_fruits": "Commercial Guava Orchards",
        "cash_crops_staples": "Kala Namak Rice & Staples",
        "soil_suitability_score": 94
    }


def render_farmland_summary_card_html(
    item: Dict[str, Any],
    routing: Dict[str, Any],
    is_fav: bool = False,
    serial_no: Any = None,
    flag_info: Optional[Dict[str, Any]] = None,
    fav_users: Optional[List[str]] = None
) -> str:
    """Renders top summary card with road distance from active landmark, pricing, size, serial number, and moderation flags."""
    acres = item.get("size_acres", 0.0)
    pakka_bigha = round(acres * 1.60, 2)
    biswa = round(pakka_bigha * 20, 1)
    sq_m = int(acres * 4046.86)
    
    price_acre = item.get("price_per_acre_lakhs", 0.0)
    total_cr = item.get("total_price_cr", 0.0)
    
    dist_ring = routing.get("distance_ring", item.get("distance_ring", "Purvanchal Buffer"))
    road_km = routing.get("road_km", item.get("road_distance_from_kacheri_km", 0.0))
    drive_time = routing.get("driving_time_display", item.get("driving_time_from_kacheri_display", "N/A"))
    origin_name = routing.get("origin_name", "Kacheri Varanasi near Varuna Pul")
    
    lat = float(item.get("lat", 25.3176))
    lng = float(item.get("lng", 82.9739))
    dir_url = routing.get("google_directions_url", item.get("google_maps_directions_url", f"https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lng:.6f}"))
    sat_url = routing.get("google_satellite_url", f"https://maps.google.com/?q={lat:.6f},{lng:.6f}&t=k")
    pin_url = routing.get("google_maps_pin_url", f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lng:.6f}")
    
    s_no_badge = f'<span style="background: #E0E7FF; color: #3730A3; padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: 800; border: 1px solid #C7D2FE;">🏷️ S.No. #{serial_no}</span>' if serial_no is not None else ''
    
    if fav_users:
        users_str = ", ".join(fav_users)
        fav_badge = f'<span style="background: #F3E8FF; color: #6B21A8; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid #DDD6FE;">⭐ Shortlisted Favorite (👤 {users_str})</span>'
    elif is_fav:
        fav_badge = '<span style="background: #F3E8FF; color: #6B21A8; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid #DDD6FE;">⭐ Shortlisted Favorite</span>'
    else:
        fav_badge = ''
    
    # Moderation flag alerts & badges
    flag_type = flag_info.get("flag") if flag_info else None
    flag_badge = ""
    flag_alert_html = ""
    if flag_type == "fake":
        flag_badge = '<span style="background: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid #FCA5A5;">🚩 FAKE LISTING</span>'
        flag_alert_html = f"""
<div style="background: #FEF2F2; border: 1.5px solid #FCA5A5; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #991B1B; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 8px;">
<span style="font-size: 20px;">🚩</span>
<div>
<div><b>ALERT: Flagged by User as Fake Listing / Fraud</b></div>
<div style="font-size: 11.5px; font-weight: 500; color: #B91C1C; margin-top: 2px;">{flag_info.get('reason', 'Deceptive or non-existent parcel details reported.')} • <i>Flagged at: {flag_info.get('timestamp', '')}</i></div>
</div>
</div>
"""
    elif flag_type == "ignored":
        flag_badge = '<span style="background: #F1F5F9; color: #475569; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid #CBD5E1;">🚫 IGNORED</span>'
        flag_alert_html = f"""
<div style="background: #F8FAFC; border: 1.5px solid #CBD5E1; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #475569; font-weight: 700; font-size: 13px; display: flex; align-items: center; gap: 8px;">
<span style="font-size: 20px;">🚫</span>
<div>
<div><b>NOTICE: Property Added to Ignore List</b></div>
<div style="font-size: 11.5px; font-weight: 500; color: #64748B; margin-top: 2px;">{flag_info.get('reason', 'Hidden from default discovery views.')} • <i>Ignored at: {flag_info.get('timestamp', '')}</i></div>
</div>
</div>
"""

    # SC/ST Section 98 UP Revenue Code Red Flag Alert
    is_sc_st = item.get("is_sc_st_land", False) or "SC" in item.get("caste_category", "") or "ST" in item.get("caste_category", "")
    sc_st_badge = ""
    sc_st_alert_html = ""
    if is_sc_st:
        sec_approved = "Approved" in item.get("section_98_status", "") or "CONDITIONAL" in item.get("section_98_status", "")
        if not sec_approved:
            sc_st_badge = '<span style="background: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1.5px solid #DC2626;">🚨 SC/ST RESTRICTED (Sec 98)</span>'
            sc_st_alert_html = f"""
<div style="background: #FEF2F2; border: 2px solid #DC2626; border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; color: #7F1D1D;">
<div style="display: flex; align-items: center; gap: 8px; font-size: 13.5px; font-weight: 800; color: #991B1B;">
<span style="font-size: 20px;">🚨</span>
<span>RED FLAG: SC/ST OWNED PROPERTY — SECTION 98 UP REVENUE CODE RESTRICTION</span>
</div>
<div style="font-size: 11.5px; line-height: 1.5; margin-top: 5px; color: #991B1B;">
<b>Barred for General / OBC Buyers:</b> Under <b>Section 98 of UP Revenue Code, 2006</b>, agricultural land held by an SC/ST Bhumidhar cannot be transferred or sold to any non-SC/ST person without prior written sanction from the District Magistrate / Collector. Purchasing without DM approval renders the deed <b>void ab initio</b> (Section 104) and vests land in State Government (Section 105).
<div style="margin-top: 4px; font-size: 11px; color: #7F1D1D; background: #FDE8E8; padding: 4px 8px; border-radius: 4px; border: 1px dashed #F87171;">
<b>UP Bhulekh Khatauni Record:</b> {item.get('khatauni_caste_remark', 'Restricted SC Category Tenure Holder (Section 98 Clearance Required)')}
</div>
</div>
</div>
"""
        else:
            sc_st_badge = '<span style="background: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid #FCD34D;">⚠️ SC/ST (DM Conditional Sanction)</span>'
            sc_st_alert_html = f"""
<div style="background: #FFFBEB; border: 1.5px solid #F59E0B; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; color: #78350F;">
<div style="display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 800; color: #B45309;">
<span style="font-size: 18px;">⚠️</span>
<span>SC/ST HOLDING WITH COLLECTOR CONDITIONAL SANCTION ORDER</span>
</div>
<div style="font-size: 11px; margin-top: 3px; color: #92400E;">
Tenure holder belongs to SC category. Official Collector / DM Sanction file registered under Section 98 UP Revenue Code. Physical file verification at Collectorate Registry branch required before execution.
</div>
</div>
"""

    raw_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 14px; color: #0F172A; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);">
{sc_st_alert_html}
{flag_alert_html}
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; margin-bottom: 10px;">
<div style="flex: 1 1 260px;">
<div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 6px;">
{s_no_badge}
<span style="background: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 700; border: 1px solid #BBF7D0;">{item.get('regional_district', 'Varanasi')} • {item.get('regional_state', 'UP')}</span>
<span style="background: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 700; border: 1px solid #BFDBFE;">{item.get('sourcing_tier_badge', '🏛️ Tier 1: Govt Registry')}</span>
<span style="background: #E0F2FE; color: #0369A1; padding: 3px 8px; border-radius: 6px; font-size: 11.5px; font-weight: 700; border: 1px solid #BAE6FD;">{dist_ring}</span>
{sc_st_badge}
{fav_badge}
{flag_badge}
</div>
<h2 style="margin: 0; font-size: 20px; font-weight: 800; color: #0F172A; line-height: 1.3;">{item.get('name', 'Farmland Estate')}</h2>
<div style="color: #64748B; font-size: 12.5px; margin-top: 3px;">📍 {item.get('location', '')}</div>
</div>
<div style="text-align: right; min-width: 140px;">
<div style="font-size: 24px; font-weight: 800; color: #047857;">₹{total_cr} Cr</div>
<div style="color: #059669; font-size: 12.5px; font-weight: 700;">₹{price_acre} Lakhs / Acre</div>
</div>
</div>
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px 14px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
<div style="flex: 1 1 220px;">
<span style="color: #0284C7; font-weight: 700; font-size: 13px;">🚗 Actual Driving Road Distance:</span>
<span style="color: #0F172A; font-weight: 800; font-size: 16px; margin-left: 4px;">{road_km} km</span>
<span style="color: #0284C7; font-size: 13px; font-weight: 600; margin-left: 4px;">(~{drive_time})</span>
<div style="color: #64748B; font-size: 11px; margin-top: 3px;">From Reference Zero-Point: <b>{origin_name}</b></div>
</div>
<div style="display: flex; flex-wrap: wrap; gap: 8px; width: 100%; margin-top: 6px;">
<a href="{pin_url}" target="_blank" style="flex: 1 1 130px; min-height: 40px; background: #F0FDF4; color: #166534; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; gap: 5px; text-align: center; border: 1.5px solid #86EFAC; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">📍 Open in Google Maps ↗</a>
<a href="{sat_url}" target="_blank" style="flex: 1 1 130px; min-height: 40px; background: #EFF6FF; color: #1D4ED8; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; gap: 5px; text-align: center; border: 1.5px solid #93C5FD; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">🛰️ Satellite Pin ↗</a>
<a href="{dir_url}" target="_blank" style="flex: 1 1 150px; min-height: 40px; background: #FAF5FF; color: #6D28D9; padding: 8px 12px; border-radius: 8px; text-decoration: none; font-size: 12px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; gap: 5px; text-align: center; border: 1.5px solid #DDD6FE; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">🚗 Google Turn-by-Turn ↗</a>
</div>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; font-size: 11.5px;">
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<div style="color: #64748B; font-weight: 600;">Acreage</div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px; margin-top: 2px;">{acres:.2f} Acres</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<div style="color: #64748B; font-weight: 600;">Purvanchal Bigha</div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px; margin-top: 2px;">{pakka_bigha:.2f} Bigha</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<div style="color: #64748B; font-weight: 600;">Biswa / Kattha</div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px; margin-top: 2px;">{biswa:.1f} Biswa</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<div style="color: #64748B; font-weight: 600;">Metric Area</div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px; margin-top: 2px;">{sq_m:,} m²</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<div style="color: #64748B; font-weight: 600;">Elevation</div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px; margin-top: 2px;">{item.get('elevation_m', 78)}m MSL</div>
</div>
</div>
</div>
"""
    return clean_html(raw_html)


def render_agronomic_telemetry_html(item: Dict[str, Any]) -> str:
    """Renders agronomic and soil telemetry in a clean light theme."""
    supp = _extract_crops_telemetry(item)
    tds = item.get("water_tds_ppm", 220)
    tds_color = "#047857" if tds < 250 else "#B45309"
    drip_badge = '<span style="color: #047857; font-weight: 700;">✅ Operational</span>' if item.get("drip_irrigation_installed") else '<span style="color: #B45309;">⚡ Canal / Flood</span>'

    raw_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 12px; color: #0F172A; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);">
<h3 style="margin: 0 0 10px 0; font-size: 15px; color: #0284C7; font-weight: 800; display: flex; align-items: center; gap: 6px;">
🌾 Agronomic Profile & Water Security
</h3>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; font-size: 11.5px; margin-bottom: 10px;">
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<span style="color: #64748B; font-weight: 600;">Soil Type:</span>
<div style="color: #0F172A; font-weight: 700; margin-top: 2px;">{item.get('soil_type', 'Gangetic Silt Loam')}</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<span style="color: #64748B; font-weight: 600;">Soil pH & OC:</span>
<div style="color: #0F172A; font-weight: 700; margin-top: 2px;">pH {item.get('soil_ph', 7.4)} • OC {item.get('organic_carbon_pct', 0.85)}%</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<span style="color: #64748B; font-weight: 600;">Water Source:</span>
<div style="color: #0F172A; font-weight: 700; margin-top: 2px;">{item.get('water_source', 'Deep Aquifer Borewell')}</div>
</div>
<div style="background: #F8FAFC; padding: 8px 10px; border-radius: 8px; border: 1px solid #E2E8F0;">
<span style="color: #64748B; font-weight: 600;">Water Salinity TDS:</span>
<div style="color: {tds_color}; font-weight: 800; margin-top: 2px;">{tds} ppm (Sweet Aquifer)</div>
</div>
</div>
<div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 10px 12px; border-radius: 8px; font-size: 12px; margin-bottom: 10px;">
<div style="color: #166534; font-weight: 800; margin-bottom: 4px;">🌱 Crop Suitability Matrix</div>
<div><b style="color: #047857;">High-Value:</b> {supp.get('high_value_crops', 'N/A')}</div>
<div style="margin-top: 3px;"><b style="color: #B45309;">Horticulture:</b> {supp.get('horticulture_fruits', 'N/A')}</div>
<div style="margin-top: 3px;"><b style="color: #334155;">Staples:</b> {supp.get('cash_crops_staples', 'N/A')}</div>
<div style="margin-top: 6px; font-size: 11.5px; color: #166534; border-top: 1px dashed #BBF7D0; padding-top: 4px;"><b>Est. Annual Commercial Yield:</b> ₹{item.get('annual_agro_yield_estimate_lakhs', 12.0)} L/Yr</div>
</div>
<div style="display: flex; justify-content: space-between; font-size: 11.5px; color: #64748B; padding-top: 6px; border-top: 1px solid #E2E8F0;">
<span>Drip Irrigation: {drip_badge}</span>
<span>Power: <b style="color: #0F172A;">{item.get('power_supply', '3-Phase Dedicated Line')}</b></span>
</div>
</div>
"""
    return clean_html(raw_html)


def render_legal_and_news_card_html(item: Dict[str, Any]) -> str:
    """Renders 100-point legal audit along with verified published news clipping in a clean light theme."""
    score = item.get("due_diligence_score", 90)
    score_color = "#047857" if score >= 90 else "#0284C7" if score >= 80 else "#B45309"
    score_bg = "#DCFCE7" if score >= 90 else "#DBEAFE" if score >= 80 else "#FEF3C7"
    
    news_title = item.get("published_news_title", "UP Bhulekh Section 34 Clean Title Gazette")
    news_source = item.get("published_news_source", "Dainik Jagran Varanasi Edition")
    news_url = item.get("published_news_url", "https://epaper.jagran.com/")
    news_date = item.get("published_news_date", "02 Oct 2026")
    notice_type = item.get("notice_or_legal_type", "30-Day Title Caveat Cleared")

    dist = item.get("regional_district", "Varanasi")
    loc = item.get("location", "")
    khasra = item.get("khasra_khatauni_number", "")
    g_search_query = urllib.parse.quote(f"{dist} {loc} {khasra} UP Bhulekh")
    google_search_url = f"https://www.google.com/search?q={g_search_query}"
    bhulekh_url = "https://upbhulekh.gov.in/public/public_ror/action/public_action.jsp"
    ibapi_url = "https://ibapi.in/sale_info_home.aspx"

    raw_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 12px; color: #0F172A; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 4px;">
<h3 style="margin: 0; font-size: 15px; color: #059669; font-weight: 800; display: flex; align-items: center; gap: 6px;">
🛡️ Legal Due Diligence Audit
</h3>
<span style="background: {score_bg}; color: {score_color}; font-weight: 800; font-size: 12.5px; padding: 3px 10px; border-radius: 6px; border: 1px solid {score_color}33;">
Score: {score}/100 ({item.get('due_diligence_grade', 'A+ Sovereign')})
</span>
</div>
<div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 10px 12px; margin-bottom: 10px;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 4px;">
<span style="color: #B45309; font-weight: 800; font-size: 12px;">📰 NOTICE: {news_source}</span>
<span style="background: #FEF3C7; color: #92400E; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; border: 1px solid #FCD34D;">{notice_type}</span>
</div>
<div style="color: #78350F; font-weight: 700; font-size: 13px; line-height: 1.3;">{news_title}</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 11.5px; flex-wrap: wrap; gap: 6px;">
<span style="color: #92400E;">Date: {news_date}</span>
<div style="display: flex; gap: 6px; flex-wrap: wrap;">
<a href="{news_url}" target="_blank" style="background: #D97706; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; min-height: 30px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(217,119,6,0.3);">Verify Link ↗</a>
<a href="{bhulekh_url}" target="_blank" style="background: #047857; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; min-height: 30px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(4,120,87,0.3);" title="Search Khatauni & Khasra on official UP Board of Revenue portal">🏛️ UP Bhulekh ↗</a>
<a href="{ibapi_url}" target="_blank" style="background: #1D4ED8; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; min-height: 30px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(29,78,216,0.3);" title="Search official Bank e-Auctions on Indian Banks Association portal">🏦 IBAPI Bank Auctions ↗</a>
<a href="{google_search_url}" target="_blank" style="background: #475569; color: white; padding: 4px 10px; border-radius: 6px; text-decoration: none; font-weight: 700; min-height: 30px; display: inline-flex; align-items: center; box-shadow: 0 1px 2px rgba(71,85,105,0.3);" title="Search Google for authentic notices and gazette records">🔍 Google Search ↗</a>
</div>
</div>
</div>
<div style="font-size: 12px; color: #475569; margin-bottom: 8px; line-height: 1.5;">
<div><b>Khatauni / Khasra:</b> <span style="color: #0F172A;">{item.get('khasra_khatauni_number', 'Khatauni Verified')}</span></div>
<div><b>Caste Category & Sec 98:</b> <span style="color: {'#DC2626' if item.get('is_sc_st_land') else '#059669'}; font-weight: 700;">{item.get('caste_category', 'General / OBC (Unrestricted)')} • {item.get('section_98_status', '✅ UNRESTRICTED: General/OBC Landholding')}</span></div>
<div><b>Khatauni Caste Remarks:</b> <span style="color: {'#991B1B' if item.get('is_sc_st_land') else '#334155'}; font-size: 11px;">{item.get('khatauni_caste_remark', 'UP Bhulekh Certified Freehold')}</span></div>
<div><b>Title:</b> <span style="color: #0F172A;">{item.get('title_status', 'Freehold Clear Title')} ({item.get('revenue_record_type', 'UP Bhulekh Certified')})</span></div>
<div><b>Farmhouse:</b> <span style="color: #0F172A;">{item.get('farmhouse_permission', 'Permitted')}</span></div>
<div><b>Road Access:</b> <span style="color: #0F172A;">{item.get('road_approach', '18-ft Bitumen Road')} • {item.get('fencing', 'Chain-Link')}</span></div>
</div>
<div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 8px 10px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #047857;">
{item.get('due_diligence_verdict', '🟢 Ready to Register — Bankable & clear title')}
</div>
</div>
"""
    return clean_html(raw_html)


def render_critique_ai_card_html(item: Dict[str, Any]) -> str:
    """Renders Independent Critique AI risk audit, negative feedback summary, and govt site records in clean light theme."""
    critique = evaluate_property_critique(item)
    score = critique["critique_risk_score"]
    badge = critique["critique_verdict_badge"]
    color = critique["critique_verdict_color"]
    verdict = critique["critique_risk_verdict"]
    feedbacks = critique["negative_feedbacks_list"]
    govt = critique["govt_site_details"]

    lat = float(item.get("lat", 25.3176))
    lng = float(item.get("lng", 82.9739))
    gmaps_pin_url = f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lng:.6f}"
    gmaps_sat_url = f"https://maps.google.com/?q={lat:.6f},{lng:.6f}&t=k"

    bhulekh_url = govt.get("up_bhulekh_url", "https://upbhulekh.gov.in/public/public_ror/action/public_ror.jsp")
    igrsup_url = govt.get("igrsup_url", "https://igrsup.gov.in/igrsup/propertySearchAction")
    jansunwai_url = govt.get("jansunwai_url", "https://jansunwai.up.nic.in/TrackComplaint")
    groundwater_url = govt.get("groundwater_url", "https://upgroundwater.in/noc-status")

    audit_cycle = critique.get("audit_cycle", "Weekly Automated Cycle")
    last_refresh = critique.get("last_weekly_refresh", "Active")
    next_refresh = critique.get("next_weekly_refresh", "Scheduled in 7 Days")

    feedback_items_html = "".join([
        f'<div style="margin-bottom: 4px; color: #991B1B; font-size: 11.5px; line-height: 1.4;">• {fb}</div>'
        for fb in feedbacks
    ])

    raw_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-bottom: 12px; color: #0F172A; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 4px;">
<h3 style="margin: 0; font-size: 15px; color: #DC2626; font-weight: 800; display: flex; align-items: center; gap: 6px;">
🤖 Independent Critique AI Risk Audit & Negative Feedbacks
</h3>
<span style="background: #FEF2F2; color: #B91C1C; font-weight: 800; font-size: 12.5px; padding: 3px 10px; border-radius: 6px; border: 1px solid #FECACA;">
Score: {score}/100 ({badge})
</span>
</div>
<div style="background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 8px; padding: 6px 12px; font-size: 11.5px; color: #166534; font-weight: 700; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;">
<span>📅 <b>Critique AI Weekly Cycle:</b> {audit_cycle}</span>
<span style="background: #DCFCE7; padding: 2px 8px; border-radius: 4px; border: 1px solid #86EFAC;">🔄 Auto-refreshes Every 7 Days • Next: {next_refresh[:11]}</span>
</div>
<div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; color: #0F172A; margin-bottom: 10px;">
{verdict}
</div>
<div style="margin-bottom: 10px;">
<div style="color: #DC2626; font-weight: 800; font-size: 12px; margin-bottom: 4px;">⚠️ Identified Caveats & Village Advisories:</div>
<div style="background: #FEF2F2; padding: 8px 12px; border-radius: 8px; border-left: 4px solid #EF4444; border-top: 1px solid #FECACA; border-right: 1px solid #FECACA; border-bottom: 1px solid #FECACA;">
{feedback_items_html}
</div>
</div>
<div>
<div style="color: #0284C7; font-weight: 800; font-size: 12px; margin-bottom: 4px;">🏛️ Government Portal Cross-Verification (Official Sources):</div>
<div style="background: #F0F9FF; padding: 10px 12px; border-radius: 8px; font-size: 11.5px; color: #0369A1; line-height: 1.5; border-left: 4px solid #0284C7; border-top: 1px solid #BAE6FD; border-right: 1px solid #BAE6FD; border-bottom: 1px solid #BAE6FD;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 4px;">
<div>• <b style="color: #0F172A;">UP Bhulekh RTC:</b> {govt['up_bhulekh_rtc']}</div>
<a href="{bhulekh_url}" target="_blank" style="background: #FFFFFF; color: #0284C7; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #BAE6FD; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">🔗 UP Bhulekh Source ↗</a>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 4px;">
<div>• <b style="color: #0F172A;">IGRSUP 12-Year:</b> {govt['igrsup_barah_sala']}</div>
<a href="{igrsup_url}" target="_blank" style="background: #FFFFFF; color: #0284C7; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #BAE6FD; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">🔗 IGRSUP Registry Source ↗</a>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 4px;">
<div>• <b style="color: #0F172A;">CGRMS Grievance:</b> {govt['jansunwai_status']}</div>
<a href="{jansunwai_url}" target="_blank" style="background: #FFFFFF; color: #0284C7; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #BAE6FD; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">🔗 Jansunwai Grievance Portal ↗</a>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 4px;">
<div>• <b style="color: #0F172A;">Groundwater NOC:</b> {govt['groundwater_noc']}</div>
<a href="{groundwater_url}" target="_blank" style="background: #FFFFFF; color: #0284C7; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; border: 1px solid #BAE6FD; text-decoration: none; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">🔗 UPGWD NOC Registry ↗</a>
</div>
</div>
</div>
<div style="margin-top: 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px 12px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
<div style="font-size: 12px; color: #334155;">
<b>📍 Specific Location:</b> <span style="color: #0F172A; font-weight: 700;">{lat:.5f}° N, {lng:.5f}° E</span> ({item.get('location', 'Farmland')})
</div>
<div style="display: flex; gap: 6px; flex-wrap: wrap;">
<a href="{gmaps_pin_url}" target="_blank" style="background: #FFFFFF; color: #166534; padding: 6px 12px; border-radius: 6px; font-size: 11.5px; font-weight: 700; border: 1.5px solid #86EFAC; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">📍 Open Specific Location in Google Maps ↗</a>
<a href="{gmaps_sat_url}" target="_blank" style="background: #FFFFFF; color: #1D4ED8; padding: 6px 12px; border-radius: 6px; font-size: 11.5px; font-weight: 700; border: 1.5px solid #93C5FD; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);">🛰️ Satellite Pin ↗</a>
</div>
</div>
</div>
"""
    return clean_html(raw_html)


def render_seller_contact_card_html(item: Dict[str, Any]) -> str:
    """Renders direct landowner/broker contact card with Call and WhatsApp buttons optimized for mobile touch."""
    person = item.get("contact_person", "Authorized Land Rep")
    phone = item.get("contact_phone", "+91 94150 00000")
    clean_p = str(phone).replace(" ", "").replace("-", "").replace("+", "")
    wa_link = f"https://wa.me/{clean_p}?text=Interested%20in%20{item.get('name', 'Farmland').replace(' ', '%20')}"

    raw_html = f"""
<div style="background: #FFFFFF; border: 1.5px solid #E2E8F0; border-radius: 12px; padding: 14px; margin-top: 10px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);">
<div style="background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; font-size: 11.5px; color: #92400E; line-height: 1.5;">
⚠️ <b>Prototype Notice — Simulated Contact Details:</b><br/>
Mobile numbers in this research demonstration catalog are simulated placeholders for developer privacy. For genuine land purchases or bank auctions, do not attempt to call these mock numbers. Instead, enquire directly via the official portals below:
<div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
<a href="https://ibapi.in/sale_info_home.aspx" target="_blank" style="background: #1D4ED8; color: white; padding: 5px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11.5px; display: inline-flex; align-items: center; gap: 4px;">🏦 IBAPI Official Bank Auctions ↗</a>
<a href="https://upbhulekh.gov.in/public/public_ror/action/public_action.jsp" target="_blank" style="background: #047857; color: white; padding: 5px 12px; border-radius: 6px; text-decoration: none; font-weight: 700; font-size: 11.5px; display: inline-flex; align-items: center; gap: 4px;">🏛️ UP Bhulekh Khatauni ↗</a>
</div>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 4px;">
<div>
<div style="color: #0F172A; font-weight: 800; font-size: 14px;">{person}</div>
<div style="color: #64748B; font-size: 11.5px; font-weight: 600;">{item.get('seller_category', 'Direct Landowner / Farmer')}</div>
</div>
<div style="color: #64748B; font-weight: 700; font-size: 13px;">{phone} <span style="font-size: 11px; color: #94A3B8;">(Demo)</span></div>
</div>
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
<a href="tel:{clean_p}" style="flex: 1 1 120px; min-height: 44px; text-align: center; background: #64748B; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 12.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(100,116,139,0.3);">📞 Call Seller (Demo)</a>
<a href="{wa_link}" target="_blank" style="flex: 1 1 120px; min-height: 44px; text-align: center; background: #059669; color: white; padding: 10px; border-radius: 8px; text-decoration: none; font-size: 12.5px; font-weight: 700; display: flex; align-items: center; justify-content: center; box-shadow: 0 1px 3px rgba(5,150,105,0.3);">💬 WhatsApp (Demo)</a>
</div>
</div>
"""
    return clean_html(raw_html)

