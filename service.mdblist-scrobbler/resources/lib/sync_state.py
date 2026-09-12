import json
import os
import threading

import xbmcaddon
import xbmcvfs


_lock = threading.Lock()


def _addon():
    return xbmcaddon.Addon()


def _state_path():
    profile = xbmcvfs.translatePath(_addon().getAddonInfo("profile"))
    return os.path.join(profile, "sync_state.json")


def _load():
    try:
        with open(_state_path(), "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write(data):
    path = _state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Write to a temp file then atomically replace -- a reader never sees a
    # partially-written file, even one that doesn't hold _lock (this module's
    # own lock only protects callers within this process; NotifyAll-based
    # "Sync now" keeps every writer in this same process -- see script.py).
    tmp_path = path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, path)


def _update(mutate):
    """Load, apply mutate(data) in place, write -- the whole cycle under one
    lock. Every setter below used to do load-mutate-write independently,
    which let concurrent callers (the periodic timers, the live
    VideoLibrary.OnUpdate listener, and the rating-prompt flow) clobber each
    other's known_items patches -- confirmed bug, fixed by making this the
    only place that touches the file."""
    with _lock:
        data = _load()
        mutate(data)
        _write(data)


def get_synced_at(category: str):
    with _lock:
        return _load().get(category, {}).get("synced_at")


def set_synced_at(category: str, timestamp: str):
    def mutate(data):
        data.setdefault(category, {})["synced_at"] = timestamp
    _update(mutate)


def get_known_items(category: str):
    """Returns {key: identity_dict} for the last-pushed state of a category.
    Storing the identity (not just the key) means a removal payload can still
    be built even after the item has left the Kodi library snapshot entirely
    (e.g. the file was deleted, not just marked unwatched)."""
    with _lock:
        items = _load().get(category, {}).get("known_items")
        return items if isinstance(items, dict) else {}


def merge_known_items(category: str, upserts: dict, removed_keys=None):
    """Merges a batch of upserts and removals into a category's known_items
    map in one disk round trip -- used to persist push progress
    chunk-by-chunk rather than only once at the very end of a whole
    category's diff. That way, if a later chunk aborts the run (e.g. a rate
    limit that survives its retry budget), the chunks that already pushed
    successfully are not forgotten and re-pushed from scratch on the next
    attempt. A single-item live push (see push_single in watched_sync.py /
    ratings_sync.py) is just the one-item case of the same call."""
    def mutate(data):
        bucket = data.setdefault(category, {}).setdefault("known_items", {})
        for key, value in (upserts or {}).items():
            bucket[key] = value
        for key in (removed_keys or []):
            bucket.pop(key, None)
    _update(mutate)


def get_last_activities_seen():
    with _lock:
        activities = _load().get("last_activities_seen")
        return activities if isinstance(activities, dict) else {}


def set_last_activities_seen(activities: dict):
    def mutate(data):
        data["last_activities_seen"] = activities
    _update(mutate)


def get_last_sync_summary():
    with _lock:
        return _load().get("last_run")


def set_last_sync_summary(summary: dict):
    def mutate(data):
        data["last_run"] = summary
    _update(mutate)


def reset_all():
    """Wipes all persisted sync state (cursors, known_items, the
    last_activities_seen watermark, and the last-run summary) -- port of
    jellyfin-plugin-mdblist's SyncStateStore.ResetUserAsync, adapted: Kodi
    is single-profile/single-account, so there's no per-user scoping to
    remove here, just the whole file's sync state. Migration markers are
    left alone -- they're one-time-setup completion flags, unrelated to
    which MDBList account is linked. Called on disconnect so a later
    reconnect (same or a different MDBList account) starts from a clean
    full resync instead of diffing/pulling against the previous account's
    leftover baseline."""
    def mutate(data):
        for category in ("watched", "ratings", "collection"):
            data.pop(category, None)
        data.pop("last_activities_seen", None)
        data.pop("last_run", None)
    _update(mutate)


def get_migration_done(name: str):
    with _lock:
        done = _load().get("migrations")
        return isinstance(done, list) and name in done


def set_migration_done(name: str):
    def mutate(data):
        migrations = data.setdefault("migrations", [])
        if name not in migrations:
            migrations.append(name)
    _update(mutate)
