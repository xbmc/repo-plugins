import sys
import urllib
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


        """
        I don't know what xbmc/kodi is doing with a simple uri, but we have to extract the information from the
        sys parameters and re-build our clean uri.
        Also we extract the path and parameters - man, that would be so simple with the normal url-parsing routines.
        """
        # first the path of the uri
        self._uri = sys.argv[0]
        comps = urlparse.urlparse(self._uri)
        self._path = urllib.unquote(comps[2]).decode('utf-8')

        # after that try to get the params
        params = sys.argv[2][1:]
        if len(params)>0:
            self._uri = self._uri+'?'+params

            self._params = {}
            params = dict(urlparse.parse_qsl(params))
            for _param in params:
                item = params[_param]
                self._params[_param] = item.decode('utf-8')
                pass
            pass

        self._plugin_handle = int(sys.argv[1])
        self._plugin_id = plugin_id or self._addon.getAddonInfo('id')
        self._plugin_name = plugin_name or self._addon.getAddonInfo('name')
        self._navtive_path = xbmc.translatePath(self._addon.getAddonInfo('path'))

        self._settings = XbmcPluginSettings(self._addon)

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

    def get_uri(self):
        return self._uri

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