"""One plugin call as the views see it: its address, handle and parameters, the client, its timings."""

import time
from urllib.parse import parse_qsl
from urllib.parse import urlencode

import xbmcgui
import xbmcplugin

from resources.lib import clientfactory
from resources.lib import kodiutil
from resources.lib.data import guidedata
from resources.lib.util import laps
from resources.lib.views import routes


class Call:
    """The plugin call Kodi made: what the views share of it.

    :param argv: Kodi's sys.argv for the call (base URL, handle, query, and Kodi's resume answer if any)
    :param started: when Kodi started the call; now if not given
    :param imported: seconds the plugin's modules took to load, for the log
    :param client: the provider's client; else made at first use (not every action needs one)
    """

    def __init__(self, argv, started=None, imported=None, client=None):
        self.started = started or time.time()
        self.imported = imported
        self.base = argv[0]
        self.handle = int(argv[1])
        self.params = dict(parse_qsl(argv[2].lstrip("?")))
        if self.params.get("programme"):
            self.params["programme"] = guidedata.kodi_resume(self.params["programme"], argv)
        # Steps an action marks, logged with its time (see plugin.Plugin.run).
        self.laps = laps.Laps()
        self._client = client
        self._colours = None

    @property
    def action(self):
        """Return the action the call runs now (see redirect)."""
        return self.params.get("action", "root")

    @property
    def client(self):
        """Return the provider's client, made at first use."""
        if self._client is None:
            self._client = clientfactory.make_client()
        return self._client

    @property
    def colours(self):
        """Return whether the rows have their category's guide colour (the "Category colours" setting)."""
        if self._colours is None:
            self._colours = kodiutil.addon().getSettingBool("colours")
        return self._colours

    def url(self, **params):
        """Return this plugin's address with these parameters."""
        return self.base + "?" + urlencode(params)

    def redirect(self, params):
        """Run another action in this call (a menu's choice, a play): its parameters, and its end (see end)."""
        self.params = params

    def end(self, ok):
        """End the call as its action must for Kodi: a play resolved (with nothing), a listing ended."""
        if self.handle < 0:
            return
        if self.action == "play":
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
        elif routes.is_listing(self.action):
            xbmcplugin.endOfDirectory(self.handle, succeeded=ok)

    def decline_play(self):
        """Tell Kodi at once that nothing plays, if its own Play ran a row that only opens a menu or a notice.

        Kodi would wait for a stream otherwise, and say playback failed after its 20 s.
        """
        if self.handle >= 0:
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
