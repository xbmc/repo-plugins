"""Directory listings: addon root, library nodes, and drill-down browsing."""

import os
from typing import Any, Callable, Optional
from collections.abc import Iterable

import xbmcgui
import xbmcplugin

from kofin.core import settings, state
from kofin.core.api import Api, paged
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.core.urls import plugin_url
from kofin.plugin import feedback, listitems
from kofin.plugin.router import Request

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# The addon fanart asset, the backdrop behind structural listings: the same
# file addon.xml declares, named here rather than read from the manifest.
# Nothing rewrites it. With the server-backdrop setting on, the server's
# splashscreen — a content-addressed file in addon_data (service/backdrop.py,
# profile_path) — wins over it in with_backdrop.
BACKDROP_IMAGE = "fanart.jpeg"

BROWSE_FIELDS = (
    "Overview,Genres,Studios,Taglines,PremiereDate,ProductionYear,"
    "OfficialRating,CommunityRating,RunTimeTicks,DateCreated,"
    "ProviderIds,SortName"
)

# MediaStreams is the field that prices a listing. Bounded listings keep it,
# and whole-library nodes drop it and render without codec/resolution flags.
# Music never asks: _fill_music never reads stream details.
BROWSE_FIELDS_STREAMS = BROWSE_FIELDS + ",MediaStreams"

# How many rows a "recent" node shows. Also what makes those nodes bounded,
# which is what earns them the fields above.
RECENT_LIMIT = 25


def bounded_fields() -> str:
    """The field list for a listing short enough to carry the expensive ones.

    MediaStreams always (BROWSE_FIELDS_STREAMS). People only when the viewer
    asked for cast in the add-on's listings (browseCast, off by default).

    The gate is boundedness, and it is not a preference: People's cost to the
    *server* is linear in the result set, so the whole-library and filter
    nodes (all, unwatched, favorites, sets, genres, years, tags, the
    alphabet) never ask for it, whatever the setting says — and neither does
    music, which reads no people at all.

    Every caller is a listing something already bounds: a node with a Limit,
    Next up, Continue watching, a season's episodes, search results and a
    person's filmography (both SEARCH_LIMIT). Extras are the one bounded
    listing without it — /Items/{id}/SpecialFeatures takes no Fields.
    """
    fields = BROWSE_FIELDS_STREAMS
    if settings.get_bool("browseCast"):
        fields += ",People"
    return fields


# Node menus per collection type: (folder key, label string id).
#
# A label id outside 30000-30999 is Kodi's own (:func:`node_label`). Years,
# Tags, Album artists, Last played and Top 100 songs are lifted from Kodi's own
# library nodes (system/library/{video,music}), which is also where their icons
# come from.
NODES: dict[str, list[tuple[str, int]]] = {
    "movies": [
        ("all", 30030),
        ("recent", 30031),
        ("inprogress", 30033),
        ("unwatched", 30034),
        ("favorites", 30035),
        ("sets", 30038),
        ("genres", 30036),
        ("years", 652),
        ("tags", 20459),
        ("alpha", 30818),
        ("random", 30037),
    ],
    "tvshows": [
        ("all", 30030),
        ("recentepisodes", 30031),
        ("nextup", 30032),
        ("inprogressepisodes", 30033),
        ("unwatched", 30034),
        ("favorites", 30035),
        ("genres", 30036),
        ("years", 652),
        ("tags", 20459),
        ("alpha", 30818),
        ("random", 30037),
    ],
    "music": [
        ("artists", 30039),
        ("albumartists", 38043),
        ("albums", 30040),
        ("recentalbums", 30031),
        ("lastplayed", 568),
        ("topsongs", 10504),
        ("favoritealbums", 30035),
        ("genres", 30036),
        ("alpha", 30818),
    ],
    "musicvideos": [
        ("all", 30030),
        ("recent", 30031),
        ("unwatched", 30034),
        ("favorites", 30035),
        ("genres", 30036),
        ("alpha", 30818),
        ("random", 30037),
    ],
}

# Folder key -> label id, flattened from NODES. First listing wins if a
# key is reused (they currently share wording: All, Recently added, …).
FOLDER_LABELS: dict[str, int] = {}
for _nodes in NODES.values():
    for _key, _label_id in _nodes:
        FOLDER_LABELS.setdefault(_key, _label_id)
# Show-library Favourites is a submenu; these are its two legs (not in NODES).
FOLDER_LABELS["favoriteshows"] = 30359
FOLDER_LABELS["favoriteepisodes"] = 30360

# The two listings under a show library's Favourites row, in menu order.
# Empty legs are omitted; the parent row is omitted when both are.
TV_FAVORITE_LEGS: tuple[tuple[str, int, str], ...] = (
    ("favoriteshows", 30359, "Series"),
    ("favoriteepisodes", 30360, "Episode"),
)

# Structural menus whose content type stays empty, so Container.FolderName
# (the row the viewer clicked) is what Estuary shows. Setting a category
# on those would stack the same word twice.
_STRUCTURAL_FOLDERS = frozenset({"alpha", "years", "tags", "genres"})

# The alphabet menu's rows. "#" is everything sorting before A, which
# Jellyfin answers with NameLessThan rather than a NameStartsWith it has no
# character for.
ALPHABET = ("#",) + tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# Play history is song-level. Filters=IsPlayed against MusicAlbum returns zero,
# and sorting albums by DatePlayed with no filter puts unplayed ones first, so
# both history nodes list songs.
PLAY_HISTORY_LIMIT = 100

# Past this many tags the menu shows initials first. Under it, a flat list is
# friendlier than a letter you have to guess.
TAG_MENU_MAX = 200

# What search offers, as {type key: (Kodi core string id, IncludeItemTypes,
# Kodi content type)}. Order is the menu order. Actors (string 344) sit
# directly under episodes; artists sit directly under songs.
SEARCH_KINDS: dict[str, tuple[int, str, str]] = {
    "movies": (20342, "Movie", "movies"),
    "tvshows": (20343, "Series", "tvshows"),
    "episodes": (20360, "Episode", "episodes"),
    "people": (344, "", ""),
    "albums": (132, "MusicAlbum", "albums"),
    "songs": (134, "Audio", "songs"),
    "artists": (133, "MusicArtist", "artists"),
}

SEARCH_ICONS = {
    "movies": "DefaultMovies.png",
    "tvshows": "DefaultTVShows.png",
    "episodes": "DefaultTVShows.png",
    "people": "DefaultActor.png",
    "albums": "DefaultMusicAlbums.png",
    "songs": "DefaultMusicSongs.png",
    "artists": "DefaultMusicArtists.png",
}

# Search results are bounded on purpose: the caller is waiting on this fetch,
# and a hundred rows is already past what anyone reads.
SEARCH_LIMIT = 100

# A playlist is listed whole, a page at a time; most fit in one.
PLAYLIST_PAGE = 500

CONTENT_TYPES = {
    "movies": "movies",
    "tvshows": "tvshows",
    "musicvideos": "musicvideos",
    "music": "artists",
}

# The Jellyfin item type one collection type is made of: the genre listing,
# the year/tag filter menus and the tag pages ask by it.
# The Jellyfin item type one collection type is made of.
ITEM_TYPES = {
    "movies": "Movie",
    "tvshows": "Series",
    "music": "MusicAlbum",
    "musicvideos": "MusicVideo",
}

# Stock Kodi icons for structural entries (never addon art — the skin
# substitutes its own native artwork for Default*.png names). Server artwork
# belongs only on real media items.
MEDIA_ICONS = {
    "movies": "DefaultMovies.png",
    "tvshows": "DefaultTVShows.png",
    "musicvideos": "DefaultMusicVideos.png",
    "music": "DefaultAddonMusic.png",
    "books": "DefaultAddonInformation.png",
    "homevideos": "DefaultAddonVideo.png",
    "playlists": "DefaultPlaylist.png",
    "boxsets": "DefaultSets.png",
    # Jellyfin DVR UserView often has no CollectionType; we map it to this key.
    "recordings": "DefaultPVRRecordings.png",
}

NODE_ICONS: dict[str, Any] = {
    "recent": {
        "movies": "DefaultRecentlyAddedMovies.png",
        "musicvideos": "DefaultRecentlyAddedMusicVideos.png",
    },
    "recentepisodes": "DefaultRecentlyAddedEpisodes.png",
    # Not DefaultRecentlyAddedAlbums.png, which reads like the video names
    # above and renders as nothing: no skin has it. Kodi's own node for this
    # (system/library/music/recentlyaddedalbums.xml) says
    # DefaultMusicRecentlyAdded.png, and the music icons follow that shape
    # throughout — DefaultMusicRecentlyPlayed, DefaultMusicRoles, and so on.
    "recentalbums": "DefaultMusicRecentlyAdded.png",
    "inprogress": "DefaultInProgressShows.png",
    "inprogressepisodes": "DefaultInProgressShows.png",
    "nextup": "DefaultInProgressShows.png",
    "favorites": "DefaultFavourites.png",
    "favoriteshows": "DefaultFavourites.png",
    "favoriteepisodes": "DefaultFavourites.png",
    "favoritealbums": "DefaultFavourites.png",
    "sets": "DefaultSets.png",
    "genres": "DefaultGenre.png",
    "artists": "DefaultMusicArtists.png",
    "albumartists": "DefaultMusicArtists.png",
    "albums": "DefaultMusicAlbums.png",
    # Kodi's own nodes for the same things: video/movies/years.xml says
    # DefaultYear, music/years.xml says DefaultMusicYears, and both tags.xml
    # files say DefaultTags.
    "years": {
        "movies": "DefaultYear.png",
        "tvshows": "DefaultYear.png",
        "musicvideos": "DefaultYear.png",
        "music": "DefaultMusicYears.png",
    },
    "tags": "DefaultTags.png",
    "lastplayed": "DefaultMusicRecentlyPlayed.png",
    "topsongs": "DefaultMusicTop100Songs.png",
}


# Rows that stand for a piece of media rather than for a place to go. The
# addon backdrop never fills one (:func:`apply_backdrop` is called only for
# the others): it is the *addon's* artwork, and drawn behind a media item it
# reads as that item's own.
#
# Everything else a listing holds — genres, folders, playlists, library rows,
# the Extras link — stands for a query or a container and keeps the backdrop.
MEDIA_TYPES = frozenset(
    {
        "Movie",
        "Episode",
        "Series",
        "Season",
        "MusicVideo",
        "Video",
        "Trailer",
        "Recording",
        "BoxSet",
        "Audio",
        "MusicAlbum",
        "MusicArtist",
        "Photo",
    }
)


def is_media_row(item: JsonDict) -> bool:
    return item.get("Type", "") in MEDIA_TYPES


def node_icon(media: str, node: str = "") -> str:
    if node == "alpha":
        # The one structural row with no Kodi counterpart to substitute: no
        # skin ships an alphabet glyph. Material Symbols "sort_by_alpha"
        # (Apache-2.0), shipped white-on-transparent like the addon's others.
        return _addon_media("alphabet.png") or "DefaultMusicArtists.png"
    icon = NODE_ICONS.get(node)
    if isinstance(icon, dict):
        icon = icon.get(media)
    return icon or MEDIA_ICONS.get(media, "DefaultVideo.png")


def node_label(label_id: int) -> str:
    """A node's label, from whichever string table owns the id.

    The addon's own ids are 30000-30999; everything else in NODES is a Kodi
    core id, lifted from the shipped node that means the same thing, so its
    wording needs no translation of the add-on's. Asking the addon for a core
    id returns an empty string, which renders as a nameless row.
    """
    if 30000 <= label_id <= 30999:
        return settings.localized(label_id)

    import xbmc

    return xbmc.getLocalizedString(label_id)


def structural_art(icon: str) -> dict[str, str]:
    """Art for a structural row: a node-menu entry, a genre, an Extras link.

    Both keys, always. Contuary binds the list glyph to ListItem.Icon, which
    prefers thumb over Art(icon), so an icon-only row draws nothing at all --
    and the listing that holds these rows has to leave its content type empty
    for the same reason the root does: with "files" the skin switches to
    ListWatchedIconVar (folder and status overlays) and ignores setArt(icon)
    outright. The two rules only work together.

    Server artwork never comes through here. These rows stand for a query, not
    for a thing that has a poster.
    """
    return with_backdrop({"icon": icon, "thumb": icon})


def with_backdrop(art: dict[str, str]) -> dict[str, str]:
    """Fill in the addon backdrop for an item that has no fanart of its own.

    A fallback, not a decoration — it only ever fills an empty slot, so an
    item with real server artwork keeps it. Media rows are excluded at the
    call site rather than here (see :data:`MEDIA_TYPES`).

    Two kinds of row need this, which is why it is not folded into
    :func:`structural_art`. Structural rows stand for a query and have no art
    at all. Library rows carry a Primary image, but a Jellyfin UserView has
    no ``BackdropImageTags``, so ``art_for`` never sets fanart for one.

    It goes on the *item* because ``setPluginFanart`` and
    ``setProperty(handle, "fanart_image")`` leave ``Container.Art(fanart)``
    empty. Being per-item, the backdrop tracks focus, and Kodi's synthesised
    ".." row carries no art and takes none, so the background blanks while
    the parent row is focused; there is no addon-side hook for it.
    """
    if not art.get("fanart"):
        from kofin.service.backdrop import profile_path

        backdrop = profile_path() or _addon_media(BACKDROP_IMAGE)
        if backdrop:
            art["fanart"] = backdrop
    return art


def apply_backdrop(li: xbmcgui.ListItem) -> None:
    """:func:`with_backdrop` for a row whose art is already on the ListItem."""
    if not li.getArt("fanart"):
        li.setArt(with_backdrop({}))


def _collection_type(view: JsonDict) -> str:
    """Jellyfin CollectionType for a root view, with recordings inferred.

    The DVR Recordings UserView commonly ships with an empty CollectionType,
    so node_icon would fall through to DefaultVideo.png. Name-match is the
    stable signal Jellyfin clients use when the enum is missing.
    """
    collection = view.get("CollectionType") or ""
    if collection:
        return collection
    name = (view.get("Name") or "").lower()
    if "recording" in name:
        return "recordings"
    return ""


def _addon_media(filename: str) -> str:
    """Absolute path to a file under resources/media/.

    Empty when the addon path is unknown (same defensive posture as
    toast.addon_icon): Kodi draws a blank glyph for a path to nowhere.
    """
    try:
        path = settings.addon_path()
    except Exception:  # pragma: no cover - defensive
        return ""
    if not path:
        return ""
    return os.path.join(path, "resources", "media", filename)


def node_query(media: str, node: str, view_id: str) -> Optional[JsonDict]:
    """API query params for a browse node; None for nodes with special routes."""
    base: JsonDict = {
        "ParentId": view_id,
        "Recursive": True,
        "Fields": BROWSE_FIELDS,
        "ImageTypeLimit": 1,
        "SortBy": "SortName",
        "SortOrder": "Ascending",
    }
    types = ITEM_TYPES.get(media, "")

    if node == "all":
        base["IncludeItemTypes"] = types
    elif node == "recent":
        base.update(
            IncludeItemTypes=types,
            SortBy="DateCreated",
            SortOrder="Descending",
            Limit=25,
        )
    elif node == "recentepisodes":
        base.update(
            IncludeItemTypes="Episode",
            SortBy="DateCreated",
            SortOrder="Descending",
            Limit=25,
        )
    elif node == "inprogress":
        base.update(
            IncludeItemTypes=types,
            Filters="IsResumable",
            SortBy="DatePlayed",
            SortOrder="Descending",
            Limit=25,
        )
    elif node == "inprogressepisodes":
        base.update(
            IncludeItemTypes="Episode",
            Filters="IsResumable",
            SortBy="DatePlayed",
            SortOrder="Descending",
            Limit=25,
        )
    elif node == "unwatched":
        base.update(IncludeItemTypes=types, Filters="IsUnplayed")
    elif node == "favorites":
        if media == "tvshows":
            # Submenu of favorite shows / favorite episodes, not a listing.
            return None
        base.update(IncludeItemTypes=types, Filters="IsFavorite")
    elif node == "favoriteshows":
        base.update(IncludeItemTypes="Series", Filters="IsFavorite")
    elif node == "favoriteepisodes":
        base.update(IncludeItemTypes="Episode", Filters="IsFavorite")
    elif node == "favoritealbums":
        base.update(IncludeItemTypes="MusicAlbum", Filters="IsFavorite")
    elif node == "sets":
        base.update(IncludeItemTypes="BoxSet")
    elif node == "random":
        base.update(IncludeItemTypes=types, SortBy="Random", Limit=25)
    elif node == "albums":
        base.update(IncludeItemTypes="MusicAlbum", SortBy="AlbumArtist,SortName")
    elif node.startswith("genre-"):
        base["GenreIds"] = node.split("-", 1)[1]
        base["IncludeItemTypes"] = types
    elif node.startswith("alpha-"):
        letter = node.split("-", 1)[1]
        base["IncludeItemTypes"] = "MusicArtist" if media == "music" else types
        # "#" is everything before A, which has no NameStartsWith character.
        if letter == "#":
            base["NameLessThan"] = "A"
        else:
            base["NameStartsWith"] = letter
    elif node.startswith("year-"):
        base.update(IncludeItemTypes=types, Years=node.split("-", 1)[1])
    elif node.startswith("tag-"):
        base.update(IncludeItemTypes=types, Tags=node.split("-", 1)[1])
    elif node == "lastplayed":
        base.update(
            IncludeItemTypes="Audio",
            Filters="IsPlayed",
            SortBy="DatePlayed",
            SortOrder="Descending",
            Limit=PLAY_HISTORY_LIMIT,
        )
    elif node == "topsongs":
        base.update(
            IncludeItemTypes="Audio",
            Filters="IsPlayed",
            SortBy="PlayCount",
            SortOrder="Descending",
            Limit=PLAY_HISTORY_LIMIT,
        )
    else:
        return None
    # Boundedness decides the field list: a Limit is what makes the payload
    # per-row cost worth paying (see bounded_fields).
    if media != "music" and "Limit" in base:
        base["Fields"] = bounded_fields()
    return base


def _api() -> Optional[Api]:
    creds = Credentials.load()
    if not creds.is_logged_in:
        return None
    return Api.for_plugin(creds)


Builder = Callable[[Request, Api], None]


def plugin_category(params: dict[str, str]) -> str:
    """The listing title skins show as Container.PluginCategory.

    Estuary (and skins that follow it, Contuary included) hide
    Container.FolderName in the videos window once a content type is set,
    so a plugin listing that does not set this is just "Videos" or "Movies"
    in the header. Structural menus leave content empty on purpose — the
    clicked row's label is the header — and this returns "" there so the
    two do not stack.
    """
    mode = params.get("mode", "")
    if mode == "continuewatching":
        return settings.localized(30049)
    if mode == "nextepisodes":
        return settings.localized(30032)
    if mode == "extras":
        return settings.localized(30500)
    if mode == "search":
        if params.get("person") or params.get("type"):
            import xbmc

            return xbmc.getLocalizedString(137)
        return ""
    if mode not in ("browse", ""):
        return ""

    folder = params.get("folder", "")
    if not folder or folder in _STRUCTURAL_FOLDERS or folder.startswith("tags-"):
        return ""
    if folder in FOLDER_LABELS:
        return node_label(FOLDER_LABELS[folder])
    if folder == "extras":
        return settings.localized(30500)
    if folder.startswith("year-"):
        return folder.split("-", 1)[1]
    if folder.startswith("tag-"):
        return folder.split("-", 1)[1]
    if folder.startswith("alpha-"):
        return folder.split("-", 1)[1]
    if folder.startswith("genre-"):
        return node_label(30036)
    return ""


def set_category(handle: int, category: str) -> None:
    if handle >= 0 and category:
        xbmcplugin.setPluginCategory(handle, category)


def _item_category(media: str, items: list[JsonDict]) -> str:
    """A drill-down's title, from the rows it holds (series/season names
    never travel in the URL)."""
    if not items:
        return ""
    first = items[0]
    if media == "series":
        return str(first.get("SeriesName") or "")
    if media == "season":
        series = first.get("SeriesName") or ""
        season = first.get("SeasonName") or first.get("Name") or ""
        return " / ".join(part for part in (series, season) if part)
    return ""


def listing(request: Request, build: Builder, what: str) -> None:
    """The opening every listing route shares: nothing for a handle-less
    invocation, a failed directory for a logged-out one, and a failed
    directory — rather than a Kodi error dialog — when the server refuses the
    fetch. ``build`` does the route's own work with the Api; the router's
    ``finally`` closes the handle on any other exception.

    The root listing is not one of them on purpose: it tolerates a
    logged-out state (Settings must stay reachable) and treats an
    unavailable view list as a warning, not a failure.
    """
    if request.handle < 0:
        return
    api = _api()
    if api is None:
        xbmcplugin.endOfDirectory(request.handle, succeeded=False)
        return
    try:
        set_category(request.handle, plugin_category(request.params))
        build(request, api)
    except JellyfinError as error:
        LOG.warning("%s failed %s: %s", what, dict(request.params), error)
        _announce_failure(error)
        xbmcplugin.endOfDirectory(request.handle, succeeded=False)


def _announce_failure(error: Exception) -> None:
    """One toast for a listing that failed: the viewer asked for this
    folder, and an empty one says nothing about why."""
    feedback.failed(error)


StructuralRow = tuple[str, str, dict[str, str]]


def structural_row(
    label: str, icon: str, params: dict[str, str], folder: bool = True
) -> tuple[str, xbmcgui.ListItem, bool]:
    """One row that stands for a place to go rather than a piece of media:
    a label, stock art on both keys (:func:`structural_art`), a plugin URL."""
    li = xbmcgui.ListItem(label)
    li.setArt(structural_art(icon))
    return plugin_url(params), li, folder


def structural_rows(
    request: Request, rows: Iterable[StructuralRow], content: str = ""
) -> None:
    """A whole structural menu — the search kinds, the alphabet, a
    library's nodes, its years or tags — from ``(label, icon, params)``
    triples, closed with the empty content type the skins need to draw
    ``setArt(icon)`` instead of watched-status overlays."""
    entries = [structural_row(label, icon, params) for label, icon, params in rows]
    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))
    xbmcplugin.setContent(request.handle, content)
    xbmcplugin.endOfDirectory(request.handle)


def _who_is_watching_label() -> str:
    """Root label reflecting who is on the session: the base 'Who's watching?'
    plus any additional users.

    Read from the window property the service publishes (state.PROP_WHO_NAMES)
    rather than from /Sessions: the service owns every change to the set (the
    picker worker, the connect-time restore) and publishes as it goes, so a
    root render never asks the server. An empty or stale property degrades to
    the base label."""
    names = state.watching_names()
    if not names:
        return settings.localized(30041)
    return settings.localized(30046) % ", ".join(names)


def root(request: Request) -> None:
    if request.handle < 0:
        return
    api = _api()
    entries: list[tuple[str, xbmcgui.ListItem, bool]] = []

    import xbmc

    if api is not None:
        # First, the way the web client leads with it: the one entry that is
        # about what the viewer was in the middle of rather than about where it
        # is filed. Offered without asking the server whether it has anything —
        # every root render would pay for that question, and the answer changes
        # with every playback.
        entries.append(
            structural_row(
                settings.localized(30049),
                node_icon("", "inprogress"),
                {"mode": "continuewatching"},
            )
        )

        # Next up across every shows library, matching the web client's
        # home row. Per-library Next up stays on each shows node menu.
        entries.append(
            structural_row(
                settings.localized(30032),
                node_icon("tvshows", "nextup"),
                {"mode": "nextepisodes"},
            )
        )

        # Search sits with Continue watching and Next up, above the
        # libraries: they are ways in that are not a place, and a viewer
        # who knows what they want should not have to pick a library first.
        entries.append(
            structural_row(
                xbmc.getLocalizedString(137),  # Search
                "DefaultAddonsSearch.png",
                {"mode": "search"},
            )
        )

        try:
            views = api.views().get("Items", [])
        except JellyfinError as error:
            LOG.warning("views unavailable: %s", error)
            views = []
            # The libraries are missing for a reason, and the row says
            # which; it opens the settings, where the Account tab is.
            entries.append(
                structural_row(
                    feedback.message(error),
                    "DefaultIconError.png",
                    {"mode": "settings"},
                )
            )
        for view in views:
            if view.get("CollectionType") == "livetv":
                continue  # live TV is pvr.kofin's job
            collection = _collection_type(view)
            li = listitems.build(view, api.server)
            # Stock Default*.png on icon and thumb (structural_art); server
            # Primary stays on poster for the focus pane (InfoWallThumbVar
            # prefers poster).
            art = listitems.art_for(view, api.server)
            icon = node_icon(collection)
            primary = art.get("thumb") or art.get("poster")
            art["icon"] = icon
            art["thumb"] = icon
            if primary:
                art["poster"] = primary
            li.setArt(with_backdrop(art))
            params = {"mode": "browse", "view": view.get("Id", ""), "type": collection}
            if collection not in NODES:
                params["folder"] = "children"
            entries.append((plugin_url(params), li, True))

    # "Who's watching?" — gone entirely when the Advanced-tab shortlist has
    # nobody on it, which is how the feature is switched off (adduser.py).
    from kofin.service import whoswatching

    if api is not None and whoswatching.is_enabled():
        entries.append(
            structural_row(
                _who_is_watching_label(),
                _addon_media("person-search.png") or "DefaultUser.png",
                {"mode": "adduser"},
                folder=False,
            )
        )

    # SyncPlay root entry: gated on the master toggle, read fresh each
    # listing, and hidden when an external player is configured.
    from kofin.syncplay import offer

    if api is not None and offer.available():
        entries.append(
            structural_row(
                settings.localized(30560),
                _addon_media("syncplay-groups.png") or "DefaultUser.png",
                {"mode": "syncplay"},
                folder=False,
            )
        )
    entries.append(
        structural_row(
            xbmc.getLocalizedString(5),  # "Settings"
            "DefaultAddonService.png",
            {"mode": "settings"},
            folder=False,
        )
    )

    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))
    # Empty content, not "files" (structural_art).
    xbmcplugin.setContent(request.handle, "")
    xbmcplugin.endOfDirectory(request.handle)


def next_episodes(request: Request) -> None:
    """Next-up episodes — one library when ``id`` is set (the generated
    per-library node), every shows library when it is not (the add-on
    root and the Kofin-folder node). Dynamic because no Kodi filter
    expresses "what follows what was watched"."""

    def build(request: Request, api: Api) -> None:
        view_id = request.params.get("id", "")
        items = api.next_up(view_id, bounded_fields()).get("Items", [])
        _add_items(request, api, items, view_id, "tvshows")
        xbmcplugin.setContent(request.handle, "episodes")
        xbmcplugin.endOfDirectory(request.handle)

    listing(request, build, "next episodes")


def continue_watching(request: Request) -> None:
    """In-progress items across every library (mode=continuewatching).

    A live listing, like the extras node: nothing is written and nothing is
    cached, because a resume point is exactly the thing that has changed by the
    time the viewer comes back to it. The per-library "In progress" nodes ask
    /Items for one library's resumable items; this asks the server for the list
    it already keeps, so the entries and their order are the ones the web
    client shows.

    No sort methods are offered. The server hands these back most recently
    played first, which is the whole point of the listing -- letting Kodi sort
    them by title would throw that away.
    """

    def build(request: Request, api: Api) -> None:
        items = api.resume(bounded_fields()).get("Items", [])
        _add_items(request, api, items, "", "")
        # Movies and episodes in one listing: "videos" is the content type
        # that describes both, and the items carry their own media type for
        # the skin.
        xbmcplugin.setContent(request.handle, "videos")
        xbmcplugin.endOfDirectory(request.handle)

    listing(request, build, "continue watching")


def browse(request: Request) -> None:
    listing(request, _browse, "browse")


def _browse(request: Request, api: Api) -> None:
    view_id = request.params.get("view", "")
    media = request.params.get("type", "")
    folder = request.params.get("folder", "")

    if not folder and media in NODES:
        _node_menu(request, api, media, view_id)
        return
    if folder == "alpha":
        _alpha_menu(request, media, view_id)
        return
    if folder in ("years", "tags"):
        _filter_menu(request, api, media, view_id, folder)
        return
    if folder.startswith("tags-"):
        _tag_menu(request, api, media, view_id, folder.split("-", 1)[1])
        return
    if folder == "favorites" and media == "tvshows":
        _favorites_menu(request, api, view_id)
        return
    if folder == "extras" and media == "tvshows":
        _extras_node(request, api, view_id)
        return
    items, content = _list_items(api, media, folder or "children", view_id, request)
    derived = _item_category(media, items)
    if derived:
        set_category(request.handle, derived)

    _add_items(request, api, items, view_id, media)
    if media in ("series", "season"):
        _append_extras_entry(request, api, folder)
    xbmcplugin.setContent(request.handle, content)
    for method in (
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL,
        xbmcplugin.SORT_METHOD_VIDEO_YEAR,
        xbmcplugin.SORT_METHOD_DATEADDED,
    ):
        xbmcplugin.addSortMethod(request.handle, method)
    xbmcplugin.endOfDirectory(request.handle)


def search(request: Request) -> None:
    """Search the server (mode=search).

    Three shapes, one route:

    * no ``type`` — the menu of what can be searched. It asks nothing, so it
      is safe as a library node, a widget or a favourite.
    * ``type`` with no ``query`` — asks for the term, then lists the results.
      The keyboard is a modal, and a modal fights a directory fetch, so *this*
      shape is the one that must not be a node.
    * ``type`` and ``query`` — lists results with nothing to answer. This is
      what lets a skin's own search box address kofin directly, and it is why
      the term is a parameter rather than only a prompt.

    ``person`` replaces both and lists everything one person appears in, which
    is where a result from the Actors leg leads.
    """
    listing(request, _search, "search")


def _search(request: Request, api: Api) -> None:
    person_id = request.params.get("person", "")
    if person_id:
        _search_person_items(request, api, person_id)
        return

    kind = request.params.get("type", "")
    if kind not in SEARCH_KINDS:
        _search_menu(request)
        return

    query = request.params.get("query", "") or _ask_for_query(kind)
    if not query:
        # Cancelled at the keyboard. A failed fetch is what returns the
        # viewer to where they were; an empty listing would strand them in a
        # results screen they did not ask for.
        xbmcplugin.endOfDirectory(request.handle, succeeded=False)
        return

    if kind == "people":
        items = api.persons(query, SEARCH_LIMIT).get("Items", [])
        _add_person_items(request, api, items)
        xbmcplugin.setContent(request.handle, "")
        xbmcplugin.endOfDirectory(request.handle)
        return
    items = api.items(_search_query(kind, query)).get("Items", [])

    _add_items(request, api, items, "", "")
    xbmcplugin.setContent(request.handle, SEARCH_KINDS[kind][2])
    for method in (
        xbmcplugin.SORT_METHOD_UNSORTED,
        xbmcplugin.SORT_METHOD_LABEL,
        xbmcplugin.SORT_METHOD_VIDEO_YEAR,
    ):
        xbmcplugin.addSortMethod(request.handle, method)
    xbmcplugin.endOfDirectory(request.handle)


def _search_menu(request: Request) -> None:
    """What can be searched. One row per kind, none of which asks anything."""
    import xbmc

    structural_rows(
        request,
        [
            (
                xbmc.getLocalizedString(label_id),
                SEARCH_ICONS[kind],
                {"mode": "search", "type": kind},
            )
            for kind, (label_id, _types, _content) in SEARCH_KINDS.items()
        ],
    )


def _ask_for_query(kind: str) -> str:
    """The search term, from the viewer. Empty when they backed out."""
    import xbmc

    heading = "%s: %s" % (
        xbmc.getLocalizedString(137),  # Search
        xbmc.getLocalizedString(SEARCH_KINDS[kind][0]),
    )
    return xbmcgui.Dialog().input(heading, type=xbmcgui.INPUT_ALPHANUM).strip()


def _search_query(kind: str, query: str) -> JsonDict:
    """The /Items query for one search kind.

    Bounded by SEARCH_LIMIT, so it takes the bounded field list — cast
    included when the viewer asked for it. Stream details ride along for the
    same reason every other bounded listing carries them.
    """
    return {
        "searchTerm": query,
        "IncludeItemTypes": SEARCH_KINDS[kind][1],
        "Recursive": True,
        "Fields": bounded_fields(),
        "ImageTypeLimit": 1,
        "Limit": SEARCH_LIMIT,
    }


def _search_person_items(request: Request, api: Api, person_id: str) -> None:
    """Everything one person appears in."""
    try:
        items = api.items(
            {
                "PersonIds": person_id,
                "Recursive": True,
                "IncludeItemTypes": "Movie,Series,Episode",
                "Fields": bounded_fields(),
                "ImageTypeLimit": 1,
                # Newest first, so what SEARCH_LIMIT leaves out is the oldest
                # credits rather than a series lead's latest work.
                "SortBy": "PremiereDate,SortName",
                "SortOrder": "Descending,Ascending",
                "Limit": SEARCH_LIMIT,
            }
        ).get("Items", [])
    except JellyfinError as error:
        LOG.warning("person listing failed (%s): %s", person_id, error)
        _announce_failure(error)
        xbmcplugin.endOfDirectory(request.handle, succeeded=False)
        return

    _add_items(request, api, items, "", "")
    xbmcplugin.setContent(request.handle, "videos")
    xbmcplugin.endOfDirectory(request.handle)


def _add_person_items(request: Request, api: Api, items: list[JsonDict]) -> None:
    """People as folders leading to their own filmography.

    Built here rather than through :func:`_add_items`, which would give a
    person a playable path.
    """
    entries = []
    for item in items:
        li = listitems.build(item, api.server)
        if not li.getArt("thumb"):
            li.setArt(structural_art("DefaultActor.png"))
        path = plugin_url({"mode": "search", "person": item.get("Id", "")})
        entries.append((path, li, True))
    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))


def extras(request: Request) -> None:
    """Special features of a series/season (mode=extras) — a live listing
    over the SpecialFeatures endpoint."""

    def build(request: Request, api: Api) -> None:
        items = api.special_features(request.params.get("id", ""))
        _add_items(request, api, items, "", "")
        xbmcplugin.setContent(request.handle, "videos")
        xbmcplugin.endOfDirectory(request.handle)

    listing(request, build, "extras listing")


def _alpha_menu(request: Request, media: str, view_id: str) -> None:
    """The alphabet. Letters are letters, so no server call and no strings."""
    icon = node_icon(media, "alpha")
    structural_rows(
        request,
        [
            (letter, icon, _folder_params(view_id, media, "alpha-%s" % letter))
            for letter in ALPHABET
        ],
    )


def _tag_letters(request: Request, media: str, view_id: str, values: list[Any]) -> None:
    """The initials a library's tags actually use, for a tag list too long to
    show flat. Only letters with tags behind them, so no empty rows."""
    letters = sorted({str(v)[:1].upper() or "#" for v in values})
    icon = node_icon(media, "tags")
    structural_rows(
        request,
        [
            (letter, icon, _folder_params(view_id, media, "tags-%s" % letter))
            for letter in letters
        ],
    )


def _tag_menu(
    request: Request, api: Api, media: str, view_id: str, letter: str
) -> None:
    """One letter's worth of tags."""
    values = api.filters(view_id, ITEM_TYPES.get(media, "")).get("Tags") or []
    wanted = sorted(v for v in values if str(v)[:1].upper() == letter.upper())
    icon = node_icon(media, "tags")
    structural_rows(
        request,
        [
            (str(value), icon, _folder_params(view_id, media, "tag-%s" % value))
            for value in wanted
        ],
    )


def _filter_menu(
    request: Request, api: Api, media: str, view_id: str, kind: str
) -> None:
    """Years or tags for one library, from the server's own filter list.

    One call answers both — /Items/Filters returns Years, Tags, Genres and
    OfficialRatings together — so the menu is what the library actually holds
    rather than a fixed range.
    """
    values = (
        api.filters(view_id, ITEM_TYPES.get(media, "")).get(
            "Years" if kind == "years" else "Tags"
        )
        or []
    )
    if kind == "years":
        # Newest first: a year list that opens at 1918 is a list nobody wants
        # to page to the end of.
        values = sorted(values, reverse=True)
    elif len(values) > TAG_MENU_MAX:
        # Every row is a ListItem in the plugin process, so past the threshold
        # the letters come first and the tags sit under them.
        _tag_letters(request, media, view_id, values)
        return
    icon = node_icon(media, kind)
    prefix = "year" if kind == "years" else "tag"
    structural_rows(
        request,
        [
            (
                str(value),
                icon,
                _folder_params(view_id, media, "%s-%s" % (prefix, value)),
            )
            for value in values
        ],
    )


def _folder_params(view_id: str, media: str, folder: str) -> dict[str, str]:
    """The browse URL for one node of one library — the shape every
    structural menu row links to."""
    return {"mode": "browse", "view": view_id, "type": media, "folder": folder}


def _node_menu(request: Request, api: Api, media: str, view_id: str) -> None:
    nodes = list(NODES[media])
    if media == "tvshows":
        if not _view_has_favorites(api, view_id):
            nodes = [(key, label_id) for key, label_id in nodes if key != "favorites"]
        if _view_has_specials(api, view_id):
            nodes.append(("extras", 30500))
    structural_rows(
        request,
        [
            (
                node_label(label_id),
                node_icon(media, key),
                _folder_params(view_id, media, key),
            )
            for key, label_id in nodes
        ],
    )


def _extras_node(request: Request, api: Api, view_id: str) -> None:
    """The Extras node: series in the view that advertise special features,
    each opening its extras listing."""
    result = api.items(
        {
            "ParentId": view_id,
            "IncludeItemTypes": "Series",
            "Recursive": True,
            "Fields": BROWSE_FIELDS + ",SpecialFeatureCount",
            "SortBy": "SortName",
            "SortOrder": "Ascending",
        }
    )
    entries = []
    resume_offset = settings.resume_offset()
    for item in specials_only(result.get("Items", [])):
        # No apply_backdrop: these are series rows, and a media row keeps
        # whatever backdrop the server gave it or none (MEDIA_TYPES).
        li = listitems.build(item, api.server, resume_offset=resume_offset)
        path = plugin_url({"mode": "extras", "id": item.get("Id", "")})
        entries.append((path, li, True))
    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))
    xbmcplugin.setContent(request.handle, "tvshows")
    xbmcplugin.endOfDirectory(request.handle)


def specials_only(items: list[JsonDict]) -> list[JsonDict]:
    """The items that actually carry special features.

    Filtered here rather than by the server: ``HasSpecialFeature=true``
    matches no series on 10.11. SpecialFeatureCount agrees with the listing
    the entry opens.
    """
    return [item for item in items if item.get("SpecialFeatureCount")]


def _favorites_menu(request: Request, api: Api, view_id: str) -> None:
    """Favourites under a show library: favorite shows and favorite episodes.

    Each leg is omitted when it has nothing, so a library with only
    favourite episodes does not offer an empty Favorite shows row.
    """
    structural_rows(
        request,
        [
            (
                node_label(label_id),
                node_icon("tvshows", key),
                _folder_params(view_id, "tvshows", key),
            )
            for key, label_id, item_type in TV_FAVORITE_LEGS
            if _view_has_favorites(api, view_id, item_type)
        ],
    )


def _view_has_favorites(
    api: Api, view_id: str, item_types: str = "Series,Episode"
) -> bool:
    """Whether this view has any favourite series or episodes (gates the node).

    Limit=1, no images, no userdata: the menu only needs existence. IsFavorite
    works here, unlike HasSpecialFeature on series (see specials_only).
    """
    try:
        result = api.items(
            {
                "ParentId": view_id,
                "IncludeItemTypes": item_types,
                "Recursive": True,
                "Filters": "IsFavorite",
                "Limit": 1,
                "EnableImages": False,
                "EnableUserData": False,
            }
        )
    except JellyfinError:
        return False
    return bool(result.get("Items"))


def _view_has_specials(api: Api, view_id: str) -> bool:
    """Whether any series in the view has special features (gates the node)."""
    try:
        result = api.items(
            {
                "ParentId": view_id,
                "IncludeItemTypes": "Series",
                "Recursive": True,
                # Just the counts: no artwork, no userdata.
                "Fields": "SpecialFeatureCount",
                "EnableImages": False,
                "EnableUserData": False,
            }
        )
    except JellyfinError:
        return False
    return bool(specials_only(result.get("Items", [])))


def _append_extras_entry(request: Request, api: Api, item_id: str) -> None:
    """An Extras entry at the end of a series/season drill-down when its DTO
    reports special features."""
    try:
        count = api.item(item_id).get("SpecialFeatureCount") or 0
    except JellyfinError:
        return
    if not count:
        return
    row = structural_row(
        settings.localized(30500), "DefaultVideo.png", {"mode": "extras", "id": item_id}
    )
    xbmcplugin.addDirectoryItems(request.handle, [row], 1)


def _list_items(
    api: Api, media: str, folder: str, view_id: str, request: Request
) -> tuple[list[JsonDict], str]:
    """Fetch the item list for a folder; returns (items, kodi content type)."""
    # Special routes first.
    if folder == "nextup":
        result = api.next_up(view_id, bounded_fields())
        return result.get("Items", []), "episodes"
    if folder == "recentalbums":
        # Latest, not a sort: an album's DateCreated is when the server's
        # scanner last created its row, so the node asks /Items/Latest, which
        # sorts the songs and groups them by album, as the web client does.
        return api.latest(view_id, "Audio", BROWSE_FIELDS, RECENT_LIMIT), "albums"
    if folder == "genres":
        # Empty content, like the node menu above it (structural_art).
        result = api.genres(view_id, ITEM_TYPES.get(media, ""))
        return result.get("Items", []), ""
    if folder == "artists":
        result = api.artists(view_id)
        return result.get("Items", []), "artists"
    if folder == "albumartists":
        result = api.album_artists(view_id)
        return result.get("Items", []), "artists"

    query = node_query(media, folder, view_id)
    if query is not None:
        content = _node_content(media, folder)
        return api.items(query).get("Items", []), content

    # Drill-down into a concrete item id.
    item_type = media  # for drill-down paths, `type` carries the item type
    if item_type == "series":
        return api.seasons(folder).get("Items", []), "seasons"
    if item_type == "season":
        series = request.params.get("series", "")
        return (
            api.episodes(series, folder, bounded_fields()).get("Items", []),
            "episodes",
        )
    if item_type == "musicartist":
        result = api.items(
            {
                "ArtistIds": folder,
                "IncludeItemTypes": "MusicAlbum",
                "Recursive": True,
                "Fields": BROWSE_FIELDS,
                "SortBy": "ProductionYear,SortName",
            }
        )
        return result.get("Items", []), "albums"
    if item_type == "musicalbum":
        result = api.items(
            {
                "ParentId": folder,
                "Fields": BROWSE_FIELDS,
                "SortBy": "ParentIndexNumber,IndexNumber,SortName",
            }
        )
        return result.get("Items", []), "songs"
    if item_type == "playlist":
        # /Items answers a playlist's items once each, in the order SortBy
        # names; the playlist's own route answers its entries in its order,
        # an item added twice included.
        entries = list(
            paged(
                lambda start, limit: api.playlist_items(
                    folder, start_index=start, limit=limit, fields=BROWSE_FIELDS
                ),
                PLAYLIST_PAGE,
                dedupe=False,
                what="playlist %s" % folder,
            )
        )
        return entries, _guess_content(entries)

    # Generic container (boxset, folder, photo album, view children).
    parent = folder if folder != "children" else view_id
    result = api.items(
        {"ParentId": parent, "Fields": BROWSE_FIELDS, "SortBy": "SortName"}
    )
    items = result.get("Items", [])
    content = "movies" if item_type == "boxset" else _guess_content(items)
    return items, content


def _add_items(
    request: Request, api: Api, items: list[JsonDict], view_id: str, media: str
) -> None:
    entries = []
    # One settings read for the whole listing (resume_of).
    resume_offset = settings.resume_offset()
    for item in items:
        li = listitems.build(item, api.server, resume_offset=resume_offset)
        if not is_media_row(item):
            apply_backdrop(li)
        item_type = item.get("Type", "")

        if item_type in ("Genre", "MusicGenre"):
            if not li.getArt("thumb"):
                li.setArt(structural_art("DefaultGenre.png"))
            path = plugin_url(
                {
                    "mode": "browse",
                    "view": view_id,
                    "type": media,
                    "folder": "genre-%s" % item.get("Id", ""),
                }
            )
            entries.append((path, li, True))
            continue

        if item_type == "Playlist":
            # A playlist is a place, not a piece of media: the stock glyph on
            # icon and thumb for the list (structural_art), the server's own
            # art kept on poster for the focus pane.
            art = listitems.art_for(item, api.server)
            primary = art.get("thumb") or art.get("poster")
            icon = (
                "DefaultMusicPlaylists.png"
                if item.get("MediaType") == "Audio"
                else "DefaultVideoPlaylists.png"
            )
            art["icon"] = icon
            art["thumb"] = icon
            if primary:
                art["poster"] = primary
            li.setArt(with_backdrop(art))
            entries.append((listitems.path_for(item), li, True))
            continue

        if item_type == "Photo":
            tags = item.get("ImageTags") or {}
            path = api.image_url(item.get("Id", ""), "Primary", tags.get("Primary", ""))
            entries.append((path, li, False))
            continue

        path = listitems.path_for(item)
        if item_type == "Season":
            path = plugin_url(
                {
                    "mode": "browse",
                    "folder": item.get("Id", ""),
                    "type": "season",
                    "series": item.get("SeriesId", ""),
                }
            )
        # No addContextMenuItems: Kodi pins a listing's own entries above its
        # Play, so server-side actions live in plugin/context.py.
        entries.append((path, li, listitems.is_folder(item)))

    xbmcplugin.addDirectoryItems(request.handle, entries, len(entries))


def _node_content(media: str, node: str) -> str:
    if node in ("recentepisodes", "inprogressepisodes", "nextup", "favoriteepisodes"):
        return "episodes"
    if node in ("albums", "recentalbums", "favoritealbums"):
        return "albums"
    if node in ("lastplayed", "topsongs"):
        return "songs"
    if node == "sets":
        return "movies"
    if node.startswith("alpha-") and media == "music":
        # An alphabet leg over music lists artists, not the albums the rest of
        # the music tree is made of (node_query switches the item type too).
        return "artists"
    return CONTENT_TYPES.get(media, "videos")


def _guess_content(items: list[JsonDict]) -> str:
    for item in items:
        content = {
            "Movie": "movies",
            "Series": "tvshows",
            "Episode": "episodes",
            "Audio": "songs",
            "MusicAlbum": "albums",
            "Photo": "images",
            "PhotoAlbum": "images",
        }.get(item.get("Type", ""))
        if content:
            return content
    # Playlists alone take empty content (structural_art). Checked after the
    # loop so a listing that merely *holds* a playlist beside real media still
    # describes the media.
    if items and all(item.get("Type") == "Playlist" for item in items):
        return ""
    return "videos"
