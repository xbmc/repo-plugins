# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from contextlib import contextmanager

import xbmc
import xbmcplugin

try:
    from urllib.parse import urlencode, unquote
except ImportError:
    from urllib import urlencode
    from urllib2 import unquote

sort_methods = dict(
    # date=xbmcplugin.SORT_METHOD_DATE,
    dateadded=xbmcplugin.SORT_METHOD_DATEADDED,
    duration=xbmcplugin.SORT_METHOD_DURATION,
    episode=xbmcplugin.SORT_METHOD_EPISODE,
    # genre=xbmcplugin.SORT_METHOD_GENRE,
    label=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
    # none=xbmcplugin.SORT_METHOD_UNSORTED,
    # FIXME: We would like to be able to sort by unprefixed title (ignore date/episode prefix)
    # title=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
    unsorted=xbmcplugin.SORT_METHOD_UNSORTED,
)

log_levels = dict(
    Quiet=0,
    Info=1,
    Verbose=2,
    Debug=3,
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
    if not hasattr(has_socks, 'installed'):
        try:
            import socks  # noqa: F401; pylint: disable=unused-variable,unused-import
            has_socks.installed = True
        except ImportError:
            has_socks.installed = False
            return None  # Detect if this is the first run
    return has_socks.installed


class KodiWrapper:
    ''' A wrapper around all Kodi functionality '''

    def __init__(self, handle, url, addon):
        ''' Initialize the Kodi wrapper '''
        self._handle = handle
        self._url = url
        self._addon = addon
        self._addon_id = addon.getAddonInfo('id')
        self._max_log_level = log_levels.get(self.get_setting('max_log_level'), 3)
        self._usemenucaching = self.get_setting('usemenucaching') == 'true'
        self._cache_path = self.get_userdata_path() + 'cache/'
        self._system_locale_works = None

    def install_widevine(self):
        ''' Install Widevine using inputstreamhelper '''
        ok = self.show_yesno_dialog(heading=self.localize(30971), message=self.localize(30972))
        if not ok:
            return
        try:
            from inputstreamhelper import Helper
            is_helper = Helper('mpd', drm='com.widevine.alpha')
            if is_helper.check_inputstream():
                self.show_notification(heading=self.localize(30971), message=self.localize(30974), icon='info', time=5000)
            else:
                self.show_notification(heading=self.localize(30971), message=self.localize(30973), icon='error', time=5000)
        except Exception:
            self.show_notification(heading=self.localize(30971), message=self.localize(30973), icon='error', time=5000)
        self.end_of_directory()

    def show_listing(self, list_items, sort='unsorted', ascending=True, content=None, cache=None):
        ''' Show a virtual directory in Kodi '''
        import xbmcgui
        listing = []

        if cache is None:
            cache = self._usemenucaching

        if content:
            # content is one of: files, songs, artists, albums, movies, tvshows, episodes, musicvideos
            xbmcplugin.setContent(self._handle, content=content)

        # FIXME: Since there is no way to influence descending order, we force it here
        if not ascending:
            sort = 'unsorted'

        # Add all sort methods to GUI (start with preferred)
        xbmcplugin.addSortMethod(handle=self._handle, sortMethod=sort_methods[sort])
        for key in sorted(sort_methods):
            if key != sort:
                xbmcplugin.addSortMethod(handle=self._handle, sortMethod=sort_methods[key])

        # FIXME: This does not appear to be working, we have to order it ourselves
#        xbmcplugin.setProperty(handle=self._handle, key='sort.ascending', value='true' if ascending else 'false')
#        if ascending:
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(sort_methods[sort]))
#        else:
#            # NOTE: When descending, use unsorted
#            xbmcplugin.setProperty(handle=self._handle, key='sort.order', value=str(sort_methods['unsorted']))

        for title_item in list_items:
            # Three options:
            #  - item is a virtual directory/folder (not playable, url_dict)
            #  - item is a playable file (playable, url_dict)
            #  - item is non-actionable item (not playable, no url_dict)
            is_folder = bool(not title_item.is_playable and title_item.url_dict)
            is_playable = bool(title_item.is_playable and title_item.url_dict)

            list_item = xbmcgui.ListItem(label=title_item.title, thumbnailImage=title_item.art_dict.get('thumb'))
            list_item.setProperty(key='IsPlayable', value='true' if is_playable else 'false')

            # FIXME: The setIsFolder is new in Kodi18, so we cannot use it just yet.
            # list_item.setIsFolder(is_folder)

            if title_item.art_dict:
                list_item.setArt(title_item.art_dict)

            if title_item.video_dict:
                # type is one of: video, music, pictures, game
                list_item.setInfo(type='video', infoLabels=title_item.video_dict)

            if title_item.context_menu:
                list_item.addContextMenuItems(title_item.context_menu)

            url = None
            if title_item.url_dict:
                url = self._url + '?' + urlencode(title_item.url_dict)

            listing.append((url, list_item, is_folder))

        ok = xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        xbmcplugin.endOfDirectory(self._handle, ok, cacheToDisc=cache)

    def play(self, video):
        ''' Create a virtual directory listing to play its only item '''
        import xbmcgui
        play_item = xbmcgui.ListItem(path=video.stream_url)
        play_item.setProperty('inputstream.adaptive.max_bandwidth', str(self.get_max_bandwidth() * 1000))
        play_item.setProperty('network.bandwidth', str(self.get_max_bandwidth() * 1000))
        if video.stream_url is not None and video.use_inputstream_adaptive:
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            play_item.setMimeType('application/dash+xml')
            play_item.setContentLookup(False)
            if video.license_key is not None:
                import inputstreamhelper
                is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
                if is_helper.check_inputstream():
                    play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    play_item.setProperty('inputstream.adaptive.license_key', video.license_key)

        subtitles_visible = self.get_setting('showsubtitles') == 'true'
        # Separate subtitle url for hls-streams
        if subtitles_visible and video.subtitle_url is not None:
            self.log_notice('Subtitle URL: ' + unquote(video.subtitle_url), 'Verbose')
            play_item.setSubtitles([video.subtitle_url])

        self.log_notice('Play: %s' % unquote(video.stream_url), 'Info')
        xbmcplugin.setResolvedUrl(self._handle, bool(video.stream_url), listitem=play_item)
        while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
            xbmc.sleep(100)
        xbmc.Player().showSubtitles(subtitles_visible)

    def get_search_string(self):
        ''' Ask the user for a search string '''
        search_string = None
        keyboard = xbmc.Keyboard('', self.localize(30097))
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_string = keyboard.getText()
        return search_string

    def show_ok_dialog(self, heading='', message=''):
        ''' Show Kodi's OK dialog '''
        import xbmcgui
        if not heading:
            heading = self._addon.getAddonInfo('name')
        xbmcgui.Dialog().ok(heading=heading, line1=message)

    def show_notification(self, heading='', message='', icon='info', time=4000):
        ''' Show a Kodi notification '''
        import xbmcgui
        if not heading:
            heading = self._addon.getAddonInfo('name')
        xbmcgui.Dialog().notification(heading=heading, message=message, icon=icon, time=time)

    def show_yesno_dialog(self, heading='', message=''):
        ''' Show Kodi's yes/no dialog '''
        import xbmcgui
        if not heading:
            heading = self._addon.getAddonInfo('name')
        return xbmcgui.Dialog().yesno(heading=self.localize(30971), line1=self.localize(30972))

    def set_locale(self):
        ''' Load the proper locale for date strings '''
        import locale
        locale_lang = self.get_global_setting('locale.language').split('.')[-1]
        try:
            # NOTE: This only works if the platform supports the Kodi configured locale
            locale.setlocale(locale.LC_ALL, locale_lang)
            return True
        except Exception as e:
            self.log_notice("Your system does not support locale '%s': %s" % (locale_lang, e), 'Debug')
            return False

    def localize(self, string_id):
        ''' Return the translated string from the .po language files '''
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

    def localize_dateshort(self, date):
        ''' Return a localized short date string '''
        return self.localize_date(date, xbmc.getRegion('dateshort'))

    def localize_datelong(self, date):
        ''' Return a localized long date string '''
        return self.localize_date(date, xbmc.getRegion('datelong'))

    def get_setting(self, setting_id):
        ''' Get an add-on setting '''
        return self._addon.getSetting(setting_id)

    def set_setting(self, setting_id, setting_value):
        ''' Set an add-on setting '''
        return self._addon.setSetting(setting_id, setting_value)

    def open_settings(self):
        ''' Open the add-in settings window, shows Credentials '''
        self._addon.openSettings()

    def get_global_setting(self, setting):
        ''' Get a Kodi setting '''
        import json
        json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": "%s"}, "id": 1}' % setting)
        return json.loads(json_result).get('result', dict()).get('value')

    def get_max_bandwidth(self):
        ''' Get the max bandwidth based on Kodi and VRT NU add-on settings '''
        vrtnu_max_bandwidth = int(self.get_setting('max_bandwidth'))
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
        if usehttpproxy is False:
            return None

        httpproxytype = self.get_global_setting('network.httpproxytype')

        socks_supported = has_socks()
        if httpproxytype != 0 and not socks_supported:
            # Only open the dialog the first time (to avoid multiple popups)
            if socks_supported is None:
                self.show_ok_dialog('', self.localize(30961))  # Requires PySocks
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

    def has_inputstream_adaptive(self):
        ''' Whether InputStream Adaptive is installed and enabled in add-on settings '''
        return self.get_setting('useinputstreamadaptive') == 'true' and xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)') == 1

    def has_credentials(self):
        ''' Whether the add-on has credentials configured '''
        return bool(self.get_setting('username') and self.get_setting('password'))

    def kodi_version(self):
        ''' Returns major Kodi version '''
        return int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])

    def can_play_drm(self):
        ''' Whether this Kodi can do DRM using InputStream Adaptive '''
        return self.get_setting('useinputstreamadaptive') == 'true' and self.kodi_version() > 17

    def get_userdata_path(self):
        ''' Return the profile's userdata path '''
        return xbmc.translatePath(self._addon.getAddonInfo('profile'))

    def get_addon_path(self):
        ''' Return the addon path '''
        return xbmc.translatePath(self._addon.getAddonInfo('path'))

    def get_path(self, path):
        ''' Convert a special path '''
        return xbmc.translatePath(path)

    def listdir(self, path):
        ''' Return all files in a directory (using xbmcvfs)'''
        import xbmcvfs
        return xbmcvfs.listdir(path)

    def mkdir(self, path):
        ''' Create a directory (using xbmcvfs) '''
        import xbmcvfs
        self.log_notice("Create directory '%s'." % path, 'Debug')
        return xbmcvfs.mkdir(path)

    def mkdirs(self, path):
        ''' Create directory including parents (using xbmcvfs) '''
        import xbmcvfs
        self.log_notice("Recursively create directory '%s'." % path, 'Debug')
        return xbmcvfs.mkdirs(path)

    def check_if_path_exists(self, path):
        ''' Whether the path exists (using xbmcvfs)'''
        import xbmcvfs
        return xbmcvfs.exists(path)

    @contextmanager
    def open_file(self, path, flags='r'):
        ''' Open a file (using xbmcvfs) '''
        import xbmcvfs
        f = xbmcvfs.File(path, flags)
        yield f
        f.close()

    def stat_file(self, path):
        ''' Return information about a file (using xbmcvfs) '''
        import xbmcvfs
        return xbmcvfs.Stat(path)

    def delete_file(self, path):
        ''' Remove a file (using xbmcvfs) '''
        import xbmcvfs
        self.log_notice("Delete file '%s'." % path, 'Debug')
        return xbmcvfs.delete(path)

    def md5(self, path):
        ''' Return an MD5 checksum of a file '''
        import hashlib
        with self.open_file(path) as f:
            return hashlib.md5(f.read().encode('utf-8'))

    def human_delta(self, seconds):
        ''' Return a human-readable representation of the TTL '''
        import math
        days = int(math.floor(seconds / (24 * 60 * 60)))
        seconds = seconds % (24 * 60 * 60)
        hours = int(math.floor(seconds / (60 * 60)))
        seconds = seconds % (60 * 60)
        if days:
            return '%d day%s and %d hour%s' % (days, 's' if days != 1 else '', hours, 's' if hours != 1 else '')
        minutes = int(math.floor(seconds / 60))
        seconds = seconds % 60
        if hours:
            return '%d hour%s and %d minute%s' % (hours, 's' if hours != 1 else '', minutes, 's' if minutes != 1 else '')
        if minutes:
            return '%d minute%s and %d second%s' % (minutes, 's' if minutes != 1 else '', seconds, 's' if seconds != 1 else '')
        return '%d second%s' % (seconds, 's' if seconds != 1 else '')

    def get_cache(self, path, ttl=None):
        ''' Get the content from cache, if it's still fresh '''
        if self.get_setting('usehttpcaching') == 'false':
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
                self.log_notice("Cache '%s' is forced from cache." % path, 'Debug')
            else:
                self.log_notice("Cache '%s' is fresh, expires in %s." % (path, self.human_delta(mtime + ttl - now)), 'Debug')
            with self.open_file(fullpath, 'r') as f:
                try:
                    # return json.load(f, encoding='utf-8')
                    return json.load(f)
                except ValueError:
                    return None

        return None

    def update_cache(self, path, data):
        ''' Update the cache, if necessary '''
        if self.get_setting('usehttpcaching') == 'false':
            return

        import hashlib
        import json
        fullpath = self._cache_path + path
        if self.check_if_path_exists(fullpath):
            md5 = self.md5(fullpath)
        else:
            md5 = 0
            # Create cache directory if missing
            if not self.check_if_path_exists(self._cache_path):
                self.mkdirs(self._cache_path)

        # Avoid writes if possible (i.e. SD cards)
        if md5 != hashlib.md5(json.dumps(data).encode('utf-8')):
            self.log_notice("Write cache '%s'." % path, 'Debug')
            with self.open_file(fullpath, 'w') as f:
                # json.dump(data, f, encoding='utf-8')
                json.dump(data, f)
        else:
            # Update timestamp
            import os
            self.log_notice("Cache '%s' has not changed, updating mtime only." % path, 'Debug')
            os.utime(path)

    def invalidate_cache(self, path):
        ''' Invalidate an existing cache file '''
        self.delete_file(self._cache_path + path)

    def invalidate_caches(self, expr=None):
        ''' Invalidate multiple cache files '''
        import fnmatch
        _, files = self.listdir(self._cache_path)
        if expr:
            files = fnmatch.filter(files, expr)
        for f in files:
            self.delete_file(self._cache_path + f)

    def container_refresh(self):
        ''' Refresh the current container '''
        self.log_notice('Execute: Container.Refresh', 'Debug')
        xbmc.executebuiltin('Container.Refresh')

    def container_update(self, url=None, path='', replace=False):
        ''' Update the current container '''
        if url is None:
            url = self._url
        self.log_notice('Execute: Container.Update(%s%s%s)' % (url, path, ',replace' if replace else ''), 'Debug')
        xbmc.executebuiltin('Container.Update(%s%s%s)' % (url, path, ',replace' if replace else ''))

    def end_of_directory(self):
        ''' Close a virtual directory, required to avoid a waiting Kodi '''
        xbmcplugin.endOfDirectory(handle=self._handle, succeeded=False, updateListing=False, cacheToDisc=False)

    def log_access(self, url, query_string, log_level='Verbose'):
        ''' Log addon access '''
        if log_levels.get(log_level, 0) <= self._max_log_level:
            message = url + ('?' if query_string else '') + query_string
            xbmc.log(msg='[%s] Access: %s' % (self._addon_id, unquote(message)), level=xbmc.LOGNOTICE)

    def log_notice(self, message, log_level='Info'):
        ''' Log info messages to Kodi '''
        if log_levels.get(log_level, 0) <= self._max_log_level:
            xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGNOTICE)

    def log_error(self, message, log_level='Info'):
        ''' Log error messages to Kodi '''
        xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGERROR)
