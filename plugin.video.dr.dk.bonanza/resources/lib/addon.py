#
#      Copyright (C) 2014 Tommy Winther, termehansen

#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu#
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
from urllib.parse import parse_qsl
import re
import requests_cache
from pathlib import Path
import time
from datetime import datetime
from inputstreamhelper import Helper
import traceback

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from html import unescape


BASE_URL = 'http://www.dr.dk/bonanza/'
addon = xbmcaddon.Addon()
get_setting = addon.getSetting
tr = addon.getLocalizedString
addon_path = Path(addon.getAddonInfo('path'))
addon_name = addon.getAddonInfo('name')
ICON = str(addon_path/'resources/icon.png')
FANART = str(addon_path/'resources/fanart.jpg')
HOURS_EXPIRE = 24
cleanup_every = 7


def make_notice(object):
    xbmc.log(str(object), xbmc.LOGINFO)


class BonanzaException(Exception):
    pass


class Bonanza(object):
    def __init__(self, plugin_url, plugin_handle):
        self._plugin_url = plugin_url
        self._plugin_handle = plugin_handle
        self.cachePath = Path(addon_path)
        self.init_sqlite_db()

    def init_sqlite_db(self):
        if not (self.cachePath/'requests_cleaned').exists():
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
        request_fname = str(self.cachePath/'requests.cache')
        self.session = requests_cache.CachedSession(
            request_fname, backend='sqlite', expire_after=3600*HOURS_EXPIRE)

        if (self.cachePath/'requests_cleaned').exists():
            if (time.time() - (self.cachePath/'requests_cleaned').stat().st_mtime)/3600/24 < cleanup_every:
                # less than self.cleanup_every days since last cleaning, no need...
                return

        # doing recache.db cleanup
        try:
            self.session.remove_expired_responses()
        except Exception:
            if (self.cachePath/'requests.cache.sqlite').exists():
                (self.cachePath/'requests.cache.sqlite').unlink()
            self.session = requests_cache.CachedSession(
                request_fname, backend='sqlite', expire_after=3600*self.expire_hours)
        (self.cachePath/'requests_cleaned').write_text(str(datetime.now()))

    def search(self):
        keyboard = xbmc.Keyboard('', tr(30001))
        keyboard.doModal()
        if keyboard.isConfirmed():
            html = self._downloadUrl('http://www.dr.dk/bonanza/sog?q=' + keyboard.getText().replace(' ', '+'))

            items = list()
            pattern = '<a.*?href="/bonanza/(serie/.*?)".*?' \
                      'data-src="(//asset\.dr\.dk/[^"]+)".*?' \
                      '<h3.*?>([^<]+)</h3>.*?<p>([^<]+)</p>'

            for m in re.finditer(pattern, html, re.DOTALL):
                url = BASE_URL + m.group(1)
                image = 'http:' + m.group(2)
                title = unescape(m.group(3))
                description = unescape(m.group(4))

                infoLabels = {
                    'title': title,
                    'plot': description,
                    'studio': addon_name}

                item = xbmcgui.ListItem(infoLabels['title'], offscreen=True)
                item.setArt({'fanart': FANART, 'icon': image, 'thumb': image})
                item.setProperty('IsPlayable', 'true')
                item.setInfo('video', infoLabels)

                url = '?mode=play&url=' + url
                items.append((self._plugin_url + url, item, False))
            xbmcplugin.addDirectoryItems(self._plugin_handle, items)

            xbmcplugin.endOfDirectory(self._plugin_handle)

    def showCategories(self):
        items = list()
        html = self._downloadUrl(BASE_URL)

        item = xbmcgui.ListItem(tr(30001), offscreen=True)
        item.setArt({'fanart': FANART, 'icon': ICON})
        xbmcplugin.addDirectoryItem(self._plugin_handle, self._plugin_url + '?mode=search', item, True)

        pattern = '<a href="(/bonanza/kategori/.*)">(.*)</a>'
        for m in re.finditer(pattern, html):
            path = m.group(1)
            title = m.group(2)

            item = xbmcgui.ListItem(title, offscreen=True)
            item.setArt({'fanart': FANART, 'icon': ICON})
            item.setInfo('video', infoLabels={
                'title': title
            })
            url = self._plugin_url + '?mode=subcat&url=http://www.dr.dk' + path
            items.append((url, item, True))

        xbmcplugin.addDirectoryItems(self._plugin_handle, items)
        xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showSubCategories(self, url):
        html = self._downloadUrl(url.replace(' ', '+'))
        self.addSubCategories(html)
        xbmcplugin.addSortMethod(self._plugin_handle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(self._plugin_handle)

    def showContent(self, url):
        html = self._downloadUrl(url)
        self.addContent(html)

        xbmcplugin.endOfDirectory(self._plugin_handle)

    def addSubCategories(self, html):
        pattern = '<a href="/bonanza/(serie/.*?)".*?' \
                  'data-src="(//asset\.dr\.dk/[^"]+)".*?' \
                  '<h3>([^<]+)</h3>.*?<p>([^<]+)</p>'
        for m in re.finditer(pattern, html, re.DOTALL):
            url = BASE_URL + m.group(1)
            image = 'http:' + m.group(2)
            title = unescape(m.group(3))
            description = unescape(m.group(4))

            item = xbmcgui.ListItem(title, offscreen=True)
            item.setArt({'fanart': FANART, 'icon': image})
            item.setInfo('video', infoLabels={
                'title': title,
                'plot': description
            })
            url = self._plugin_url + '?mode=content&url=' + url
            xbmcplugin.addDirectoryItem(self._plugin_handle, url, item, True)

    def addContent(self, html):
        items = list()
        pattern = '<a href="/bonanza/(serie/.*?)".*?title="([^"]+)".*?' \
                  'data-src="(//asset\.dr\.dk/[^"]+)".*?' \
                  '<h3>([^<]+)</h3>'
        html = html.split('<div class="list-footer"></div>', 1)[0]
        for m in re.finditer(pattern, html, re.DOTALL):
            url = BASE_URL + m.group(1)
            description = unescape(m.group(2))
            image = 'http:' + m.group(3)
            title = unescape(m.group(4))
            infoLabels = {
                'title': title,
                'plot': description,
                'studio': addon_name}

            item = xbmcgui.ListItem(infoLabels['title'], offscreen=True)
            item.setArt({'fanart': FANART, 'icon': image, 'thumb': image})
            item.setProperty('IsPlayable', 'true')
            item.setInfo('video', infoLabels)

            url = '?mode=play&url=' + url
            items.append((self._plugin_url + url, item, False))
        xbmcplugin.addDirectoryItems(self._plugin_handle, items)

    def playContent(self, url):
        html = self._downloadUrl(url)
        pattern = '<source.*?src="([^"]+)"'
        m = re.search(pattern, html, re.DOTALL)
        if m is not None:
            item = xbmcgui.ListItem(path=m.group(1))
            if int(get_setting('inputstream')) == 0 and '.mp3' not in m.group(1):
                is_helper = Helper('hls')
                if is_helper.check_inputstream():
                    item.setProperty('inputstream', is_helper.inputstream_addon)
                    item.setProperty('inputstream.adaptive.manifest_type', 'hls')

            xbmcplugin.setResolvedUrl(self._plugin_handle, True, item)
        else:
            xbmcplugin.setResolvedUrl(self._plugin_handle, False, xbmcgui.ListItem())

    def _downloadUrl(self, url):
        try:
            u = self.session.get(url)
            if u.status_code == 200:
                data = u.text
                u.close()
                return data
        except Exception as ex:
            raise BonanzaException(ex)

    def showError(self, message):
        heading = 'API error'
        xbmcgui.Dialog().ok(heading, '\n'.join([tr(30900), tr(30901), message]))

    def route(self, query):
        try:
            PARAMS = dict(parse_qsl(query[1:]))
            if 'mode' in PARAMS:
                if PARAMS['mode'] == 'subcat':
                    self.showSubCategories(PARAMS['url'])
                elif PARAMS['mode'] == 'content':
                    self.showContent(PARAMS['url'])
                elif PARAMS['mode'] == 'search':
                    self.search()
                elif PARAMS['mode'] == 'play':
                    self.playContent(PARAMS['url'])
            else:
                self.showCategories()

        except BonanzaException as ex:
            self.showError(str(ex))

        except Exception as ex:
            stack = traceback.format_exc()
            heading = 'dr bonaza addon crash'
            xbmcgui.Dialog().ok(heading, '\n'.join([tr(30906), tr(30907), str(stack)]))
            raise ex
