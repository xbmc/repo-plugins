"""The addon backdrop: the server's splashscreen, or the bundled artwork.

``addon.xml`` names ``resources/media/fanart.jpeg`` as the addon's fanart, and
that file is never rewritten: Kodi keys cached textures on the source URL, so
an asset rewritten in place would keep rendering the old bytes. The server's
splashscreen goes to addon_data under a name that is its content hash
(``fanart-<sha256>.webp``), and :func:`profile_path` hands the current one to
the listings (``browse.with_backdrop``), which fall back to the bundled file
while the setting is off or nothing has been fetched yet. A new image is a new
URL, so no cache needs invalidating.

* **A daily floor gates the fetch.** ``_connect`` runs on every service start
  and every reconnect, and the splashscreen endpoint serves no ETag or
  Last-Modified, so there is no conditional GET to make.
* **The write is atomic.** Kodi may be reading the file to cache it; a
  partial write would cache a truncated image under a name that says it is
  complete.
* **Only the current image is kept.** No write replaces an earlier image, so
  once the state names a new one every other, and any write cut short, is
  deleted.

:meth:`Api.splashscreen` records why the image is taken as WebP.
"""

import hashlib
import json
import os
import re
from typing import Optional

from kofin.core import settings
from kofin.core.api import Api
from kofin.core.log import Logger

LOG = Logger(__name__)

# Records the hash of the splashscreen last fetched and when, so the daily
# floor holds across service restarts. In addon_data rather than a hidden
# setting: an open settings dialog discards external setting writes on
# Cancel, and this is written from a worker thread at arbitrary times.
STATE_NAME = "backdrop.json"

# Floor between fetches. The splashscreen is a collage the server rebuilds as
# the library changes, so it does move — just never faster than this matters.
REFRESH_INTERVAL_SECONDS = 24 * 60 * 60

# A server backdrop in addon_data, or a write of one cut short.
IMAGE_NAME = re.compile(r"fanart-[0-9a-f]{64}\.webp(\.part)?")


def _state_path() -> str:
    return os.path.join(settings.addon_data_path(), STATE_NAME)


def _read_state() -> dict:
    try:
        with open(_state_path(), encoding="utf-8") as handle:
            state: dict = json.load(handle)
            return state
    except (OSError, ValueError):
        return {}


def _write_state(fetched: float) -> None:
    payload = {"fetched": fetched}
    try:
        directory = settings.addon_data_path()
        if not os.path.isdir(directory):
            os.makedirs(directory)
        with open(_state_path(), "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
    except OSError as error:
        # Only costs a redundant fetch/write next time round.
        LOG.warning("backdrop state not written: %s", error)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply(api: Optional[Api], now: float, force: bool = False) -> None:
    """Bring the live asset in line with the setting. Never raises.

    ``force`` skips the daily floor; it is what the settings toggle uses, so
    switching the option on acts immediately rather than at the next connect.
    """
    try:
        _apply_profile(api, now, force)
    except Exception:
        LOG.exception("backdrop update failed")


def profile_path() -> str:
    """Current dynamic-listing fanart; the installed manifest asset stays fixed."""
    if not settings.get_bool("useServerBackdrop"):
        return ""
    digest = str(_read_state().get("profile_hash") or "")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        return ""
    path = os.path.join(settings.addon_data_path(), "fanart-" + digest + ".webp")
    return path if os.path.isfile(path) else ""


def _apply_profile(api: Optional[Api], now: float, force: bool) -> None:
    if api is None or not settings.get_bool("useServerBackdrop"):
        return
    previous = _read_state()
    if (
        not force
        and profile_path()
        and now - float(previous.get("fetched") or 0) < REFRESH_INTERVAL_SECONDS
    ):
        return
    if not api.branding_configuration().get("SplashscreenEnabled"):
        _write_state(now)
        return
    data = api.splashscreen()
    if not data:
        return
    directory = settings.addon_data_path()
    os.makedirs(directory, exist_ok=True)
    digest = _digest(data)
    target = os.path.join(directory, "fanart-" + digest + ".webp")
    with open(target + ".part", "wb") as handle:
        handle.write(data)
    os.replace(target + ".part", target)
    state_path = _state_path()
    with open(state_path + ".part", "w", encoding="utf-8") as handle:
        json.dump({"profile_hash": digest, "fetched": now}, handle)
    os.replace(state_path + ".part", state_path)
    _remove_others(directory, os.path.basename(target))


def _remove_others(directory: str, keep: str) -> None:
    for name in os.listdir(directory):
        if name == keep or not IMAGE_NAME.fullmatch(name):
            continue
        try:
            os.remove(os.path.join(directory, name))
        except OSError as error:
            LOG.debug("old backdrop %s not removed: %s", name, error)
