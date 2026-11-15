"""The add-on's menus: what Kodi shows under Simple GO, and the actions behind them.

Each click runs this in a fresh interpreter, so it imports only the view its action needs
(see views.routes); the views themselves are in resources.lib.views.
"""

import importlib
import time

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import kodiutil
from resources.lib import playmessages
from resources.lib import provider
from resources.lib.views import call as calls
from resources.lib.views import routes

_s = kodiutil.string
_log = kodiutil.log


class Plugin:
    """Run one plugin call: the action its URL names (see run).

    :param argv: Kodi's sys.argv for the call (base URL, handle, query)
    :param started: when Kodi started the call; now if not given
    :param imported: seconds the plugin's modules took to load, for the log (see run)
    """

    def __init__(self, argv, started=None, imported=None):
        self._call = calls.Call(argv, started, imported)

    def run(self):
        """Run the action the URL names, telling the user about the provider's errors."""
        call = self._call
        action = call.action
        begun = time.time()
        route = routes.ROUTES.get(action)
        if route is None:  # an address from an older version (a favourite, a widget): nothing to run
            _log("unknown action: %s" % action, xbmc.LOGWARNING)
            if call.handle >= 0:  # whatever it was, Kodi waits for a listing's end
                xbmcplugin.endOfDirectory(call.handle, succeeded=False)
            return
        if route.category and call.handle >= 0:
            xbmcplugin.setPluginCategory(call.handle, " / ".join(_s(i) for i in route.category))
        view = getattr(importlib.import_module("resources.lib.views." + route.module), route.view)(call)
        try:
            getattr(view, "do_" + action)()
        except provider.ApiError as e:
            tell(e, call.base)
            call.end(False)  # as the action it ended in: a play reached from a picker resolves (see Call.redirect)
        steps = (", %s" % call.laps) if call.laps.steps else ""
        # "start" is Python's start and the imports; "imports" the plugin's own modules of it.
        imports = ", imports %.2fs" % call.imported if call.imported is not None else ""
        _log(
            "%s: done in %.2fs (start %.2fs%s%s)" % (action, time.time() - call.started, begun - call.started, imports, steps),
            xbmc.LOGDEBUG,
        )


def tell(e, base):
    """Log a provider error and tell the user, as the play service's answer does (see quickplay).

    :param base: the plugin's address, for what the message offers to do (see playmessages.offer_instead)
    """
    if e.kind in playmessages.SILENT:
        _log(str(e))
    elif e.kind == "licence":
        from resources.lib.stream import streamsession

        _log(str(e))
        xbmcgui.Dialog().ok(kodiutil.name(), streamsession.licence_message(e.code))
    elif e.kind in playmessages.ERRORS:
        # A login or the country is the user's to fix; the rest is the programme's own.
        _log(str(e), xbmc.LOGWARNING if e.kind in ("auth", "geo") else xbmc.LOGDEBUG)
        if e.offer:
            playmessages.offer_instead(base, _s(playmessages.ERRORS[e.kind]), e.offer)
        else:
            xbmcgui.Dialog().ok(kodiutil.name(), _s(playmessages.ERRORS[e.kind]))
    else:
        _log(str(e), xbmc.LOGERROR)
        xbmcgui.Dialog().notification(kodiutil.name(), str(e)[:120], xbmcgui.NOTIFICATION_ERROR)


def run(argv, started=None, imported=None):
    """Run the plugin call Kodi made (see Plugin)."""
    Plugin(argv, started, imported).run()
