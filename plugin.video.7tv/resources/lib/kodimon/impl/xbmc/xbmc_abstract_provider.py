__author__ = 'bromix'

import xbmc

from ...abstract_provider import AbstractProvider


class XbmcAbstractProvider(AbstractProvider):
    def __init__(self, plugin=None):
        AbstractProvider.__init__(self, plugin)
        pass

    def refresh_container(self):
        xbmc.executebuiltin("Container.Refresh")
        pass

    def show_notification(self, message, header='', image_uri='', time_milliseconds=5000):
        _header = header
        if not _header:
            _header = self.get_plugin().get_name()
            pass

        _image = image_uri
        if not _image:
            _image = self.get_plugin().get_icon()
            pass

        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(_header, message, time_milliseconds, _image))
        pass

    pass
