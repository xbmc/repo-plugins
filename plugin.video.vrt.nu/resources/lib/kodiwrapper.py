# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' All functionality that requires Kodi imports '''

# pylint: disable=too-many-function-args

from __future__ import absolute_import, division, unicode_literals
from contextlib import contextmanager
import xbmc
import xbmcplugin
from xbmcaddon import Addon
from statichelper import from_unicode, to_unicode

try:  # Python 3
    from urllib.parse import unquote
except ImportError:  # Python 2
    from urllib2 import unquote

SORT_METHODS = dict(
    # date=xbmcplugin.SORT_METHOD_DATE,
    dateadded=xbmcplugin.SORT_METHOD_DATEADDED,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    # genre=xbmcplugin.SORT_METHOD_GENRE,
    # label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    label=xbmcplugin.SORT_METHOD_LABEL,
    # none=xbmcplugin.SORT_METHOD_UNSORTED,
    # FIXME: We would like to be able to sort by unprefixed title (ignore date/episode prefix)
    # title=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
)

LOG_LEVELS = dict(
    Quiet=0,
    Info=1,
    Verbose=2,
    Debug=3,
)

XBMC_LOG_LEVELS = dict(
    Quiet=xbmc.LOGNONE,
    Info=xbmc.LOGNOTICE,
    Verbose=xbmc.LOGINFO,
    Debug=xbmc.LOGDEBUG,
)

WEEKDAY_LONG = {
    '0': xbmc.getLocalizedString(17),
    '1': xbmc.getLocalizedString(11),
    '2': xbmc.getLocalizedString(12),
    '3': xbmc.getLocalizedString(13),
    '4': xbmc.getLocalizedString(14),
    '5': xbmc.getLocalizedString(15),
    '6': xbmc.getLocalizedString(16),
}

MONTH_LONG = {
    '01': xbmc.getLocalizedString(21),
    '02': xbmc.getLocalizedString(22),
    '03': xbmc.getLocalizedString(23),
    '04': xbmc.getLocalizedString(24),
    '05': xbmc.getLocalizedString(25),
    '06': xbmc.getLocalizedString(26),
    '07': xbmc.getLocalizedString(27),
    '08': xbmc.getLocalizedString(28),
    '09': xbmc.getLocalizedString(29),
    '10': xbmc.getLocalizedString(30),
    '11': xbmc.getLocalizedString(31),
    '12': xbmc.getLocalizedString(32),
}

WEEKDAY_SHORT = {
    '0': xbmc.getLocalizedString(47),
    '1': xbmc.getLocalizedString(41),
    '2': xbmc.getLocalizedString(42),
    '3': xbmc.getLocalizedString(43),
    '4': xbmc.getLocalizedString(44),
    '5': xbmc.getLocalizedString(45),
    '6': xbmc.getLocalizedString(46),
}

MONTH_SHORT = {
    '01': xbmc.getLocalizedString(51),
    '02': xbmc.getLocalizedString(52),
    '03': xbmc.getLocalizedString(53),
    '04': xbmc.getLocalizedString(54),
    '05': xbmc.getLocalizedString(55),
    '06': xbmc.getLocalizedString(56),
    '07': xbmc.getLocalizedString(57),
    '08': xbmc.getLocalizedString(58),
    '09': xbmc.getLocalizedString(59),
    '10': xbmc.getLocalizedString(60),
    '11': xbmc.getLocalizedString(61),
    '12': xbmc.getLocalizedString(62),
}


def has_socks():
    ''' Test if socks is installed, and remember this information '''
    if hasattr(has_socks, 'installed'):
        return has_socks.installed
    try:
        import socks  # noqa: F401; pylint: disable=unused-variable,unused-import
        has_socks.installed = True
        return True
    except ImportError:
        has_socks.installed = False
        return None  # Detect if this is the first run


class SafeDict(dict):
    ''' A safe dictionary implementation that does not break down on missing keys '''
    def __missing__(self, key):
        ''' Replace missing keys with the original placeholder '''
        return '{' + key + '}'


class KodiWrapper:
    ''' A wrapper around all Kodi functionality '''

    def __init__(self, addon):
        ''' Initialize the Kodi wrapper '''
        if addon:
            self.addon = addon
            self.plugin = addon['plugin']
            self._handle = self.plugin.handle
            self._url = self.plugin.base_url
        self._addon = Addon()
        self._addon_id = to_unicode(self._addon.getAddonInfo('id'))
        self._addon_fanart = to_unicode(self._addon.getAddonInfo('fanart'))
        self._debug_logging = self.get_global_setting('debug.showloginfo')   # Returns a boolean
        self._max_log_level = LOG_LEVELS.get(self.get_setting('max_log_level', 'Debug'), 3)
        self._usemenucaching = self.get_setting('usemenucaching', 'true') == 'true'
        self._cache_path = self.get_userdata_path() + 'cache/'
        self._tokens_path = self.get_userdata_path() + 'tokens/'
        self._system_locale_works = None

    def url_for(self, name, *args, **kwargs):
        ''' Wrapper for routing.url_for() to lookup by name '''
        return self.plugin.url_for(self.addon[name], *args, **kwargs)

    def show_listing(self, list_items, category=None, sort='unsorted', ascending=True, content=None, cache=None):
        ''' Show a virtual directory in Kodi '''
        from xbmcgui import ListItem

        xbmcplugin.setPluginFanart(handle=self._handle, image=from_unicode(self._addon_fanart))

        if cache is None:
            cache = self._usemenucaching

        if content:
            # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
            xbmcplugin.setContent(self._handle, content=content)

        # Jump through hoops to get a stable breadcrumbs implementation
        category_label = ''
        if category:
            if not content:
                category_label = 'VRT NU / '
            if isinstance(category, int):
                category_label += self.localize(category)
            else:
                category_label += category
        elif not content:
            category_label = 'VRT NU'
        xbmcplugin.setPluginCategory(handle=self._handle, category=category_label)

        # FIXME: Since there is no way to influence descending order, we force it here
        if not ascending:
            sort = 'unsorted'

        # NOTE: When showing tvshow listings and 'showoneoff' was set, force 'unsorted'
        if self.get_setting('showoneoff', 'true') == 'true' and sort == 'label' and content == 'tvshows':
            sort = 'unsorted'

        # Add all sort methods to GUI (start with preferred)
        xbmcplugin.addSortMethod(handle=self._handle, sortMethod=SORT_METHODS[sort])
        for key in sorted(SORT_METHODS):
            if key != sort:
                xbmcplugin.addSortMethod(handle=self._handle, sortMethod=SORT_METHODS[key])

        # FIXME: This does not appear to be working, we have to order it ourselves
#        xbmcplugin.setProperty(handle=self._handle, key='sort.ascending', value='true' if ascending else 'false')
#        if ascending:
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(SORT_METHODS[sort]))
#        else:
#            # NOTE: When descending, use unsorted
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(SORT_METHODS['unsorted']))

        listing = []
        for title_item in list_items:
            # Three options:
            #  - item is a virtual directory/folder (not playable, path)
            #  - item is a playable file (playable, path)
            #  - item is non-actionable item (not playable, no path)
            is_folder = bool(not title_item.is_playable and title_item.path)
            is_playable = bool(title_item.is_playable and title_item.path)

            list_item = ListItem(label=title_item.title)

            if title_item.prop_dict:
                # FIXME: The setProperties method is new in Kodi18, so we cannot use it just yet.
                # list_item.setProperties(values=title_item.prop_dict)
                for key, value in title_item.prop_dict.items():
                    list_item.setProperty(key=key, value=str(value))
            list_item.setProperty(key='IsInternetStream', value='true' if is_playable else 'false')
            list_item.setProperty(key='IsPlayable', value='true' if is_playable else 'false')

            # FIXME: The setIsFolder method is new in Kodi18, so we cannot use it just yet.
            # list_item.setIsFolder(is_folder)

            if title_item.art_dict:
                list_item.setArt(dict(fanart=self._addon_fanart))
                list_item.setArt(title_item.art_dict)

            if title_item.info_dict:
                # type is one of: video, music, pictures, game
                list_item.setInfo(type='video', infoLabels=title_item.info_dict)

            if title_item.stream_dict:
                # type is one of: video, audio, subtitle
                list_item.addStreamInfo('video', title_item.stream_dict)

            if title_item.context_menu:
                list_item.addContextMenuItems(title_item.context_menu)

            url = None
            if title_item.path:
                url = title_item.path

            listing.append((url, list_item, is_folder))

        succeeded = xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        xbmcplugin.endOfDirectory(self._handle, succeeded, cacheToDisc=cache)

    def play(self, stream, video=None):
        ''' Create a virtual directory listing to play its only item '''
        from xbmcgui import ListItem
        play_item = ListItem(path=stream.stream_url)
        if video and hasattr(video, 'info_dict'):
            play_item.setProperty('subtitle', video.title)
            play_item.setArt(video.art_dict)
            play_item.setInfo(
                type='video',
                infoLabels=video.info_dict
            )
        play_item.setProperty('inputstream.adaptive.max_bandwidth', str(self.get_max_bandwidth() * 1000))
        play_item.setProperty('network.bandwidth', str(self.get_max_bandwidth() * 1000))
        if stream.stream_url is not None and stream.use_inputstream_adaptive:
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            play_item.setMimeType('application/dash+xml')
            play_item.setContentLookup(False)
            if stream.license_key is not None:
                import inputstreamhelper
                is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
                if is_helper.check_inputstream():
                    play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    play_item.setProperty('inputstream.adaptive.license_key', stream.license_key)

        subtitles_visible = self.get_setting('showsubtitles', 'true') == 'true'
        # Separate subtitle url for hls-streams
        if subtitles_visible and stream.subtitle_url is not None:
            self.log('Subtitle URL: {url}', 'Verbose', url=unquote(stream.subtitle_url))
            play_item.setSubtitles([stream.subtitle_url])

        self.log('Play: {url}', 'Info', url=unquote(stream.stream_url))

        # To support video playback directly from RunPlugin() we need to use xbmc.Player().play instead of
        # setResolvedUrl that only works with PlayMedia() or with internal playable menu items
        xbmcplugin.setResolvedUrl(self._handle, bool(stream.stream_url), listitem=play_item)

        while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
            xbmc.sleep(100)
        xbmc.Player().showSubtitles(subtitles_visible)

    def get_search_string(self):
        ''' Ask the user for a search string '''
        search_string = None
        keyboard = xbmc.Keyboard('', self.localize(30097))
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = to_unicode(keyboard.getText())
        return search_string

    def show_ok_dialog(self, heading='', message=''):
        ''' Show Kodi's OK dialog '''
        from xbmcgui import Dialog
        if not heading:
            heading = self._addon.getAddonInfo('name')
        return Dialog().ok(heading=heading, line1=message)

    def show_notification(self, heading='', message='', icon='info', time=4000):
        ''' Show a Kodi notification '''
        from xbmcgui import Dialog
        if not heading:
            heading = self._addon.getAddonInfo('name')
        Dialog().notification(heading=heading, message=message, icon=icon, time=time)

    def show_multiselect(self, heading='', options=None, autoclose=0, preselect=None, use_details=False):
        ''' Show a Kodi multi-select dialog '''
        from xbmcgui import Dialog
        if not heading:
            heading = self._addon.getAddonInfo('name')
        return Dialog().multiselect(heading=heading, options=options, autoclose=autoclose, preselect=preselect, useDetails=use_details)

    def set_locale(self):
        ''' Load the proper locale for date strings '''
        import locale
        locale_lang = self.get_global_setting('locale.language').split('.')[-1]
        try:
            # NOTE: This only works if the platform supports the Kodi configured locale
            locale.setlocale(locale.LC_ALL, locale_lang)
            return True
        except Exception as exc:  # pylint: disable=broad-except
            if locale_lang == 'en_gb':
                return True
            self.log("Your system does not support locale '{locale}': {error}", 'Debug', locale=locale_lang, error=exc)
            return False

    def localize(self, string_id, **kwargs):
        ''' Return the translated string from the .po language files, optionally translating variables '''
        if kwargs:
            import string
            return string.Formatter().vformat(self._addon.getLocalizedString(string_id), (), SafeDict(**kwargs))

        return self._addon.getLocalizedString(string_id)

    def localize_date(self, date, strftime):
        ''' Return a localized date, even if the system does not support your locale '''
        if self._system_locale_works is None:
            self._system_locale_works = self.set_locale()
        if not self._system_locale_works:
            if '%a' in strftime:
                strftime = strftime.replace('%a', WEEKDAY_SHORT[date.strftime('%w')])
            elif '%A' in strftime:
                strftime = strftime.replace('%A', WEEKDAY_LONG[date.strftime('%w')])
            if '%b' in strftime:
                strftime = strftime.replace('%b', MONTH_SHORT[date.strftime('%m')])
            elif '%B' in strftime:
                strftime = strftime.replace('%B', MONTH_LONG[date.strftime('%m')])
        return date.strftime(strftime)

    def localize_datelong(self, date):
        ''' Return a localized long date string '''
        return self.localize_date(date, xbmc.getRegion('datelong'))

    def localize_from_data(self, name, data):
        ''' Return a localized name string from a Dutch data object '''
        # Return if Kodi language is Dutch
        if self.get_global_setting('locale.language') == 'resource.language.nl_nl':
            return name
        return next((self.localize(item.get('msgctxt')) for item in data if item.get('name') == name), name)

    def get_setting(self, setting_id, default=None):
        ''' Get an add-on setting '''
        value = to_unicode(self._addon.getSetting(setting_id))
        if value == '' and default is not None:
            return default
        return value

    def set_setting(self, setting_id, setting_value):
        ''' Set an add-on setting '''
        return self._addon.setSetting(setting_id, setting_value)

    def open_settings(self):
        ''' Open the add-in settings window, shows Credentials '''
        self._addon.openSettings()

    @staticmethod
    def get_global_setting(setting):
        ''' Get a Kodi setting '''
        import json
        json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": "%s"}, "id": 1}' % setting)
        return json.loads(json_result).get('result', dict()).get('value')

    def get_max_bandwidth(self):
        ''' Get the max bandwidth based on Kodi and VRT NU add-on settings '''
        vrtnu_max_bandwidth = int(self.get_setting('max_bandwidth', '0'))
        global_max_bandwidth = int(self.get_global_setting('network.bandwidth'))
        if vrtnu_max_bandwidth != 0 and global_max_bandwidth != 0:
            return min(vrtnu_max_bandwidth, global_max_bandwidth)
        if vrtnu_max_bandwidth != 0:
            return vrtnu_max_bandwidth
        if global_max_bandwidth != 0:
            return global_max_bandwidth
        return 0

    def get_proxies(self):
        ''' Return a usable proxies dictionary from Kodi proxy settings '''
        usehttpproxy = self.get_global_setting('network.usehttpproxy')
        if usehttpproxy is not True:
            return None

        try:
            httpproxytype = int(self.get_global_setting('network.httpproxytype'))
        except ValueError:
            httpproxytype = 0

        socks_supported = has_socks()
        if httpproxytype != 0 and not socks_supported:
            # Only open the dialog the first time (to avoid multiple popups)
            if socks_supported is None:
                self.show_ok_dialog('', self.localize(30966))  # Requires PySocks
            return None

        proxy_types = ['http', 'socks4', 'socks4a', 'socks5', 'socks5h']
        if 0 <= httpproxytype < 5:
            httpproxyscheme = proxy_types[httpproxytype]
        else:
            httpproxyscheme = 'http'

        httpproxyserver = self.get_global_setting('network.httpproxyserver')
        httpproxyport = self.get_global_setting('network.httpproxyport')
        httpproxyusername = self.get_global_setting('network.httpproxyusername')
        httpproxypassword = self.get_global_setting('network.httpproxypassword')

        if httpproxyserver and httpproxyport and httpproxyusername and httpproxypassword:
            proxy_address = '%s://%s:%s@%s:%s' % (httpproxyscheme, httpproxyusername, httpproxypassword, httpproxyserver, httpproxyport)
        elif httpproxyserver and httpproxyport and httpproxyusername:
            proxy_address = '%s://%s@%s:%s' % (httpproxyscheme, httpproxyusername, httpproxyserver, httpproxyport)
        elif httpproxyserver and httpproxyport:
            proxy_address = '%s://%s:%s' % (httpproxyscheme, httpproxyserver, httpproxyport)
        elif httpproxyserver:
            proxy_address = '%s://%s' % (httpproxyscheme, httpproxyserver)
        else:
            return None

        return dict(http=proxy_address, https=proxy_address)

    @staticmethod
    def get_cond_visibility(condition):
        ''' Test a condition in XBMC '''
        return xbmc.getCondVisibility(condition)

    def has_inputstream_adaptive(self):
        ''' Whether InputStream Adaptive is installed and enabled in add-on settings '''
        return self.get_setting('useinputstreamadaptive', 'true') == 'true' and xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') == 1

    def credentials_filled_in(self):
        ''' Whether the add-on has credentials filled in '''
        return bool(self.get_setting('username') and self.get_setting('password'))

    @staticmethod
    def kodi_version():
        ''' Returns major Kodi version '''
        return int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])

    def can_play_drm(self):
        ''' Whether this Kodi can do DRM using InputStream Adaptive '''
        return self.get_setting('usedrm', 'true') == 'true' and self.get_setting('useinputstreamadaptive', 'true') == 'true' and self.supports_drm()

    def supports_drm(self):
        ''' Whether this Kodi version supports DRM decryption using InputStream Adaptive '''
        return self.kodi_version() > 17

    def get_userdata_path(self):
        ''' Return the profile's userdata path '''
        return to_unicode(xbmc.translatePath(self._addon.getAddonInfo('profile')))

    def get_tokens_path(self):
        ''' Return the userdata tokens path '''
        return self._tokens_path

    def get_addon_info(self, key):
        ''' Return addon information '''
        return self._addon.getAddonInfo(key)

    @staticmethod
    def listdir(path):
        ''' Return all files in a directory (using xbmcvfs)'''
        from xbmcvfs import listdir
        return listdir(path)

    def mkdir(self, path):
        ''' Create a directory (using xbmcvfs) '''
        from xbmcvfs import mkdir
        self.log("Create directory '{path}'.", 'Debug', path=path)
        return mkdir(path)

    def mkdirs(self, path):
        ''' Create directory including parents (using xbmcvfs) '''
        from xbmcvfs import mkdirs
        self.log("Recursively create directory '{path}'.", 'Debug', path=path)
        return mkdirs(path)

    @staticmethod
    def check_if_path_exists(path):
        ''' Whether the path exists (using xbmcvfs)'''
        from xbmcvfs import exists
        return exists(path)

    @staticmethod
    @contextmanager
    def open_file(path, flags='r'):
        ''' Open a file (using xbmcvfs) '''
        from xbmcvfs import File
        fdesc = File(path, flags)
        yield fdesc
        fdesc.close()

    @staticmethod
    def stat_file(path):
        ''' Return information about a file (using xbmcvfs) '''
        from xbmcvfs import Stat
        return Stat(path)

    def delete_file(self, path):
        ''' Remove a file (using xbmcvfs) '''
        from xbmcvfs import delete
        self.log("Delete file '{path}'.", 'Debug', path=path)
        return delete(path)

    def delete_cached_thumbnail(self, url):
        ''' Remove a cached thumbnail from Kodi in an attempt to get a realtime live screenshot '''
        import json
        # Get texture
        textures_json = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Textures.GetTextures", "params": \
        {"filter": {"field": "url", "operator": "is", "value":"%s"}}, "id": 1}' % url))
        result = textures_json.get('result')
        if result and result.get('textures'):
            texture_id = next((texture.get('textureid') for texture in textures_json.get('result').get('textures')), None)
            self.log('found texture_id {id} for url {url} in texture cache', 'Verbose', id=texture_id, url=url)
            if texture_id:
                # Remove texture
                remove_json = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Textures.RemoveTexture", "params": \
                {"textureid": %d}, "id": 1}' % texture_id))
                result = remove_json.get('result')
                if result and result == 'OK':
                    self.log('succesfully removed {url} from texture cache', 'Verbose', url=url)
                    return True
                error_message = remove_json.get('error').get('message')
                if error_message:
                    self.log_error('failed to remove %s from texture cache: %s' % (url, error_message))
                    return False
        self.log_error('%s not found in texture cache' % url)
        return False

    @staticmethod
    def md5(data):
        ''' Return an MD5 checksum '''
        import hashlib
        return hashlib.md5(data)

    @staticmethod
    def human_delta(seconds):
        ''' Return a human-readable representation of the TTL '''
        from math import floor
        days = int(floor(seconds / (24 * 60 * 60)))
        seconds = seconds % (24 * 60 * 60)
        hours = int(floor(seconds / (60 * 60)))
        seconds = seconds % (60 * 60)
        if days:
            return '%d day%s and %d hour%s' % (days, 's' if days != 1 else '', hours, 's' if hours != 1 else '')
        minutes = int(floor(seconds / 60))
        seconds = seconds % 60
        if hours:
            return '%d hour%s and %d minute%s' % (hours, 's' if hours != 1 else '', minutes, 's' if minutes != 1 else '')
        if minutes:
            return '%d minute%s and %d second%s' % (minutes, 's' if minutes != 1 else '', seconds, 's' if seconds != 1 else '')
        return '%d second%s' % (seconds, 's' if seconds != 1 else '')

    def get_cache(self, path, ttl=None):
        ''' Get the content from cache, if it's still fresh '''
        if self.get_setting('usehttpcaching', 'true') == 'false':
            return None

        fullpath = self._cache_path + path
        if not self.check_if_path_exists(fullpath):
            return None

        import time
        mtime = self.stat_file(fullpath).st_mtime()
        now = time.mktime(time.localtime())
        if ttl is None or now - mtime < ttl:
            import json
            if ttl is None:
                self.log("Cache '{path}' is forced from cache.", 'Debug', path=path)
            else:
                self.log("Cache '{path}' is fresh, expires in {time}.", 'Debug', path=path, time=self.human_delta(mtime + ttl - now))
            with self.open_file(fullpath, 'r') as fdesc:
                try:
                    # return json.load(fdesc, encoding='utf-8')
                    return json.load(fdesc)
                except (ValueError, TypeError):
                    return None

        return None

    def update_cache(self, path, data):
        ''' Update the cache, if necessary '''
        if self.get_setting('usehttpcaching', 'true') == 'false':
            return

        import hashlib
        import json
        fullpath = self._cache_path + path
        if self.check_if_path_exists(fullpath):
            with self.open_file(fullpath) as fdesc:
                cachefile = fdesc.read().encode('utf-8')
            md5 = self.md5(cachefile)
        else:
            md5 = 0
            # Create cache directory if missing
            if not self.check_if_path_exists(self._cache_path):
                self.mkdirs(self._cache_path)

        # Avoid writes if possible (i.e. SD cards)
        if md5 != hashlib.md5(json.dumps(data).encode('utf-8')):
            self.log("Write cache '{path}'.", 'Debug', path=path)
            with self.open_file(fullpath, 'w') as fdesc:
                # json.dump(data, fdesc, encoding='utf-8')
                json.dump(data, fdesc)
        else:
            # Update timestamp
            import os
            self.log("Cache '{path}' has not changed, updating mtime only.", 'Debug', path=path)
            os.utime(path)

    def refresh_caches(self, cache_file=None):
        ''' Invalidate the needed caches and refresh container '''
        self.invalidate_caches(expr=cache_file)
        self.container_refresh()
        self.show_notification(message=self.localize(30981))

    def invalidate_caches(self, expr=None):
        ''' Invalidate multiple cache files '''
        import fnmatch
        _, files = self.listdir(self._cache_path)
        if expr:
            files = fnmatch.filter(files, expr)
        for filename in files:
            self.delete_file(self._cache_path + filename)
        self.delete_file(self._cache_path + 'favorites.json')
        self.delete_file(self._cache_path + 'oneoff.json')

    @staticmethod
    def input_down():
        ''' Move the cursor down '''
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Input.Down", "id": 1}')

    def container_refresh(self):
        ''' Refresh the current container '''
        self.log('Execute: Container.Refresh', 'Debug')
        xbmc.executebuiltin('Container.Refresh')

    def end_of_directory(self):
        ''' Close a virtual directory, required to avoid a waiting Kodi '''
        xbmcplugin.endOfDirectory(handle=self._handle, succeeded=False, updateListing=False, cacheToDisc=False)

    def log_access(self, url, query_string=None, log_level='Verbose'):
        ''' Log addon access '''
        if LOG_LEVELS.get(log_level, 0) <= self._max_log_level:
            message = '[%s] Access: %s' % (self._addon_id, url + ('?' + query_string if query_string else ''))
            xbmc.log(msg=from_unicode(message), level=xbmc.LOGNOTICE)

    def log(self, message, log_level='Info', **kwargs):
        ''' Log info messages to Kodi '''
        cur_log_level = LOG_LEVELS.get(log_level, 0)
        if not self._debug_logging and 1 < cur_log_level <= self._max_log_level:
            # If Debug Logging is not enabled, Kodi filters everything up to NOTICE out
            log_level = 'Info'
        if kwargs:
            import string
            message = string.Formatter().vformat(message, (), SafeDict(**kwargs))
        message = '[{addon}] {message}'.format(addon=self._addon_id, message=message)
        xbmc.log(msg=from_unicode(message), level=XBMC_LOG_LEVELS.get(log_level))

    def log_error(self, message, **kwargs):
        ''' Log error messages to Kodi '''
        if kwargs:
            import string
            message = string.Formatter().vformat(message, (), SafeDict(**kwargs))
        message = '[{addon}] {message}'.format(addon=self._addon_id, message=message)
        xbmc.log(msg=from_unicode(message), level=xbmc.LOGERROR)
