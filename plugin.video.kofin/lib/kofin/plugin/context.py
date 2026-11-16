"""Context-menu entry points (invoked with a focused ListItem)."""

import os
import re
import sys
from typing import Optional, Union

import xbmc
import xbmcgui
import xbmcvfs

from kofin.core import kodirpc, settings, state, toast
from kofin.core.api import Api
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.core.urls import PARAM_BITRATE, PARAM_TRANSCODE, plugin_url
from kofin.plugin.listitems import PLAYABLE_TYPES

LOG = Logger(__name__)

# How long to wait for the outgoing playback to stop. The ceiling only stops a
# wedged player from stranding the context item.
STOP_TIMEOUT_SECONDS = 3.0
STOP_POLL_SECONDS = 0.05


def _api() -> Api:
    return Api.for_plugin(Credentials.load())


def _focused_listitem() -> Optional[xbmcgui.ListItem]:
    return getattr(sys, "listitem", None)


def _focused_dynamic_id() -> str:
    """The Jellyfin id of the focused item when it is one kofin listed itself.

    Only kofin's own listings build their items, so only they carry the
    property: a synced library's rows are Kodi's, and reach their Jellyfin id
    through the database mapping instead. That makes this the test for "is this
    item from a dynamic library", which decides whether the watched toggle is
    worth offering.
    """
    listitem = _focused_listitem()
    if listitem is None:
        return ""
    return listitem.getProperty("kofin.id")


def _focused_item_id() -> str:
    item_id = _focused_dynamic_id()
    if item_id:
        return item_id
    node = re.fullmatch(
        r"library://music/kofin/kofinmusic([0-9a-fA-F]{32})/?",
        xbmc.getInfoLabel("ListItem.FileNameAndPath"),
    )
    if node:
        return node.group(1).lower()
    # Library items carry no kofin.id property; resolve the Kodi database id
    # through the kofin.db mapping instead.
    listitem = _focused_listitem()
    tag = listitem.getVideoInfoTag() if listitem is not None else None
    if tag is not None and tag.getDbId() > 0 and tag.getMediaType():
        return lookup_item_id(tag.getDbId(), tag.getMediaType())
    # A music-library row carries a music tag instead, which has a database
    # id but no media type — the infolabels of the focused item say which
    # table it came from (the same DBTYPE the addon.xml visibility tests).
    dbtype = xbmc.getInfoLabel("ListItem.DBTYPE")
    if dbtype in ("song", "album", "artist"):
        dbid = xbmc.getInfoLabel("ListItem.DBID")
        if dbid.isdigit():
            return lookup_item_id(int(dbid), dbtype)
    return ""


def lookup_item_id(dbid: int, media_type: str) -> str:
    """The Jellyfin item id for a Kodi library row, '' when not kofin's."""
    from kofin.service.libraryclaim import mapped_jellyfin_id

    return mapped_jellyfin_id(dbid, media_type) or ""


def _bitrate_value(value: str) -> Optional[float]:
    """Parse a context-bitrate token (Mbit/s, '0' == no override); None if junk."""
    try:
        parsed = float(value)
    except ValueError:
        return None
    return parsed if parsed >= 0 else None


def _bitrate_label(value: str) -> str:
    if _bitrate_value(value) == 0:
        return settings.localized(30206)  # Default (max streaming bitrate)
    return "%s Mbit/s" % value


def choose_bitrate(configured: list[str]) -> Optional[str]:
    """The bitrate token to transcode at; None means nothing to offer.

    A token of '0' overrides nothing: ``deviceprofile.build`` falls back to the
    max-streaming-bitrate setting, and only when that is unset too does the
    server size the transcode itself. With exactly one configured bitrate the
    dialog is skipped. No valid bitrate
    means no transcode: addon.xml hides the context item in that case, so
    falling back to an invented default would only surface a bitrate the user
    never chose.
    """
    valid = [value for value in configured if _bitrate_value(value) is not None]
    if not valid:
        return None
    if len(valid) == 1:
        return valid[0]
    labels: list[Union[str, xbmcgui.ListItem]] = [
        _bitrate_label(value) for value in valid
    ]
    index = xbmcgui.Dialog().select(settings.localized(30010), labels)
    return valid[index] if index >= 0 else None


def _focused_resume() -> tuple[str, float]:
    """(the ``dbid`` play param, the position that item would resume at).

    The two travel together so the prompt and the start agree: the dbid is
    handed on only where Kodi's bookmark is the answer
    (``play.resume_start_ticks``), and the seconds are read from whichever
    source that leaves in play.
    """
    listitem = _focused_listitem()
    tag = listitem.getVideoInfoTag() if listitem is not None else None
    if tag is None:
        return "", 0.0
    dbid, media = tag.getDbId(), tag.getMediaType()
    if dbid and dbid > 0 and media in kodirpc.RESUME_QUERY:
        return str(dbid), kodirpc.resume_seconds(dbid, media) or 0.0
    return "", max(tag.getResumeTime(), 0.0)


def _resume_label(seconds: float) -> str:
    """Kodi's "Resume from HH:MM:SS", stamped the way Kodi stamps it.

    ``SecondsToTimeString(..., TIME_FORMAT_HH_MM_SS)`` zero-pads all three
    fields. The string is a fmt template ("Resume from {0:s}") that a
    translation may write differently, so a substitution that does not take
    falls back to the bare time rather than to a label with braces in it.
    """
    whole = int(round(seconds))
    stamp = "%02d:%02d:%02d" % (whole // 3600, whole % 3600 // 60, whole % 60)
    try:
        return xbmc.getLocalizedString(12022).format(stamp)  # Resume from {0:s}
    except (IndexError, KeyError, ValueError):
        return stamp


def choose_resume(resume_seconds: float) -> Optional[bool]:
    """Whether to resume; None when the user backed out of the question.

    Kodi never asks it on this path: it prompts only for the playbacks it
    starts itself, and the transcode item starts its own. Same wording,
    options and order as ``CGUIWindowVideoBase::ShowResumeMenu``; nothing to
    ask means resume=False.
    """
    if resume_seconds <= 0:
        return False
    index = xbmcgui.Dialog().contextmenu(
        [
            _resume_label(resume_seconds),
            xbmc.getLocalizedString(12021),  # Play from beginning
        ]
    )
    if index < 0:
        return None
    return index == 0


def play_with_transcode() -> None:
    item_id = _focused_item_id()
    if not item_id:
        LOG.warning("transcode context invoked without a kofin item")
        return
    dbid, resume_seconds = _focused_resume()
    resume = choose_resume(resume_seconds)
    if resume is None:
        return
    bitrate = choose_bitrate(settings.get_list("contextBitrates"))
    if bitrate is None:
        return
    params: dict[str, str] = {
        "mode": "play",
        "id": item_id,
        PARAM_TRANSCODE: "1",
        PARAM_BITRATE: bitrate,
    }
    if dbid:
        params["dbid"] = dbid
    # The answer is stated outright, because Kodi will not carry it: PlayMedia's
    # own "resume" flag is gated on GetItemResumeInformation().isResumable, and
    # the bare plugin:// path it builds an item from has no resume information
    # to find ("LoadDetails: Unsupported item type"), so the flag downgrades
    # itself to noresume and the play route is handed resume:false either way.
    # A start position in the params owes Kodi nothing: the play route resolves
    # the stream at that offset and stamps it on the item Kodi then seeks.
    if resume:
        params["startticks"] = str(int(resume_seconds * 10_000_000))
    else:
        params["fromstart"] = "1"
    LOG.debug(
        "context transcode %s at %s Mbit/s (%s)",
        item_id,
        bitrate,
        "resume" if resume else "from start",
    )
    # PlayMedia, not RunPlugin: playback Kodi starts is resolved through
    # setResolvedUrl, the path every other kofin playback takes, and the one
    # whose resume point Kodi acts on.
    stop_current_playback()
    xbmc.executebuiltin("PlayMedia(%s)" % plugin_url(params))


def stop_current_playback() -> None:
    """Stop whatever is playing, and wait for it to be gone.

    ``PlayMedia`` on a bare ``plugin://`` path handed to Kodi while something
    else is still playing loses a race: the outgoing player's stop is queued to
    the application thread, which gets to it only *after* it has opened the
    new video player. Processing it then closes the player that just opened,
    and because the demuxer open is still in flight the play dies as
    "OpenDemuxStream - Error creating demuxer" rather than as a stop.

    Library playback does not go through ``PlayMedia`` -- Kodi opens the
    ``videodb://`` item and sequences the handover itself. Stopping here
    rather than inside Kodi's open also lets the service report the stop
    against the item it belongs to.
    """
    player = xbmc.Player()
    if not player.isPlaying():
        return
    kodirpc.stop_player()  # not player.stop()
    monitor = xbmc.Monitor()
    waited = 0.0
    while waited < STOP_TIMEOUT_SECONDS:
        if monitor.waitForAbort(STOP_POLL_SECONDS):
            return
        waited += STOP_POLL_SECONDS
        if not player.isPlaying():
            return
    LOG.warning("playback did not stop in %.1fs; starting anyway", waited)


# Anything playable, plus the containers Jellyfin tracks played state for.
WATCHED_TYPES = PLAYABLE_TYPES | {"Series", "Season", "BoxSet"}

# What a resume point can be reset on: the playable video kinds. Jellyfin
# keeps a position for songs only as audiobooks, and Kodi has nowhere to
# resume one (Api.resume says the same).
RESUMABLE_TYPES = PLAYABLE_TYPES - {"Audio", "AudioBook"}

# The containers Play all / Shuffle expand (plugin/playall.py). A Playlist
# joins when it is an audio one (``_plays_all``).
PLAY_ALL_TYPES = frozenset({"MusicAlbum", "MusicArtist", "MusicGenre"})


def _plays_all(item: dict) -> bool:
    item_type = item.get("Type")
    if item_type in PLAY_ALL_TYPES:
        return True
    return item_type == "Playlist" and item.get("MediaType") == "Audio"


# Containers expand to their downloadable leaves at the route.
DOWNLOADABLE_TYPES = frozenset(
    {
        "Movie",
        "Episode",
        "Season",
        "Series",
        "Audio",
        "MusicAlbum",
        "MusicArtist",
        "Playlist",
        "CollectionFolder",
        "UserView",
    }
)
DOWNLOAD_CONTAINER_TYPES = frozenset(
    {
        "Season",
        "Series",
        "MusicAlbum",
        "MusicArtist",
        "Playlist",
        "CollectionFolder",
        "UserView",
    }
)


def _container_download_options(
    item_id: str, music_scope: str = ""
) -> list[tuple[str, dict]]:
    """What a Season/Series/album/artist/playlist offers, from local state.

    Download stays unless everything under the container is already
    finished: a partly downloaded show is still worth completing, and
    knowing whether the *server* has more children than the store does would
    cost the very round trip this menu is built to avoid. So: Remove
    whenever something is downloaded, Cancel whenever something is in
    flight, Download unless the container is done and idle.
    """
    from kofin.downloads import store

    if music_scope:
        states = store.music_container_unclaimed_states(item_id, music_scope)
        counts = {
            "done": sum(state == store.DONE for state in states.values()),
            "pending": sum(
                state in (store.QUEUED, store.ACTIVE) for state in states.values()
            ),
        }
        unfinished = any(state != store.DONE for state in states.values())
    else:
        counts = store.container_counts(item_id)
        unfinished = bool(counts["pending"])
    params = {"id": item_id}
    if music_scope:
        params["playlist" if music_scope == "playlist" else "library"] = "1"
    entries: list[tuple[str, dict]] = []
    if unfinished or not counts["done"]:
        entries.append((settings.localized(30708), {"mode": "download", "id": item_id}))
    if counts["done"]:
        entries.append(
            (
                settings.localized(30710),
                {"mode": "removedownload", **params},
            )
        )
    if counts["pending"]:
        entries.append(
            (settings.localized(30709), {"mode": "canceldownload", **params})
        )
    return entries


def downloads_enabled() -> bool:
    """The downloads master toggle; False in a profile whose settings have
    no downloads section (getSettingBool raises on an undefined setting)."""
    try:
        return settings.get_bool("downloadsEnabled")
    except TypeError:
        return False


def _download_options(item: dict) -> list[tuple[str, dict]]:
    """Download / Cancel download / Remove download, from local state.

    Leaves gate on the server's ``CanDownload`` exactly as delete gates on
    ``CanDelete`` — never offer what the server will 403 (the field is false
    when the admin turned EnableContentDownloading off). Containers cannot
    carry the field (folders always answer false), so they never gate on it;
    the route's own filter drops children the server refuses.
    """
    item_type = item.get("Type")
    if item_type not in DOWNLOADABLE_TYPES:
        return []
    if (
        item_type in ("CollectionFolder", "UserView")
        and item.get("CollectionType") != "music"
    ):
        return []
    item_id = item.get("Id", "")
    if item_type in DOWNLOAD_CONTAINER_TYPES:
        from kofin.downloads import subscriptions

        music_scope = (
            "playlist"
            if item_type == "Playlist"
            else "musiclibrary" if item_type in ("CollectionFolder", "UserView") else ""
        )
        subscribed = bool(music_scope) and item_id in subscriptions.subscribed(
            subscriptions.PLAYLIST_SETTING
            if music_scope == "playlist"
            else subscriptions.LIBRARY_SETTING
        )
        entries = (
            [] if subscribed else _container_download_options(item_id, music_scope)
        )
        if item_type == "Series":
            # The new-episode subscription toggle, labeled by the show's
            # current state.
            from kofin.downloads import auto as downloads_auto

            subscribed = item_id in downloads_auto.subscribed_shows()
            entries.append(
                (
                    settings.localized(30761 if subscribed else 30760),
                    {
                        "mode": "downloadshow",
                        "id": item_id,
                        "name": item.get("Name", ""),
                    },
                )
            )
        if item_type in ("CollectionFolder", "UserView"):
            entries.append(
                (
                    settings.localized(30850 if subscribed else 30849),
                    {"mode": "downloadmusiclibrary", "id": item_id},
                )
            )
        return entries

    from kofin.downloads import store

    row = store.get(item_id)
    if row is None or row.state == store.FAILED:
        if not item.get("CanDownload"):
            return []
        return [(settings.localized(30708), {"mode": "download", "id": item_id})]
    if row.state == store.DONE:
        return [(settings.localized(30710), {"mode": "removedownload", "id": item_id})]
    return [(settings.localized(30709), {"mode": "canceldownload", "id": item_id})]


def _manage_options(item: dict, dynamic: bool) -> list[tuple[str, dict]]:
    """The (label, RunPlugin params) pairs for the Jellyfin actions menu.

    Every server-side action for an item lives here: a listing's own context
    entries are pinned to the very top of Kodi's menu, above its Play
    (``CGUIMediaWindow::OnPopupMenu`` builds plugin items, then the global
    menu, then window buttons, then addon extensions). Delete is offered only
    when the user has opted in on the Advanced tab; the watched and favorite
    labels reflect the server-reported state queried when the menu opened.

    ``dynamic`` says the item came from one of kofin's own listings rather than
    from a synced library, and only there is the watched toggle offered. A
    library row has Kodi's own "Mark as watched", which
    ``service/kodiuserdata.py`` forwards to Jellyfin — including the
    per-episode announcements a whole season fires.
    """
    item_id = item.get("Id", "")
    userdata = item.get("UserData") or {}
    is_favorite = bool(userdata.get("IsFavorite"))
    options: list[tuple[str, dict]] = []

    # Play all and Shuffle (plugin/playall.py) come first, because playing is
    # what the row is for. Core strings: 22083 "Play all", 191 "Shuffle".
    if _plays_all(item):
        options.append(
            (xbmc.getLocalizedString(22083), {"mode": "playall", "id": item_id})
        )
        options.append(
            (
                xbmc.getLocalizedString(191),
                {"mode": "playall", "id": item_id, "shuffle": "1"},
            )
        )

    if dynamic and item.get("Type") in WATCHED_TYPES:
        played = bool(userdata.get("Played"))
        options.append(
            (
                settings.localized(30509 if played else 30508),
                {"mode": "unwatched" if played else "watched", "id": item_id},
            )
        )

    # Kodi's own "Reset resume position" is what the viewer reaches first, and
    # on a listing row it does nothing that lasts: it deletes a MyVideos
    # bookmark the row does not have and never speaks to the server, so the
    # refresh it triggers stamps the server's position straight back. Offered
    # here under Kodi's own wording (38209), only where there is a position to
    # reset and only on kofin's rows — a library row's Kodi entry works, and
    # the service forwards it (kodiuserdata.py).
    if (
        dynamic
        and item.get("Type") in RESUMABLE_TYPES
        and int(userdata.get("PlaybackPositionTicks") or 0) > 0
    ):
        options.append(
            (xbmc.getLocalizedString(38209), {"mode": "resetresume", "id": item_id})
        )

    fav_label = xbmc.getLocalizedString(14077 if is_favorite else 14076)
    fav_mode = "unfavorite" if is_favorite else "favorite"
    options.append((fav_label, {"mode": fav_mode, "id": item_id}))

    # Extras belongs here rather than in its own context item: a context item's
    # <visible> can only ask Kodi, and ListItem.HasVideoExtras is movie-only
    # (hasVideoExtras is computed in movie_view; tvshow_view has no such
    # column), so it reads false for every show, and a library row carries no
    # addon-settable property to stand in.
    if item.get("SpecialFeatureCount"):
        options.append((settings.localized(30501), {"mode": "extras", "id": item_id}))

    if downloads_enabled():
        options.extend(_download_options(item))

    # Two gates: the setting is whether the *user* wants deletion offered at
    # all, CanDelete is whether the *server* would allow it. The item manage()
    # fetched carries CanDelete without a Fields request.
    if settings.get_bool("enableDelete") and item.get("CanDelete"):
        options.append(
            (
                xbmc.getLocalizedString(117),  # Delete
                {"mode": "delete", "id": item_id, "name": item.get("Name", "")},
            )
        )

    options.append((settings.localized(30504), {"mode": "settings"}))
    return options


def _offline_menu(item_id: str) -> None:
    """The Jellyfin actions menu built from local state alone.

    Only what does not need the server: removing a download, and the
    settings shortcut. The server-side actions are deliberately absent
    rather than queued — a menu action that silently waits for a
    reconnection is worse than one that is simply not offered.
    """
    options: list[tuple[str, dict]] = []
    if downloads_enabled():
        from kofin.downloads import store

        row = store.get(item_id)
        if row is not None and row.state == store.DONE:
            options.append(
                (
                    settings.localized(30710),
                    {"mode": "removedownload", "id": item_id},
                )
            )
        elif row is not None:
            options.append(
                (settings.localized(30709), {"mode": "canceldownload", "id": item_id})
            )
        else:
            # No row of its own: it may still be a container holding some,
            # which the store answers without the server.
            options.extend(
                entry
                for entry in _container_download_options(item_id)
                if entry[1]["mode"] != "download"  # queueing needs the server
            )
    options.append((settings.localized(30504), {"mode": "settings"}))

    index = xbmcgui.Dialog().contextmenu([label for label, _ in options])
    if index < 0:
        return
    _, params = options[index]
    xbmc.executebuiltin("RunPlugin(%s)" % plugin_url(params))


def save_playlist() -> None:
    """Context entry: save the focused basic playlist file to Jellyfin."""
    path = xbmc.getInfoLabel("ListItem.FileNameAndPath")
    xbmc.executebuiltin(
        "RunPlugin(%s)" % plugin_url({"mode": "saveplaylist", "path": path})
    )


def manage_download_playlist() -> None:
    """Download actions for one file in the managed music playlist folder."""
    from kofin.downloads import store, subscriptions
    from kofin.sync import playlists
    from kofin.sync import kofindb
    from kofin.sync.private import Database

    path = xbmc.getInfoLabel("ListItem.FileNameAndPath")
    directory = os.path.realpath(playlists.managed_dir())
    candidate = os.path.realpath(xbmcvfs.translatePath(path))
    if os.path.dirname(candidate) != directory or not candidate.endswith(".m3u8"):
        return
    filename = os.path.basename(candidate)
    with Database("kofin") as opened:
        tables = kofindb.JellyfinDatabase(opened.cursor)
        playlist_id = tables.playlist_for_file(filename, side="Audio")
    if not playlist_id:
        return
    enabled = playlist_id in subscriptions.subscribed(subscriptions.PLAYLIST_SETTING)
    states = list(store.playlist_unclaimed_states(playlist_id).values())
    entries: list[tuple[str, dict]] = []
    if not enabled and (not states or any(state != store.DONE for state in states)):
        entries.append(
            (settings.localized(30708), {"mode": "download", "id": playlist_id})
        )
    if not enabled and store.DONE in states:
        entries.append(
            (
                settings.localized(30710),
                {"mode": "removedownload", "id": playlist_id, "playlist": "1"},
            )
        )
    if not enabled and any(state in (store.QUEUED, store.ACTIVE) for state in states):
        entries.append(
            (
                settings.localized(30709),
                {"mode": "canceldownload", "id": playlist_id, "playlist": "1"},
            )
        )
    entries.append(
        (
            settings.localized(30850 if enabled else 30849),
            {"mode": "downloadplaylist", "id": playlist_id},
        )
    )
    index = xbmcgui.Dialog().contextmenu([label for label, _ in entries])
    if index >= 0:
        xbmc.executebuiltin("RunPlugin(%s)" % plugin_url(entries[index][1]))


def manage() -> None:
    """Open the "Jellyfin actions" menu for the focused kofin item."""
    item_id = _focused_item_id()
    if not item_id:
        LOG.warning("jellyfin actions invoked without a kofin item")
        return

    if state.is_offline():
        # Offline the fetch below is a doomed wait, and the actions it
        # unlocks are all server writes. What still works locally is the
        # download the user already has.
        _offline_menu(item_id)
        return

    try:
        item = _api().item(item_id)
    except JellyfinError as error:
        LOG.warning("manage: item fetch failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return

    options = _manage_options(item, dynamic=bool(_focused_dynamic_id()))
    index = xbmcgui.Dialog().contextmenu([label for label, _ in options])
    if index < 0:
        return

    _, params = options[index]
    LOG.debug("manage: %s for %s", params.get("mode"), item_id)
    if params.get("mode") == "extras":
        # The one entry here that goes somewhere rather than doing something.
        # RunPlugin would execute the listing and throw it away.
        xbmc.executebuiltin("ActivateWindow(Videos,%s,return)" % plugin_url(params))
        return
    xbmc.executebuiltin("RunPlugin(%s)" % plugin_url(params))
