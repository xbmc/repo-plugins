# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals

import inputstreamhelper
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
from resources.lib.kodiwrappers import sortmethod

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode


def has_socks():
    ''' Test if socks is installed, and remember this information '''
    if not hasattr(has_socks, 'installed'):
        try:
            import socks  # pylint: disable=unused-variable,unused-import
            has_socks.installed = True
        except ImportError:
            has_socks.installed = False
            return None  # Detect if this is the first run
    return has_socks.installed


class KodiWrapper:

    def __init__(self, handle, url, addon):
        self._handle = handle
        self._url = url
        self._addon = addon
        self._addon_id = addon.getAddonInfo('id')

    def show_listing(self, list_items, sort=None, content_type='episodes'):
        listing = []
        for title_item in list_items:
            list_item = xbmcgui.ListItem(label=title_item.title)
            url = self._url + '?' + urlencode(title_item.url_dict)
            list_item.setProperty('IsPlayable', str(title_item.is_playable))

            if title_item.art_dict:
                list_item.setArt(title_item.art_dict)

            if title_item.video_dict:
                list_item.setInfo('video', infoLabels=title_item.video_dict)

            listing.append((url, list_item, not title_item.is_playable))

        ok = xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))

        if sort is not None:
            kodi_sorts = {sortmethod.ALPHABET: xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE}
            kodi_sortmethod = kodi_sorts.get(sort)
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=kodi_sortmethod)
        else:
            xbmcplugin.addSortMethod(handle=self._handle, sortMethod=xbmcplugin.SORT_METHOD_NONE)

        xbmcplugin.setContent(self._handle, content=content_type)
        xbmcplugin.endOfDirectory(self._handle, ok)

    def play(self, video):
        play_item = xbmcgui.ListItem(path=video.stream_url)
        if video.stream_url is not None and video.use_inputstream_adaptive:
            play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')
            play_item.setProperty('inputstream.adaptive.manifest_type', 'mpd')
            play_item.setMimeType('application/dash+xml')
            play_item.setContentLookup(False)
            if video.license_key is not None:
                is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
                if is_helper.check_inputstream():
                    play_item.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
                    play_item.setProperty('inputstream.adaptive.license_key', video.license_key)

        subtitles_visible = self.get_setting('showsubtitles') == 'true'
        # Separate subtitle url for hls-streams
        if subtitles_visible and video.subtitle_url is not None:
            self.log_notice('subtitle ' + video.subtitle_url)
            play_item.setSubtitles([video.subtitle_url])

        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)
        while not xbmc.Player().isPlaying() and not xbmc.Monitor().abortRequested():
            xbmc.sleep(100)
        xbmc.Player().showSubtitles(subtitles_visible)

    def show_ok_dialog(self, title, message):
        xbmcgui.Dialog().ok(self._addon.getAddonInfo('name'), title, message)

    def get_localized_string(self, string_id):
        return self._addon.getLocalizedString(string_id)

    def get_localized_dateshort(self):
        return xbmc.getRegion('dateshort')

    def get_setting(self, setting_id):
        return self._addon.getSetting(setting_id)

    def open_settings(self):
        self._addon.openSettings()

    def get_global_setting(self, setting):
        json_result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": {"setting": "%s"}, "id": 1}' % setting)
        return json.loads(json_result)['result']['value']

    def get_proxies(self):
        usehttpproxy = self.get_global_setting('network.usehttpproxy')
        if usehttpproxy is False:
            return None

        httpproxytype = self.get_global_setting('network.httpproxytype')

        socks_supported = has_socks()
        if httpproxytype != 0 and not socks_supported:
            # Only open the dialog the first time (to avoid multiple popups)
            if socks_supported is None:
                message = self.get_localized_string(32061)
                self.show_ok_dialog('', message)
            return None

        proxy_types = ['http', 'socks4', 'socks4a', 'socks5', 'socks5h']
        if 0 <= httpproxytype <= 5:
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

    # NOTE: normally inputstream adaptive will always be installed, this only applies for people uninstalling inputstream adaptive while this addon is disabled
    def has_inputstream_adaptive_installed(self):
        return xbmc.getCondVisibility('System.HasAddon("{0}")'.format('inputstream.adaptive')) == 1

    def can_play_widevine(self):
        kodi_version = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
        return kodi_version > 17

    def get_userdata_path(self):
        return xbmc.translatePath(self._addon.getAddonInfo('profile'))

    def get_addon_path(self):
        return xbmc.translatePath(self._addon.getAddonInfo('path'))

    def get_path(self, path):
        return xbmc.translatePath(path)

    def make_dir(self, path):
        xbmcvfs.mkdir(path)

    def check_if_path_exists(self, path):
        return xbmcvfs.exists(path)

    def open_path(self, path):
        return json.loads(open(path, 'r').read())

    def delete_path(self, path):
        return xbmcvfs.delete(path)

    def log_notice(self, message):
        ''' Log info messages to Kodi '''
        xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGNOTICE)

    def log_error(self, message):
        ''' Log error messages to Kodi '''
        xbmc.log(msg='[%s] %s' % (self._addon_id, message), level=xbmc.LOGERROR)
