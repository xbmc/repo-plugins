# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""This is the actual VRT MAX service entry point"""

from xbmc import Monitor
from favorites import Favorites
from kodiutils import container_refresh, get_setting_bool, has_credentials, log
from playerinfo import PlayerInfo
from tokenresolver import TokenResolver


class VrtMonitor(Monitor, object):  # pylint: disable=useless-object-inheritance
    """This is the class that monitors Kodi for the VRT MAX video plugin"""

    def __init__(self):
        """VRT Monitor initialisation"""
        self._playerinfo = None
        self._favorites = None
        self.init_watching_activity()
        super(VrtMonitor, self).__init__()

    def run(self):
        """Main loop"""
        while not self.abortRequested():
            if self.waitForAbort(10):
                break

    def init_watching_activity(self):
        """Only load components for watching activity when needed"""

        # Is resumepoints activated in the menu and do we have credentials
        if get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials():
            if not self._playerinfo:
                self._playerinfo = PlayerInfo()
            if not self._favorites:
                self._favorites = Favorites()
        else:
            self._playerinfo = None

    def onNotification(self, sender, method, data):  # pylint: disable=invalid-name
        """Handler for notifications"""
        # log(2, '[Notification] sender={sender}, method={method}, data={data}', sender=sender, method=method, data=data)

        # Handle play_action events from upnextprovider
        if sender.startswith('upnextprovider') and method.endswith('plugin.video.vrt.nu_play_action'):
            from json import loads
            hexdata = loads(data)

            if not hexdata:
                return

            # NOTE: With Python 3.5 and older json.loads() does not support bytes or bytearray, so we convert to unicode
            from base64 import b64decode
            data = loads(b64decode(hexdata[0]).decode('utf-8'))
            log(2, '[Up Next notification] sender={sender}, method={method}, data={data}', sender=sender, method=method, data=data)
            self._playerinfo.add_upnext(data.get('episode_id'))

    def onSettingsChanged(self):  # pylint: disable=invalid-name
        """Handler for changes to settings"""

        log(1, 'Settings changed')
        TokenResolver().refresh_login()

        # Init watching activity again when settings change
        self.init_watching_activity()

        # Refresh container when settings change
        container_refresh()
