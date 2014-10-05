import sys
import urlparse

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs

from ...abstract_plugin import AbstractPlugin
from xbmc_plugin_settings import XbmcPluginSettings


class XbmcPlugin(AbstractPlugin):
    def __init__(self, plugin_name=None, plugin_id=None):
        AbstractPlugin.__init__(self, plugin_name, plugin_id)

        if plugin_id:
            self._addon = xbmcaddon.Addon(id=plugin_id)
        else:
            self._addon = xbmcaddon.Addon()

        self._addon_uri = sys.argv[0]
        self._plugin_handle = int(sys.argv[1])
        self._plugin_id = plugin_id or self._addon.getAddonInfo('id')
        self._plugin_name = plugin_name or self._addon.getAddonInfo('name')
        self._navtive_path = xbmc.translatePath(self._addon.getAddonInfo('path'))

        self._settings = XbmcPluginSettings(self._addon)

        """
        Collect the current path and parameter
        """
        url_components = urlparse.urlparse(self._addon_uri)
        self._path = url_components[2]
        self._params = dict(urlparse.parse_qsl(sys.argv[2][1:]))

        """
        Set the data path for this addon and create the folder
        """
        self._data_path = xbmc.translatePath('special://profile/addon_data/%s' % self._plugin_id)
        if not xbmcvfs.exists(self._data_path):
            xbmcvfs.mkdir(self._data_path)
            pass
        pass

    def get_handle(self):
        return self._plugin_handle

    def get_data_path(self):
        return self._data_path

    def get_native_path(self):
        return self._navtive_path

    def get_path(self):
        return self._path

    def get_params(self):
        return self._params

    def get_settings(self):
        return self._settings

    def localize(self, text_id, default_text=None):
        result = default_text

        if text_id and isinstance(text_id, int):
            result = self._addon.getLocalizedString(text_id)
            pass

        if result is None:
            if default_text:
                return default_text

            return unicode(text_id)

        return result

    def set_content_type(self, content_type):
        xbmcplugin.setContent(self._plugin_handle, content_type)
        pass

    def add_sort_method(self, sort_method):
        xbmcplugin.addSortMethod(self._plugin_handle, sort_method)
        pass

    pass