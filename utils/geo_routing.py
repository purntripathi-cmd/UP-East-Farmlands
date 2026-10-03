"""
Geo-Routing & Actual Road Distance Engine
Calculates aerial and realistic driving road distances from selectable reference landmarks in Eastern UP,
defaulting to Kacheri Varanasi near Varuna Pul.
Supports automatic anchoring to respective District City Centers (Varanasi, Chandauli, Mirzapur,
Jaunpur, Ghazipur, Azamgarh, Prayagraj, Bhadohi, Sonbhadra, Ballia, Mau).
Generates one-click Google Maps Navigation and Satellite Exploration links.
"""

import math
import os
import json
from typing import Dict, Any, List, Tuple

# Default Reference Landmark: Kacheri Varanasi near Varuna Pul (Varanasi Revenue Court & Collectorate)
DEFAULT_ORIGIN_LAT = 25.3375
DEFAULT_ORIGIN_LNG = 82.9815
DEFAULT_ORIGIN_NAME = "Kacheri Varanasi near Varuna Pul (Collectorate / Court)"

# Respective District City Centers (Administrative Collectorates & Zero-Points)
DISTRICT_CITY_CENTERS: Dict[str, Dict[str, Any]] = {
    "Varanasi": {
        "id": "kacheri_varuna",
        "name": "Kacheri Varanasi near Varuna Pul (Collectorate / Court)",
        "district": "Varanasi",
        "lat": 25.3375,
        "lng": 82.9815,
        "description": "Varanasi Revenue Court, Collectorate & Varuna Bridge Zero-Point"
    },
    "Chandauli": {
        "id": "chandauli_collectorate",
        "name": "Chandauli District Collectorate & Court (Chandauli City Center)",
        "district": "Chandauli",
        "lat": 25.2600,
        "lng": 83.2650,
        "description": "Chandauli District Administrative Headquarters & Revenue Court (Rice Bowl of UP)"
    },
    "Mirzapur": {
        "id": "mirzapur_kacheri",
        "name": "Mirzapur Kacheri & Clock Tower (Mirzapur City Center)",
        "district": "Mirzapur",
        "lat": 25.1480,
        "lng": 82.5690,
        "description": "Mirzapur District Court, Ghanta Ghar & Vindhya Administrative Hub"
    },
    "Jaunpur": {
        "id": "jaunpur_collectorate",
        "name": "Jaunpur Collectorate & Olandganj Chowk (Jaunpur City Center)",
        "district": "Jaunpur",
        "lat": 25.7464,
        "lng": 82.6837,
        "description": "Jaunpur District Court, Collectorate & Gomti River Basin Center"
    },
    "Ghazipur": {
        "id": "ghazipur_collectorate",
        "name": "Ghazipur Collectorate & Lanka Chowk (Ghazipur City Center)",
        "district": "Ghazipur",
        "lat": 25.5840,
        "lng": 83.5770,
        "description": "Ghazipur District Headquarters, Court & Ganga Alluvium Center"
    },
    "Azamgarh": {
        "id": "azamgarh_collectorate",
        "name": "Azamgarh District Collectorate & Chowk (Azamgarh City Center)",
        "district": "Azamgarh",
        "lat": 26.0738,
        "lng": 83.1859,
        "description": "Azamgarh Divisional Headquarters & Civil Lines Court"
    },
    "Prayagraj": {
        "id": "prayagraj_collectorate",
        "name": "Prayagraj Collectorate & Civil Lines (Prayagraj City Center)",
        "district": "Prayagraj",
        "lat": 25.4500,
        "lng": 81.8400,
        "description": "Prayagraj District Magistrate Office, Civil Lines & Revenue Board"
    },
    "Bhadohi": {
        "id": "bhadohi_gyanpur",
        "name": "Gyanpur Collectorate & Bhadohi Hub (Bhadohi City Center)",
        "district": "Bhadohi",
        "lat": 25.3450,
        "lng": 82.4330,
        "description": "Bhadohi District Administrative Headquarters at Gyanpur Kacheri"
    },
    "Sonbhadra": {
        "id": "sonbhadra_robertsganj",
        "name": "Robertsganj District Collectorate (Sonbhadra City Center)",
        "district": "Sonbhadra",
        "lat": 24.6850,
        "lng": 83.0650,
        "description": "Sonbhadra Administrative Headquarters at Robertsganj"
    },
    "Ballia": {
        "id": "ballia_collectorate",
        "name": "Ballia District Collectorate (Ballia City Center)",
        "district": "Ballia",
        "lat": 25.7600,
        "lng": 84.1500,
        "description": "Ballia Easternmost District Court & Revenue Office"
    },
    "Mau": {
        "id": "mau_collectorate",
        "name": "Mau District Collectorate (Mau City Center)",
        "district": "Mau",
        "lat": 25.9400,
        "lng": 83.5600,
        "description": "Mau District Administrative & Revenue Court Complex"
    },
    "Kaimur": {
        "id": "kaimur_bhabua",
        "name": "Bhabua Collectorate & Kaimur Hub (Kaimur City Center)",
        "district": "Kaimur",
        "lat": 25.0450,
        "lng": 83.6150,
        "description": "Kaimur District Administrative Center at Bhabua"
    }
}


def get_city_center_for_district(district_name: str) -> Dict[str, Any]:
    """
    Returns the respective city center benchmark (name, lat, lng, description) for any district.
    Defaults to Kacheri Varanasi near Varuna Pul if district is None, empty, or 'All Districts'.
    """
    if not district_name or "All" in district_name:
        return DISTRICT_CITY_CENTERS["Varanasi"]
    
    clean_d = district_name.strip()
    for d_key, center_obj in DISTRICT_CITY_CENTERS.items():
        if d_key.lower() == clean_d.lower():
            return center_obj
    return DISTRICT_CITY_CENTERS["Varanasi"]


def load_landmarks() -> List[Dict[str, Any]]:
    """Loads all selectable reference landmarks and city centers."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    benchmarks_path = os.path.join(base_dir, "data", "benchmarks.json")
    if os.path.exists(benchmarks_path):
        try:
            with open(benchmarks_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [{
        "id": "kacheri_varuna",
        "name": DEFAULT_ORIGIN_NAME,
        "description": "Varanasi Revenue Court & Collectorate Hub",
        "lat": DEFAULT_ORIGIN_LAT,
        "lng": DEFAULT_ORIGIN_LNG,
        "is_default": True
    }]


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates aerial Great-Circle distance in kilometers using Haversine formula."""
    R = 6371.0088  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


def estimate_road_distance_km(aerial_km: float, location_name: str = "") -> float:
    """
    Estimates actual driving road distance based on Eastern UP Highway & Arterial network layout.
    Major corridors (NH-19, NH-56, NH-31, Ring Road Phase 2) have a 1.20 - 1.24 winding factor,
    while interior village / taluk link roads have a 1.28 - 1.35 winding factor.
    """
    loc_lower = location_name.lower()
    if any(k in loc_lower for k in ["nh-19", "nh-56", "nh-31", "ring road", "highway", "expressway", "gt road", "babatpur"]):
        factor = 1.22
    elif any(k in loc_lower for k in ["rohania", "shivpur", "harahua", "sarnath", "chitaipur", "ramnagar"]):
        factor = 1.25
    elif aerial_km < 15:
        factor = 1.28
    elif aerial_km < 40:
        factor = 1.26
    else:
        factor = 1.30

    road_km = round(aerial_km * factor, 1)
    return max(road_km, round(aerial_km * 1.15, 1))


def estimate_driving_time_minutes(road_km: float) -> int:
    """
    Estimates realistic driving time in minutes assuming mixed urban / highway speeds
    (avg 35 km/h urban fringe, 50 km/h regional highways).
    """
    if road_km <= 15:
        speed = 32.0  # City traffic / suburban bottleneck
    elif road_km <= 50:
        speed = 42.0  # Mixed ring road & 4-lane highway
    else:
        speed = 52.0  # National Highway / Expressway
    minutes = int(round((road_km / speed) * 60))
    return max(minutes, 5)


def get_google_maps_directions_url(dest_lat: float, dest_lng: float, origin_lat: float = DEFAULT_ORIGIN_LAT, origin_lng: float = DEFAULT_ORIGIN_LNG) -> str:
    """Generates official Google Maps turn-by-turn driving directions URL."""
    return f"https://www.google.com/maps/dir/?api=1&origin={origin_lat:.5f},{origin_lng:.5f}&destination={dest_lat:.5f},{dest_lng:.5f}&travelmode=driving"


def get_google_maps_satellite_search_url(lat: float, lng: float, query: str = "") -> str:
    """Generates official Google Maps satellite layer URL focused on parcel coordinates."""
    # &t=k parameter forces Google Maps to load the high-resolution satellite imagery layer
    return f"https://maps.google.com/?q={lat:.6f},{lng:.6f}&t=k"


def get_google_maps_pin_url(lat: float, lng: float) -> str:
    """Generates official Google Maps direct pin URL for specific parcel coordinates."""
    return f"https://www.google.com/maps/search/?api=1&query={lat:.6f},{lng:.6f}"


def assign_concentric_ring(aerial_km: float) -> str:
    """Categorizes distance into concentric radial rings."""
    if aerial_km <= 20.0:
        return "Within 20 km"
    elif aerial_km <= 40.0:
        return "20 to 40 km"
    elif aerial_km <= 60.0:
        return "40 to 60 km"
    elif aerial_km <= 80.0:
        return "60 to 80 km"
    elif aerial_km <= 100.0:
        return "80 to 100 km"
    else:
        return "100 to 200 km Buffer"


def compute_parcel_routing(
    parcel: Dict[str, Any],
    origin_lat: float = DEFAULT_ORIGIN_LAT,
    origin_lng: float = DEFAULT_ORIGIN_LNG,
    origin_name: str = DEFAULT_ORIGIN_NAME
) -> Dict[str, Any]:
    """Computes full routing telemetry from active origin to farmland parcel."""
    dest_lat = float(parcel.get("lat", DEFAULT_ORIGIN_LAT))
    dest_lng = float(parcel.get("lng", DEFAULT_ORIGIN_LNG))

    aerial_km = haversine_distance_km(origin_lat, origin_lng, dest_lat, dest_lng)
    road_km = estimate_road_distance_km(aerial_km, parcel.get("location", ""))
    driving_mins = estimate_driving_time_minutes(road_km)
    directions_url = get_google_maps_directions_url(dest_lat, dest_lng, origin_lat, origin_lng)
    satellite_url = get_google_maps_satellite_search_url(dest_lat, dest_lng, parcel.get("name", ""))
    maps_pin_url = get_google_maps_pin_url(dest_lat, dest_lng)
    ring = assign_concentric_ring(aerial_km)

    # Format human-readable travel time
    if driving_mins >= 60:
        hours = driving_mins // 60
        mins = driving_mins % 60
        time_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
    else:
        time_str = f"{driving_mins} mins"

    return {
        "origin_name": origin_name,
        "origin_lat": origin_lat,
        "origin_lng": origin_lng,
        "aerial_km": aerial_km,
        "road_km": road_km,
        "driving_minutes": driving_mins,
        "driving_time_display": time_str,
        "google_directions_url": directions_url,
        "google_satellite_url": satellite_url,
        "google_maps_pin_url": maps_pin_url,
        "distance_ring": ring
    }
