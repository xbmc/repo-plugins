"""The ``Kofin.nodes.*`` / ``Kofin.wnodes.*`` window properties: the
contract skins read (plugin.video.kofin.wiki/Skin-integration.md).

Session state, rebuilt on every service start and every regeneration --
window properties do not survive a Kodi restart. Names are a skin contract
and never change here.
"""

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Optional

import xbmcgui

from kofin.core.log import Logger
from kofin.sync.nodes.video import (
    NODES,
    _label,
    browse_url,
    library_node_path,
    single_node_path,
)

if TYPE_CHECKING:
    from kofin.core.api import Api
    from kofin.sync.dynamic import View

LOG = Logger(__name__)


def window_prop(
    key: str, value: Optional[str] = None, clear: bool = False
) -> Optional[str]:
    """Plain string window-property access on the home window."""
    window = xbmcgui.Window(10000)
    if clear:
        window.clearProperty(key)
        return None
    if value is not None:
        window.setProperty(key, value)
        return None
    return window.getProperty(key)


NODES_PREFIX = "Kofin.nodes"
WNODES_PREFIX = "Kofin.wnodes"

# What one entry publishes on its own name...
ENTRY_PROPS = ("index", "id", "path", "artwork", "title", "content", "type")
# ...and on each of its sub-nodes. Derived from the node table, so a node
# added there is cleared here without a second list to forget.
SUB_PROPS = ("title", "content", "path", "id", "type", "artwork")
# A retired sub-node, still cleared so a property an earlier version set
# does not keep a dead path until Kodi restarts.
_RETIRED_SUB_NODES = ("nextepisodes",)
SUB_NODES = tuple(
    sorted(
        {key for kind in NODES.values() for key, _label_id in kind if key != "all"}
        | set(_RETIRED_SUB_NODES)
    )
)


def clear(prefix: str = NODES_PREFIX) -> None:
    """Every property a previous publish under ``prefix`` may have set."""
    total = int(window_prop(prefix + ".total") or 0)
    for index in range(total):
        entry = "%s.%s" % (prefix, index)
        for prop in ENTRY_PROPS:
            window_prop("%s.%s" % (entry, prop), clear=True)
        for node in SUB_NODES:
            for prop in SUB_PROPS:
                window_prop("%s.%s.%s" % (entry, node, prop), clear=True)
    for prop in ENTRY_PROPS:
        window_prop("%s.%s" % (prefix, prop), clear=True)


def ordered(
    libraries: Sequence["View"], sorted_views: Iterable[str]
) -> Sequence["View"]:
    """The view rows in SortedViews order, unknown ones last. Pure."""
    if not libraries:
        return libraries

    order = list(sorted_views)
    unordered = [x[0] for x in libraries]

    for library in unordered:
        if library not in order:
            order.append(library)

    return [libraries[unordered.index(x)] for x in order if x in unordered]


def publish(
    libraries: Sequence["View"],
    sync: dict[str, Any],
    singles: Iterable[dict[str, Any]],
    media_folders: Optional[Iterable[dict[str, Any]]],
    server: Optional["Api"],
) -> None:
    """Set every property from the views and the whitelist.

    ``libraries`` are the server's views (``dynamic.View``), ``media_folders``
    the server's listing (for the library tiles' artwork; None when there is
    no server to ask, which clears the prop outright).
    """
    clear(NODES_PREFIX)
    clear(WNODES_PREFIX)

    whitelist = [x.replace("Mixed:", "") for x in sync["Whitelist"]]
    index = 0
    windex = 0
    artwork = _Artwork(media_folders, server)

    for library in ordered(libraries or [], sync["SortedViews"]):
        view = {
            "Id": library.view_id,
            "Name": library.view_name,
            "Tag": library.view_name,
            "Media": library.media_type,
        }

        if library.view_id in whitelist:
            if view["Media"] in ("movies", "tvshows", "musicvideos", "mixed"):
                if view["Media"] == "mixed":
                    for media in ("movies", "tvshows"):
                        for node in NODES[media]:
                            temp_view = dict(view)
                            temp_view["Media"] = media
                            temp_view["Name"] = "%s (%s)" % (
                                view["Name"],
                                _label(media),
                            )
                            _node(index, temp_view, artwork, *node)
                            _wnode(windex, temp_view, artwork, *node)

                        # Each half takes an index of its own; with the
                        # outer step below that leaves one unused per mixed
                        # library, and skins read this numbering.
                        index += 1
                        windex += 1
                else:
                    for node in NODES[view["Media"]]:
                        _node(index, view, artwork, *node)

                        if view["Media"] in ("movies", "tvshows"):
                            _wnode(windex, view, artwork, *node)

                    if view["Media"] in ("movies", "tvshows"):
                        windex += 1

            elif view["Media"] == "music":
                _node(index, view, artwork, "music")
        else:  # dynamic entry
            if view["Media"] in ("homevideos", "books", "playlists"):
                _wnode(windex, view, artwork, "browse")
                windex += 1

            _node(index, view, artwork, "browse")

        index += 1

    for single in singles:
        _single(index, single.get("Type", "favorites"), single)
        index += 1

    window_prop("%s.total" % NODES_PREFIX, str(index))
    window_prop("%s.total" % WNODES_PREFIX, str(windex))


class _Artwork:
    """Server artwork for the library tiles, when the view has any.

    A real media image (the library's Primary), not a structural icon, so a
    server URL is correct here; skins fall back to their own art when the
    prop is empty.
    """

    def __init__(
        self, media_folders: Optional[Iterable[dict[str, Any]]], server: Optional["Api"]
    ) -> None:
        self.media_folders = media_folders
        self.server = server

    def publish(self, prop: str, view_id: str) -> None:
        if self.server is None:
            window_prop("%s.artwork" % prop, clear=True)

        elif self.media_folders is not None:
            for library in self.media_folders:
                if library["Id"] == view_id and "Primary" in library.get(
                    "ImageTags", {}
                ):
                    window_prop(
                        "%s.artwork" % prop,
                        "%s/Items/%s/Images/Primary/0?Format=original"
                        % (self.server.server, view_id),
                    )
                    break
            else:
                window_prop("%s.artwork" % prop, clear=True)


def _node(
    index: int,
    view: dict[str, Any],
    artwork: _Artwork,
    node: str,
    node_label: Optional[int] = None,
) -> None:
    """Leads to another listing of nodes."""
    if view["Media"] in ("homevideos", "photos"):
        path = browse_url(view, None if node in ("all", "browse") else node)
    elif node == "music":
        path = "library://music/"
    elif node == "browse":
        path = browse_url(view)
    else:
        path = library_node_path(view, node)

    if node == "music":
        window_path = "ActivateWindow(Music,%s,return)" % path
    elif node in ("browse", "homevideos", "photos"):
        window_path = path
    else:
        window_path = "ActivateWindow(Videos,%s,return)" % path

    label = _label(node_label) or view["Name"]

    if node in ("all", "music"):
        name = "%s.%s" % (NODES_PREFIX, index)
        window_prop("%s.index" % name, path.replace("all.xml", ""))
        window_prop("%s.title" % name, view["Name"])
        window_prop("%s.content" % name, path)
    elif node == "browse":
        name = "%s.%s" % (NODES_PREFIX, index)
        window_prop("%s.title" % name, view["Name"])
    else:
        name = "%s.%s.%s" % (NODES_PREFIX, index, node)
        window_prop("%s.title" % name, label)
        window_prop("%s.content" % name, path)

    window_prop("%s.id" % name, view["Id"])
    window_prop("%s.path" % name, window_path)
    window_prop("%s.type" % name, view["Media"])
    artwork.publish(name, view["Id"])


def _single(index: int, item_type: str, single: dict[str, Any]) -> None:
    """Single destination node."""
    path = single_node_path(single)
    name = "%s.%s" % (NODES_PREFIX, index)
    window_prop("%s.title" % name, single["Name"])
    window_prop("%s.path" % name, "ActivateWindow(Videos,%s,return)" % path)
    window_prop("%s.content" % name, path)
    window_prop("%s.type" % name, item_type)


def _wnode(
    index: int,
    view: dict[str, Any],
    artwork: _Artwork,
    node: str,
    node_label: Optional[int] = None,
) -> None:
    """Similar to _node, but without music and musicvideos, and with books
    and playlists."""
    if view["Media"] in ("homevideos", "photos", "books", "playlists"):
        path = browse_url(view, None if node in ("all", "browse") else node)
    else:
        path = library_node_path(view, node)

    if node in ("browse", "homevideos", "photos", "books", "playlists"):
        window_path = path
    else:
        window_path = "ActivateWindow(Videos,%s,return)" % path

    label = _label(node_label) or view["Name"]

    if node == "all":
        name = "%s.%s" % (WNODES_PREFIX, index)
        window_prop("%s.index" % name, path.replace("all.xml", ""))
        window_prop("%s.title" % name, view["Name"])
    elif node == "browse":
        name = "%s.%s" % (WNODES_PREFIX, index)
        window_prop("%s.title" % name, view["Name"])
    else:
        name = "%s.%s.%s" % (WNODES_PREFIX, index, node)
        window_prop("%s.title" % name, label)
    window_prop("%s.content" % name, path)

    window_prop("%s.id" % name, view["Id"])
    window_prop("%s.path" % name, window_path)
    window_prop("%s.type" % name, view["Media"])
    artwork.publish(name, view["Id"])

    LOG.debug(
        "--[ wnode/%s/%s ] %s",
        index,
        window_prop("%s.title" % name),
        window_prop("%s.artwork" % name),
    )
