import xbmcgui
import xbmcplugin
from urllib.parse import urlencode

class KodiUI:
    def __init__(self, handle, base_url):
        self.handle = handle
        self.base_url = base_url

    def build_url(self, action: str, **kwargs):
        kwargs["action"] = action
        return f"{self.base_url}?{urlencode(kwargs)}"

    def add_dir(self, label, action, **kwargs):
        url = self.build_url(action=action, **kwargs)
        li = xbmcgui.ListItem(label=label)
        xbmcplugin.addDirectoryItem(
            handle=self.handle, url=url, listitem=li, isFolder=True
        )

    def add_playable(self, label, url, icon=None):
        li = xbmcgui.ListItem(label=label)
        li.setProperty("IsPlayable", "true")
        li.setInfo("music", {"title": label})
        if icon:
            li.setArt({"thumb": icon})
        xbmcplugin.addDirectoryItem(
            handle=self.handle, url=url, listitem=li, isFolder=False
        )

    def resolve_url(self, stream_url: str):
        li = xbmcgui.ListItem(path=stream_url)
        xbmcplugin.setResolvedUrl(self.handle, True, li)

    def end_directory(self):
        xbmcplugin.endOfDirectory(self.handle)

    def notify(self, title, message, icon=xbmcgui.NOTIFICATION_INFO, time=3000):
        xbmcgui.Dialog().notification(title, message, icon, time)

    def notify_error(self, message):
        self.notify("Error", message, icon=xbmcgui.NOTIFICATION_ERROR)
