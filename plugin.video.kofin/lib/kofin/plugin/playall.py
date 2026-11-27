"""Play all / Shuffle for a music container (mode=playall).

Kodi has no play for a plugin *folder* — ``VIDEO_UTILS::IsItemPlayable`` and
``MUSIC_UTILS::IsItemPlayable`` both stop at ``IsPlugin()`` for folders — so
this route expands an album, artist, genre or playlist server-side, in the
order the container deserves, and hands Kodi a music playlist of plugin
items. Each entry still resolves through ``mode=play``, so reporting,
downloads-first and the stream menu apply per track exactly as they do for a
track Kodi queued itself.

Music only, by decision: seasons and series keep Kodi's own behaviour.
"""

import random
from typing import Any, Optional

import xbmc

from kofin.core import ipc, settings, state, toast
from kofin.core.api import Api, paged
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin import listitems
from kofin.plugin.context import stop_current_playback
from kofin.plugin import feedback
from kofin.plugin.router import Request

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# What a queue may hold. Past this a "play all" is a library dump, and the
# plugin process builds a ListItem per row before anything plays.
QUEUE_LIMIT = 500

# The order each container deserves. An album by disc and track; an artist by
# year, then album, then disc and track; a genre by album artist first so the
# albums come out whole. A playlist keeps the server's order (below).
TRACK_ORDER = "ParentIndexNumber,IndexNumber,SortName"
SORT_BY = {
    "MusicAlbum": TRACK_ORDER,
    "MusicArtist": "ProductionYear,Album," + TRACK_ORDER,
    "MusicGenre": "AlbumArtist,Album," + TRACK_ORDER,
}

# What listitems._fill_music reads beyond the fields every DTO carries. The
# queue is built from these rows before the first note, so the payload is the
# wait.
TRACK_FIELDS = "Genres"

# Playlist pages: the server's own maximum is larger, but a page is also the
# unit a half-finished expansion can stop at.
PAGE_SIZE = 100


def _api() -> Optional[Api]:
    creds = Credentials.load()
    if not creds.is_logged_in:
        return None
    return Api.for_plugin(creds)


def expand(api: Api, item: JsonDict, shuffle: bool) -> list[JsonDict]:
    """The tracks under a container, in playing order; [] for anything else."""
    return expand_counted(api, item, shuffle)[0]


def expand_counted(
    api: Api, item: JsonDict, shuffle: bool
) -> tuple[list[JsonDict], int]:
    """The tracks under a container, in playing order, and how many the
    container holds: more than were taken when the queue bound cut the
    listing. ([], 0) for anything else."""
    item_type = item.get("Type", "")
    item_id = item.get("Id", "")
    if item_type == "Playlist":
        return _playlist_tracks(api, item_id, shuffle)
    if item_type not in SORT_BY:
        LOG.warning("play all: %s is a %s, which has no tracks", item_id, item_type)
        return [], 0

    query: JsonDict = {
        # Songs alone. Jellyfin keeps an AudioBook in a books library, under
        # no album; one that names an artist or a genre is a book, not that
        # artist's or genre's music. A playlist plays what it holds.
        "IncludeItemTypes": "Audio",
        "Recursive": True,
        "Fields": TRACK_FIELDS,
        "ImageTypeLimit": 1,
        "Limit": QUEUE_LIMIT,
        "EnableTotalRecordCount": True,
        "SortBy": "Random" if shuffle else SORT_BY[item_type],
    }
    if item_type == "MusicArtist":
        # ArtistIds, not ParentId (actions._expand_downloadable says why).
        query["ArtistIds"] = item_id
    elif item_type == "MusicGenre":
        query["GenreIds"] = item_id
    else:
        query["ParentId"] = item_id

    body = api.items(query)
    rows = list(body.get("Items") or [])
    total = int(body.get("TotalRecordCount") or 0)
    if total > len(rows):
        LOG.debug(
            "play all: %s holds %d tracks; queuing the first %d",
            item_id,
            total,
            len(rows),
        )
    return rows, max(total, len(rows))


def _playlist_tracks(
    api: Api, playlist_id: str, shuffle: bool
) -> tuple[list[JsonDict], int]:
    """A playlist's audio entries in the server's order, shuffled here if
    asked: the playlist route has no SortBy, and the order is the playlist.
    Cut at the queue bound, the count is what the playlist holds."""
    tracks: list[JsonDict] = []
    seen = 0
    cut = False
    for row in paged(
        lambda start, limit: api.playlist_items(
            playlist_id, start_index=start, limit=limit, fields=TRACK_FIELDS
        ),
        PAGE_SIZE,
        dedupe=False,
        what="playlist %s" % playlist_id,
    ):
        seen += 1
        if row.get("Type") in listitems.AUDIO_TYPES:
            tracks.append(row)
        if len(tracks) >= QUEUE_LIMIT:
            cut = True
            break
    total = len(tracks)
    if cut:
        body = api.playlist_items(playlist_id, start_index=0, limit=1, fields="")
        total = max(int(body.get("TotalRecordCount") or 0), seen)
    if shuffle:
        random.shuffle(tracks)
    return tracks, total


def queue_and_play(tracks: list[JsonDict], server: str) -> None:
    """Hand Kodi a music playlist of the tracks and start it.

    An explicit *music* playlist: the queue Kodi builds for a kofin listing
    itself lands on the video playlist, because ``<provides>video audio
    </provides>`` makes ``CGUIViewStateFromItems`` pick video last. Playback
    is stopped first (context.stop_current_playback).

    The service starts the queue (ipc.START_QUEUE). Kodi resolves the first
    track with a plugin request of its own, and gives it the interpreter it
    keeps warm only once this script has ended; ``Player().play`` returns
    only after that resolve, so a start from here gets a cold interpreter.

    The request goes before the tracks, because every track added is a
    ``Playlist.OnAdd`` announcement for every Python monitor in Kodi. Sent
    first, through JSON-RPC (ipc.notify_now) so that it is announced before
    the first add, it carries the count, and the service waits for the queue
    to hold that many. When Kodi refuses it the queue is started here.
    """
    stop_current_playback()
    owner = state.take_queue()
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    asked = ipc.notify_now(ipc.START_QUEUE, {"Count": len(tracks), "Owner": owner})
    for track in tracks:
        if not state.owns_queue(owner):
            # A newer Play all cleared the playlist and is filling it.
            LOG.debug("play all: a newer request took the queue")
            return
        playlist.add(listitems.path_for(track), listitems.build(track, server))
    if not asked:
        LOG.warning("play all: the service was not asked; starting the queue here")
        xbmc.Player().play(playlist)


def play_all(request: Request) -> None:
    item_id = request.params.get("id", "")
    shuffle = request.params.get("shuffle") == "1"
    if not item_id:
        return
    api = _api()
    if api is None:
        return
    try:
        item = api.item(item_id)
        tracks, total = expand_counted(api, item, shuffle)
    except JellyfinError as error:
        LOG.warning("play all failed for %s: %s", item_id, error)
        feedback.failed(error)
        return
    if not tracks:
        LOG.debug("play all: nothing playable under %s", item_id)
        return
    LOG.debug(
        "play all: %d tracks under %s (%s)",
        len(tracks),
        item_id,
        "shuffled" if shuffle else "in order",
    )
    queue_and_play(tracks, api.server)
    if total > len(tracks):
        # The bound cut the listing: the viewer is told what was queued of
        # what there is, in the words Kodi uses for the count.
        toast.show(
            settings.localized(30897) % (len(tracks), total), toast.INFO, time_ms=5000
        )
