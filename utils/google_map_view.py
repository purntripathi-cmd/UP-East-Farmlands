"""
Google Maps Interactive Folium Engine
Renders high-resolution Google Satellite, Hybrid, Roadmap, and Terrain layers.
Overlays concentric radial buffer rings (20 km, 40 km, 60 km, 80 km, 100 km) from Kacheri Varanasi,
plots individual farmland parcels with telemetry popups,
and supports dynamic marker placement for newly clicked or searched coordinates.
"""

import folium
from folium import plugins
from typing import List, Dict, Any, Set, Optional, Tuple
from utils.geo_routing import (
    DEFAULT_ORIGIN_LAT,
    DEFAULT_ORIGIN_LNG,
    DEFAULT_ORIGIN_NAME,
    compute_parcel_routing
)

# Official Google Maps Web Tile Endpoints
GOOGLE_TILES = {
    "hybrid": {
        "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "name": "Google Maps Satellite (Hybrid)",
        "attr": "Google Maps Satellite Imagery with Road Overlay"
    },
    "satellite": {
        "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "name": "Google Maps Satellite (Pure)",
        "attr": "Google Maps Pure Satellite Imagery"
    },
    "roadmap": {
        "url": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "name": "Google Maps Streets / Roadmap",
        "attr": "Google Maps Street Map"
    },
    "terrain": {
        "url": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        "name": "Google Maps Terrain",
        "attr": "Google Maps Physical Terrain"
    }
}

# Concentric Ring Definitions (Radius in metres, color, label)
CONCENTRIC_RINGS = [
    {"radius_m": 20000, "color": "#10B981", "label": "20 km Buffer (Immediate Urban Fringe)"},
    {"radius_m": 40000, "color": "#38BDF8", "label": "40 km Buffer (Chandauli / Mirzapur Border)"},
    {"radius_m": 60000, "color": "#F59E0B", "label": "60 km Buffer (Ghazipur / Jaunpur Core)"},
    {"radius_m": 80000, "color": "#A855F7", "label": "80 km Buffer (Azamgarh / Vindhya Border)"},
    {"radius_m": 100000, "color": "#F43F5E", "label": "100 km Buffer (Purvanchal Agro Perimeter)"}
]


def create_google_farmland_map(
    parcels: List[Dict[str, Any]],
    origin_lat: float = DEFAULT_ORIGIN_LAT,
    origin_lng: float = DEFAULT_ORIGIN_LNG,
    origin_name: str = DEFAULT_ORIGIN_NAME,
    favorite_ids: Set[str] = None,
    show_concentric_rings: bool = True,
    center_lat: Optional[float] = None,
    center_lng: Optional[float] = None,
    zoom_start: int = 10,
    selected_pin: Optional[Dict[str, Any]] = None,
    focused_sno: Optional[int] = None
) -> folium.Map:
    """
    Constructs an interactive Folium Map using Google Maps satellite/hybrid tiles,
    with an active landmark origin marker, farmland estate pins,
    and optional user-clicked / searched target pin.
    """
    fav_set = favorite_ids or set()
    map_center_lat = center_lat if center_lat is not None else origin_lat
    map_center_lng = center_lng if center_lng is not None else origin_lng

    # Initialize Folium Map with mobile-friendly gestures
    m = folium.Map(
        location=[map_center_lat, map_center_lng],
        zoom_start=zoom_start,
        tiles=None,
        control_scale=True,
        prefer_canvas=True
    )

    # Add Google Maps Tile Layers
    folium.TileLayer(
        tiles=GOOGLE_TILES["hybrid"]["url"],
        attr=GOOGLE_TILES["hybrid"]["attr"],
        name=GOOGLE_TILES["hybrid"]["name"],
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles=GOOGLE_TILES["roadmap"]["url"],
        attr=GOOGLE_TILES["roadmap"]["attr"],
        name=GOOGLE_TILES["roadmap"]["name"],
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles=GOOGLE_TILES["terrain"]["url"],
        attr=GOOGLE_TILES["terrain"]["attr"],
        name=GOOGLE_TILES["terrain"]["name"],
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles=GOOGLE_TILES["satellite"]["url"],
        attr=GOOGLE_TILES["satellite"]["attr"],
        name=GOOGLE_TILES["satellite"]["name"],
        overlay=False,
        control=True
    ).add_to(m)

    # 1. Plot Origin Benchmark Landmark (Kacheri Varanasi / Selected Origin)
    origin_popup = f"""
    <div style="font-family: Arial, sans-serif; font-size: 13px; color: #0F172A; min-width: 200px;">
        <div style="background: #D97706; color: white; padding: 5px 8px; border-radius: 4px; font-weight: bold; margin-bottom: 4px;">
            🏛️ Benchmark Reference Zero-Point
        </div>
        <b>{origin_name}</b><br>
        <span style="color: #64748B; font-size: 11px;">Lat: {origin_lat:.4f}, Lng: {origin_lng:.4f}</span>
        <div style="margin-top: 4px; font-size: 11px; color: #475569;">
            All road distances, drive times, and concentric radial buffers are measured from this point.
        </div>
    </div>
    """
    folium.Marker(
        location=[origin_lat, origin_lng],
        popup=folium.Popup(origin_popup, max_width=280),
        tooltip=f"📍 Reference Landmark: {origin_name}",
        icon=folium.Icon(color="darkred", icon="star", prefix="fa")
    ).add_to(m)

    # 2. Draw Concentric Radial Buffer Rings if enabled
    if show_concentric_rings:
        ring_group = folium.FeatureGroup(name="Concentric Distance Rings (20 - 100 km)")
        for ring in CONCENTRIC_RINGS:
            folium.Circle(
                location=[origin_lat, origin_lng],
                radius=ring["radius_m"],
                color=ring["color"],
                weight=2,
                fill=True,
                fill_color=ring["color"],
                fill_opacity=0.04,
                dash_array="5, 8",
                tooltip=f"⭕ {ring['label']}"
            ).add_to(ring_group)
        ring_group.add_to(m)

    # 3. Plot Farmland Parcels with Custom Numbered S.No. Badges & Popups
    marker_cluster = plugins.MarkerCluster(name="Farmland Parcels Cluster", disableClusteringAtZoom=12).add_to(m)

    for idx, p in enumerate(parcels):
        p_lat = float(p.get("lat", origin_lat))
        p_lng = float(p.get("lng", origin_lng))
        pid = str(p.get("id"))
        is_fav = pid in fav_set
        sno = p.get("_serial_no", idx + 1)
        is_sc_st = p.get("is_sc_st_land", False) or "SC" in p.get("caste_category", "") or "ST" in p.get("caste_category", "")
        is_focused = (focused_sno is not None and sno == focused_sno)

        # Compute dynamic routing relative to active origin
        routing = compute_parcel_routing(p, origin_lat, origin_lng, origin_name)
        road_km = routing["road_km"]
        drive_time = routing["driving_time_display"]
        directions_url = routing["google_directions_url"]

        score = p.get("due_diligence_score", 85)
        grade = p.get("due_diligence_grade", "A Institutional Grade")

        # Color coding by caste, favorite, or score
        if is_sc_st:
            badge_bg = "#DC2626"
            badge_border = "#7F1D1D"
            badge_text = f"#{sno} 🚨"
        elif is_fav:
            badge_bg = "#7C3AED"
            badge_border = "#4C1D95"
            badge_text = f"#{sno} ★"
        elif score >= 90:
            badge_bg = "#059669"
            badge_border = "#064E3B"
            badge_text = f"#{sno}"
        elif score >= 75:
            badge_bg = "#2563EB"
            badge_border = "#1E3A8A"
            badge_text = f"#{sno}"
        elif score >= 60:
            badge_bg = "#D97706"
            badge_border = "#78350F"
            badge_text = f"#{sno}"
        else:
            badge_bg = "#EF4444"
            badge_border = "#991B1B"
            badge_text = f"#{sno}"

        focus_style = "box-shadow: 0 0 0 4px #FBBF24, 0 6px 16px rgba(0,0,0,0.5); transform: scale(1.25); z-index: 9999;" if is_focused else "box-shadow: 0 2px 6px rgba(0,0,0,0.35);"

        icon_html = f"""
        <div style="
            background: {badge_bg};
            color: white;
            border: 2px solid {badge_border if not is_focused else '#FBBF24'};
            border-radius: 12px;
            padding: 2px 7px;
            font-size: 11px;
            font-weight: 800;
            text-align: center;
            white-space: nowrap;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            cursor: pointer;
            {focus_style}
        ">
            {badge_text}
        </div>
        """

        # Highlight circle if focused
        if is_focused:
            folium.Circle(
                location=[p_lat, p_lng],
                radius=400,
                color="#F59E0B",
                weight=3,
                fill=True,
                fill_color="#FDE68A",
                fill_opacity=0.4,
                tooltip=f"🎯 Focused Farmland S.No. #{sno}: {p.get('name')}"
            ).add_to(m)

        # News information
        news_title = p.get("published_news_title", "UP Bhulekh Land Mutation Verified")
        news_source = p.get("published_news_source", "State Revenue Gazette")
        news_url = p.get("published_news_url", "https://upbhulekh.gov.in/")
        news_date = p.get("published_news_date", "Recent")

        sc_alert_html = ""
        if is_sc_st:
            sc_alert_html = """
            <div style="background: #FEF2F2; border: 1px solid #DC2626; color: #991B1B; padding: 4px 6px; border-radius: 4px; font-size: 10.5px; font-weight: bold; margin-bottom: 6px;">
                🚨 RED FLAG: SC/ST Owned (Sec 98 UP Revenue Code — Barred for General Buyers)
            </div>
            """

        acres_val = float(p.get('size_acres', 0.0))
        bigha_val = round(acres_val * 1.60, 2)

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; color: #0F172A; min-width: 250px; line-height: 1.4;">
            <div style="background: {'#991B1B' if is_sc_st else '#1E293B'}; color: white; padding: 6px 10px; border-radius: 6px 6px 0 0; font-weight: bold;">
                🌾 #{sno}. {p.get('name', 'Farmland Estate')}
            </div>
            <div style="padding: 8px 10px; border: 1px solid #CBD5E1; border-top: none; border-radius: 0 0 6px 6px;">
                {sc_alert_html}
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="background: #E2E8F0; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{p.get('regional_district', 'Varanasi')}</span>
                    <span style="font-weight: bold; color: #10B981; font-size: 12px;">₹{p.get('price_per_acre_lakhs')} L/Acre</span>
                </div>
                
                <div style="background: #F8FAFC; padding: 4px 6px; border-radius: 4px; margin-bottom: 6px; font-size: 11px;">
                    <b>🚗 Road Distance:</b> <span style="color: #2563EB; font-weight: bold;">{road_km} km</span> ({drive_time})<br>
                    <span style="color: #64748B;">From: {origin_name.split('(')[0].strip()[:24]}</span>
                </div>

                <div style="font-size: 11px; margin-bottom: 6px;">
                    <b>📐 Size:</b> {acres_val} Acres (<b>{bigha_val} Pakka Bigha</b>)<br>
                    <b>💧 TDS:</b> {p.get('water_tds_ppm', 220)} ppm • <b>Soil pH:</b> {p.get('soil_ph', 7.2)}<br>
                    <b>🛡️ DD Score:</b> <b style="color: #059669;">{score}/100</b> ({grade})
                </div>

                <div style="background: #FEF3C7; border: 1px solid #FDE68A; padding: 4px 6px; border-radius: 4px; font-size: 10px; margin-bottom: 6px;">
                    <b>📰 {news_source}:</b> {news_title[:45]}...
                    <a href="{news_url}" target="_blank" style="color: #D97706; font-weight: bold; text-decoration: underline;">Verify ↗</a>
                </div>

                <div style="display: flex; gap: 4px; margin-top: 6px;">
                    <a href="{directions_url}" target="_blank" style="flex: 1; text-align: center; background: #2563EB; color: white; padding: 6px 4px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">
                        🗺️ Directions ↗
                    </a>
                    <a href="{p.get('contact_whatsapp', '#')}" target="_blank" style="flex: 1; text-align: center; background: #16A34A; color: white; padding: 6px 4px; border-radius: 4px; text-decoration: none; font-size: 11px; font-weight: bold;">
                        💬 WhatsApp ↗
                    </a>
                </div>
            </div>
        </div>
        """

        folium.Marker(
            location=[p_lat, p_lng],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"#{sno}. {p.get('name')} | {road_km} km ({drive_time}) | ₹{p.get('price_per_acre_lakhs')} L/Ac {'[🚨 SC/ST RESTRICTED]' if is_sc_st else ''}",
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(44, 24),
                icon_anchor=(22, 12)
            )
        ).add_to(marker_cluster)

    # 4. Optional Selected Pin (Clicked on Map or Searched)
    if selected_pin:
        s_lat = float(selected_pin.get("lat", origin_lat))
        s_lng = float(selected_pin.get("lng", origin_lng))
        s_title = selected_pin.get("title", "Selected Map Location")
        s_desc = selected_pin.get("description", "Complete the form below to add this parcel.")

        sel_popup = f"""
        <div style="font-family: Arial, sans-serif; font-size: 12px; color: #0F172A; min-width: 220px;">
            <div style="background: #F59E0B; color: #78350F; padding: 6px 8px; border-radius: 4px; font-weight: bold; margin-bottom: 4px;">
                📍 {s_title}
            </div>
            <b>Coordinates:</b> {s_lat:.5f}, {s_lng:.5f}<br>
            <div style="color: #475569; font-size: 11px; margin-top: 4px;">
                {s_desc}
            </div>
        </div>
        """

        folium.Marker(
            location=[s_lat, s_lng],
            popup=folium.Popup(sel_popup, max_width=280),
            tooltip=f"📍 {s_title} ({s_lat:.4f}, {s_lng:.4f})",
            icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
        ).add_to(m)

        # Draw a small circle around the clicked location
        folium.Circle(
            location=[s_lat, s_lng],
            radius=600,
            color="#EF4444",
            weight=2,
            fill=True,
            fill_color="#F87171",
            fill_opacity=0.25
        ).add_to(m)

    folium.LayerControl(position="topright").add_to(m)
    return m
