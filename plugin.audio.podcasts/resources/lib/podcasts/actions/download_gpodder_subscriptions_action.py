import re

import xbmcgui
import xbmcvfs
import xmltodict
from resources.lib.podcasts.actions.action import Action
from resources.lib.podcasts.gpodder import GPodder
from resources.lib.podcasts.util import get_asset_path
from resources.lib.rssaddon.http_status_error import HttpStatusError


class DownloadGpodderSubscriptionsAction(Action):

    def download_gpodder_subscriptions(self) -> None:

        # Step 1: download subscriptions from gPodder
        try:
            host = self.addon.getSetting("gpodder_hostname")
            user = self.addon.getSetting("gpodder_username")
            password = self.addon.getSetting("gpodder_password")

            gPodder = GPodder(self.addon, host, user)
            sessionid = gPodder.login(password)

            opml_data = gPodder.request_subscriptions(sessionid)

        except HttpStatusError as error:
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(32151), error.message)
            return

        # Step 2: Save file in folder
        path, filename = self._save_opml_file(opml_data)
        if not path:
            return

        # Success
        xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
            32085), message="%s %s" % (self.addon.getLocalizedString(32083), filename), icon=get_asset_path("notification.png"))

        # Step 3: Select target opml slot
        slot = self._select_target_opml_slot(
            self.addon.getLocalizedString(32079))
        if slot == -1:
            return

        self.addon.setSetting("opml_file_%i" % slot, path)

        # Success
        xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(
            32085), message=self.addon.getLocalizedString(32086), icon=get_asset_path("notification.png"))

    def _save_opml_file(self, data: str) -> 'tuple[str,str]':

        opml = xmltodict.parse(data)
        filename = "%s.opml" % re.sub(
            "[^A-Za-z0-9']", " ", opml["opml"]["head"]["title"])

        path = xbmcgui.Dialog().browse(
            type=3, heading=self.addon.getLocalizedString(32080), shares="")

        if not path:
            return None, None

        try:
            fullpath = "%s%s" % (path, filename)
            with xbmcvfs.File(fullpath, 'w') as _file:
                _file.write(data)

            return fullpath, filename

        except:
            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(
                32081), message=self.addon.getLocalizedString(32082))

            return None, None
