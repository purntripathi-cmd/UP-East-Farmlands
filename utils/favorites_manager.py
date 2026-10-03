"""
Persistent User Favorites / Shortlisting Manager
Enables investors to star, shortlist, persist, and export preferred farmland estates.
Synchronizes with local JSON storage (data/user_favorites.json) for persistence across sessions.
"""

import os
import json
from typing import List, Set, Dict, Any


def get_favorites_file_path() -> str:
    """Returns absolute path to user_favorites.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "user_favorites.json")


def load_favorites() -> Set[str]:
    """Loads favorited parcel IDs from persistent disk storage."""
    file_path = get_favorites_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(str(x) for x in data)
        except Exception:
            pass
    return set()


def save_favorites(fav_set: Set[str]) -> bool:
    """Persists favorited parcel IDs to disk."""
    file_path = get_favorites_file_path()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(sorted(list(fav_set)), f, indent=2)
        return True
    except Exception:
        return False


def toggle_favorite(parcel_id: str) -> bool:
    """
    Toggles favorite status for a given parcel ID and saves to disk.
    Returns: True if now favorited, False if unfavorited.
    """
    favs = load_favorites()
    pid = str(parcel_id)
    if pid in favs:
        favs.remove(pid)
        is_now_fav = False
    else:
        favs.add(pid)
        is_now_fav = True
    save_favorites(favs)
    return is_now_fav


def is_favorite(parcel_id: str, cached_set: Set[str] = None) -> bool:
    """Checks whether a parcel ID is in favorites."""
    if cached_set is not None:
        return str(parcel_id) in cached_set
    favs = load_favorites()
    return str(parcel_id) in favs


def filter_favorite_parcels(parcels: List[Dict[str, Any]], cached_set: Set[str] = None) -> List[Dict[str, Any]]:
    """Returns list of parcel dictionaries that match user favorites."""
    favs = cached_set if cached_set is not None else load_favorites()
    return [p for p in parcels if str(p.get("id")) in favs]
