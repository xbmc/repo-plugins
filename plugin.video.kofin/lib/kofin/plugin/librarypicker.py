"""The library-selection multiselect (settings button -> RunPlugin).

Writes the chosen view ids back to the hidden ``librarySelection`` csv; the
service-side diff engine (service/settings_apply.py) computes add/remove
sets against the synced whitelist and dispatches the work. Selection state
therefore survives failed syncs: the picker only ever records intent.
"""

from typing import Any

import xbmcgui

from kofin.core import settings, toast
from kofin.core.api import Api
from kofin.core.http import JellyfinError
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin import feedback
from kofin.plugin.router import Request

LOG = Logger(__name__)

# The library types the sync files.
SYNCABLE_TYPES = ("movies", "tvshows", "music", "musicvideos", "mixed")


def syncable_views(views: list[dict[str, Any]]) -> list[dict[str, str]]:
    """(Id, Name, Media) of the views the sync can file."""
    result = []

    supported = SYNCABLE_TYPES
    for view in views:
        collection = view.get("CollectionType") or "mixed"
        if collection in supported:
            result.append(
                {
                    "Id": view.get("Id", ""),
                    "Name": view.get("Name", ""),
                    "Media": collection,
                }
            )
    return result


def select_libraries(request: Request) -> None:
    creds = Credentials.load()
    if not creds.is_logged_in:
        return

    api = Api.for_plugin(creds)
    try:
        views = api.views(include_hidden=True).get("Items", [])
    except JellyfinError as error:
        LOG.warning("library picker: views unavailable: %s", error)
        # Not "No libraries available" (30269): the request failed, so
        # whether the server has libraries is unknown.
        feedback.failed(error)
        return

    candidates = syncable_views(views)
    if not candidates:
        toast.show(settings.localized(30269), time_ms=4000)
        return

    selection = settings.get_list("librarySelection")
    preselect = [
        index for index, view in enumerate(candidates) if view["Id"] in selection
    ]

    chosen = xbmcgui.Dialog().multiselect(
        settings.localized(30268),
        [view["Name"] for view in candidates],
        preselect=preselect,
    )

    if chosen is None:
        return  # cancelled; nothing changes

    # A selected library the server did not list is kept: only an untick
    # takes a library out, and the service removes one the server confirms
    # is gone.
    listed = {view["Id"] for view in candidates}
    picked = [candidates[index]["Id"] for index in chosen] + [
        library for library in selection if library not in listed
    ]
    settings.set_str("librarySelection", ",".join(picked))
    LOG.debug("library selection updated: %s ids", len(picked))
