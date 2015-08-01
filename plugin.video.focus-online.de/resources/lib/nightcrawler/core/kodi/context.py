import json
import sys
import urllib
import urlparse
import weakref
import datetime

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcvfs

from ... import utils
from ..abstract_context import AbstractContext
from . import kodi_items
from .settings import KodiSettings
from .context_ui import KodiContextUI
from .player import KodiPlayer
from .playlist import KodiPlaylist


class KodiContext(AbstractContext):
    def __init__(self, path='/', params=None, plugin_name=u'', plugin_id=u'', override=True):
        AbstractContext.__init__(self, path, params, plugin_name, plugin_id)

        # initialize KODI addon
        if plugin_id:
            self._addon = xbmcaddon.Addon(id=plugin_id)
            pass
        else:
            self._addon = xbmcaddon.Addon()
            pass

        self._system_info = {}

        """
        I don't know what kodi/kodi is doing with a simple uri, but we have to extract the information from the
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
                    self._params[_param] = utils.strings.to_unicode(item)
                    pass
                pass
            pass

        self._content_type = None
        self._ui = None
        self._video_playlist = None
        self._audio_playlist = None
        self._video_player = None
        self._audio_player = None
        self._settings = None

        self._plugin_handle = int(sys.argv[1])
        self._plugin_id = plugin_id or self._addon.getAddonInfo('id')
        self._plugin_name = plugin_name or self._addon.getAddonInfo('name')
        self._version = self._addon.getAddonInfo('version')
        self._native_path = xbmc.translatePath(self._addon.getAddonInfo('path'))

        """
        Set the data path for this addon and create the folder
        """
        self._data_path = xbmc.translatePath('special://profile/addon_data/%s' % self._plugin_id)
        if isinstance(self._data_path, str):
            self._data_path = self._data_path.decode('utf-8')
            pass
        if not xbmcvfs.exists(self._data_path):
            xbmcvfs.mkdir(self._data_path)
            pass
        pass

    def log(self, text, log_level):
        log_text = '[%s] %s' % (self.get_id(), text)
        map_log_level = {self.LOG_DEBUG: 0,  # DEBUG
                         self.LOG_INFO: 2,  # INFO
                         self.LOG_WARNING: 3,  # WARNING
                         self.LOG_ERROR: 4}  # ERROR
        xbmc.log(msg=log_text, level=map_log_level.get(log_level, 2))
        pass

    def format_date_short(self, date_obj):
        date_format = xbmc.getRegion('dateshort')
        _date_obj = date_obj
        if isinstance(_date_obj, datetime.date):
            _date_obj = datetime.datetime(_date_obj.year, _date_obj.month, _date_obj.day)
            pass

        return _date_obj.strftime(date_format)

    def format_time(self, time_obj):
        time_format = xbmc.getRegion('time')
        _time_obj = time_obj
        if isinstance(_time_obj, datetime.time):
            _time_obj = datetime.time(_time_obj.hour, _time_obj.minute, _time_obj.second)
            pass

        return _time_obj.strftime(time_format)

    def get_language(self):
        # The xbmc.getLanguage() method is fucked up!!! We always return 'en-US' for now
        return 'en-US'

    def _update_system_info(self):
        try:
            json_rpc = {'jsonrpc': '2.0',
                        'method': 'Application.GetProperties',
                        'params': {'properties': ['version', 'name']},
                        'id': 1}
            json_query = xbmc.executeJSONRPC(json.dumps(json_rpc))
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = json.loads(json_query)
            version_installed = []
            if 'result' in json_query and 'version' in json_query['result']:
                version_installed = json_query['result']['version']
                self._system_info['version'] = (version_installed.get('major', 1), version_installed.get('minor', 0))
                pass
        except Exception, ex:
            self.log_error('Failed to get system info via jsonrpc')
            self.log_error(ex.__str__())

            self._system_info['version'] = (1, 0)
            pass

        self._system_info['name'] = 'unknown system'

        if self._system_info['version'] >= (16, 0):
            self._system_info['name'] = 'J.....'
            pass
        elif self._system_info['version'] >= (15, 0):
            self._system_info['name'] = 'Isengard'
            pass
        elif self._system_info['version'] >= (14, 0):
            self._system_info['name'] = 'Helix'
            pass
        elif self._system_info['version'] >= (13, 0):
            self._system_info['name'] = 'Gotham'
            pass
        elif self._system_info['version'] >= (12, 0):
            self._system_info['name'] = 'Frodo'
            pass
        pass

    def get_system_version(self):
        if not self._system_info:
            self._update_system_info()
            pass
        return self._system_info['version']

    def get_system_name(self):
        if not self._system_info:
            self._update_system_info()
            pass
        return self._system_info['name']

    def get_video_playlist(self):
        if not self._video_playlist:
            self._video_playlist = KodiPlaylist('video', weakref.proxy(self))
            pass
        return self._video_playlist

    def get_audio_playlist(self):
        if not self._audio_playlist:
            self._audio_playlist = KodiPlaylist('audio', weakref.proxy(self))
            pass
        return self._audio_playlist

    def get_video_player(self):
        if not self._video_player:
            self._video_player = KodiPlayer('video', weakref.proxy(self))
            pass
        return self._video_player

    def get_audio_player(self):
        if not self._audio_player:
            self._audio_player = KodiPlayer('audio', weakref.proxy(self))
            pass
        return self._audio_player

    def get_ui(self):
        if not self._ui:
            self._ui = KodiContextUI(self._addon, weakref.proxy(self))
            pass
        return self._ui

    def get_handle(self):
        return self._plugin_handle

    def get_data_path(self):
        return self._data_path

    def get_native_path(self):
        return self._native_path

    def get_settings(self):
        if not self._settings:
            self._settings = KodiSettings(self, self._addon)
            pass

        return self._settings

    def localize(self, text_id, default=u''):
        if isinstance(text_id, int):
            """
            We want to use all localization strings!
            Addons should only use the range 30000 thru 30999 (see: http://kodi.wiki/view/Language_support) but we
            do it anyway. I want some of the localized strings for the views of a skin.
            """
            if text_id >= 0 and (text_id < 30000 or text_id > 30999):
                result = xbmc.getLocalizedString(text_id)
                if result is not None and result:
                    return utils.strings.to_unicode(result)
                pass
            pass

        result = self._addon.getLocalizedString(int(text_id))
        if result is not None and result:
            return utils.strings.to_unicode(result)

        return utils.strings.to_unicode(default)

    def set_content_type(self, content_type):
        self.log_debug('Setting content-type: "%s" for "%s"' % (content_type, self.get_path()))
        xbmcplugin.setContent(self._plugin_handle, content_type)

        self._content_type = content_type
        pass

    def add_sort_method(self, *sort_methods):
        sort_map = {'album': 13,
                    'album_ignore_the': 14,
                    'artist': 11,
                    'artist_ignore_the': 12,
                    'bit_rate': 39,
                    'channel': 38,
                    'country': 16,
                    'date': 3,
                    'date_added': 19,
                    'date_taken': 40,
                    'drive_type': 6,
                    'duration': 8,
                    'episode': 22,
                    'file': 5,
                    'full_path': 32,
                    'genre': 15,
                    'label': 1,
                    'label_ignore_folders': 33,
                    'label_ignore_the': 2,
                    'last_played': 34,
                    'listeners': 36,
                    'mpaa_rating': 28,
                    'none': 0,
                    'play_count': 35,
                    'playlist_order': 21,
                    'production_code': 26,
                    'program_count': 20,
                    'size': 4,
                    'song_rating': 27,
                    'studio': 30,
                    'studio_ignore_the': 31,
                    'title': 9,
                    'title_ignore_the': 10,
                    'track_number': 7,
                    'unsorted': 37,
                    'video_rating': 18,
                    'video_runtime': 29,
                    'video_sort_title': 24,
                    'video_sort_title_ignore_the': 25,
                    'video_title': 23,
                    'video_year': 17}
        for sort_method in sort_methods:
            xbmcplugin.addSortMethod(self._plugin_handle, sort_map.get(sort_method, 0))
            pass
        pass

    def clone(self, new_path=None, new_params=None):
        if not new_path:
            new_path = self.get_path()
            pass

        if not new_params:
            new_params = self.get_params()
            pass

        new_context = KodiContext(path=new_path, params=new_params, plugin_name=self._plugin_name,
                                  plugin_id=self._plugin_id, override=False)
        new_context._function_cache = self._function_cache
        new_context._search_history = self._search_history
        new_context._favorite_list = self._favorite_list
        new_context._watch_later_list = self._watch_later_list
        new_context._access_manager = self._access_manager
        new_context._ui = self._ui
        new_context._video_playlist = self._video_playlist
        new_context._video_player = self._video_player

        return new_context

    def execute(self, command):
        xbmc.executebuiltin(command)
        pass

    def sleep(self, milli_seconds):
        xbmc.sleep(milli_seconds)
        pass

    def resolve_item(self, item):
        kodi_items.process_item(self, item, resolve=True)
        pass

    def add_item(self, item):
        kodi_items.process_item(self, item)
        pass

    def end_of_content(self, succeeded=True):
        xbmcplugin.endOfDirectory(self.get_handle(), succeeded=succeeded)

        # override view mode
        settings = self.get_settings()
        if settings.is_override_view_enabled() and self._content_type and isinstance(self._content_type, basestring):
            view_id = settings.get_int(settings.VIEW_X % self._content_type, 50)
            self.log_debug('Override view mode to "%d"' % view_id)
            xbmc.executebuiltin('Container.SetViewMode(%d)' % view_id)
            pass
        pass

    pass