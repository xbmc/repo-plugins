"""Route plugin invocations (pluginsource and RunPlugin) to handlers."""

from importlib import import_module
from typing import Callable, Optional
from urllib.parse import parse_qsl

from kofin.core.log import Logger

LOG = Logger(__name__)

# Every path the scanner provider answers lies under this
# (sync/backends/api/paths.py); spelled again in plugin/gate.py, which
# imports nothing of kofin's, and a test holds the two together.
NATIVE_MARK = "/native/"

Params = dict[str, str]


class Request:
    def __init__(
        self,
        base_url: str,
        handle: int,
        params: Params,
        resume: bool = False,
    ) -> None:
        self.base_url = base_url
        self.handle = handle
        self.params = params
        self.resume = resume


# The handler registry, as (module under kofin.plugin, attribute) pairs
# resolved per dispatch, so an invocation imports only the module it routes to.
ROUTES: dict[str, tuple[str, str]] = {
    "": ("browse", "root"),
    "streams": ("streams", "menu"),
    "browse": ("browse", "browse"),
    "continuewatching": ("browse", "continue_watching"),
    "nextepisodes": ("browse", "next_episodes"),
    "extras": ("browse", "extras"),
    "search": ("browse", "search"),
    "lyrics": ("lyrics", "lyrics"),
    "play": ("play", "play"),
    "check_exists": ("exists", "check_exists"),
    "syncplay": ("syncplay", "menu"),
    "findservers": ("serverpicker", "find_servers"),
    "login": ("account", "login"),
    "logout": ("account", "logout"),
    "testconnection": ("account", "test_connection"),
    "restart": ("account", "restart"),
    "settings": ("actions", "open_settings"),
    "adduser": ("adduser", "who_is_watching"),
    "whoshortlist": ("adduser", "select_shortlist"),
    "userprefs": ("userprefs", "jellyfin_settings"),
    "watched": ("actions", "watched"),
    "unwatched": ("actions", "unwatched"),
    "resetresume": ("actions", "reset_resume"),
    "playall": ("playall", "play_all"),
    "download": ("actions", "download"),
    "downloadshow": ("actions", "download_show"),
    "downloadplaylist": ("actions", "download_playlist"),
    "downloadmusiclibrary": ("actions", "download_music_library"),
    "downloadsubscriptions": ("actions", "manage_download_subscriptions"),
    "downloadshows": ("actions", "manage_download_shows"),
    "canceldownload": ("actions", "cancel_download"),
    "removedownload": ("actions", "remove_download"),
    "deletealldownloads": ("actions", "delete_all_downloads"),
    "downloadsize": ("actions", "download_size"),
    "librarystatus": ("actions", "library_status"),
    "favorite": ("actions", "favorite"),
    "unfavorite": ("actions", "unfavorite"),
    "delete": ("actions", "delete_item"),
    "selectlibraries": ("librarypicker", "select_libraries"),
    "updatelibs": ("actions", "update_libraries"),
    "repairlibs": ("actions", "repair_libraries"),
    "saveplaylist": ("actions", "save_playlist"),
}

# The routes that answer a directory fetch themselves: they either build a
# listing and call endOfDirectory (browse and friends, lyrics) or resolve a
# playable item with setResolvedUrl (play, on every path including its
# failures). Every other route runs for its side effect and returns nothing,
# and dispatch closes the handle on its behalf.
#
# With reuselanguageinvoker the invoker thread parks between invocations
# instead of exiting, and Kodi only marks a script done from
# CLanguageInvokerThread::OnExit — so CScriptRunner::WaitOnScriptResult, which
# loops on IsRunning(scriptId) with no timeout on its first loop, waits forever
# for a route that leaves its handle open. test_router.py refuses any ROUTES
# entry that is in neither set.
LISTING_MODES = frozenset(
    {
        "",
        "browse",
        "continuewatching",
        "nextepisodes",
        "extras",
        "search",
        "lyrics",
        "play",
        "check_exists",
    }
)


def _resolve(mode: str) -> Optional[Callable[[Request], None]]:
    """The handler for ``mode``, imported on demand; None when unregistered."""
    route = ROUTES.get(mode)
    if route is None:
        return None
    module = import_module("kofin.plugin." + route[0])
    handler: Callable[[Request], None] = getattr(module, route[1])
    return handler


def _root(request: Request) -> None:
    """Unknown-mode fallback: the root listing."""
    from kofin.plugin import browse

    browse.root(request)


def dispatch(argv: list[str]) -> None:
    base_url = argv[0] if argv else ""
    handle = -1
    if len(argv) > 1:
        try:
            handle = int(argv[1])
        except ValueError:
            handle = -1
    query = argv[2] if len(argv) > 2 else ""
    # One trailing slash off the whole query before it is parsed. A library
    # node's <path> is a folder path and carries one, and it lands on whichever
    # parameter happens to be last.
    params = dict(parse_qsl(query.lstrip("?").rstrip("/")))
    # Kodi appends "resume:true|false" for video plugin items (the native
    # resume prompt's outcome).
    resume = len(argv) > 3 and argv[3].split(":", 1)[-1] == "true"
    request = Request(base_url, handle, params, resume)

    # A path outside the provider's is not parsed, and pays for none of the
    # provider's imports.
    if NATIVE_MARK in base_url:
        import time

        imports_began = time.monotonic()
        from kofin.sync.backends.api import paths
        from kofin.sync.backends.api.provider import serve

        location = paths.parse(base_url)
        LOG.debug(
            "native dispatch handle=%s after %.2f s of imports",
            handle,
            time.monotonic() - imports_began,
        )
        native = location.key if location else None
        if (
            native
            and location is not None
            and location.song
            and not params.get("kodi_action")
        ):
            # A native song is a file in its album directory, not a query:
            # Kodi's music database keeps no query string on a file name.
            params.setdefault("mode", "play")
            params["id"] = location.song
        if (
            native
            and location is not None
            and location.extra
            and not params.get("kodi_action")
        ):
            # A movie extra is a file in its movie's extras folder, named by
            # its stem; the id is looked up from the stem. A stem the
            # catalogue no longer names is a failed play, never a listing.
            from kofin.sync.backends.api.provider import resolve_extra

            extra_id = resolve_extra(location)
            if not extra_id:
                import xbmcgui
                import xbmcplugin

                LOG.warning(
                    "extra %r of movie %s not in the catalogue",
                    location.extra,
                    (location.movie or "")[:8],
                )
                xbmcplugin.setResolvedUrl(
                    handle, False, xbmcgui.ListItem(path=base_url)
                )
                return
            params.setdefault("mode", "play")
            params["id"] = extra_id
        if base_url.endswith("/native/") or (
            native and (params.get("kodi_action") or params.get("mode") != "play")
        ):
            try:
                serve(request)
            except BaseException:
                import xbmcgui
                import xbmcplugin

                if params.get("kodi_action") == "check_exists":
                    # Kodi's clean deletes the row of a probe that fails: a
                    # catalogue that cannot be read is no word on the row.
                    xbmcplugin.setResolvedUrl(
                        handle, True, xbmcgui.ListItem(path=base_url)
                    )
                else:
                    xbmcplugin.endOfDirectory(
                        handle, succeeded=False, cacheToDisc=False
                    )
                raise
            return

    # Kodi's cleaner appends kodi_action to the stored play URL. It must win
    # over mode=play: resolving a stream would start playback-side work and
    # make a library clean depend on Jellyfin being online.
    mode = (
        "check_exists"
        if params.get("kodi_action") == "check_exists"
        else params.get("mode", "")
    )
    handler = _resolve(mode)
    LOG.debug("dispatch mode=%s params=%s handle=%s", mode or "<root>", params, handle)
    builds_listing = mode in LISTING_MODES
    if handler is None:
        LOG.warning("unknown mode %r; showing root", mode)
        handler = _root
        # The fallback *is* the root listing, whatever was asked for.
        builds_listing = True
    failed = False
    try:
        handler(request)
    except BaseException:
        failed = True
        raise
    finally:
        # Close the handle for the routes that build nothing (LISTING_MODES)
        # and for *any* route whose handler raised: a listing route closes its
        # own handle only on JellyfinError. The exception still propagates;
        # only the caller is released.
        if handle >= 0 and (failed or not builds_listing):
            import xbmcplugin

            xbmcplugin.endOfDirectory(handle, succeeded=False)
