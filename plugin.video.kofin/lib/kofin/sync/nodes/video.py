"""The generated video node tree: a ``Kofin`` folder in Kodi's video
library holding one folder per synced library and a few single nodes.

Every file is written whole on every pass. Nothing under the tree is the
user's to keep except the parent's own ``index.xml`` (its order and label),
which stays creation-only; the per-library ``index.xml`` restates what the
server says about the library and is rewritten like the rest.

Structural entries carry Kodi's stock icon names (Default*.png) so every
skin substitutes its own artwork; the two exceptions (the parent, the
Downloaded singles) are the addon itself and have nothing to substitute.
"""

import os
import xml.etree.ElementTree as etree
from collections.abc import Iterable
from typing import Any, Optional, Union

import xbmc
import xbmcvfs

from kofin.core import settings
from kofin.core.log import Logger
from kofin.core.urls import plugin_url
from kofin.sync.nodes import fs

LOG = Logger(__name__)

# Every generated node lives under one folder in the video library root, so
# Kodi shows a single "Kofin" entry instead of one per synced library. The
# folder name is the prefix every managed name carries.
NODE_ROOT = fs.PREFIX


# Kind ordering for the generated library nodes, following Kodi's own
# top-level video ordering (movies 10, tvshows 20, musicvideos 30). Libraries
# of one kind sit together (dynamic.node_entries).
MEDIA_RANK = {
    "movies": 0,
    "tvshows": 1,
    "musicvideos": 2,
    "homevideos": 3,
    "episodes": 4,
}

# Order of the "Kofin" parent among Kodi's own top-level video nodes (movies
# 10, tvshows 20, musicvideos 30).
NODE_ROOT_ORDER = 15

# The one structural entry that is allowed addon art: this node *is* the
# addon, so a skin has nothing of its own to substitute. Kodi resolves
# special:// for textures (URIUtils::IsHD translates it), so the path stays
# valid wherever the addon is installed.
NODE_ROOT_ICON = (
    "special://home/addons/plugin.video.kofin/resources/media/kofin-node.png"
)

# The other allowed exception, for the same reason: a Downloaded node has no
# Kodi-native counterpart for a skin to substitute artwork for.
NODE_DOWNLOADS_ICON = (
    "special://home/addons/plugin.video.kofin/resources/media/downloaded.png"
)

# (node key, label) per library kind. Ints are Kodi-core string ids that node
# XML resolves natively; ours (30xxx) are resolved at generation time.
NODES = {
    "tvshows": [
        ("all", None),
        ("recent", 30350),
        ("recentepisodes", 30355),
        ("inprogress", 30351),
        ("inprogressepisodes", 30356),
        ("genres", 135),
        ("random", 30353),
        ("recommended", 30354),
    ],
    "movies": [
        ("all", None),
        ("recent", 30350),
        ("inprogress", 30351),
        ("unwatched", 30352),
        ("sets", 20434),
        ("genres", 135),
        ("random", 30353),
        ("recommended", 30354),
    ],
    "musicvideos": [
        ("all", None),
        ("recent", 30350),
        ("inprogress", 30351),
        ("unwatched", 30352),
    ],
}

# What each filter node carries after its path rule, in the order the file
# is written. ("order", by, direction) / ("limit",) / ("group", name) /
# ("rule", field, operator, value-or-None). The two episode-level nodes of a
# show library list episodes rather than shows.
NODE_PARTS = {
    "all": (("order", "sorttitle", "ascending"),),
    "recent": (
        ("order", "dateadded", "descending"),
        ("limit",),
        ("rule", "playcount", "is", "0"),
    ),
    "inprogress": (("rule", "inprogress", "true", None), ("limit",)),
    "unwatched": (
        ("order", "sorttitle", "ascending"),
        ("rule", "playcount", "is", "0"),
    ),
    "sets": (("order", "sorttitle", "ascending"), ("group", "sets")),
    "genres": (("order", "sorttitle", "ascending"), ("group", "genres")),
    "random": (("order", "random", "ascending"), ("limit",)),
    "recommended": (
        ("order", "rating", "descending"),
        ("limit",),
        ("rule", "playcount", "is", "0"),
        ("rule", "rating", "greaterthan", "7"),
    ),
    "recentepisodes": (
        ("order", "dateadded", "descending"),
        ("limit",),
        ("rule", "playcount", "is", "0"),
    ),
    "inprogressepisodes": (("limit",), ("rule", "inprogress", "true", None)),
}
EPISODE_CONTENT = ("recentepisodes", "inprogressepisodes")

# Rows a node lists at most, where it lists a selection.
LIMIT = 25

# Stock Kodi icon per media type (structural entries never carry addon or
# server art).
MEDIA_ICONS = {
    "movies": "DefaultMovies.png",
    "tvshows": "DefaultTVShows.png",
    "musicvideos": "DefaultMusicVideos.png",
    "episodes": "DefaultTVShows.png",
    "music": "DefaultMusicAlbums.png",
}
NODE_ICONS: dict[str, Union[str, dict[str, str]]] = {
    "recent": {
        "movies": "DefaultRecentlyAddedMovies.png",
        "tvshows": "DefaultRecentlyAddedEpisodes.png",
        "musicvideos": "DefaultRecentlyAddedMusicVideos.png",
    },
    "recentepisodes": "DefaultRecentlyAddedEpisodes.png",
    "inprogress": "DefaultInProgressShows.png",
    "inprogressepisodes": "DefaultInProgressShows.png",
    "genres": "DefaultGenre.png",
    "sets": "DefaultSets.png",
    "favorites": "DefaultFavourites.png",
}


def node_icon(media: str, node: Optional[str] = None) -> str:
    found = NODE_ICONS.get(node or "")
    icon = found.get(media) if isinstance(found, dict) else found
    return icon or MEDIA_ICONS.get(media, "DefaultVideo.png")


def _label(value: Union[int, str, None], fallback: str = "") -> str:
    if isinstance(value, int):
        return (
            settings.localized(value)
            if value >= 30000
            else xbmc.getLocalizedString(value)
        )
    return value or fallback


def _node_label(value: Union[int, str, None], fallback: str = "") -> str:
    """``<label>`` text for a node file.

    Kodi resolves a *numeric* node label against its own strings
    (``CGUIControlFactory::FilterLabel``, from ``CLibraryDirectory``), where
    the 30000+ addon range is empty -- a bare ``30350`` renders blank in the
    library and in the node editor. Ours therefore go in as text; Kodi-core
    ids stay numeric so they keep following the UI language.
    """
    if isinstance(value, int):
        return settings.localized(value) if value >= 30000 else str(value)
    return value or fallback


def set_node_icon(xml: etree.Element, icon: str) -> None:
    """Set (or add) a node's ``<icon>``, keeping it before the other
    children the way Kodi's own node files write it."""
    element = xml.find("icon")
    if element is None:
        element = etree.Element("icon")
        xml.insert(0, element)
    element.text = icon


def write_xml(file: str, element: etree.Element) -> None:
    etree.ElementTree(element).write(file)


# --- paths ---------------------------------------------------------------------


def node_root_path() -> str:
    """Directory holding every generated video node."""
    return os.path.join(
        xbmcvfs.translatePath("special://profile/library/video"), NODE_ROOT
    )


def node_folder(view: dict[str, Any]) -> str:
    """Per-library folder name inside :data:`NODE_ROOT`."""
    return "%s%s%s" % (fs.PREFIX, view["Media"], view["Id"])


def single_file(single: dict[str, Any]) -> str:
    """A single node's file name. ``File`` names it when the tag cannot:
    the two Downloads singles share one tag and would otherwise collide."""
    name = single.get("File") or single["Tag"].replace(" ", "")
    return "%s_%s.xml" % (fs.PREFIX, name)


def library_node_path(view: dict[str, Any], node: str) -> str:
    return "library://video/%s/%s/%s.xml" % (NODE_ROOT, node_folder(view), node)


def single_node_path(single: dict[str, Any]) -> str:
    return "library://video/%s/%s" % (NODE_ROOT, single_file(single))


def browse_url(view: dict[str, Any], node: Optional[str] = None) -> str:
    params = {"mode": "browse", "type": view["Media"]}

    if view.get("Id"):
        params["view"] = view["Id"]

    if node:
        params["folder"] = node

    return plugin_url(params)


# --- what goes in the tree ------------------------------------------------------


def single_nodes(
    episode_tags: bool = True, downloads: Optional[bool] = None
) -> list[dict[str, Any]]:
    """The tag-filtered singles beside the library nodes: the favorites
    for movies and shows always, for episodes while this Kodi keeps an
    episode's tags (``episode_tags``: a tag rule lists nothing on a Kodi
    without it), the Downloads set while the feature is on (``downloads``,
    read from the settings when None), its episodes on the same condition
    as the favorites. One list for both the node files and the window
    properties, so the two surfaces cannot disagree."""
    singles = [
        {
            "Name": settings.localized(30358),
            "Tag": "Favorite movies",
            "Media": "movies",
        },
        {
            "Name": settings.localized(30359),
            "Tag": "Favorite tvshows",
            "Media": "tvshows",
        },
    ]
    if episode_tags:
        singles.append(
            {
                "Name": settings.localized(30360),
                "Tag": "Favorite episodes",
                "Media": "episodes",
            }
        )
    if downloads is None:
        try:
            downloads = settings.get_bool("downloadsEnabled")
        except TypeError:
            # getSettingBool raises TypeError on a setting it cannot find.
            downloads = False
    if downloads:
        from kofin.downloads import EPISODE_TAG, TAG as DOWNLOADS_TAG

        singles.append(
            {
                "Name": settings.localized(30718),
                "Tag": DOWNLOADS_TAG,
                "Media": "movies",
                "File": "DownloadedMovies",
                "Type": "downloads",
                "Icon": NODE_DOWNLOADS_ICON,
            }
        )
        singles.append(
            {
                "Name": settings.localized(30719),
                "Tag": DOWNLOADS_TAG,
                "Media": "tvshows",
                "File": "DownloadedShows",
                "Type": "downloads",
                "Icon": NODE_DOWNLOADS_ICON,
            }
        )
    if downloads and episode_tags:
        # Filtered on the episode's own tag, not the show's: a tag rule on
        # episodes matches either, so DOWNLOADS_TAG would list every
        # episode of a show with one download. A downloaded episode's row
        # keeps its plugin URL, so a path rule has nothing to match, and a
        # Kodi without episode tags has no Downloaded-episodes single.
        singles.append(
            {
                "Name": settings.localized(30721),
                "Tag": EPISODE_TAG,
                "Media": "episodes",
                "File": "DownloadedEpisodes",
                "Type": "downloads",
                "Icon": NODE_DOWNLOADS_ICON,
            }
        )
    return singles


# --- building one file ----------------------------------------------------------


def _node(kind: str, order: int, icon: str) -> etree.Element:
    attributes = {"order": str(order)}
    if kind != "main":
        attributes["type"] = kind
    element = etree.Element("node", attributes)
    etree.SubElement(element, "icon").text = icon
    return element


def _tag_rule(xml: etree.Element, tag: str) -> None:
    rule = etree.SubElement(xml, "rule", {"field": "tag", "operator": "is"})
    etree.SubElement(rule, "value").text = tag


def path_rule(xml: etree.Element, path: str) -> None:
    """A library's rows: every one is filed under its folder
    (dynamic.node_entries)."""
    rule = etree.SubElement(xml, "rule", {"field": "path", "operator": "startswith"})
    etree.SubElement(rule, "value").text = path


def _parts(xml: etree.Element, parts: Iterable[tuple[Any, ...]]) -> None:
    for part in parts:
        if part[0] == "order":
            etree.SubElement(xml, "order", {"direction": part[2]}).text = part[1]
        elif part[0] == "limit":
            etree.SubElement(xml, "limit").text = str(LIMIT)
        elif part[0] == "group":
            etree.SubElement(xml, "group").text = part[1]
        elif part[0] == "rule":
            rule = etree.SubElement(
                xml, "rule", {"field": part[1], "operator": part[2]}
            )
            if part[3] is not None:
                etree.SubElement(rule, "value").text = part[3]


def build_parent() -> etree.Element:
    xml = _node("main", NODE_ROOT_ORDER, NODE_ROOT_ICON)
    etree.SubElement(xml, "label").text = settings.addon_name()
    return xml


def build_index(view: dict[str, Any], mixed: bool, order: int) -> etree.Element:
    """A library folder's own ``index.xml``: its position and its name."""
    xml = _node("main", order, node_icon(view["Media"]))
    etree.SubElement(xml, "label").text = (
        view["Name"] if not mixed else "%s (%s)" % (view["Name"], _label(view["Media"]))
    )
    return xml


def build_node(
    view: dict[str, Any], key: str, label: Optional[int], order: int
) -> etree.Element:
    """One filter node of a library folder."""
    xml = _node("filter", order, node_icon(view["Media"], key))
    etree.SubElement(xml, "label").text = _node_label(label or view["Name"])
    etree.SubElement(xml, "match").text = "all"
    etree.SubElement(xml, "content").text = (
        "episodes" if key in EPISODE_CONTENT else view["Media"]
    )
    path_rule(xml, view["Path"])
    _parts(xml, NODE_PARTS[key])
    return xml


def build_single(single: dict[str, Any], order: int) -> etree.Element:
    """A single node: a favourites or a Downloads listing, by its tag."""
    icon = single.get("Icon") or node_icon(single["Media"], "favorites")
    xml = _node("filter", order, icon)
    etree.SubElement(xml, "label").text = single["Name"]
    etree.SubElement(xml, "match").text = "all"
    content = etree.SubElement(xml, "content")
    content.text = single["Media"]
    _tag_rule(xml, single["Tag"])
    _parts(xml, NODE_PARTS["all"])
    return xml


# --- the tree ----------------------------------------------------------------


def write_parent(root: str) -> None:
    """The ``Kofin`` folder node itself. Written on creation only: ``order``
    and ``label`` are the user's to change afterwards."""
    file = os.path.join(root, "index.xml")
    if not os.path.isfile(file):
        write_xml(file, build_parent())


def write_library(root: str, view: dict[str, Any], mixed: bool, order: int) -> None:
    """One library's folder: its index and every node of its kind."""
    folder = fs.entry(root, node_folder(view))
    if not os.path.isdir(folder):
        os.makedirs(folder)

    write_xml(os.path.join(folder, "index.xml"), build_index(view, mixed, order))

    keep_files = {"index.xml"}
    for position, (key, label) in enumerate(NODES[view["Media"]]):
        filename = "%s.xml" % key
        keep_files.add(filename)
        write_xml(
            os.path.join(folder, filename),
            build_node(view, key, label, position),
        )

    # The folder is ours and its file names carry no prefix, so anything not
    # written this pass goes.
    _, files = fs.listdir(folder)
    for name in files:
        if name not in keep_files:
            fs.delete_file(os.path.join(folder, name))


def write_single(root: str, single: dict[str, Any], order: int) -> None:
    write_xml(os.path.join(root, single_file(single)), build_single(single, order))


def write_tree(
    entries: Iterable[tuple[dict[str, Any], bool]], singles: Iterable[dict[str, Any]]
) -> None:
    """The whole tree from what should be in it: ``entries`` are the sorted
    ``(view, mixed)`` pairs of the whitelist, ``singles`` the single nodes.

    Numbered on the nodes actually written, not on the entries walked: a
    music library is whitelisted and sorted like the rest but has no video
    node, and numbering it anyway leaves holes that the singles then start
    after. Ends by reconciling the tree against what was written -- a
    library can leave the whitelist by a route that never called
    remove_library (server-side deletion, a settings diff), and a single can
    go with its feature.
    """
    root = node_root_path()
    if not os.path.isdir(root):
        os.makedirs(root)

    write_parent(root)
    keep = set()
    order = 0

    for view, mixed in entries:
        if view["Media"] not in NODES:
            # A music library, or a kind the table does not know, has no
            # video node: skip it, since raising here stops the library
            # thread.
            if view["Media"] != "music":
                LOG.warning(
                    "--[ nodes ] no node kind for %s (%s); skipped",
                    view["Id"],
                    view["Media"],
                )
            continue
        write_library(root, view, mixed, order)
        keep.add(node_folder(view))
        order += 1

    for single in singles:
        write_single(root, single, order)
        keep.add(single_file(single))
        order += 1

    for name in fs.remove_managed_entries(root, keep=keep):
        LOG.debug("--[ nodes ] pruned stale %s", name)


# --- taking it down ------------------------------------------------------------


def tree_written() -> bool:
    """Whether the generated tree is on disk: its root's index, which
    ``write_tree`` writes first and ``delete_tree`` removes."""
    return os.path.isfile(os.path.join(node_root_path(), "index.xml"))


def written_singles() -> list[dict[str, Any]]:
    """The singles whose files are in the tree, in ``single_nodes`` order:
    what the tree offers while the settings that choose them cannot be
    read."""
    root = node_root_path()
    return [
        single
        for single in single_nodes(episode_tags=True, downloads=True)
        if os.path.isfile(os.path.join(root, single_file(single)))
    ]


def delete_tree() -> None:
    """Remove the whole generated tree."""
    root = node_root_path()
    fs.remove_managed_entries(root, also=("index.xml",))
    fs.remove_empty(root)
