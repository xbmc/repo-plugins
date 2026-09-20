# -*- coding: utf-8 -*-
"""Small persistent state shared by the plugin and metadata service."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import xbmc
import xbmcaddon
import xbmcvfs
import tempfile
import uuid
from contextlib import contextmanager

ADDON_ID = "plugin.audio.jazzradio"


def _state_path():
    """Return the playback-state path inside this add-on's profile."""
    addon = xbmcaddon.Addon(ADDON_ID)
    profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
    os.makedirs(profile, exist_ok=True)
    return Path(profile) / "playback_state.json"

_LOCK_STALE_AFTER = 30.0


def _pid_is_running(pid):
    """Return False only when the recorded lock owner is known to be gone."""
    if not isinstance(pid, int) or pid <= 0:
        return False
    if pid == os.getpid():
        return True

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        # On platforms where probing another PID is not reliable, avoid
        # deleting a potentially live lock solely on that basis.
        return True
    return True


def _lock_owner(lock_path):
    """Read lock-owner metadata, returning an empty dict if unavailable."""
    try:
        data = json.loads(
            (lock_path / "owner.json").read_text(encoding="utf-8")
        )
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _lock_is_stale(lock_path):
    """Whether an abandoned playback-state lock can safely be recovered."""
    owner = _lock_owner(lock_path)

    try:
        pid = int(owner.get("pid", 0))
    except (TypeError, ValueError):
        pid = 0

    if pid and not _pid_is_running(pid):
        return True

    try:
        created_at = float(owner.get("created_at", 0))
    except (TypeError, ValueError):
        created_at = 0

    try:
        reference_time = created_at or lock_path.stat().st_mtime
    except OSError:
        return False

    return time.time() - reference_time > _LOCK_STALE_AFTER


def _remove_lock(lock_path, token=None):
    """Remove a lock, optionally only when it is still owned by token."""
    if token is not None:
        owner = _lock_owner(lock_path)
        if owner.get("token") != token:
            return False

    try:
        (lock_path / "owner.json").unlink()
    except FileNotFoundError:
        pass

    try:
        lock_path.rmdir()
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


@contextmanager
def _state_lock(timeout=1.0):
    """Serialize state writers and recover locks left by terminated owners."""
    path = _state_path()
    lock_path = path.with_suffix(".lock")
    deadline = time.monotonic() + timeout
    token = uuid.uuid4().hex

    while True:
        try:
            lock_path.mkdir()
            try:
                (lock_path / "owner.json").write_text(
                    json.dumps(
                        {
                            "pid": os.getpid(),
                            "created_at": time.time(),
                            "token": token,
                        }
                    ),
                    encoding="utf-8",
                )
            except Exception:
                _remove_lock(lock_path)
                raise
            break
        except FileExistsError:
            if _lock_is_stale(lock_path):
                if _remove_lock(lock_path):
                    xbmc.log(
                        "[plugin.audio.jazzradio] recovered stale "
                        "playback-state lock",
                        xbmc.LOGWARNING,
                    )
                    continue

            if time.monotonic() >= deadline:
                raise TimeoutError("Timed out waiting for playback-state lock")
            time.sleep(0.02)

    try:
        yield
    finally:
        _remove_lock(lock_path, token=token)

def load_state():
    """Load playback state, returning an empty dict if unavailable."""
    try:
        path = _state_path()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.jazzradio] unable to read playback state: {exc!r}",
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
            f"[plugin.audio.jazzradio] unable to save playback state: {exc!r}",
            xbmc.LOGWARNING,
        )


def clear_state():
    """Remove stale playback state."""
    try:
        path = _state_path()
        if path.exists():
            path.unlink()
    except Exception as exc:
        xbmc.log(
            f"[plugin.audio.jazzradio] unable to clear playback state: {exc!r}",
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
            f"[plugin.audio.jazzradio] unable to update playback state: {exc!r}",
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
                "[plugin.audio.jazzradio] unable to restrict playback state "
                f"permissions: {exc!r}",
                xbmc.LOGWARNING,
            )

    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
