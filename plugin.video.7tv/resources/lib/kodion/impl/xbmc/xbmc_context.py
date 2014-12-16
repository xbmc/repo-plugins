import sys
import urllib
import urlparse
import weakref

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs
from ..abstract_context import AbstractContext
from .xbmc_plugin_settings import XbmcPluginSettings
from .xbmc_context_ui import XbmcContextUI
from .xbmc_system_version import XbmcSystemVersion


class XbmcContext(AbstractContext):
    def __init__(self, path='/', params=None, plugin_name=u'', plugin_id=u'', override=True):
        AbstractContext.__init__(self, path, params, plugin_name, plugin_id)

        if plugin_id:
            self._addon = xbmcaddon.Addon(id=plugin_id)
        else:
            self._addon = xbmcaddon.Addon()
            pass

        self._system_version = XbmcSystemVersion()

        """
        I don't know what xbmc/kodi is doing with a simple uri, but we have to extract the information from the
        sys parameters and re-build our clean uri.
        Also we extract the path and parameters - man, that would be so simple with the normal url-parsing routines.
        """
        # first the path of the uri
        if override:
            self._uri = sys.argv[0]
            comps = urlparse.urlparse(self._uri)
            self._path = urllib.unquote(comps.path).decode('utf-8')

            # after that try to get the params
            params = sys.argv[2][1:]
            if len(params) > 0:
                self._uri = self._uri + '?' + params

                self._params = {}
                params = dict(urlparse.parse_qsl(params))
                for _param in params:
                    item = params[_param]
                    self._params[_param] = item.decode('utf-8')
                    pass
                pass
            pass

        self._ui = None
        self._plugin_handle = int(sys.argv[1])
        self._plugin_id = plugin_id or self._addon.getAddonInfo('id')
        self._plugin_name = plugin_name or self._addon.getAddonInfo('name')
        self._native_path = xbmc.translatePath(self._addon.getAddonInfo('path'))
        self._settings = XbmcPluginSettings(self._addon)

        """
        Set the data path for this addon and create the folder
        """
        self._data_path = xbmc.translatePath('special://profile/addon_data/%s' % self._plugin_id)
        if not xbmcvfs.exists(self._data_path):
            xbmcvfs.mkdir(self._data_path)
            pass
        pass

    def get_language(self):
        if self.get_system_version().get_name() == 'Frodo':
            return 'en-US'

        try:
            language = xbmc.getLanguage(0, region=True)
            language = language.split('-')
            language = '%s-%s' % (language[0].lower(), language[1].upper())
            return language
        except Exception, ex:
            self.log_error('Failed to get system language (%s)', ex.__str__())
            return 'en-US'

    def get_system_version(self):
        return self._system_version

    def get_ui(self):
        if not self._ui:
            self._ui = XbmcContextUI(self._addon, weakref.proxy(self))
            pass
        return self._ui

    def get_handle(self):
        return self._plugin_handle

    def get_data_path(self):
        return self._data_path

    def get_native_path(self):
        return self._native_path

    def get_settings(self):
        return self._settings

    def localize(self, text_id, default_text=u''):
        result = self._addon.getLocalizedString(int(text_id))
        if result is not None and result:
            return result

        return default_text

    def set_content_type(self, content_type):
        xbmcplugin.setContent(self._plugin_handle, content_type)
        pass

    def add_sort_method(self, *sort_methods):
        for sort_method in sort_methods:
            xbmcplugin.addSortMethod(self._plugin_handle, sort_method)
            pass
        pass

    def clone(self, new_path=None, new_params=None):
        if not new_path:
            new_path = self.get_path()
            pass

        if not new_params:
            new_params = self.get_params()
            pass

        new_context = XbmcContext(path=new_path, params=new_params, plugin_name=self._plugin_name,
                                  plugin_id=self._plugin_id, override=False)
        new_context._function_cache = self._function_cache
        new_context._search_history = self._search_history
        new_context._favorite_list = self._favorite_list
        new_context._watch_later_list = self._watch_later_list
        new_context._access_manager = self._access_manager

        return new_context

    def execute(self, command):
        xbmc.executebuiltin(command)
        pass

    def sleep(self, milli_seconds):
        xbmc.sleep(milli_seconds)
        pass

    pass