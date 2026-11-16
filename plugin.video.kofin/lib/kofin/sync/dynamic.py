"""Skin entries and node trees from the server's views and the native selection.

Every server view is a ``Kofin.nodes.*`` entry. A whitelisted video library
gets the generated node tree under ``special://profile/library/video/kofin/``
(``nodes/video.write_tree``) and ``library://`` paths in its properties, and
everything else is a dynamic ``browse`` entry. The tree's filter nodes select
by the folder the library's rows are filed under (``paths.library_dir``): a
movie's folder or an episode's show folder is below it, and Kodi files the row
on that path because its URL has a query (``CVideoDatabase::SplitPath``). A
whitelisted music library gets a folder in the music tree
(``nodes/music.write_music_nodes``), whose nodes filter on the folder the
library's songs are filed under; its skin entry is Kodi's music root. The
folder's path is what the Manage menu reads a library's downloads from
(``plugin/context.py``).

Ownership is the ``kofin`` name prefix throughout (``nodes/fs.py``): a tree
rewrite reconciles the folder against what it wrote and never touches a
hand-made node beside it, and an empty whitelist takes the whole tree down.

One setting switches the generated presentation as a whole (``SETTING``):
the tree, the smart playlists beside it and the Jellyfin playlists
(``backends/api/playlists.py`` reads the same switch). Off, the files Kofin
wrote go the way an empty whitelist takes them and a synced video library is
published as a browse entry, like an unsynced one; Kodi's own library and the
rows in it are untouched.

Kodi's shipped video nodes are seeded into the profile before the tree is
written (``kodisetup.seed_default_nodes``): the moment
``special://profile/library/video/`` exists, every ``library://video/...``
path resolves there and nowhere else (CLibraryDirectory::GetDirectory, no
merge), so a profile holding only ``kofin/`` lists nothing for
``library://video/movies/`` and a skin's categories row goes empty. The
music tree gets Kodi's shipped music nodes the same way.
"""

import re
from collections.abc import Collection, Iterable
from typing import TYPE_CHECKING, Any, NamedTuple, Optional

import xbmcaddon

from kofin.core import settings
from kofin.core.log import Logger
from kofin.sync import kodisetup, playlists, private
from kofin.sync.backends.api import capabilities
from kofin.sync.nodes import music as music_nodes
from kofin.sync.nodes import props, video

if TYPE_CHECKING:
    from kofin.core.api import Api

LOG = Logger(__name__)

SETTING = "libraryNodes"

# How Jellyfin spells an item id. A library's id names its node folders and
# its smart playlist, so a view the server names any other way is left out.
LIBRARY_ID = re.compile(r"[0-9a-f]{32}")


class View(NamedTuple):
    view_id: str
    view_name: str
    media_type: str


def node_entries(
    views: list[View], whitelist: list[str], key: str
) -> list[tuple[dict, bool]]:
    """The whitelist as the tree writer wants it: ``(view, mixed)`` pairs in
    tree order, a mixed library split into its two kinds, movies before
    shows before music videos and the server's order within a kind. Each
    names the folder its rows are filed under in ``Path``; ``key`` is the
    catalogue's (``login_key``)."""
    from kofin.sync.backends.api import paths

    order = [v.view_id for v in views]
    entries = []
    for view in views:
        if view.view_id not in whitelist:
            continue
        node = {"Id": view.view_id, "Name": view.view_name, "Media": view.media_type}
        if view.media_type == "mixed":
            for media in ("movies", "tvshows"):
                entries.append(
                    (
                        dict(
                            node,
                            Media=media,
                            Path=paths.library_dir(key, view.view_id, media),
                        ),
                        True,
                    )
                )
        elif view.media_type in video.NODES:
            node["Path"] = paths.library_dir(key, view.view_id, view.media_type)
            entries.append((node, False))
    entries.sort(
        key=lambda entry: (
            video.MEDIA_RANK.get(entry[0]["Media"], len(video.MEDIA_RANK)),
            entry[0]["Media"],
            order.index(entry[0]["Id"]),
            entry[0]["Name"],
        )
    )
    return entries


def _answering() -> Optional[xbmcaddon.Addon]:
    """This add-on's Addon while its settings answer, or None.

    A store Kodi has unregistered and a settings document that did not load
    both read every string blank and a boolean as its default, so only a
    store that answered can mean a logout or a switch turned off. The second
    is told by ``deviceId``, which is never empty once a login has happened
    (the applier's LOAD_CANARY). Every value is read off the one Addon, as
    Credentials.load reads its record."""
    addon = settings.get_addon()
    if addon is None or not addon.getSetting("deviceId"):
        return None
    return addon


def login_key() -> Optional[str]:
    """The catalogue's key for the logged-in user, which every path the
    node trees filter on starts with; "" with no login, and None while the
    settings cannot say who is logged in (``_answering``), since an empty
    tree deletes files."""
    from kofin.sync.backends.api.store import namespace

    addon = _answering()
    if addon is None:
        return None
    try:
        return str(namespace(addon.getSetting("serverId"), addon.getSetting("userId")))
    except ValueError:
        return ""


def music_entries(
    views: list[View], whitelist: list[str], key: Optional[str]
) -> Optional[list[dict]]:
    """The whitelisted music libraries as the music tree wants them, in the
    server's order, each with the folder its songs are filed under. None
    while ``key`` is (``login_key``), since an empty list deletes the
    tree."""
    from kofin.sync.backends.api import paths

    if key is None:
        return None
    music = [v for v in views if v.media_type == "music" and v.view_id in whitelist]
    if not music or not key:
        return []
    return [
        {
            "Id": view.view_id,
            "Name": view.view_name,
            "Path": paths.library_dir(key, view.view_id, "music"),
        }
        for view in music
    ]


def wanted() -> Optional[bool]:
    """Whether the generated presentation is on (``SETTING``), and None
    while the settings cannot say: a store that did not answer
    (``_answering``) or a value that is neither, as from a build without the
    setting. On None nothing is written and nothing taken down."""
    addon = _answering()
    if addon is None:
        return None
    try:
        value = addon.getSetting(SETTING).strip().lower()
    except TypeError:
        return None
    if value in ("true", "false"):
        return value == "true"
    return None


def publish_from(api: "Api") -> None:
    """Publish the server's libraries as the user has them: every synced
    one, hidden from My Media or grouped into a combined view or not, and of
    the rest those Jellyfin's home screen shows."""
    from kofin.core.api import library_folders
    from kofin.core.http import JellyfinError

    every = api.views(include_hidden=True).get("Items", [])
    shown = {item.get("Id") for item in api.views().get("Items", [])}
    listed = {item.get("Id") for item in every}
    whitelist = [
        x.replace("Mixed:", "") for x in (private.get_sync().get("Whitelist") or [])
    ]
    grouped, unread = library_folders(api, [i for i in whitelist if i not in listed])
    if unread:
        # The writers delete every node folder they do not write, and nothing
        # republishes before the next publish_from: a synced library the
        # server could not answer for keeps the tree it has.
        raise JellyfinError("synced libraries not read: %s" % ", ".join(unread))
    every = every + grouped
    publish(every, api, hidden={item.get("Id") for item in every} - shown)


def publish(
    items: Iterable[dict[str, Any]],
    server: "Api",
    hidden: Collection[str] = frozenset(),
) -> None:
    """``hidden`` names the libraries the user hid from My Media: one that is
    not synced is left out of the entries, as Jellyfin leaves it out."""
    whitelist = [
        x.replace("Mixed:", "") for x in (private.get_sync().get("Whitelist") or [])
    ]
    items = [i for i in items if i.get("Id") not in hidden or i["Id"] in whitelist]
    views: list[View] = []
    for item in items:
        library, media = item.get("Id"), item.get("CollectionType") or "mixed"
        if not library or media == "livetv":
            continue
        if not LIBRARY_ID.fullmatch(str(library)):
            LOG.warning("library %r left out: its id is not an item id", library)
            continue
        views.append(View(library, item.get("Name", ""), media))
    nodes = wanted()
    key: Optional[str] = None
    if nodes is not None:
        key = login_key() if nodes else ""
    entries = node_entries(views, whitelist, key) if nodes and key else []
    singles: list[dict] = []
    try:
        if key is None:
            LOG.debug("settings unreadable; video node tree left as it is")
            # The skin entries describe the tree as it stands.
            nodes = video.tree_written()
            singles = video.written_singles()
        elif entries:
            kodisetup.seed_default_nodes("video")
            singles = video.single_nodes(capabilities.has("episode_tags"))
            video.write_tree(entries, singles)
            playlists.write_video_playlists(entries)
        else:
            video.delete_tree()
            playlists.remove_video_playlists()
    except Exception:
        # The tree is presentation; the properties below still publish.
        LOG.exception("library node tree not written")
        singles = []
    try:
        libraries = music_entries(views, whitelist, key)
        if libraries is None:
            LOG.debug("settings unreadable; music node tree left as it is")
        else:
            if libraries:
                kodisetup.seed_default_nodes("music")
            music_nodes.write_music_nodes(libraries)
    except Exception:
        LOG.exception("music node tree not written")
    if not nodes:
        # Without the tree a synced video library has no node to point at,
        # so its entries are browse entries; a synced music library keeps
        # Kodi's music root, which is Kodi's, not a file of ours.
        music = {v.view_id for v in views if v.media_type == "music"}
        whitelist = [x for x in whitelist if x in music]
    props.publish(
        views,
        {"Whitelist": whitelist, "SortedViews": [v.view_id for v in views]},
        singles,
        items,
        server,
    )
