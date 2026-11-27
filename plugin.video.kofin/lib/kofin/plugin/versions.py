"""Which version a play takes when it names none.

Kodi offers versions of a movie it filed with them (the video_versions
feature) and of nothing else, so for every other item with several media
sources the viewer is asked here, by the play route.
"""

from typing import Any, Optional, Union

import xbmc
import xbmcgui

JsonDict = dict[str, Any]

# Kodi's own "Versions": the picker's heading.
HEADING = 40000


def unfiled(item: JsonDict) -> bool:
    """Whether Kodi has no versions of this item to choose between: an
    episode on every Kodi, since Kodi groups versions of a movie alone, and a
    movie on a Kodi without the video_versions feature."""
    kind = item.get("Type")
    if kind == "Episode":
        return True
    if kind != "Movie":
        return False
    from kofin.sync.backends.api.capabilities import has

    return not has("video_versions")


def _name(source: JsonDict) -> str:
    return str(source.get("Name") or "").strip()


def choose(item: JsonDict, unattended: bool, followed: Optional[str]) -> Optional[str]:
    """The media source of a play that names none: the version the viewer
    picks, "" for the server's default, None when the viewer cancelled.

    Only an item with several sources that Kodi offers no versions of asks.
    An ``unattended`` play takes the default, and one Play Next started
    (``followed``, the name of the version that was playing) takes the
    version of that name, or the default when there is none.
    """
    sources = [
        source
        for source in item.get("MediaSources") or []
        if isinstance(source, dict) and source.get("Id")
    ]
    if len(sources) < 2 or not unfiled(item) or unattended:
        return ""
    if followed is not None:
        wanted = followed.strip().casefold()
        return next(
            (
                str(source["Id"])
                for source in sources
                if wanted and _name(source).casefold() == wanted
            ),
            "",
        )
    labels: list[Union[str, xbmcgui.ListItem]] = [
        _name(source) or str(item.get("Name") or source["Id"]) for source in sources
    ]
    index = xbmcgui.Dialog().select(
        xbmc.getLocalizedString(HEADING), labels, preselect=0
    )
    if index < 0:
        return None
    return str(sources[index]["Id"])
