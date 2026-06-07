import xbmc
import xbmcgui
from resources.lib.podcasts.actions.remote_action import RemoteAction
from resources.lib.podcasts.fyyd import Fyyd
from resources.lib.podcasts.util import get_asset_path
from resources.lib.rssaddon.http_status_error import HttpStatusError


class SearchFyydAction(RemoteAction):

    def _query_fyyd(self, term: str) -> dict:

        try:
            fyydClient = Fyyd(self.addon)
            response = fyydClient.search_podcasts(term=term)
            if response["msg"] == "ok":
                return [
                    {
                        "title": d["title"],
                        "subtitle": d["subtitle"],
                        "url": d["xmlURL"],
                        "icon": d["imgURL"]
                    } for d in response["data"] if d["status"] == 200
                ]
            else:
                return None

        except HttpStatusError as error:
            xbmc.log(str(error), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(32151), error.message)
            return None

    def search_fyyd(self) -> None:

        while True:
            term = xbmcgui.Dialog().input(heading=self.addon.getLocalizedString(32123))
            if not term:
                break

            xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(32122),
                                          message=self.addon.getLocalizedString(32124) % term, icon=get_asset_path(asset="notification.png"))

            feeds = self._query_fyyd(term=term)
            if feeds == None:
                return

            elif not feeds:
                xbmcgui.Dialog().notification(heading=self.addon.getLocalizedString(32122),
                                              message=self.addon.getLocalizedString(32125) % term, icon=get_asset_path(asset="notification.png"))
                continue

            feeds, abort = self.subscribe_feeds(feeds=feeds)
            if abort:
                break
