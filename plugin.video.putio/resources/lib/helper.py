import putio
import xbmcgui
import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.putio')
__lang__ = __settings__.getLocalizedString


class PutioAuthFailureException(Exception):
    """An authentication error occured."""

    def __init__(self, header, message, duration=10000, icon=xbmcgui.NOTIFICATION_ERROR):
        self.header = header
        self.message = message
        self.duration = duration
        self.icon = icon


class PutioApiHandler(object):
    """A Put.io API client helper."""

    def __init__(self, oauth2_token):
        if not oauth2_token:
            raise PutioAuthFailureException(header=__lang__(30001), message=__lang__(30002))
        self.client = putio.Client(access_token=oauth2_token, use_retry=True)

    def get(self, id_):
        return self.client.File.get(id_)

    def list(self, parent=0):
        items = []
        for item in self.client.File.list(parent_id=parent):
            if item.content_type and self.is_showable(item):
                items.append(item)
        return items

    def is_showable(self, item):
        if item.is_audio or item.is_video or item.is_folder:
            return True
        return False
