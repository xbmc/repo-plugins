"""Small RunPlugin actions: watched/favorite toggles, settings, library
maintenance buttons (Library tab -> IPC -> service library manager)."""

from typing import Any, Optional, Union

import xbmc
import xbmcgui

from kofin.core import ipc, kodirpc, settings, toast
from kofin.core.api import Api, paged
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin.listitems import play_path
from kofin.plugin import feedback
from kofin.plugin.router import Request

LOG = Logger(__name__)


def _api() -> Api:
    return Api.for_plugin(Credentials.load())


def _refresh() -> None:
    xbmc.executebuiltin("Container.Refresh")


def watched(request: Request) -> None:
    item_id = request.params.get("id", "")
    try:
        _api().mark_played(item_id)
    except JellyfinError as error:
        LOG.warning("mark played failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    _refresh()


def unwatched(request: Request) -> None:
    item_id = request.params.get("id", "")
    try:
        _api().mark_unplayed(item_id)
    except JellyfinError as error:
        LOG.warning("mark unplayed failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    _refresh()


def reset_resume(request: Request) -> None:
    """Zero an item's resume point on the server, then Kodi's own copy.

    The server half is the call the service makes when Kodi resets a library
    row. The local half is the bookmark Kodi keeps for the row's plugin path:
    once kofin stops stamping a position, Kodi falls back to that bookmark
    and would resurrect the very resume the viewer just removed
    (kodirpc.clear_resume_bookmark). Server first — if that fails nothing
    local is touched, and the listing keeps telling the truth.
    """
    item_id = request.params.get("id", "")
    if not item_id:
        return
    try:
        _api().set_resume_position(item_id, 0)
    except JellyfinError as error:
        LOG.warning("resume reset failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    kodirpc.clear_resume_bookmark(play_path(item_id))
    _refresh()


def favorite(request: Request) -> None:
    _set_favorite(request, True)


def unfavorite(request: Request) -> None:
    _set_favorite(request, False)


def _set_favorite(request: Request, value: bool) -> None:
    item_id = request.params.get("id", "")
    try:
        _api().set_favorite(item_id, value)
    except JellyfinError as error:
        LOG.warning("favorite toggle failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    _refresh()


def delete_item(request: Request) -> None:
    """Delete the item from the server, after opt-in and confirmation.

    ``deleteNoConfirm`` drops the confirmation only for this path — picking
    Delete off the context menu is already a deliberate act. The
    finished-watching offer (service/player.py) asks either way.
    """
    if not settings.get_bool("enableDelete"):
        return
    item_id = request.params.get("id", "")
    name = request.params.get("name", "")
    if not settings.get_bool("deleteNoConfirm") and not xbmcgui.Dialog().yesno(
        xbmc.getLocalizedString(117),  # Delete
        settings.localized(30505) % name,
    ):
        return
    try:
        _api().delete_item(item_id)
    except JellyfinError as error:
        LOG.warning("delete failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    _refresh()


def open_settings(request: Request) -> None:
    xbmc.executebuiltin("Addon.OpenSettings(plugin.video.kofin)")


# -- Library tab buttons -------------------------------------------------------


def update_libraries(request: Request) -> None:
    """Library tab button: list every selected library again now. The
    coordinator reads no ids from the command, so the only question is
    whether to update them all."""
    if not settings.get_list("librarySelection"):
        return
    if xbmcgui.Dialog().yesno(settings.localized(30256), settings.localized(30873)):
        ipc.notify(ipc.UPDATE_LIBRARY, {})


def save_playlist(request: Request) -> None:
    """Push a local Kodi basic playlist to Jellyfin, then refresh the managed copy."""
    import os

    import xbmcvfs

    path = request.params.get("path", "") or xbmc.getInfoLabel(
        "ListItem.FileNameAndPath"
    )
    if not path or not path.lower().endswith((".m3u", ".m3u8")):
        toast.show(settings.localized(30844), toast.WARNING)
        return
    from kofin.sync import kofindb as jellyfin_db
    from kofin.sync import playlists as music_playlists
    from kofin.sync.private import Database

    translated = xbmcvfs.translatePath(path)
    try:
        # Kodi writes a .m3u in the GUI's character set, only a .m3u8 in
        # UTF-8. The lines that name kofin's rows are ASCII either way.
        with open(translated, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
    except OSError:
        LOG.exception("could not read playlist %s", path)
        toast.show(settings.localized(30507), toast.ERROR)
        return

    lines = music_playlists.parse_m3u_paths(text)
    api = _api()
    found = _playlist_items(lines)
    ids = [jellyfin_id for jellyfin_id, side in found if side]
    sides = {side for _, side in found if side}
    skipped = len(found) - len(ids)
    if not ids:
        toast.show(settings.localized(30844), toast.WARNING)
        return
    if len(sides) != 1:
        toast.show(settings.localized(30842), toast.WARNING)
        return
    media_type = sides.pop()
    name = request.params.get("name") or ""
    if not name:
        name = os.path.splitext(os.path.basename(path.rstrip("/")))[0]
    with Database("kofin") as kofindb:
        # By name and by side: a music and a video playlist can share a
        # name, and each side's managed copy is named after its title.
        stored_id = jellyfin_db.JellyfinDatabase(kofindb.cursor).playlist_for_file(
            os.path.basename(path), side=media_type
        )
    try:
        if stored_id:
            api.replace_playlist_items(stored_id, ids)
            playlist_id = stored_id
        else:
            created = api.create_playlist(name, ids, media_type)
            playlist_id = (created or {}).get("Id") or ""
    except JellyfinError as error:
        LOG.warning("save playlist failed: %s", error)
        toast.show(settings.localized(30507), toast.ERROR)
        return
    toast.show(settings.localized(30843))
    if skipped:
        LOG.debug("save playlist %s: %d line(s) not in the Kodi library", name, skipped)
    ipc.notify(ipc.SYNC_PLAYLISTS, {"Id": playlist_id} if playlist_id else {})


def _playlist_items(lines: list[str]) -> list[tuple[str, str]]:
    """The Jellyfin id and side ("Audio" or "Video") of each playlist line,
    ("", "") for a line kofin did not file, through the catalogue."""
    from kofin.sync.backends.api import playlists as api_playlists
    from kofin.sync.backends.api.identity import current_store

    return api_playlists.items_of_lines(current_store(), lines)


def repair_libraries(request: Request) -> None:
    """Per-library picker (or all) -> remove + re-add.

    No confirmation: the picker is the decision, and a repair rebuilds the
    same libraries from the server.
    """
    whitelist = settings.get_list("librarySelection")
    if not whitelist:
        return

    names = _selection_names(whitelist)
    choices: list[Union[str, xbmcgui.ListItem]] = [settings.localized(30267)]
    choices.extend(names)  # "All" first
    picked = xbmcgui.Dialog().multiselect(settings.localized(30266), choices)

    if not picked:  # cancelled or empty
        return

    if 0 in picked:
        selected = list(whitelist)
    else:
        selected = [whitelist[index - 1] for index in picked]

    ipc.notify(ipc.REPAIR_LIBRARY, {"Id": ",".join(selected)})


def _selection_names(library_ids: list[str]) -> list[str]:
    """View names for the picker; falls back to the raw ids offline."""
    from kofin.sync import private as sync_db
    from kofin.sync import kofindb

    names = []
    try:
        with sync_db.Database("kofin") as opened:
            db = kofindb.JellyfinDatabase(opened.cursor)
            for library_id in library_ids:
                view = db.get_view(library_id.replace("Mixed:", ""))
                names.append(view.name if view else library_id)
    except Exception:
        LOG.exception("view names unavailable")
        names = list(library_ids)
    return names


# -- offline downloads ---------------------------------------------------------


def _human_size(size_bytes: int) -> str:
    if size_bytes >= 1024**3:
        return "%.1f GB" % (size_bytes / 1024**3)
    return "%d MB" % max(1, size_bytes // 1024**2)


def _report_size(size_bytes: int) -> str:
    """``_human_size`` without the 1 MB floor: a report has real zeroes."""
    if size_bytes <= 0:
        return "0 MB"
    return _human_size(size_bytes)


# What actually downloads: everything else expands to these.
DOWNLOAD_LEAF_TYPES = ("Movie", "Episode", "Audio")
MAX_DOWNLOAD_EXPANSION = 50000


def _music_library(item: dict) -> bool:
    if item.get("Type") not in ("CollectionFolder", "UserView"):
        return False
    collection = item.get("CollectionType") or ""
    if collection:
        return collection == "music"
    # Some item endpoints omit the collection type supplied by /Views.
    from kofin.sync import kofindb
    from kofin.sync.private import Database

    with Database("kofin") as opened:
        tables = kofindb.JellyfinDatabase(opened.cursor)
        return tables.view_media(item.get("Id") or "") == "music"


class _DownloadTooLarge(Exception):
    def __init__(self, minimum_size: int, free: int) -> None:
        self.minimum_size = minimum_size
        self.free = free


class _ExpansionBar:
    """Kodi's background bar, shown once an expansion runs past a thousand rows."""

    def __init__(self) -> None:
        self._dialog: Optional[xbmcgui.DialogProgressBG] = None

    def update(self, seen: int, total: int) -> None:
        if total > 1000 and self._dialog is None:
            self._dialog = xbmcgui.DialogProgressBG()
            self._dialog.create("Kofin", settings.localized(30708))
        if self._dialog is not None and total and (seen % 1000 == 0 or seen >= total):
            self._dialog.update(min(100, int(seen * 100 / total)))

    def close(self) -> None:
        if self._dialog is not None:
            self._dialog.close()


def _paged_items(
    api: Api,
    params: dict,
    *,
    free: int = -1,
    live_ids: Optional[set[str]] = None,
    options: Optional[tuple] = None,
) -> list[dict]:
    children: list[dict] = []
    estimated = 0
    bar = _ExpansionBar()
    try:
        for row in paged(
            lambda start, limit: api.items(
                dict(
                    params,
                    Fields="MediaSources",
                    StartIndex=start,
                    Limit=limit,
                    EnableTotalRecordCount=True,
                )
            ),
            200,
            strict=True,
            cap=MAX_DOWNLOAD_EXPANSION,
            what="download expansion",
            progress=bar.update,
        ):
            children.append(row)
            if (
                free >= 0
                and row.get("Id")
                and row.get("Id") not in (live_ids or ())
                and row.get("CanDownload") is not False
                and row.get("Type") in DOWNLOAD_LEAF_TYPES
            ):
                from kofin.downloads.files import FREE_SPACE_RESERVE

                estimated += _estimated_size(row, options)
                if estimated + FREE_SPACE_RESERVE > free:
                    raise _DownloadTooLarge(estimated, free)
    finally:
        bar.close()
    return children


def _expand_downloadable(
    api: Api,
    item: dict,
    *,
    free: int = -1,
    live_ids: Optional[set[str]] = None,
    options: Optional[tuple] = None,
) -> list[dict]:
    """The downloadable leaves under an item: itself, or a container's
    episodes/tracks. Client-side expansion, because the server has no folder
    download — CanDownload is false for every folder type by construction."""
    item_type = item.get("Type")
    item_id = item.get("Id", "")
    if item_type in DOWNLOAD_LEAF_TYPES:
        return [item]
    if item_type == "Season":
        listing = api.episodes(item.get("SeriesId", ""), item_id, "MediaSources")
        return list(listing.get("Items") or [])
    if item_type == "Series":
        return _paged_items(
            api,
            {"ParentId": item_id, "IncludeItemTypes": "Episode", "Recursive": True},
            free=free,
            live_ids=live_ids,
            options=options,
        )
    if item_type == "MusicAlbum":
        return _paged_items(
            api,
            {"ParentId": item_id, "IncludeItemTypes": "Audio", "Recursive": True},
            free=free,
            live_ids=live_ids,
            options=options,
        )
    if item_type == "MusicArtist":
        # ArtistIds, not ParentId: an artist is a link target, not a folder,
        # and albums an artist merely appears on still count.
        return _paged_items(
            api,
            {"ArtistIds": item_id, "IncludeItemTypes": "Audio", "Recursive": True},
            free=free,
            live_ids=live_ids,
            options=options,
        )
    if _music_library(item):
        return _paged_items(
            api,
            {"ParentId": item_id, "IncludeItemTypes": "Audio", "Recursive": True},
            free=free,
            live_ids=live_ids,
            options=options,
        )
    if item_type == "Playlist":
        # Playlists mix types; keep the leaves this feature downloads.
        children = _paged_items(
            api,
            {"ParentId": item_id},
            free=free,
            live_ids=live_ids,
            options=options,
        )
        return [child for child in children if child.get("Type") in DOWNLOAD_LEAF_TYPES]
    return []


def _source_size(item: dict) -> int:
    sources = item.get("MediaSources") or [{}]
    return int(sources[0].get("Size") or 0)


def _estimate_options() -> tuple:
    """Read settings once for a large container, not once per track."""
    return (
        settings.get_bool("downloadsMusicTranscode"),
        settings.get_int("downloadsMusicBitrate") or 128,
        settings.get_bool("downloadsTranscode"),
        settings.get_float("downloadsMaxBitrate"),
    )


def _estimated_size(item: dict, options: Optional[tuple] = None) -> int:
    """What this child will weigh on disk.

    A track the music transcode re-encodes weighs the target bitrate times its
    runtime. Which tracks transcode is the server's call at download time
    (``quality.decide``), so take the smaller of that and the source — a
    track already inside the cap downloads untouched, and the confirmation
    says "about".
    """
    original = _source_size(item)
    item_type = item.get("Type")
    music_transcode, music_kbps, video_transcode, video_mbps = (
        options if options is not None else _estimate_options()
    )
    if item_type == "Audio":
        if not music_transcode:
            return original
        target_bps = music_kbps * 1000
    elif item_type in ("Movie", "Episode"):
        if not video_transcode:
            return original
        target_bps = int(video_mbps * 1_000_000)
        if target_bps <= 0:
            return original
    else:
        return original
    seconds = int(item.get("RunTimeTicks") or 0) / 10_000_000
    if seconds <= 0:
        return original
    transcoded = int(seconds * target_bps / 8)
    return min(original, transcoded) if original else transcoded


def _download_toast(string_id: int, *values: Any) -> None:
    """A downloads toast that honours the notification opt-out.

    Only the informational ones pass through here; failures go straight to
    ``toast.show`` so the opt-out cannot swallow them (kofin.downloads
    .LOUD_STRINGS states which is which).
    """
    from kofin.downloads import notify_allowed

    if not notify_allowed(string_id):
        return
    message = settings.localized(string_id)
    toast.show(message % values if values else message, time_ms=3000)


def _free_space_note() -> str:
    from kofin.downloads import downloads_root, files

    free = files.free_bytes(downloads_root())
    return _human_size(free) if free >= 0 else "?"


def _confirm_download(item: dict, wanted: list[dict]) -> bool:
    """Whether to go ahead with a queue request — asking, or refusing.

    The request is sized against what is free:

      * over free space minus the reserve: refused outright, since the
        manager would only fail it item by item further down;
      * at or over ``CONFIRM_FREE_SPACE_RATIO`` of what is free: confirmed;
      * anything smaller: queued in silence, whatever the count.

    A probe that cannot answer (files.free_bytes -1) confirms a container
    and queues a single item in silence.
    """
    from kofin.downloads import downloads_root, files
    from kofin.plugin.context import DOWNLOAD_CONTAINER_TYPES

    options = _estimate_options()
    total = sum(_estimated_size(child, options) for child in wanted)
    free = files.free_bytes(downloads_root())

    if free < 0:
        if item.get("Type") not in DOWNLOAD_CONTAINER_TYPES:
            return True
    elif total + files.FREE_SPACE_RESERVE > free:
        toast.show(
            settings.localized(30810) % (_human_size(total), _human_size(free)),
            toast.WARNING,
        )
        return False
    elif total < free * files.CONFIRM_FREE_SPACE_RATIO:
        return True

    return bool(
        xbmcgui.Dialog().yesno(
            settings.localized(30708),
            settings.localized(30771)
            % (len(wanted), _human_size(total), _free_space_note()),
        )
    )


def download(request: Request) -> None:
    """Queue downloads for an item or a container's episodes, then hand the
    ids to the service over the guarded IPC — the manager owns everything
    after that. Big requests confirm, and ones that will not fit are
    refused (:func:`_confirm_download`)."""
    item_id = request.params.get("id", "")
    if not item_id:
        return
    try:
        api = _api()
        item = api.item(item_id)
        from kofin.downloads import downloads_root, files, store

        live = {row.jellyfin_id for row in store.rows() if row.state != store.FAILED}
        free = files.free_bytes(downloads_root())
        children = _expand_downloadable(
            api,
            item,
            free=free,
            live_ids=live,
            options=_estimate_options() if free >= 0 else None,
        )
    except _DownloadTooLarge as error:
        toast.show(
            settings.localized(30810)
            % (_human_size(error.minimum_size), _human_size(error.free)),
            toast.WARNING,
        )
        return
    except JellyfinError as error:
        LOG.warning("download expansion failed for %s: %s", item_id, error)
        feedback.failed(error)
        return

    wanted = [
        child
        for child in children
        if child.get("Id")
        and child.get("Id") not in live
        and child.get("CanDownload") is not False
    ]
    if not wanted:
        return

    if not _confirm_download(item, wanted):
        return

    # The types travel with the ids: the manager sizes its two worker pools
    # by media kind, and the kind is not knowable from an id alone without
    # the very server round trip the queue is trying to get ahead of.
    #
    # So does the request — the container this expanded, and what to call it.
    # Its children can span albums and media types, but the manager announces
    # the whole request only once, when every child has settled.
    payload: dict[str, Any] = {
        "Ids": [child["Id"] for child in wanted],
        "Types": [str(child.get("Type") or "") for child in wanted],
    }
    payload["Request"] = item_id
    payload["RequestName"] = str(item.get("Name") or item_id)
    ipc.notify(ipc.DOWNLOAD_ADD, payload)


def download_show(request: Request) -> None:
    """Toggle a show's new-episode subscription."""
    item_id = request.params.get("id", "")
    if not item_id:
        return
    from kofin.downloads import auto as downloads_auto

    subscribed = downloads_auto.toggle_show(item_id)
    name = request.params.get("name", "") or item_id
    _download_toast(30762 if subscribed else 30763, name)


def download_playlist(request: Request) -> None:
    from kofin.downloads import subscriptions

    item_id = request.params.get("id", "")
    if not item_id:
        return
    enabled = subscriptions.toggle(subscriptions.PLAYLIST_SETTING, item_id)
    if enabled:
        ipc.notify(ipc.SYNC_PLAYLISTS, {"Id": item_id})
    else:
        subscriptions.release(subscriptions.owner("playlist", item_id))


def download_music_library(request: Request) -> None:
    from kofin.downloads import subscriptions

    item_id = request.params.get("id", "")
    if not item_id:
        return
    enabled = subscriptions.toggle(subscriptions.LIBRARY_SETTING, item_id)
    if enabled:
        ipc.notify(ipc.SYNC_PLAYLISTS, {})
    else:
        subscriptions.release(subscriptions.owner("musiclibrary", item_id))


def manage_download_subscriptions(request: Request) -> None:
    """Settings picker for either kind of standing music download order.

    The button carries ``<close>true</close>``: written into a settings
    dialog still open, the list would be put back when the user backs out.
    """
    from kofin.downloads import subscriptions
    from kofin.sync import kofindb
    from kofin.sync.private import Database

    kind = request.params.get("kind", "playlist")
    setting_id = (
        subscriptions.PLAYLIST_SETTING
        if kind == "playlist"
        else subscriptions.LIBRARY_SETTING
    )
    ids = subscriptions.subscribed(setting_id)
    if not ids:
        toast.show(settings.localized(30853), time_ms=3000)
        return
    names: list[Union[str, xbmcgui.ListItem]] = []
    with Database("kofin") as opened:
        tables = kofindb.JellyfinDatabase(opened.cursor)
        for item_id in ids:
            if kind == "playlist":
                name = tables.playlist_filename(item_id)
            else:
                name = tables.view_name(item_id)
            names.append(item_id if name is None else name)
    picked = xbmcgui.Dialog().multiselect(
        settings.localized(30851 if kind == "playlist" else 30852),
        names,
        preselect=list(range(len(ids))),
    )
    if picked is None:
        return
    kept = {ids[index] for index in picked}
    subscriptions.save(setting_id, (item_id for item_id in ids if item_id in kept))
    for item_id in ids:
        if item_id not in kept:
            subscriptions.release(
                subscriptions.owner(
                    "playlist" if kind == "playlist" else "musiclibrary", item_id
                )
            )


def manage_download_shows(request: Request) -> None:
    """Settings button: review the subscribed shows; untick to stop.

    Cancel changes nothing; OK keeps exactly what stayed ticked. Names come
    from Kodi's own rows via the mapping, so the picker works offline; a
    show missing from the library falls back to its raw id, which is still
    removable. The button closes the settings dialog first, as the
    subscriptions picker's does.
    """
    from kofin.downloads import auto as downloads_auto

    shows = downloads_auto.subscribed_shows()
    if not shows:
        toast.show(settings.localized(30766), time_ms=3000)
        return
    choices: list[Union[str, xbmcgui.ListItem]] = list(_show_names(shows))
    picked = xbmcgui.Dialog().multiselect(
        settings.localized(30758), choices, preselect=list(range(len(shows)))
    )
    if picked is None:
        return
    downloads_auto.save_subscribed_shows(shows[index] for index in picked)


def _show_names(series_ids: list[str]) -> list[str]:
    """Titles for the picker, from the shows' catalogue payloads, so the
    picker answers offline. A show the catalogue does not hold is listed by
    its id."""
    from kofin.sync.backends.api.identity import current_store

    try:
        payloads = current_store().payloads(series_ids)
    except Exception:
        LOG.exception("show names unavailable")
        return list(series_ids)
    return [
        str((payloads.get(series_id) or {}).get("Name") or series_id)
        for series_id in series_ids
    ]


def delete_all_downloads(request: Request) -> None:
    """The settings button: confirm, then let the service clear the lot.

    Counted and sized from the local store, so it works offline and states
    what is actually about to be freed. One IPC for the whole request — the
    service walks the store itself.
    """
    from kofin.downloads import store

    rows = store.rows()

    if not rows:
        toast.show(settings.localized(30807), time_ms=3000)
        return

    # What is on disk, not what was promised: a queued row has downloaded
    # nothing yet, and a finished one may have transcoded smaller than its
    # source.
    freed = sum(row.bytes_done or 0 for row in rows)

    if not xbmcgui.Dialog().yesno(
        settings.localized(30804),
        settings.localized(30806) % (len(rows), _human_size(freed)),
    ):
        return

    ipc.notify(ipc.DOWNLOAD_REMOVE_ALL)


def library_status(request: Request) -> None:
    """Settings button: what is synced, what is pending, what the sync is
    doing. The report and its dialog are status.py's; the button carries no
    ``<close>``, so reading it returns to the settings."""
    from kofin.sync.backends.api import status
    from kofin.sync.backends.api.identity import current_store, owner_store

    if Credentials.load().is_logged_in:
        status.show(current_store())
        return
    # Logged out, the rows stay keyed to the account that filed them, and
    # the report is theirs, with what becomes of them said first.
    store = owner_store()
    if store is None:
        toast.show(settings.localized(30026), toast.WARNING)
        return
    status.show(store, logged_out=True)


def download_size(request: Request) -> None:
    """Settings button: where the downloads are and what they weigh.

    Read-only. The button carries no ``<close>``, so answering the dialog
    returns to the Downloads settings.

    Each size goes in the row's own label: ``Dialog().select``'s plain list
    layout draws no ``label2``.

    The walk happens here, in the plugin process, which must stay thin — so
    it is stat-only, bounded (``usage.MAX_ENTRIES``), and covered by a
    background progress dialog for a root on slow or network storage.
    """
    from kofin.downloads import downloads_root, usage

    root = downloads_root()
    progress = xbmcgui.DialogProgressBG()
    try:
        progress.create(settings.localized(30832))
        report = usage.scan(root)
    finally:
        try:
            progress.close()
        except Exception:  # pragma: no cover - Kodi's own dialog bookkeeping
            LOG.debug("progress dialog would not close")

    if report.empty:
        toast.show(settings.localized(30835), time_ms=4000)
        return

    rows: list[Union[str, xbmcgui.ListItem]] = [
        # The capped notice is a sentence, not a measurement, and carries no
        # value to append.
        "%s:  %s" % (label, value) if value else label
        for label, value in size_rows(report)
    ]
    # The heading names the folder, because "where" is half the question the
    # button answers and a path is too long for a row label.
    xbmcgui.Dialog().select("%s — %s" % (settings.localized(30832), root), rows)


def size_rows(report: Any) -> list[tuple]:
    """``[(label, value)]`` for the size report — the whole decision, kept
    out of the widget so it can be tested without one."""
    rows = [
        (
            (
                settings.localized(bucket.label_id)
                if bucket.label_id >= 30000
                else xbmc.getLocalizedString(bucket.label_id)
            ),
            _report_size(bucket.size),
        )
        for bucket in report.buckets
    ]
    rows.append((xbmc.getLocalizedString(20161), _report_size(report.total)))
    if report.free >= 0:
        # -1 is "could not tell" (an exotic mount, a permissions refusal),
        # and the row is dropped rather than shown empty or as zero — zero
        # is a real answer meaning a full disk, and the two must not read
        # alike to somebody deciding whether to download something.
        rows.append((xbmc.getLocalizedString(160), _report_size(report.free)))
    if report.capped:
        rows.append((settings.localized(30836), ""))
    return rows


def _music_targets(
    request: Request, item_id: str, states: tuple[str, ...]
) -> Optional[list[str]]:
    """The songs a music container's download entry acts on, those in the
    given states; None for an entry that is not a music container's. A
    playlist or a library a subscription keeps answers no song: the
    subscription owns its downloads."""
    music_scope = (
        "playlist"
        if request.params.get("playlist") == "1"
        else "musiclibrary" if request.params.get("library") == "1" else ""
    )
    if not music_scope:
        return None
    from kofin.downloads import store, subscriptions

    setting = (
        subscriptions.PLAYLIST_SETTING
        if music_scope == "playlist"
        else subscriptions.LIBRARY_SETTING
    )
    if item_id in subscriptions.subscribed(setting):
        return []
    return [
        song_id
        for song_id, state in store.music_container_unclaimed_states(
            item_id, music_scope
        ).items()
        if state in states
    ]


def cancel_download(request: Request) -> None:
    """Cancel one download, or every unfinished one under a container.

    The expansion is local (kofin.db), not a server walk: cancelling has to
    work offline, and the store already knows which rows belong to the show
    or album in front of the user.
    """
    item_id = request.params.get("id", "")
    if not item_id:
        return
    from kofin.downloads import store

    targets = _music_targets(request, item_id, (store.QUEUED, store.ACTIVE))
    if targets is None:
        targets = (
            [item_id] if store.get(item_id) else store.container_pending_ids(item_id)
        )
    for target in targets:
        ipc.notify(ipc.DOWNLOAD_CANCEL, {"Id": target})


def remove_download(request: Request) -> None:
    """Let the service delete the downloaded files. No confirmation.

    Unlike Delete on the same menu, only a local copy goes: the server still
    has the item.

    A container removes everything finished under it, expanded from kofin.db
    rather than the server so the entry keeps working offline, and sent as one
    message: a season is one request and gets one refresh and one toast (see
    ``downloads/manager.py::remove``).
    """
    item_id = request.params.get("id", "")
    if not item_id:
        return
    from kofin.downloads import store

    targets = _music_targets(request, item_id, (store.DONE,))
    if targets is None:
        targets = (
            [item_id]
            if store.get(item_id) is not None
            else store.container_done_ids(item_id)
        )
    if targets:
        ipc.notify(ipc.DOWNLOAD_REMOVE, {"Ids": targets})
