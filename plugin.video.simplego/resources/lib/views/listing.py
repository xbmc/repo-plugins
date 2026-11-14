"""What the lists share: the channel list's data, info pages, Kodi's select action, a redraw."""

import xbmc
import xbmcgui

from resources.lib import kodiutil
from resources.lib import provider

_log = kodiutil.log
# Kodi's "Default select action" (myvideos.selectaction): what a picker row's click opens instead.
SELECT_PLAY = 1
SELECT_OPENS = {0: "Action(ContextMenu)", 3: "Action(Info)"}  # "Choose", "Show information"
# Seconds a channel list waits for the play service's; after that it makes it itself.
LIST_TIMEOUT = 10


def list_view(call, scope=None):
    """Return what a channel list shows (see channellist.view): the play service's, else made here.

    Made here, a refused login is reported and the public channels are listed.
    """
    from resources.lib.data import channellist
    from resources.lib.service import quickplay

    view = quickplay.ask("/list", LIST_TIMEOUT, scope=scope or "")
    if view is not None and "error" not in view:
        call.laps("from the service")
        return view
    if view is not None:
        _log("list from the service failed: %s" % view.get("message"))
    try:
        view = channellist.view(call.client, scope)
    except provider.AuthError as e:
        _log("auth error: %s" % e, xbmc.LOGWARNING)
        xbmcgui.Dialog().notification(kodiutil.name(), kodiutil.string(30010), xbmcgui.NOTIFICATION_WARNING)
        call.client.guest = True
        view = channellist.view(call.client, scope)
    call.laps("made here")
    return view


def pages(call, keys, full=True):
    """Return the info pages of these (kind, id) keys, kept or fetched once (see infopages.pages_for)."""
    from resources.lib.data import infopages

    if not keys:
        return {}
    found = infopages.pages_for(lambda: call.client, keys, kodiutil.PROFILE, full=full)
    call.laps("pages")
    return found


def opened_by_select_action():
    """Open what Kodi's "Default select action" asks instead of a row's own picker; whether it did.

    Kodi applies the setting to playable rows only, so a picker row (an action) does it itself:
    "Choose" opens the context menu, "Show information" the info page.
    """
    action = kodiutil.kodi_setting("myvideos.selectaction", SELECT_PLAY)
    if action not in SELECT_OPENS:
        return False
    xbmc.executebuiltin(SELECT_OPENS[action])
    return True


def list_changed():
    """Show a list again after a change of the account's (a favourite, the order, a deactivation).

    The list shows it at once; Kodi TV's channels (their order, its Favourites group) follow at
    the next scheduled export: a list change is no settings change to export for right away.
    """
    xbmc.executebuiltin("Container.Refresh")
