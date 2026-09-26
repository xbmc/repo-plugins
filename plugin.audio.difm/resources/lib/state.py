# -*- coding: utf-8 -*-
"""Small persistent state shared by the plugin and metadata service."""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import xbmc
import xbmcaddon
import xbmcvfs

ADDON_ID = "plugin.audio.difm"


def _state_path():
    """Return the playback-state path inside this add-on's profile."""
    addon = xbmcaddon.Addon(ADDON_ID)
    profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
    os.makedirs(profile, exist_ok=True)
    return Path(profile) / "playback_state.json"


@contextmanager
def _state_lock(timeout=1.0):
    """Serialize state writers using a kernel-managed POSIX file lock.

    The lock file may remain on disk, but the kernel releases the lock
    automatically when its process exits, including after an unexpected Kodi
    termination. This avoids stale-owner recovery races entirely.
    """
    path = _state_path()
    lock_path = path.with_suffix(".lock")

    # Older releases used a directory as the lock. A crash could leave that
    # directory behind permanently. Remove it once before switching to the
    # kernel-managed flock file used by current releases.
    if lock_path.is_dir():
        try:
            shutil.rmtree(lock_path)
            xbmc.log(
                "[plugin.audio.difm] removed legacy playback-state lock directory",
                xbmc.LOGDEBUG,
            )
        except FileNotFoundError:
            pass
        except OSError as exc:
            if lock_path.is_dir():
                raise OSError(
                    f"Unable to remove legacy playback-state lock directory: {exc}"
                )

    deadline = time.monotonic() + timeout

    with open(lock_path, "a+", encoding="utf-8") as handle:
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        "Timed out waiting for playback-state lock"
                    )
                time.sleep(0.02)

        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_state():
    """Load playback state, returning an empty dict if unavailable."""
    try:
        path = _state_path()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.difm] unable to read playback state: {exc!r}",
            xbmc.LOGWARNING,
        )
    return {}


def save_state(data):
    """Persist playback state for the background Now Playing service."""
    try:
        path = _state_path()
        payload = dict(data or {})
        payload["updated_at"] = int(time.time())

        with _state_lock():
            _write_state_atomic(path, payload)

    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.difm] unable to save playback state: {exc!r}",
            xbmc.LOGWARNING,
        )


def clear_state():
    """Remove stale playback state."""
    try:
        path = _state_path()
        with _state_lock():
            if path.exists():
                path.unlink()
    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.difm] unable to clear playback state: {exc!r}",
            xbmc.LOGWARNING,
        )


def update_state_if_current(stream_url, channel_key, updates):
    """Update state only if it still belongs to the expected playback."""
    try:
        path = _state_path()

        with _state_lock():
            if not path.exists():
                return False

            data = json.loads(path.read_text(encoding="utf-8"))

            if not isinstance(data, dict):
                return False

            if (
                data.get("mode") != "linear"
                or data.get("stream_url") != stream_url
                or data.get("channel_key") != channel_key
            ):
                return False

            data.update(updates)
            data["updated_at"] = int(time.time())
            _write_state_atomic(path, data)

        return True

    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.difm] unable to update playback state: {exc!r}",
            xbmc.LOGWARNING,
        )
        return False


def _write_state_atomic(path, data):
    """Atomically replace the playback state file."""
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(data, handle, indent=2)
            temp_path = Path(handle.name)

        os.replace(temp_path, path)

        try:
            os.chmod(path, 0o600)
        except Exception as exc:
            xbmc.log(
                "[plugin.audio.difm] unable to restrict playback state "
                f"permissions: {exc!r}",
                xbmc.LOGWARNING,
            )

    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
