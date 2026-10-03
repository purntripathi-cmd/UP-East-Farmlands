"""
Property Flags & Moderation Manager
Handles user moderation actions:
- Flagging properties as "Fake Listing" (fraudulent, non-existent, deceptive)
- Adding properties to "Ignore List" (dismissed from active views)
- Restoring / unflagging properties
- Disk persistence in data/property_flags.json
"""

import os
import json
import datetime
from typing import Dict, Any, List, Set, Optional, Tuple


def get_flags_file_path() -> str:
    """Returns absolute path to property_flags.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "property_flags.json")


def load_property_flags() -> Dict[str, Dict[str, Any]]:
    """Loads all property flags from persistent JSON storage."""
    file_path = get_flags_file_path()
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception:
            pass
    return {}


def save_property_flags(flags: Dict[str, Dict[str, Any]]) -> bool:
    """Persists property flags to disk."""
    file_path = get_flags_file_path()
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(flags, f, indent=2)
        return True
    except Exception:
        return False


def set_property_flag(parcel_id: str, flag: str, reason: str = "") -> bool:
    """
    Sets or updates flag for a parcel ('fake' or 'ignored').
    """
    if flag not in ("fake", "ignored"):
        raise ValueError("flag must be either 'fake' or 'ignored'")

    flags = load_property_flags()
    pid = str(parcel_id)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    flags[pid] = {
        "flag": flag,
        "timestamp": now_str,
        "reason": reason.strip() or ("Reported as Fake Listing" if flag == "fake" else "Added to Ignore List")
    }
    return save_property_flags(flags)


def remove_property_flag(parcel_id: str) -> bool:
    """Removes any flag from a parcel, restoring it to active inventory."""
    flags = load_property_flags()
    pid = str(parcel_id)
    if pid in flags:
        del flags[pid]
        return save_property_flags(flags)
    return False


def get_property_flag(parcel_id: str, flags_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """Returns flag info dict for parcel if flagged, else None."""
    flags = flags_dict if flags_dict is not None else load_property_flags()
    return flags.get(str(parcel_id))


def is_fake(parcel_id: str, flags_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
    """Returns True if property is marked as a fake listing."""
    info = get_property_flag(parcel_id, flags_dict)
    return info is not None and info.get("flag") == "fake"


def is_ignored(parcel_id: str, flags_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
    """Returns True if property is marked as ignored."""
    info = get_property_flag(parcel_id, flags_dict)
    return info is not None and info.get("flag") == "ignored"


def get_ignored_ids(flags_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> Set[str]:
    """Returns set of parcel IDs marked as ignored."""
    flags = flags_dict if flags_dict is not None else load_property_flags()
    return {pid for pid, v in flags.items() if v.get("flag") == "ignored"}


def get_fake_ids(flags_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> Set[str]:
    """Returns set of parcel IDs marked as fake listings."""
    flags = flags_dict if flags_dict is not None else load_property_flags()
    return {pid for pid, v in flags.items() if v.get("flag") == "fake"}


def filter_parcels_by_flag_status(
    parcels: List[Dict[str, Any]],
    show_ignored: bool = False,
    show_fake: bool = False,
    flags_dict: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Filters parcels based on whether user wants to see ignored or fake listings.
    By default (show_ignored=False, show_fake=False), returns only clean active parcels.
    """
    flags = flags_dict if flags_dict is not None else load_property_flags()
    clean_list = []
    for p in parcels:
        pid = str(p.get("id"))
        flag_info = flags.get(pid)
        if flag_info:
            flag_type = flag_info.get("flag")
            if flag_type == "ignored" and not show_ignored:
                continue
            if flag_type == "fake" and not show_fake:
                continue
        clean_list.append(p)
    return clean_list
