"""Map what Kodi is playing back to a Jellyfin id."""

import os
import re
from typing import Any, Optional

import xbmcgui

from kofin.core.log import Logger

LOG = Logger(__name__)

JsonDict = dict[str, Any]


def library_video_path(jellyfin_id: str, media: str) -> Optional[str]:
    """The resolver URL Kodi filed a synced video item under, when it has one.

    A Play Next started with it matches ``ListItem.IsPlaying`` on the browsing
    row; another URL will play, but will not match.
    """
    if media not in ("movie", "episode", "musicvideo"):
        return None
    from kofin.sync.backends.api.identity import library_url

    try:
        url = library_url(jellyfin_id)
        return str(url) if url else None
    except Exception:
        LOG.exception("library path unavailable for %s", jellyfin_id)
        return None


# A song played from a saved playlist is a bare ``musicdb://songs/<id><ext>``
# line: nothing ever loads its music tag, so Kodi announces the playback
# without a database id. The id is still in the path, which is the only thing
# that identifies the row.
_MUSICDB_SONG = re.compile(r"^musicdb://songs/(\d+)")


def downloaded_path(path: str) -> bool:
    """A local file under the downloads root."""
    if not path or "://" in path:
        return False
    try:
        from kofin.downloads import downloads_root

        root = os.path.abspath(downloads_root())
    except Exception:  # pragma: no cover - settings unavailable
        return False
    return os.path.abspath(path).startswith(root + os.sep)


def musicdb_song_id(path: str) -> Optional[int]:
    """The Kodi song id in a ``musicdb://songs/<id><ext>`` path, or None."""
    match = _MUSICDB_SONG.match(path or "")
    return int(match.group(1)) if match else None


def mapped_jellyfin_id(kodi_id: int, media: str) -> Optional[str]:
    """The Jellyfin id kofin synced a Kodi library row from, or None if the row
    is not ours (or the mapping database cannot be read)."""
    from kofin.sync.backends.api.identity import mapped_item

    try:
        value = mapped_item(kodi_id, media)
        return str(value) if value else None
    except Exception:
        LOG.exception("library identity unavailable")
        return None


# A Jellyfin id as it appears in whichever path Kodi is playing: the play
# route's direct stream ``<server>/Audio/<id>/stream.<ext>``, the plugin URL's
# ``…?id=<id>``, or a native song's ``…/music/<folder>/<id>.<ext>`` file
# (``paths.song_url``).
_ID_IN_PATH = re.compile(
    r"/Audio/([0-9a-f]{32})/|[?&]id=([0-9a-f]{32})\b"
    r"|/music/(?:singles/)?[0-9a-f]{32}/([0-9a-f]{32})\."
)


def path_item_id(path: str) -> Optional[str]:
    """The Jellyfin id one of kofin's own URLs names, or None."""
    match = _ID_IN_PATH.search(path or "")
    if match:
        return match.group(1) or match.group(2) or match.group(3)
    return None


def playing_jellyfin_id(item: xbmcgui.ListItem, path: str) -> Optional[str]:
    """The Jellyfin id of the song Kodi is playing, or None if it is not ours.

    Prefers the Kodi database id, which is authoritative and cannot collide
    with foreign playback; falls back to reading the id out of the path for
    songs played from kofin's browse listing, which never get a library row.

    A playlist line carries its database id in the path rather than the tag
    (see :func:`musicdb_song_id`), so that is tried as the library id before
    the path is read for a Jellyfin one.
    """
    try:
        kodi_id = item.getMusicInfoTag().getDbId()
    except Exception:  # pragma: no cover - defensive, tag may be absent
        kodi_id = 0

    if not (kodi_id and kodi_id > 0):
        kodi_id = musicdb_song_id(path) or 0

    if kodi_id and kodi_id > 0:
        mapped = mapped_jellyfin_id(kodi_id, "song")
        if mapped:
            return mapped

    return path_item_id(path)
