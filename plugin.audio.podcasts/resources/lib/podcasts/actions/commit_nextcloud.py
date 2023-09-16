import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.podcasts.actions.action import Action
from resources.lib.podcasts.nextcloud import Nextcloud
from resources.lib.rssaddon.http_status_error import HttpStatusError


class CommitNextcloudAction(Action):

    def commit_nextcloud(self) -> None:

        try:
            host = self.addon.getSetting("nextcloud_hostname")
            user = self.addon.getSetting("nextcloud_username")
            password = self.addon.getSetting("nextcloud_password")

            nextcloud = Nextcloud(self.addon, host, user, password)
            response = nextcloud.request_subscriptions()
            if "timestamp" not in response:
                raise HttpStatusError()

        except HttpStatusError as error:
            xbmc.log(str(error), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(32151), error.message)

        xbmcaddon.Addon().openSettings()
