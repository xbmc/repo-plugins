import sys, urlparse, os, urllib, datetime, time
import xbmcgui, xbmcplugin, xbmcaddon, xbmc

from resources.lib import utils
from resources.lib import redbulltv_client as redbulltv

class RedbullTV2(object):
    def __init__(self):
        self.id = 'plugin.video.redbull.tv'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.base_url = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        self.args = urlparse.parse_qs(sys.argv[2][1:])
        xbmcplugin.setContent(self.addon_handle, 'movies')
        self.redbulltv_client = redbulltv.RedbullTVClient(self.addon.getSetting('video.resolution'))

    @staticmethod
    def get_keyboard(default="", heading="", hidden=False):
        keyboard = xbmc.Keyboard(default, heading, hidden)
        keyboard.doModal()
        if keyboard.isConfirmed():
            return str(urllib.quote_plus(keyboard.getText()))
        return default

    def navigation(self):
        url = self.args.get("api_url")[0].decode('base64') if self.args.get("api_url") else None
        category = self.args.get('category', [None])[0]

        if url and "search?q=" in url:
            url += self.get_keyboard()

        try:
            items = self.redbulltv_client.get_items(url, category)
        except IOError:
            # Error getting data from Redbull server
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30020), self.addon.getLocalizedString(30021), self.addon.getLocalizedString(30022))
            return

        if not items:
            # No results found
            xbmcgui.Dialog().ok(self.addon.getLocalizedString(30023), self.addon.getLocalizedString(30024), self.addon.getLocalizedString(30025))
            return
        elif items[0].get("is_stream"):
            self.play_stream(items[0])
        elif items[0].get("event_date"):
            # Scheduled Event Time
            xbmcgui.Dialog().ok(
                self.addon.getLocalizedString(30026),
                self.addon.getLocalizedString(30027),
                datetime.datetime.fromtimestamp(int(items[0].get("event_date"))).strftime('%a %-d %b %Y %H:%M') +
                " (GMT+" + str(time.timezone / 3600 * -1) + ")"
            )
            return
        else:
            self.add_items(items)

        xbmcplugin.endOfDirectory(self.addon_handle)

    def add_items(self, items):
        for item in items:
            params = {'api_url' : item["url"].encode('base64')}
            if "category" in item:
                params['category'] = item["category"].encode('utf-8')

            url = utils.build_url(self.base_url, params)
            list_item = xbmcgui.ListItem(
                item.get("title"),
                iconImage='DefaultFolder.png',
                thumbnailImage=item.get("image", self.icon)
            )
            list_item.setInfo(type="Video", infoLabels={"Title": item["title"], "Plot": item.get("summary", None)})
            if item.get("is_content"):
                list_item.setProperty('IsPlayable', 'true')
            xbmcplugin.addDirectoryItem(handle=self.addon_handle, url=url, listitem=list_item, isFolder=(not item["is_content"]))

    def play_stream(self, item):
        list_item = xbmcgui.ListItem(label=item.get("title"), path=item.get("url"))
        list_item.setInfo(type="Video", infoLabels={"title": item.get("title"), "plot": item.get("summary")})
        list_item.setArt({'poster': item.get("image"), 'iconImage': "DefaultVideo.png", 'thumbnailImage': item.get("image")})
        list_item.setProperty("IsPlayable", "true")
        xbmcplugin.setResolvedUrl(handle=self.addon_handle, succeeded=True, listitem=list_item)

if __name__ == '__main__':
    RedbullTV2().navigation()
