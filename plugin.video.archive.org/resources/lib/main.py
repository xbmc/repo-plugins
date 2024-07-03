"""
    Internet Archive Kodi Addon
    Copyright (C) 2024 gujal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import json
import random
import re
import sys
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
from html import unescape
from resources.lib import client, cache

_addon = xbmcaddon.Addon()
_addonID = _addon.getAddonInfo('id')
_plugin = _addon.getAddonInfo('name')
_version = _addon.getAddonInfo('version')
_icon = _addon.getAddonInfo('icon')
_fanart = _addon.getAddonInfo('fanart')
_language = _addon.getLocalizedString
_settings = _addon.getSetting
_addonpath = 'special://profile/addon_data/{}/'.format(_addonID)
_kodiver = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])
# DEBUG
DEBUG = _settings("DebugMode") == "true"

if not xbmcvfs.exists(_addonpath):
    xbmcvfs.mkdir(_addonpath)

cache_duration = int(_settings('timeout'))

if not xbmcvfs.exists(_addonpath + 'settings.xml'):
    _addon.openSettings()


class Main(object):
    def __init__(self):
        self.base_url = 'https://archive.org/'
        self.search_url = self.base_url + 'services/search/beta/page_production/'
        self.img_path = self.base_url + 'services/img/'
        self.item_path = self.base_url + 'details/'
        self.headers = {'Referer': self.base_url}
        self.litems = []
        content_type = self.parameters('content_type')
        if content_type and _settings('context') != content_type:
            _addon.setSetting('context', content_type)
        action = self.parameters('action')
        content_type = _settings('context')
        if action == 'list_items':
            page = int(self.parameters('page'))
            target = self.parameters('target')
            self.list_items(target, page, content_type)
        elif action == 'list_collections':
            page = int(self.parameters('page'))
            self.list_collections(page, content_type)
        elif action == 'play':
            item_id = self.parameters('target')
            self.play(item_id, content_type)
        elif action == 'search':
            self.search(content_type)
        elif action == 'search_word':
            keyword = urllib.parse.unquote(self.parameters('keyword'))
            page = int(self.parameters('page'))
            self.search_word(keyword, page, content_type)
        elif action == 'clear':
            self.clear_cache()
        else:
            self.main_menu(content_type)

    def main_menu(self, content_type):
        if DEBUG:
            self.log('main_menu({0})'.format(content_type))
        category = [{'title': _language(30101), 'key': 'popular'},
                    {'title': _language(30102), 'key': 'search'},
                    {'title': _language(30002), 'key': 'cache'}]
        for i in category:
            listitem = xbmcgui.ListItem(i['title'])
            listitem.setArt({'thumb': _icon,
                             'fanart': _fanart,
                             'icon': _icon})

            if i['key'] == 'cache':
                url = sys.argv[0] + '?action=clear'
            elif i['key'] == 'search':
                url = '{}?action=search&content_type={}'.format(sys.argv[0], content_type)
            else:
                url = '{}?action=list_collections&page=1&content_type={}'.format(sys.argv[0], content_type)

            xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(url, listitem, True)])

        # Sort methods and content type...
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setContent(int(sys.argv[1]), 'addons')
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def clear_cache(self):
        """
        Clear the cache database.
        """
        if DEBUG:
            self.log('clear_cache()')
        cache.cache_clear()
        xbmcgui.Dialog().notification(_plugin, _language(30201), _icon, 3000, False)

    def get_search_items(self, filter_map, target, page):
        cd = {}
        params = {
            'service_backend': 'metadata',
            'user_query': target,
            'hits_per_page': 100,
            'page': page,
            'filter_map': filter_map,
            'aggregations': 'false',
            'client_url': 'https://archive.org/'
        }
        resp = client.request(self.search_url, headers=self.headers, params=params)
        if resp:
            cd = resp.get('response').get('body').get('hits')
        return cd

    def get_items(self, filter_map, target, page):
        cd = {}
        params = {
            'page_type': 'collection_details',
            'page_target': target,
            'hits_per_page': 100,
            'page': page,
            'filter_map': filter_map,
            'aggregations': 'false',
            'client_url': 'https://archive.org/'
        }
        resp = client.request(self.search_url, headers=self.headers, params=params)
        if resp:
            cd = resp.get('response').get('body').get('hits')
        return cd

    def list_collections(self, page, content_type):
        target = 'movies' if content_type == 'video' else 'audio'
        if DEBUG:
            self.log('list_collections({0}, {1})'.format(page, content_type))

        filter_map = '{"mediatype":{"collection":"inc"}}'
        data = cache.get(self.get_items, cache_duration, filter_map, target, page)
        if data:
            items = data.get('hits')
            for item in items:
                item = item.get('fields')
                title = item.get('title')
                plot = item.get('description')
                if plot:
                    plot = unescape(plot)
                slug = item.get('identifier')
                count = item.get('item_count')
                labels = {
                    'title': '{0} [I]({1:,} items)[/I]'.format(title, count),
                    'plot' if content_type == 'video' else 'comment': plot
                }
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': self.img_path + slug,
                    'thumb': self.img_path + slug,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'false')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'list_items',
                    'page': 1,
                    'target': slug,
                    'content_type': content_type
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

            total = data.get('total')
            if page * 100 < total:
                lastpg = -1 * (-total // 100)
                page += 1
                labels = {'title': '[COLOR lime]{}...[/COLOR] ({}/{})'.format(_language(30204), page, lastpg)}
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': _icon,
                    'thumb': _icon,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'false')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'list_collections',
                    'page': page,
                    'content_type': content_type
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

            # Sort methods and content type...
            xbmcplugin.setContent(int(sys.argv[1]), 'videos' if content_type == 'video' else 'albums')
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
            # End of directory...
            xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

    def list_items(self, target, page, content_type):
        if DEBUG:
            self.log('list_items("{0}, {1}, {2}")'.format(target, page, content_type))

        filter_map = '{{"mediatype":{{"{}":"inc","etree":"inc"}}}}'.format('movies' if content_type == 'video' else 'audio')
        data = cache.get(self.get_items, cache_duration, filter_map, target, page)
        if data:
            items = data.get('hits')
            for item in items:
                item = item.get('fields')
                title = item.get('title')
                plot = item.get('description')
                if plot:
                    plot = unescape(plot)
                slug = item.get('identifier')
                labels = {
                    'title': title,
                    'plot' if content_type == 'video' else 'comment': plot
                }
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': self.img_path + slug,
                    'thumb': self.img_path + slug,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'play',
                    'target': slug,
                    'content_type': content_type
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

            total = data.get('total')
            if page * 100 < total:
                lastpg = -1 * (-total // 100)
                page += 1
                labels = {'title': '[COLOR lime]{}...[/COLOR] ({}/{})'.format(_language(30204), page, lastpg)}
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': _icon,
                    'thumb': _icon,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'false')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'list_items',
                    'page': page,
                    'target': target,
                    'content_type': content_type
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

            # Sort methods and content type...
            xbmcplugin.setContent(int(sys.argv[1]), 'videos' if content_type == 'video' else 'songs')
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
            # End of directory...
            xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

    def format_bytes(self, size):
        n = 0
        slabels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
        while size > 1024:
            size /= 1024
            n += 1
        return '{0:.2f} {1}'.format(size, slabels[n])

    def search(self, content_type):
        if DEBUG:
            self.log('search({0})'.format(content_type))
        keyboard = xbmc.Keyboard()
        keyboard.setHeading(_language(30102))
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_text = urllib.parse.quote(keyboard.getText())
        else:
            search_text = ''
        xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
        if len(search_text) > 2:
            url = sys.argv[0] + '?' + urllib.parse.urlencode({'action': 'search_word',
                                                              'keyword': search_text,
                                                              'content_type': content_type,
                                                              'page': 1})
            xbmc.executebuiltin("Container.Update({0},replace)".format(url))
        else:
            xbmcgui.Dialog().notification(_plugin, _language(30202), _icon, 3000, False)
            xbmc.executebuiltin("Container.Update({0},replace)".format(sys.argv[0]))

    def search_word(self, search_text, page, content_type):
        if DEBUG:
            self.log('search_word("{0}, page {1}, {2}")'.format(search_text, page, content_type))
        filter_map = '{{"mediatype":{{"{}":"inc","etree":"inc"}}}}'.format('movies' if content_type == 'video' else 'audio')
        data = cache.get(self.get_search_items, cache_duration, filter_map, search_text, page)
        if data:
            items = data.get('hits')
            for item in items:
                item = item.get('fields')
                title = item.get('title')
                plot = item.get('description')
                if plot:
                    plot = unescape(plot)
                slug = item.get('identifier')
                labels = {
                    'title': title,
                    'plot' if content_type == 'video' else 'comment': plot
                }
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': self.img_path + slug,
                    'thumb': self.img_path + slug,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'play',
                    'target': slug,
                    'content_type': content_type
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

            total = data.get('total')
            if page * 100 < total:
                lastpg = -1 * (-total // 100)
                page += 1
                labels = {'title': '[COLOR lime]{}...[/COLOR] ({}/{})'.format(_language(30204), page, lastpg)}
                listitem = self.make_listitem(labels, content_type)
                listitem.setArt({
                    'icon': _icon,
                    'thumb': _icon,
                    'fanart': _fanart
                })
                listitem.setProperty('IsPlayable', 'false')
                url = sys.argv[0] + '?' + urllib.parse.urlencode({
                    'action': 'search_word',
                    'keyword': search_text,
                    'content_type': content_type,
                    'page': page
                })
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, True)

            # Sort methods and content type...
            xbmcplugin.setContent(int(sys.argv[1]), 'videos' if content_type == 'video' else 'songs')
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
            # End of directory...
            xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

    def play(self, item_id, content_type):
        url = self.item_path + item_id
        if DEBUG:
            self.log('play("{}") {}'.format(item_id, content_type))

        html = client.request(url, headers=self.headers)
        jsob = re.search('''class="js-play8-playlist".+?value='([^']+)''', html)
        if jsob:
            surl = ''
            data = json.loads(jsob.group(1))
            total = len(data)
            if total > 1:
                sources = [(i.get('title'), i.get('sources')[0].get('file')) for i in data]
                if content_type == 'video':
                    ret = xbmcgui.Dialog().select(_language(30203), [source[0] for source in sources])
                    if ret == -1:
                        return
                    surl = self.base_url + sources[ret][1]
                    item_id = sources[ret][0]
                else:
                    if DEBUG:
                        self.log('Found {} audio items'.format(total))
                    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
                    playlist.clear()
                    for title, source in sources:
                        li = self.make_listitem({'title': title}, content_type)
                        playlist.add(url=urllib.parse.urljoin(self.base_url, source), listitem=li)
            elif total == 1:
                jd = client.request(url.replace('/details/', '/metadata/'))
                sources = [i for i in jd.get('files') if 'height' in i.keys() and '.jpg' not in i.get('name')]
                if len(sources) > 1:
                    sources.sort(key=lambda item: (int(item.get('height')), item.get('source'), int(item.get('size'))), reverse=True)
                    srcs = ['{0} ({1} {2}p) {3}'.format(
                        i.get('name').split('.')[-1],
                        i.get('source'),
                        i.get('height'),
                        self.format_bytes(int(i.get('size')))
                    ) for i in sources]
                    ret = xbmcgui.Dialog().select(_language(30203), srcs)
                    if ret == -1:
                        return
                else:
                    ret = 0
                surl = 'https://{0}{1}/{2}'.format(
                    random.choice(jd.get('workable_servers')),
                    jd.get('dir'),
                    urllib.parse.quote(sources[ret].get('name'))
                )

            if total > 1 and content_type == 'audio':
                xbmc.Player().play(playlist)
            else:
                li = self.make_listitem({'title': item_id}, content_type)
                li.setArt({'fanart': _fanart})
                li.setPath(surl)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=li)

    def parameters(self, arg):
        _parameters = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[2]).query)
        val = _parameters.get(arg, '')
        if isinstance(val, list):
            val = val[0]
        return val

    def make_listitem(self, labels, content_type):
        li = xbmcgui.ListItem(labels.get('title'))
        if _kodiver > 19.8:
            vtag = li.getVideoInfoTag() if content_type == 'video' else li.getMusicInfoTag()
            vtag.setTitle(labels.get('title'))
            if content_type == 'video':
                vtag.setOriginalTitle(labels.get('title'))
            if labels.get('plot'):
                vtag.setPlot(labels.get('plot'))
                vtag.setPlotOutline(labels.get('plot'))
            if labels.get('comment'):
                vtag.setComment(labels.get('comment'))
            if labels.get('mediatype'):
                vtag.setMediaType(labels.get('mediatype'))
            if labels.get('duration'):
                vtag.setDuration(labels.get('duration'))
        else:
            li.setInfo(type='video' if content_type == 'video' else 'music', infoLabels=labels)

        return li

    def log(self, description):
        xbmc.log("[ADD-ON] '{} v{}': {}".format(_plugin, _version, description), xbmc.LOGINFO)
