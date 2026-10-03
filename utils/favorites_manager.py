"""
Persistent Multi-User Favorites & Shortlisting Manager
Enables investors to star, shortlist, persist, and export preferred farmland estates by username.
Supports multi-user tagging (default usernames: VPT, PPT, Guest-1, guest-2) and custom first names.
Synchronizes with local JSON storage (data/user_favorites.json) for persistence across sessions.
All favorites are visible to all users and can be filtered by username.
"""

import os
import json
from datetime import datetime
from typing import List, Set, Dict, Any, Optional

DEFAULT_USERNAMES: List[str] = ["VPT", "PPT", "Guest-1", "guest-2"]


def get_favorites_file_path() -> str:
    """Returns absolute path to user_favorites.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "user_favorites.json")


def load_raw_favorites() -> List[Dict[str, Any]]:
    """
    Loads raw favorite records from persistent disk storage.
    Automatically migrates legacy string lists ['id1', 'id2'] to structured records.
    """
    file_path = get_favorites_file_path()
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            records: List[Dict[str, Any]] = []
            for item in data:
                if isinstance(item, str):
                    # Legacy migration: attribute to default user VPT
                    records.append({
                        "parcel_id": str(item),
                        "username": "VPT",
                        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST")
                    })
                elif isinstance(item, dict) and "parcel_id" in item:
                    records.append({
                        "parcel_id": str(item["parcel_id"]),
                        "username": str(item.get("username", "VPT")).strip() or "VPT",
                        "timestamp": str(item.get("timestamp", datetime.now().strftime("%d %b %Y, %H:%M IST")))
                    })
            return records
    except Exception:
        pass
    return []


def save_raw_favorites(records: List[Dict[str, Any]]) -> bool:
    """Persists favorite records list to disk."""
    file_path = get_favorites_file_path()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # Deduplicate identical (parcel_id, username)
        seen = set()
        deduped = []
        for r in records:
            key = (str(r.get("parcel_id")), str(r.get("username", "")).strip())
            if key not in seen and key[0] and key[1]:
                seen.add(key)
                deduped.append(r)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(deduped, f, indent=2)
        return True
    except Exception:
        return False


def load_favorites(username: Optional[str] = None) -> Set[str]:
    """
    Loads favorited parcel IDs.
    - If username is None or 'All Users': returns set of all parcel IDs favorited by any user.
    - If username is specified: returns set of parcel IDs favorited by that specific user.
    """
    records = load_raw_favorites()
    if not username or username in ("All Users", "All", ""):
        return {r["parcel_id"] for r in records}
    target_user = username.strip().lower()
    return {r["parcel_id"] for r in records if r.get("username", "").strip().lower() == target_user}


def save_favorites(fav_set: Set[str], username: str = "VPT") -> bool:
    """
    Persists favorited parcel IDs for a specific user to disk.
    Preserves favorites registered by other users.
    """
    records = load_raw_favorites()
    target_user = username.strip().lower() if username else "vpt"
    # Keep other users' favorites
    kept_records = [r for r in records if r.get("username", "").strip().lower() != target_user]
    # Add new favorites for this user
    now_str = datetime.now().strftime("%d %b %Y, %H:%M IST")
    for pid in sorted(list(fav_set)):
        kept_records.append({
            "parcel_id": str(pid),
            "username": username.strip() if username else "VPT",
            "timestamp": now_str
        })
    return save_raw_favorites(kept_records)


def add_favorite(parcel_id: str, username: str = "VPT") -> bool:
    """
    Adds a favorite for a given parcel ID and username.
    Returns True if added, False if already existed or on error.
    """
    clean_user = username.strip() if username and username.strip() else "VPT"
    pid = str(parcel_id)
    records = load_raw_favorites()
    for r in records:
        if r.get("parcel_id") == pid and r.get("username", "").strip().lower() == clean_user.lower():
            return False  # Already favorited by this user

    records.append({
        "parcel_id": pid,
        "username": clean_user,
        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST")
    })
    return save_raw_favorites(records)


def remove_favorite(parcel_id: str, username: Optional[str] = None) -> bool:
    """
    Removes favorite(s) for a given parcel ID.
    - If username is specified: removes favorite for that specific user only.
    - If username is None: removes all favorites for this parcel across all users.
    """
    pid = str(parcel_id)
    records = load_raw_favorites()
    if username and username not in ("All Users", "All"):
        clean_user = username.strip().lower()
        new_records = [
            r for r in records
            if not (r.get("parcel_id") == pid and r.get("username", "").strip().lower() == clean_user)
        ]
    else:
        new_records = [r for r in records if r.get("parcel_id") != pid]

    return save_raw_favorites(new_records)


def toggle_favorite(parcel_id: str, username: str = "VPT") -> bool:
    """
    Toggles favorite status for a given parcel ID and user.
    Returns: True if now favorited by this user, False if removed.
    """
    clean_user = username.strip() if username and username.strip() else "VPT"
    pid = str(parcel_id)
    records = load_raw_favorites()

    found_idx = -1
    for i, r in enumerate(records):
        if r.get("parcel_id") == pid and r.get("username", "").strip().lower() == clean_user.lower():
            found_idx = i
            break

    if found_idx >= 0:
        records.pop(found_idx)
        save_raw_favorites(records)
        return False
    else:
        records.append({
            "parcel_id": pid,
            "username": clean_user,
            "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST")
        })
        save_raw_favorites(records)
        return True


def is_favorite(
    parcel_id: str,
    username: Optional[Any] = None,
    cached_set: Optional[Set[str]] = None
) -> bool:
    """
    Checks whether a parcel ID is favorited.
    - If username is a set/list/tuple: treated as cached_set (backward compatibility).
    - If username is a string: checks if favorited by that user.
    - If username is None or 'All Users': checks if favorited by ANY user.
    - If cached_set is provided and username is None: directly checks membership in cached_set.
    """
    pid = str(parcel_id)
    # Backward compatibility: handle 2nd positional argument passed as a collection/set of fav IDs
    if isinstance(username, (set, list, tuple)):
        cached_set = set(username)
        username = None

    if cached_set is not None and (username is None or username in ("All Users", "All", "")):
        return pid in cached_set

    records = load_raw_favorites()
    if not username or username in ("All Users", "All", ""):
        return any(r.get("parcel_id") == pid for r in records)

    if isinstance(username, str):
        clean_user = username.strip().lower()
        return any(r.get("parcel_id") == pid and r.get("username", "").strip().lower() == clean_user for r in records)

    return False


def get_users_for_parcel(parcel_id: str, raw_records: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Returns list of usernames who have favorited the specified parcel."""
    pid = str(parcel_id)
    records = raw_records if raw_records is not None else load_raw_favorites()
    users = []
    seen = set()
    for r in records:
        if r.get("parcel_id") == pid:
            u = r.get("username", "").strip()
            if u and u.lower() not in seen:
                seen.add(u.lower())
                users.append(u)
    return users


def get_all_active_usernames(raw_records: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Returns list of all active usernames, starting with the defaults:
    VPT, PPT, Guest-1, guest-2, followed by any custom usernames in records.
    """
    records = raw_records if raw_records is not None else load_raw_favorites()
    names = list(DEFAULT_USERNAMES)
    seen = {n.lower() for n in names}
    for r in records:
        u = r.get("username", "").strip()
        if u and u.lower() not in seen:
            seen.add(u.lower())
            names.append(u)
    return names


def filter_favorite_parcels(
    parcels: List[Dict[str, Any]],
    cached_set: Optional[Set[str]] = None,
    username: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Returns list of parcel dictionaries matching favorites (by user, or all users)."""
    if username and username not in ("All Users", "All", ""):
        fav_ids = load_favorites(username=username)
    else:
        fav_ids = cached_set if cached_set is not None else load_favorites()
    return [p for p in parcels if str(p.get("id")) in fav_ids]


def clear_all_favorites(username: Optional[str] = None) -> bool:
    """
    Clears favorites:
    - If username is specified: clears favorites for that user only.
    - If username is None: clears all favorites across all users.
    """
    if not username or username in ("All Users", "All"):
        return save_raw_favorites([])
    clean_user = username.strip().lower()
    records = load_raw_favorites()
    new_records = [r for r in records if r.get("username", "").strip().lower() != clean_user]
    return save_raw_favorites(new_records)
