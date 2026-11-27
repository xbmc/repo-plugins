"""The main menu: the lists, each with what it holds said beside it, and the login."""

import time

import xbmc
import xbmcplugin

from resources.lib import clientfactory
from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.views import rows

_s = kodiutil.string
_log = kodiutil.log
# Seconds the main menu waits for the play service's counts; after that it makes them itself.
MENU_TIMEOUT = 5
# Set once the main menu was shown since Kodi started (its timings say whether it was the first time).
ROOT_SHOWN = "%s.root_shown" % kodiutil.ADDON_ID


class MainMenu:
    """The add-on's first page (see views.routes).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_root(self):
        """List the main menu."""
        # The channel list shows without a login too (the public one, as on the web player).
        # Kodi's own icons: every skin has them.
        logged_in = clientfactory.has_login()
        notes = self._notes() if logged_in else {}
        self._folder(rows.with_note(_s(30001), notes.get("channels")), "DefaultPVRChannels.png", action="channels")
        if logged_in:
            self._folder(rows.with_note(_s(30175), notes.get("mychannels")), "DefaultFavourites.png", action="mychannels")
            self._folder(rows.with_note(_s(30168), notes.get("watchlist")), "DefaultTVShows.png", action="watchlist")
            self._folder(rows.with_note(_s(30188), notes.get("continue")), "DefaultInProgressShows.png", action="continue")
            self._action(_s(30003), "DefaultUser.png", action="logout")
        else:
            self._action(_s(30002), "DefaultUser.png", action="login")
        xbmcplugin.endOfDirectory(self._call.handle, cacheToDisc=False)

    def _folder(self, label, icon, **params):
        xbmcplugin.addDirectoryItem(self._call.handle, self._call.url(**params), rows.menu_item(label, icon), isFolder=True)

    def _action(self, label, icon, **params):
        """Add a row that runs an action: neither a folder nor playable, so the listing stays and can be refreshed."""
        xbmcplugin.addDirectoryItem(self._call.handle, self._call.url(**params), rows.menu_item(label, icon), isFolder=False)

    def _notes(self):
        """Return what the main menu says beside its rows, by action (none where there is nothing to say).

        The subscribed channels, the favourite and deactivated ones, the favourite programmes by type,
        (see menucounts): the play service's, else made here.
        Timed in the debug log, each part, and whether it was the first menu since Kodi started.
        """
        begun = time.time()
        counts, source = self._counts()
        notes = {}
        if counts.get("subscribed") is not None:
            notes["channels"] = _s(30239) % counts["subscribed"]
            if counts.get("favourites") is not None:
                notes["mychannels"] = "%s: %d | %s: %d" % (_s(30237), counts["favourites"], _s(30236), counts["deactivated"])
        if counts.get("series") is not None:
            notes["watchlist"] = "%s: %d | %s: %d" % (kodiutil.kodi_string(20343), counts["series"], _s(30242), counts["other"])
        home = kodiutil.home()
        first = not home.getProperty(ROOT_SHOWN)
        home.setProperty(ROOT_SHOWN, "1")
        _log(
            "main menu counts %s in %d ms: %s (%s)"
            % (
                source,
                (time.time() - begun) * 1000,
                ", ".join(counts["timed"]),
                "first since Kodi started" if first else "again",
            ),
            xbmc.LOGDEBUG,
        )
        return notes

    def _counts(self):
        """Return the menu's counts (see menucounts.counts) and where they came from."""
        from resources.lib.service import quickplay

        counts = quickplay.ask("/menu", MENU_TIMEOUT)
        if counts is not None and "error" not in counts:
            return counts, "from the service"
        from resources.lib.data import menucounts

        if counts is not None:
            _log("main menu counts from the service failed: %s" % counts.get("message"))
        try:
            return menucounts.counts(self._call.client), "made here"
        except provider.ApiError as e:  # the client could not be made (a refused login)
            _log("main menu counts unavailable: %s" % e)
            return {"timed": []}, "made here"
