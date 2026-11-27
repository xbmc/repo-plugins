"""'Who's watching?' route handlers.

The feature's vocabulary, the toggle picker and the session restore live in
``service/whoswatching.py``; the picker runs in the service
(:func:`who_is_watching`). The Advanced-tab shortlist dialog stays a route:
the settings button runs in the plugin process and may block.
"""

import xbmc
import xbmcgui

from kofin.core import ipc, settings, state, toast
from kofin.core.api import Api
from kofin.core.http import JellyfinError, Unauthorized
from kofin.core.log import Logger
from kofin.core.settings import Credentials
from kofin.plugin.router import Request
from kofin.service.whoswatching import (
    SHORTLIST,
    SHORTLIST_ALL,
    SHORTLIST_NOBODY,
    detach_all,
    is_enabled,
    offered_ids,
    shortlist_setting,
)

LOG = Logger(__name__)

__all__ = ["who_is_watching", "select_shortlist", "is_enabled"]


def who_is_watching(request: Request) -> None:
    """Route handler: ask the service to open the picker, then get out.

    The dialog itself runs in the service (``show_picker``) for the same
    reason SyncPlay's does — a plugin invocation that blocks on a modal cannot
    be reached as a library node, because Kodi runs the node's ``<path>`` as a
    directory fetch and the two fight. Firing and exiting lets that fetch fail
    out at once while the picker comes up over whatever is on screen.
    """
    if not Credentials.load().is_logged_in:
        return
    if not is_enabled():
        # The root entry is gone when the feature is off, but a favourite or a
        # keymap kept from before still reaches this route.
        return
    if not state.is_online():
        toast.show(settings.localized(30045), time_ms=4000)
        return

    LOG.debug("requesting the who's-watching picker from the service")
    ipc.notify(ipc.WHO_IS_WATCHING)


def select_shortlist(request: Request) -> None:
    """Advanced-tab button: pick which users "Who's watching?" offers.

    Stores ids, not names: a rename on the server must not silently empty the
    shortlist. Row 0 is "All", which stores the sentinel rather than a snapshot
    of today's user list, so an account added on the server later is offered
    without anyone revisiting this dialog. Selecting nothing switches the
    feature off (:func:`detach_all`).
    """
    creds = Credentials.load()
    if not creds.is_logged_in:
        return
    api = Api.for_plugin(creds)

    try:
        users = api.users()
    except Unauthorized:
        users = api.public_users()
    except JellyfinError as error:
        LOG.warning("shortlist: user list unavailable: %s", error)
        toast.show(settings.localized(30507), toast.ERROR, time_ms=4000)
        return

    # The primary user is on every session by definition, so it is no more
    # selectable here than it is in the toggle dialog. A server with nobody
    # else still gets the dialog rather than an early return: "All" alone is
    # how the root entry is switched off, and a one-account server is exactly
    # where someone wants it gone.
    candidates = [user for user in users if user.get("Id") != api.user_id]

    tokens = shortlist_setting()
    was_enabled = is_enabled(tokens)
    ids = offered_ids(tokens)
    preselect = [0] if was_enabled and not ids else []
    preselect += [
        index + 1 for index, user in enumerate(candidates) if user.get("Id") in ids
    ]

    chosen = xbmcgui.Dialog().multiselect(
        settings.localized(30048),
        [settings.localized(30817)] + [user.get("Name", "") for user in candidates],
        preselect=preselect,
    )
    if chosen is None:
        return  # cancelled; the shortlist is left as-is

    if not chosen:
        value = SHORTLIST_NOBODY
    elif 0 in chosen:
        value = SHORTLIST_ALL  # "All" wins over any individual rows ticked with it
    else:
        value = ",".join(str(candidates[i - 1].get("Id", "")) for i in chosen)
    settings.set_str(SHORTLIST, value)
    LOG.debug(
        "who's-watching shortlist updated: %s",
        {SHORTLIST_ALL: "everyone", SHORTLIST_NOBODY: "off"}.get(
            value, "%d users" % len(chosen)
        ),
    )

    if value == SHORTLIST_NOBODY:
        detach_all(api, creds.device_id)
    if was_enabled != (value != SHORTLIST_NOBODY) and xbmc.getCondVisibility(
        "Window.IsMedia"
    ):
        # The root entry comes and goes with the feature, and the settings
        # dialog has already closed (<close>true</close>), so what is behind it
        # is usually the listing that has to change. Guarded the same way the
        # toggle's refresh is: with no media window there is no container for
        # the builtin to act on.
        xbmc.executebuiltin("Container.Refresh")
