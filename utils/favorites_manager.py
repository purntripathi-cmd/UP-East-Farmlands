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


def get_favorites_csv_file_path() -> str:
    """Returns absolute path to user_favorites.csv."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "user_favorites.csv")


def get_candidate_favorites_file_paths() -> List[str]:
    """Returns all potential disk paths where favorites might be persisted."""
    primary = get_favorites_file_path()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")

    # If primary was overridden outside the project data directory (e.g., isolated test sandbox)
    if not os.path.abspath(primary).startswith(os.path.abspath(data_dir)):
        return [primary]

    candidates = [
        primary,
        os.path.join(data_dir, "user_favorites.csv"),
        os.path.join(data_dir, "favorites.json"),
        os.path.join(data_dir, "saved_favorites.json"),
    ]
    res = []
    seen = set()
    for c in candidates:
        if c not in seen:
            seen.add(c)
            res.append(c)
    return res


def load_raw_favorites() -> List[Dict[str, Any]]:
    """
    Loads raw favorite records from persistent disk storage.
    Consolidates old and new favorites across all candidate files.
    Preserves all records, even if username tagging was omitted (defaults to 'Untagged').
    """
    all_records: List[Dict[str, Any]] = []
    seen = set()

    for file_path in get_candidate_favorites_file_paths():
        if not os.path.exists(file_path):
            continue
        try:
            if file_path.endswith(".csv"):
                import csv
                with open(file_path, "r", encoding="utf-8") as f_csv:
                    reader = csv.DictReader(f_csv)
                    for row in reader:
                        pid = str(row.get("parcel_id") or row.get("id") or "").strip()
                        if not pid:
                            continue
                        clean_u = str(row.get("username") or "Untagged").strip()
                        key = (pid, clean_u.lower())
                        if key not in seen:
                            seen.add(key)
                            all_records.append({
                                "parcel_id": pid,
                                "username": clean_u,
                                "timestamp": row.get("timestamp") or datetime.now().strftime("%d %b %Y, %H:%M IST")
                            })
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_items = []
            if isinstance(data, list):
                raw_items = data
            elif isinstance(data, dict):
                if "favorites" in data and isinstance(data["favorites"], list):
                    raw_items = data["favorites"]
                elif "records" in data and isinstance(data["records"], list):
                    raw_items = data["records"]
                elif "saved" in data and isinstance(data["saved"], list):
                    raw_items = data["saved"]
                else:
                    for k, v in data.items():
                        if isinstance(v, dict):
                            item_d = dict(v)
                            item_d.setdefault("parcel_id", k)
                            raw_items.append(item_d)
                        elif v:
                            raw_items.append({"parcel_id": str(k)})

            for item in raw_items:
                if isinstance(item, str):
                    pid = str(item).strip()
                    if pid:
                        key = (pid, "untagged")
                        if key not in seen:
                            seen.add(key)
                            all_records.append({
                                "parcel_id": pid,
                                "username": "Untagged",
                                "timestamp": datetime.now().strftime("%d %b %Y, %H:%M IST")
                            })
                elif isinstance(item, dict):
                    pid = str(item.get("parcel_id") or item.get("id") or item.get("farm_id") or "").strip()
                    if not pid:
                        continue
                    raw_u = item.get("username")
                    clean_u = str(raw_u).strip() if raw_u and str(raw_u).strip() else "Untagged"
                    key = (pid, clean_u.lower())
                    if key not in seen:
                        seen.add(key)
                        all_records.append({
                            "parcel_id": pid,
                            "username": clean_u,
                            "timestamp": str(item.get("timestamp") or datetime.now().strftime("%d %b %Y, %H:%M IST"))
                        })
        except Exception:
            continue

    return all_records


def save_raw_favorites(records: List[Dict[str, Any]]) -> bool:
    """Persists favorite records list to disk, preserving all items including untagged."""
    file_path = get_favorites_file_path()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        seen = set()
        deduped = []
        for r in records:
            pid = str(r.get("parcel_id") or r.get("id") or "").strip()
            if not pid:
                continue
            raw_u = r.get("username")
            clean_u = str(raw_u).strip() if raw_u and str(raw_u).strip() else "Untagged"
            key = (pid, clean_u.lower())
            if key not in seen:
                seen.add(key)
                deduped.append({
                    "parcel_id": pid,
                    "username": clean_u,
                    "timestamp": str(r.get("timestamp") or datetime.now().strftime("%d %b %Y, %H:%M IST"))
                })

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(deduped, f, indent=2)

        # Mirror to CSV file for immediate user inspection, QGIS, and spreadsheet access
        csv_path = get_favorites_csv_file_path()
        try:
            import csv
            with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
                writer = csv.writer(f_csv)
                writer.writerow(["parcel_id", "username", "timestamp"])
                for item in deduped:
                    writer.writerow([item["parcel_id"], item["username"], item.get("timestamp", "")])
        except Exception:
            pass

        return True
    except Exception:
        return False


def load_favorites(username: Optional[str] = None) -> Set[str]:
    """
    Loads favorited parcel IDs.
    - If username is None, 'All Users', 'All', or '': returns set of all parcel IDs favorited by any user (including untagged).
    - If username is 'Untagged' or 'General': returns parcel IDs that have no specific user tagged.
    - If username is specified: returns set of parcel IDs favorited by that specific user.
    """
    records = load_raw_favorites()
    if not username or username in ("All Users", "All", ""):
        return {r["parcel_id"] for r in records}
    target_user = username.strip().lower()
    if target_user in ("untagged", "general", "general / untagged"):
        return {r["parcel_id"] for r in records if r.get("username", "").strip().lower() in ("untagged", "general", "general / untagged", "")}
    return {r["parcel_id"] for r in records if r.get("username", "").strip().lower() == target_user}


def save_favorites(fav_set: Set[str], username: str = "VPT") -> bool:
    """
    Persists favorited parcel IDs for a specific user to disk.
    Preserves favorites registered by other users and untagged records.
    """
    records = load_raw_favorites()
    target_user = username.strip().lower() if username and username.strip() else "vpt"
    # Keep other users' favorites
    kept_records = [r for r in records if r.get("username", "").strip().lower() != target_user]
    # Add new favorites for this user
    now_str = datetime.now().strftime("%d %b %Y, %H:%M IST")
    for pid in sorted(list(fav_set)):
        kept_records.append({
            "parcel_id": str(pid),
            "username": username.strip() if username and username.strip() else "VPT",
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
    - If username is None or 'All Users': removes all favorites for this parcel across all users.
    """
    pid = str(parcel_id)
    records = load_raw_favorites()
    if username and username not in ("All Users", "All"):
        clean_user = username.strip().lower()
        if clean_user in ("untagged", "general", "general / untagged"):
            new_records = [
                r for r in records
                if not (r.get("parcel_id") == pid and r.get("username", "").strip().lower() in ("untagged", "general", "general / untagged", ""))
            ]
        else:
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
    - If username is None or 'All Users' or 'All' or '': checks if favorited by ANY user (including untagged).
    - If username is 'Untagged': checks if favorited without a user tag.
    - If username is a string: checks if favorited by that user.
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
        if clean_user in ("untagged", "general", "general / untagged"):
            return any(
                r.get("parcel_id") == pid and r.get("username", "").strip().lower() in ("untagged", "general", "general / untagged", "")
                for r in records
            )
        return any(r.get("parcel_id") == pid and r.get("username", "").strip().lower() == clean_user for r in records)

    return False


def get_users_for_parcel(parcel_id: str, raw_records: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Returns list of usernames who have favorited the specified parcel."""
    pid = str(parcel_id)
    records = raw_records if raw_records is not None else load_raw_favorites()
    users = []
    seen = set()
    for r in records:
        if str(r.get("parcel_id") or r.get("id")) == pid:
            raw_u = r.get("username")
            u = str(raw_u).strip() if raw_u and str(raw_u).strip() else "Untagged"
            if u.lower() not in seen:
                seen.add(u.lower())
                users.append(u)
    return users


def get_all_active_usernames(raw_records: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """
    Returns list of all active usernames, starting with the defaults:
    VPT, PPT, Guest-1, guest-2, followed by any custom or untagged usernames in records.
    """
    records = raw_records if raw_records is not None else load_raw_favorites()
    names = list(DEFAULT_USERNAMES)
    seen = {n.lower() for n in names}
    for r in records:
        raw_u = r.get("username")
        u = str(raw_u).strip() if raw_u and str(raw_u).strip() else ""
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
