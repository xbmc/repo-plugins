"""
    IMDB Trailers Kodi Addon
    Copyright (C) 2018 gujal

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

# Imports
import re
import sys
import datetime
import json
from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
from bs4 import BeautifulSoup, SoupStrainer
from resources.lib import client
import six
from six.moves import urllib_parse
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

# HTMLParser() deprecated in Python 3.4 and removed in Python 3.9
if sys.version_info >= (3, 4, 0):
    import html
    _html_parser = html
else:
    from six.moves import html_parser
    _html_parser = html_parser.HTMLParser()

_addon = xbmcaddon.Addon()
_addonID = _addon.getAddonInfo('id')
_plugin = _addon.getAddonInfo('name')
_version = _addon.getAddonInfo('version')
_icon = _addon.getAddonInfo('icon')
_fanart = _addon.getAddonInfo('fanart')
_language = _addon.getLocalizedString
_settings = _addon.getSetting
_addonpath = 'special://profile/addon_data/{}/'.format(_addonID)
# DEBUG
DEBUG = _settings("DebugMode") == "true"
# View Mode
force_mode = _settings("forceViewMode") == "true"
if force_mode:
    menu_mode = int(_settings('MenuMode'))
    view_mode = int(_settings('VideoMode'))

if not xbmcvfs.exists(_addonpath):
    xbmcvfs.mkdir(_addonpath)

cache = StorageServer.StorageServer(_plugin if six.PY3 else _plugin.encode('utf8'), _settings('timeout'))
CONTENT_URL = 'https://www.imdb.com/trailers/'
SHOWING_URL = 'https://www.imdb.com/showtimes/location/'
COMING_URL = 'https://www.imdb.com/calendar/'
ID_URL = 'https://www.imdb.com/_json/video/{0}'
SHOWING_TRAILER = 'https://www.imdb.com/showtimes/title/{0}/'
DETAILS_PAGE = "https://www.imdb.com/video/{0}/"
quality = int(_settings("video_quality")[:-1])
LOGINFO = xbmc.LOGINFO if six.PY3 else xbmc.LOGNOTICE

if not xbmcvfs.exists(_addonpath + 'settings.xml'):
    _addon.openSettings()


class Main(object):
    def __init__(self):
        action = self.parameters('action')
        if action == 'list2':
            self.list_contents2()
        elif action == 'list1':
            self.list_contents1()
        elif action == 'play_id':
            self.play_id()
        elif action == 'play':
            self.play()
        elif action == 'search':
            self.search()
        elif action == 'search_word':
            self.search_word()
        elif action == 'clear':
            self.clear_cache()
        else:
            self.main_menu()

    def main_menu(self):
        if DEBUG:
            self.log('main_menu()')
        category = [{'title': _language(30201), 'key': 'showing'},
                    {'title': _language(30202), 'key': 'coming'},
                    {'title': _language(30208), 'key': 'trending'},
                    {'title': _language(30209), 'key': 'anticipated'},
                    {'title': _language(30210), 'key': 'popular'},
                    {'title': _language(30211), 'key': 'recent'},
                    {'title': _language(30206), 'key': 'search'},
                    {'title': _language(30207), 'key': 'cache'}]
        for i in category:
            listitem = xbmcgui.ListItem(i['title'])
            listitem.setArt({'thumb': _icon,
                             'fanart': _fanart,
                             'icon': _icon})

            if i['key'] == 'cache':
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'clear'})
            elif i['key'] == 'search':
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'search'})
            elif i['key'] == 'showing' or i['key'] == 'coming':
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'list1',
                                                                  'key': i['key']})
            else:
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'list2',
                                                                  'key': i['key']})

            xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(url, listitem, True)])

        # Sort methods and content type...
        xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setContent(int(sys.argv[1]), 'addons')
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(menu_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True)

    def clear_cache(self):
        """
        Clear the cache database.
        """
        if DEBUG:
            self.log('clear_cache()')
        msg = 'Cached Data has been cleared'
        cache.table_name = _plugin
        cache.cacheDelete(r'%fetch%')
        xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)

    def search(self):
        if DEBUG:
            self.log('search()')
        keyboard = xbmc.Keyboard()
        keyboard.setHeading('Search IMDb by Title')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_text = urllib_parse.quote(keyboard.getText())
        else:
            search_text = ''
        xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)
        if len(search_text) > 2:
            url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'search_word',
                                                              'keyword': search_text})
            xbmc.executebuiltin("Container.Update({0})".format(url))
        else:
            msg = 'Need atleast 3 characters'
            xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)
            xbmc.executebuiltin("Container.Update({0},replace)".format(sys.argv[0]))

    def search_word(self):
        search_text = urllib_parse.unquote(self.parameters('keyword'))
        if DEBUG:
            self.log('search_word("{0}")'.format(search_text))
        # url = 'https://www.imdb.com/find?q={}&s=tt'.format(search_text)
        # page_data = cache.cacheFunction(fetch, url)
        # tlink = SoupStrainer('table', {'class': 'findList'})
        # soup = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
        # items = soup.find_all('tr')
        api_url = 'https://graphql.prod.api.imdb.a2z.com/'
        searchTerm = 'searchTerm: "{0}"'.format(search_text)
        query = ("query {"
                 "  mainSearch("
                 "      first: 5"
                 "      options: {"
                 + searchTerm +  # noQA
                 "      isExactMatch: false"
                 "      type: TITLE"
                 "      titleSearchOptions: { type: MOVIE }"
                 "      }"
                 "  ) {"
                 "      edges {"
                 "      node {"
                 "          entity {"
                 "            ... on Title {"
                 "              id"
                 "              titleText {"
                 "                text"
                 "              }"
                 "              plot {"
                 "                plotText {"
                 "                  plainText"
                 "                }"
                 "              }"
                 "              primaryImage {"
                 "                url"
                 "              }"
                 "              releaseDate {"
                 "                year"
                 "              }"
                 "              ratingsSummary {"
                 "                aggregateRating"
                 "                voteCount"
                 "              }"
                 "              certificate {"
                 "              rating"
                 "              }"
                 "              titleGenres {"
                 "                genres {"
                 "                  genre {"
                 "                    text"
                 "                  }"
                 "                }"
                 "              }"
                 "              directors: credits(first: 5, filter: { categories: [\"director\"] }) {"
                 "                edges {"
                 "                  node {"
                 "                    name {"
                 "                      nameText {"
                 "                        text"
                 "                      }"
                 "                    }"
                 "                  }"
                 "                }"
                 "              }"
                 "              cast: credits(first: 10, filter: { categories: [\"actor\", \"actress\"] }) {"
                 "                edges {"
                 "                  node {"
                 "                    name {"
                 "                      nameText {"
                 "                        text"
                 "                      }"
                 "                      primaryImage {"
                 "                        url"
                 "                      }"
                 "                    }"
                 "                  }"
                 "                }"
                 "              }"
                 "              latestTrailer {"
                 "                id"
                 "                  runtime {"
                 "                    value"
                 "                  }"
                 "                  thumbnail {"
                 "                    url"
                 "                  }"
                 "              }"
                 "            }"
                 "         }"
                 "      }"
                 "    }"
                 "  }"
                 "}")

        qstr = urllib_parse.quote(query, "(")
        data = cache.cacheFunction(fetch, "{0}?query={1}".format(api_url, qstr))
        items = data.get('data').get('mainSearch').get('edges')
        for item in items:
            video = item.get('node').get('entity')
            title = video.get('titleText').get('text')
            if video.get('latestTrailer'):
                videoId = video.get('latestTrailer').get('id')
                duration = video.get('latestTrailer').get('runtime').get('value')
                labels = {'title': title,
                          'duration': duration}
                plot = video.get('plot')
                if plot:
                    labels.update({'plot': plot.get('plotText').get('plainText')})

                try:
                    director = [x.get('node').get('name').get('nameText').get('text') for x in video.get('directors').get('edges')]
                    labels.update({'director': director})
                except AttributeError:
                    pass

                try:
                    writer = [x.get('node').get('name').get('nameText').get('text') for x in video.get('writers').get('edges')]
                    labels.update({'writer': writer})
                except AttributeError:
                    pass

                try:
                    cast = [x.get('node').get('name').get('nameText').get('text') for x in video.get('cast').get('edges')]
                    labels.update({'cast': cast})
                    cast2 = [
                        {'name': x.get('node').get('name').get('nameText').get('text'),
                         'thumbnail': x.get('node').get('name').get('primaryImage').get('url')
                            if x.get('node').get('name').get('primaryImage') else ''}
                        for x in video.get('cast').get('edges')
                    ]

                except AttributeError:
                    cast2 = []
                    pass

                try:
                    genre = [x.get('genre').get('text') for x in video.get('titleGenres').get('genres')]
                    labels.update({'genre': genre})
                except AttributeError:
                    pass

                cert = video.get('certificate')
                if cert:
                    labels.update({'mpaa': cert.get('rating')})

                rating = video.get('ratingsSummary')
                if rating.get('aggregateRating'):
                    labels.update({'rating': rating.get('aggregateRating'),
                                   'votes': rating.get('voteCount')})

                try:
                    fanart = video.get('latestTrailer').get('thumbnail').get('url')
                except AttributeError:
                    fanart = ''
                try:
                    poster = video.get('primaryImage').get('url')
                except AttributeError:
                    poster = fanart
                try:
                    year = video.get('releaseDate').get('year')
                except AttributeError:
                    year = ''

                if year:
                    labels.update({'year': year})

                labels.update({'mediatype': 'movie'})
                if 'mpaa' in labels.keys():
                    if 'TV' in labels.get('mpaa'):
                        labels.update({'mediatype': 'tvshow'})

                listitem = xbmcgui.ListItem(title)
                listitem.setArt({'thumb': poster,
                                 'icon': poster,
                                 'poster': poster,
                                 'fanart': fanart})

                listitem.setInfo(type='Video', infoLabels=labels)
                if cast2:
                    listitem.setCast(cast2)

                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'play',
                                                                  'videoid': videoId})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

        # Sort methods and content type...
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True, cacheToDisc=False)

    def list_contents1(self):
        key = self.parameters('key')
        if DEBUG:
            self.log('list_contents1({0})'.format(key))

        if key == 'showing':
            page_data = cache.cacheFunction(fetch, SHOWING_URL)
            tlink = SoupStrainer('div', {'class': 'lister-list'})
            mdiv = BeautifulSoup(page_data, "html.parser", parse_only=tlink)
            videos = mdiv.find_all('div', {'class': 'lister-item'})
            imdbIDs = [x.find('div', {'class': 'lister-item-image'}).get('data-tconst') for x in videos]
        else:
            page_data = cache.cacheFunction(fetch, COMING_URL)
            imdbIDs = re.findall(r'<li>\s*<a\s*href="/title/([^/]+)', page_data, re.DOTALL)

        for imdbId in imdbIDs:
            video = cache.cacheFunction(self.fetchdata_id, imdbId)
            video = video.get('data').get('title')
            title = video.get('titleText').get('text')
            if video.get('latestTrailer'):
                videoId = video.get('latestTrailer').get('id')
                duration = video.get('latestTrailer').get('runtime').get('value')
                labels = {'title': title,
                          'duration': duration}
                plot = video.get('plot')
                if plot:
                    labels.update({'plot': plot.get('plotText').get('plainText')})

                try:
                    director = [x.get('node').get('name').get('nameText').get('text') for x in video.get('directors').get('edges')]
                    labels.update({'director': director})
                except AttributeError:
                    pass

                try:
                    writer = [x.get('node').get('name').get('nameText').get('text') for x in video.get('writers').get('edges')]
                    labels.update({'writer': writer})
                except AttributeError:
                    pass

                try:
                    cast = [x.get('node').get('name').get('nameText').get('text') for x in video.get('cast').get('edges')]
                    labels.update({'cast': cast})
                    cast2 = [
                        {'name': x.get('node').get('name').get('nameText').get('text'),
                         'thumbnail': x.get('node').get('name').get('primaryImage').get('url')
                            if x.get('node').get('name').get('primaryImage') else ''}
                        for x in video.get('cast').get('edges')
                    ]

                except AttributeError:
                    cast2 = []
                    pass

                try:
                    genre = [x.get('genre').get('text') for x in video.get('titleGenres').get('genres')]
                    labels.update({'genre': genre})
                except AttributeError:
                    pass

                cert = video.get('certificate')
                if cert:
                    labels.update({'mpaa': cert.get('rating')})

                rating = video.get('ratingsSummary')
                if rating.get('aggregateRating'):
                    labels.update({'rating': rating.get('aggregateRating'),
                                   'votes': rating.get('voteCount')})

                try:
                    fanart = video.get('latestTrailer').get('thumbnail').get('url')
                except AttributeError:
                    fanart = ''
                try:
                    poster = video.get('primaryImage').get('url')
                except AttributeError:
                    poster = fanart
                try:
                    year = video.get('releaseDate').get('year')
                except AttributeError:
                    year = ''

                if year:
                    labels.update({'year': year})

                labels.update({'mediatype': 'movie'})
                if 'mpaa' in labels.keys():
                    if 'TV' in labels.get('mpaa'):
                        labels.update({'mediatype': 'tvshow'})

                listitem = xbmcgui.ListItem(title)
                listitem.setArt({'thumb': poster,
                                 'icon': poster,
                                 'poster': poster,
                                 'fanart': fanart})

                listitem.setInfo(type='Video', infoLabels=labels)
                if cast2:
                    listitem.setCast(cast2)

                listitem.setProperty('IsPlayable', 'true')
                url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'play',
                                                                  'videoid': videoId})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

        # Sort methods and content type...
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

    def list_contents2(self):
        key = self.parameters('key')
        if DEBUG:
            self.log('content_list3("{0}")'.format(key))

        videos = cache.cacheFunction(self.fetchdata, key)
        for video in videos:
            if DEBUG:
                self.log(repr(video))
            if key == 'trending' or key == 'anticipated' or key == 'popular':
                title = video.get('titleText')
                if title:
                    title = title.get('text')
                else:
                    title = ''
                videoId = video.get('latestTrailer').get('id')
                duration = video.get('latestTrailer').get('runtime').get('value')
                name = video.get('latestTrailer').get('name').get('value')
                labels = {'title': title,
                          'duration': duration}
                try:
                    plot = video.get('latestTrailer').get('description').get('value')
                except AttributeError:
                    plot = ''
                if plot == name or len(plot) == 0:
                    try:
                        plot = video.get('plot').get('plotText').get('plainText')
                    except AttributeError:
                        pass
                if plot:
                    labels.update({'plot': plot})

                try:
                    director = [x.get('node').get('name').get('nameText').get('text') for x in video.get('directors').get('edges')]
                    labels.update({'director': director})
                except AttributeError:
                    pass

                try:
                    writer = [x.get('node').get('name').get('nameText').get('text') for x in video.get('writers').get('edges')]
                    labels.update({'writer': writer})
                except AttributeError:
                    pass

                try:
                    cast = [x.get('node').get('name').get('nameText').get('text') for x in video.get('cast').get('edges')]
                    labels.update({'cast': cast})
                    cast2 = [
                        {'name': x.get('node').get('name').get('nameText').get('text'),
                         'thumbnail': x.get('node').get('name').get('primaryImage').get('url')
                            if x.get('node').get('name').get('primaryImage') else ''}
                        for x in video.get('cast').get('edges')
                    ]
                except AttributeError:
                    cast2 = []
                    pass

                try:
                    genre = [x.get('genre').get('text') for x in video.get('titleGenres').get('genres')]
                    labels.update({'genre': genre})
                except AttributeError:
                    pass

                cert = video.get('certificate')
                if cert:
                    labels.update({'mpaa': cert.get('rating')})

                rating = video.get('ratingsSummary')
                if rating:
                    labels.update({'rating': rating.get('aggregateRating'),
                                   'votes': rating.get('voteCount')})

                try:
                    fanart = video.get('latestTrailer').get('thumbnail').get('url', '')
                except AttributeError:
                    fanart = ''
                try:
                    poster = video.get('primaryImage').get('url', '')
                except AttributeError:
                    poster = fanart
                try:
                    year = video.get('releaseDate').get('year')
                except AttributeError:
                    year = ''
            elif key == 'recent':
                try:
                    title = video.get('primaryTitle', {}).get('titleText', {}).get('text', '')
                except AttributeError:
                    title = ''
                videoId = video.get('id')
                duration = video.get('runtime').get('value')
                name = video.get('name').get('value')
                labels = {'title': title,
                          'duration': duration}

                try:
                    plot = video.get('description', {}).get('value', '')
                except AttributeError:
                    plot = ''
                v_det = video.get('primaryTitle')
                if plot == name or len(plot) == 0:
                    try:
                        plot = v_det.get('plot', {}).get('plotText', {}).get('plainText', '')
                    except AttributeError:
                        pass
                if plot:
                    labels.update({'plot': plot})

                try:
                    director = [x.get('node').get('name').get('nameText').get('text') for x in v_det.get('directors').get('edges')]
                    labels.update({'director': director})
                except AttributeError:
                    pass

                try:
                    writer = [x.get('node').get('name').get('nameText').get('text') for x in v_det.get('writers').get('edges')]
                    labels.update({'writer': writer})
                except AttributeError:
                    pass

                try:
                    cast = [x.get('node').get('name').get('nameText').get('text') for x in v_det.get('cast').get('edges')]
                    labels.update({'cast': cast})
                    cast2 = [
                        {'name': x.get('node').get('name').get('nameText').get('text'),
                         'thumbnail': x.get('node').get('name').get('primaryImage').get('url')
                            if x.get('node').get('name').get('primaryImage') else ''}
                        for x in v_det.get('cast').get('edges')
                    ]
                except AttributeError:
                    cast2 = []
                    pass

                try:
                    genre = [x.get('genre').get('text') for x in v_det.get('titleGenres').get('genres')]
                    labels.update({'genre': genre})
                except AttributeError:
                    pass

                cert = v_det.get('certificate')
                if cert:
                    labels.update({'mpaa': cert.get('rating')})

                rating = v_det.get('ratingsSummary')
                if rating.get('aggregateRating'):
                    labels.update({'rating': rating.get('aggregateRating'),
                                   'votes': rating.get('voteCount')})

                try:
                    fanart = video.get('thumbnail').get('url')
                except AttributeError:
                    fanart = ''
                try:
                    poster = v_det.get('primaryImage').get('url')
                except AttributeError:
                    poster = fanart
                try:
                    year = v_det.get('releaseDate').get('year')
                except AttributeError:
                    year = ''

            if title in name:
                name = name.replace(title, '').strip()
            if len(name) > 0:
                if six.PY2:
                    name = name.encode('utf8')
                    title = title.encode('utf8')
                title = '{0} [COLOR cyan][I]{1}[/I][/COLOR]'.format(title, name)

            if year:
                labels.update({'year': year})

            labels.update({'mediatype': 'movie'})
            if 'mpaa' in labels.keys():
                if 'TV' in labels.get('mpaa'):
                    labels.update({'mediatype': 'tvshow'})

            listitem = xbmcgui.ListItem(title)
            listitem.setArt({'thumb': poster,
                             'icon': poster,
                             'poster': poster,
                             'fanart': fanart})

            listitem.setInfo(type='Video', infoLabels=labels)
            if cast2:
                listitem.setCast(cast2)

            listitem.setProperty('IsPlayable', 'true')
            url = sys.argv[0] + '?' + urllib_parse.urlencode({'action': 'play',
                                                              'videoid': videoId})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, listitem, False)

        # Sort methods and content type...
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        if force_mode:
            xbmc.executebuiltin('Container.SetViewMode({})'.format(view_mode))
        # End of directory...
        xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=True)

    def fetch_video_url(self, video_id):
        if DEBUG:
            self.log('fetch_video_url("{0})'.format(video_id))
        vidurl = DETAILS_PAGE.format(video_id)
        pagedata = cache.cacheFunction(fetch, vidurl)
        r = re.search(r'application/json">([^<]+)', pagedata)
        if r:
            details = json.loads(r.group(1)).get('props', {}).get('pageProps', {}).get('videoPlaybackData', {}).get('video')
            if details:
                details = {i.get('displayName').get('value'): i.get('url') for i in details.get('playbackURLs') if i.get('mimeType') == 'video/mp4'}
                vids = [(x[:-1], details[x]) for x in details.keys() if 'p' in x]
                vids.sort(key=lambda x: int(x[0]), reverse=True)
                if DEBUG:
                    self.log('Found %s videos' % len(vids))
                for qual, vid in vids:
                    if int(qual) <= quality:
                        if DEBUG:
                            self.log('videoURL: %s' % vid)
                        return vid

        return None

    def play(self):
        if DEBUG:
            self.log('play()')
        title = xbmc.getInfoLabel("ListItem.Title")
        thumbnail = xbmc.getInfoImage("ListItem.Thumb")
        plot = xbmc.getInfoLabel("ListItem.Plot")
        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
        listitem = xbmcgui.ListItem(title)
        listitem.setArt({'thumb': thumbnail})

        # set the key information
        listitem.setInfo('video', {'title': title,
                                   'plot': plot,
                                   'plotOutline': plot})

        listitem.setPath(cache.cacheFunction(self.fetch_video_url, self.parameters('videoid')))
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listitem)

    def play_id(self):
        imdb_id = self.parameters('imdb')
        if DEBUG:
            self.log('play_id("{0})'.format(imdb_id))

        video = cache.cacheFunction(self.fetchdata_id, imdb_id)
        video = video.get('data').get('title')
        if video.get('latestTrailer'):
            videoid = video.get('latestTrailer').get('id')
            title = video.get('titleText').get('text')
            try:
                year = video.get('releaseDate').get('year')
            except AttributeError:
                year = ''
            plot = video.get('plot')
            if plot:
                plot = plot.get('plotText').get('plainText')
            thumbnail = video.get('latestTrailer').get('thumbnail').get('url')
            poster = video.get('primaryImage').get('url')
            listitem = xbmcgui.ListItem(title)
            listitem.setArt({'thumb': poster,
                             'icon': poster,
                             'poster': poster,
                             'fanart': thumbnail})
            # set the key information
            listitem.setInfo('video', {'title': title,
                                       'plot': plot,
                                       'plotOutline': plot,
                                       'year': year})
            listitem.setPath(cache.cacheFunction(self.fetch_video_url, videoid))
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem=listitem)
        else:
            msg = 'No Trailers available'
            xbmcgui.Dialog().notification(_plugin, msg, _icon, 3000, False)

    def parameters(self, arg):
        _parameters = urllib_parse.parse_qs(urllib_parse.urlparse(sys.argv[2]).query)
        val = _parameters.get(arg, '')
        if isinstance(val, list):
            val = val[0]
        return val

    def log(self, description):
        xbmc.log("[ADD-ON] '{} v{}': {}".format(_plugin, _version, description), LOGINFO)

    def fetchdata_id(self, imdb_id):
        api_url = 'https://graphql.prod.api.imdb.a2z.com/'
        title = "title(id: \"{}\") {{".format(imdb_id)
        query = ("query {"
                 + title +  # noQA
                 "  titleText {"
                 "    text"
                 "  }"
                 "  plot {"
                 "    plotText {"
                 "      plainText"
                 "    }"
                 "  }"
                 "  primaryImage {"
                 "    url"
                 "  }"
                 "  releaseDate {"
                 "    year"
                 "  }"
                 "  ratingsSummary {"
                 "    aggregateRating"
                 "    voteCount"
                 "  }"
                 "  certificate {"
                 "  rating"
                 "  }"
                 "  titleGenres {"
                 "    genres {"
                 "      genre {"
                 "        text"
                 "      }"
                 "    }"
                 "  }"
                 "  directors: credits(first: 5, filter: { categories: [\"director\"] }) {"
                 "    edges {"
                 "      node {"
                 "        name {"
                 "          nameText {"
                 "            text"
                 "          }"
                 "        }"
                 "      }"
                 "    }"
                 "  }"
                 "  writers: credits(first: 5, filter: { categories: [\"writer\"] }) {"
                 "    edges {"
                 "      node {"
                 "        name {"
                 "          nameText {"
                 "            text"
                 "          }"
                 "        }"
                 "      }"
                 "    }"
                 "  }"
                 "  cast: credits(first: 10, filter: { categories: [\"actor\", \"actress\"] }) {"
                 "    edges {"
                 "      node {"
                 "        name {"
                 "          nameText {"
                 "            text"
                 "          }"
                 "          primaryImage {"
                 "            url"
                 "          }"
                 "        }"
                 "      }"
                 "    }"
                 "  }"
                 "  latestTrailer {"
                 "    id"
                 "      runtime {"
                 "        value"
                 "      }"
                 "      thumbnail {"
                 "        url"
                 "      }"
                 "  }"
                 "}"
                 "}")

        qstr = urllib_parse.quote(query, "(")
        data = cache.cacheFunction(fetch, "{0}?query={1}".format(api_url, qstr))
        return data

    def fetchdata(self, key):
        api_url = 'https://graphql.prod.api.imdb.a2z.com/'
        vpar = {'limit': 100}
        if key == 'trending':
            query_pt1 = ("query TrendingTitles($limit: Int!, $paginationToken: String) {"
                         "  trendingTitles(limit: $limit, paginationToken: $paginationToken) {"
                         "    titles {"
                         "      latestTrailer {"
                         "        ...TrailerVideoMeta"
                         "      }"
                         "      ...TrailerTitleMeta"
                         "    }"
                         "    paginationToken"
                         "  }"
                         "}")
            ptoken = "60"
            opname = "TrendingTitles"
        elif key == 'recent':
            query_pt1 = ("query RecentVideos($limit: Int!, $paginationToken: String, $queryFilter: RecentVideosQueryFilter!) {"
                         "  recentVideos(limit: $limit, paginationToken: $paginationToken, queryFilter: $queryFilter) {"
                         "    videos {"
                         "      ...TrailerVideoMeta"
                         "      primaryTitle {"
                         "        ...TrailerTitleMeta"
                         "      }"
                         "    }"
                         "    paginationToken"
                         "  }"
                         "}")
            ptoken = "blank"
            opname = "RecentVideos"
            vpar.update({'queryFilter': {"contentTypes": ["TRAILER"]}})
        elif key == 'anticipated' or key == 'popular':
            query_pt1 = ("query PopularTitles($limit: Int!, $paginationToken: String, $queryFilter: PopularTitlesQueryFilter!) {"
                         "  popularTitles(limit: $limit, paginationToken: $paginationToken, queryFilter: $queryFilter) {"
                         "    titles {"
                         "      latestTrailer {"
                         "        ...TrailerVideoMeta"
                         "      }"
                         "      ...TrailerTitleMeta"
                         "    }"
                         "    paginationToken"
                         "  }"
                         "}")
            ptoken = "blank"
            opname = "PopularTitles"
            d1 = datetime.date.today().isoformat()
            if key == 'anticipated':
                vpar.update({'queryFilter': {"releaseDateRange": {"start": d1}}})
            else:
                vpar.update({'queryFilter': {"releaseDateRange": {"end": d1}}})

        if key == 'popular':
            query_pt2 = ("fragment TrailerTitleMeta on Title {"
                         "  id"
                         "  titleText {"
                         "    text"
                         "  }"
                         "  plot {"
                         "    plotText {"
                         "      plainText"
                         "    }"
                         "  }"
                         "  primaryImage {"
                         "    url"
                         "  }"
                         "  releaseDate {"
                         "    year"
                         "  }"
                         "  ratingsSummary {"
                         "    aggregateRating"
                         "    voteCount"
                         "  }"
                         "  certificate {"
                         "  rating"
                         "  }"
                         "  titleGenres {"
                         "    genres {"
                         "      genre {"
                         "        text"
                         "      }"
                         "    }"
                         "  }"
                         "  directors: credits(first: 5, filter: { categories: [\"director\"] }) {"
                         "    edges {"
                         "      node {"
                         "        name {"
                         "          nameText {"
                         "            text"
                         "          }"
                         "        }"
                         "      }"
                         "    }"
                         "  }"
                         "  cast: credits(first: 10, filter: { categories: [\"actor\", \"actress\"] }) {"
                         "    edges {"
                         "      node {"
                         "        name {"
                         "          nameText {"
                         "            text"
                         "          }"
                         "          primaryImage {"
                         "            url"
                         "          }"
                         "        }"
                         "      }"
                         "    }"
                         "  }"
                         "}"
                         "fragment TrailerVideoMeta on Video {"
                         "  id"
                         "  name {"
                         "    value"
                         "  }"
                         "  runtime {"
                         "    value"
                         "  }"
                         "  description {"
                         "    value"
                         "  }"
                         "  thumbnail {"
                         "    url"
                         "  }"
                         "}")
        else:
            query_pt2 = ("fragment TrailerTitleMeta on Title {"
                         "  id"
                         "  titleText {"
                         "    text"
                         "  }"
                         "  plot {"
                         "    plotText {"
                         "      plainText"
                         "    }"
                         "  }"
                         "  primaryImage {"
                         "    url"
                         "  }"
                         "  releaseDate {"
                         "    year"
                         "  }"
                         "  ratingsSummary {"
                         "    aggregateRating"
                         "    voteCount"
                         "  }"
                         "  certificate {"
                         "  rating"
                         "  }"
                         "  titleGenres {"
                         "    genres {"
                         "      genre {"
                         "        text"
                         "      }"
                         "    }"
                         "  }"
                         "  directors: credits(first: 5, filter: { categories: [\"director\"] }) {"
                         "    edges {"
                         "      node {"
                         "        name {"
                         "          nameText {"
                         "            text"
                         "          }"
                         "        }"
                         "      }"
                         "    }"
                         "  }"
                         "  writers: credits(first: 5, filter: { categories: [\"writer\"] }) {"
                         "    edges {"
                         "      node {"
                         "        name {"
                         "          nameText {"
                         "            text"
                         "          }"
                         "        }"
                         "      }"
                         "    }"
                         "  }"
                         "  cast: credits(first: 10, filter: { categories: [\"actor\", \"actress\"] }) {"
                         "    edges {"
                         "      node {"
                         "        name {"
                         "          nameText {"
                         "            text"
                         "          }"
                         "          primaryImage {"
                         "            url"
                         "          }"
                         "        }"
                         "      }"
                         "    }"
                         "  }"
                         "}"
                         "fragment TrailerVideoMeta on Video {"
                         "  id"
                         "  name {"
                         "    value"
                         "  }"
                         "  runtime {"
                         "    value"
                         "  }"
                         "  description {"
                         "    value"
                         "  }"
                         "  thumbnail {"
                         "    url"
                         "  }"
                         "}")

        qstr = urllib_parse.quote(query_pt1 + query_pt2, "(")
        items = []
        pages = 0

        while len(items) < 200 and ptoken and pages < 5:
            if ptoken != "blank":
                vpar.update({"paginationToken": ptoken})

            vtxt = urllib_parse.quote(json.dumps(vpar).replace(" ", ""))
            data = cache.cacheFunction(fetch, "{0}?operationName={1}&query={2}&variables={3}".format(api_url, opname, qstr, vtxt))
            pages += 1
            data = data.get('data')

            if key == 'trending' or key == 'anticipated' or key == 'popular':
                if key == 'trending':
                    data = data.get('trendingTitles')
                elif key == 'anticipated' or key == 'popular':
                    data = data.get('popularTitles')
                titles = data.get('titles')
                for title in titles:
                    if title.get('latestTrailer'):
                        items.append(title)
            elif key == 'recent':
                data = data.get('recentVideos')
                titles = data.get('videos')
                items.extend(titles)

            if len(titles) < 1:
                ptoken = None
            else:
                ptoken = data.get('paginationToken')

        return items


def fetch(url):
    headers = {'Referer': 'https://www.imdb.com/',
               'Origin': 'https://www.imdb.com'}
    if 'graphql' in url:
        headers.update({'content-type': 'application/json'})
    r = client.request(url, headers=headers)
    return r
