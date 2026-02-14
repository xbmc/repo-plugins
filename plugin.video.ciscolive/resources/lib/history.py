"""
Watch history tracking for Cisco Live Kodi plugin.

Stores recently played sessions locally in the addon profile directory.
Max 100 entries, auto-prunes oldest when exceeded.
"""

import json
import os
import time

try:
    import xbmcaddon
    import xbmcvfs
    _ADDON = xbmcaddon.Addon()
    HISTORY_DIR = xbmcvfs.translatePath(_ADDON.getAddonInfo("profile"))
except Exception:
    HISTORY_DIR = os.path.join(os.path.dirname(__file__), ".profile")

HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
MAX_ENTRIES = 100


def _load():
    """Load history from disk."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _save(entries):
    """Save history to disk."""
    os.makedirs(HISTORY_DIR, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    except Exception:
        pass


def add(session_id, title="", video_id="", code="", event=""):
    """Record that a session was played."""
    entries = _load()

    # Remove existing entry for this session (we'll re-add at top)
    entries = [e for e in entries if e.get("session_id") != session_id]

    entry = {
        "session_id": session_id,
        "title": title,
        "video_id": video_id,
        "code": code,
        "event": event,
        "timestamp": time.time(),
    }
    entries.insert(0, entry)

    # Prune to max size
    entries = entries[:MAX_ENTRIES]
    _save(entries)


def get_recent(limit=50):
    """Get recently played sessions, newest first."""
    entries = _load()
    return entries[:limit]


def clear():
    """Clear all watch history."""
    _save([])
