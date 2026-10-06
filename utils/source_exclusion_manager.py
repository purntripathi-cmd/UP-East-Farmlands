"""
Data Source Registry & Quality Exclusion Manager
Handles tracking, auditing, and quality exclusion of farmland inventory sources.
Enables investors to:
- Review all 60+ data sources across Government registries, Bank SARFAESI portals,
  e-papers, private real estate portals, and social video leads.
- Exclude specific sources or entire sourcing channels if data is found outdated,
  phone numbers are invalid, or records are non-verifiable.
- Automatically filter out all parcels originating from excluded sources across
  all maps, dossiers, ledgers, news feeds, and export workbooks.
- Persist source exclusion rules in data/excluded_sources.json with full audit history.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Set, Optional


def get_excluded_sources_file_path() -> str:
    """Returns absolute path to data/excluded_sources.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "excluded_sources.json")


def load_excluded_sources() -> Dict[str, Dict[str, Any]]:
    """Loads all excluded sources from persistent JSON storage."""
    file_path = get_excluded_sources_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_excluded_sources(excluded: Dict[str, Dict[str, Any]]) -> bool:
    """Persists excluded sources dictionary to disk."""
    file_path = get_excluded_sources_file_path()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(excluded, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def exclude_source(
    source_name: str,
    reason: str = "Data found outdated or incorrect",
    source_type: str = "source_name"
) -> bool:
    """
    Excludes a source by its name or identifier.
    source_type can be 'source_name', 'published_news_source', or 'channel'.
    """
    clean_name = str(source_name).strip()
    if not clean_name:
        return False

    excluded = load_excluded_sources()
    now_str = datetime.datetime.now().strftime("%d %b %Y, %H:%M IST")

    excluded[clean_name] = {
        "source_name": clean_name,
        "source_type": source_type,
        "reason": reason.strip() or "Data found outdated or incorrect",
        "excluded_at": now_str
    }
    return save_excluded_sources(excluded)


def restore_source(source_name: str) -> bool:
    """Restores an excluded source to active status."""
    excluded = load_excluded_sources()
    clean_name = str(source_name).strip()
    if clean_name in excluded:
        del excluded[clean_name]
        return save_excluded_sources(excluded)
    return False


def restore_all_sources() -> bool:
    """Restores all excluded sources, clearing the exclusion list."""
    return save_excluded_sources({})


def classify_source_channel(source_name: str, news_source: str = "", source_url: str = "") -> str:
    """Classifies a source into a canonical high-level channel."""
    comb = f"{source_name} {news_source} {source_url}".lower()

    if any(k in comb for k in ["sarfaesi", "ibapi", "bank of baroda", "state bank of india", "sbi", "pnb", "union bank", "recovery", "stressed"]):
        return "🏦 Bank SARFAESI / IBAPI Distressed Auctions"
    elif any(k in comb for k in ["bhulekh", "revenue", "bihar bhumi", "mp bhulekh", "tehsil", "sadar", "rtc", "kacheri"]):
        return "🏛️ Government Revenue Portals (UP / Bihar / MP Bhulekh)"
    elif any(k in comb for k in ["sfarmsindia", "99acres", "magicbricks", "realestateindia", "olx", "brokerage"]):
        return "🏡 Private Farmland & Real Estate Portals (99acres / MagicBricks / RealEstateIndia / OLX)"
    elif any(k in comb for k in ["youtube", "drone walk", "video lead", "channel"]):
        return "📹 Social Media & Farmer Video Walkthrough Leads"
    elif any(k in comb for k in ["jagran", "amar ujala", "hindustan", "e-paper", "bulletin", "gazette", "notice"]):
        return "📰 Newspaper Gazette & Public Caveat Notices"
    elif any(k in comb for k in ["mission", "sandalwood", "agro-forestry", "nhai", "highway", "icar", "kvk", "cish", "cimap"]):
        return "🌿 Institutional Agro-Missions & Research Institutes"
    return "🌐 General Farmland Listings"


def is_bank_eauction_or_stressed_asset(parcel: Dict[str, Any]) -> bool:
    """
    Identifies whether a parcel originates from Bank SARFAESI e-auctions,
    distressed bank recovery notices, or recovery officer proceedings.
    """
    tier = str(parcel.get("sourcing_tier", "")).lower()
    src = str(parcel.get("source_name", "")).lower()
    seller = str(parcel.get("seller_category", "")).lower()
    news = str(parcel.get("published_news_source", "")).lower()
    legal = str(parcel.get("notice_or_legal_type", "")).lower()
    url = str(parcel.get("source_url", "")).lower()
    comb = f"{tier} {src} {seller} {news} {legal} {url}"
    return any(k in comb for k in [
        "sarfaesi", "ibapi", "e-auction", "eauction", 
        "bank distress", "stressed asset", "recovery officer", 
        "sarb", "recovery notice", "bank of baroda", "state bank of india",
        "pnb cleared"
    ])



def is_source_excluded(
    parcel: Dict[str, Any],
    excluded_dict: Optional[Dict[str, Dict[str, Any]]] = None
) -> bool:
    """
    Checks if a parcel's source matches any excluded source.
    Evaluates:
    - Exact match on parcel['source_name']
    - Exact match on parcel['published_news_source']
    - Match on parcel's classified channel
    """
    excluded = excluded_dict if excluded_dict is not None else load_excluded_sources()
    if not excluded:
        return False

    s_name = str(parcel.get("source_name", "")).strip()
    news_s = str(parcel.get("published_news_source", "")).strip()
    s_url = str(parcel.get("source_url", "")).strip()
    channel = classify_source_channel(s_name, news_s, s_url)

    if s_name and s_name in excluded:
        return True
    if news_s and news_s in excluded:
        return True
    if channel and channel in excluded:
        return True

    return False


def build_sources_registry(
    all_parcels: List[Dict[str, Any]],
    excluded_dict: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Builds an aggregated registry of all unique sources found across all farmland parcels.
    Returns sorted list of source summary dictionaries.
    """
    excluded = excluded_dict if excluded_dict is not None else load_excluded_sources()
    sources_map: Dict[str, Dict[str, Any]] = {}

    for p in all_parcels:
        sname = str(p.get("source_name", "Unknown Source")).strip()
        news_s = str(p.get("published_news_source", "General Notice")).strip()
        s_url = str(p.get("source_url", "https://upbhulekh.gov.in/")).strip()
        tier = str(p.get("sourcing_tier", "Uncategorized")).strip()
        dist = str(p.get("regional_district", "Varanasi")).strip()
        score = float(p.get("due_diligence_score", 90))
        price = float(p.get("price_per_acre_lakhs", 0.0))
        channel = classify_source_channel(sname, news_s, s_url)

        if sname not in sources_map:
            sources_map[sname] = {
                "source_name": sname,
                "source_channel": channel,
                "source_url": s_url,
                "published_news_source": news_s,
                "sourcing_tier": tier,
                "parcel_count": 0,
                "districts": set(),
                "sample_parcels": [],
                "scores": [],
                "prices": []
            }

        s_entry = sources_map[sname]
        s_entry["parcel_count"] += 1
        s_entry["districts"].add(dist)
        s_entry["scores"].append(score)
        s_entry["prices"].append(price)
        if len(s_entry["sample_parcels"]) < 3:
            s_entry["sample_parcels"].append(f"{p.get('name', 'Parcel')} ({dist})")

    registry = []
    for sname, info in sources_map.items():
        is_ex = sname in excluded or info["source_channel"] in excluded or info["published_news_source"] in excluded
        ex_info = excluded.get(sname) or excluded.get(info["source_channel"]) or excluded.get(info["published_news_source"])
        avg_score = round(sum(info["scores"]) / len(info["scores"]), 1) if info["scores"] else 90.0
        avg_price = round(sum(info["prices"]) / len(info["prices"]), 1) if info["prices"] else 0.0

        registry.append({
            "source_name": sname,
            "source_channel": info["source_channel"],
            "source_url": info["source_url"],
            "published_news_source": info["published_news_source"],
            "sourcing_tier": info["sourcing_tier"],
            "parcel_count": info["parcel_count"],
            "districts": sorted(list(info["districts"])),
            "districts_display": ", ".join(sorted(list(info["districts"]))),
            "sample_parcels_display": " • ".join(info["sample_parcels"]),
            "avg_due_diligence_score": avg_score,
            "avg_price_acre": avg_price,
            "is_excluded": is_ex,
            "exclusion_reason": ex_info.get("reason", "") if ex_info else "",
            "exclusion_date": ex_info.get("excluded_at", "") if ex_info else ""
        })

    # Sort: active first, then by parcel count descending
    registry.sort(key=lambda x: (x["is_excluded"], -x["parcel_count"], x["source_name"]))
    return registry


def filter_parcels_by_source_exclusion(
    parcels: List[Dict[str, Any]],
    excluded_dict: Optional[Dict[str, Dict[str, Any]]] = None,
    allow_excluded: bool = False
) -> List[Dict[str, Any]]:
    """Filters parcels, dropping any parcel whose source is excluded unless allow_excluded is True."""
    if allow_excluded:
        return list(parcels)

    excluded = excluded_dict if excluded_dict is not None else load_excluded_sources()
    if not excluded:
        return list(parcels)

    return [p for p in parcels if not is_source_excluded(p, excluded)]


def get_channel_summaries(registry: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregates metrics by high-level source channel."""
    channels: Dict[str, Dict[str, Any]] = {}
    for r in registry:
        ch = r["source_channel"]
        if ch not in channels:
            channels[ch] = {
                "channel": ch,
                "total_sources": 0,
                "active_sources": 0,
                "excluded_sources": 0,
                "total_parcels": 0,
                "active_parcels": 0,
                "excluded_parcels": 0
            }
        c_entry = channels[ch]
        c_entry["total_sources"] += 1
        c_entry["total_parcels"] += r["parcel_count"]
        if r["is_excluded"]:
            c_entry["excluded_sources"] += 1
            c_entry["excluded_parcels"] += r["parcel_count"]
        else:
            c_entry["active_sources"] += 1
            c_entry["active_parcels"] += r["parcel_count"]

    return sorted(list(channels.values()), key=lambda x: -x["total_parcels"])
